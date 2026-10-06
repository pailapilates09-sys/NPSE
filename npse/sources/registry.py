from urllib.parse import urlparse
from pathlib import Path
import json
from ..evidence import timestamp
from ..models.common import number
from ..config import AUTHORITY

SOURCES = [
 {"name":"NEPSE", "type":"official market/disclosures", "url":"https://www.nepalstock.com.np", "status":"Official adapter requires a supported authorized feed"},
 {"name":"SEBON", "type":"regulator/corporate actions", "url":"https://www.sebon.gov.np", "status":"Disclosure admission available; automatic extraction pending"},
 {"name":"Nepal Rastra Bank", "type":"financial regulator", "url":"https://www.nrb.org.np/category/key-financial-indicators/", "status":"July 2026 commercial-bank and microfinance reports admitted, with regulatory-basis notes and per-metric provenance"},
 {"name":"Nepal Insurance Authority", "type":"insurance regulator", "url":"https://nia.gov.np", "status":"Validated report admission available"},
 {"name":"Company audited and quarterly filings", "type":"primary financial authority", "url":None, "status":"Per-value evidence required; no silently invented ratios"},
 {"name":"YONEPSE", "type":"secondary market discovery", "url":"https://shubhamnpk.github.io/yonepse", "status":"Market adapter active; GitHub origin fallback when Pages is stale"},
 {"name":"Aabishkar2 / nepse-data", "type":"secondary daily price history", "url":"https://github.com/Aabishkar2/nepse-data", "status":"Historical CSV adapter available; admitted coverage shown by company. Unadjusted prices, not independent current-price confirmation"},
 {"name":"SocrateAI / nepse-open-data", "type":"secondary adjusted/unadjusted archive", "url":"https://github.com/socrateai-official/nepse-open-data", "status":"September 18, 2026 adjusted/unadjusted comparison snapshot connected. Provider adjustment factors are not a verified corporate-action ledger or today's quote"},
 {"name":"ShareSansar", "type":"secondary verification/discovery", "url":"https://www.sharesansar.com", "status":"Research citations and manually reviewed Daily Evidence journal; automatic news/market/financial adapter not connected"},
 {"name":"MeroLagani", "type":"secondary verification/discovery", "url":"https://merolagani.com", "status":"Not connected"},
 {"name":"NepseAlpha", "type":"secondary verification/discovery", "url":"https://nepsealpha.com", "status":"Not connected"},
]

OFFICIAL_COMPANIES = [
 {"symbol":"SCB","company":"Standard Chartered Bank Nepal Limited","sector":"banks","profile":{"description":"Commercial bank: evaluate capital strength, asset quality, earnings durability and valuation.","official_domain":"sc.com"}},
 {"symbol":"EBL","company":"Everest Bank Limited","sector":"banks","profile":{"description":"Commercial bank: compare low reported NPL, capital buffers, distributable earnings and the price paid for the business.","official_domain":"everestbankltd.com"}},
 {"symbol":"NABIL","company":"Nabil Bank Limited","sector":"banks","profile":{"description":"Commercial bank: evaluate credit quality, capital and distributable earnings.","official_domain":"nabilbank.com"}},
 {"symbol":"CHCL","company":"Chilime Hydropower Company Limited","sector":"hydropower","profile":{"description":"Hydropower: evaluate generation, project economics, debt service and concession life.","official_domain":"chilime.com.np"}},
 {"symbol":"SHIVM","company":"Shivam Cements Limited","sector":"manufacturing","profile":{"description":"Cement manufacturing: evaluate capacity economics, margins and cash flow.","official_domain":"shivamcement.com.np"}},
 {"symbol":"CBBL","company":"Chhimek Laghubitta Bittiya Sanstha Limited","sector":"microfinance","profile":{"description":"Microfinance: evaluate borrower quality, funding and provisioning.","official_domain":"chhimekbank.org"}},
 {"symbol":"NLIC","company":"Nepal Life Insurance Company Limited","sector":"life-insurance","profile":{"description":"Life insurance: evaluate life-fund obligations, reserves and solvency.","official_domain":"nepallife.com.np"}},
 {"symbol":"SICL","company":"Shikhar Insurance Company Limited","sector":"non-life-insurance","profile":{"description":"Non-life insurance: evaluate underwriting, claims and reinsurance.","official_domain":"shikharinsurance.com"}},
]

