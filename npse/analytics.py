from __future__ import annotations

from statistics import mean


def pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current / previous - 1) * 100


def simple_moving_average(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    for i in range(len(values)):
        if i + 1 < window:
            out.append(None)
        else:
            out.append(mean(values[i + 1 - window : i + 1]))
    return out


def breadth(rows: list[dict]) -> dict:
    changes = [float(r.get("percent_change", 0) or 0) for r in rows if (r.get("volume") or 0) > 0]
    advancers = sum(1 for x in changes if x > 0)
    decliners = sum(1 for x in changes if x < 0)
    unchanged = sum(1 for x in changes if x == 0)
    ratio = advancers / decliners if decliners else None
    return {"advancers": advancers, "decliners": decliners, "unchanged": unchanged, "ratio": ratio}


def movers(rows: list[dict], limit: int = 8) -> tuple[list[dict], list[dict], list[dict]]:
    cleaned = []
    for row in rows:
        if not row.get("symbol") or not isinstance(row.get("ltp"), (int, float)) or (row.get("volume") or 0) <= 0:
            continue
        cleaned.append({
            "symbol": row.get("symbol"),
            "name": row.get("name") or row.get("symbol"),
            "ltp": float(row.get("ltp") or 0),
            "percent_change": float(row.get("percent_change") or 0),
            "turnover": float(row.get("turnover") or 0),
        })
    gainers = sorted(cleaned, key=lambda r: r["percent_change"], reverse=True)[:limit]
    losers = sorted(cleaned, key=lambda r: r["percent_change"])[:limit]
    turnover = sorted(cleaned, key=lambda r: r["turnover"], reverse=True)[:limit]
    return gainers, losers, turnover


def flatten_index_months(months: list[dict], code: str) -> list[dict]:
    by_date: dict[str, dict] = {}
    for month in months:
        dates = month.get("dates") or []
        rows = (month.get("series") or {}).get(code) or []
        for row in rows:
            if not row or not isinstance(row[0], int) or row[0] >= len(dates):
                continue
            date = dates[row[0]]
            by_date[date] = {
                "date": date,
                "close": float(row[1]),
                "open": float(row[2]),
                "high": float(row[3]),
                "low": float(row[4]),
                "turnover": float(row[5]),
                "volume": float(row[6]),
                "trades": float(row[7]),
            }
    return [by_date[d] for d in sorted(by_date)]


def enrich_index_history(rows: list[dict], limit: int = 90) -> list[dict]:
    rows = rows[-limit:]
    closes = [r["close"] for r in rows]
    sma20 = simple_moving_average(closes, 20)
    sma50 = simple_moving_average(closes, 50)
    return [
        {"date": row["date"], "close": row["close"], "sma20": sma20[i], "sma50": sma50[i]}
        for i, row in enumerate(rows)
    ]


def sector_performance(months: list[dict], metadata: list[dict]) -> list[dict]:
    names = {m.get("indexCode"): m.get("indexName") for m in metadata}
    excluded = {"NEPSE", "SENSIND", "FLOATIND", "SENSFLTIND"}
    all_codes = set()
    for month in months:
        all_codes.update((month.get("series") or {}).keys())

    output = []
    for code in sorted(all_codes):
        if code in excluded:
            continue
        rows = flatten_index_months(months, code)
        closes = [r["close"] for r in rows]
        if len(closes) < 2:
            continue
        def ret(sessions: int):
            if len(closes) <= sessions:
                return None
            return pct_change(closes[-1], closes[-1 - sessions])
        output.append({
            "code": code,
            "name": names.get(code) or code,
            "latest_date": rows[-1]["date"],
            "return_1d": ret(1),
            "return_5d": ret(5),
            "return_20d": ret(20),
        })
    return output

