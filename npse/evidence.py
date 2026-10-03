from datetime import datetime, timezone, timedelta
from .config import AUTHORITY
from .models.common import number
from urllib.parse import urlparse

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


def comparison_key(obs):
    """Unknown basis is not interchangeable with an explicitly different accounting basis."""
    raw = obs.get('raw') or {}
    def field(k, default='unspecified'):
        return obs.get(k) or raw.get(k) or default
    return (obs.get('metric'), field('period_key', obs.get('reported_period')),
            obs.get('period_end'), obs.get('unit'), field('definition'), field('accounting_basis'),
            field('period_basis'), field('consolidation'))


def source_family(obs):
    host = (urlparse(obs.get('source_url', '')).hostname or '').removeprefix('www.')
    for domain in ('nrb.org.np', 'nia.gov.np', 'nepalstock.com.np', 'sebon.gov.np'):
        if host == domain or host.endswith('.' + domain): return domain
    if 'yonepse' in obs.get('source_url', '').lower(): return 'YONEPSE'
    for domain in ('nabilbank.com', 'sc.com', 'everestbankltd.com', 'chhimekbank.org',
                   'nepallife.com.np', 'shikharinsurance.com', 'shivamcement.com.np'):
        if host == domain or host.endswith('.' + domain): return domain
    return host


def authority_key(obs):
    # Corpus AUTH-002/003/004: regulator first for regulatory definitions.
    regulatory = {'npl', 'capital_adequacy', 'ccar', 'cd_ratio', 'net_liquidity', 'slr',
                  'crr', 'lar', 'regulatory_roe', 'regulatory_roa', 'solvency_ratio'}
    rank = AUTHORITY.get(obs.get('source_type'), 99)
    if obs.get('metric') in regulatory and obs.get('source_type') in ('nrb', 'nia'): rank = 0
    return (rank, -timestamp(obs['published_at']).timestamp(), obs.get('source_url', ''))


def comparable(a, b):
    return comparison_key(a) == comparison_key(b)


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
        groups.setdefault(comparison_key(obs), []).append(obs)
    for key, rows in sorted(groups.items(), key=lambda x: str(x[0])):
        metric, period, _, unit, *_ = key
        rows.sort(key=authority_key)
        chosen = rows[0]
        for other in rows[1:]:
            if source_family(other) == source_family(chosen): continue
            delta = abs(other["value"]-chosen["value"])/max(abs(chosen["value"]), 1e-9)
            if delta > .03:
                discrepancies.append({"metric": metric, "period": period, "unit": unit,
                    "status": "SOURCE DISCREPANCY", "chosen": chosen, "contradiction": other, "relative_difference": delta})
        old = selected.get(metric)
        period_end = str(chosen.get("period_end", ""))
        if old is None or period_end > str(old.get('period_end', '')) or (period_end == str(old.get('period_end', '')) and authority_key(chosen) < authority_key(old)):
            selected[metric] = chosen
    return selected, discrepancies, rejected
