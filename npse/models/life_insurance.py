MODEL = {
 "critical": ["eps", "book_value", "roe", "solvency_ratio", "reserve_coverage", "premium_growth", "investment_yield"],
 "metrics": {"quality": [("roe", True), ("investment_yield", True), ("persistency", True)],
 "valuation": [("pb", False), ("pe", False)], "growth": [("premium_growth", True), ("eps_growth", True)],
 "strength": [("solvency_ratio", True), ("reserve_coverage", True)], "governance": [("governance", True)],
 "regime": [("sector_return_20d", True)], "liquidity": [("turnover_20d", True)]},
 "risk": [("solvency_ratio", "<", 1, "Solvency ratio below 1"), ("reserve_coverage", "<", 1, "Reserve coverage below 1")],
 "monitor": ["Life-fund liabilities, reserves, persistency and investment asset/liability duration", "Premium growth, solvency, distributable shareholder earnings and dilution"],
 "invalidate": ["Reserves or solvency no longer cover long-duration obligations", "Actuarial or investment evidence undermines sustainable shareholder earnings"]}
