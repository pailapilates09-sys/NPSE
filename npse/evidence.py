from datetime import datetime, timezone, timedelta
from .config import AUTHORITY
from .models.common import number

NPT = timezone(timedelta(hours=5, minutes=45))


def timestamp(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.replace(tzinfo=NPT) if dt.tzinfo is None else dt
    except (ValueError, TypeError):
        return None


def age_days(value, now=None):
    dt = timestamp(value)
    now = now or datetime.now(timezone.utc)
    return max(0, (now-dt).total_seconds()/86400) if dt and dt <= now+timedelta(hours=1) else None


def resolve(observations, as_of=None):
    """Only available-by-time observations; never compare different periods or units."""
    selected, discrepancies, rejected = {}, [], []
    cutoff = timestamp(as_of) if as_of else datetime.now(timezone.utc)
    groups = {}
    for obs in observations:
        published = timestamp(obs.get("published_at"))
        retrieved = timestamp(obs.get("retrieved_at"))
        if not published or not retrieved or max(published, retrieved) > cutoff or number(obs.get("value")) is None or not obs.get("source_url") or obs.get("validation_status") != "validated" or obs.get("normalization_state") != "normalized":
            rejected.append(obs)
            continue
        groups.setdefault((obs["metric"], obs["reported_period"], obs.get("unit")), []).append(obs)
    latest_period = {}
    for (metric, period, unit), rows in sorted(groups.items(), key=lambda x: str(x[0])):
        rows.sort(key=lambda r: (AUTHORITY.get(r.get("source_type"), 99), -timestamp(r["published_at"]).timestamp()))
        chosen = rows[0]
        for other in rows[1:]:
            delta = abs(other["value"]-chosen["value"])/max(abs(chosen["value"]), 1e-9)
            if delta > .03:
                discrepancies.append({"metric": metric, "period": period, "unit": unit,
                    "status": "SOURCE DISCREPANCY", "chosen": chosen, "contradiction": other, "relative_difference": delta})
        period_end = str(chosen.get("period_end", ""))
        if period_end >= latest_period.get(metric, ""):
            latest_period[metric] = period_end
            selected[metric] = chosen
    return selected, discrepancies, rejected
