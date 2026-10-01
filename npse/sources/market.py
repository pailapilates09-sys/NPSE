import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from ..evidence import timestamp, age_days

ORIGINS = ["https://shubhamnpk.github.io/yonepse", "https://raw.githubusercontent.com/Shubhamnpk/yonepse/main"]


def read_json(url):
    request = Request(url,headers={"User-Agent":"NPSE-Research/1.0","Accept":"application/json"})
    with urlopen(request,timeout=8) as r:
        body = r.read(8_000_001)
        if len(body)>8_000_000: raise ValueError("Source exceeds payload limit")
        return json.loads(body)


def fetch_market():
    """Same provider two transports: never counted as independent source agreement."""
    def origin(base):
        try:
            rows = read_json(base+"/data/nepse_data.json")
            valid = [r for r in rows if timestamp(r.get("last_updated"))]
            observed = max((r["last_updated"] for r in valid),default=None)
            return {"rows": rows,"url":base+"/data/nepse_data.json","observed_at":observed,"error":None}
        except Exception:
            return {"rows":[],"url":base+"/data/nepse_data.json","observed_at":None,"error":"UPSTREAM UNAVAILABLE"}
    with ThreadPoolExecutor(max_workers=2) as p:
        responses = list(p.map(origin,ORIGINS))
    chosen = max(responses,key=lambda r:timestamp(r["observed_at"]).timestamp() if timestamp(r["observed_at"]) else 0)
    return {**chosen,"retrieved_at":datetime.now(timezone.utc).isoformat(),"transports":[{k:v for k,v in r.items() if k!="rows"} for r in responses],"source":"YONEPSE secondary","independent_sources":1}
