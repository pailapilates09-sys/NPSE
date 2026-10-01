from math import isfinite
from statistics import median


def number(value):
    return float(value) if isinstance(value, (float, int)) and not isinstance(value, bool) and isfinite(value) else None


def ratio(a, b):
    a, b = number(a), number(b)
    return a / b if a is not None and b is not None and b > 0 else None


def percentile(value, peers, higher=True):
    """Midrank empirical percentile; needs five peers; ties do not become perfect scores."""
    peers = sorted(v for p in peers if (v := number(p)) is not None)
    value = number(value)
    if value is None or len(peers) < 5:
        return None
    lo, hi = peers[int((len(peers)-1)*.05)], peers[int((len(peers)-1)*.95)]
    v = min(max(value, lo), hi)
    clipped = [min(max(p, lo), hi) for p in peers]
    score = 100 * (sum(p < v for p in clipped) + .5*sum(p == v for p in clipped)) / len(clipped)
    return score if higher else 100-score


def normalize_metrics(metrics, price):
    out = dict(metrics)
    out["pe"] = ratio(price, out.get("eps"))
    out["pb"] = ratio(price, out.get("book_value"))
    ev = None
    if all(number(out.get(k)) is not None for k in ("shares", "debt", "cash")) and number(price) is not None:
        ev = price*out["shares"] + out["debt"] - out["cash"]
    out["ev_ebitda"] = ratio(ev, out.get("ebitda"))
    out["fcf_yield"] = ratio(out.get("fcf"), price*out["shares"] if number(price) is not None and number(out.get("shares")) else None)
    return out