UNIVERSE = json.loads(Path(__file__).resolve().parents[2].joinpath("data/universe.json").read_text())
for official in OFFICIAL_COMPANIES:
    found = next((c for c in UNIVERSE if c["symbol"] == official["symbol"]), None)
    if found:
        found["profile"].update(official["profile"])
    else:
        UNIVERSE.append(official)


def validate_observation(r):
    required = {"symbol","metric","value","unit","reported_period","period_end","published_at","retrieved_at","source","source_url","source_type","normalization_state","validation_status"}
    if not required.issubset(r) or number(r.get("value")) is None:
        raise ValueError("Observation requires complete provenance and a finite numeric value")
    if r["source_type"] not in AUTHORITY:
        raise ValueError("Unknown source authority type")
    for k in ("period_end", "published_at", "retrieved_at"):
        if timestamp(r[k]) is None:
            raise ValueError("Invalid observation date")
    if r["normalization_state"] != "normalized" or r["validation_status"] != "validated":
        raise ValueError("Only explicitly normalized, validated observations can be admitted")
    if r["symbol"] not in {s["symbol"] for s in UNIVERSE}:
        raise ValueError("Symbol is outside the registered universe")
    if timestamp(r["period_end"]) > timestamp(r["published_at"]) or timestamp(r["published_at"]) > timestamp(r["retrieved_at"]):
        raise ValueError("Publication/retrieval chronology is inconsistent")
    if r["metric"] == "market_price" and (r["unit"] != "NPR" or not timestamp(r.get("market_timestamp")) or r["value"] <= 0 or timestamp(r['market_timestamp']) > timestamp(r['retrieved_at'])):
        raise ValueError("Market price requires NPR units, positive value and observation timestamp")
    if r["metric"] in ("eps","normalized_eps","book_value","distributable_eps") and r["unit"] != "NPR/share":
        raise ValueError("Per-share financials require NPR/share units")
    if r["metric"] in ("normalized_eps", "sustainable_roe") and not r.get("normalization_notes"):
        raise ValueError("Normalized earning-power assumptions require documented normalization notes")
    url = urlparse(r["source_url"])
    if url.scheme != "https" or not url.hostname:
        raise ValueError("HTTPS provenance required")
    authority_domains = {"nrb":"nrb.org.np", "nia":"nia.gov.np", "nepse":"nepalstock.com.np", "sebon":"sebon.gov.np"}
    if r["source_type"].startswith("company_"):
        company = next((s for s in OFFICIAL_COMPANIES if s["symbol"] == r["symbol"]), None)
        if not company:
            raise ValueError("Company official-domain registration required before financial admission")
        domain = company["profile"]["official_domain"]
    else:
        domain = authority_domains.get(r["source_type"])
    if domain and url.hostname != domain and not url.hostname.endswith("."+domain):
        raise ValueError("Source type does not match the registered official domain")
    if not domain and r["source_type"] != "secondary":
        raise ValueError("Unknown authority type")
    review_metrics = {'project_ppa_verified','project_operating','corporate_action_review','nfrs17_comparable',
                     'reinsurance_review','reserve_adequacy_review','regulatory_liquidity_compliance',
                     'regulatory_capital_compliance','regulatory_solvency_compliance','borrower_stress_review'}
    if r['metric'] in review_metrics and (r['value'] not in (0,1) or r['source_type']=='secondary' or not r.get('normalization_notes')):
        raise ValueError('Evidence review requires a primary source, documented review and 0/1 state')
    # Canonical units: ratios as fractions, currency NPR, diluted shares as count.
    if r["metric"] in ("roe","sustainable_roe","roa","npl","capital_adequacy","ccar","cd_ratio","net_liquidity","slr","crr","lar","premium_growth","eps_growth","combined_ratio","claims_ratio") and r["unit"] != "ratio":
        raise ValueError("Financial percentage metrics must be normalized fractions with unit ratio")
    return dict(r)
