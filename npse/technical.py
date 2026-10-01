"""Transparent price/volume research; separate from fundamental valuation."""
from datetime import date
from math import isfinite
from statistics import mean
from zoneinfo import ZoneInfo

METHOD = {
    'name':'Trend + momentum · NPSE adaptation v1',
    'description':'Rank by 63-session price momentum (60%), 20-session momentum (20%) and 20-session average turnover (20%), using empirical midrank percentiles. Filter entry setups for price above both 50- and 200-session averages, positive 63-session momentum, mean turnover ≥Rs 1 million, and no detected discontinuity. These weights and thresholds are implementation choices, not a published NEPSE-tested strategy.',
    'entry_rule':'Watch the prior 20-session high ×1.005. A completed-session close above that trigger with volume ≥1.2× the prior 20-session mean confirms a breakout. Recheck the trend, current price and corporate actions before any order; skip an entry more than 5% above the trigger.',
    'exit_rule':'Illustrative initial risk line = trigger −2×14-session average true range. Also review an exit after a completed close below the 50- or 200-session average. The 2R level is arithmetic, not a price forecast. Gaps, circuit limits, fees and slippage can exceed the risk line.',
    'limitations':'Secondary unadjusted prices; dividends, bonus/right issues and splits can distort momentum. Discontinuity detection is only a heuristic. No NEPSE backtest or expected-return claim. Price strength does not establish business quality or intrinsic value.',
    'references':[
        {'title':'Meb Faber: trend following and relative strength','url':'https://mebfaber.com/2017/12/13/episode-86-quantitative-approach-tactical-asset-allocation/','scope':'Original uses a monthly 10-month average and total returns across asset classes. This board uses daily 200-session averages and raw stock prices.'},
        {'title':'Moskowitz, Ooi & Pedersen (2012): Time Series Momentum','url':'https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum','scope':'Evidence from liquid futures, not NEPSE equities. Our shorter 63-session window and stock ranking are adaptations.'}
    ]
}


