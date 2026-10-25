/* Everyday US calculators. Browser-local math; not medical, tax or financial advice. */
(()=>{'use strict';
const $=(r,n)=>r.querySelector('[name="'+n+'"]');
const val=(r,n)=>Number($(r,n)?.value);
const fmt=(n,places=2)=>Number.isFinite(n)?n.toLocaleString('en-US',{maximumFractionDigits:places}):'—';
const usd=n=>Number.isFinite(n)?new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(n):'—';
function result(el,title,label,entries=[]){
 const box=el.querySelector('[data-results]');if(!box)return;
 box.replaceChildren();const p=document.createElement('p');p.className='t-label';p.textContent=label;
 const amount=document.createElement('strong');amount.className='t-amount';amount.textContent=title;
 const dl=document.createElement('dl');dl.className='t-metrics';
 for(const [name,number] of entries){const div=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=name;dd.textContent=number;div.append(dt,dd);dl.append(div)}
 box.append(p,amount,dl);
}
function error(el,msg){let box=el.querySelector('[data-results]');if(box)box.textContent=msg}
function run(el){
 let kind=el.dataset.daily;
 const v=x=>val(el,x),good=x=>Number.isFinite(x)&&x>=0;
 if(kind==='sales-tax'){
  const p=v('price'),r=v('rate'),fee=v('fees'),qty=v('qty');
  if(![p,r,fee,qty].every(good)||r>100||qty<=0)return error(el,'Enter valid price, tax rate, fees and quantity.');
  const base=p*qty,tax=base*r/100;result(el,usd(base+tax+fee),'Estimated purchase total',[['Before tax',usd(base)],['Sales tax',usd(tax)],['Other fees',usd(fee)]]);
 }else if(kind==='discount'){
  const p=v('price'),off=v('discount'),tax=v('tax');
  if(![p,off,tax].every(good)||off>100||tax>100)return error(el,'Enter a valid discount and sales tax percentage (0–100).');
  const after=p*(1-off/100),amount=after*tax/100;
  result(el,usd(after+amount),'Final total after discount and tax',[['Discount savings',usd(p-after)],['Price after discount',usd(after)],['Sales tax',usd(amount)]]);
 }else if(kind==='percentage'){
  const base=v('base'),part=v('part');
  if(!Number.isFinite(base)||!Number.isFinite(part))return error(el,'Enter valid numbers.');
  result(el,base===0?'Undefined':fmt(part/base*100)+'%','Part as percentage of total',[['Part',fmt(part)],['Total',fmt(base)],['Total minus part',fmt(base-part)]]);
 }else if(kind==='bmi'){
  const lb=v('weight'),feet=v('feet'),inch=v('inches');
  const totalInches=feet*12+inch;
  if(!good(lb)||!good(feet)||!good(inch)||lb<=0||totalInches<=0)return error(el,'Enter positive weight and height.');
  const bmi=703*lb/(totalInches*totalInches);
  const category=bmi<18.5?'Underweight':bmi<25?'Healthy weight range':bmi<30?'Overweight range':'Obesity range';
  result(el,fmt(bmi,1),'Adult BMI (illustrative)',[['Adult BMI classification',category],['Height',Math.floor(totalInches/12)+' ft '+fmt(totalInches%12)+' in'],['Weight',fmt(lb)+' lb']]);
 }else if(kind==='age'){
  const birth=$(el,'birth')?.value,asOf=$(el,'asof')?.value;
  if(!birth||!asOf)return error(el,'Choose both birth date and date to compare.');
  const b=new Date(birth+'T12:00:00Z'),d=new Date(asOf+'T12:00:00Z');
  if(d<b)return error(el,'Comparison date must be on or after date of birth.');
  let years=d.getUTCFullYear()-b.getUTCFullYear();const birthdayPassed=d.getUTCMonth()>b.getUTCMonth()||(d.getUTCMonth()===b.getUTCMonth()&&d.getUTCDate()>=b.getUTCDate());if(!birthdayPassed)years--;
  const dayCount=Math.floor((d-b)/86400000);
  result(el,years+' years','Age on selected date',[['Days elapsed',fmt(dayCount,0)],['Birth date',birth],['Comparison date',asOf]]);
 }else if(kind==='unit'){
  const amount=v('amount'),unit=$(el,'measure')?.value;if(!Number.isFinite(amount))return error(el,'Enter a valid amount.');
  const conv={miles:['Kilometers',1.609344,'km'],km:['Miles',1/1.609344,'mi'],lb:['Kilograms',0.45359237,'kg'],kg:['Pounds',1/0.45359237,'lb'],feet:['Meters',0.3048,'m'],meters:['Feet',1/0.3048,'ft'],gallons:['Liters',3.785411784,'L'],liters:['US gallons',1/3.785411784,'gal'],fahrenheit:['Celsius',null,'°C'],celsius:['Fahrenheit',null,'°F']};
  const c=conv[unit];if(!c)return error(el,'Choose a unit conversion.');
  const output=unit==='fahrenheit'?(amount-32)*5/9:unit==='celsius'?amount*9/5+32:amount*c[1];
  result(el,fmt(output,4)+' '+c[2],c[0],[['Original input',fmt(amount,4)+' '+unit],['Converted value',fmt(output,4)+' '+c[2]]]);
 }
}
document.querySelectorAll('[data-daily]').forEach(r=>{
 r.addEventListener('input',()=>run(r));r.addEventListener('change',()=>run(r));
 r.querySelector('[data-reset]')?.addEventListener('click',()=>{for(const i of r.querySelectorAll('input')){if(i.type!=='date')i.value=i.defaultValue}for(const x of r.querySelectorAll('select'))x.selectedIndex=0;run(r)});
 run(r);
});
})();