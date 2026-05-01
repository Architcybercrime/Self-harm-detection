FROM python:3.11-slim

WORKDIR /app

# System deps needed by OpenCV, librosa, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data at build time so runtime has no network dependency
RUN python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"

COPY backend/ .

# Port injected by Render/Railway; default to 8000 locally
ENV PORT=8000
EXPOSE $PORT

CMD ["sh", "-c", "uvicorn main:socket_app --host 0.0.0.0 --port $PORT"]
