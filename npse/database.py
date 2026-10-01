import os
import json
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def connect():
    import psycopg
    from psycopg.rows import dict_row
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    with psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as connection:
        yield connection


def status():
    if not os.environ.get("DATABASE_URL"):
        return {"state": "NOT CONFIGURED", "connected": False, "schema_version": None}
    try:
        with connect() as c:
            v = c.execute("SELECT max(version) AS version FROM schema_migrations").fetchone()["version"]
        return {"state": "CONNECTED" if v == 1 else "MIGRATION REQUIRED", "connected": v == 1, "schema_version": v}
    except Exception:
        return {"state": "UNAVAILABLE / MIGRATION REQUIRED", "connected": False, "schema_version": None}


def migrate():
    with connect() as c:
        c.execute(Path(__file__).resolve().parents[1].joinpath("migrations/001_research.sql").read_text())


def research_inputs():
    with connect() as c:
        securities = c.execute("SELECT * FROM securities ORDER BY symbol").fetchall()
        observations = c.execute("SELECT * FROM source_observations WHERE validation_status='validated' ORDER BY period_end").fetchall()
        prices = c.execute("SELECT * FROM daily_ohlcv ORDER BY session_date").fetchall()
        actions = c.execute("SELECT * FROM corporate_actions ORDER BY announced_at").fetchall()
    for row in observations:
        row["value"] = float(row["value"])
        for k in ("published_at", "retrieved_at", "period_end", "market_timestamp"):
            row[k] = row[k].isoformat() if row[k] is not None else None
    for row in prices:
        for k in ("open", "high", "low", "close", "volume", "turnover", "adjusted_close"):
            row[k] = float(row[k]) if row[k] is not None else None
        row["date"] = row.pop("session_date").isoformat()
        row["observed_at"] = row["observed_at"].isoformat()
    return securities, observations, prices, actions


def persist_market(companies, market, source_url, retrieved_at):
    from psycopg.types.json import Jsonb
    from .evidence import timestamp
    with connect() as c:
        for s in companies:
            c.execute("INSERT INTO securities(symbol,company,sector,profile) VALUES(%s,%s,%s,%s) ON CONFLICT(symbol) DO UPDATE SET company=EXCLUDED.company,sector=EXCLUDED.sector,profile=EXCLUDED.profile,updated_at=now()", (s["symbol"],s["company"],s["sector"],Jsonb(s.get("profile", {}))))
            p = s.get("market", {})
            if p.get("price") is not None and p.get("observed_at"):
                c.execute("INSERT INTO daily_ohlcv(symbol,session_date,observed_at,high,low,close,volume,turnover,source_url) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(symbol,session_date) DO UPDATE SET observed_at=EXCLUDED.observed_at,close=EXCLUDED.close,high=EXCLUDED.high,low=EXCLUDED.low,volume=EXCLUDED.volume,turnover=EXCLUDED.turnover,source_url=EXCLUDED.source_url WHERE EXCLUDED.observed_at >= daily_ohlcv.observed_at", (s["symbol"],p["observed_at"][:10],timestamp(p["observed_at"]),p.get("high"),p.get("low"),p["price"],p.get("volume"),p.get("turnover"),source_url))
        if market.get("observed_at"):
            c.execute("INSERT INTO market_sessions(session_date,observed_at,retrieved_at,source_url,payload) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(session_date) DO UPDATE SET observed_at=EXCLUDED.observed_at,retrieved_at=EXCLUDED.retrieved_at,source_url=EXCLUDED.source_url,payload=EXCLUDED.payload WHERE EXCLUDED.observed_at >= market_sessions.observed_at",(market["observed_at"][:10],timestamp(market["observed_at"]),timestamp(retrieved_at),source_url,Jsonb(market)))


def import_observations(rows):
    from hashlib import sha256
    from psycopg.types.json import Jsonb
    from .sources.registry import validate_observation, UNIVERSE
    from .evidence import timestamp
    validated = [validate_observation(r) for r in rows]
    with connect() as c:
        for s in UNIVERSE:
            c.execute("INSERT INTO securities(symbol,company,sector,profile) VALUES(%s,%s,%s,%s) ON CONFLICT(symbol) DO NOTHING",(s["symbol"],s["company"],s["sector"],Jsonb(s["profile"])))
        for r in validated:
            digest = sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()
            fields = ["symbol","metric","value","unit","reported_period","period_end","published_at","retrieved_at","source","source_url","source_type","normalization_state","validation_status","market_timestamp"]
            values = [timestamp(r.get(k)) if k in ("published_at","retrieved_at","market_timestamp") else r[k] for k in fields]
            c.execute("INSERT INTO source_observations(id,"+",".join(fields)+",raw,payload_sha256) VALUES("+",".join(["%s"]*17)+") ON CONFLICT(id) DO NOTHING", [digest]+values+[Jsonb(r),digest])
            c.execute("INSERT INTO financial_periods(symbol,reported_period,period_end,published_at) VALUES(%s,%s,%s,%s) ON CONFLICT(symbol,reported_period) DO NOTHING",(r["symbol"],r["reported_period"],r["period_end"],timestamp(r["published_at"])))
    return len(validated)


def persist_history(batch):
    """Insert secondary historical sessions without replacing existing provider records."""
    from .evidence import timestamp
    counts = []
    with connect() as c:
        for result in batch["results"]:
            rows = result["rows"]
            if rows:
                with c.cursor() as cursor:
                    cursor.executemany("INSERT INTO daily_ohlcv(symbol,session_date,observed_at,high,low,close,volume,turnover,source_url) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(symbol,session_date) DO NOTHING",
                        [(r["symbol"],r["date"],timestamp(r["observed_at"]),r["high"],r["low"],r["close"],r["volume"],r["turnover"],r["source_url"]) for r in rows])
            counts.append({k:v for k,v in result.items() if k != "rows"} | {"sessions_checked":len(rows)})
    return counts


def save_snapshot(board):
    from hashlib import sha256
    from psycopg.types.json import Jsonb
    from .config import GATES, WEIGHTS, SCENARIOS
    config_hash = sha256(json.dumps([GATES, WEIGHTS, SCENARIOS],sort_keys=True).encode()).hexdigest()
    payload = json.loads(json.dumps(board,default=str))
    run_id = sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    with connect() as c:
        c.execute("INSERT INTO research_snapshots VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",(run_id,board["as_of"],board["version"],config_hash,len(board["companies"]),Jsonb(payload)))
        for s in board["companies"]:
            c.execute("INSERT INTO valuation_runs VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",(run_id,s["symbol"],Jsonb(s["valuation"])))
            c.execute("INSERT INTO investment_scores VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",(run_id,s["symbol"],s["quality_score"],s["timing_score"],s["confidence"],s["state"],Jsonb(s["score_breakdown"])))
            c.execute("INSERT INTO derived_features VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",(s["symbol"],board["as_of"],board["version"],Jsonb(s["metrics"])))
            for discrepancy in s["discrepancies"]:
                key=sha256(json.dumps([s["symbol"],discrepancy],sort_keys=True,default=str).encode()).hexdigest()
                c.execute("INSERT INTO source_discrepancies(id,symbol,metric,period,status,evidence) VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",(key,s["symbol"],discrepancy["metric"],discrepancy["period"],discrepancy["status"],Jsonb(discrepancy)))
    return run_id
