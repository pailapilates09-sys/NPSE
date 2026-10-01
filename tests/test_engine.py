import unittest
from datetime import datetime, timezone, timedelta
from copy import deepcopy
from npse.models.common import percentile, ratio
from npse.evidence import resolve, age_days
from npse.valuation import value_company
from npse.decision import evaluate, rank
from npse.sources.registry import validate_observation, UNIVERSE
from npse.research import build_research

NOW=datetime(2026,10,1,2,0,tzinfo=timezone.utc)
def observation(metric,value,source="Nabil filing",kind="company_quarterly",period="2082/83 Q4"):
    return {"symbol":"NABIL","metric":metric,"value":value,"unit":"NPR/share" if metric in ("eps","normalized_eps","book_value","distributable_eps") else "ratio","reported_period":period,"period_end":"2026-07-16","published_at":"2026-08-10T00:00:00+00:00","retrieved_at":"2026-08-11T00:00:00+00:00","source":source,"source_type":kind,"source_url":"https://nabilbank.com/filing.pdf","normalization_state":"normalized","validation_status":"validated","normalization_notes":"Synthetic unit-test earning power; never an admitted production filing"}

def bank():
    metrics={"eps":30,"normalized_eps":30,"book_value":200,"roe":.18,"sustainable_roe":.18,"npl":.02,"capital_adequacy":.14,"distributable_eps":20,"roa":.02,"nim":.05,"eps_growth":.15,"deposit_growth":.15,"provision_coverage":1.5,"governance":90,"sector_return_20d":.04}
    return {"symbol":"NABIL","company":"Test fixture only","sector":"banks","observations":[observation(k,v) for k,v in metrics.items()],"market":{"price":170,"observed_at":"2026-09-30T15:00:00+05:45","verified":True},"price_history":[{"date":(NOW-timedelta(days=200-i)).date().isoformat(),"close":160,"turnover":2_000_000} for i in range(200)],"metrics":metrics}

