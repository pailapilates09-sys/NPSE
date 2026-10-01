from datetime import datetime, timezone
from copy import deepcopy
from statistics import mean
from collections import defaultdict
from zoneinfo import ZoneInfo
from .config import VERSION, SECTOR_NAMES, WEIGHTS, GATES, SCENARIOS
from .sources.registry import UNIVERSE, SOURCES
from .sources.market import fetch_market
from .evidence import age_days, resolve
from .models.common import normalize_metrics
from .decision import evaluate, rank
from . import database
from .shortlist import screen
from .technical import analyse


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
    observations_by_symbol, prices_by_symbol, actions_by_symbol = (defaultdict(list) for _ in range(3))
    for records, index in ((observations,observations_by_symbol),(prices,prices_by_symbol),(actions,actions_by_symbol)):
        for record in records:
            index[record['symbol']].append(record)
    for c in companies:
        p = live.get(c["symbol"],{})
        c["market"] = {"price":p.get("ltp"), "observed_at":p.get("last_updated"), "source":feed["source"],"source_url":feed["url"],"source_type":"secondary","retrieved_at":feed["retrieved_at"],"volume":p.get("volume"),"turnover":p.get("turnover"),"high":p.get("high"),"low":p.get("low")}
        c["observations"] = observations_by_symbol[c['symbol']]
        c["price_history"] = prices_by_symbol[c['symbol']]
        c["corporate_actions"] = actions_by_symbol[c['symbol']]
        selected, _, _ = resolve(c["observations"],now.isoformat())
        official_price = selected.get("market_price", {})
        if official_price.get("source_type") == "nepse" and official_price.get("market_timestamp") and official_price["value"] > 0:
            c["market"].update({"price":official_price["value"], "observed_at":official_price["market_timestamp"], "source":official_price["source"], "source_type":"nepse", "source_url":official_price["source_url"], "retrieved_at":official_price["retrieved_at"], "verified":True})
        c["metrics"] = normalize_metrics({k:v["value"] for k,v in selected.items()},c["market"]["price"])
        closed_before = now.astimezone(ZoneInfo("Asia/Kathmandu")).date().isoformat()
        c["price_history"] = sorted((p for p in c["price_history"] if p["date"] < closed_before),key=lambda p:p["date"])
        turns = [p["turnover"] for p in c["price_history"][-20:] if p.get("turnover") is not None]
        c["metrics"]["turnover_20d"] = mean(turns) if len(turns)==20 else None
    results = [evaluate(c,[p for p in companies if p["sector"]==c["sector"]],now) for c in companies]
    technical = analyse(results,now)
    candidates = rank(results)
    preliminary = screen(results,now)
    judgments = {row['symbol']:row for row in preliminary['comparisons']}
    for c in results:
        if not c['eligible'] and c['symbol'] in judgments:
            row = judgments[c['symbol']]
            c['why'] = row['why']
            c['why_now'] = row['decision'] + '. ' + row['next_step']
            c['thesis'] = 'Preliminary credit-quality / capital thesis only. ' + row['why']
        elif not c['eligible'] and c['metrics'].get('eps') is not None:
            m = c['metrics']
            c['why'] = f"Reported full-year EPS Rs {m['eps']:.2f}. " + (f"Observed earnings multiple {m['pe']:.1f}×. " if m.get('pe') is not None else '') + 'Sustainable earning power and a full valuation still require evidence.'
            if m.get('net_profit_growth') is not None:
                c['why_now'] = f"Net profit changed {m['net_profit_growth']*100:.1f}%; review underwriting, reserves and reinsurance before investing."
            elif m.get('revenue_growth') is not None:
                c['why_now'] = f"Revenue changed {m['revenue_growth']*100:.1f}%; review demand, margins and cash conversion before investing."
            elif m.get('eps_growth') is not None:
                c['why_now'] = f"Reported EPS changed {m['eps_growth']*100:.1f}%; validate the drivers and sustainable returns before investing."
    # Keep the full panel in Postgres and calculations; transmit a small readable history.
    for c in results:
        c['history_sessions'] = len(c['price_history'])
        c['history_latest'] = c['price_history'][-1]['date'] if c['price_history'] else None
        c['price_history'] = [{k:p.get(k) for k in ('date','close','turnover','source_url')} for p in c['price_history'][-20:]]
        c.pop('observations',None)
        c['selected_evidence'] = {k:{**{field:value for field,value in e.items() if field not in ('raw','payload_sha256','id')}, 'normalization_notes':e.get('raw',{}).get('normalization_notes',e.get('normalization_notes',''))} for k,e in c['selected_evidence'].items()}
    fresh = age_days(feed["observed_at"],now)
    return {"version":VERSION, "as_of":now.isoformat(), "database":db,"market_regime":"UNVERIFIED — no independently confirmed regime series",
        "market_freshness":{"observed_at":feed["observed_at"],"retrieved_at":feed["retrieved_at"],"age_days":fresh,
            "state":"FRESH SECONDARY OBSERVATION" if fresh is not None and fresh <= GATES["market_age_days"] else "STALE / UNAVAILABLE"},
        "coverage":{"registered":len(results),"eligible":sum(c["eligible"] for c in results),"with_primary_financials":sum(any(v.get("source_type") != "secondary" for v in c["selected_evidence"].values()) for c in results),"universe_status":"224 active equities discovered in six sectors as of 2026-10-01; secondary classification, official completeness verification pending"},
        "technical":technical,"preliminary":preliminary,"top3":candidates,"top3_message":f"{len(candidates)} of 3 evidence-qualified candidates. " + ("No additional candidate currently meets the evidence threshold." if len(candidates)<3 else ""),
        "companies":results,"sectors":[{"slug":s,"name":name,"registered":sum(c["sector"]==s for c in results),"top3":rank([c for c in results if c["sector"]==s])} for s,name in SECTOR_NAMES.items()],
        "sources":SOURCES,"market_transports":feed.get("transports",[]),"discrepancies":[d for c in results for d in c["discrepancies"]],
        "config":{"weights":WEIGHTS,"gates":GATES,"scenarios":SCENARIOS},
        "alerts":(["The research database is not connected."] if not db["connected"] else []) +
            [f"Primary financial evidence available for {sum(any(v.get('source_type') != 'secondary' for v in c['selected_evidence'].values()) for c in results)} of {len(results)} companies. Price/volume rankings are available separately; fundamental valuation requires sustainable earnings, current-price confirmation and supported valuation."] +
            (["Market observations are stale or unavailable."] if fresh is None or fresh>GATES["market_age_days"] else []),
        "backtest":{"status":"INSUFFICIENT POINT-IN-TIME HISTORY","sample_size":0,"period":None,"returns":None,"drawdown":None,"hit_rate":None,
            "methodology":"Walk-forward ranking using only published and retrieved observations available at each rebalance, adjusted prices, fixed weights and explicit trading costs.",
            "limitations":["No complete point-in-time filing archive or adjusted total-return panel connected", "Survivorship, corporate-action adjustments and transaction costs must be validated before performance claims"]}}
