# NPSE Investment Decision Engine

Release candidate **1.0.0-rc.1**, built on the existing Control Tower. The Decision Board is the homepage; the former market tracker is at `/diagnostics`.

## Actual readiness

Six sector models, explainable scoring, scenario valuations, timing/confidence gates, company/sector pages, provenance and Postgres schema are implemented. **This is not yet a finished investment-data service.** Authoritative financial ingestion, official market confirmation and live Postgres must be connected and verified. No positive ranking is issued from prices alone; performance results are withheld without point-in-time and adjusted outcome history.

The discovery registry contains 224 active equities across commercial banks, hydro, manufacturing, microfinance, life insurance and non-life insurance, using secondary metadata retrieved 2026-10-01. Official exchange completeness remains unverified. Official company-domain admission is initially registered for NABIL, CHCL, SHIVM, CBBL, NLIC and SICL; further company domains need verification.

## Local development and verification

```bash
npm ci
python -m pip install -r requirements.txt
python scripts/serve_api.py
# In another terminal:
DEV_PYTHON_API=1 npm run dev
# Verification:
npm run build
npm run typecheck
python -m unittest discover -s tests -v
```

Production uses Vercel Python functions. The local rewrite requires `DEV_PYTHON_API=1`. Financial calculations are implemented in reusable Python, not React. Three integration tests require an explicitly supplied disposable `TEST_DATABASE_URL`; they create/remove an isolated schema. GitHub Actions provides Postgres. Skipped tests are not a database pass. Synthetic fixtures remain in tests and are never loaded into production.

## Durable data

Configure the provider's authorized TLS `DATABASE_URL` and separate `INGEST_TOKEN` / `CRON_SECRET` values in Vercel. Never put credentials in source control or audit documents.

```bash
python scripts/manage.py migrate
python scripts/manage.py status
python scripts/manage.py import verified-observations.json
```

Public API: GET `/api/research`, `?symbol=NABIL`, `?sector=banks`. Protected POST requires `Authorization: Bearer <INGEST_TOKEN>` and either `{"action":"import","observations":[...]}` or `{"action":"refresh"}`. Cron GET `/api/refresh` requires `CRON_SECRET`. `vercel.json` requests daily 11:00 UTC refresh; actual scheduling and plan compatibility need provider verification. The public button rechecks evidence; it does not claim durable ingestion.

Every observation requires symbol, metric, finite value, unit, reported_period, Gregorian period_end, published_at, retrieved_at, source, HTTPS source_url, source_type, normalization_state `normalized` and validation_status `validated`. Source authority must match its registered domain. Ratios are fractions; per-share values use `NPR/share`. `normalized_eps` and `sustainable_roe` require `normalization_notes` documenting annualization, one-offs, diluted shares and sustainable assumptions. Reported EPS is never automatically used as normalized earning power. `market_price` requires NPR units, a positive value and `market_timestamp`; only admitted NEPSE authority clears the official-confirmation gate. Naive timestamps mean Nepal time (UTC+05:45). Observations are content-hashed and appended.

## Decision model

Quality uses same-sector midrank percentiles, 5th/95th clipping and at least five peers. Missing metrics contribute zero; weighted coverage below 80% withholds the score. Timing uses margin of safety (60), price versus the 50-session mean (20) and liquidity (20). Confidence uses critical coverage (25), primary filing coverage (25), financial freshness (15), market freshness (15), independent-source agreement (10) and historical depth (10). Provider labels and future evidence cannot increase agreement.

Positive states require all critical authoritative financials, official market confirmation, confidence ≥75, quality ≥65, timing ≥50, at least 50 price sessions, mean 20-session turnover ≥Rs 1 million, margin of safety ≥20%, no material conflict and no sector risk override. Market age over three calendar days or financial-period age over 160 days blocks eligibility, conservatively including holidays.

Banks/microfinance: justified P/B and normalized P/E. Hydro/manufacturing: EV-to-equity bridge, normalized P/E and FCFE DCF where supported. Hydro has finite project life and no perpetual terminal value. Life/non-life insurers have separate solvency/reserve/underwriting rules. At least two methods are required for a range. Scenario rates, multiples, haircuts, weights and gates are NPSE implementation choices, not investor prescriptions.

## Deployment and rollback

Reuse the existing GitHub-to-Vercel project. Verify CI, commit/deployment parity, APIs, representative companies in all six models and source-health states before declaring success. Rollback commit `615b14b865372ad758212525440b05ae7cd1ea7d` is preserved in `rollback/before-investment-engine-20261001`; deploying it should preserve subsequent history.

GitHub holds source, tests and secondary discovery metadata. Live observations, financials, history, actions, features and snapshots belong in Postgres. Storage structures do not prove operational ingestion. See SOURCES.md and docs/READINESS.md.
