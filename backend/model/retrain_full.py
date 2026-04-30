"""
retrain_full.py
Train on the full 174k HuggingFace dataset using sparse matrices throughout.
Uses scipy sparse hstack so the TF-IDF matrix is never converted to dense.
Typical RAM usage: ~600 MB peak.

Run from backend/ directory:
    python model/retrain_full.py
"""
import os, sys, joblib, datetime
import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nltk
for pkg in ('vader_lexicon', 'stopwords', 'wordnet', 'punkt'):
    nltk.download(pkg, quiet=True)

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from nltk.sentiment.vader import SentimentIntensityAnalyzer

from utils.preprocess import full_preprocess

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))

print("=" * 55)
print("  SAFESIGNAL — FULL DATASET RETRAIN")
print("=" * 55)

# ── Load dataset ──────────────────────────────────────
print("\n=== Loading full 174k dataset ===")
try:
    from datasets import load_dataset
    ds = load_dataset("Ram07/Detection-for-Suicide", split="train")
    texts  = ds["text"]
    labels = ds["class"]
except Exception as e:
    print(f"HuggingFace load failed: {e}")
    print("Falling back to local CSV...")
    import pandas as pd
    df = pd.read_csv(os.path.join(MODEL_DIR, '..', 'data', 'Suicide_Detection.csv'))
    df.dropna(subset=['text', 'class'], inplace=True)
    texts  = df['text'].tolist()
    labels = df['class'].tolist()

print(f"Total rows: {len(texts)}")

# Balance classes (cap at 80k each to avoid RAM issues on 8 GB machines)
MAX_PER_CLASS = 80_000
pos_texts, neg_texts = [], []
for t, l in zip(texts, labels):
    if l == 'suicide' and len(pos_texts) < MAX_PER_CLASS:
        pos_texts.append(t)
    elif l != 'suicide' and len(neg_texts) < MAX_PER_CLASS:
        neg_texts.append(t)
    if len(pos_texts) >= MAX_PER_CLASS and len(neg_texts) >= MAX_PER_CLASS:
        break

all_texts  = pos_texts + neg_texts
all_labels = ['suicide'] * len(pos_texts) + ['non-suicide'] * len(neg_texts)
print(f"Balanced: {len(pos_texts)} suicide + {len(neg_texts)} non-suicide = {len(all_texts)} rows")

# ── VADER sentiment ───────────────────────────────────
print("\n=== VADER sentiment ===")
sia = SentimentIntensityAnalyzer()
compounds, negs, pos_scores = [], [], []
for i, t in enumerate(all_texts):
    sc = sia.polarity_scores(str(t))
    compounds.append(sc['compound'])
    negs.append(sc['neg'])
    pos_scores.append(sc['pos'])
    if (i + 1) % 20_000 == 0:
        print(f"  {i+1}/{len(all_texts)}")

# ── Preprocess ────────────────────────────────────────
print("\n=== Preprocessing text ===")
clean = [full_preprocess(t) for t in all_texts]

# ── TF-IDF (sparse) ───────────────────────────────────
print("\n=== TF-IDF (5000 features, trigrams, sparse) ===")
tfidf = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 3),
    min_df=3,
    sublinear_tf=True,
)
X_tfidf = tfidf.fit_transform(clean)   # sparse CSR matrix

# ── Append sentiment columns (still sparse) ───────────
X_sent = sp.csr_matrix(np.column_stack([compounds, negs, pos_scores]))
X = sp.hstack([X_tfidf, X_sent], format='csr')
y = np.array(all_labels)

print(f"Feature matrix: {X.shape}, nnz={X.nnz:,}, dtype={X.dtype}")

# ── Train / test split ────────────────────────────────
print("\n=== Train/test split ===")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y
)
print(f"Train: {X_train.shape[0]:,}  |  Test: {X_test.shape[0]:,}")

# ── Logistic Regression ───────────────────────────────
print("\n=== Training Logistic Regression ===")
lr = LogisticRegression(
    C=1.0, max_iter=1000, solver='saga',
    class_weight='balanced', n_jobs=-1, random_state=42,
)
lr.fit(X_train, y_train)

y_pred = lr.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"\nAccuracy: {acc*100:.2f}%")
print(classification_report(y_test, y_pred))

# ── Save ─────────────────────────────────────────────
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
joblib.dump(lr,    os.path.join(MODEL_DIR, 'risk_model.pkl'))
joblib.dump(tfidf, os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl'))
print(f"\nSaved risk_model.pkl + tfidf_vectorizer.pkl")
print(f"  Accuracy: {acc*100:.2f}%  |  {len(all_texts):,} samples  |  {ts}")
