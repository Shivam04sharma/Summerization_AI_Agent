-- ============================================================
-- Migration  : V3__add_deleted_by
-- Env        : local
-- Description: Add deleted_by to summary_configs
-- ============================================================

ALTER TABLE {schema}.summary_configs
    ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(128);
