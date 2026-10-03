import unittest
from copy import deepcopy
from hashlib import sha256
from npse.corpus import CORPUS, sector_trace, observation_trace, FORMULAS
from npse.formulas import derive
from npse.evidence import resolve, comparable
from npse.decision import evaluate
from npse.sources.primary import verified_report
from npse.corporate_actions import adjusted_prices, validate_action
from npse.backtest import walk_forward
from test_engine import NOW, bank, observation


class CorpusTests(unittest.TestCase):
    def test_canonical_source_identity_and_six_families(self):
        rows=CORPUS['sources']
        self.assertEqual(len(rows),37)
        self.assertEqual(len({s['citation_key'] for s in rows}),37)
        self.assertEqual(len(FORMULAS),20)
        for s in ('banks','hydropower','manufacturing','microfinance','life-insurance','non-life-insurance'):
            t=sector_trace(s)
            self.assertGreaterEqual(len(t['rule_ids']),7)
            self.assertTrue(t['source_ids'])
            self.assertTrue(all(r.startswith('SRC-NPSE-') for r in t['source_ids']))
        r=observation('capital_adequacy',.14,kind='nrb');r['source_url']='https://www.nrb.org.np/bsd/report.pdf'
        self.assertEqual(observation_trace(r)['citation_key'],'nrb_bank_kfi_mid_july_2026')

    def test_regulatory_accounting_and_underwriting_definitions_not_conflicts(self):
        a=observation('roe',.18);b=observation('roe',.26,kind='nrb')
        b.update(source_url='https://nrb.org.np/roe.pdf',accounting_basis='core capital denominator')
        self.assertFalse(comparable(a,b))
        self.assertFalse(resolve([a,b],NOW.isoformat())[1])
        b.pop('accounting_basis');b['definition']='consolidated return'
        self.assertFalse(resolve([a,b],NOW.isoformat())[1])

    def test_aligned_independent_source_conflict_blocks(self):
        c=bank();o=observation('roe',.40);o.update(source_url='https://secondary.example/roe',source_type='secondary')
        c['observations'].append(o)
        self.assertEqual(evaluate(c,[],NOW)['state'],'SOURCE DISCREPANCY')

    def test_old_conflict_does_not_block_new_clean_period(self):
        c=bank();a=observation('roe',.10,period='2081/82 Q4');a['period_end']='2025-07-16'
        b=deepcopy(a);b.update(value=.20,source_url='https://secondary.example/old',source_type='secondary')
        c['observations'] += [a,b]
        r=evaluate(c,[],NOW)
        self.assertEqual(r['historical_discrepancy_count'],1)
        self.assertNotEqual(r['state'],'SOURCE DISCREPANCY')

    def test_stale_or_incompatible_peers_do_not_create_quality(self):
        c=bank();peers=[deepcopy(c) for _ in range(6)]
        for p in peers:
            for r in p['observations']:r['accounting_basis']='different accounting framework'
        result=evaluate(c,peers,NOW)
        self.assertIsNone(result['quality_score'])
        self.assertTrue(all(m['peer_count']==0 for g in result['score_breakdown'] for m in g['metrics']))

    def test_reported_eps_does_not_become_normalized_pe(self):
        c=bank();c['observations']=[o for o in c['observations'] if o['metric']!='normalized_eps']
        r=evaluate(c,[],NOW)
        self.assertIsNone(r['metrics']['pe'])
        self.assertAlmostEqual(r['metrics']['reported_pe'],170/30)

    def test_cash_flow_arithmetic_and_mixed_period_rejection(self):
        inputs={}
        for metric,value in [('ebit',100),('tax_rate',.25),('depreciation_amortization',10),('capex',20),('delta_working_capital',5)]:
            r=observation(metric,value);r['unit']='ratio' if metric=='tax_rate' else 'NPR';inputs[metric]=r
        metrics,trace=derive(inputs,'manufacturing')
        self.assertEqual(metrics['fcff'],60)
        self.assertEqual(trace[0]['formula_id'],'FOR-008')
        inputs['capex']['period_end']='2025-07-16'
        self.assertNotIn('fcff',derive(inputs,'manufacturing')[0])
        self.assertEqual(derive(inputs,'manufacturing')[1][0]['status'],'WITHHELD')

    def test_capacity_factor_annual_and_zero_denominator(self):
        a=observation('annual_generation',43800);a.update(unit='MWh',period_basis='annual')
        b=observation('installed_mw',10);b.update(unit='MW',period_basis='annual')
        self.assertEqual(derive({'annual_generation':a,'installed_mw':b},'hydropower')[0]['capacity_factor'],.5)
        b['value']=0
        self.assertNotIn('capacity_factor',derive({'annual_generation':a,'installed_mw':b},'hydropower')[0])

    def test_underwriting_denominator_required(self):
        a=observation('claims_ratio',.8);b=observation('expense_ratio',.25)
        inputs={'claims_ratio':a,'expense_ratio':b}
        self.assertNotIn('combined_ratio',derive(inputs,'non-life-insurance')[0])
        a['underwriting_basis']=b['underwriting_basis']='net earned premium'
        self.assertAlmostEqual(derive(inputs,'non-life-insurance')[0]['combined_ratio'],1.05)

    def test_primary_hash_change_requires_new_review(self):
        pdf=b'%PDF-1.7 reviewed content';r={'payload_sha256':sha256(pdf).hexdigest()}
        self.assertEqual(verified_report(r,pdf,'2026-10-03')['retrieved_at'],'2026-10-03')
        with self.assertRaises(ValueError):verified_report(r,b'%PDF-1.7 changed content','2026-10-03')

    def test_bonus_price_normalization_and_future_availability(self):
        action={'symbol':'NABIL','action_type':'bonus','effective_date':'2026-09-29',
                'announced_at':'2026-09-20T00:00:00Z','retrieved_at':'2026-09-21T00:00:00Z',
                'source_url':'https://nabilbank.com/bonus','source_type':'company_disclosure','payload':{'share_multiplier':1.1}}
        prices=[{'symbol':'NABIL','date':'2026-09-28','close':110},{'symbol':'NABIL','date':'2026-09-30','close':100}]
        result=adjusted_prices(prices,[action],NOW.isoformat())
        self.assertAlmostEqual(result['prices'][0]['calculated_adjusted_close'],100)
        self.assertNotIn('adjusted_close',result['prices'][0]);self.assertFalse(result['complete'])
        action['retrieved_at']='2026-10-02T00:00:00Z'
        self.assertEqual(adjusted_prices(prices,[action],NOW.isoformat())['prices'][0]['calculated_adjusted_close'],110)

    def test_untrusted_corporate_action_and_unverified_backtest_blocked(self):
        with self.assertRaises(ValueError):validate_action({'symbol':'NABIL'})
        c=bank()
        self.assertEqual(walk_forward([c],['2026-09-30'],{('2026-09-30','NABIL'):999})['sample_size'],0)


if __name__=='__main__':unittest.main()
