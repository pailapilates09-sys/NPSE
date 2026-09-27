# NPSE Data Source Policy

## Authority order

1. **NEPSE official data** — target authority when a stable machine-readable path is available.
2. **YONEPSE** — current Phase 1 machine-readable adapter. It publishes JSON and documents its upstream sources.
3. **Independent market sites** — validation/cross-check only unless explicitly promoted after testing.
4. **Historical GitHub datasets** — bootstrap/backtest use; never treated as live authority without freshness checks.

## Phase 1 adapter

Base URL:

`https://shubhamnpk.github.io/yonepse`

Used endpoints:

- `/data/market/status.json`
- `/data/market/indices.json`
- `/data/market/summary.json`
- `/data/market/history.json`
- `/data/market/sector_indices.json`
- `/data/nepse_data.json`
- `/data/indices/manifest.json`
- `/data/indices/monthly/YYYY-MM.json`

## Provenance requirements

Every API response must expose:

- adapter name
- upstream base URL
- retrieval timestamp
- market observation timestamp when supplied upstream
- final historical-through date for index shards

Later database ingestion will also record raw payload hashes, normalization versions, discrepancy flags, and validation outcomes.

## Freshness

A green dashboard does not mean the exchange is open. The UI separately displays market-open status and the latest upstream observation time. Sector history may lag the intraday snapshot because finalized historical index shards can be published later.
