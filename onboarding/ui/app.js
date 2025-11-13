(function(){
  const $ = s => document.querySelector(s);
  const $$ = s => Array.from(document.querySelectorAll(s));
  const state = { step: 1, total: 5, done: JSON.parse(localStorage.getItem('pn_done')||'[]') };

  function setStep(n){
    state.step = n; updateUI();
  }
  function toggleDone(n, val){
    const idx = state.done.indexOf(n);
    if(val){ if(idx===-1) state.done.push(n); }
    else { if(idx!==-1) state.done.splice(idx,1); }
    localStorage.setItem('pn_done', JSON.stringify(state.done));
    updateRail(); updateProgress();
  }
  function updateRail(){
    $$('#steps .step').forEach(li=>{
      const n = parseInt(li.dataset.step,10);
      li.classList.toggle('active', n===state.step);
      li.classList.toggle('done', state.done.includes(n));
    });
  }
  function updateProgress(){
    $('#progress').textContent = state.done.length;
  }
  function copyHandler(e){
    const btn = e.target.closest('.copy');
    if(!btn) return; e.preventDefault();
    const text = btn.dataset.copy.replaceAll('&lt;','<').replaceAll('&gt;','>');
    navigator.clipboard.writeText(text).then(()=>{
      btn.textContent = 'Copied!';
      setTimeout(()=>btn.textContent='Copy', 900);
    }).catch(()=>{
      btn.textContent = 'Copy failed';
      setTimeout(()=>btn.textContent='Copy', 1200);
    });
  }
  function renderStep(){
    const tpl = document.getElementById(`tpl-step-${state.step}`);
    $('#content').innerHTML = tpl ? tpl.innerHTML : '<p>Step not found.</p>';
    $('#panel-title').textContent = {
      1: 'Step 1 — Identity',
      2: 'Step 2 — Blind Listing',
      3: 'Step 3 — Secure Messaging',
      4: 'Step 4 — RANDPAY',
      5: 'Step 5 — Gateway'
    }[state.step] || 'Onboarding';
  }
  function updateButtons(){
    const prev = $('#prev'), next = $('#next');
    prev.disabled = state.step<=1; next.disabled = state.step>=state.total;
  }
  function updateUI(){
    renderStep(); updateRail(); updateButtons(); updateProgress();
  }

  // events
  $('#steps').addEventListener('click', e=>{
    const li = e.target.closest('.step'); if(!li) return;
    setStep(parseInt(li.dataset.step,10));
  });
  $('#prev').addEventListener('click', ()=> setStep(Math.max(1, state.step-1)) );
  $('#next').addEventListener('click', ()=> setStep(Math.min(state.total, state.step+1)) );
  $('#mark-done').addEventListener('click', ()=> toggleDone(state.step, true));
  $('#content').addEventListener('click', copyHandler);

  // init
  updateUI();
})();
