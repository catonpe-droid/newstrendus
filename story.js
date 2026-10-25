'use strict';
const byId=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cover=i=>'assets/'+(['US','Gaming','Technology','Business','Science','Entertainment','World','Sports'].includes(i.category)?i.category.toLowerCase():'news')+'.svg';
const requested=new URLSearchParams(location.search).get('id');
byId('date').textContent=new Date().toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'});
byId('year').textContent=new Date().getFullYear();
function timestamp(s){
 if(!s)return 'Publication date not provided by source';
 const d=new Date(s);return Number.isNaN(d.getTime())?'Date unavailable':d.toLocaleString('en-US',{dateStyle:'long',timeStyle:'short',timeZone:'UTC'})+' UTC';
}
function cleanSourceURL(u){try{const v=new URL(u);return v.protocol==='https:'?v.href:'#';}catch{return '#';}}
const context={
'US':{
 title:'How to follow this US story',
 paragraphs:[
 'This report was collected from a publisher’s RSS feed. Its headline and summary reflect information provided by that source at its publication time, not an independent investigation by NewsTrendus.',
 'For a developing US report, check the event date, the source of any numerical claims, statements from the relevant authorities and the publisher’s latest corrections. The source article is the right place to find the underlying evidence and complete context.'
 ],guide:'guides/verify-breaking-news.html',label:'Guide: how to verify breaking US news'},
'Sports':{
 title:'What to check in sports coverage',
 paragraphs:[
 'Sports news often moves quickly as sessions, matches and press conferences progress. A report published before the end of an event may describe a situation that has already changed.',
 'For a race, game or league update, look for the official event results, timing sheet, governing-body announcement and any later penalties or revisions before interpreting standings or a championship scenario.'
 ],guide:'guides/verify-breaking-news.html',label:'Guide: verifying fast-changing headlines'},
'Gaming':{
 title:'Confirmed update or gaming rumor?',
 paragraphs:[
 'Gaming stories can discuss confirmed publisher information, previews or early speculation. An RSS headline alone may not tell readers which category a claim belongs in.',
 'Check the official developer or publisher channels for announcements about release dates, platforms and gameplay. If a report refers to a leak or anonymous source, treat the claim as unconfirmed until reliable evidence is available.'
 ],guide:'guides/gaming-announcements-checklist.html',label:'Guide: verify trailers, release windows and platforms'},
'Technology':{
 title:'Putting a technology report in context',
 paragraphs:[
 'Technology headlines may describe a product launch, a technical demonstration, a planned rollout or a company statement. These are not always the same as general availability.',
 'Look for the developer’s documentation or official announcement, technical limitations, pricing scope and the date a feature will actually become available. Treat benchmark or performance claims as specific to the testing circumstances.'
 ],guide:'guides/understanding-us-news-feeds.html',label:'Guide: understand news sources and trends'},
'Business':{
 title:'How to read a business news update',
 paragraphs:[
 'Business coverage often blends reported facts, company guidance and outside forecasts. A single headline cannot capture every assumption behind a number or statement.',
 'For financial or corporate news, confirm dates, reported figures, official filings, accounting periods and the difference between actual results and projections. This page is for general news discovery, not investment advice.'
 ],guide:'guides/verify-breaking-news.html',label:'Guide: evaluating claims and attribution'},
'Science':{
 title:'Reading science headlines carefully',
 paragraphs:[
 'A science news preview may summarize early research, a press release or a finding that depends on particular study conditions. Headlines usually cannot communicate an entire method.',
 'For research claims, consider the original paper, study population, sample size, peer-review status and whether the result has been independently replicated. Do not interpret a preliminary headline as a medical or safety recommendation.'
 ],guide:'guides/verify-breaking-news.html',label:'Guide: tracing claims back to evidence'},
'Entertainment':{
 title:'Checking an entertainment update',
 paragraphs:[
 'Entertainment stories frequently mix a confirmed event, an interview, an industry report and speculation about future projects. A popular online discussion does not make all claims official.',
 'For cast announcements, release schedules, awards or studio decisions, compare coverage with original statements from organizers, studios or verified participants. Check dates so that older material is not mistaken for new news.'
 ],guide:'guides/gaming-announcements-checklist.html',label:'Guide: official announcements versus speculation'},
'World':{
 title:'Understanding an international report',
 paragraphs:[
 'International coverage may be updated as events develop and new accounts become available. Translations, local dates and different reporting time zones can affect how a story is presented.',
 'For a significant report, compare reliable sources, find primary statements where possible and distinguish verified events from allegations or forecasts. Avoid treating early figures or unconfirmed accounts as final.'
 ],guide:'guides/verify-breaking-news.html',label:'Guide: verify a developing report'}
};
fetch('news.json',{cache:'no-store'})
.then(r=>{if(!r.ok)throw Error('Feed unavailable');return r.json()})
.then(data=>{
 const all=Array.isArray(data.items)?data.items:[],a=all.find(x=>x.id===requested);
 if(!a){
  byId('reader').innerHTML='<div class="article-inside"><h1>Story no longer in the active feed</h1><p>RSS listings change as publishers release updates. Browse the latest coverage for the current source links.</p><a class="sourcebtn" href="index.html">Browse latest headlines</a></div>';
  byId('related').textContent='View all recent stories from our homepage.';
  return;
 }
 document.title=a.title+' | NewsTrendus';
 const origin=cleanSourceURL(a.url),ctx=context[a.category]||context.US;
 const summary=a.summary?.trim()?esc(a.summary.trim()):'This source feed did not provide a description for this headline. NewsTrendus does not add unverified details to fill the gap. Please consult the original reporting for the full account.';
 const date=timestamp(a.date);
 const para=ctx.paragraphs.map(t=>'<p>'+esc(t)+'</p>').join('');
 const factlist=[
  '<li><strong>Story:</strong> '+esc(a.title)+'</li>',
  '<li><strong>Reported by:</strong> '+esc(a.source||'Original news publisher')+'</li>',
  '<li><strong>Publication date:</strong> '+esc(date)+'</li>',
  '<li><strong>Section:</strong> '+esc(a.category||'News')+'</li>'
 ].join('');
 const photo=window.NewsTrendusPhotos?.forStory(a)||null;
 const photoURL=photo?photo.src:cover(a);
 const caption=photo
 ? 'Representative photo (not of the reported event). Photo by <a href="'+esc(photo.url)+'" target="_blank" rel="noopener noreferrer">'+esc(photo.artist)+'</a> on Pexels · '+esc(photo.license)+'.'
 : 'Original NewsTrendus category illustration. Not a documentary photo of this event.';
 const sourceLink='<a class="sourcebtn" href="'+esc(origin)+'" target="_blank" rel="noopener noreferrer">Read the full report at '+esc(a.source)+' ↗</a>';
 byId('reader').innerHTML=
 '<div class="article-inside"><span class="eyebrow">'+esc(a.category||'News')+' / Sourced news brief</span>'+
 '<h1 class="article-title">'+esc(a.title)+'</h1>'+
 '<div class="article-meta">Original publisher: <strong>'+esc(a.source)+'</strong> · '+esc(date)+' · RSS-based preview</div>'+
 '<div class="reader-tools"><button id="shareStory" type="button">Share this news brief</button><a href="index.html" style="font-size:13px;font-weight:700;color:#a9233d">← Back to US news</a></div></div>'+
 '<img class="article-graphic" src="'+esc(photoURL)+'" alt="'+esc(photo?'Representative '+photo.description:'Original category illustration')+'" loading="eager" decoding="async" onerror="this.onerror=null;this.src=\''+cover(a)+'\'">'+
 '<div class="article-inside"><p class="article-caption">'+caption+'</p>'+
 '<div class="article-body">'+
 '<h2>News at a glance</h2><p>'+summary+'</p>'+
 '<div class="story-notice">This preview comes from publisher-supplied RSS text. It may be shorter than the full report and can omit important updates, quotes and context.</div>'+
 '<h2>Key details from the source listing</h2><ul class="source-facts">'+factlist+'</ul>'+
 '<h2>'+esc(ctx.title)+'</h2>'+para+
 '<div class="story-more"><h2>Related reading</h2><p>For practical advice on evaluating developments like this, see our original <a href="'+esc(ctx.guide)+'" style="color:#aa1c32;text-decoration:underline">'+esc(ctx.label)+'</a>.</p></div>'+
 '<h2>Where to verify the report</h2><p>NewsTrendus does not reproduce the publisher’s full article or claim its reporting as our own. Open the source for primary details, direct quotations and updates. The link below opens the original publication.</p>'+
 sourceLink+
 '<p class="state">Source credit is visible by design. Context guidance is general and does not add facts to the specific event.</p>'+
 '</div></div>';
 const related=all.filter(x=>x.id!==a.id&&x.category===a.category).slice(0,9);
 byId('related').innerHTML=related.length?related.map(x=>
  '<a class="relatedlink" href="story.html?id='+encodeURIComponent(x.id)+'">'+
  esc(x.title)+'<small>'+esc(x.source)+'</small></a>').join(''):'<p class="state">Explore all recent stories on the homepage.</p>';
 byId('category').textContent=a.category||'News';
 byId('trendcount').textContent=Array.isArray(data.trends)?data.trends.length:0;
 const btn=byId('shareStory');
 btn?.addEventListener('click',async()=>{
  const url=location.href;
  try{
   if(navigator.share)await navigator.share({title:a.title,url});
   else if(navigator.clipboard){await navigator.clipboard.writeText(url);btn.textContent='Link copied';}
  }catch{}
 });
})
.catch(()=>{byId('reader').innerHTML='<div class="article-inside"><h1>News currently unavailable</h1><p>Our source listing could not be loaded. Return to the homepage and try again later.</p><a class="sourcebtn" href="index.html">Back to latest news</a></div>';});
