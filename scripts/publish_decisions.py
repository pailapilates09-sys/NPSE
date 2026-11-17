"""Make the public Buy / Sell / Why snapshot from the NPSE research API."""

import argparse
import json
import math
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


API = "https://npse-pailapilates09.vercel.app/api/research"
KATHMANDU = ZoneInfo("Asia/Kathmandu")
SYMBOL = re.compile(r"^[A-Z][A-Z0-9.]{0,15}$")
MAX_BYTES = 12_000_000
SNAPSHOT_LIFETIME = timedelta(hours=30)


def positive(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value > 0)


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=KATHMANDU)
    except ValueError:
        return None


def report_date(value):
    try:
        return date.fromisoformat(value).isoformat()
    except (ValueError, TypeError):
        return None


def source_url(value):
    if not isinstance(value, str):
        return None
    try:
        url = urlsplit(value)
        return value if url.scheme == "https" and url.hostname and url.username is None else None
    except ValueError:
        return None


def short_text(value, size=260):
    return " ".join(value.split())[:size] if isinstance(value, str) else ""


def policy_items(value):
    return [short_text(item, 200) for item in value[:2] if isinstance(item, str)] if isinstance(value, list) else []


def project(data, now):
    as_of = timestamp(data.get("as_of"))
    if not as_of or as_of - now > timedelta(minutes=5) or now - as_of > SNAPSHOT_LIFETIME:
        raise ValueError("The research response has no current snapshot timestamp.")
    if not isinstance(data.get("companies"), list) or not isinstance(data.get("top3"), list):
        raise ValueError("Unexpected decision response shape.")
    coverage = data["coverage"]
    registered = coverage["registered"]
    primary = coverage["with_primary_financials"]
    if (not isinstance(registered, int) or registered != len(data["companies"]) or registered < 1
            or not isinstance(primary, int) or not 0 <= primary <= registered):
        raise ValueError("Company coverage does not reconcile.")
    health = data["database"]["state"] == "CONNECTED"
    gate = data.get("config", {}).get("gates", {}).get("market_age_days", 3)
    market_lifetime = timedelta(days=min(gate, 3)) if positive(gate) else timedelta(days=3)

    companies, methods, priced = {}, {}, {}
    for company in data["companies"]:
        symbol = company.get("symbol", "")
        if not isinstance(symbol, str) or not SYMBOL.fullmatch(symbol) or symbol in companies:
            raise ValueError("A symbol is missing, invalid or repeated.")
        sector = company["sector"]
        methods.setdefault(sector, {
            "invalidate": policy_items(company.get("exit", {}).get("thesis_invalidation")),
            "monitor": policy_items(company.get("monitor")),
        })
        state = company["state"]
        summary = {"name": short_text(company["company"], 100), "sector": sector, "state": state}
        if state in ("FUNDAMENTAL RISK", "SOURCE DISCREPANCY"):
            notes = company.get("why_not") or []
            if notes:
                summary["risk_note"] = short_text(notes[0])
        companies[symbol] = summary

        quote = company.get("market", {})
        date_seen = timestamp(quote.get("observed_at"))
        official = (quote.get("verified") is True and quote.get("source_type") == "nepse"
                    and date_seen and date_seen <= as_of and now < date_seen + market_lifetime
                    and positive(quote.get("price")) and source_url(quote.get("source_url")))
        if not official:
            continue
        priced[symbol] = quote
        valuation = company.get("valuation", {})
        buy_limit, high = valuation.get("entry_high"), valuation.get("fair_value_high")
        if (health and company.get("gate_reasons") == [] and valuation.get("status") == "available"
                and valuation.get("evidence_alignment") == "ALIGNED"
                and all(positive(n) for n in (buy_limit, high, valuation.get("base")))):
            summary["valuation"] = {
                "price": quote["price"],
                "price_observed_at": date_seen.isoformat(),
                "expires_at": min(as_of + SNAPSHOT_LIFETIME, date_seen + market_lifetime).isoformat(),
                "entry_ceiling": math.floor(buy_limit * 100) / 100,
                "exit_review_above": round(high * 1.15, 2),
                "source": quote["source_url"],
                "reason": short_text(company.get("why_now")),
                "margin": company.get("margin_of_safety") if positive(company.get("margin_of_safety")) else None,
            }

    by_symbol = {c["symbol"]: c for c in data["companies"]}
    buy = []
    for candidate in data["top3"][:3]:
        symbol = candidate["symbol"]
        company = by_symbol[symbol]
        valued = companies[symbol].get("valuation")
        if (company.get("eligible") is True and valued and valued["price"] <= valued["entry_ceiling"]
                and symbol not in buy):
            buy.append(symbol)

    watch = []
    for row in data.get("preliminary", {}).get("focus", [])[:3]:
        symbol = row.get("symbol")
        if symbol not in companies or symbol in buy:
            continue
        source, period = source_url(row.get("source_url")), report_date(row.get("period_end"))
        if source and period and period <= as_of.astimezone(KATHMANDU).date().isoformat():
            watch.append({"symbol": symbol, "why": short_text(row["why"].split(". Passes", 1)[0].rstrip(".") + "."),
                          "period": period, "source": source})

    observed = timestamp(data.get("market_freshness", {}).get("observed_at"))
    market_date = observed.astimezone(KATHMANDU).date().isoformat() if observed and observed <= as_of else None
    return {
        "schema": 1, "as_of": as_of.isoformat(), "expires_at": (as_of + SNAPSHOT_LIFETIME).isoformat(),
        "market_date": market_date, "official_prices": len(priced), "primary_financials": primary,
        "registered": registered, "engine_connected": health, "buy": buy, "watch": watch,
        "companies": companies, "exit_rules": methods,
    }


def fetch():
    req = Request(API, headers={"Accept": "application/json", "User-Agent": "NPSE09-Pages/1.0"})
    with urlopen(req, timeout=30) as response:
        if (urlsplit(response.geturl()).netloc != urlsplit(API).netloc
                or response.headers.get_content_type() != "application/json"):
            raise ValueError("The research endpoint returned an unexpected destination or content type.")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Research response exceeded the size limit.")
        return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--input", type=Path, help="Use a previously read API response.")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8")) if args.input else fetch()
    result = project(data, datetime.now(timezone.utc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n",
                         encoding="utf-8")
    temporary.replace(args.output)
    print(f"Decisions as of {result['as_of']}: {len(result['buy'])} buys; "
          f"{result['official_prices']}/{result['registered']} current official prices.")


if __name__ == "__main__":
    main()
