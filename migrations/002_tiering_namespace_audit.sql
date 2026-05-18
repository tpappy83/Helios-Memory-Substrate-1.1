-- Helios v0.2 NEXT — schema migration v1 → v2
-- Target: helios-memory/migrations/002_tiering_namespace_audit.sql
-- Applied via core.db.migrate_v1_to_v2() on startup when PRAGMA user_version < 2.
--
-- Adds:
--   1. Tiering columns on memory_records (per Volt's audit)
--   2. namespace column on memory_records + chat_history (per Whirl's multi-tenant)
--   3. Audit log table (per Glyph's productization gap)
--
-- Does NOT add: region, vector_summary, centroid_id, query_log table
-- (rejected as premature / wedge-incompatible per Quill's audit)
--
-- Idempotent? NO — SQLite does not support ADD COLUMN IF NOT EXISTS.
-- The migration runner in core/db.py checks PRAGMA user_version and only
-- runs this when version < 2; on success it bumps to user_version = 2.

BEGIN;

-- ─── memory_records: tiering columns ────────────────────────────────
ALTER TABLE memory_records ADD COLUMN tier               TEXT    NOT NULL DEFAULT 'cold';
ALTER TABLE memory_records ADD COLUMN temperature        REAL    NOT NULL DEFAULT 0.5;
ALTER TABLE memory_records ADD COLUMN compression_cycles INTEGER NOT NULL DEFAULT 0;
ALTER TABLE memory_records ADD COLUMN read_count         INTEGER NOT NULL DEFAULT 0;
ALTER TABLE memory_records ADD COLUMN last_accessed      REAL;

-- ─── memory_records: multi-tenant primitive ─────────────────────────
ALTER TABLE memory_records ADD COLUMN namespace          TEXT    NOT NULL DEFAULT 'default';

-- ─── chat_history: multi-tenant primitive ───────────────────────────
ALTER TABLE chat_history   ADD COLUMN namespace          TEXT    NOT NULL DEFAULT 'default';

-- ─── Indexes for tiering queries + namespace filters ────────────────
CREATE INDEX IF NOT EXISTS idx_memory_records_tier            ON memory_records(tier);
CREATE INDEX IF NOT EXISTS idx_memory_records_last_accessed   ON memory_records(last_accessed);
CREATE INDEX IF NOT EXISTS idx_memory_records_namespace       ON memory_records(namespace);
CREATE INDEX IF NOT EXISTS idx_chat_history_namespace         ON chat_history(namespace);
CREATE INDEX IF NOT EXISTS idx_memory_records_temperature     ON memory_records(temperature);

-- ─── Audit log (Glyph: lightweight productization primitive) ────────
CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       REAL    NOT NULL DEFAULT (strftime('%s','now')),
    actor_ref       TEXT    NOT NULL,    -- API key id, "system", or "default"
    namespace       TEXT    NOT NULL DEFAULT 'default',
    action          TEXT    NOT NULL,    -- "memory.write", "memory.delete", "config.update", ...
    target_kind     TEXT    NOT NULL,    -- "memory_record" | "config" | "chat_session" | ...
    target_ref      TEXT,                 -- ID of the affected resource, NULL for system events
    reason          TEXT,                 -- Free-form human-readable explanation
    metadata        TEXT                  -- JSON blob for context
);

CREATE INDEX IF NOT EXISTS idx_audit_log_namespace_ts ON audit_log(namespace, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_target       ON audit_log(target_kind, target_ref);

-- ─── Bump schema version ────────────────────────────────────────────
PRAGMA user_version = 2;

COMMIT;

-- Note: FTS5 virtual table memory_records_fts and its ai/ad/au triggers are
-- UNAFFECTED by this migration. None of the new columns are FTS-indexed.
-- If the user later wants to FTS-index `namespace` for cross-tenant search,
-- that's a separate v3 migration with a CREATE VIRTUAL TABLE rebuild.
