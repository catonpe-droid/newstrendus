'use strict';
const $=s=>document.querySelector(s), $$=s=>document.querySelectorAll(s);
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cover=i=>'assets/'+(['US','Gaming','Technology','Business','Science','Entertainment','World','Sports','Health','Trending'].includes(i.category)?i.category.toLowerCase():'news')+'.svg';
const day=d=>{if(!d)return 'Latest';const x=new Date(d);return isNaN(x)?'Latest':x.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})};
const link=i=>'story.html?id='+encodeURIComponent(i.id||'');
const shot=i=>window.NewsTrendusPhotos?.forStory(i)||null;
const imageHTML=(i,priority=false)=>{
 const p=shot(i),alt=(p?'Representative '+p.description:'Editorial '+i.category+' illustration');
 const url=p?p.src:cover(i);
 const fallback=cover(i);
 return '<img loading="'+(priority?'eager':'lazy')+'" decoding="async" src="'+escapeHTML(url)+'" alt="'+escapeHTML(alt)+'" onerror="this.onerror=null;this.src=\''+fallback+'\'">';
};
const photoCredit=i=>{
 const p=shot(i);
 return p?'<span class="photo-attribution">Representative photo: <a href="'+escapeHTML(p.url)+'" target="_blank" rel="noopener noreferrer">'+escapeHTML(p.artist)+' / Pexels</a></span>':'<span class="photo-attribution">NewsTrendus editorial illustration</span>';
};
let articles=[],activeCat='All',search='',limit=16;
const brandDate=new Date().toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'});
$('#date').textContent=brandDate;$('#year').textContent=new Date().getFullYear();
function feature(item,small=false){
if(!item)return '';
return '<article class="'+(small?'feature-sm':'feature')+'">'+
imageHTML(item,!small)+
'<span class="artnote">Representative photo (not of this event)</span>'+
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
$('#count').textContent=list.length+' headlines';
$('#listTitle').textContent=activeCat==='All'?'Latest Stories':activeCat+' News';
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
fetch('news.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('feed unavailable');return r.json()}).then(d=>{
articles=Array.isArray(d.items)?d.items:[];articles=articles.filter(x=>x&&x.title&&x.url&&x.id);
$('#refreshed').textContent=d.updated?'Refreshed '+day(d.updated):'Updates pending';
$('#tickerHeadline').textContent=articles.length?articles[0].title:'Latest headlines coming soon';
$('#tickerHeadline').href=articles.length?link(articles[0]):'index.html';
$('#countTotal').textContent=articles.length;
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
