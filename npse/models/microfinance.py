from .banks import MODEL as BANK
MODEL = {**BANK,
 "risk": [("npl", ">", .08, "NPL exceeds 8% NPSE research risk limit; not a regulatory threshold")],
 "critical": ["eps", "book_value", "roe", "npl", "capital_adequacy", "provision_coverage", "funding_cost"],
 "metrics": {**BANK["metrics"], "growth": [("eps_growth", True), ("borrower_growth", True)],
 "quality": [("roe", True), ("roa", True), ("interest_spread", True)]},
 "monitor": ["PAR/NPL, collection quality, provisioning and borrower growth", "Funding mix/cost, lending caps, dividend sustainability and rights issues"],
 "invalidate": ["Borrower impairment or provisioning destroys normalized earnings", "Capital or funding shortfall, adverse lending regulation, or governance evidence"]}
