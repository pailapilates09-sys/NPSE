# Hosting migration to pailapilates09-sys

The original NPSE Git history and nine branches are preserved. The baseline is
`dd457c9a11f89df462fe93c0bbd126f0d7c783b9`; the pre-hosting rollback branch is
`rollback/before-09-hosting-20261009`.

- Source: https://github.com/pailapilates09-sys/NPSE
- Full app: https://npse-pailapilates09.vercel.app/
- GitHub Pages entry: https://pailapilates09-sys.github.io/NPSE/

GitHub Pages publishes the entry page and forwards deep links to the full app.
The Next.js app and Python research APIs run on Vercel, which supplies their
server runtime. Pages cannot replace that runtime.

The existing Vercel project `npse-control-tower` is retained to preserve its
authorized Neon/Postgres connection, observations, research snapshots, ingestion
authorization and daily cron configuration. Production deployments now take
their source from `pailapilates09-sys/NPSE`. Database migrations are not rerun and
credentials are not copied into GitHub. The Vercel project and database remain
in the existing provider account; this is a source and website migration, not
a transfer of provider account ownership.

GitHub Actions automatically republishes the Pages entry. For a full app update,
deploy the new `main` SHA to the existing Vercel project using its authenticated
deployment connection. Automatic Git-to-Vercel linking is a separate provider
setting. Do not remove the existing project or create a second empty database.

The original governance, research sources, daily journal, sector models,
uncertainty gates and learning pages are retained. Drive document links continue
to point to their original artifacts. Hosting migration does not turn historical
source evidence into current market data.
