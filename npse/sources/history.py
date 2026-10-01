"""Bounded secondary price-history ingestion; never an official-price confirmation."""
import csv
import io
import math
from datetime import date, datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from urllib.request import Request, urlopen

BASE = "https://raw.githubusercontent.com/Aabishkar2/nepse-data/main/data/company-wise/"
DEFAULT_SYMBOLS = ["NABIL", "CHCL", "SHIVM", "CBBL", "NLIC", "SICL"]


def parse_history(body, symbol, cutoff=None):
    cutoff = cutoff or date.today()
    records, rejected = {}, 0
    for raw in csv.DictReader(io.StringIO(body)):
        try:
            day = date.fromisoformat(raw["published_date"])
            if day >= cutoff:
                continue  # Never treat today's partial session as a historical close.
            values = {k: float(raw[src]) for k, src in {
                "high": "high", "low": "low", "close": "close",
                "volume": "traded_quantity", "turnover": "traded_amount"}.items()}
            if not all(math.isfinite(v) and v >= 0 for v in values.values()):
                raise ValueError("Invalid numeric field")
            if not 0 < values["low"] <= values["close"] <= values["high"] or values["volume"] <= 0:
                raise ValueError("Inconsistent trading range or no traded shares")
            if day.isoformat() in records:
                raise ValueError("Duplicate session")
            records[day.isoformat()] = {"symbol": symbol, "date": day.isoformat(), **values,
                "observed_at": day.isoformat()+"T15:00:00+05:45", "source_url": BASE+symbol+".csv"}
        except (ValueError, KeyError, TypeError):
            rejected += 1
    return [records[d] for d in sorted(records)[-200:]], rejected


def fetch_history(symbols=None):
    from .registry import UNIVERSE
    symbols = DEFAULT_SYMBOLS if symbols is None else symbols
    if not isinstance(symbols, list) or not 1 <= len(symbols) <= 10:
        raise ValueError("Provide 1 to 10 registered symbols")
    allowed = {s["symbol"] for s in UNIVERSE}
    if any(s not in allowed for s in symbols):
        raise ValueError("Unregistered history symbol")
    def read(symbol):
        url = BASE+symbol+".csv"
        try:
            with urlopen(Request(url, headers={"User-Agent":"NPSE-Research/1.0"}), timeout=8) as r:
                content = r.read(2_000_001)
            if len(content) > 2_000_000:
                raise ValueError("History file exceeds limit")
            rows, rejected = parse_history(content.decode("utf-8-sig"), symbol)
            return {"symbol":symbol, "rows":rows, "rejected":rejected,
                "latest": rows[-1]["date"] if rows else None, "source_url":url,
                "payload_sha256":sha256(content).hexdigest(), "error":None}
        except Exception:
            return {"symbol":symbol,"rows":[],"error":"History source unavailable or invalid", "source_url":url}
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(read, dict.fromkeys(symbols)))
    return {"retrieved_at":datetime.now(timezone.utc).isoformat(),"results":results}
