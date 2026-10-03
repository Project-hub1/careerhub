const toastEl=document.getElementById('toast');
function toast(message){if(!toastEl)return;toastEl.textContent=message;toastEl.classList.add('show');clearTimeout(window.__toastTimer);window.__toastTimer=setTimeout(()=>toastEl.classList.remove('show'),2400)}

document.addEventListener('click',async(e)=>{
  const menu=e.target.closest('#mobileMenu');
  if(menu){const nav=document.getElementById('navLinks');const open=nav.classList.toggle('open');menu.setAttribute('aria-expanded',open);return;}
  const close=e.target.closest('.flash-close');if(close){close.closest('.flash')?.remove();return;}
  const toggle=e.target.closest('.filter-toggle');if(toggle){document.querySelector('.filter-body')?.classList.toggle('open');return;}
  const btn=e.target.closest('.save-btn');if(!btn)return;
  const id=btn.dataset.jobId;btn.disabled=true;
  try{const r=await fetch(`/jobs/${id}/save`,{method:'POST',headers:{'X-CSRFToken':document.querySelector('meta[name="csrf-token"]')?.content||'','Accept':'application/json'}});const d=await r.json();if(r.status===401){window.location.href=`/login?next=${encodeURIComponent(location.pathname+location.search)}`;return}if(d.ok){btn.classList.toggle('saved',d.saved);btn.setAttribute('aria-pressed',String(d.saved));btn.textContent=d.saved?(btn.classList.contains('big')?'Saved':'Saved'):(btn.classList.contains('big')?'Save job':'Save');toast(d.saved?'Job saved':'Job removed from saved jobs')}else toast(d.message||'Unable to save job.')}catch(err){toast('Network error. Please try again.')}finally{btn.disabled=false;}
});

document.addEventListener('submit',(e)=>{const form=e.target;if(form.matches('.js-confirm')){const msg=form.dataset.confirm||'Are you sure?';if(!window.confirm(msg))e.preventDefault();}});
window.copyJobLink=async()=>{try{await navigator.clipboard.writeText(location.href);toast('Job link copied')}catch{toast('Copy failed — copy the URL from your browser')}};
