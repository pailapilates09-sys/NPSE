# NPSE Control Tower

A source-traceable Nepal Stock Exchange research dashboard. GitHub holds the application and analytics code; Vercel runs the Next.js frontend and Python data functions. A database layer can be added after the first live deployment is verified.

## Phase 1

- Live/near-live market snapshot from machine-readable NEPSE-derived sources
- NEPSE index level and session change
- Turnover trend and 20-session comparison
- Market breadth (advancers / decliners / unchanged)
- Top gainers, losers, and turnover leaders
- Sector 1D / 5D / 20D relative performance from historical index shards
- Source timestamps and provenance on every dashboard response

## Architecture

```text
NEPSE / public market sources
        |
        v
Python source adapters (npse/)
        |
        v
Vercel Python Function (/api/dashboard)
        |
        v
Next.js dashboard (app/)
        |
        v
Vercel production deployment
```

GitHub is **not** used as the live market database. Later phases will add Postgres/Neon for durable observations, validation history, derived features, and research runs.

## Current upstream

Phase 1 uses the public YONEPSE static JSON API as a machine-readable adapter. YONEPSE documents its own upstreams as NEPSE Official API plus secondary sources. NPSE Control Tower keeps the upstream path and observation timestamps visible so we can cross-check and replace adapters without rewriting the dashboard.

See [SOURCES.md](SOURCES.md).

## Local development

```bash
npm install
npm run dev
```

The frontend calls `/api/dashboard`, implemented in Python at `api/dashboard.py`.

## Deploy on Vercel

1. Import `pailapilates10-cmd/NPSE-Control-Tower` into Vercel.
2. Keep the framework preset as Next.js.
3. No environment variables are required for Phase 1.
4. Deploy.
5. Verify `/api/dashboard` first, then the homepage.

Vercel supports Python Functions on all plans. This repository intentionally uses the standard-library HTTP client for the first deployment so the Python bundle stays small.

## Research rule

The dashboard is for evidence and research, not trade execution. New analysis requests should become reproducible calculations and visualizations in this repository rather than one-off chat answers.

## Status

**Phase 1 bootstrap** — data adapter + analytics API + first live dashboard.
