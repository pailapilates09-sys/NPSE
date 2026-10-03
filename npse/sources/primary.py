"""Bounded primary ingestion: verify the official PDF against its reviewed extraction hash."""
import json
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request


def verified_report(report, content, retrieved_at):
    if not content.startswith(b'%PDF-') or sha256(content).hexdigest() != report['payload_sha256']:
        raise ValueError('Official report changed or is not a PDF; extraction review required before admission')
    r = {**report,'retrieved_at':retrieved_at}
    return r


def fetch_reviewed_primary():
    from scripts.prepare_primary_evidence import observations
    dataset = json.loads(Path(__file__).resolve().parents[2].joinpath('data/primary-financials-2026-07.json').read_text())
    reports = [r for r in dataset['reports'] if r['source_type'] == 'nrb']
    retrieved = datetime.now(timezone.utc).isoformat()
    def download(report):
        with urlopen(Request(report['source_url'],headers={'User-Agent':'NPSE-Control-Tower/1.1 primary-evidence-verification'}),timeout=12) as response:
            content = response.read(5_000_001)
        if len(content)>5_000_000: raise ValueError('Primary report exceeds bounded ingestion size')
        return verified_report(report,content,retrieved)
    with ThreadPoolExecutor(max_workers=2) as executor:
        checked = list(executor.map(download,reports))
    rows = observations({'reports':checked})
    return {'observations':rows,'verification':[{'source_url':r['source_url'],'sha256':r['payload_sha256'],'retrieved_at':retrieved} for r in checked]}
