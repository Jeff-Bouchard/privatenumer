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

  function openModal(title, content){
    $('#modal-title').textContent = title;
    $('#script').value = content;
    $('#download-script').href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(content);
    $('#modal').classList.remove('hidden');
  }
  function closeModal(){ $('#modal').classList.add('hidden'); }

  function shHeader(){
    return [
      '#!/usr/bin/env bash',
      'set -euo pipefail',
      'IFS=$"\n\t"',
      'echo "🔒 Privateness Onboarding Script — Git Bash / POSIX"',
      'echo "This script will prompt for minimal inputs and run commands for you."',
      'echo',
    ].join('\n');
  }

  function blockInstall(){
    return [
      'echo "[0/5] Installing Python tooling (uv) if missing..."',
      'if command -v uv >/dev/null 2>&1; then',
      '  uv venv || true',
      '  uv pip install cryptography >/dev/null',
      '  uv pip install git+https://github.com/ness-network/pyuheprng.git >/dev/null',
      '  echo "uv + deps ready."',
      'else',
      '  echo "uv not found — falling back to python/pip (user site)."',
      '  if command -v python3 >/dev/null 2>&1; then PY=python3; elif command -v python >/dev/null 2>&1; then PY=python; else echo "Python not found. Install Python then re-run."; exit 1; fi',
      '  "$PY" -m pip install --user --quiet cryptography',
      '  "$PY" -m pip install --user --quiet git+https://github.com/ness-network/pyuheprng.git',
      '  echo "python/pip deps ready (user site)."',
      'fi',
      'hash -r || true',
      'echo',
    ].join('\n');
  }

  function blockIdentity(){
    return [
      'echo "[1/5] Identity — generate and export WORM"',
      'read -rp "Enter username (alnum, no spaces): " USERNAME',
      './keygen user "$USERNAME" 5',
      './key worm "$HOME/.privateness-keys/$USERNAME.key.json"',
      'echo',
      'read -rp "Enter Emercoin wallet passphrase (will echo): " EMC_PASS',
      'WORM_ESCAPED=$(printf %q "$(cat \"$HOME/.privateness-keys/$USERNAME.key.json\")")',
      'emercoin-cli walletpassphrase "$EMC_PASS" 300',
      'emercoin-cli name_new "worm:user:ness:$USERNAME" "$WORM_ESCAPED" 365',
      'echo "WORM published: worm:user:ness:$USERNAME"',
      'echo',
    ].join('\n');
  }

  function blockListing(){
    return [
      'echo "[2/5] Blind listing — publish minimal JSON"',
      'read -rp "Enter opaque listing id: " OPAQUE',
      'read -rp "Enter SHA-256 of signed off-chain record: " COMMIT',
      'MIN_JSON=$(printf \'{"worm_ref":"worm:user:ness:%s","commitment":"%s","capabilities":7,"rev":1}\' "$USERNAME" "$COMMIT")',
      'emercoin-cli name_new "ness:sms:listing:$OPAQUE" "$MIN_JSON" 365',
      'echo "Listing published: ness:sms:listing:$OPAQUE"',
      'echo',
    ].join('\n');
  }

  function blockSecure(){
    return [
      'echo "[3/5] Secure messaging — encrypt/sign using keyfiles"',
      'read -rp "Path to renter keyfile (~/.privateness-keys/renter.key.json): " RENTER_KF',
      'RENTER_KF=${RENTER_KF:-$HOME/.privateness-keys/renter.key.json}',
      'read -rp "Path to provider keyfile (~/.privateness-keys/$USERNAME.key.json): " PROVIDER_KF',
      'PROVIDER_KF=${PROVIDER_KF:-$HOME/.privateness-keys/$USERNAME.key.json}',
      'read -rp "Message file to send (sms.txt): " SMSF',
      'SMSF=${SMSF:-sms.txt}',
      'python tools/ptool_encrypt.py --peer-pub-keyfile "$RENTER_KF" --peer-pub-field x25519.public --in "$SMSF" --out sms.enc',
      'python tools/ptool_sign.py --priv-keyfile "$PROVIDER_KF" --priv-field ed25519.private --in sms.enc --out sms.sig',
      'echo "Envelope: sms.enc, Signature: sms.sig"',
      'echo',
    ].join('\n');
  }

  function blockRandpay(){
    return [
      'echo "[4/5] RANDPAY — 1 EMC, risk 1/6, 6h"',
      'echo "Run these interactively between provider and renter terminals:"',
      'echo "  Provider: emercoin-cli randpay_mkchap 1 6 21600"',
      'echo "  Renter:   emercoin-cli randpay_mktx \"<chap>\" 21600 0"',
      'echo "  Provider: emercoin-cli randpay_accept \"<txhex>\" 2"',
      'echo "Expected cost ≈ 1/6 EMC per attempt; rotate chap after accept/timeout."',
      'echo',
    ].join('\n');
  }

  function blockVerify(){
    return [
      'echo "[5/5] Verify and decrypt — renter side"',
      'read -rp "Path to provider keyfile (ed25519 public) (~/.privateness-keys/$USERNAME.key.json): " PROVIDER_KF2',
      'PROVIDER_KF2=${PROVIDER_KF2:-$HOME/.privateness-keys/$USERNAME.key.json}',
      'read -rp "Path to renter keyfile (~/.privateness-keys/renter.key.json): " RENTER_KF2',
      'RENTER_KF2=${RENTER_KF2:-$HOME/.privateness-keys/renter.key.json}',
      'python tools/ptool_verify.py --pub-keyfile "$PROVIDER_KF2" --pub-field ed25519.public --in sms.enc --sig sms.sig',
      'python tools/ptool_decrypt.py --priv-keyfile "$RENTER_KF2" --priv-field x25519.private --in sms.enc --out sms.txt',
      'python tools/ptool_receipt.py \
  --from-priv-keyfile "$PROVIDER_KF2" --from-priv-field ed25519.private \
  --from-pub-keyfile "$PROVIDER_KF2"  --from-pub-field ed25519.public \
  --to-pub-keyfile "$RENTER_KF2"     --to-pub-field ed25519.public \
  --envelope sms.enc --out receipt.json',
      'echo "Decrypted: sms.txt, Receipt: receipt.json"',
      'echo',
    ].join('\n');
  }

  function buildFullScript(){
    return [
      shHeader(),
      blockInstall(),
      blockIdentity(),
      blockListing(),
      blockSecure(),
      blockRandpay(),
      blockVerify(),
      'echo "✅ All steps finished."'
    ].join('\n');
  }

  function buildStepScript(n){
    const blocks = {1:blockIdentity,2:blockListing,3:blockSecure,4:blockRandpay,5:blockVerify};
    return [shHeader(), (blocks[n]||(()=>"echo 'Step not found'"))()].join('\n');
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
  $('#gen-step').addEventListener('click', ()=> openModal(`Step ${state.step} — script`, buildStepScript(state.step)) );
  $('#gen-all').addEventListener('click', ()=> openModal('Full onboarding script', buildFullScript()) );
  $('#modal-close').addEventListener('click', closeModal);
  $('#copy-script').addEventListener('click', ()=>{
    const ta = $('#script'); ta.select(); document.execCommand('copy');
  });

  // init
  updateUI();
})();
