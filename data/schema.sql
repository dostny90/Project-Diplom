-- PostgreSQL schema for CIC network flows and ML anomaly predictions.
-- Run from the repository root:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f data/schema.sql

CREATE TABLE IF NOT EXISTS network_flows (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flow_key         TEXT,
    observed_at      TIMESTAMPTZ,
    source_ip        INET,
    source_port      INTEGER CHECK (source_port BETWEEN 0 AND 65535),
    destination_ip   INET,
    destination_port INTEGER CHECK (destination_port BETWEEN 0 AND 65535),
    protocol         INTEGER,
    -- Dynamic CIC feature columns are kept in JSONB because train.py derives
    -- the feature list from the CSV each time it trains a model.
    features         JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw_label        TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS anomaly_predictions (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    flow_id     BIGINT NOT NULL REFERENCES network_flows(id) ON DELETE CASCADE,
    model_name  TEXT NOT NULL DEFAULT 'RandomForestClassifier',
    status      TEXT NOT NULL CHECK (status IN ('Normal', 'Anomaly')),
    is_anomaly  BOOLEAN NOT NULL,
    confidence  NUMERIC(5, 2) NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((status = 'Anomaly') = is_anomaly)
);

CREATE INDEX IF NOT EXISTS idx_network_flows_observed_at
    ON network_flows (observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_network_flows_destination
    ON network_flows (destination_ip, destination_port);
CREATE INDEX IF NOT EXISTS idx_network_flows_features
    ON network_flows USING GIN (features);
CREATE INDEX IF NOT EXISTS idx_anomaly_predictions_anomalies
    ON anomaly_predictions (created_at DESC)
    WHERE is_anomaly = TRUE;
CREATE INDEX IF NOT EXISTS idx_anomaly_predictions_flow_id
    ON anomaly_predictions (flow_id);
