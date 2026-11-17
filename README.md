# NPSE Investment Decision Engine

**NPSE 09 is the working project.** Use [this repository](https://github.com/pailapilates09-sys/NPSE) for code and rules, the [Pages operating map](https://pailapilates09-sys.github.io/NPSE/) for navigation, and [09 Google Drive](https://drive.google.com/drive/folders/1UzBkzbPWxUbLaGD9fwVDS7y6tuazViLj) for editable research. The [Decision Board](https://npse-pailapilates09.vercel.app/) and Python API run on Vercel.

The research engine helps identify which companies merit deeper research, at what price and under what conditions, and what evidence would invalidate the thesis. The older market tracker is available at `/diagnostics`.

## Actual readiness

Six sector models, explainable scoring, scenario valuations, evidence gates and company-level provenance are implemented. The live research API reports database connectivity and evidence coverage. Official market confirmation, deeper normalized financial coverage and adjusted price history are still needed. A company only qualifies when it meets the evidence gates.

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

GitHub Actions tests the engine and publishes the static Pages site. The server app is deployed separately to the existing Vercel project. Verify the deployed commit and public runtime before claiming Vercel received a GitHub update. See the [09 hosting notes](docs/HOSTING_MIGRATION_09.md) for the boundary and rollback references.

GitHub holds source, tests and secondary discovery metadata. Live observations, financials, history, actions, features and snapshots belong in Postgres. Storage structures do not prove operational ingestion. See SOURCES.md and docs/READINESS.md.

## Working directory and recovery records

The [09 Workspace](https://pailapilates09-sys.github.io/NPSE/workspace/) links the verified working Docs, Sheets and tools. After editing `data/workspace-links.json`, run `python scripts/sync_workspace.py` to refresh the static Pages directory. The [October recovery record](docs/DRIVE_RECOVERY_09.md) preserves the historical context.
