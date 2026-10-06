import csv
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from api.research import handler
from npse.exports import attachment
from npse.corpus import CORPUS

ROOT = Path(__file__).resolve().parents[1]


class ExportsAndDailyTests(unittest.TestCase):
    def board(self):
        return {'as_of':'2026-10-06T00:00:00Z','companies':[{'symbol':'EBL',
                'company':'="formula"','sector':'banks','selected_evidence':{
                'eps':{'value':-3.5,'unit':'NPR/share','source_url':'https://issuer.example/report',
                       'source_id':'test-source','published_at':'2026-09-01',
                       'reported_period':'2082/83 Q4','normalization_state':'normalized'}}}]}

    def test_csv_provenance_and_spreadsheet_injection(self):
        body,mime,name=attachment(self.board(),'csv')
        row=list(csv.DictReader(io.StringIO(body.decode('utf-8-sig'))))[0]
        self.assertEqual(row['company'],'\'="formula"')
        self.assertEqual(row['value'],'-3.5')
        self.assertEqual(row['source_id'],'test-source')
        self.assertEqual(row['reported_period'],'2082/83 Q4')
        self.assertEqual(name,'npse-selected-evidence.csv')
        self.assertTrue(mime.startswith('text/csv'))

    def test_http_exports_are_attachments_and_do_not_persist(self):
        for kind in ('csv','json'):
            h=handler.__new__(handler);h.path='/api/research?download='+kind
            h.wfile=io.BytesIO();headers={};statuses=[]
            h.send_response=statuses.append;h.send_header=lambda k,v:headers.update({k:v})
            h.end_headers=lambda:None
            with patch('api.research.build_research',return_value=self.board()), patch('api.research.database.save_snapshot') as save:
                h.do_GET();save.assert_not_called()
            self.assertEqual(statuses,[200])
            self.assertIn('attachment;',headers['Content-Disposition'])
            self.assertEqual(int(headers['Content-Length']),len(h.wfile.getvalue()))
            if kind=='json':self.assertEqual(json.loads(h.wfile.getvalue()),self.board())

    def test_export_invalid_query_fails_before_provider_fetch(self):
        for query in ('download=exe','download=csv&download=json','download=csv&symbol=EBL','download='):
            h=handler.__new__(handler);h.path='/api/research?'+query
            h.send_json=lambda status,payload:self.assertEqual(status,400)
            with patch('api.research.build_research') as build:
                h.do_GET();build.assert_not_called()

    def test_daily_provenance_symbols_chronology_and_correction_chain(self):
        channels=json.loads((ROOT/'data/daily-sources.json').read_text())['channels']
        self.assertEqual(len(channels),5)
        source_ids={s['source_id'] for s in CORPUS['sources']}
        for channel in channels:
            self.assertTrue(channel['url'].startswith('https://'))
            self.assertTrue(set(channel['source_ids'])<=source_ids)
        universe={r['symbol'] for r in json.loads((ROOT/'data/universe.json').read_text())}
        seen=set()
        for line in (ROOT/'data/daily-evidence.jsonl').read_text().splitlines():
            e=json.loads(line)
            self.assertNotIn(e['id'],seen)
            self.assertIn(e['source_id'],source_ids)
            self.assertTrue(set(e['symbols'])<=universe)
            self.assertLessEqual(e['published_at'],e['retrieved_at'][:10])
            self.assertTrue(e['source_url'].startswith('https://'))
            self.assertTrue(e['confirmation_needed'])
            if e['supersedes']:self.assertIn(e['supersedes'],seen)
            seen.add(e['id'])
