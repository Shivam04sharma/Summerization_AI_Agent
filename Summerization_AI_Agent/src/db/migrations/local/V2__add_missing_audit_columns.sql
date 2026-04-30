-- ============================================================
-- Migration  : V2__add_missing_audit_columns
-- Env        : local
-- Description: Add missing audit columns to summary_configs
-- ============================================================

ALTER TABLE {schema}.summary_configs
    ADD COLUMN IF NOT EXISTS deleted_at  TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS created_by  VARCHAR(128),
    ADD COLUMN IF NOT EXISTS updated_by  VARCHAR(128);
