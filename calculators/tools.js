/* NewsTrendus USA calculators, no API, no tracking, works fully offline. */
(()=>{'use strict';
const money=(v)=>Number.isFinite(v)?new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(v):'—';
const num=(v,def=0)=>{const n=Number(v);return Number.isFinite(n)?n:def};
const fmtMonths=m=>m>=12?Math.floor(m/12)+' yr '+(m%12)+' mo':m+' months';
const monthlyPayment=(p,r,n)=>n>0?(r===0?p/n:p*r/(1-Math.pow(1+r,-n))):NaN;
const inputs=(root)=>Object.fromEntries([...root.querySelectorAll('[name]')].map(el=>[el.name,el]));
function calc(root) {
 const els=inputs(root),v=(key)=>num(els[key]?.value);
 const kind=root.dataset.calculator;
 let result=null;
 if(kind==='tip'){
   const bill=Math.max(0,v('bill')),pct=Math.max(0,v('tip')),people=Math.max(1,Math.floor(v('people')));
   const tip=bill*pct/100,total=bill+tip;
   result={primary:money(total/people),label:'Total per person',metrics:[['Tip amount',money(tip)],['Total bill',money(total)],['Tip per person',money(tip/people)]]};
 } else if(kind==='mortgage'){
   const price=Math.max(0,v('price')),dp=Math.max(0,Math.min(price,v('down'))),apr=Math.max(0,v('rate')),years=v('years');
   const loan=price-dp,n=Math.round(years*12),rate=apr/1200;
   if(years<=0||apr>100||n>600)return error(root,'Enter a term from 1 to 50 years and a valid interest rate.');
   const pi=monthlyPayment(loan,rate,n),tax=Math.max(0,v('tax'))/12,ins=Math.max(0,v('insurance')),hoa=Math.max(0,v('hoa'));
   result={primary:money(pi+tax+ins+hoa),label:'Estimated total monthly payment',metrics:[['Principal and interest',money(pi)],['Property tax / mo',money(tax)],['Insurance + HOA / mo',money(ins+hoa)],['Loan balance at start',money(loan)],['Total loan interest',money(pi*n-loan)]]};
 } else if(kind==='auto'){
   const price=Math.max(0,v('price')),down=Math.max(0,v('down')),trade=Math.max(0,v('trade')),tax=Math.max(0,v('tax')),fees=Math.max(0,v('fees')),apr=Math.max(0,v('rate')),n=Math.round(v('months'));
   if(n<=0||n>120||apr>100)return error(root,'Choose 1–120 months and a valid interest rate.');
   const taxAmount=price*tax/100,loan=Math.max(0,price+taxAmount+fees-down-trade),monthly=monthlyPayment(loan,apr/1200,n);
   result={primary:money(monthly),label:'Estimated monthly car payment',metrics:[['Amount financed',money(loan)],['Estimated sales tax',money(taxAmount)],['Interest over term',money(monthly*n-loan)],['Total monthly payments',money(monthly*n)]]};
 } else if(kind==='credit'){
   const balance=Math.max(0,v('balance')),apr=Math.max(0,v('rate')),monthly=v('payment'),rate=apr/1200;
   if(balance===0){result={primary:'$0.00',label:'Balance already paid',metrics:[['Interest','0.00'],['Months','0']]} }
   else if(monthly<=balance*rate || monthly<=0){return error(root,'Monthly payment must exceed the first month’s interest to pay off this balance. Increase your payment.');}
   else {
     let owed=balance,interest=0,months=0;while(owed>.005&&months<1200){const i=owed*rate;interest+=i;owed=owed+i-Math.min(monthly,owed+i);months++}
     if(months>=1200)return error(root,'Payoff exceeds 100 years. Try a higher monthly payment.');
     result={primary:fmtMonths(months),label:'Estimated payoff time',metrics:[['Total estimated interest',money(interest)],['Total repaid',money(balance+interest)],['Monthly payment',money(monthly)]]};
   }
 } else if(kind==='salary'){
   const pay=Math.max(0,v('pay')),hrs=Math.max(0,v('hours')),weeks=Math.max(0,v('weeks'));
   let yearly=0;switch(els.period?.value){case'weekly':yearly=pay*weeks;break;case'biweekly':yearly=pay*weeks/2;break;case'monthly':yearly=pay*12;break;case'annual':yearly=pay;break;default:yearly=pay*hrs*weeks}
   if(weeks>53||hrs>168)return error(root,'Enter realistic working hours and weeks.');
   result={primary:money(yearly),label:'Annual GROSS salary (before taxes)',metrics:[['Monthly gross',money(yearly/12)],['Weekly gross',money(yearly/52)],['Hourly equivalent',money(yearly/(hrs*weeks)||0)],['Every two weeks',money(yearly/26)]]};
 } else if(kind==='rent'){
   const annual=Math.max(0,v('income')),share=Math.max(0,Math.min(100,v('percent'))),debt=Math.max(0,v('debt')),utilities=Math.max(0,v('utilities'));
   const available=Math.max(0,annual/12*share/100-debt-utilities);
   result={primary:money(available),label:'Illustrative monthly rent ceiling',metrics:[['Monthly gross income',money(annual/12)],['Housing allocation',money(annual/12*share/100)],['Debt + utilities deducted',money(debt+utilities)],['Annual rent at this level',money(available*12)]]};
 }
 if(!result)return;
 const output=root.querySelector('[data-results]');if(!output)return;
 output.innerHTML='<p class="t-label">'+result.label+'</p><strong class="t-amount">'+result.primary+'</strong><dl class="t-metrics">'+result.metrics.map(([k,val])=>'<div><dt>'+k+'</dt><dd>'+val+'</dd></div>').join('')+'</dl>';
}
function error(root,msg){const output=root.querySelector('[data-results]');if(output)output.innerHTML='<div class="t-error" role="status">'+msg+'</div>';}
document.querySelectorAll('[data-calculator]').forEach(root=>{
  root.addEventListener('input',()=>calc(root));root.addEventListener('change',()=>calc(root));
  const reset=root.querySelector('[data-reset]');if(reset)reset.addEventListener('click',()=>{root.querySelectorAll('input').forEach(e=>e.value=e.defaultValue);root.querySelectorAll('select').forEach(e=>e.selectedIndex=0);calc(root)});
  calc(root);
});
})();