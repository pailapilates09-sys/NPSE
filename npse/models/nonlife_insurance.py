MODEL = {
 "critical": ["eps", "book_value", "roe", "solvency_ratio", "combined_ratio", "claims_ratio", "premium_growth"],
 "metrics": {"quality": [("combined_ratio", False), ("claims_ratio", False), ("roe", True)],
 "valuation": [("pb", False), ("pe", False)], "growth": [("premium_growth", True), ("eps_growth", True)],
 "strength": [("solvency_ratio", True), ("reserve_coverage", True)], "governance": [("governance", True)],
 "regime": [("sector_return_20d", True)], "liquidity": [("turnover_20d", True)]},
 "risk": [("solvency_ratio", "<", 1, "Solvency ratio below 1"), ("combined_ratio", ">", 1.10, "Combined ratio above 110% research risk limit")],
 "monitor": ["Net premium, claims, combined/expense ratios and catastrophe exposure", "Reinsurance recoverables, underwriting reserves, solvency and investment income"],
 "invalidate": ["Persistent underwriting losses invalidate normalized profit", "Catastrophe, reserve inadequacy or reinsurance impairment creates a solvency shortfall"]}
