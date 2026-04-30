"""
upload_models.py
Run this ONCE locally after training to push model files to Supabase Storage.

Usage:
    cd backend
    python upload_models.py
"""

import os, sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BUCKET       = "models"
FILES        = ["model/risk_model.pkl", "model/tfidf_vectorizer.pkl"]

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")
    sys.exit(1)

from supabase import create_client
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create bucket if it doesn't exist
try:
    sb.storage.create_bucket(BUCKET, options={"public": False})
    print(f"Created bucket '{BUCKET}'")
except Exception:
    print(f"Bucket '{BUCKET}' already exists")

for filepath in FILES:
    if not os.path.exists(filepath):
        print(f"SKIP  {filepath} (not found locally)")
        continue

    dest = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        data = f.read()

    try:
        sb.storage.from_(BUCKET).remove([dest])
    except Exception:
        pass

    sb.storage.from_(BUCKET).upload(dest, data)
    size_mb = len(data) / 1024 / 1024
    print(f"OK    {filepath} → {BUCKET}/{dest}  ({size_mb:.1f} MB)")

print("\nDone. Render will download these during its next build.")
