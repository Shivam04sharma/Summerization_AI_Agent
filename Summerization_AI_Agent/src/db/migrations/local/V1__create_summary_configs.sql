-- ============================================================
-- Migration  : V1__create_summary_configs
-- Env        : local
-- Description: Create schema and summary_configs table
-- Note       : {schema} is replaced at runtime from DB_SCHEMA env var
-- ============================================================

CREATE SCHEMA IF NOT EXISTS {schema};

CREATE TABLE IF NOT EXISTS {schema}.summary_configs (
    id           SERIAL          PRIMARY KEY,
    key          VARCHAR(50)     UNIQUE NOT NULL,
    label        VARCHAR(100)    NOT NULL,
    intent       VARCHAR(50)     NOT NULL,
    format       VARCHAR(50)     NOT NULL,
    min_words    INT             NOT NULL,
    max_words    INT             NOT NULL,
    instruction  TEXT            NOT NULL,
    style_hint   TEXT,
    is_default   BOOLEAN         NOT NULL DEFAULT FALSE,
    is_active    BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
