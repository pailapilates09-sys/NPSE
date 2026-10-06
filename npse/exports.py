"""Read-only attachments; no database mutation or credential export."""
import csv
import io
import json

FIELDS = ('symbol','company','sector','metric','value','unit','reported_period',
          'period_end','published_at','retrieved_at','source_id','citation_key',
          'source','source_url','accounting_basis','period_basis',
          'normalization_state','validation_status')


def safe_cell(value):
    text = '' if value is None else str(value)
    if not isinstance(value, (int, float)) and text.lstrip().startswith(('=', '+', '-', '@')):
        text = "'" + text
    if text.startswith(('\t', '\r', '\n')):
        text = "'" + text
    return text


def attachment(board, kind):
    if kind not in ('csv', 'json'):
        raise ValueError('Unsupported export format')
    if kind == 'json':
        body = (json.dumps(board, default=str, allow_nan=False, indent=2)+'\n').encode()
        return body, 'application/json; charset=utf-8', 'npse-research.json'
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, quoting=csv.QUOTE_ALL)
    writer.writerow(FIELDS)
    for company in board['companies']:
        for metric, evidence in company['selected_evidence'].items():
            row = {**evidence, 'symbol': company['symbol'], 'company': company['company'],
                   'sector': company['sector'], 'metric': metric}
            writer.writerow([safe_cell(row.get(field)) for field in FIELDS])
    return ('\ufeff'+stream.getvalue()).encode(), 'text/csv; charset=utf-8', 'npse-selected-evidence.csv'
