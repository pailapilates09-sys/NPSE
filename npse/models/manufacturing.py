MODEL = {
 "critical": ["eps", "shares", "ebitda", "debt", "cash", "fcf", "roic", "interest_coverage"],
 "metrics": {"quality": [("roic", True), ("operating_margin", True), ("asset_turnover", True)],
 "valuation": [("ev_ebitda", False), ("pe", False), ("fcf_yield", True)],
 "growth": [("revenue_growth", True), ("eps_growth", True)],
 "strength": [("interest_coverage", True), ("debt_equity", False), ("cash_conversion", True)],
 "governance": [("governance", True)], "regime": [("sector_return_20d", True)], "liquidity": [("turnover_20d", True)]},
 "risk": [("interest_coverage", "<", 1, "Operating earnings do not cover interest"), ("roic", "<", 0, "Negative return on invested capital")],
 "monitor": ["Revenue, pricing power, capacity utilization and gross/operating margins", "Cash conversion, capex, working capital, ROIC and leverage"],
 "invalidate": ["Persistent margin/ROIC deterioration erodes value creation", "Cash flow or debt service no longer supports the valuation assumptions"]}
