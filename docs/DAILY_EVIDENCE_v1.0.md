# NPSE Daily Evidence v1.0

This release resolves A8 navigation and the old Blob-download implementation, and adds five readable source channels plus a manually reviewed company event. Engine 1.1.0 and schema 1 remain unchanged.

## Ownership and update contract

- `data/daily-sources.json`: current channel directory; checked dates are historical checks, not live health.
- `data/daily-evidence.jsonl`: append-only qualitative event history. Preserve publication and retrieval dates separately; retain original BS dates when conversion is unverified.
- Corrections append a new unique event ID with `supersedes` pointing to an earlier ID. Earlier entries remain visible in history; company context excludes superseded entries.
- Facts, interpretations, confirmation questions and decision effects stay separate. A secondary headline cannot become validated financial data, sustainable earnings or a buy recommendation.
- `/daily`, the Decision Board context and relevant company context render the journal. No automatic daily news job, Slack notification or journal-to-Neon financial admission was added.
- Existing protected market cron remains separate. A schedule does not prove a run succeeded.

## Daily operator procedure

Read current GitHub head and journal history. Read the five channels once; inspect new material documents rather than recrawling the corpus. Match issuer, event date, financial period, unit and accounting definition. Corroborate consequential secondary claims against primary evidence. Append a short paraphrase and original URL, source ID, retrieval time, interpretation, confirmation tasks and invalidation conditions. Record no-new-evidence checks in the audit receipt when applicable. Use a candidate branch, tests and provider readback before promotion. Save a research snapshot through the existing protected persistence path only after inputs validate. Do not manufacture performance or conviction from news sentiment.

Use each issuer’s actual filing rather than substituting EBL for the whole universe. NRB is relevant to banks/microfinance, SEBON to disclosures, NEA to hydropower context, and ShareSansar to event discovery. Insurance still requires NIA and issuer disclosures.

## Export contract

GET `/api/research?download=csv` returns a UTF-8 BOM CSV attachment containing selected company observations and provenance. GET `?download=json` returns a JSON attachment of a newly computed board. Both are read-only, no-store, with fixed filenames and no database writes. Each request recomputes the board; its timestamp can differ from the status previously shown. Invalid/mixed export queries fail before fetching providers. CSV cells neutralize spreadsheet formulas while preserving numeric negatives. Exported data is a copy, not a full historical database backup.

## A8 scope and bounded debt

The live A8 routing governs this locally owned NPSE project. Older A9 names remain historical provenance. External Fabin Main federation is separate and was not requested for this run; keep its existing cursor rather than inventing an ACK.

Known evidence debt remains: authoritative current market observations; normalized sustainable earnings and comparable peers; hydro PPA/COD/generation/debt/project-life data; insurance solvency/reserves/NFRS 17 normalization; verified corporate actions and complete point-in-time survivorship coverage. NRB’s public archive is readable in research, but the runtime downloader timed out in the bounded local probe; no new values were admitted. NIA’s financial-statement index was discovered, but direct retrieval failed. No validated investment performance is claimed.

The selected GitHub connector exposes branch/commit operations but no annotated-tag/GitHub-Release mutation. The exact commit and preserved rollback branch identify this release; immutable tag/Release remains a bounded capability debt unless completed through an authorized provider operation.

## Rollback

Restore the prior verified commit `1629054b45a5b2eaa976fb5830bb422b86a9e411` from `rollback/before-a8-daily-evidence-20261006` if a live regression is found. The run does not migrate schema, rewrite the research corpus, lower qualification gates or mutate external Main.
