# NPSE How to use and Workspace v1.0

Routes: `/how-to`, `/workspace`; `/guide` redirects to `/how-to`.

This owner-requested learning addition explains the actual engine v1.1.0 release,
its evidence gates, database role and CSV/Sheets alternatives. It preserves the
financial engine, schema and admission rules. Guide pages render independently
of the research API so a failed data service does not hide the instructions.

The Workspace is built from `data/workspace-links.json`. Each stable entry has a
purpose, instructions, role/status and integration limit. Client search and category
filters operate on server-rendered anchors; no document contents or credentials
are published. Existing provider access permissions are unchanged.

The export component performs GET only after an explicit button click. It checks
the response, displays run and market-observation dates and exports either the
current board JSON or selected company evidence CSV with provenance. CSV fields
are quoted, and text beginning with spreadsheet formula markers is neutralized.
Exports are dated copies, not full database backups or an input/sync mechanism.
The JSON export does not contain server connection credentials.

Storage explanation distinguishes the live A9 v2.4 evidence/structured-file rule
from this release's Neon runtime store. There is no new ownership migration or
automatic Neon/GitHub/Sheets reconciliation. No new financial formulas, fake
observations, brokerage actions or performance claims are introduced.

Observed baseline on 2026-10-06: main `4e51577f13ebcdcc46a3bad7baf14a300014df77`,
engine v1.1.0, database CONNECTED/schema1, 224 securities, 71 with primary financials,
0 qualified candidates; market observation 2026-10-05. Historical implementation
counts remain labelled 2026-10-04 in the guide. Automatic NRB refresh503 is recorded
as last verified debt, not retried or claimed repaired in this learning change.

Rollback: `rollback/before-how-to-workspace-20261006` at the verified predecessor.
Publish on a candidate branch, build/typecheck, provider-read its blobs/tree and CI,
then promote via non-forced update to main. User owns final visual/taste QA.

Reference portal inspected through live GitHub: Paila-Pilates-SOP's `guide/index.html`,
`workspace/links.json` and `docs/workspace-directory.md`. NPSE links and explanatory
content are project-specific; no studio data or unrelated A8 controls are copied.
