"""Explicit NPSE implementation choices; percentages are not investor prescriptions."""
VERSION = "1.1.0"
# Pure business-quality weights. Valuation and timing have separate gates and outputs.
WEIGHTS = {"quality": 1/3, "growth": .25, "strength": .25, "governance": 1/6}
GATES = {"confidence": 75, "quality": 65, "timing": 50, "coverage": .80,
         "market_age_days": 3, "filing_age_days": 160, "min_history": 50,
         "min_turnover_20d": 1_000_000, "min_peers": 5, "margin_of_safety": .20}
SCENARIOS = {
    "bear": {"cost_equity": .18, "growth": .02, "pe": 10, "ev_ebitda": 6, "haircut": .20},
    "base": {"cost_equity": .15, "growth": .04, "pe": 14, "ev_ebitda": 8, "haircut": .10},
    "bull": {"cost_equity": .13, "growth": .05, "pe": 18, "ev_ebitda": 10, "haircut": 0},
}
AUTHORITY = {"company_audited": 1, "company_quarterly": 2, "company_disclosure": 3,
             "nrb": 2, "nia": 2, "nepse": 2, "sebon": 2, "secondary": 9}
SECTOR_NAMES = {"banks": "Commercial Banks", "hydropower": "Hydropower",
    "manufacturing": "Manufacturing & Processing", "microfinance": "Microfinance",
    "life-insurance": "Life Insurance", "non-life-insurance": "Non-Life Insurance"}
