from datetime import datetime, timezone
from .decision import evaluate, rank
from .evidence import resolve
from .models.common import normalize_metrics
from statistics import mean


def walk_forward(universe, rebalance_dates, forward_prices, costs=.005):
    outcomes = []
    for date in sorted(rebalance_dates):
        asof = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        point = []
        for c in universe:
            history = [p for p in c["price_history"] if p["date"] <= date]
            if not history: continue
            last = history[-1]
            selected,_,_=resolve(c.get("observations",[]),asof.isoformat())
            metrics=normalize_metrics({k:v["value"] for k,v in selected.items()},last["close"])
            turns=[p["turnover"] for p in history[-20:] if p.get("turnover") is not None]
            metrics["turnover_20d"]=mean(turns) if len(turns)==20 else None
            point.append({**c,"metrics":metrics,"price_history":history,"market":{**c.get("market",{}),"price":last["close"],"observed_at":date,"verified":bool(last.get("verified",False))}})
        evaluated = [evaluate(c,[p for p in point if p["sector"] == c["sector"]],asof) for c in point]
        picks = rank(evaluated)
        for c in picks:
            end = forward_prices.get((date,c["symbol"]))
            if end is not None and c["market"]["price"]>0:
                outcomes.append({"rebalance":date,"symbol":c["symbol"],"net_return":end/c["market"]["price"]-1-2*costs})
    return {"sample_size":len(outcomes),"outcomes":outcomes,"hit_rate":sum(o["net_return"]>0 for o in outcomes)/len(outcomes) if outcomes else None,
        "status":"RESEARCH SAMPLE" if outcomes else "INSUFFICIENT DATA","cost_per_side":costs,
        "limitations":"Forward prices must be independently adjusted and universe must include delisted securities. Holding-period observations are not a portfolio drawdown series."}
