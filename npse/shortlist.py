"""Useful preliminary judgments without overriding the full investment gates."""
from .evidence import age_days
from .config import GATES

def screen(companies, now):
    rows=[]
    for c in companies:
        m=c['metrics']
        npl,car=m.get('npl'),m.get('capital_adequacy')
        evidence=c['selected_evidence']
        if c['sector'] not in ('banks','microfinance') or npl is None or car is None or c['discrepancies']:
            continue
        if any(evidence.get(k,{}).get('source_type') not in ('nrb','company_quarterly','company_audited') or age_days(evidence.get(k,{}).get('period_end'),now) is None or age_days(evidence[k]['period_end'],now)>GATES['filing_age_days'] for k in ('npl','capital_adequacy')):
            continue
        stronger=npl<=.03 and car>=.12
        decision='RESEARCH FIRST' if stronger else 'WAIT / HIGHER CREDIT RISK' if npl>.05 else 'WATCH'
        if car<.11 or npl>.08:
            decision='AVOID NEW EXPOSURE PENDING REVIEW'
        explanation=f"Reported NPL {npl*100:.2f}% and capital adequacy {car*100:.2f}%. "
        explanation += 'Passes this preliminary low-NPL / capital-buffer screen.' if stronger else 'Does not pass the preliminary NPL ≤3% and capital ≥12% screen.'
        rows.append({'symbol':c['symbol'],'company':c['company'],'sector':c['sector'],'decision':decision,'npl':npl,'capital_adequacy':car,'price':c['market'].get('price'),'eps':m.get('eps'),'pe':m.get('reported_pe'),'why':explanation,'next_step':'Confirm sustainable earnings, current price and valuation before committing money.','period_end':evidence['npl']['period_end'],'source_url':evidence['npl']['source_url']})
    rows.sort(key=lambda r:(r['sector'],r['npl'],-r['capital_adequacy'],r['symbol']))
    banks=[r for r in rows if r['sector']=='banks' and r['decision']=='RESEARCH FIRST']
    micro=[r for r in rows if r['sector']=='microfinance' and r['decision']=='RESEARCH FIRST']
    # Two banks plus one microfinance company; disclosed sector mix, not an overall return ranking.
    focus=banks[:2]+micro[:1]
    return {'focus':focus,'comparisons':rows,'methodology':'Preliminary screen: primary NPL ≤3%, capital adequacy ≥12%, report age ≤160 days, no material source discrepancy. Within each sector sort by NPL then capital. Show two banks and one microfinance company. This measures credit quality/capital only, not investment value or predicted returns.','counts':{'compared':len(rows),'screen_passed':sum(r['decision']=='RESEARCH FIRST' for r in rows)}}
