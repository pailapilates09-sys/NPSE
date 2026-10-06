'use client';
import { useState } from 'react';
import type { Board } from '../contracts';

export default function EvidenceExport() {
 const [board,setBoard]=useState<Board|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function check() {
  setBusy(true);setError('');setBoard(null);
  const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),90000);
  try {const r=await fetch('/api/research',{cache:'no-store',signal:controller.signal});if(!r.ok)throw Error();const d=await r.json();if(!Array.isArray(d.companies)||!d.coverage||!d.database)throw Error();setBoard(d);}
  catch {setError('The live research response is unavailable. No new export was created. You can still read this guide and Workspace.');}
  finally {clearTimeout(timer);setBusy(false);}
 }
 return <div className="learning-export"><button onClick={check} disabled={busy}>{busy?'Reading current evidence…':'Read current status and prepare exports'}</button><div role="status" aria-live="polite">{error&&<p>{error}</p>}{board&&<><p><strong>Response run:</strong> {board.as_of}<br/><strong>Engine:</strong> {board.version} · <strong>Database:</strong> {board.database.state}<br/><strong>Primary evidence:</strong> {board.coverage.with_primary_financials}/{board.coverage.registered} companies · <strong>Qualified:</strong> {board.top3.length}/3<br/><strong>Market observation:</strong> {board.market_freshness.observed_at??'Unavailable'} · {board.market_freshness.state}</p><div className="learning-actions"><a href="/api/research?download=csv" download>Download selected evidence CSV</a><a href="/api/research?download=json" download>Download research JSON</a></div><p className="small">CSV contains the selected company observations and their provenance; JSON contains a fresh API result. Each download recomputes the current read-only response, so its run timestamp may differ from the status above. Neither contains the full database or its credentials. The data retains its original reporting/observation dates.</p></>}</div></div>;
}
