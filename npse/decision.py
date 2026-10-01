from statistics import mean
from urllib.parse import urlparse
from .config import GATES, WEIGHTS
from .models import MODELS
from .models.common import number, percentile, normalize_metrics
from .evidence import resolve, age_days
from .valuation import value_company


def evaluate(company, sector_peers, now=None):
    model = MODELS[company["sector"]]
    selected, discrepancies, rejected = resolve(company.get("observations", []), now.isoformat() if now else None)
    market = company.get("market", {})
    metrics = normalize_metrics({k:v["value"] for k,v in selected.items()}, market.get("price"))
    history = sorted((p for p in company.get("price_history", []) if now is None or p["date"] <= now.date().isoformat()), key=lambda p:p["date"])
    closes = [p["close"] for p in history if number(p.get("close")) is not None and (now is None or p["date"] <= now.date().isoformat())]
    turnovers = [p["turnover"] for p in history[-20:] if number(p.get("turnover")) is not None]
    metrics["turnover_20d"] = mean(turnovers) if len(turnovers) == 20 else None
    critical = model["critical"] + ["normalized_eps"]
    if company["sector"] in ("banks", "microfinance", "life-insurance", "non-life-insurance"):
        critical += ["sustainable_roe"]
    missing = [k for k in critical if number(metrics.get(k)) is None]
    coverage = 1-len(missing)/len(critical)
    market_age = age_days(market.get("observed_at"), now)
    filing_dates = [v.get("period_end") for k,v in selected.items() if k != "market_price" and v.get("source_type") != "secondary"]
    filing_age = max([age_days(d, now) if age_days(d, now) is not None else 9999 for d in filing_dates], default=None)
    primary = sum(selected.get(k, {}).get("source_type") in ("company_audited", "company_quarterly", "nrb", "nia") for k in critical)
    market_fresh = market_age is not None and market_age <= GATES["market_age_days"]
    financial_fresh = filing_age is not None and filing_age <= GATES["filing_age_days"]
    accepted = [o for o in company.get("observations",[]) if o not in rejected]
    agreement_count = sum(len({urlparse(o["source_url"]).hostname.removeprefix("www.") for o in accepted if o.get("metric")==k and o.get("reported_period")==selected.get(k,{}).get("reported_period") and o.get("unit")==selected.get(k,{}).get("unit")}) >= 2 for k in critical)
    confidence_parts = {"critical_coverage": coverage*25, "primary_filing_coverage": primary/len(critical)*25,
        "financial_recency": 15 if financial_fresh else 0, "market_recency": 15 if market_fresh else 0,
        "source_agreement": 10*agreement_count/len(critical) if not discrepancies else 0,
        "historical_depth": min(1, len(closes)/200)*10}
    confidence = round(sum(confidence_parts.values()))
    if not market_fresh:
        confidence = min(confidence, 49)
    components, contribution = [], 0
    score_coverage = 0
    for category, weight in WEIGHTS.items():
        rows = []
        rules = model["metrics"][category]
        for metric, higher in rules:
            peers = [p.get("metrics", {}).get(metric) for p in sector_peers]
            score = percentile(metrics.get(metric), peers, higher)
            part = score*weight/len(rules) if score is not None else 0
            contribution += part
            if score is not None:
                score_coverage += weight/len(rules)
            rows.append({"metric": metric, "raw": metrics.get(metric), "normalization": "sector midrank percentile, 5/95% clipping",
                         "sector_percentile": score, "higher_is_better": higher, "weight": weight/len(rules), "contribution": part})
        components.append({"category": category, "weight": weight, "metrics": rows})
    quality = round(contribution) if score_coverage >= GATES["coverage"] else None
    valuation = value_company(company["sector"], metrics)
    price = number(market.get("price"))
    mos = 1-price/valuation["base"] if price and valuation["base"] else None
    averages = {str(w): mean(closes[-w:]) if len(closes) >= w else None for w in (20, 50, 200)}
    timing_parts = {"margin_of_safety": max(0, min(60, (mos or 0)/.3*60)) if mos is not None else None,
        "trend": (20 if price >= averages["50"] else 0) if price and averages["50"] else None,
        "liquidity": (20 if metrics["turnover_20d"] >= GATES["min_turnover_20d"] else 0) if metrics.get("turnover_20d") is not None else None}
    timing = round(sum(timing_parts.values())) if all(v is not None for v in timing_parts.values()) else None
    risks = []
    for metric, op, limit, reason in model["risk"]:
        v = number(metrics.get(metric))
        if v is not None and ((op == ">" and v > limit) or (op == "<" and v < limit)):
            risks.append(reason)
    reasons = []
    if missing: reasons.append("Missing critical metrics: " + ", ".join(missing))
    if primary < len(critical): reasons.append("Critical financial inputs require authoritative filings")
    if not market_fresh: reasons.append("Market price is stale or timestamp unavailable")
    if not market.get("verified", False): reasons.append("Market price lacks independent or official confirmation")
    if not financial_fresh: reasons.append("Financial reporting is stale or unverified")
    if quality is None: reasons.append("Comparable sector history/peer coverage is inadequate")
    if valuation["base"] is None: reasons.append("Two supported valuation methods are required")
    if len(closes) < GATES["min_history"]: reasons.append("Fewer than 50 verified price sessions")
    if metrics.get("turnover_20d") is None or metrics["turnover_20d"] < GATES["min_turnover_20d"]: reasons.append("20-session liquidity threshold not met")
    if confidence < GATES["confidence"]: reasons.append("Data confidence below 75/100")
    state = "INSUFFICIENT DATA"
    if discrepancies: state = "SOURCE DISCREPANCY"
    elif risks: state = "FUNDAMENTAL RISK"
    elif not reasons:
        if price > valuation["fair_value_high"]*1.15: state = "OVERVALUED"
        elif price >= valuation["fair_value_low"]: state = "FULLY VALUED"
        elif quality is not None and quality >= GATES["quality"] and timing is not None and timing >= GATES["timing"] and mos is not None and mos >= GATES["margin_of_safety"]:
            state = "ACCUMULATION ZONE" if valuation["entry_low"] <= price <= valuation["entry_high"] else "STRONG RESEARCH CANDIDATE"
        else: state = "WATCH / WAIT"
    eligible = state in ("ACCUMULATION ZONE", "STRONG RESEARCH CANDIDATE")
    return {**company, "metrics": metrics, "selected_evidence": selected, "discrepancies": discrepancies,
        "quality_score": quality, "score_coverage": score_coverage, "score_breakdown": components,
        "timing_score": timing, "timing_breakdown": timing_parts, "moving_averages": averages,
        "confidence": confidence, "confidence_breakdown": confidence_parts, "coverage": coverage,
        "missing": missing, "valuation": valuation, "margin_of_safety": mos, "state": state, "eligible": eligible,
        "gate_reasons": reasons, "market_age_days": market_age, "financial_age_days": filing_age,
        "why": "Validated sector quality, valuation and liquidity meet configured gates" if eligible else "Evidence threshold not met",
        "why_now": "Discount to the fair-value range with supported timing and liquidity" if eligible else "Wait for the failed gates to clear",
        "why_not": risks + ["Valuation depends on normalized earnings, sustainable returns and scenario assumptions", "Sector percentiles reflect the observed peer set and may change", "Unexpected dilution, regulation or governance evidence can change the thesis"] + (["Unresolved contradictory source evidence"] if discrepancies else []),
        "thesis": "Sustainable sector earning power bought at a margin of safety" if eligible else "No positive thesis issued before evidence gates pass",
        "entry_conditions": ["Fresh market price and authoritative financials", "Quality ≥65, timing ≥50, confidence ≥75 and margin of safety ≥20%", "20-session average turnover ≥Rs 1 million"],
        "monitor": model["monitor"], "invalidation": model["invalidate"],
        "trim": ["Position concentration exceeds the investor's allocation limit", "Price materially exceeds the updated fair-value range"],
        "exit": {"risk_stop": "Investor-defined capital/liquidity budget; no automatic price-only exit",
            "thesis_invalidation": model["invalidate"], "valuation_exit": "Review above 115% of bull-case fair value; reassess the assumptions first",
            "portfolio_trim": "Review concentration, liquidity needs and better-supported alternatives"}}


def rank(candidates):
    return sorted((c for c in candidates if c["eligible"]), key=lambda c: (-c["quality_score"], -c["timing_score"], -c["confidence"], c["symbol"]))[:3]
