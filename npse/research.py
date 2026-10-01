from datetime import datetime, timezone
from copy import deepcopy
from statistics import mean
from .config import VERSION, SECTOR_NAMES, WEIGHTS, GATES, SCENARIOS
from .sources.registry import UNIVERSE, SOURCES
from .sources.market import fetch_market
from .evidence import age_days, resolve
from .models.common import normalize_metrics
from .decision import evaluate, rank
from . import database


def build_research(market_feed=None, inputs=None, now=None):
    now = now or datetime.now(timezone.utc)
    feed = market_feed if market_feed is not None else fetch_market()
    db = database.status() if inputs is None else {"state":"TEST INPUTS", "connected":False}
    companies = deepcopy(UNIVERSE)
    observations, prices, actions = [], [], []
    if inputs is None and db["connected"]:
        try: inputs = database.research_inputs()
        except Exception: db = {"state":"READ FAILED","connected":False}
    if inputs is not None:
        registered, observations, prices, actions = inputs
        known = {c["symbol"] for c in companies}
        companies += [c for c in registered if c["symbol"] not in known and c["sector"] in SECTOR_NAMES]
    live = {p["symbol"]:p for p in feed["rows"]}
    for c in companies:
        p = live.get(c["symbol"],{})
        c["market"] = {"price":p.get("ltp"), "observed_at":p.get("last_updated"), "source":feed["source"],"source_url":feed["url"],"source_type":"secondary","retrieved_at":feed["retrieved_at"],"volume":p.get("volume"),"turnover":p.get("turnover"),"high":p.get("high"),"low":p.get("low")}
        c["observations"] = [o for o in observations if o["symbol"]==c["symbol"]]
        c["price_history"] = [p for p in prices if p["symbol"]==c["symbol"]]
        c["corporate_actions"] = [a for a in actions if a["symbol"]==c["symbol"]]
        selected, _, _ = resolve(c["observations"],now.isoformat())
        official_price = selected.get("market_price", {})
        if official_price.get("source_type") == "nepse" and official_price.get("market_timestamp") and official_price["value"] > 0:
            c["market"].update({"price":official_price["value"], "observed_at":official_price["market_timestamp"], "source":official_price["source"], "source_type":"nepse", "source_url":official_price["source_url"], "retrieved_at":official_price["retrieved_at"], "verified":True})
        c["metrics"] = normalize_metrics({k:v["value"] for k,v in selected.items()},c["market"]["price"])
        c["price_history"] = sorted((p for p in c["price_history"] if p["date"] <= now.date().isoformat()),key=lambda p:p["date"])
        turns = [p["turnover"] for p in c["price_history"][-20:] if p.get("turnover") is not None]
        c["metrics"]["turnover_20d"] = mean(turns) if len(turns)==20 else None
    results = [evaluate(c,[p for p in companies if p["sector"]==c["sector"]],now) for c in companies]
    candidates = rank(results)
    fresh = age_days(feed["observed_at"],now)
    return {"version":VERSION, "as_of":now.isoformat(), "database":db,"market_regime":"UNVERIFIED — no independently confirmed regime series",
        "market_freshness":{"observed_at":feed["observed_at"],"retrieved_at":feed["retrieved_at"],"age_days":fresh,
            "state":"FRESH SECONDARY OBSERVATION" if fresh is not None and fresh <= GATES["market_age_days"] else "STALE / UNAVAILABLE"},
        "coverage":{"registered":len(results),"eligible":sum(c["eligible"] for c in results),"with_primary_financials":sum(any(v.get("source_type") != "secondary" for v in c["selected_evidence"].values()) for c in results),"universe_status":"224 active equities discovered in six sectors as of 2026-10-01; secondary classification, official completeness verification pending"},
        "top3":candidates,"top3_message":f"{len(candidates)} of 3 evidence-qualified candidates. " + ("No additional candidate currently meets the evidence threshold." if len(candidates)<3 else ""),
        "companies":results,"sectors":[{"slug":s,"name":name,"registered":sum(c["sector"]==s for c in results),"top3":rank([c for c in results if c["sector"]==s])} for s,name in SECTOR_NAMES.items()],
        "sources":SOURCES,"market_transports":feed.get("transports",[]),"discrepancies":[d for c in results for d in c["discrepancies"]],
        "config":{"weights":WEIGHTS,"gates":GATES,"scenarios":SCENARIOS},
        "alerts":["Authoritative financial ingestion and Postgres connection must pass before a positive ranking."] + (["Market observations are stale or unavailable."] if fresh is None or fresh>GATES["market_age_days"] else []),
        "backtest":{"status":"INSUFFICIENT POINT-IN-TIME HISTORY","sample_size":0,"period":None,"returns":None,"drawdown":None,"hit_rate":None,
            "methodology":"Walk-forward ranking using only published and retrieved observations available at each rebalance, adjusted prices, fixed weights and explicit trading costs.",
            "limitations":["No complete point-in-time filing archive or adjusted total-return panel connected", "Survivorship, corporate-action adjustments and transaction costs must be validated before performance claims"]}}
