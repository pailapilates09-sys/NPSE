"""Point-in-time price normalization; a partial ledger never establishes adjusted-history completeness."""
from copy import deepcopy
from hashlib import sha256
import json
from .evidence import timestamp
from .models.common import number
from .sources.registry import validate_observation


def validate_action(row):
    required = {'symbol','action_type','effective_date','announced_at','retrieved_at','source_url','source_type','payload'}
    if not required.issubset(row): raise ValueError('Corporate action requires complete primary provenance')
    # Reuse verified official-domain admission. A market blog cannot impersonate a primary ledger.
    probe = dict(symbol=row['symbol'],metric='corporate_action_review',value=1,unit='ratio',
                 reported_period='corporate action',period_end=str(row['announced_at'])[:10],
                 published_at=row['announced_at'],retrieved_at=row['retrieved_at'],source='Corporate action',
                 source_url=row['source_url'],source_type=row['source_type'],normalization_state='normalized',validation_status='validated',
                 normalization_notes='Primary action terms reviewed; action import does not establish ledger completeness')
    validate_observation(probe)
    if row['source_type'] not in ('nepse','sebon','company_disclosure','company_audited','company_quarterly'):
        raise ValueError('Primary corporate-action evidence required')
    effective = timestamp(row['effective_date'])
    if not effective or effective < timestamp(row['announced_at']): raise ValueError('Invalid corporate-action chronology')
    p = row['payload']
    if row['action_type'] in ('bonus','split'):
        factor = number(p.get('share_multiplier'))
        if factor is None or factor <= 0: raise ValueError('Positive share multiplier required')
    elif row['action_type'] == 'rights':
        values = [number(p.get(k)) for k in ('rights_ratio','subscription_price','cum_rights_price')]
        if any(v is None for v in values) or values[0] <= 0 or values[1] < 0 or values[2] <= 0:
            raise ValueError('Rights adjustment requires ratio, subscription price and primary cum-rights price')
    else: raise ValueError('Only evidenced bonus, split and rights price adjustments supported')
    identity={k:v for k,v in row.items() if k!='id'}
    return {**row,'id':sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()}


def adjusted_prices(prices, actions, as_of, ledger_complete=False):
    cutoff = timestamp(as_of)
    rows = deepcopy(prices)
    admitted = []
    for action in actions:
        if max(timestamp(action['announced_at']),timestamp(action['retrieved_at']),timestamp(action['effective_date'])) > cutoff: continue
        a = validate_action(action)
        p = a['payload']
        factor = 1/p['share_multiplier'] if a['action_type'] in ('bonus','split') else (p['cum_rights_price']+p['rights_ratio']*p['subscription_price'])/((1+p['rights_ratio'])*p['cum_rights_price'])
        for row in rows:
            if row.get('symbol') == a['symbol'] and row['date'] < a['effective_date']:
                row['calculated_adjusted_close'] = row.get('calculated_adjusted_close',row['close'])*factor
        admitted.append(a['id'])
    for row in rows:
        row.setdefault('calculated_adjusted_close',row['close'])
        row['adjustment_status'] = 'COMPLETE REVIEWED LEDGER' if ledger_complete else 'PARTIAL LEDGER — NOT VERIFIED TOTAL RETURN'
        if ledger_complete: row['adjusted_close'] = row['calculated_adjusted_close']
    return {'prices':rows,'action_ids':admitted,'complete':ledger_complete,
            'choice':'NPSE engineering price adjustment; cash dividends and total return are not inferred'}
