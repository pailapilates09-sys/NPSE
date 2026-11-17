# NPSE 09 — Buy, Sell, Why

**[Open the decision board](https://pailapilates09-sys.github.io/NPSE/).**

- **Buy:** See which shares pass the evidence and entry-price checks, or why to wait.
- **Sell:** Pick a ticker you hold and see what evidence would warrant a sell or trim review.
- **Why:** Check the market observation date, official quote coverage and primary financial evidence.

The public site is one page. GitHub Actions tests the engine and publishes the site. The board uses a dated, read-only projection of the existing [research API](https://npse-pailapilates09.vercel.app/api/research); it withholds price-based decisions when the evidence or snapshot is stale. The private Drive journal is for your notes.

## Run and publish

- Run the Python tests with `python -m unittest discover -s tests -v`. GitHub CI supplies a test PostgreSQL database and also runs the Next.js build.
- Refresh the tracked fallback snapshot with `python scripts/publish_decisions.py --output pages/data/decisions.json`. The Pages workflow also tries to refresh the snapshot when it publishes.
- Serve the page locally with `python -m http.server --directory pages 8001`.
- Publish a reviewed commit through `main`, or use the Pages workflow's manual trigger to refresh the public data. [View Actions](https://github.com/pailapilates09-sys/NPSE/actions).

Vercel supplies the research API and its connected PostgreSQL. Deploy the same GitHub revision to the existing Vercel project to retire its old frontend routes. Verify the old Workspace redirects here and the API still responds. A GitHub Pages run does not deploy Vercel.

The pre-reset site and repository are preserved in the private 09 Drive archive and at the `rollback/before-buy-sell-why-20261117` branch. [Source definitions](SOURCES.md) and [engine notes](docs/CORPUS_IMPLEMENTATION_v1.1.md) remain in the repository.
