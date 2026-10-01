"""Reproduce the reviewed July 2026 financial extraction; does not send credentials."""
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BANKS = {1:'NBL',3:'ADBL',4:'NABIL',5:'NIMB',6:'SCB',7:'HBL',8:'SBI',9:'EBL',10:'NICA',11:'MBL',12:'KBL',13:'LSL',14:'SBL',15:'GBIME',16:'CZBIL',17:'PCBL',18:'NMB',19:'PRVU',20:'SANIMA'}
MICRO = dict(enumerate(['SKBBL','FMDBL','RSDC','NUBL','DDBL','CBBL','SWBBL','NMLBBL','MLBBL','SLBBL','KMCDB','JSLBB','SWMF','LLBS','HLBSL','VLBS','NMBMF','FOWAD','GILB','MSLB','MERO','SMATA','SLBSL','NMFBS','GBLBS',None,'USLB','NADEP','SMB','ACLBSL','ALBSL','GLBSL','GMFBS','ILBS','SMFBS','SMPDA','NICLBSL','MLBSL','MLBS','UNLB','ULBSL','DLBS','CYCL','NESDO','SWASTIK','SHLB','MATRI','JBLB','ANLB',None,'AVYAN'], 1))

def table_rows(path, width):
    rows = {}
    for line in path.read_text().splitlines():
        match = re.match(r'^\s*(\d+)\s+(.+?)\s{2,}([-\d].*)$', line)
        if not match:
            continue
        values = match[3].split()
        assert len(values) == width, (match[1], len(values))
        rows[int(match[1])] = (match[2], [None if v == '-' else float(v.replace(',', '').replace('%', '')) for v in values])
    return rows

def prepare(directory):
    now = datetime.now(timezone.utc).isoformat()
    reports = []
    for name, mapping, width, url, published in [
        ('nrb-banks', BANKS, 23, 'https://www.nrb.org.np/bsd/2082-83-mid-july-2026/', '2026-09-17T00:00:00+05:45'),
        ('nrb-micro', MICRO, 19, 'https://www.nrb.org.np/mfd/key-financial-indicators-of-microfinance-institutions-as-on-asar-end-2083/', '2026-09-22T00:00:00+05:45')]:
        extracted = table_rows(directory / (name + '.txt'), width)
        entries = []
        for ordinal, symbol in mapping.items():
            if not symbol:
                continue
            institution, v = extracted[ordinal]
            metrics = {'capital_adequacy':v[3]/100, 'npl':v[13]/100}
            if name == 'nrb-banks':
                metrics.update(deposits=v[4]*1e6, loans=v[6]*1e6, interest_spread=v[12]/100, regulatory_net_npl=v[14]/100)
            else:
                metrics.update(deposits=v[5]*1e6, loans=v[7]*1e6, net_profit=v[15]*1e6, regulatory_roa=v[16]/100, regulatory_roe=v[17]/100, base_rate=v[18]/100)
            entries.append({'symbol':symbol, 'reported_name':institution, 'metrics':metrics})
        reports.append({'source':'Nepal Rastra Bank — ' + name, 'source_type':'nrb', 'source_url':url, 'published_at':published, 'retrieved_at':now, 'period_end':'2026-07-16', 'reported_period':'2082/83 Asadh end — provisional regulatory basis', 'basis':'Amounts: NPR million converted to NPR. Percentages divided by 100. Microfinance regulatory ROE uses core capital, not accounting equity; it is kept separate from accounting ROE. Regulatory figures can differ from NFRS filings.', 'payload_sha256':hashlib.sha256((directory/(name+'.pdf')).read_bytes()).hexdigest(), 'companies':entries})
    companies = [
        ('NABIL','Nabil Bank — Q4 FY 2025/26 standalone','https://assets.nabilbank.com/uploads/Finance/Interim%20Financial/interim-financial-report-q4-fy-2025-26-nabil-bank-71d27cb6.pdf',
         {'eps':28.36,'book_value':247.28,'roe':.1176,'roa':.0115,'npl':.042,'capital_adequacy':.1237,'provision_coverage':1.1973,'funding_cost':.0309,'interest_spread':.0318,'distributable_eps':19.10,'eps_growth':28.36/21.89-1,'net_profit':7905796000}, 'EPS and book value exclude preference capital/dividend as disclosed. Distributable EPS includes retained earnings; it is not a declared dividend.'),
        ('SHIVM','Shivam Cements — Q4 FY 2082/83 standalone','https://shivamcement.com.np/assets/uploads/6d187-4th-qtr-fs-fy-2082_83.pdf',
         {'eps':14.03,'book_value':10557565882/55932287.125,'shares':55932287.125,'revenue':6922657420,'revenue_growth':6922657420/7766576397-1,'eps_growth':14.03/14.27-1,'net_profit':784474151,'operating_cash_flow':755095451,'capex':208903094,'cash':750188792,'debt':5502368,'cash_conversion':755095451/784474151}, 'EPS comparison uses NAS33 bonus-restated prior-year EPS 14.27. Cash flow and revenue are standalone. Capex = cash PPE + intangible purchases. Debt excludes lease liabilities; no normalized earning power or FCFE is inferred.'),
        ('EBL','Everest Bank — Q4 FY 2082/83','https://everestbankltd.com/wp-content/uploads/2026/08/4th-Quarterly-Financial-Report-of-Fiscal-Year-2082-83.pdf',
         {'eps':36.95,'book_value':256.47,'roe':.151,'roa':.0136,'npl':.0049,'capital_adequacy':.1223,'provision_coverage':2.9525,'funding_cost':.0315,'interest_spread':.0305,'distributable_eps':38.32,'eps_growth':36.95/37.39-1,'net_profit':5069936000,'deposit_growth':316018577/298818400-1}, 'Web-extracted official PDF pages 0–7. Amounts NPR thousands converted to NPR. Distributable EPS includes accumulated retained earnings and is not a declared dividend. Reported EPS and ROE remain distinct from sustainable earning-power assumptions.')]
    for symbol, source, url, metrics, basis in companies:
        reports.append({'source':source,'source_type':'company_quarterly','source_url':url,'published_at':now,'retrieved_at':now,'period_end':'2026-07-16','reported_period':'2082/83 Q4 full-year YTD — standalone','basis':basis+' Original publication date unavailable: first verified availability used conservatively.','companies':[{'symbol':symbol,'metrics':metrics}]})
    return {'prepared_at':now,'reports':reports}