def number(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and isfinite(value)


def percentile(value, values):
    return 100*(sum(v < value for v in values)+.5*sum(v == value for v in values))/len(values)


def analyse(companies, now):
    today=now.astimezone(ZoneInfo('Asia/Kathmandu')).date()
    rows=[]; excluded=[]
    for c in companies:
        # Only the completed-session history source is admitted. Saved intraday
        # YONE quotes do not turn into official closing prices the next day.
        by_date={}
        for p in c.get('price_history',[]):
            if 'Aabishkar2/nepse-data/' not in p.get('source_url',''): continue
            try: day=date.fromisoformat(p['date'])
            except (KeyError,ValueError): continue
            if day>=today or not number(p.get('close')) or p['close']<=0: continue
            by_date[p['date']]=p
        history=[by_date[d] for d in sorted(by_date)]
        if len(history)<64:
            excluded.append({'symbol':c['symbol'],'reason':f'{len(history)} admitted completed sessions; need 64 for this momentum window.'})
            continue
        closes=[p['close'] for p in history]; last=history[-1]; close=closes[-1]
        ret63=(close/closes[-64]-1)*100; ret20=(close/closes[-21]-1)*100
        sma50=mean(closes[-50:]); sma200=mean(closes[-200:]) if len(closes)>=200 else None
        turns=[p['turnover'] for p in history[-20:] if number(p.get('turnover')) and p['turnover']>=0]
        turnover=mean(turns) if len(turns)==20 else None
        volumes=[p['volume'] for p in history[-21:-1] if number(p.get('volume')) and p['volume']>0]
        volume_ratio=last['volume']/mean(volumes) if len(volumes)==20 and number(last.get('volume')) else None
        hl=all(number(p.get('high')) and number(p.get('low')) and p['low']<=p['close']<=p['high'] for p in history[-21:])
        trigger=max(p['high'] for p in history[-21:-1])*1.005 if hl else None
        atr=mean(max(history[i]['high']-history[i]['low'],abs(history[i]['high']-history[i-1]['close']),abs(history[i]['low']-history[i-1]['close'])) for i in range(len(history)-14,len(history))) if hl else None
        stop=trigger-2*atr if trigger and atr and trigger>2*atr else None
        jumps=[history[i]['date'] for i in range(max(1,len(history)-199),len(history)) if abs(closes[i]/closes[i-1]-1)>.15]
        age=(today-date.fromisoformat(last['date'])).days
        archive=c.get('selected_evidence',{}).get('archive_unadjusted_close')
        matched=by_date.get(archive['period_end']) if archive else None
        archive_gap=(matched['close']/archive['value']-1)*100 if matched and archive['value']>0 else None
        archive_conflict=archive_gap is not None and abs(archive_gap)>3
        financial_risk=(c.get('metrics',{}).get('eps') is not None and c['metrics']['eps']<0) or (c.get('metrics',{}).get('npl') is not None and c['metrics']['npl']>.05)
        trend=bool(sma200 is not None and close>sma50 and close>sma200 and ret63>0)
        liquid=turnover is not None and turnover>=1_000_000
        setup=bool(trend and liquid and not jumps and age<=7 and not financial_risk and not archive_conflict and stop)
        confirmed=bool(setup and trigger and close>=trigger and volume_ratio is not None and volume_ratio>=1.2 and close<=trigger*1.05)
        warnings=['Raw prices are unadjusted; verify bonus, rights, splits and dividends before using these levels.']
        if archive_conflict: warnings.append(f"Aabishkar and SocrateAI unadjusted closes differ {archive_gap:+.1f}% on {archive['period_end']}; reconcile the providers.")
        if jumps: warnings.append('Possible corporate action or data error: >15% one-session move on '+', '.join(jumps[-3:])+'.')
        if financial_risk: warnings.append('Reported negative EPS or NPL above 5%; positive price strength cannot resolve that business risk.')
        if sma200 is None: warnings.append('Fewer than 200 completed sessions; long-term trend filter is unavailable.')
        if age>7: warnings.append(f'Last admitted close is {age} calendar days old; refresh history before using levels.')
        if not liquid: warnings.append('Mean traded value is below Rs 1 million or incomplete; execution risk is higher.')
        if not hl: warnings.append('High/low data is incomplete; breakout and risk levels are withheld.')
        if archive_conflict: state='SOURCE COMPARISON CONFLICT'
        elif jumps: state='CHECK PRICE ADJUSTMENTS'
        elif financial_risk: state='BUSINESS RISK REVIEW'
        elif age>7: state='REFRESH HISTORY'
        elif not liquid: state='LOW LIQUIDITY'
        elif sma200 is None: state='DEVELOPING HISTORY'
        elif not trend: state='WAIT FOR UPTREND'
        elif trigger and close>trigger*1.05: state='EXTENDED · WAIT'
        elif confirmed: state='BREAKOUT OBSERVED'
        else: state='WATCH FOR BREAKOUT'
        why=f"63-session price return {ret63:+.1f}%; 20-session return {ret20:+.1f}%. Close Rs {close:.2f} is {'above' if close>sma50 else 'below'} its 50-session average Rs {sma50:.2f}. "
        why += f"{'Above' if close>sma200 else 'Below'} the 200-session average Rs {sma200:.2f}." if sma200 is not None else 'Long-term trend history is still developing.'
        action=(f'Wait for a completed close above Rs {trigger:.2f} with volume at least 1.2× its prior 20-session mean; recheck the 50/200-session trends and adjustment status. ' if trigger else 'Complete the high/low history before using an entry trigger. ')
        if confirmed: action='Breakout and volume conditions were observed on the historical close. Verify the current quote and adjustments; do not chase more than 5% above the trigger. '
        if not setup: action='This is a relative-strength comparison, with no entry setup active. '+action
        rows.append({'symbol':c['symbol'],'company':c['company'],'sector':c['sector'],'date':last['date'],'sessions':len(history),'close':round(close,2),'observed_price':c.get('market',{}).get('price'),'observed_at':c.get('market',{}).get('observed_at'),'return_63d':round(ret63,2),'return_20d':round(ret20,2),'sma50':round(sma50,2),'sma200':round(sma200,2) if sma200 is not None else None,'turnover_20d':round(turnover,2) if turnover is not None else None,'volume_ratio':round(volume_ratio,2) if volume_ratio is not None else None,'atr14':round(atr,2) if atr is not None else None,'entry_trigger':round(trigger,2) if trigger else None,'risk_line':round(stop,2) if stop else None,'reference_2r':round(trigger+2*(trigger-stop),2) if stop else None,'trend':trend,'setup':setup and state!='EXTENDED · WAIT','confirmed':confirmed,'state':state,'why':why,'action':action,'warnings':warnings,'source_url':last['source_url'],'archive_comparison':{'date':archive['period_end'] if archive else None,'difference_pct':round(archive_gap,2) if archive_gap is not None else None,'status':'CONFLICT' if archive_conflict else 'WITHIN 3%' if archive_gap is not None else 'NO SAME-DATE COMPARISON','source_url':archive['source_url'] if archive else None}})
    comparable=[r for r in rows if r['state'] not in ('CHECK PRICE ADJUSTMENTS','SOURCE COMPARISON CONFLICT','REFRESH HISTORY','DEVELOPING HISTORY')]
    for r in rows:
        r['score']=round(.6*percentile(r['return_63d'],[p['return_63d'] for p in comparable])+.2*percentile(r['return_20d'],[p['return_20d'] for p in comparable])+.2*percentile(r['turnover_20d'] or 0,[p['turnover_20d'] or 0 for p in comparable]),1) if comparable and r in comparable else None
    rows.sort(key=lambda r:(-(r['score'] if r['score'] is not None else -1),r['symbol']))
    leaders=sorted((r for r in rows if r['score'] is not None and r['state'] not in ('BUSINESS RISK REVIEW','LOW LIQUIDITY')),key=lambda r:(not r['setup'],-r['score'],r['symbol']))[:3]
    above=sum(r['trend'] for r in comparable); denominator=len(comparable)
    return {'method':METHOD,'rows':rows,'leaders':leaders,'excluded':excluded,'counts':{'analysed':len(rows),'comparable':denominator,'setups':sum(r['setup'] for r in rows),'breakouts':sum(r['confirmed'] for r in rows),'above_trend':above},'breadth_pct':round(100*above/denominator,1) if denominator else None,'regime':'BROAD UPTREND' if denominator and above/denominator>=.6 else 'MIXED / SELECTIVE' if denominator and above/denominator>=.4 else 'DEFENSIVE / WEAK BREADTH','regime_note':'Equal-count breadth of the covered stock universe, not the NEPSE index or an independently confirmed market regime.','latest_date':max((r['date'] for r in rows),default=None)}