class Tests(unittest.TestCase):
    def test_ratio_invalid(self):
        self.assertIsNone(ratio(10,0)); self.assertIsNone(ratio(10,-1)); self.assertIsNone(ratio(float('nan'),1))
    def test_ties_and_peer_gate(self):
        self.assertEqual(percentile(3,[3]*5),50); self.assertIsNone(percentile(3,[1,2,3]))
    def test_bank_value_manual(self):
        v=value_company("banks",{"normalized_eps":30,"book_value":200,"sustainable_roe":.18})
        base=v["scenarios"][1]
        self.assertAlmostEqual(base["methods"][0]["value"],200*(.18-.04)/(.15-.04))
        self.assertAlmostEqual(base["methods"][1]["value"],420)
        self.assertLess(v["entry_high"],v["fair_value_low"])
    def test_reported_eps_not_normalized(self):
        self.assertEqual(value_company("banks",{"eps":30,"roe":.18,"book_value":200})["status"],"INSUFFICIENT DATA")
    def test_manufacturing_equity_bridge(self):
        v=value_company("manufacturing",{"normalized_eps":20,"ebitda":1000,"shares":10,"debt":500,"cash":100})
        self.assertAlmostEqual(v["scenarios"][1]["methods"][0]["value"],760)
    def test_hydro_no_perpetuity(self):
        v=value_company("hydropower",{"normalized_eps":20,"fcfe":100,"shares":10,"remaining_life":2})
        dcf=v["scenarios"][1]["methods"][0]
        self.assertFalse(dcf["inputs"]["terminal_value"])
        self.assertAlmostEqual(dcf["value"],(100*1.04/1.15+100*1.04**2/1.15**2)/10)
    def test_discrepancy_authority(self):
        a=observation("eps",30); b=observation("eps",40,"Secondary","secondary")
        sel,d,_=resolve([b,a],NOW.isoformat())
        self.assertEqual(sel["eps"]["value"],30); self.assertEqual(len(d),1)
    def test_different_periods_not_conflict(self):
        a=observation("eps",30); b=observation("eps",40,period="2081/82 Q4"); b["period_end"]="2025-07-16"
        sel,d,_=resolve([a,b],NOW.isoformat()); self.assertEqual(len(d),0); self.assertEqual(sel["eps"]["value"],30)
    def test_future_knowledge_excluded(self):
        a=observation("eps",30); a["retrieved_at"]="2026-10-02T00:00:00Z"
        sel,_,_=resolve([a],NOW.isoformat()); self.assertFalse(sel)
    def test_npt_timestamp(self):
        self.assertAlmostEqual(age_days("2026-10-01T07:45:00",NOW),0)
    def test_stale_market_blocks(self):
        c=bank();c["market"]["observed_at"]="2026-09-24"
        r=evaluate(c,[],NOW);self.assertFalse(r["eligible"]);self.assertLess(r["confidence"],50)
    def test_missing_data_blocks(self):
        c=bank();c["observations"]=[];r=evaluate(c,[],NOW)
        self.assertEqual(r["state"],"INSUFFICIENT DATA");self.assertIsNone(r["quality_score"])
    def test_fundamental_risk_overrides_momentum(self):
        c=bank();c["observations"].append(observation("npl",.20,"NRB","nrb"));r=evaluate(c,[],NOW)
        self.assertFalse(r["eligible"]);self.assertIn(r["state"],["FUNDAMENTAL RISK","SOURCE DISCREPANCY"])
    def test_secondary_cannot_impersonate_official(self):
        r=observation("roe",.18);r["source_url"]="https://evil.example/filing.pdf"
        with self.assertRaises(ValueError):validate_observation(r)
    def test_deterministic_rank(self):
        rows=[{"symbol":s,"eligible":True,"quality_score":80,"timing_score":60,"confidence":90} for s in ["B","A","D","C"]]
        self.assertEqual([r["symbol"] for r in rank(rows)],["A","B","C"])
    def test_six_model_families_without_data(self):
        feed={"rows":[],"source":"Test fixture","url":"https://example.com","observed_at":None,"retrieved_at":NOW.isoformat()}
        b=build_research(feed,([],[],[],[]),NOW)
        self.assertEqual(len(b["sectors"]),6);self.assertEqual(len(b["top3"]),0)
        self.assertTrue(all(c["state"]=="INSUFFICIENT DATA" for c in b["companies"]))
    def test_positive_candidate_requires_all_gates(self):
        c=bank()
        peers=[{"metrics":{r["metric"]: (r["value"]*(.5+i*.05) if r["metric"] not in ("npl",) else .04+i*.005) for r in c["observations"]}} for i in range(6)]
        for i,p in enumerate(peers):p["metrics"].update({"pb":2+i*.1,"pe":20+i,"turnover_20d":1_000_000+i*100_000})
        r=evaluate(c,peers,NOW)
        self.assertTrue(r["eligible"],r["gate_reasons"])
        c["market"]["verified"]=False
        self.assertFalse(evaluate(c,peers,NOW)["eligible"])
    def test_future_and_same_provider_not_agreement(self):
        c=bank()
        duplicates=deepcopy(c["observations"])
        for o in duplicates:o["source"]="Other label for same provider"
        future=deepcopy(c["observations"])
        for o in future:o.update(source_url="https://nrb.org.np/future.pdf",retrieved_at="2026-10-02T00:00:00Z")
        c["observations"]+=duplicates+future
        self.assertEqual(evaluate(c,[],NOW)["confidence_breakdown"]["source_agreement"],0)
    def test_future_price_history_does_not_boost_liquidity(self):
        c=bank();c["price_history"]=[{"date":"2026-10-02","close":200,"turnover":9_000_000}]*20
        r=evaluate(c,[],NOW);self.assertIsNone(r["metrics"]["turnover_20d"])
    def test_insurance_and_microfinance_no_ev(self):
        for sector in ("microfinance","life-insurance","non-life-insurance"):
            v=value_company(sector,{"normalized_eps":20,"book_value":200,"sustainable_roe":.15,"ebitda":99999,"debt":1,"cash":1,"shares":100})
            self.assertEqual([m["method"] for m in v["scenarios"][1]["methods"]],["justified P/B","normalized P/E"])

if __name__=="__main__":unittest.main()
