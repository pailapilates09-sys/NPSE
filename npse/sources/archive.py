"""Pinned secondary archive comparison; never replaces a current market quote."""
import csv
import io
import math
from datetime import datetime, timezone
from urllib.request import urlopen
from .registry import UNIVERSE

REVISION = '71b96618a2b8b0d085eec2edfac61193e9d8b51f'
DAY = '2026-09-18'
BASE = f'https://raw.githubusercontent.com/socrateai-official/nepse-open-data/{REVISION}/'

def parse_snapshot(body):
    rows = {}
    for raw in csv.DictReader(io.StringIO(body)):
        values = {k:float(raw[k]) for k in ('close','open','high','low','volume')}
        if raw['date'] != DAY or not all(math.isfinite(v) and v>=0 for v in values.values()) or not 0<values['low']<=values['close']<=values['high'] or raw['symbol'] in rows:
            raise ValueError('Invalid archive snapshot')
        rows[raw['symbol']] = values
    return rows

def fetch_archive():
    now = datetime.now(timezone.utc).isoformat()
    allowed = {c['symbol'] for c in UNIVERSE}
    observations = []
    for kind,prefix,metric in [('adjusted','adj','archive_adjusted_close'),('unadjusted','unadj','archive_unadjusted_close')]:
        url=BASE+f'ohlc_{kind}_stock/{prefix}_{DAY}.csv'
        with urlopen(url,timeout=8) as response:
            body=response.read(1_000_001)
        if len(body)>1_000_000:
            raise ValueError('Archive snapshot too large')
        for symbol,row in parse_snapshot(body.decode('utf-8-sig')).items():
            if symbol in allowed:
                observations.append({'symbol':symbol,'metric':metric,'value':row['close'],'unit':'NPR','reported_period':f'SocrateAI archive session {DAY}','period_end':DAY,'published_at':now,'retrieved_at':now,'source':'SocrateAI archive — '+kind,'source_url':url,'source_type':'secondary','normalization_state':'normalized','validation_status':'validated','market_timestamp':None,'normalization_notes':'Provider-labelled adjustment basis; numeric/session validation only. Not official corporate-action verification or a fresh current quote.'})
    return observations
