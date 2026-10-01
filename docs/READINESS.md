# Release candidate readiness

This milestone must not be labeled FINAL_CLOSED_PASS.

Implemented: Decision Board; diagnostics separation; six sector models; explainable quality/timing/confidence; valuations; entry/monitor/invalidation/exit reasoning; stale/conflict blocks; 224-company discovery; all requested pages; Postgres schema, protected admissions and refresh; cron configuration; engine tests and isolated Postgres test suite.

Remaining debt:

1. Authorized production Postgres/Neon and Vercel secrets, migration, durable ingestion/readback and persistence verification. Schema availability does not mean connected storage.
2. Current primary filings and validated earning-power assumptions for sufficient sector peers. Six official company domains are registered; further domain registrations require verification.
3. Official market-price confirmation. Current YONEPSE transports are secondary and cannot clear this gate.
4. Verified daily backfill, index/regime series, corporate actions and disclosures. Tables exist, but extraction/backfill/adjustment pipelines are incomplete. Regime remains unverified.
5. Nirmal Pradhan transcript extraction and principle verification.
6. Existing Vercel management authorization. Connector currently sees no projects. GitHub deployment statuses/public-domain checks provide narrower evidence, not secret or runtime-log access.
7. Historical cohort comparison and adjusted returns/drawdowns before performance claims.
8. A9 lane → Local → Main terminal closeout only when the actual product/production conditions pass. An OPEN checkpoint is not a finished closeout.

QA must distinguish build/type/engine passes, skipped Postgres tests, local HTTP route checks and real browser/production checks. Manual valuation fixtures are synthetic and do not satisfy verification against an authoritative company filing.
