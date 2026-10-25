'use strict';
(()=>{
const feed=document.getElementById('electionFeed'),count=document.getElementById('electionCount'),select=document.getElementById('electionState'),search=document.getElementById('electionSearch'),more=document.getElementById('electionMore');
let all=[],shown=18;
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function redraw(){
 const state=select.value,query=search.value.trim().toLowerCase();
 const found=all.filter(x=>(!state||x.state===state)&&(!query||(x.title+' '+x.source+' '+x.state_name).toLowerCase().includes(query)));
 count.textContent=found.length+' source-credited headlines';
 feed.innerHTML=found.length?found.slice(0,shown).map(x=>'<article class="card"><div class="in"><span class="kicker">'+esc(x.state_name)+'</span><h3><a href="'+esc(x.url)+'" target="_blank" rel="noopener noreferrer">'+esc(x.title)+'</a></h3><p class="excerpt">This is a link to original reporting, not an independently verified NewsTrendus article. Check the source for full context and corrections.</p><div class="byline">'+esc(x.source)+' · '+(x.date?new Date(x.date).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}):'Recent')+' · Original publisher ↗</div></div></article>').join(''):'<div class="empty">No recent election stories match these filters. Try All states or consult your official state election office for current details.</div>';
 more.hidden=shown>=found.length;
}
select.addEventListener('change',()=>{shown=18;redraw()});search.addEventListener('input',()=>{shown=18;redraw()});more.addEventListener('click',()=>{shown+=18;redraw()});
fetch('../elections.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Unavailable');return r.json()}).then(data=>{
all=Array.isArray(data.items)?data.items:[];for(const s of data.jurisdictions||[]){const option=document.createElement('option');option.value=s.code;option.textContent=s.name;select.append(option)}
redraw();
}).catch(()=>{count.textContent='Data update pending';feed.innerHTML='<div class="empty">The local elections feed has not completed its first refresh. For official voting information, use the USAGov links below.</div>'});
})();