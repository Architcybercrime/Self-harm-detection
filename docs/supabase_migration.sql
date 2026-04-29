-- ============================================================
-- SafeSignal — Supabase Migration
-- Run this in the Supabase SQL editor ONCE to create the two
-- new tables required by the audit-log and MFA features.
-- ============================================================

-- ── AuditLogs ────────────────────────────────────────────────
-- Stores every security event (logins, failures, predictions, etc.)
CREATE TABLE IF NOT EXISTS "AuditLogs" (
    id          BIGSERIAL PRIMARY KEY,
    event_type  TEXT        NOT NULL,
    username    TEXT,
    ip_address  TEXT,
    details     JSONB       DEFAULT '{}'::jsonb,
    success     BOOLEAN     DEFAULT TRUE,
    severity    TEXT        DEFAULT 'INFO'
                            CHECK (severity IN ('INFO','WARNING','CRITICAL')),
    timestamp   TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups by user or event type
CREATE INDEX IF NOT EXISTS idx_auditlogs_username   ON "AuditLogs" (username);
CREATE INDEX IF NOT EXISTS idx_auditlogs_event_type ON "AuditLogs" (event_type);
CREATE INDEX IF NOT EXISTS idx_auditlogs_timestamp  ON "AuditLogs" (timestamp DESC);

-- Row-Level Security: only the service-role key (backend) can insert/read
ALTER TABLE "AuditLogs" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_only" ON "AuditLogs"
    USING (auth.role() = 'service_role');


-- ── UserMFA ──────────────────────────────────────────────────
-- Stores per-user TOTP secrets and enabled state
CREATE TABLE IF NOT EXISTS "UserMFA" (
    id          BIGSERIAL PRIMARY KEY,
    username    TEXT        NOT NULL UNIQUE,
    totp_secret TEXT,
    is_enabled  BOOLEAN     DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE "UserMFA" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_only" ON "UserMFA"
    USING (auth.role() = 'service_role');

-- Auto-update updated_at on any row change
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_usermfa_updated_at
    BEFORE UPDATE ON "UserMFA"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
