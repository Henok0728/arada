-- Lodge-Link Database Initialization
-- Creates required extensions. Schema tables are created via Alembic migrations.
-- See docs/Lodge-Link_Implementation_Plan.md § 1.2 for schema design rationale.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Platform schema (shared, Lodge-Link managed)
CREATE SCHEMA IF NOT EXISTS platform;

-- Grant the app user access to platform schema
-- Individual hotel schemas (hotel_{slug}) are created during KYC onboarding
COMMENT ON SCHEMA platform IS 'Shared platform schema — Lodge-Link managed. See Implementation Plan § 1.2.';
