-- Helios canonical schema (v2). Single source of truth.
-- Retrieval: FTS5 keyword candidates + LLM rerank, with tier-aware reranker
-- (core/tiering.py). No vector DB dependency — that's an architectural wedge.

PRAGMA journal_mode = WAL;
PRAGMA user_version = 3;

CREATE TABLE IF NOT EXISTS memory_records (
    id                  TEXT    PRIMARY KEY,
    type                TEXT    NOT NULL CHECK(type IN ('event', 'state', 'summary', 'decision', 'observation')),
    content             TEXT    NOT NULL,
    metadata            TEXT    NOT NULL DEFAULT '{}',
    timestamp           REAL    NOT NULL,
    importance          REAL    NOT NULL DEFAULT 0.5,
    -- v2 tiering columns
    tier                TEXT    NOT NULL DEFAULT 'cold',
    temperature         REAL    NOT NULL DEFAULT 0.5,
    compression_cycles  INTEGER NOT NULL DEFAULT 0,
    read_count          INTEGER NOT NULL DEFAULT 0,
    last_accessed       REAL,
    -- v2 multi-tenant primitive
    namespace           TEXT    NOT NULL DEFAULT 'default'
);

CREATE INDEX IF NOT EXISTS idx_memory_records_type            ON memory_records(type);
CREATE INDEX IF NOT EXISTS idx_memory_records_timestamp       ON memory_records(timestamp);
CREATE INDEX IF NOT EXISTS idx_memory_records_importance      ON memory_records(importance);
CREATE INDEX IF NOT EXISTS idx_memory_records_tier            ON memory_records(tier);
CREATE INDEX IF NOT EXISTS idx_memory_records_last_accessed   ON memory_records(last_accessed);
CREATE INDEX IF NOT EXISTS idx_memory_records_namespace       ON memory_records(namespace);
CREATE INDEX IF NOT EXISTS idx_memory_records_temperature     ON memory_records(temperature);

-- FTS5 virtual table for keyword candidate generation.
CREATE VIRTUAL TABLE IF NOT EXISTS memory_records_fts USING fts5(
    content, content='memory_records', content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS memory_records_ai AFTER INSERT ON memory_records BEGIN
    INSERT INTO memory_records_fts(rowid, content) VALUES (new.rowid, new.content);
END;

CREATE TRIGGER IF NOT EXISTS memory_records_ad AFTER DELETE ON memory_records BEGIN
    INSERT INTO memory_records_fts(memory_records_fts, rowid, content) VALUES('delete', old.rowid, old.content);
END;

CREATE TRIGGER IF NOT EXISTS memory_records_au AFTER UPDATE ON memory_records BEGIN
    INSERT INTO memory_records_fts(memory_records_fts, rowid, content) VALUES('delete', old.rowid, old.content);
    INSERT INTO memory_records_fts(rowid, content) VALUES (new.rowid, new.content);
END;

CREATE TABLE IF NOT EXISTS chat_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT    NOT NULL,
    role       TEXT    NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content    TEXT    NOT NULL,
    timestamp  REAL    NOT NULL,
    metadata   TEXT    NOT NULL DEFAULT '{}',
    -- v2 multi-tenant primitive
    namespace  TEXT    NOT NULL DEFAULT 'default'
);

CREATE INDEX IF NOT EXISTS idx_chat_history_session_ts ON chat_history(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_chat_history_namespace  ON chat_history(namespace);

-- v2 audit log (per Glyph audit — closes B2D productization gap)
CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       REAL    NOT NULL DEFAULT (strftime('%s','now')),
    actor_ref       TEXT    NOT NULL,
    namespace       TEXT    NOT NULL DEFAULT 'default',
    action          TEXT    NOT NULL,
    target_kind     TEXT    NOT NULL,
    target_ref      TEXT,
    reason          TEXT,
    metadata        TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_log_namespace_ts ON audit_log(namespace, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_target       ON audit_log(target_kind, target_ref);

-- ─── v3: Multi-tenant control plane ─────────────────────────────────
-- Tenants + API keys for the hosted/multi-tenant deployment path.
-- A "default" tenant is bootstrapped for backward compat with single-tenant local-first.

CREATE TABLE IF NOT EXISTS tenants (
    id          TEXT    PRIMARY KEY,
    email       TEXT    UNIQUE NOT NULL,
    name        TEXT    NOT NULL,
    created_at  REAL    NOT NULL DEFAULT (strftime('%s','now')),
    status      TEXT    NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'suspended', 'deleted')),
    metadata    TEXT    NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_tenants_email  ON tenants(email);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);

CREATE TABLE IF NOT EXISTS api_keys (
    id           TEXT    PRIMARY KEY,
    tenant_id    TEXT    NOT NULL,
    key_hash     TEXT    NOT NULL UNIQUE,
    prefix       TEXT    NOT NULL,
    name         TEXT    NOT NULL DEFAULT 'default',
    created_at   REAL    NOT NULL DEFAULT (strftime('%s','now')),
    last_used_at REAL,
    revoked_at   REAL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash   ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(revoked_at) WHERE revoked_at IS NULL;

-- Bootstrap the default tenant (single-tenant local-first backward compat).
INSERT OR IGNORE INTO tenants (id, email, name, status, metadata)
VALUES ('default', 'local@helios.local', 'Local single-tenant', 'active', '{"is_local_default": true}');
