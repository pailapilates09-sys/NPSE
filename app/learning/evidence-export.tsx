'use client';
import { useState } from 'react';
import type { Board } from '../contracts';

const fields = ['symbol','company','sector','metric','value','unit','reported_period','period_end','published_at','retrieved_at','source_id','citation_key','source','source_url','accounting_basis','period_basis','normalization_state','validation_status'] as const;
function cell(value: unknown) {
 let text = value == null ? '' : String(value);
 if (typeof value !== 'number' && /^[=+\-@\t\r]/.test(text)) text = "'" + text;
 return '"' + text.replaceAll('"','""') + '"';
}
function download(text: string, name: string, type: string) {
 const url=URL.createObjectURL(new Blob([text],{type}));
 const anchor=document.createElement('a'); anchor.href=url; anchor.download=name; anchor.click();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export default function EvidenceExport() {
 const [board,setBoard]=useState<Board|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function check() {
  setBusy(true);setError('');setBoard(null);
  const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),90000);
  try {const r=await fetch('/api/research',{cache:'no-store',signal:controller.signal});if(!r.ok)throw Error();const d=await r.json();if(!Array.isArray(d.companies)||!d.coverage||!d.database)throw Error();setBoard(d);}
  catch {setError('The live research response is unavailable. No new export was created. You can still read this guide and Workspace.');}
  finally {clearTimeout(timer);setBusy(false);}
 }
 function csv() {
  if(!board)return;
  const rows=board.companies.flatMap(c=>Object.entries(c.selected_evidence).map(([metric,e])=>({symbol:c.symbol,company:c.company,sector:c.sector,metric,...e})));
  const text='\ufeff'+[fields.map(cell).join(','),...rows.map(r=>fields.map(f=>cell(r[f])).join(','))].join('\r\n')+'\r\n';
  download(text,`npse-selected-evidence-${board.as_of.slice(0,10)}.csv`,'text/csv;charset=utf-8');
 }
 return <div className="learning-export"><button onClick={check} disabled={busy}>{busy?'Reading current evidence…':'Read current status and prepare exports'}</button><div role="status" aria-live="polite">{error&&<p>{error}</p>}{board&&<><p><strong>Response run:</strong> {board.as_of}<br/><strong>Engine:</strong> {board.version} · <strong>Database:</strong> {board.database.state}<br/><strong>Primary evidence:</strong> {board.coverage.with_primary_financials}/{board.coverage.registered} companies · <strong>Qualified:</strong> {board.top3.length}/3<br/><strong>Market observation:</strong> {board.market_freshness.observed_at??'Unavailable'} · {board.market_freshness.state}</p><div className="learning-actions"><button onClick={csv}>Download selected evidence CSV</button><button onClick={()=>download(JSON.stringify(board,null,2)+'\n',`npse-research-${board.as_of.slice(0,10)}.json`,'application/json')}>Download research JSON</button></div><p className="small">CSV contains the selected company observations and their provenance; JSON contains this API result. Neither contains the full database or its credentials. The data retains its original reporting/observation dates.</p></>}</div></div>;
}
