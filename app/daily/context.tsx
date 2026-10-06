import Link from 'next/link';
import {activeEvents} from './journal';

export default function DailyContext({symbol}:{symbol?:string}) {
 const events=activeEvents(symbol);
 if(!events.length)return null;
 return <section className="shell learning-shell"><div className="card research-card"><p className="eyebrow">Dated thesis context · manually reviewed</p><h2>What changed in the business?</h2>{events.slice(0,3).map(e=><article key={e.id}><h3><Link href={`/company/${e.symbols[0]}`}>{e.symbols.join(', ')}</Link> · {e.title}</h3><p>{e.summary}</p><p><strong>Interpretation:</strong> {e.interpretation}</p><p><strong>Research action:</strong> {e.decision_effect}</p><p className="small">Published {e.published_at} · read {e.retrieved_at.slice(0,10)} · {e.verification_status} · <a href={e.source_url} target="_blank" rel="noreferrer">Original article ↗</a></p></article>)}<p><Link href="/daily#history">Read confirmation tasks and journal history →</Link></p><p className="small">This dated context does not alter the engine’s evidence gates or numeric valuation. It remains visible as history when the live research API is unavailable.</p></div></section>;
}
