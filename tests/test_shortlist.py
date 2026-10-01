import unittest
from copy import deepcopy
from test_engine import NOW
from npse.shortlist import screen
from npse.research import build_research

def company(symbol='EBL', npl=.005, car=.13, period='2026-07-16'):
    evidence={k:{'source_type':'nrb','period_end':period,'source_url':'https://www.nrb.org.np/bsd/2082-83-mid-july-2026/'} for k in ('npl','capital_adequacy')}
    return {'symbol':symbol,'company':symbol,'sector':'banks','metrics':{'npl':npl,'capital_adequacy':car},'selected_evidence':evidence,'discrepancies':[],'market':{'price':600},'eligible':False}

class ShortlistTests(unittest.TestCase):
    def test_credit_screen_does_not_create_buy_eligibility(self):
        c=company()
        result=screen([c],NOW)
        self.assertEqual(result['focus'][0]['symbol'],'EBL')
        self.assertEqual(result['focus'][0]['decision'],'RESEARCH FIRST')
        self.assertFalse(c['eligible'])
    def test_stale_and_discrepant_evidence_excluded(self):
        stale=company(period='2025-07-16')
        conflict=company();conflict['discrepancies']=[{'metric':'npl'}]
        self.assertEqual(screen([stale,conflict],NOW)['comparisons'],[])
    def test_high_npl_and_low_capital_are_not_shortlisted(self):
        c=company(npl=.10,car=.10)
        result=screen([c],NOW)
        self.assertEqual(result['focus'],[])
        self.assertIn('AVOID',result['comparisons'][0]['decision'])
    def test_full_history_used_before_response_is_compacted(self):
        from test_engine import bank
        c=bank();history=deepcopy(c['price_history'])
        feed={'rows':[],'source':'test','url':'https://example.com','observed_at':None,'retrieved_at':NOW.isoformat()}
        for p in history:p['symbol']=c['symbol']
        board=build_research(feed,([],[],history,[]),NOW)
        row=next(r for r in board['companies'] if r['symbol']==c['symbol'])
        self.assertEqual(row['history_sessions'],len(history))
        self.assertEqual(len(row['price_history']),20)
        self.assertIsNotNone(row['moving_averages']['50'])
        self.assertNotIn('observations',row)
