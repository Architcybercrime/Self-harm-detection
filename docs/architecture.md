# System Architecture

## ML Pipeline Stages

### Stage 1: Data Ingestion
- Source: Kaggle Suicide Detection Dataset
- 232,074 samples, perfectly balanced classes
- Loaded via Pandas CSV reader

### Stage 2: Data Preprocessing
- Lowercase normalization
- URL and mention removal
- Stopword removal (keeping negations)
- Lemmatization via NLTK WordNetLemmatizer

### Stage 3: Feature Engineering
- TF-IDF Vectorization (5000 features, bigrams)
- VADER Sentiment Score (compound + negative)
- Combined feature matrix

### Stage 4: Model Training
- Compared: Logistic Regression vs Random Forest
- Best: Logistic Regression (91.8% accuracy)
- 5-Fold Cross Validation: 0.9142 F1

### Stage 5: Evaluation
- Accuracy: 91.8%
- Precision: 92%
- Recall: 92%
- F1-Score: 0.92
- Confusion matrix saved to docs/

### Stage 6: Deployment
- Flask REST API on port 5000
- Endpoints: /predict, /health, /stats, /monitor
- CORS enabled for frontend integration

### Stage 7: Monitoring
- Every prediction logged to JSON
- Drift detection on HIGH RISK rate
- Alert if rate exceeds 70% threshold