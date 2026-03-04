-- ═══════════════════════════════════════════════════════════════════════════
-- APEX Trading System - Database Schema
-- ═══════════════════════════════════════════════════════════════════════════
-- PostgreSQL + TimescaleDB schema for time-series optimized storage
--
-- Usage:
--   psql -U apex_user -d apex -f db/init_schema.sql

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ═══════════════════════════════════════════════════════════════════════════
-- PRICE DATA (time-series optimized hypertable)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ticks (
    time        TIMESTAMPTZ NOT NULL,
    asset       TEXT NOT NULL,
    price       DOUBLE PRECISION,
    bid         DOUBLE PRECISION,
    ask         DOUBLE PRECISION,
    volume      DOUBLE PRECISION,
    source      TEXT DEFAULT 'binance'
);

-- Convert to hypertable (TimescaleDB magic)
SELECT create_hypertable('ticks', 'time', if_not_exists => TRUE);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_ticks_asset_time ON ticks (asset, time DESC);
CREATE INDEX IF NOT EXISTS idx_ticks_source ON ticks (source, time DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- FACTOR VALUES (computed signals)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS factor_values (
    time        TIMESTAMPTZ NOT NULL,
    asset       TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    value       DOUBLE PRECISION,
    z_score     DOUBLE PRECISION,
    metadata    JSONB
);

SELECT create_hypertable('factor_values', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_factors_asset_time ON factor_values (asset, time DESC);
CREATE INDEX IF NOT EXISTS idx_factors_name ON factor_values (factor_name, time DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- PATTERN OUTCOMES (for learning/backtesting)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS pattern_outcomes (
    time        TIMESTAMPTZ NOT NULL,
    asset       TEXT NOT NULL,
    market_id   TEXT,
    outcome     INTEGER,                    -- 1=YES resolved, 0=NO resolved
    polymarket_mid DOUBLE PRECISION,
    model_prob  DOUBLE PRECISION,
    edge        DOUBLE PRECISION,
    factor_snapshot JSONB                   -- Full factor state at prediction time
);

SELECT create_hypertable('pattern_outcomes', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_outcomes_asset ON pattern_outcomes (asset, time DESC);
CREATE INDEX IF NOT EXISTS idx_outcomes_market ON pattern_outcomes (market_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- TRADE EXECUTION LOG
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS trades (
    id          SERIAL PRIMARY KEY,
    time        TIMESTAMPTZ DEFAULT NOW(),
    asset       TEXT NOT NULL,
    market_id   TEXT,
    direction   TEXT,                       -- 'YES' or 'NO'
    size_usdc   DOUBLE PRECISION,
    entry_price DOUBLE PRECISION,
    exit_price  DOUBLE PRECISION,
    edge_at_entry DOUBLE PRECISION,
    pnl         DOUBLE PRECISION,
    regime_state INTEGER,                   -- 0=low, 1=med, 2=high volatility
    is_paper    BOOLEAN DEFAULT TRUE,
    explanation JSONB,                      -- Full context for explainability
    exit_time   TIMESTAMPTZ,
    status      TEXT DEFAULT 'open'         -- 'open', 'closed', 'cancelled'
);

CREATE INDEX IF NOT EXISTS idx_trades_time ON trades (time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_asset ON trades (asset, time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_market ON trades (market_id);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades (status, time DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- REGIME STATE HISTORY
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS regime_history (
    time        TIMESTAMPTZ NOT NULL,
    regime      INTEGER NOT NULL,           -- 0, 1, or 2
    volatility  DOUBLE PRECISION,
    confidence  DOUBLE PRECISION,           -- HMM posterior probability
    metadata    JSONB
);

SELECT create_hypertable('regime_history', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_regime_time ON regime_history (time DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- SOCIAL SIGNALS (Farcaster, news sentiment)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS social_signals (
    time        TIMESTAMPTZ NOT NULL,
    asset       TEXT NOT NULL,
    source      TEXT NOT NULL,              -- 'farcaster', 'twitter', 'news'
    sentiment   DOUBLE PRECISION,           -- [-1, 1]
    volume      INTEGER,                    -- Number of mentions
    keywords    TEXT[],
    raw_data    JSONB
);

SELECT create_hypertable('social_signals', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_social_asset_time ON social_signals (asset, time DESC);
CREATE INDEX IF NOT EXISTS idx_social_source ON social_signals (source, time DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- SYSTEM HEALTH / MONITORING
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS system_health (
    time        TIMESTAMPTZ DEFAULT NOW(),
    component   TEXT NOT NULL,              -- 'binance_ws', 'polymarket_api', etc.
    status      TEXT NOT NULL,              -- 'healthy', 'degraded', 'down'
    latency_ms  INTEGER,
    error_msg   TEXT,
    metadata    JSONB
);

SELECT create_hypertable('system_health', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_health_component ON system_health (component, time DESC);

-- ═══════════════════════════════════════════════════════════════════════════
-- DATA RETENTION POLICIES
-- ═══════════════════════════════════════════════════════════════════════════
-- Keep raw ticks for 30 days (downsample to 1-minute bars after that)
SELECT add_retention_policy('ticks', INTERVAL '30 days', if_not_exists => TRUE);

-- Keep factor values for 90 days
SELECT add_retention_policy('factor_values', INTERVAL '90 days', if_not_exists => TRUE);

-- Keep system health logs for 14 days
SELECT add_retention_policy('system_health', INTERVAL '14 days', if_not_exists => TRUE);

-- Keep trades and patterns forever (no retention policy)

-- ═══════════════════════════════════════════════════════════════════════════
-- CONTINUOUS AGGREGATES (for dashboard performance)
-- ═══════════════════════════════════════════════════════════════════════════
-- 1-minute OHLCV bars
CREATE MATERIALIZED VIEW IF NOT EXISTS ticks_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    asset,
    first(price, time) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price, time) AS close,
    sum(volume) AS volume
FROM ticks
GROUP BY bucket, asset;

-- Refresh policy: update every 1 minute
SELECT add_continuous_aggregate_policy('ticks_1min',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

-- Daily performance summary
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_performance
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    COUNT(*) AS total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS winning_trades,
    SUM(pnl) AS total_pnl,
    AVG(edge_at_entry) AS avg_edge,
    MAX(pnl) AS max_win,
    MIN(pnl) AS max_loss
FROM trades
WHERE status = 'closed'
GROUP BY day;

SELECT add_continuous_aggregate_policy('daily_performance',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ═══════════════════════════════════════════════════════════════════════════
-- HELPER FUNCTIONS
-- ═══════════════════════════════════════════════════════════════════════════
-- Calculate Sharpe ratio over time window
CREATE OR REPLACE FUNCTION calculate_sharpe(days INTEGER DEFAULT 30)
RETURNS DOUBLE PRECISION AS $$
DECLARE
    sharpe DOUBLE PRECISION;
BEGIN
    SELECT
        (AVG(daily_pnl) / NULLIF(STDDEV(daily_pnl), 0)) * SQRT(365)
    INTO sharpe
    FROM (
        SELECT
            DATE(time) AS date,
            SUM(pnl) AS daily_pnl
        FROM trades
        WHERE time > NOW() - (days || ' days')::INTERVAL
          AND status = 'closed'
        GROUP BY DATE(time)
    ) AS daily_returns;
    
    RETURN sharpe;
END;
$$ LANGUAGE plpgsql;

-- Get current drawdown
CREATE OR REPLACE FUNCTION current_drawdown()
RETURNS DOUBLE PRECISION AS $$
DECLARE
    peak DOUBLE PRECISION;
    current DOUBLE PRECISION;
    dd DOUBLE PRECISION;
BEGIN
    -- Get peak balance
    SELECT MAX(running_balance) INTO peak
    FROM (
        SELECT SUM(pnl) OVER (ORDER BY time) AS running_balance
        FROM trades
        WHERE status = 'closed'
    ) AS balances;
    
    -- Get current balance
    SELECT SUM(pnl) INTO current
    FROM trades
    WHERE status = 'closed';
    
    -- Calculate drawdown
    dd := (peak - current) / NULLIF(peak, 0);
    
    RETURN COALESCE(dd, 0);
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════════════════
-- GRANTS (adjust user as needed)
-- ═══════════════════════════════════════════════════════════════════════════
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO apex_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO apex_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO apex_user;

-- ═══════════════════════════════════════════════════════════════════════════
-- DONE
-- ═══════════════════════════════════════════════════════════════════════════
-- Schema initialized successfully!
-- Next: python main.py
