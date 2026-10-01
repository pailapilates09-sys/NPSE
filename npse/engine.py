from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from statistics import mean

from .analytics import breadth, enrich_index_history, flatten_index_months, movers, pct_change, sector_performance
from .sources.yonepse import BASE_URL, fetch_json


def _summary_map(rows: list[dict]) -> dict[str, float]:
    return {str(r.get("detail", "")).strip(): float(r.get("value") or 0) for r in rows}


def build_dashboard() -> dict:
    core = {
        "status": "/data/market/status.json",
        "indices": "/data/market/indices.json",
        "summary": "/data/market/summary.json",
        "history": "/data/market/history.json",
        "live": "/data/nepse_data.json",
        "sector_meta": "/data/market/sector_indices.json",
        "manifest": "/data/indices/manifest.json",
    }
    with ThreadPoolExecutor(max_workers=len(core)) as pool:
        futures = {name: pool.submit(fetch_json, path) for name, path in core.items()}
        data = {name: future.result() for name, future in futures.items()}

    available_months = (data["manifest"].get("availableMonths") or [])[-4:]
    with ThreadPoolExecutor(max_workers=max(1, len(available_months))) as pool:
        month_futures = [pool.submit(fetch_json, f"/data/indices/monthly/{month}.json") for month in available_months]
        months = [f.result() for f in month_futures]

    nepse = next((x for x in data["indices"] if x.get("index") == "NEPSE Index"), {})
    summary = _summary_map(data["summary"])
    live = data["live"]
    market_history = sorted(data["history"], key=lambda r: r.get("businessDate", ""))
    turnover_history = [
        {"date": r.get("businessDate"), "turnover": float(r.get("totalTurnover") or 0)}
        for r in market_history[-60:]
    ]
    recent_turnover = [p["turnover"] for p in turnover_history[-20:] if p["turnover"] > 0]
    current_turnover = summary.get("Total Turnover Rs:")
    turnover_avg = mean(recent_turnover) if recent_turnover else None

    index_rows = flatten_index_months(months, "NEPSE")
    current_date = str(nepse.get("generatedTime") or "")[:10]
    current_index = nepse.get("currentValue")
    if current_date and current_index and (not index_rows or current_date > index_rows[-1]["date"]):
        index_rows.append({
            "date": current_date,
            "close": float(current_index),
            "open": float(current_index),
            "high": float(nepse.get("high") or current_index),
            "low": float(nepse.get("low") or current_index),
            "turnover": float(current_turnover or 0),
            "volume": 0.0,
            "trades": 0.0,
        })

    gainers, losers, turnover = movers(live)
    market_observed_at = nepse.get("generatedTime") or data["status"].get("last_checked")

    return {
        "market": {
            "is_open": bool(data["status"].get("is_open")),
            "index": float(current_index) if current_index is not None else None,
            "change": float(nepse.get("change")) if nepse.get("change") is not None else None,
            "percent_change": float(nepse.get("perChange")) if nepse.get("perChange") is not None else None,
            "turnover": current_turnover,
            "turnover_vs_20d_pct": pct_change(current_turnover, turnover_avg),
            "traded_scrips": summary.get("Total Scrips Traded"),
        },
        "breadth": breadth(live),
        "turnover_history": turnover_history,
        "index_history": enrich_index_history(index_rows),
        "sectors": sector_performance(months, data["sector_meta"]),
        "top_gainers": gainers,
        "top_losers": losers,
        "top_turnover": turnover,
        "provenance": {
            "adapter": "YONEPSE static JSON",
            "upstream": BASE_URL,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "market_observed_at": market_observed_at,
            "index_history_final_through": data["manifest"].get("finalizedThrough") or data["manifest"].get("latestDate"),
        },
    }

