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
const stamp=Date.parse(data.updated||'');
const fresh=Number.isFinite(stamp)&&stamp<=Date.now()&&Date.now()-stamp<48*60*60*1000;
all=fresh&&Array.isArray(data.items)?data.items:[];
for(const s of data.jurisdictions||[]){const option=document.createElement('option');option.value=s.code;option.textContent=s.name;select.append(option)}
if(!fresh){
  const when=Number.isFinite(stamp)?new Date(stamp).toLocaleDateString('en-US',{year:'numeric',month:'long',day:'numeric'}):'an unknown date';
  count.textContent='No current source snapshot';
  select.disabled=true;search.disabled=true;more.hidden=true;
  feed.innerHTML='<div class="empty">Our external election-headline snapshot was last refreshed on '+esc(when)+'. It is not live voting or results coverage. For current results and official voter information, visit <a href="https://www.usa.gov/state-election-office" target="_blank" rel="noopener noreferrer">your state election office</a>.</div>';
  return;
}
redraw();
}).catch(()=>{count.textContent='Data update pending';feed.innerHTML='<div class="empty">The local elections feed has not completed its first refresh. For official voting information, use the USAGov links below.</div>'});
})();