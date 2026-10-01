MODEL = {
 "critical": ["eps", "book_value", "roe", "npl", "capital_adequacy", "distributable_eps"],
 "metrics": {"quality": [("roe", True), ("roa", True), ("nim", True)],
 "valuation": [("pb", False), ("pe", False)], "growth": [("eps_growth", True), ("deposit_growth", True)],
 "strength": [("npl", False), ("capital_adequacy", True), ("provision_coverage", True)],
 "governance": [("governance", True)], "regime": [("sector_return_20d", True)],
 "liquidity": [("turnover_20d", True)]},
 "risk": [("npl", ">", .08, "NPL exceeds 8% research risk limit"), ("capital_adequacy", "<", .11, "Capital adequacy below 11% research gate")],
 "monitor": ["NPL, provisions, distributable earnings and capital adequacy each quarter", "Funding cost, deposit/loan growth, liquidity and unexpected dilution"],
 "invalidate": ["Material credit deterioration or regulatory capital shortfall", "Normalized earnings or sustainable ROE falls materially below the valued assumptions"]}
