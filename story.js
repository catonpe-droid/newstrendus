'use strict';
const byId=id=>document.getElementById(id);
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cover=i=>'assets/'+(['US','Gaming','Technology','Business','Science','Entertainment','World'].includes(i.category)?i.category.toLowerCase():'news')+'.svg';
const slug=new URLSearchParams(location.search).get('id');
byId('date').textContent=new Date().toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'});
byId('year').textContent=new Date().getFullYear();
const stamp=s=>{if(!s)return 'Recent coverage';const v=new Date(s);return isNaN(v)?'Recent coverage':v.toLocaleString('en-US',{dateStyle:'long',timeStyle:'short',timeZone:'UTC'})+' UTC'};
const sourceurl=u=>{try{const v=new URL(u);return v.protocol==='https:'?v.href:'#'}catch{return '#'}};
fetch('news.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('RSS unavailable');return r.json()}).then(data=>{
const items=Array.isArray(data.items)?data.items:[],a=items.find(x=>x.id===slug);
if(!a){byId('reader').innerHTML='<div class="article-inside"><h1>Story not in the latest snapshot</h1><p>This headline may have aged out. Browse the latest headlines.</p><a class="sourcebtn" href="index.html">Back to latest news</a></div>';return;}
document.title=a.title+' | NewsTrendus';
const excerpt=a.summary?'<p>'+escapeHTML(a.summary)+'</p>':'<p>This story appears in the latest headlines from '+escapeHTML(a.source)+'. The RSS publisher did not provide an extract with this item.</p>';
const img='<img class="article-graphic" src="'+cover(a)+'" alt="Editorial illustration of '+escapeHTML(a.category)+' coverage">';
byId('reader').innerHTML='<div class="article-inside">'+
'<span class="eyebrow">'+escapeHTML(a.category)+'</span><h1 class="article-title">'+escapeHTML(a.title)+'</h1>'+
'<div class="article-meta"><b>Reported by '+escapeHTML(a.source)+'</b> · '+escapeHTML(stamp(a.date))+' · NewsTrendus source-based brief</div></div>'+
img+'<div class="article-inside"><div class="article-caption">Category editorial illustration. Not a photograph of this event.</div>'+
'<div class="article-body"><h2>News at a glance</h2>'+excerpt+
'<div class="quote"><strong>How this brief is prepared</strong><br>This preview is taken from the source-provided RSS feed and displayed for quick reading. We do not rewrite someone else’s full reporting as our own. Details may change as reporting develops.</div>'+
'<h2>Explore this story</h2><p>For additional facts, reporting, attributed quotations, images and updates, consult the original publisher. The link below opens a different website only if you choose to view the full source report.</p>'+
'<a class="sourcebtn" href="'+escapeHTML(sourceurl(a.url))+'" target="_blank" rel="noopener noreferrer">Full report at '+escapeHTML(a.source)+' ↗</a>'+
'<p class="state">NewsTrendus does not claim to be the original reporting organization. Publisher copyrights and ownership are respected.</p></div></div>';
let links=items.filter(x=>x.id!==a.id&&x.category===a.category).slice(0,7);
byId('related').innerHTML=links.map(x=>'<a class="relatedlink" href="story.html?id='+encodeURIComponent(x.id)+'">'+escapeHTML(x.title)+'<small>'+escapeHTML(x.source)+'</small></a>').join('')||'<p class="state">No related headlines in the latest feed.</p>';
byId('category').textContent=a.category;
byId('trendcount').textContent=Array.isArray(data.trends)?data.trends.length:0;
}).catch(()=>{byId('reader').innerHTML='<div class="article-inside"><h1>Story currently unavailable</h1><p>Please check back shortly or return to the NewsTrendus homepage.</p><a class="sourcebtn" href="index.html">Browse headlines</a></div>';});
