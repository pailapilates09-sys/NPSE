import unittest
from datetime import datetime,timedelta,timezone
from npse.technical import analyse

NOW=datetime(2026,10,1,tzinfo=timezone.utc)
def company(symbol='TEST',factor=1):
    return {'symbol':symbol,'company':'Synthetic test fixture','sector':'banks','market':{},'metrics':{},'price_history':[{'date':(NOW-timedelta(days=200-i)).date().isoformat(),'close':100+i*factor,'high':102+i*factor,'low':98+i*factor,'volume':10000,'turnover':2_000_000,'source_url':f'https://raw.githubusercontent.com/Aabishkar2/nepse-data/main/data/company-wise/{symbol}.csv'} for i in range(200)]}
class TechnicalTests(unittest.TestCase):
    def test_manual_indicator_values_and_risk_arithmetic(self):
        row=analyse([company()],NOW)['rows'][0]
        self.assertEqual(row['sma200'],199.5); self.assertEqual(row['sma50'],274.5)
        self.assertAlmostEqual(row['return_63d'],round((299/236-1)*100,2))
        self.assertAlmostEqual(row['entry_trigger'],round(300*1.005,2))
        self.assertEqual(row['atr14'],4); self.assertTrue(row['setup'])
        self.assertEqual(row['risk_line'],row['entry_trigger']-8)
        self.assertEqual(row['reference_2r'],row['entry_trigger']+16)
        self.assertFalse(row['confirmed'])
    def test_current_day_and_saved_intraday_quotes_do_not_enter_indicators(self):
        c=company(); original=analyse([c],NOW)['rows'][0]
        c['price_history'].append({**c['price_history'][-1],'date':'2026-10-01','close':999})
        c['price_history'].append({**c['price_history'][-2],'source_url':'https://shubhamnpk.github.io/yonepse/' ,'close':999})
        self.assertEqual(analyse([c],NOW)['rows'][0],original)
    def test_discontinuities_withhold_rank_and_entry(self):
        c=company(); c['price_history'][-1]['close']=180
        row=analyse([c],NOW)['rows'][0]
        self.assertEqual(row['state'],'CHECK PRICE ADJUSTMENTS');self.assertIsNone(row['score']);self.assertFalse(row['setup'])
    def test_shorter_history_cannot_pass_200_session_filter(self):
        c=company(); c['price_history']=c['price_history'][-100:]
        row=analyse([c],NOW)['rows'][0]
        self.assertEqual(row['state'],'DEVELOPING HISTORY');self.assertFalse(row['setup'])
    def test_ties_and_order_are_deterministic_and_business_risk_blocks_setup(self):
        a=company('AAA');b=company('BBB'); b['metrics']['npl']=.1
        rows=analyse([b,a],NOW)
        self.assertEqual([r['symbol'] for r in rows['rows']],['AAA','BBB'])
        self.assertEqual(rows['rows'][0]['score'],50);self.assertFalse(rows['rows'][1]['setup'])
        self.assertEqual([r['symbol'] for r in rows['leaders']],['AAA'])
if __name__=='__main__':unittest.main()
