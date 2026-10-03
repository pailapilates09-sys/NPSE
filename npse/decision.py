from statistics import mean
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from .config import GATES, WEIGHTS
from .models import MODELS
from .models.common import number, percentile, normalize_metrics
from .evidence import resolve, age_days, comparable, source_family
from .valuation import value_company
from .corpus import sector_trace, observation_trace, formula_trace, metric_rules
from .formulas import derive


def evaluate(company, sector_peers, now=None):
    model = MODELS[company["sector"]]
    selected, all_discrepancies, rejected = resolve(company.get("observations", []), now.isoformat() if now else None)
    selected = {k:observation_trace(v) for k,v in selected.items()}
    discrepancies = [d for d in all_discrepancies if comparable(d['chosen'], selected.get(d['metric'],{}))]
    market = company.get("market", {})
    derived, calculations = derive(selected, company['sector'])
    metrics = normalize_metrics(derived, market.get("price"))
    closed_before = now.astimezone(ZoneInfo("Asia/Kathmandu")).date().isoformat() if now else None
    history = sorted((p for p in company.get("price_history", []) if closed_before is None or p["date"] < closed_before), key=lambda p:p["date"])
    closes = [p["close"] for p in history if number(p.get("close")) is not None and (now is None or p["date"] <= now.date().isoformat())]
    turnovers = [p["turnover"] for p in history[-20:] if number(p.get("turnover")) is not None]
    metrics["turnover_20d"] = mean(turnovers) if len(turnovers) == 20 else None
    critical = model["critical"] + ["normalized_eps"]
    if company["sector"] in ("banks", "microfinance", "life-insurance", "non-life-insurance"):
        critical += ["sustainable_roe"]
    sector_required = {'banks':['ccar','cd_ratio','net_liquidity','slr'],
        'microfinance':['ccar','borrowings','regulatory_liquidity_compliance','borrower_stress_review'],
        'hydropower':['installed_mw','project_ppa_verified','project_operating','corporate_action_review'],
        'manufacturing':['corporate_action_review'],
        'life-insurance':['nfrs17_comparable','reinsurance_review','reserve_adequacy_review'],
        'non-life-insurance':['reserve_coverage','nfrs17_comparable','reinsurance_review','reserve_adequacy_review']}
    critical += sector_required[company['sector']]
    missing = [k for k in critical if number(metrics.get(k)) is None]
    coverage = 1-len(missing)/len(critical)
    market_age = age_days(market.get("observed_at"), now)
    filing_dates = [v.get("period_end") for k,v in selected.items() if k != "market_price" and v.get("source_type") != "secondary"]
    filing_age = max([age_days(d, now) if age_days(d, now) is not None else 9999 for d in filing_dates], default=None)
    primary = sum(selected.get(k, {}).get("source_type") in ("company_audited", "company_quarterly", "nrb", "nia") for k in critical)
    market_fresh = market_age is not None and market_age <= GATES["market_age_days"]
    financial_fresh = filing_age is not None and filing_age <= GATES["filing_age_days"]
    accepted = [o for o in company.get("observations",[]) if o not in rejected]
    agreement_count = sum(len({source_family(o) for o in accepted if comparable(o,selected.get(k,{}))}) >= 2 for k in critical)
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
            evidence = selected.get(metric)
            peers = []
            for p in sector_peers:
                peer_evidence = p.get('_selected')
                if peer_evidence is None:
                    peer_evidence, _, _ = resolve(p.get('observations',[]), now.isoformat() if now else None)
                e = peer_evidence.get(metric)
                peer_age = age_days(e.get('period_end'),now) if e else None
                if evidence and e and comparable(evidence,e) and peer_age is not None and peer_age <= GATES['filing_age_days']:
                    peers.append(e['value'])
            score = percentile(metrics.get(metric), peers, higher)
            part = score*weight/len(rules) if score is not None else 0
            contribution += part
            if score is not None:
                score_coverage += weight/len(rules)
            rows.append({"metric": metric, "raw": metrics.get(metric), "normalization": "sector midrank percentile, 5/95% clipping",
                         "sector_percentile": score, "peer_count":len(peers), "formula_id":"FOR-019", 'corpus_rule_ids':metric_rules(company['sector'],metric), "higher_is_better": higher, "weight": weight/len(rules), "contribution": part})
        components.append({"category": category, "weight": weight, "metrics": rows})
    quality = round(contribution) if score_coverage >= GATES["coverage"] else None
    valuation_metrics = dict(metrics)
    financial_valuation_keys = ('normalized_eps','book_value','sustainable_roe') if company['sector'] in ('banks','microfinance','life-insurance','non-life-insurance') else ('normalized_eps','shares','debt','cash','ebitda','fcfe','remaining_life')
    valuation_evidence = [selected[k] for k in financial_valuation_keys if k in selected]
    aligned_valuation = len({(e['period_end'],e.get('accounting_basis','unspecified'),e.get('period_basis','unspecified'),e.get('consolidation','unspecified')) for e in valuation_evidence}) <= 1
    if not aligned_valuation:
        for k in financial_valuation_keys: valuation_metrics[k] = None
    valuation = value_company(company["sector"], valuation_metrics)
    valuation['evidence_alignment'] = 'ALIGNED' if aligned_valuation else 'WITHHELD — mixed reporting periods or accounting bases'
    price = number(market.get("price"))
    official_market = market.get('verified',False) and market.get('source_type') == 'nepse'
    mos = 1-price/valuation["base"] if official_market and price and valuation["base"] else None
    if official_market and metrics.get('pe') is not None:
        calculations.append({**formula_trace('FOR-006'),'metric':'pe','value':metrics['pe'],'status':'CALCULATED',
                             'inputs':{'official_price':price,'normalized_eps':metrics['normalized_eps']}})
    else: metrics['pe'] = None
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
    if not official_market: reasons.append("Current market price requires an official NEPSE observation")
    boolean_reviews = ('project_ppa_verified','project_operating','corporate_action_review','nfrs17_comparable',
                       'reinsurance_review','reserve_adequacy_review','regulatory_liquidity_compliance','borrower_stress_review')
    for k in boolean_reviews:
        if k in critical and metrics.get(k) != 1: reasons.append('Evidence review incomplete: ' + k)
    if company['sector'] in ('banks','microfinance') and metrics.get('regulatory_capital_compliance') != 1:
        reasons.append('Current applicable NRB capital requirements need a primary compliance review')
    if company['sector'] in ('life-insurance','non-life-insurance') and metrics.get('regulatory_solvency_compliance') != 1:
        reasons.append('Current NIA solvency/RBC requirements need a primary compliance review')
    if not financial_fresh: reasons.append("Financial reporting is stale or unverified")
    if quality is None: reasons.append("Comparable sector history/peer coverage is inadequate")
    if valuation["base"] is None: reasons.append("Two supported valuation methods are required")
    if not aligned_valuation: reasons.append('Valuation inputs have incompatible reporting periods or accounting bases')
    if len(closes) < GATES["min_history"]: reasons.append("Fewer than 50 observed price sessions")
    if any("Aabishkar2/nepse-data/" in p.get("source_url", "") and p.get("adjusted_close") is None for p in history):
        reasons.append("Historical prices are secondary and corporate-action adjustments are unverified")
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
    return {**{k:v for k,v in company.items() if k != '_selected'}, "metrics": metrics, "selected_evidence": selected, "discrepancies": discrepancies,
        'historical_discrepancy_count':len(all_discrepancies)-len(discrepancies),
        'rule_trace':sector_trace(company['sector']), 'calculations':calculations,
        'judgments':{'investment_quality':'SUPPORTED BUSINESS QUALITY' if coverage==1 and primary==len(critical) and financial_fresh and quality is not None and quality>=GATES['quality'] else 'INCOMPLETE / BELOW QUALITY GATE',
                     'valuation':valuation['status'],'entry_timing':state,'data_confidence':confidence,
                     'thesis_integrity':'CONTRADICTED' if discrepancies else 'RISK BREACH' if risks else 'NO DETECTED BREACH; EVIDENCE GATES APPLY'},
        'catalysts':[{'condition':s,'status':'Monitoring condition; no observed catalyst claimed'} for s in model['monitor']],
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