def observations(dataset):
    ratios = {'roe','roa','npl','capital_adequacy','regulatory_roe','regulatory_roa','regulatory_net_npl','interest_spread','provision_coverage','funding_cost','base_rate','eps_growth','revenue_growth','deposit_growth','cash_conversion','solvency_ratio','earned_premium_growth','net_profit_growth','claims_ratio'}
    rows=[]
    for report in dataset['reports']:
        for company in report['companies']:
            for metric,value in company['metrics'].items():
                unit = 'NPR/share' if metric in ('eps','book_value','distributable_eps') else 'ratio' if metric in ratios else 'shares' if metric=='shares' else 'NPR'
                rows.append({**{k:report[k] for k in ('source','source_type','source_url','published_at','retrieved_at','period_end','reported_period')},'symbol':company['symbol'],'metric':metric,'value':value,'unit':unit,'normalization_state':'normalized','validation_status':'validated','normalization_notes':report['basis'],'market_timestamp':None})
    return rows

if __name__=='__main__':
    import sys
    data=prepare(Path(sys.argv[1]))
    existing=ROOT/'data/primary-financials-2026-07.json'
    if existing.exists():
        known={r['source_url'] for r in data['reports']}
        data['reports'] += [r for r in json.loads(existing.read_text())['reports'] if r['source_url'] not in known]
    (ROOT/'data/primary-financials-2026-07.json').write_text(json.dumps(data,indent=2)+'\n')
    out=Path(sys.argv[1])/'observations.json'
    rows=observations(data)
    out.write_text(json.dumps(rows))
    print(json.dumps({'companies':len({r['symbol'] for r in rows}),'observations':len(rows),'output':str(out)}))
