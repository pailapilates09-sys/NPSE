import unittest
from datetime import date
from npse.sources.history import parse_history
from npse.decision import evaluate
from test_engine import bank, NOW

HEADER="published_date,high,low,close,traded_quantity,traded_amount\n"
class HistoryTests(unittest.TestCase):
    def test_rejects_future_nonfinite_invalid_range_and_duplicates(self):
        body=HEADER+"2026-09-29,110,90,100,20,2000\n2026-09-29,110,90,101,20,2020\n2026-10-01,110,90,100,20,2000\n2026-09-28,110,90,nan,20,2000\n2026-09-27,110,90,120,20,2000\n"
        rows,rejected=parse_history(body,"NABIL",date(2026,10,1))
        self.assertEqual(len(rows),1);self.assertEqual(rejected,3)
        self.assertEqual(rows[0]["close"],100)
    def test_secondary_unadjusted_history_cannot_qualify(self):
        c=bank()
        for p in c["price_history"]:
            p["source_url"]="https://raw.githubusercontent.com/Aabishkar2/nepse-data/main/data/company-wise/NABIL.csv"
        r=evaluate(c,[],NOW)
        self.assertFalse(r["eligible"])
        self.assertTrue(any("corporate-action" in gap for gap in r["gate_reasons"]))
