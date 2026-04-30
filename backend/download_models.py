"""
download_models.py
Verifies model files exist at build time.
Files are committed to git, so this is just a sanity check.
Falls back to Supabase Storage if files are somehow missing.
"""

import os, sys

OUT_DIR = os.path.join(os.path.dirname(__file__), "model")
FILES   = ["risk_model.pkl", "tfidf_vectorizer.pkl"]

all_present = all(os.path.exists(os.path.join(OUT_DIR, f)) for f in FILES)

if all_present:
    for f in FILES:
        path = os.path.join(OUT_DIR, f)
        print(f"OK  {f}  ({os.path.getsize(path)/1024:.1f} KB)")
    print("Model files ready.")
    sys.exit(0)

# Fallback: try Supabase Storage
print("Model files missing from repo — attempting Supabase Storage download...")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
BUCKET       = "models"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("No Supabase credentials — app will use keyword fallback")
    sys.exit(0)

os.makedirs(OUT_DIR, exist_ok=True)
try:
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    for fname in FILES:
        dest = os.path.join(OUT_DIR, fname)
        if os.path.exists(dest):
            continue
        try:
            data = sb.storage.from_(BUCKET).download(fname)
            with open(dest, "wb") as f:
                f.write(data)
            print(f"Downloaded {fname} ({len(data)/1024:.1f} KB)")
        except Exception as e:
            print(f"Could not download {fname}: {e}")
except Exception as e:
    print(f"Supabase fallback failed: {e}")

sys.exit(0)
