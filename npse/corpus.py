"""Read-only implementation authority exported from provider-read corpus v1.1."""
import json
from hashlib import sha256
from pathlib import Path

_BYTES = Path(__file__).resolve().parents[1].joinpath("data/research-corpus-v1.1.json").read_bytes()
CORPUS = json.loads(_BYTES)
CORPUS_HASH = sha256(_BYTES).hexdigest()
SOURCES = {r['source_id']: r for r in CORPUS['sources']}
FORMULAS = {r['formula_id']: r for r in CORPUS['parsed']['FormulaRegistry']}
SECTORS = {'banks': ('COMMERCIAL_BANKS', 'SEC-BANK'), 'hydropower': ('HYDROPOWER', 'SEC-HYD'),
           'manufacturing': ('MANUFACTURING', 'SEC-MFG'), 'microfinance': ('MICROFINANCE', 'SEC-MFI'),
           'life-insurance': ('LIFE_INSURANCE', 'SEC-LIFE'), 'non-life-insurance': ('NON_LIFE_INSURANCE', 'SEC-NL')}
# Explicit implementation mappings. Filings supply observations; methodology sources supply rules.
SOURCE_MAP = {'SEC-BANK': [1, 3, 19, 20, 21, 22], 'SEC-MFI': [1, 4, 5, 19, 21, 22],
              'SEC-HYD': [14, 15, 16, 17, 18], 'SEC-MFG': [10, 23, 24, 25],
              'SEC-LIFE': [6, 7, 8, 9, 19, 22], 'SEC-NL': [6, 7, 8, 9, 19, 22]}
FORMULA_SOURCES = {'FOR-003': [3, 4], 'FOR-004': [21], 'FOR-005': [19, 21, 22], 'FOR-007': [23],
                   'FOR-014': [14, 17], 'FOR-016': [7, 9]}
METRIC_RULES = {
 'banks': {1:['npl','provision_coverage'],2:['capital_adequacy','ccar','regulatory_capital_compliance'],
           3:['cd_ratio','net_liquidity','slr'],4:['roe','roa','eps','normalized_eps'],5:['sustainable_roe','pb','pe'],
           6:['eps_growth','deposit_growth','interest_spread','nim'],7:['distributable_eps','governance']},
 'microfinance': {1:['npl','provision_coverage'],2:['capital_adequacy','ccar','regulatory_capital_compliance'],
                 3:['borrowings','funding_cost','base_rate','deposits'],4:['roe','roa','eps','normalized_eps','regulatory_roe','regulatory_roa','interest_spread'],
                 5:['eps_growth','borrower_growth'],6:['crr','lar','slr','regulatory_liquidity_compliance'],7:['sustainable_roe','pe','pb'],8:['governance','borrower_stress_review']},
 'hydropower': {1:['installed_mw','remaining_life','project_operating'],2:['generation_ratio','capacity_factor','annual_generation'],3:['project_ppa_verified'],
               4:['project_cost','cost_per_mw'],5:['debt','cash','interest_coverage','dscr','debt_equity'],6:['ebitda_margin'],
               7:['governance','shares','corporate_action_review'],8:['eps','normalized_eps','fcfe','pe','ebitda','revenue_growth','eps_growth','ev_ebitda']},
 'manufacturing': {1:['ebitda','operating_margin'],2:['roic','roe','asset_turnover'],3:['fcf','fcfe','fcff','owner_earnings','operating_cash_flow','capex'],
                   4:['debt','cash','debt_equity','interest_coverage'],5:['revenue_growth','eps_growth'],6:['eps','normalized_eps','pe','ev_ebitda','fcf_yield'],
                   7:['cash_conversion','delta_working_capital'],8:['shares','governance','corporate_action_review']},
 'life-insurance': {1:['solvency_ratio','regulatory_solvency_compliance'],2:['reserve_coverage','nfrs17_comparable','reserve_adequacy_review'],
                    3:['premium_growth','persistency','claims_ratio'],4:['investment_yield'],5:['reinsurance_review'],
                    6:['book_value','roe','sustainable_roe','eps','normalized_eps','eps_growth','pe','pb'],7:['governance']},
 'non-life-insurance': {1:['solvency_ratio','regulatory_solvency_compliance'],2:['combined_ratio','claims_ratio','expense_ratio'],
                        3:['reserve_coverage','nfrs17_comparable','reserve_adequacy_review'],4:['reinsurance_review'],5:['investment_yield'],
                        6:['book_value','roe','sustainable_roe','eps','normalized_eps','eps_growth','pe','pb'],7:['governance','premium_growth']}}


def metric_rules(sector, metric):
    return [f'{SECTORS[sector][1]}-{n:03}' for n,metrics in METRIC_RULES[sector].items() if metric in metrics]


def references(ids):
    return [{'source_id': s['source_id'], 'citation_key': s['citation_key'], 'url': s['canonical_url']}
            for n in ids if (s := SOURCES.get(f'SRC-NPSE-{n:03}'))]


def formula_trace(formula_id):
    f = FORMULAS[formula_id]
    return {'formula_id': formula_id, 'corpus_version': '1.1', 'source_basis': f['source_basis'],
            'source_references': references(FORMULA_SOURCES.get(formula_id, [])),
            'implementation_choice': 'NPSE' in f['source_basis'], 'registry_method': f['formula_or_method']}


def sector_trace(sector):
    name, prefix = SECTORS[sector]
    return {'corpus_version': '1.1', 'corpus_sha256': CORPUS_HASH,
            'rule_ids': [r['rule_id'] for r in CORPUS['parsed']['SectorRules'] if r['sector'] == name],
            'source_ids': [r['source_id'] for r in references(SOURCE_MAP[prefix])],
            'choice_version': 'NPSE-CHOICES-1.1', 'quality_formula_id': 'FOR-019',
            'confidence_formula_id': 'FOR-018', 'discrepancy_formula_id': 'FOR-020', 'margin_formula_id': 'FOR-017'}


def observation_trace(row):
    r = dict(row)
    source_id = r.get('source_id')
    if not source_id and r.get('source_type') == 'nrb':
        source_id = 'SRC-NPSE-004' if '/mfd/' in r['source_url'] else 'SRC-NPSE-003'
    if source_id in SOURCES:
        r.update(source_id=source_id, citation_key=SOURCES[source_id]['citation_key'])
    elif r.get('source_type', '').startswith('company_'):
        r.update(source_id='FIL-' + r['symbol'] + '-' + sha256(r['source_url'].encode()).hexdigest()[:12],
                 citation_key='filing_' + r['symbol'].lower() + '_' + r.get('period_end', '').replace('-', ''),
                 source_registration='supplemental company evidence; not one of the 37 methodological sources')
    r['source_authority'] = r.get('source_type')
    return r


def summary():
    return {'version': '1.1', 'sha256': CORPUS_HASH, 'retrieved_at': CORPUS['retrieved_at'],
            'drive_documents': CORPUS['drive_documents'], 'sources': CORPUS['sources'],
            'formulas': CORPUS['parsed']['FormulaRegistry'], 'sector_rules': CORPUS['parsed']['SectorRules'],
            'evidence_gaps': CORPUS['parsed']['EvidenceGaps'],
            'note': 'Corpus URLs establish methodological authority, not connected feeds or locally mirrored PDFs.'}
