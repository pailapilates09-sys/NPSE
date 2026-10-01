CREATE TABLE IF NOT EXISTS schema_migrations (version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS securities (
 symbol text PRIMARY KEY, company text NOT NULL, sector text NOT NULL, security_type text NOT NULL DEFAULT 'ordinary_equity',
 profile jsonb NOT NULL DEFAULT '{}', updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS market_sessions (
 session_date date PRIMARY KEY, observed_at timestamptz NOT NULL, retrieved_at timestamptz NOT NULL, source_url text NOT NULL,
 nepse_close numeric, turnover numeric, payload jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_ohlcv (
 symbol text REFERENCES securities(symbol), session_date date NOT NULL, observed_at timestamptz NOT NULL,
 open numeric, high numeric, low numeric, close numeric NOT NULL, volume numeric, turnover numeric,
 adjusted_close numeric, source_url text NOT NULL, PRIMARY KEY(symbol, session_date)
);
CREATE TABLE IF NOT EXISTS index_history (
 code text NOT NULL, session_date date NOT NULL, close numeric NOT NULL, source_url text NOT NULL,
 PRIMARY KEY(code, session_date)
);
CREATE TABLE IF NOT EXISTS financial_periods (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, symbol text REFERENCES securities(symbol), reported_period text NOT NULL,
 period_end date NOT NULL, published_at timestamptz NOT NULL, UNIQUE(symbol, reported_period)
);
CREATE TABLE IF NOT EXISTS source_observations (
 id text PRIMARY KEY, symbol text REFERENCES securities(symbol), metric text NOT NULL, value numeric NOT NULL,
 unit text NOT NULL, reported_period text NOT NULL, period_end date NOT NULL, published_at timestamptz NOT NULL,
 market_timestamp timestamptz, retrieved_at timestamptz NOT NULL, source text NOT NULL, source_url text NOT NULL,
 source_type text NOT NULL, normalization_state text NOT NULL, validation_status text NOT NULL,
 raw jsonb NOT NULL, payload_sha256 text NOT NULL
);
CREATE INDEX IF NOT EXISTS observations_company_time ON source_observations(symbol,published_at);
CREATE TABLE IF NOT EXISTS source_discrepancies (
 id text PRIMARY KEY, symbol text REFERENCES securities(symbol), metric text NOT NULL, period text NOT NULL,
 status text NOT NULL, evidence jsonb NOT NULL, detected_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS corporate_actions (
 id text PRIMARY KEY, symbol text REFERENCES securities(symbol), action_type text NOT NULL,
 effective_date date, announced_at timestamptz NOT NULL, source_url text NOT NULL, payload jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS disclosures (
 id text PRIMARY KEY, symbol text REFERENCES securities(symbol), published_at timestamptz NOT NULL,
 source_url text NOT NULL, disclosure_type text NOT NULL, payload jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS research_snapshots (
 id text PRIMARY KEY, as_of timestamptz NOT NULL, engine_version text NOT NULL, config_sha256 text NOT NULL,
 universe_size integer NOT NULL, payload jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS valuation_runs (
 snapshot_id text REFERENCES research_snapshots(id), symbol text REFERENCES securities(symbol), payload jsonb NOT NULL,
 PRIMARY KEY(snapshot_id,symbol)
);
CREATE TABLE IF NOT EXISTS investment_scores (
 snapshot_id text REFERENCES research_snapshots(id), symbol text REFERENCES securities(symbol), quality numeric,
 timing numeric, confidence numeric NOT NULL, state text NOT NULL, payload jsonb NOT NULL,
 PRIMARY KEY(snapshot_id,symbol)
);
CREATE TABLE IF NOT EXISTS derived_features (
 symbol text REFERENCES securities(symbol), as_of timestamptz NOT NULL, version text NOT NULL, payload jsonb NOT NULL,
 PRIMARY KEY(symbol,as_of,version)
);
CREATE OR REPLACE VIEW income_statement_metrics AS SELECT * FROM source_observations WHERE metric IN ('revenue','ebitda','eps','normalized_eps','net_profit');
CREATE OR REPLACE VIEW balance_sheet_metrics AS SELECT * FROM source_observations WHERE metric IN ('book_value','debt','cash','shares','capital_adequacy');
CREATE OR REPLACE VIEW cash_flow_metrics AS SELECT * FROM source_observations WHERE metric IN ('fcf','fcfe','operating_cash_flow','capex','cash_conversion');
CREATE OR REPLACE VIEW bank_metrics AS SELECT o.* FROM source_observations o JOIN securities s USING(symbol) WHERE s.sector='banks';
CREATE OR REPLACE VIEW microfinance_metrics AS SELECT o.* FROM source_observations o JOIN securities s USING(symbol) WHERE s.sector='microfinance';
CREATE OR REPLACE VIEW hydro_project_metrics AS SELECT o.* FROM source_observations o JOIN securities s USING(symbol) WHERE s.sector='hydropower';
CREATE OR REPLACE VIEW insurance_metrics AS SELECT o.* FROM source_observations o JOIN securities s USING(symbol) WHERE s.sector IN ('life-insurance','non-life-insurance');
CREATE OR REPLACE VIEW dividends AS SELECT * FROM corporate_actions WHERE action_type='dividend';
CREATE OR REPLACE VIEW rights_issues AS SELECT * FROM corporate_actions WHERE action_type='rights_issue';
INSERT INTO schema_migrations(version) VALUES(1) ON CONFLICT DO NOTHING;
