"""Scenario assumptions must be exposed, never described as official price targets."""
from statistics import median
from .config import SCENARIOS
from .models.common import number
from .corpus import formula_trace


def value_company(sector, metrics):
    runs = []
    for case, a in SCENARIOS.items():
        methods = []
        eps, bv, roe = (number(metrics.get(k)) for k in ("normalized_eps", "book_value", "sustainable_roe"))
        if sector in ("banks", "microfinance", "life-insurance", "non-life-insurance"):
            if bv and bv > 0 and roe is not None and roe > a["growth"]:
                pb = (roe-a["growth"])/(a["cost_equity"]-a["growth"])
                methods.append({**formula_trace('FOR-005'), "method": "justified P/B", "value": bv*pb, "formula": "BVPS × (sustainable ROE − g) / (Ke − g)", "inputs": {"book_value": bv, "roe": roe, **a}})
        else:
            shares, debt, cash, ebitda = (number(metrics.get(k)) for k in ("shares", "debt", "cash", "ebitda"))
            if shares and shares > 0 and ebitda and ebitda > 0 and debt is not None and cash is not None:
                methods.append({**formula_trace('FOR-015'), "method": "EV/EBITDA equity bridge", "value": max(0, (ebitda*a["ev_ebitda"]-debt+cash)/shares), "formula": "(EBITDA × multiple − debt + cash) / diluted shares", "inputs": {"ebitda": ebitda, "debt": debt, "cash": cash, "shares": shares, **a}})
            fcf = number(metrics.get("fcfe"))
            life = number(metrics.get("remaining_life"))
            if fcf is not None and fcf > 0 and shares and shares > 0 and (sector != "hydropower" or (life and 1 <= life <= 100)):
                years = int(life) if sector == "hydropower" else 5
                pv = sum(fcf*(1+a["growth"])**t/(1+a["cost_equity"])**t for t in range(1, years+1))
                # A concession-ending hydro never receives an infinite terminal value.
                if sector != "hydropower":
                    pv += fcf*(1+a["growth"])**6/(a["cost_equity"]-a["growth"])/(1+a["cost_equity"])**5
                methods.append({**formula_trace('FOR-014' if sector == 'hydropower' else 'FOR-009'), "method": "FCFE discounted cash flow", "value": pv/shares, "formula": "Discounted equity cash flow / diluted shares; growth path and manufacturing terminal value are NPSE scenario choices", "inputs": {"fcfe": fcf, "years": years, "terminal_value": sector != "hydropower", **a}})
        if eps and eps > 0:
            methods.append({"method": "normalized P/E", "formula_id": 'FOR-006', "implementation_choice":True, "choice_note":"FOR-006 defines observed P/E; multiplying EPS by an assumed scenario multiple is an NPSE valuation choice", "value": eps*a["pe"], "formula": "Normalized annual EPS × assumed P/E", "inputs": {"eps": eps, **a}})
        values = [m["value"]*(1-a["haircut"]) for m in methods]
        runs.append({"case": case, "assumptions": a, "methods": methods,
                     "low": min(values) if len(values) >= 2 else None,
                     "high": max(values) if len(values) >= 2 else None,
                     "mid": median(values) if len(values) >= 2 else None})
    base = runs[1]
    return {"status": "available" if base["mid"] else "INSUFFICIENT DATA", "scenarios": runs,
        "fair_value_low": base["low"], "fair_value_high": base["high"], "base": base["mid"],
        "entry_low": base["low"]*.7 if base["low"] else None,
        "entry_high": base["low"]*.8 if base["low"] else None,
        "explanation": "Entry zone applies 20–30% margin of safety to the conservative edge of the base range. Assumptions are NPSE research choices; normalized EPS/ROE require analyst validation."}
