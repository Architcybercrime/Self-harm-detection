import re
import nltk

nltk.download('vader_lexicon')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


def clean_text(text):
    """Clean and normalize raw text input."""
    text = str(text).lower()
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def remove_stopwords(text):
    """Remove common words but keep negations."""
    stops = set(stopwords.words('english'))
    stops.discard('not')
    stops.discard('no')
    stops.discard('never')
    stops.discard('nobody')
    stops.discard('nothing')
    words = text.split()
    return ' '.join([w for w in words if w not in stops])


def lemmatize_text(text):
    """Reduce words to root form."""
    lem = WordNetLemmatizer()
    return ' '.join([lem.lemmatize(w) for w in text.split()])


def get_sentiment_scores(text):
    """Get VADER sentiment scores."""
    sia = SentimentIntensityAnalyzer()
    return sia.polarity_scores(text)


def full_preprocess(text):
    """Run complete preprocessing pipeline."""
    text = clean_text(text)
    text = remove_stopwords(text)
    text = lemmatize_text(text)
    return text


# ── TEST ─────────────────────────────────────────────
if __name__ == "__main__":
    test_sentences = [
        "I feel great today, everything is wonderful!",
        "Feeling a bit tired and stressed lately",
        "I feel completely hopeless, nobody cares about me",
        "I want to disappear and never come back"
    ]

    print("=" * 55)
    print("  PREPROCESSING + SENTIMENT TEST")
    print("=" * 55)

    for sentence in test_sentences:
        cleaned = full_preprocess(sentence)
        scores  = get_sentiment_scores(sentence)

        print(f"\nOriginal : {sentence}")
        print(f"Cleaned  : {cleaned}")
        print(f"Compound : {scores['compound']}  ", end="")

        if scores['compound'] <= -0.6:
            print("🔴 HIGH RISK")
        elif scores['compound'] <= -0.2:
            print("🟡 MEDIUM RISK")
        else:
            print("🟢 LOW RISK")