import pandas as pd
import numpy as np
import sys
import os
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, classification_report,
                              confusion_matrix)
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from utils.preprocess import full_preprocess


def load_data(filepath):
    """Load and prepare dataset."""
    print("Loading dataset...")
    df = pd.read_csv(filepath)
    df.dropna(subset=['text', 'class'], inplace=True)
    # Using full dataset for maximum accuracy
    print(f"Total samples : {len(df)}")
    print(f"Class distribution:\n{df['class'].value_counts()}")
    return df


def extract_features(df):
    """Extract all features from dataframe."""
    print("\nPreprocessing text...")
    df['clean_text'] = df['text'].apply(full_preprocess)

    print("Extracting VADER sentiment scores...")
    sia = SentimentIntensityAnalyzer()
    sentiments = []
    neg_scores = []

    total = len(df)
    for i, text in enumerate(df['text']):
        scores = sia.polarity_scores(str(text))
        sentiments.append(scores['compound'])
        neg_scores.append(scores['neg'])
        if (i + 1) % 10000 == 0:
            print(f"  Progress: {i+1}/{total} rows done...")

    df['sentiment'] = sentiments
    df['neg_score'] = neg_scores
    return df


def train_models(df):
    """Train and compare multiple models."""

    print("\nBuilding TF-IDF features...")
    tfidf = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=3
    )
    X_tfidf = tfidf.fit_transform(df['clean_text']).toarray()

    X_sentiment = df[['sentiment', 'neg_score']].values
    X = np.hstack([X_tfidf, X_sentiment])
    y = df['class']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTraining samples : {len(X_train)}")
    print(f"Testing samples  : {len(X_test)}")

    print("\n" + "="*55)
    print("  MODEL COMPARISON")
    print("="*55)

    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000),
        'Random Forest': RandomForestClassifier(
            n_estimators=200, random_state=42, n_jobs=-1
        )
    }

    best_model = None
    best_score = 0
    best_name  = ""

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        cv  = cross_val_score(
            model, X_train, y_train, cv=5, scoring='f1_weighted'
        ).mean()

        print(f"  Accuracy    : {acc*100:.1f}%")
        print(f"  CV F1 Score : {cv:.4f}")

        if acc > best_score:
            best_score = acc
            best_model = model
            best_name  = name

    print(f"\n✅ Best model: {best_name} ({best_score*100:.1f}%)")

    y_pred_best = best_model.predict(X_test)
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred_best))

    save_confusion_matrix(y_test, y_pred_best)

    return best_model, tfidf


def save_confusion_matrix(y_test, y_pred):
    """Plot and save confusion matrix."""
    os.makedirs('../docs', exist_ok=True)
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Non-Suicide', 'Suicide'],
                yticklabels=['Non-Suicide', 'Suicide'])
    plt.title('Confusion Matrix - Self Harm Detection')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.tight_layout()
    plt.savefig('../docs/confusion_matrix.png')
    print("Confusion matrix saved to docs/confusion_matrix.png")


def save_model(model, tfidf):
    """Save trained model and vectorizer."""
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    joblib.dump(model, 'model/risk_model.pkl')
    joblib.dump(tfidf, 'model/tfidf_vectorizer.pkl')
    print("\n✅ Model saved to model/risk_model.pkl")
    print("✅ Vectorizer saved to model/tfidf_vectorizer.pkl")


if __name__ == "__main__":
    print("="*55)
    print("  SELF HARM DETECTION - MODEL TRAINING")
    print("  Training on FULL 232k dataset")
    print("="*55)

    df = load_data('data/Suicide_Detection.csv')
    df = extract_features(df)
    model, tfidf = train_models(df)
    save_model(model, tfidf)

    print("\n🎉 Training complete!")
    print("Run python app.py to start the API server.")