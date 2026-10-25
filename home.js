'use strict';
const $=s=>document.querySelector(s), $$=s=>document.querySelectorAll(s);
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// A real-photo fallback rather than the old SVG news illustration.
const cover=i=>{
 const ids={US:'36077357',Trending:'36077357',Business:'36755611',Sports:'33535231',Technology:'34804003',Gaming:'7862378',Health:'4031693',Science:'4031693',Entertainment:'7991112',World:'7635240'};
 const id=ids[i.category]||ids.US;
 return 'https://images.pexels.com/photos/'+id+'/pexels-photo-'+id+'.jpeg?auto=compress&cs=tinysrgb&w=1200';
};
const day=d=>{if(!d)return 'Latest';const x=new Date(d);return isNaN(x)?'Latest':x.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})};
const link=i=>i.page_url ? i.page_url : 'story.html?id='+encodeURIComponent(i.id||'');
const shot=i=>i.is_editorial && i.image ? {
 src:i.image,artist:i.photo_artist||'Photographer',url:i.photo_credit_url||'https://www.pexels.com/license/',
 description:i.image_alt||'news topic',license:'Pexels License'
} : window.NewsTrendusPhotos?.forStory(i)||null;
const imageHTML=(i,priority=false)=>{
 const p=shot(i),alt=(i.is_editorial ? (i.image_alt||'Representative photo') : (p?'Representative '+p.description:'Editorial '+i.category+' illustration'));
 const url=p?p.src:cover(i);
 const fallback=cover(i);
 return '<img loading="'+(priority?'eager':'lazy')+'" decoding="async" src="'+escapeHTML(url)+'" alt="'+escapeHTML(alt)+'" onerror="this.onerror=null;this.src=\''+fallback+'\'">';
};
const photoCredit=i=>{
 const p=shot(i);
 return p?'<span class="photo-attribution">Representative photo (not of this event): <a href="'+escapeHTML(p.url)+'" target="_blank" rel="noopener noreferrer">'+escapeHTML(p.artist)+' / Pexels</a></span>':'<span class="photo-attribution">NewsTrendus editorial illustration</span>';
};
let articles=[],activeCat=(new URLSearchParams(window.location.search).get('category')||'All'),search='',limit=16;
const brandDate=new Date().toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'});
$('#date').textContent=brandDate;$('#year').textContent=new Date().getFullYear();
function feature(item,small=false){
if(!item)return '';
return '<article class="'+(small?'feature-sm':'feature')+'">'+
imageHTML(item,!small)+
'<span class="artnote">Representative photograph</span>'+
'<div class="feature-inner"><span class="storytag">'+escapeHTML(item.category)+'</span><h2><a href="'+link(item)+'">'+escapeHTML(item.title)+'</a></h2>'+
'<div class="byline"><span>'+escapeHTML(item.source)+'</span><span>·</span><span>'+day(item.date)+'</span></div>'+photoCredit(item)+'</div></article>';
}
function card(item){
let preview=item.summary?'<p class="excerpt">'+escapeHTML(item.summary)+'</p>':'';
let extraLabel=(item.full_html?'<span class="kicker" style="margin-left:10px;color:#08765a">Full article</span>':'')+
                (item.trend_matches&&item.trend_matches.length?'<span class="kicker" style="margin-left:10px;color:#bc1734">US trending</span>':'');
return '<article class="card"><a href="'+link(item)+'" aria-label="Read news brief: '+escapeHTML(item.title)+'">'+imageHTML(item)+'</a>'+
'<div class="in">'+photoCredit(item)+'<span class="kicker">'+escapeHTML(item.category)+'</span>'+extraLabel+'<h3><a href="'+link(item)+'">'+escapeHTML(item.title)+'</a></h3>'+preview+
'<div class="byline"><span>'+escapeHTML(item.source)+'</span><span>·</span><time>'+day(item.date)+'</time><span>·</span><span>Read on NewsTrendus</span></div></div></article>';
}
function render(){
const t=search.toLowerCase(),list=articles.filter(i=>(activeCat==='All'||i.category===activeCat)&&(!t||(i.title+' '+i.category+' '+(i.summary||'')).toLowerCase().includes(t)));
$('#count').textContent=list.length+' stories';
$('#listTitle').textContent=activeCat==='All'?'Top Stories & Latest News':activeCat+' News';
$('#lead').innerHTML=list.length?feature(list[0]):'<div class="empty">No recent headlines match this filter.</div>';
$('#sideleads').innerHTML=list.slice(1,3).map(i=>feature(i,true)).join('');
$('#feed').innerHTML=list.slice(3,3+limit).map(card).join('')||'<div class="empty">Explore more topics, or try a different search.</div>';
$('#more').hidden=list.length<=limit+3;
$$('[data-category]').forEach(b=>b.classList.toggle('active',b.dataset.category===activeCat));
}
$$('[data-category]').forEach(b=>b.addEventListener('click',()=>{activeCat=b.dataset.category;limit=16;render();window.scrollTo({top:0,behavior:'smooth'})}));
$('#search').addEventListener('input',e=>{search=e.target.value.trim();limit=16;render()});
$('#more').addEventListener('click',()=>{limit+=16;render()});
$('#gta').addEventListener('click',()=>{activeCat='All';search='gta';$('#search').value='gta';limit=50;render();$('#stories').scrollIntoView({behavior:'smooth'})});
Promise.allSettled([
 fetch('news.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('RSS preview unavailable');return r.json()}),
 fetch('editorial-news.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Editorial catalogue unavailable');return r.json()})
]).then(results=>{
const d=results[0].status==='fulfilled'?results[0].value:{items:[],trends:[],updated:null};
const ed=results[1].status==='fulfilled'?results[1].value:{items:[]};
const editorial=(Array.isArray(ed.items)?ed.items:[]).filter(x=>x&&x.title&&x.page_url&&x.image&&x.is_editorial);
const feed=(Array.isArray(d.items)?d.items:[]).filter(x=>x&&x.title&&x.url&&x.id);
articles=[...editorial,...feed];
if(!articles.length)throw Error('No published articles or source briefs');

$('#refreshed').textContent=editorial.length?editorial.length+' verified on-site articles':'News updates available';
$('#tickerHeadline').textContent=articles.length?articles[0].title:'Latest headlines coming soon';
$('#tickerHeadline').href=articles.length?link(articles[0]):'index.html';
$('#countTotal').textContent=articles.length;
const full=feed.filter(a=>a.full_html && ['NASA government release','KFF Health News licensed republication'].includes(a.license_type));
const fullSpot=document.querySelector('#fullReads');
if(fullSpot){fullSpot.innerHTML=full.length?full.slice(0,4).map(a=>card(a)).join(''):'<div class="empty">Full-length licensed reports from NASA and KFF Health News will appear here as they become available.</div>';}

const trends=Array.isArray(d.trends)?d.trends.slice(0,10):[];
$('#trendCount').textContent=trends.length;
$('#trends').innerHTML=trends.length?trends.map((x,i)=>{
 const local=x.related_id?'story.html?id='+encodeURIComponent(x.related_id):'https://trends.google.com/trending?geo=US';
 const external=x.related_id?'':' target="_blank" rel="noopener noreferrer"';
 const label=x.related_title?'<small class="state" style="display:block;margin-top:5px">Related: '+escapeHTML(x.related_title)+' · '+escapeHTML(x.related_source||'')+'</small>':'';
 return '<div class="trendrow"><span class="trendnum">'+(i+1)+'</span><div><a href="'+local+'"'+external+'>'+escapeHTML(x.title)+'</a>'+label+'</div></div>';
}).join(''):'<p class="state">US search trends are temporarily unavailable.</p>';
render();
}).catch(()=>{$('#lead').innerHTML='<div class="empty">Headlines temporarily unavailable. Please try again shortly.</div>';$('#feed').innerHTML='';$('#sideleads').innerHTML='';$('#trends').textContent='Trending topics temporarily unavailable.'});
