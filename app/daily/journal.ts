import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export type NewsEvent = {id:string; source_id:string; channel_id:string; source_url:string; title:string; symbols:string[]; sector:string; published_at:string; date_precision:string; retrieved_at:string; event_date_original:string; verification_status:string; summary:string; interpretation:string; decision_effect:string; confirmation_needed:string[]; invalidation:string; supersedes:string|null};
export function journal(): NewsEvent[] {
 return readFileSync(join(process.cwd(),'data/daily-evidence.jsonl'),'utf8').trim().split('\n').filter(Boolean).map(line=>JSON.parse(line));
}
export function activeEvents(symbol?:string) {
 const rows=journal(), replaced=new Set(rows.map(e=>e.supersedes).filter(Boolean));
 return rows.filter(e=>!replaced.has(e.id)&&(!symbol||e.symbols.includes(symbol.toUpperCase()))).sort((a,b)=>b.retrieved_at.localeCompare(a.retrieved_at));
}
