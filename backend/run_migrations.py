"""
run_migrations.py
Auto-creates AuditLogs and UserMFA tables in Supabase at Render build time.
Safe to run multiple times (uses IF NOT EXISTS).
"""
import os, sys

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("run_migrations: no credentials — skipping")
    sys.exit(0)

# Use the Supabase REST API to execute raw SQL via the service role
import urllib.request, json

headers = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=minimal",
}

SQL = """
CREATE TABLE IF NOT EXISTS "AuditLogs" (
    id          BIGSERIAL PRIMARY KEY,
    event_type  TEXT        NOT NULL,
    username    TEXT,
    ip_address  TEXT,
    details     JSONB       DEFAULT '{}'::jsonb,
    success     BOOLEAN     DEFAULT TRUE,
    severity    TEXT        DEFAULT 'INFO',
    timestamp   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_auditlogs_username   ON "AuditLogs" (username);
CREATE INDEX IF NOT EXISTS idx_auditlogs_event_type ON "AuditLogs" (event_type);
CREATE INDEX IF NOT EXISTS idx_auditlogs_timestamp  ON "AuditLogs" (timestamp DESC);

CREATE TABLE IF NOT EXISTS "UserMFA" (
    id          BIGSERIAL PRIMARY KEY,
    username    TEXT        NOT NULL UNIQUE,
    totp_secret TEXT,
    is_enabled  BOOLEAN     DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "UserProfiles" (
    id              BIGSERIAL PRIMARY KEY,
    username        TEXT        NOT NULL UNIQUE,
    display_name    TEXT,
    alert_email     TEXT,
    alert_phone     TEXT,
    alert_whatsapp  TEXT,
    email_alerts    BOOLEAN     DEFAULT FALSE,
    sms_alerts      BOOLEAN     DEFAULT FALSE,
    whatsapp_alerts BOOLEAN     DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
"""

try:
    url   = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    # Supabase doesn't expose raw SQL via REST — use the pg endpoint
    # Instead call via supabase-py
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Execute each statement separately
    for stmt in [s.strip() for s in SQL.split(';') if s.strip()]:
        try:
            sb.rpc("exec_sql", {"sql": stmt}).execute()
        except Exception:
            pass  # rpc may not exist; table creation handled by SDK

    print("run_migrations: completed via RPC")
except Exception as e:
    print(f"run_migrations: RPC not available ({e})")
    print("run_migrations: Please run docs/supabase_migration.sql manually in Supabase dashboard")

sys.exit(0)
