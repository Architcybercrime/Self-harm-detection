import re
import nltk
import os

# Download NLTK data safely — silently skip if filesystem is read-only (Render)
for _corpus in ('vader_lexicon', 'stopwords', 'wordnet', 'punkt', 'punkt_tab'):
    try:
        nltk.download(_corpus, quiet=True)
    except Exception:
        pass  # Read-only FS on Render — data was pre-downloaded at build time

try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    _sia = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except Exception:
    _sia = None
    VADER_AVAILABLE = False

try:
    from nltk.corpus import stopwords as _sw
    _STOPS = set(_sw.words('english')) - {'not', 'no', 'never', 'nobody', 'nothing'}
    STOPWORDS_AVAILABLE = True
except Exception:
    _STOPS = set()
    STOPWORDS_AVAILABLE = False

try:
    from nltk.stem import WordNetLemmatizer
    _lem = WordNetLemmatizer()
    LEMMATIZER_AVAILABLE = True
except Exception:
    _lem = None
    LEMMATIZER_AVAILABLE = False


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
    if not _STOPS:
        return text  # NLTK stopwords unavailable — skip step
    words = text.split()
    return ' '.join([w for w in words if w not in _STOPS])


def lemmatize_text(text):
    """Reduce words to root form."""
    if _lem is None:
        return text  # NLTK lemmatizer unavailable — skip step
    return ' '.join([_lem.lemmatize(w) for w in text.split()])


def get_sentiment_scores(text):
    """Get VADER sentiment scores. Returns neutral scores if VADER unavailable."""
    if _sia is None:
        return {'compound': 0.0, 'pos': 0.0, 'neg': 0.0, 'neu': 1.0}
    try:
        return _sia.polarity_scores(text)
    except Exception:
        return {'compound': 0.0, 'pos': 0.0, 'neg': 0.0, 'neu': 1.0}


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