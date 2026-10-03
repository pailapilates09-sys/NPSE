# NPSE Investment Decision Engine v1.1

This release resumes `LANE-NPSE-WORK-20261001-003` from provider-verified
main `0bbdf7740a6d7c58b30bb167eebe59340fa6c938`. It consumes the existing
Research Corpus v1.1; it does not create another research corpus.

## Authority and reproducibility

`data/research-corpus-v1.1.json` preserves the live Source Manifest (37 sources),
original register and all six Parsed Knowledge tabs with provider IDs and
retrieval time. `npse/corpus.py` links sector rules and FormulaRegistry IDs to
calculations. Company filings receive supplemental filing IDs; they are not
misrepresented as additions to the 37-source methodological corpus.

Recovery path: corpus source ID/citation → SectorRules/FormulaRegistry →
`npse/models`, `formulas.py`, `valuation.py`, `decision.py` → API `rule_trace`,
`calculations`, `selected_evidence` → company evidence and methodology pages.
`/api/research?rules=1` reads the portable registry without fetching market data.
Normalization notes and sampled history URLs are deduplicated in API maps;
their reference IDs preserve recoverability while bounding response size.

## Calculation and evidence contract

- Business quality uses fixed quality 1/3, growth 1/4, financial strength 1/4,
  governance 1/6 weights. These are explicit NPSE choices, independent of
  valuation, momentum and liquidity. Missing weights are never redistributed.
- Percentiles require at least five fresh peers with matching periods, units,
  accounting bases, definitions and consolidation scopes.
- Source conflicts compare aligned observations only. Current unresolved
  conflicts block eligibility; prior-period conflicts remain separately counted.
  Subdomains and two YONEPSE transports do not establish independent agreement.
- Reported EPS/P/E remain separate from analyst-normalized EPS/P/E. Official
  current NEPSE evidence is required for normalized P/E, margin of safety and
  a positive investment state. Secondary data alone cannot clear this gate.
- Compound formulas reject mixed periods/bases, unit mismatches and nonpositive
  denominators. Capacity factor requires annual generation. Combined ratio
  requires a shared underwriting denominator. Hydro DCF uses remaining finite
  life with no automatic perpetual terminal value.
- Capital/liquidity/RBC compliance requires current primary review; historical
  research thresholds do not assert current legal requirements. Microfinance
  no longer inherits the bank 11% capital research limit.
- Hydro project-specific PPA/operating evidence, insurance NFRS 17/reserve and
  reinsurance reviews, and corporate-action review cannot be replaced by price
  momentum. Conditional catalysts are monitoring conditions, not observed facts.

## Connected evidence and ingestion

Reviewed July 2026 NRB reports cover 19 commercial banks and 49 microfinance
institutions. The extractor now includes CCAR/core capital, capital fund, bank
CD/net liquidity/SLR, and MFI borrowings/CRR/LAR/SLR where actually disclosed.
Regulatory ROE remains distinct from accounting ROE. `primary_refresh` checks
official downloadable PDFs against reviewed SHA-256 hashes before admission;
a changed report fails closed and requires another extraction review.

Protected POST actions at `/api/research` use the existing INGEST_TOKEN:
`primary_refresh`, `import`, `corporate_actions`, `backfill`, `archive`, `refresh`,
and read-only `audit`. No credentials belong in this repository or requests logs.
`audit` returns schema status, counts, source coverage and the latest persisted
snapshot identity. Schema 001 remains compatible; there is no gratuitous
migration or destructive historical rewrite.

Secondary connections are YONEPSE (discovery/observed quotes), Aabishkar2
(completed daily price history) and SocrateAI (dated archive corroboration).
The YONEPSE GitHub repository and Pages site are two transports of one source.
ShareSansar, MeroLagani and NepseAlpha are corpus/context references; their live
market/financial adapters are not connected. NIA/SEBON/DoED/NEA methodological
citations do not imply operational data feeds.

Corporate-action admission validates primary provenance and chronology.
Bonus/split and evidenced rights adjustments are point-in-time calculations;
a partial ledger never establishes complete adjusted history or total return.
Intraday secondary quotes no longer overwrite completed historical OHLCV.
Backtesting withholds outcomes without a point-in-time universe, historical
price authority and independently verified adjusted entry/forward prices.

## Product and bounded debt

The Decision Board leads with evidence-qualified 0–3 results. Preliminary
credit-quality comparisons identify deeper research priorities, with explicit
watch/wait states. Completed-session momentum analysis is under Diagnostics
(`/technical`) and company diagnostics, preserving the existing useful work.

Provider-access debt: supported official market-session feed; normalized
multi-period earning power and fuller same-sector filing depth; hydro PPA,
generation and debt evidence; insurance NFRS 17/reserve/underwriting depth;
complete corporate-action and delisted point-in-time history; operational
walk-forward validation; Vercel management connector scope. No performance or
fundamental conviction claim is issued to compensate for these gaps.

Rollback: `rollback/before-corpus-v1.1-20261003` at the predecessor commit.
Final provider/CI/database/deployment receipts are recorded in the governed
project audit checkpoint rather than inferred from this document.
