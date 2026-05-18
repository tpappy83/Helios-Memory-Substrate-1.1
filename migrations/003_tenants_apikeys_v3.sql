-- Helios v0.3 — multi-tenant control plane schema migration
-- Target: helios-memory/migrations/003_tenants_apikeys_v3.sql
-- Applied via core.db.migrate_v2_to_v3() on startup when PRAGMA user_version < 3.
--
-- Adds:
--   1. tenants table (control plane)
--   2. api_keys table (control plane) with key_hash and prefix
--   3. Indexes for tenant lookup by id, api_keys lookup by hash, prefix
--
-- Does NOT add: schema-per-tenant routing (SQLite limitation — synthetic uses
-- logical namespace=tenant_id boundary; production Postgres deploy uses physical
-- schemas via search_path manipulation in core/tenants.py).
--
-- Per the research blueprint (§5.2): this migration EXPLICITLY VIOLATES wedge #1
-- (local-first single-binary) if the deployment is multi-tenant. The migration
-- is idempotent and safe to apply against existing single-tenant DBs — a
-- "default" tenant is bootstrapped to preserve backward compatibility.

BEGIN;

CREATE TABLE IF NOT EXISTS tenants (
    id          TEXT    PRIMARY KEY,    -- UUID
    email       TEXT    UNIQUE NOT NULL,
    name        TEXT    NOT NULL,
    created_at  REAL    NOT NULL DEFAULT (strftime('%s','now')),
    status      TEXT    NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'suspended', 'deleted')),
    metadata    TEXT    NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_tenants_email ON tenants(email);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);

CREATE TABLE IF NOT EXISTS api_keys (
    id           TEXT    PRIMARY KEY,                   -- UUID
    tenant_id    TEXT    NOT NULL,
    key_hash     TEXT    NOT NULL UNIQUE,               -- SHA-256 of full key
    prefix       TEXT    NOT NULL,                      -- First 12 chars, visible (like Stripe sk_live_AAA)
    name         TEXT    NOT NULL DEFAULT 'default',    -- User-facing label
    created_at   REAL    NOT NULL DEFAULT (strftime('%s','now')),
    last_used_at REAL,                                  -- Touched on each successful auth
    revoked_at   REAL,                                  -- NULL = active; set = revoked
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash         ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant       ON api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix       ON api_keys(prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_active       ON api_keys(revoked_at) WHERE revoked_at IS NULL;

-- Bootstrap a "default" tenant for backward compat with single-tenant local-first.
-- This tenant has NO API key by default; the local-first binary uses tenant_id="default"
-- without auth. Production multi-tenant deployments do NOT use this tenant.
INSERT OR IGNORE INTO tenants (id, email, name, status, metadata)
VALUES (
    'default',
    'local@helios.local',
    'Local single-tenant',
    'active',
    '{"is_local_default": true}'
);

PRAGMA user_version = 3;

COMMIT;
