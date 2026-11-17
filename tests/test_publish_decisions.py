from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from scripts.publish_decisions import project


NOW = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)


def test_inputs():
    return {
        "as_of": NOW.isoformat(), "database": {"state": "CONNECTED"},
        "coverage": {"registered": 1, "with_primary_financials": 1},
        "top3": [{"symbol": "TEST"}],
        "companies": [{
            "symbol": "TEST", "company": "Test Company", "sector": "banks",
            "state": "ACCUMULATION ZONE", "eligible": True, "gate_reasons": [],
            "market": {"verified": True, "source_type": "nepse",
                       "observed_at": (NOW - timedelta(hours=1)).isoformat(),
                       "price": 100, "source_url": "https://www.nepalstock.com/today-price"},
            "valuation": {"status": "available", "evidence_alignment": "ALIGNED",
                          "entry_high": 105, "fair_value_high": 155, "base": 150},
            "exit": {"thesis_invalidation": ["Capital deterioration"]},
            "monitor": ["Reported capital and provision coverage"],
        }],
    }


class ProjectDecisionTests(unittest.TestCase):
    def test_proven_entry_and_conditional_exit(self):
        board = project(test_inputs(), NOW)
        self.assertEqual(board["buy"], ["TEST"])
        self.assertEqual(board["companies"]["TEST"]["valuation"]["entry_ceiling"], 105)
        self.assertEqual(board["companies"]["TEST"]["valuation"]["exit_review_above"], 178.25)

    def test_secondary_and_unverified_quotes_cannot_create_price_calls(self):
        for patch in ({"source_type": "secondary"}, {"verified": False},
                      {"observed_at": (NOW + timedelta(hours=1)).isoformat()},
                      {"observed_at": (NOW - timedelta(days=4)).isoformat()}):
            with self.subTest(patch=patch):
                data = test_inputs()
                data["companies"][0]["market"].update(patch)
                board = project(data, NOW)
                self.assertEqual(board["buy"], [])
                self.assertEqual(board["official_prices"], 0)
                self.assertNotIn("valuation", board["companies"]["TEST"])
                self.assertIn("Capital deterioration", board["exit_rules"]["banks"]["invalidate"])

    def test_entry_price_and_evidence_gates_are_independent(self):
        above_ceiling = test_inputs()
        above_ceiling["companies"][0]["market"]["price"] = 110
        board = project(above_ceiling, NOW)
        self.assertEqual(board["buy"], [])
        self.assertIn("valuation", board["companies"]["TEST"])
        no_evidence = deepcopy(above_ceiling)
        no_evidence["companies"][0]["gate_reasons"] = ["Missing normalized EPS"]
        company = project(no_evidence, NOW)["companies"]["TEST"]
        self.assertNotIn("valuation", company)

    def test_old_or_inconsistent_snapshot_is_rejected(self):
        data = test_inputs()
        with self.assertRaises(ValueError):
            project(data, NOW + timedelta(days=2))
        data["coverage"]["registered"] = 2
        with self.assertRaises(ValueError):
            project(data, NOW)


if __name__ == "__main__":
    unittest.main()
