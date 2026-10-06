'use client';
import { useState } from 'react';
type Entry={id:string;group:string;title:string;url:string;purpose:string;how:string;status:string;note:string};
export default function Directory({entries}:{entries:Entry[]}){
 const [query,setQuery]=useState(''),[group,setGroup]=useState('All');
 const groups=['All',...new Set(entries.map(e=>e.group))];
 const matches=entries.filter(e=>(group==='All'||e.group===group)&&`${e.title} ${e.group} ${e.purpose} ${e.how} ${e.status} ${e.note}`.toLowerCase().includes(query.toLowerCase()));
 return <section aria-label="Workspace directory"><div className="workspace-controls"><label>Find a tool or document<input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Try Neon, formula, source…"/></label><label>Category<select value={group} onChange={e=>setGroup(e.target.value)}>{groups.map(g=><option key={g}>{g}</option>)}</select></label><button onClick={()=>{setQuery('');setGroup('All')}}>Reset filters</button></div><p role="status" aria-live="polite">{matches.length} of {entries.length} links shown</p><div className="learning-grid workspace-grid">{matches.map(e=><article key={e.id} className="card workspace-entry"><div className="workspace-entry-top"><span className="eyebrow">{e.group}</span><span className="badge">{e.status}</span></div><h2><a href={e.url} {...(e.url.startsWith('https://')?{target:'_blank',rel:'noopener noreferrer'}:{})}>{e.title} {e.url.startsWith('https://')?'↗':'→'}</a></h2><p><strong>Why:</strong> {e.purpose}</p><p><strong>How:</strong> {e.how}</p><p className="small muted">{e.note}</p></article>)}</div>{matches.length===0&&<p>No matching links. Clear the search or choose another category.</p>}</section>
}
