from __future__ import annotations

import json
from urllib.request import Request, urlopen

BASE_URL = "https://shubhamnpk.github.io/yonepse"
USER_AGENT = "NPSE-Control-Tower/0.1 (+https://github.com/pailapilates10-cmd/NPSE-Control-Tower)"


def fetch_json(path: str, timeout: int = 15):
    url = f"{BASE_URL}{path}"
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))
