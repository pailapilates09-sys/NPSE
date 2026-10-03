"""Corpus FormulaRegistry calculations. Missing, mixed-period or mismatched units withhold output."""
from .models.common import number
from .corpus import formula_trace

# id, output, ordered (input, unit) specifications, arithmetic
SPECS = [
 ('FOR-001', 'roe', [('net_income','NPR'), ('average_equity','NPR')], lambda v:v[0]/v[1]),
 ('FOR-002', 'roa', [('net_income','NPR'), ('average_assets','NPR')], lambda v:v[0]/v[1]),
 ('FOR-003', 'npl', [('nonperforming_loans','NPR'), ('loans','NPR')], lambda v:v[0]/v[1]),
 ('FOR-004', 'sustainable_growth', [('sustainable_roe','ratio'), ('payout_ratio','ratio')], lambda v:v[0]*(1-v[1])),
 ('FOR-007', 'owner_earnings', [('net_income','NPR'),('noncash_charges','NPR'),('maintenance_capex','NPR'),('required_delta_working_capital','NPR')], lambda v:v[0]+v[1]-v[2]-v[3]),
 ('FOR-008', 'fcff', [('ebit','NPR'),('tax_rate','ratio'),('depreciation_amortization','NPR'),('capex','NPR'),('delta_working_capital','NPR')], lambda v:v[0]*(1-v[1])+v[2]-v[3]-v[4]),
 ('FOR-009', 'fcfe', [('net_income','NPR'),('depreciation_amortization','NPR'),('capex','NPR'),('delta_working_capital','NPR'),('net_borrowing','NPR')], lambda v:v[0]+v[1]-v[2]-v[3]+v[4]),
 ('FOR-010', 'capacity_factor', [('annual_generation','MWh'),('installed_mw','MW')], lambda v:v[0]/(v[1]*8760)),
 ('FOR-011', 'cost_per_mw', [('project_cost','NPR'),('installed_mw','MW')], lambda v:v[0]/v[1]),
 ('FOR-012', 'interest_coverage', [('ebit','NPR'),('interest_expense','NPR')], lambda v:v[0]/v[1]),
 ('FOR-013', 'dscr', [('cfads','NPR'),('scheduled_debt_service','NPR')], lambda v:v[0]/v[1]),
 ('FOR-015', 'equity_value', [('enterprise_value','NPR'),('debt','NPR'),('cash','NPR'),('nonoperating_assets','NPR')], lambda v:v[0]-v[1]+v[2]+v[3]),
 ('FOR-016', 'combined_ratio', [('claims_ratio','ratio'),('expense_ratio','ratio')], lambda v:v[0]+v[1]),
]
DENOMINATORS = {'FOR-001':1,'FOR-002':1,'FOR-003':1,'FOR-010':1,'FOR-011':1,'FOR-012':1,'FOR-013':1}
SECTORS = {'FOR-003':{'banks','microfinance'}, 'FOR-004':{'banks','microfinance'},
           'FOR-007':{'manufacturing'}, 'FOR-008':{'manufacturing'}, 'FOR-009':{'manufacturing','hydropower'},
           'FOR-010':{'hydropower'}, 'FOR-011':{'hydropower'}, 'FOR-012':{'hydropower','manufacturing'},
           'FOR-013':{'hydropower'}, 'FOR-015':{'manufacturing','hydropower'}, 'FOR-016':{'non-life-insurance'}}


def derive(selected, sector):
    metrics = {k:r['value'] for k,r in selected.items()}
    calculations = []
    for fid, output, specs, calc in SPECS:
        if fid in SECTORS and sector not in SECTORS[fid]: continue
        rows = [selected.get(k) for k,_ in specs]
        if not all(rows): continue
        reason = None
        if any(r['unit'] != unit for r,(_,unit) in zip(rows,specs)): reason = 'Input unit mismatch'
        # Require explicitly comparable period and accounting definitions for compound arithmetic.
        bases = {(r.get('period_key',r['reported_period']), r['period_end'], r.get('accounting_basis','unspecified'),
                  r.get('period_basis','unspecified'), r.get('consolidation','unspecified')) for r in rows}
        if len(bases) != 1: reason = 'Inputs have different periods or accounting bases'
        if fid == 'FOR-010' and rows[0].get('period_basis') != 'annual': reason = 'Capacity factor requires a full annual generation period'
        if fid == 'FOR-016' and (not rows[0].get('underwriting_basis') or rows[0].get('underwriting_basis') != rows[1].get('underwriting_basis')):
            reason = 'Loss and expense ratios require the same earned-premium underwriting denominator'
        vals = [r['value'] for r in rows]
        if fid in DENOMINATORS and vals[DENOMINATORS[fid]] <= 0: reason = 'Nonpositive denominator'
        if fid in ('FOR-004','FOR-008') and not 0 <= vals[1] <= 1: reason = 'Payout/tax fraction outside 0–1'
        value = number(calc(vals)) if not reason else None
        if value is None and not reason: reason = 'Nonfinite result'
        calculations.append({**formula_trace(fid), 'metric':output, 'value':value,
            'status':'WITHHELD' if reason else 'CALCULATED', 'reason':reason,
            'reporting_period':rows[0]['reported_period'], 'period_end':rows[0]['period_end'],
            'inputs':[{k:r.get(k) for k in ('metric','value','unit','source_id','citation_key','source_url','published_at','retrieved_at','normalization_state','validation_status')} for r in rows]})
        if value is not None and output not in metrics: metrics[output] = value
    return metrics, calculations
