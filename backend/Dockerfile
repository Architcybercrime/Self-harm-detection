FROM python:3.11-slim

WORKDIR /app

# System deps for opencv + audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "\
import nltk; \
nltk.download('vader_lexicon'); \
nltk.download('punkt'); \
nltk.download('punkt_tab'); \
nltk.download('stopwords'); \
nltk.download('wordnet')"

# Copy backend source
COPY . .

# Download ML models + run DB migrations
RUN python download_models.py && python run_migrations.py

EXPOSE 8000

CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "8000"]
