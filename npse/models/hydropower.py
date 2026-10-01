MODEL = {
 "critical": ["eps", "shares", "ebitda", "debt", "cash", "interest_coverage", "generation_ratio", "remaining_life", "dscr"],
 "metrics": {"quality": [("generation_ratio", True), ("ebitda_margin", True)],
 "valuation": [("ev_ebitda", False), ("pe", False)], "growth": [("revenue_growth", True), ("eps_growth", True)],
 "strength": [("dscr", True), ("interest_coverage", True), ("debt_equity", False)],
 "governance": [("governance", True)], "regime": [("sector_return_20d", True)],
 "liquidity": [("turnover_20d", True)]},
 "risk": [("dscr", "<", 1, "Debt service coverage below 1"), ("interest_coverage", "<", 1, "Operating earnings do not cover interest")],
 "monitor": ["Actual/design generation, hydrology, outages, PPA receipts and project life", "Cost per MW, COD/construction, transmission, debt service, rights issues and lock-in"],
 "invalidate": ["PPA/project life or generation assumptions are materially impaired", "Debt service cannot be sustained or construction/transmission failure changes economics"]}
