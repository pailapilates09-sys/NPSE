"""Isolated schema on an explicitly provided disposable Postgres, never live input data."""
import os
import unittest
from uuid import uuid4
from datetime import datetime, timezone
from npse import database
from npse.research import build_research

@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Disposable TEST_DATABASE_URL required")
class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        from psycopg import sql
        from psycopg.conninfo import make_conninfo
        cls.url=os.environ["TEST_DATABASE_URL"]
        cls.original=os.environ.get("DATABASE_URL")
        cls.schema="npse_qa_"+uuid4().hex
        with psycopg.connect(cls.url) as c:
            c.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(cls.schema)))
        os.environ["DATABASE_URL"]=make_conninfo(cls.url,options="-c search_path="+cls.schema)
        database.migrate()
        cls.company={"symbol":"NABIL","company":"SYNTHETIC DATABASE QA ONLY","sector":"banks","profile":{},"market":{"price":170,"observed_at":"2026-09-30T15:00:00","turnover":2_000_000,"completed_session":True,"source_type":"nepse"}}
        database.persist_market([cls.company],{"observed_at":"2026-09-30T15:00:00"},"https://example.com/qa","2026-10-01T02:00:00Z")

    @classmethod
    def tearDownClass(cls):
        import psycopg
        from psycopg import sql
        with psycopg.connect(cls.url) as c:
            c.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(cls.schema)))
        if cls.original is None:os.environ.pop("DATABASE_URL",None)
        else:os.environ["DATABASE_URL"]=cls.original

    def test_migration_idempotent(self):
        database.migrate();self.assertEqual(database.status()["schema_version"],1)

    def test_market_upsert_preserves_newer_timestamp(self):
        old={**self.company,"market":{"price":1,"observed_at":"2026-09-30T14:00:00"}}
        database.persist_market([old],{"observed_at":"2026-09-30T14:00:00"},"https://example.com/qa","2026-10-01T02:00:00Z")
        _,_,prices,_=database.research_inputs()
        self.assertEqual(prices[0]["close"],170)
        self.assertEqual(prices[0]["observed_at"],"2026-09-30T09:15:00+00:00")

    def test_observation_deduplication_and_snapshot_roundtrip(self):
        from test_engine import observation, NOW
        r=observation("normalized_eps",30)
        database.import_observations([r,r])
        registered, observations, prices, actions=database.research_inputs()
        self.assertEqual(len(observations),1)
        self.assertEqual(observations[0]["value"],30)
        feed={"rows":[],"source":"SYNTHETIC QA ONLY","url":"https://example.com/qa","observed_at":None,"retrieved_at":NOW.isoformat()}
        board=build_research(feed,(registered,observations,prices,actions),NOW)
        database.persist_market(board["companies"],feed,feed["url"],feed["retrieved_at"])
        first=database.save_snapshot(board);second=database.save_snapshot(board)
        self.assertEqual(first,second)
        with database.connect() as c:
            saved=c.execute("SELECT payload FROM research_snapshots WHERE id=%s",(first,)).fetchone()["payload"]
            scores=c.execute("SELECT count(*) AS n FROM investment_scores WHERE snapshot_id=%s",(first,)).fetchone()["n"]
        self.assertEqual(saved["top3"],[]);self.assertEqual(scores,224)
