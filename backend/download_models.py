"""
download_models.py
Called by Render's build command to pull model files from Supabase Storage.
Silently skips if credentials or files are missing (app uses keyword fallback).
"""

import os, sys

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BUCKET       = "models"
FILES        = ["risk_model.pkl", "tfidf_vectorizer.pkl"]
OUT_DIR      = os.path.join(os.path.dirname(__file__), "model")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("download_models: no Supabase credentials — skipping")
    sys.exit(0)

os.makedirs(OUT_DIR, exist_ok=True)

try:
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"download_models: supabase import failed ({e}) — skipping")
    sys.exit(0)

all_ok = True
for fname in FILES:
    dest = os.path.join(OUT_DIR, fname)
    if os.path.exists(dest):
        print(f"EXISTS {fname}")
        continue
    try:
        data = sb.storage.from_(BUCKET).download(fname)
        with open(dest, "wb") as f:
            f.write(data)
        print(f"OK     {fname}  ({len(data)/1024/1024:.1f} MB)")
    except Exception as e:
        print(f"MISS   {fname}: {e}")
        all_ok = False

sys.exit(0 if all_ok else 1)
