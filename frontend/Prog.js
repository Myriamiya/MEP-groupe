let currentUser   = null;
let chatHistory   = [];
let isLoading     = false;
let sidebarOpen   = true;
let attachedFiles = [];
let registeredUsers = [];
let conversations = [];
let activeConvId  = null;
let userSettings  = {
  name:'', verbose:false, sources:true,
  memory:true, retention:'forever',
  autoread:false, voiceGender:'female', voiceRate:1.0, voicePitch:1.0, voiceInput:true
};

function saveUsersToStorage(){
  try{ localStorage.setItem('medicia_users', JSON.stringify(registeredUsers)); }catch(e){ console.warn('Sauvegarde locale impossible', e); }
}
function loadUsersFromStorage(){
  try{
    const raw = localStorage.getItem('medicia_users');
    if(raw){ registeredUsers = JSON.parse(raw); }
  }catch(e){ console.warn('Lecture locale impossible', e); }
}
loadUsersFromStorage();

let currentUtterance = null;
let isSpeaking = false;
let activeTtsBtn = null;


let recognition = null;
let isListening = false;


function getVoices() { return window.speechSynthesis ? window.speechSynthesis.getVoices() : []; }

function pickVoice(gender) {
  const voices = getVoices();
  const lang = ['fr-FR', 'fr'];

  const frVoices = voices.filter(v => lang.some(l => v.lang.startsWith(l)));
  if (frVoices.length === 0) return voices[0] || null;

  const femaleHints = ['female','femme','amelie','marie','lea','julie','claire','thomas'];
  const maleHints = ['male','homme','nicolas','pierre','mathieu'];
  if (gender === 'female') {
    const found = frVoices.find(v => femaleHints.some(h => v.name.toLowerCase().includes(h)));
    return found || frVoices[0];
  } else {
    const found = frVoices.find(v => maleHints.some(h => v.name.toLowerCase().includes(h)));
    return found || frVoices[frVoices.length - 1] || frVoices[0];
  }
}

function speakText(text, btn) {
  if (!window.speechSynthesis) { alert('La synthèse vocale n\'est pas supportée par votre navigateur.'); return; }

  if (isSpeaking) {
    window.speechSynthesis.cancel();
    if (activeTtsBtn) { activeTtsBtn.classList.remove('speaking'); activeTtsBtn.textContent = '🔊 Écouter'; }
    if (activeTtsBtn === btn) { isSpeaking = false; activeTtsBtn = null; return; }
  }
  const cleanText = text.replace(/<[^>]*>/g, '').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&').replace(/📎[^\n]*/g,'').trim();
  const utter = new SpeechSynthesisUtterance(cleanText);
  utter.lang = 'fr-FR';
  utter.rate = parseFloat(userSettings.voiceRate) || 1.0;
  utter.pitch = parseFloat(userSettings.voicePitch) || 1.0;
  const voice = pickVoice(userSettings.voiceGender);
  if (voice) utter.voice = voice;
  utter.onstart = () => { isSpeaking = true; activeTtsBtn = btn; if (btn) { btn.classList.add('speaking'); btn.innerHTML = '⏹️ Arrêter'; } };
  utter.onend = utter.onerror = () => { isSpeaking = false; activeTtsBtn = null; if (btn) { btn.classList.remove('speaking'); btn.innerHTML = '🔊 Écouter'; } };
  currentUtterance = utter;
  window.speechSynthesis.speak(utter);
}

function previewVoice() {
  speakText('Bonjour, je suis MEDIC IA, votre assistant médical intelligent. Comment puis-je vous aider aujourd\'hui ?', null);
}

function updateVoicePreview() {
  const gender = document.getElementById('setting-voice-gender').value;
  const voices = getVoices();
  const voice = pickVoice(gender);
  const label = document.getElementById('voice-preview-name');
  if (label) label.textContent = voice ? `Voix : ${voice.name}` : 'Voix : par défaut';
}


if (window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = updateVoicePreview;
  setTimeout(updateVoicePreview, 500);
}


function initRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;
  const r = new SpeechRecognition();
  r.lang = 'fr-FR';
  r.continuous = true;
  r.interimResults = true;
  r.onresult = (e) => {
    let interim = '', final = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const t = e.results[i][0].transcript;
      if (e.results[i].isFinal) final += t;
      else interim += t;
    }
    const ta = document.getElementById('chat-input');
    const bar = document.getElementById('transcription-bar');
    const transcText = document.getElementById('transcription-text');
    if (interim) { transcText.textContent = interim; bar.style.display = 'flex'; }
    if (final) {
      ta.value = (ta.value + ' ' + final).trim();
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
      updateSendBtn();
      transcText.textContent = 'En écoute...';
    }
  };
  r.onerror = (e) => { console.warn('STT error:', e.error); stopListening(); };
  r.onend = () => { if (isListening) r.start(); };
  return r;
}

function toggleVoiceInput() {
  if (!userSettings.voiceInput) { alert('La dictée vocale est désactivée dans les paramètres.'); return; }
  if (isListening) { stopListening(); } else { startListening(); }
}

function startListening() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) { alert('La reconnaissance vocale n\'est pas supportée par votre navigateur (Chrome recommandé).'); return; }
  if (!recognition) recognition = initRecognition();
  try {
    recognition.start();
    isListening = true;
    document.getElementById('mic-btn').classList.add('listening');
    document.getElementById('mic-btn').textContent = '⏹️';
    document.getElementById('mic-btn').title = 'Arrêter la dictée';
    document.getElementById('transcription-bar').style.display = 'flex';
  } catch(e) { console.warn('mic start error', e); }
}

function stopListening() {
  isListening = false;
  if (recognition) { try { recognition.stop(); } catch(e){} }
  document.getElementById('mic-btn').classList.remove('listening');
  document.getElementById('mic-btn').textContent = '🎙️';
  document.getElementById('mic-btn').title = 'Dicter votre message';
  document.getElementById('transcription-bar').style.display = 'none';
}


function showLogin()    { document.getElementById('register-page').classList.remove('active'); document.getElementById('login-page').classList.add('active'); }
function showRegister() { document.getElementById('login-page').classList.remove('active'); document.getElementById('register-page').classList.add('active'); }

function handleRegister() {
  const name=document.getElementById('reg-name').value.trim(), email=document.getElementById('reg-email').value.trim();
  const pass=document.getElementById('reg-pass').value, pass2=document.getElementById('reg-pass2').value;
  const errEl=document.getElementById('reg-error'), sucEl=document.getElementById('reg-success'), btn=document.getElementById('reg-btn');
  errEl.style.display='none'; sucEl.style.display='none';
  if(!name||!email||!pass||!pass2){errEl.textContent='⚠️ Veuillez remplir tous les champs.';errEl.style.display='block';return;}
  if(pass.length<6){errEl.textContent='⚠️ Mot de passe trop court.';errEl.style.display='block';return;}
  if(pass!==pass2){errEl.textContent='⚠️ Les mots de passe ne correspondent pas.';errEl.style.display='block';return;}
  if(registeredUsers.find(u=>u.email===email)){errEl.textContent='⚠️ Email déjà utilisé.';errEl.style.display='block';return;}
  btn.disabled=true; btn.textContent='Création...';
  setTimeout(()=>{
    registeredUsers.push({name,email,password:pass,conversations:[]});
    saveUsersToStorage();
    sucEl.textContent='✅ Compte créé !'; sucEl.style.display='block';
    btn.disabled=false; btn.textContent='Créer mon compte';
    document.getElementById('login-email').value=email;
    setTimeout(()=>showLogin(),1400);
  },800);
}

function handleLogin() {
  const email=document.getElementById('login-email').value.trim(), pass=document.getElementById('login-pass').value;
  const errEl=document.getElementById('login-error'), btn=document.getElementById('login-btn');
  errEl.style.display='none';
  if(!email||!pass){errEl.textContent='⚠️ Veuillez remplir tous les champs.';errEl.style.display='block';return;}
  const user=registeredUsers.find(u=>u.email===email&&u.password===pass);
  if(!user){errEl.textContent='⚠️ Email ou mot de passe incorrect.';errEl.style.display='block';return;}
  btn.disabled=true; btn.textContent='Connexion...';
  document.getElementById('login-page').classList.remove('active');
  showLoadingPage(user);
}


function showLoadingPage(user) {
  const page=document.getElementById('loading-page'),bar=document.getElementById('loading-bar'),label=document.getElementById('loading-label');
  page.classList.add('visible');
  const steps=[{id:'step-1',label:'Vérification des identifiants...',pct:25},{id:'step-2',label:'Chargement du profil médical...',pct:50},{id:'step-3',label:'Connexion à la base de données...',pct:75},{id:'step-4',label:"Préparation de l'interface...",pct:100}];
  let i=0;
  function nextStep(){
    if(i>=steps.length){
      setTimeout(()=>{
        page.classList.remove('visible');
        currentUser={name:user.name,email:user.email};
        userSettings.name=user.name;
        document.getElementById('user-name-s').textContent=currentUser.name;
        const init=currentUser.name.split(' ').filter(w=>w.length>0).map(w=>w[0]).join('').slice(0,2).toUpperCase();
        document.getElementById('user-avatar-s').textContent=init;
        conversations=user.conversations||[];
        renderUsersSwitcher(); renderHistoryList(); syncMemoryBadge();
        buildWelcome();
        document.getElementById('app').classList.add('visible');
        document.getElementById('login-btn').disabled=false;
        document.getElementById('login-btn').textContent='Se connecter';
      },400); return;
    }
    const s=steps[i]; bar.style.width=s.pct+'%'; label.textContent=s.label;
    document.getElementById(s.id).classList.add('done'); document.getElementById(s.id).querySelector('.step-icon').textContent='✓';
    i++; setTimeout(nextStep,700);
  }
  setTimeout(nextStep,300);
}


function logout(){
  if(window.speechSynthesis) window.speechSynthesis.cancel();
  stopListening();
  currentUser=null; chatHistory=[]; attachedFiles=[]; conversations=[]; activeConvId=null;
  document.getElementById('app').classList.remove('visible');
  document.getElementById('login-email').value=''; document.getElementById('login-pass').value='';
  document.getElementById('login-error').style.display='none';
  ['step-1','step-2','step-3','step-4'].forEach(id=>{const el=document.getElementById(id);el.classList.remove('done');el.querySelector('.step-icon').textContent=id.replace('step-','');});
  document.getElementById('loading-bar').style.width='0%';
  showLogin();
}


function toggleSidebar(){ sidebarOpen=!sidebarOpen; document.getElementById('sidebar').classList.toggle('collapsed',!sidebarOpen); }

function renderUsersSwitcher(){
  const list=document.getElementById('users-list'); list.innerHTML='';
  registeredUsers.forEach(u=>{
    const init=u.name.split(' ').filter(w=>w.length>0).map(w=>w[0]).join('').slice(0,2).toUpperCase();
    const isActive=currentUser&&currentUser.email===u.email;
    const item=document.createElement('div'); item.className='user-switch-item'+(isActive?' active-user':'');
    item.innerHTML=`<div class="user-switch-avatar">${init}</div><div class="user-switch-name">${escapeHtml(u.name)}</div>${isActive?'<span class="user-switch-badge">Actif</span>':''}`;
    if(!isActive) item.onclick=()=>switchUser(u);
    list.appendChild(item);
  });
}

function switchUser(user){
  if(currentUser.email===user.email) return;
  if(window.speechSynthesis) window.speechSynthesis.cancel();
  const curU=registeredUsers.find(u=>u.email===currentUser.email);
  if(curU) curU.conversations=conversations;
  saveUsersToStorage();
  currentUser={name:user.name,email:user.email};
  userSettings.name=user.name;
  conversations=user.conversations||[];
  activeConvId=null; chatHistory=[]; attachedFiles=[];
  document.getElementById('user-name-s').textContent=currentUser.name;
  const init=currentUser.name.split(' ').filter(w=>w.length>0).map(w=>w[0]).join('').slice(0,2).toUpperCase();
  document.getElementById('user-avatar-s').textContent=init;
  renderUsersSwitcher(); renderHistoryList(); buildWelcome();
}

function openAddUser(){
  document.getElementById('new-user-name').value='';
  document.getElementById('new-user-email').value='';
  document.getElementById('new-user-pass').value='';
  document.getElementById('add-user-err').style.display='none';
  document.getElementById('add-user-modal').classList.add('active');
}
function closeAddUser(){ document.getElementById('add-user-modal').classList.remove('active'); }
function addNewUser(){
  const name=document.getElementById('new-user-name').value.trim();
  const email=document.getElementById('new-user-email').value.trim();
  const pass=document.getElementById('new-user-pass').value;
  const errEl=document.getElementById('add-user-err');
  errEl.style.display='none';
  if(!name||!email||!pass){errEl.textContent='⚠️ Tous les champs sont requis.';errEl.style.display='block';return;}
  if(pass.length<6){errEl.textContent='⚠️ Mot de passe trop court.';errEl.style.display='block';return;}
  if(registeredUsers.find(u=>u.email===email)){errEl.textContent='⚠️ Email déjà utilisé.';errEl.style.display='block';return;}
  registeredUsers.push({name,email,password:pass,conversations:[]});
  saveUsersToStorage();
  closeAddUser(); renderUsersSwitcher();
}


function syncMemoryBadge(){
  const on=userSettings.memory;
  const badge=document.getElementById('memory-badge-sidebar');
  badge.className='memory-badge '+(on?'on':'off');
  document.getElementById('memory-badge-icon').textContent=on?'💾':'🚫';
  document.getElementById('memory-badge-text').textContent=on?'Mémoire active':'Mémoire off';
}


function renderHistoryList(filter=''){
  const list=document.getElementById('history-list'); list.innerHTML='';
  const filtered=conversations.filter(c=>c.title.toLowerCase().includes((filter||'').toLowerCase()));
  if(!filtered.length){list.innerHTML='<div class="history-empty">'+(filter?'Aucun résultat':'Aucun historique pour l\'instant')+'</div>';return;}
  filtered.forEach(c=>{
    const item=document.createElement('div'); item.className='history-item';
    if(c.id===activeConvId) item.style.background='rgba(255,255,255,0.12)';
    item.innerHTML=`<div class="history-item-content" onclick="loadConversation('${c.id}')"><div class="h-title">${escapeHtml(c.title)}</div><div class="h-date">${c.dateLabel}</div></div><button class="h-delete" onclick="deleteConversation('${c.id}',event)">✕</button>`;
    list.appendChild(item);
  });
}
function filterHistory(val){ renderHistoryList(val); }

function addConversation(title,messages){
  if(!userSettings.memory) return null;
  const now=new Date(),today=new Date(),yesterday=new Date(today-86400000);
  let dateLabel=now.toLocaleDateString('fr-FR');
  if(now.toDateString()===today.toDateString()) dateLabel='Aujourd\'hui';
  else if(now.toDateString()===yesterday.toDateString()) dateLabel='Hier';
  const id='conv-'+Date.now();
  conversations.unshift({id,title,dateLabel,messages:[...messages]});
  activeConvId=id;
  renderHistoryList(document.getElementById('search-input').value);
  const curU=registeredUsers.find(u=>u.email===currentUser.email);
  if(curU) curU.conversations=conversations;
  saveUsersToStorage();
  return id;
}
function updateConversation(id,messages){
  const c=conversations.find(c=>c.id===id); if(c) c.messages=[...messages];
  const curU=registeredUsers.find(u=>u.email===currentUser.email); if(curU) curU.conversations=conversations;
  saveUsersToStorage();
}
function loadConversation(id){
  const c=conversations.find(c=>c.id===id); if(!c) return;
  activeConvId=id; chatHistory=[...c.messages];
  const msgs=document.getElementById('messages'); msgs.innerHTML='';
  c.messages.forEach(m=>{
    const role=m.role==='user'?'user':'ai';
    const text=typeof m.content==='string'?m.content:(Array.isArray(m.content)?m.content.filter(b=>b.type==='text').map(b=>b.text).join('\n'):'');
    if(text) appendBubble(role,text);
  });
  renderHistoryList(document.getElementById('search-input').value);
}
function deleteConversation(id,e){
  e.stopPropagation(); conversations=conversations.filter(c=>c.id!==id);
  if(activeConvId===id){activeConvId=null;chatHistory=[];buildWelcome();}
  const curU=registeredUsers.find(u=>u.email===currentUser.email); if(curU) curU.conversations=conversations;
  saveUsersToStorage();
  renderHistoryList(document.getElementById('search-input').value);
}
function clearAllHistory(){
  conversations=[]; activeConvId=null; chatHistory=[]; attachedFiles=[];
  const curU=registeredUsers.find(u=>u.email===currentUser.email); if(curU) curU.conversations=[];
  saveUsersToStorage();
  renderHistoryList(); buildWelcome(); closeSettings();
}


function openSettings(){
  document.getElementById('setting-name').value=userSettings.name||currentUser?.name||'';
  document.getElementById('setting-verbose').checked=userSettings.verbose;
  document.getElementById('setting-sources').checked=userSettings.sources;
  document.getElementById('setting-memory').checked=userSettings.memory;
  document.getElementById('setting-retention').value=userSettings.retention||'forever';
  document.getElementById('setting-autoread').checked=userSettings.autoread;
  document.getElementById('setting-voice-gender').value=userSettings.voiceGender||'female';
  document.getElementById('setting-voice-rate').value=String(userSettings.voiceRate||1.0);
  document.getElementById('setting-voice-pitch').value=String(userSettings.voicePitch||1.0);
  document.getElementById('setting-voice-input').checked=userSettings.voiceInput!==false;
  document.getElementById('settings-modal').classList.add('active');
  setTimeout(updateVoicePreview, 100);
}
function closeSettings(){ document.getElementById('settings-modal').classList.remove('active'); }
function saveSettings(){
  const newName=document.getElementById('setting-name').value.trim();
  userSettings.name=newName||currentUser?.name||'';
  userSettings.verbose=document.getElementById('setting-verbose').checked;
  userSettings.sources=document.getElementById('setting-sources').checked;
  userSettings.memory=document.getElementById('setting-memory').checked;
  userSettings.retention=document.getElementById('setting-retention').value;
  userSettings.autoread=document.getElementById('setting-autoread').checked;
  userSettings.voiceGender=document.getElementById('setting-voice-gender').value;
  userSettings.voiceRate=parseFloat(document.getElementById('setting-voice-rate').value);
  userSettings.voicePitch=parseFloat(document.getElementById('setting-voice-pitch').value);
  userSettings.voiceInput=document.getElementById('setting-voice-input').checked;
  if(newName){
    currentUser.name=newName;
    document.getElementById('user-name-s').textContent=newName;
    const init=newName.split(' ').filter(w=>w.length>0).map(w=>w[0]).join('').slice(0,2).toUpperCase();
    document.getElementById('user-avatar-s').textContent=init;
    const curU=registeredUsers.find(u=>u.email===currentUser.email);
    if(curU) curU.name=newName;
    saveUsersToStorage();
  }

  document.getElementById('mic-btn').style.display=userSettings.voiceInput?'flex':'none';
  syncMemoryBadge();
  closeSettings();
}


function buildWelcome(){
  if(window.speechSynthesis) window.speechSynthesis.cancel();
  const msgs=document.getElementById('messages'); msgs.innerHTML='';
  const w=document.createElement('div'); w.id='welcome';
  w.innerHTML=`
    <div class="welcome-avatar">M</div>
    <h2>Bonjour ${currentUser?currentUser.name:'Docteur'} 👋</h2>
    <p>Que souhaitez-vous faire aujourd'hui ?</p>
    <div class="suggestions">
      <button class="suggestion-btn" onclick="sendSuggestion('Résumer la consultation d\\'un patient')">📋 Résumer la consultation</button>
      <button class="suggestion-btn" onclick="sendSuggestion('Analyser un document patient')">🔍 Analyser un document</button>
      <button class="suggestion-btn" onclick="sendSuggestion('Interpréter des résultats d\\'analyses biologiques')">🧪 Interpréter des résultats</button>
    </div>`;
  msgs.appendChild(w);
}

function newChat(){
  if(window.speechSynthesis) window.speechSynthesis.cancel();
  stopListening();
  chatHistory=[]; attachedFiles=[]; activeConvId=null;
  renderFilePreviews(); buildWelcome();
  document.getElementById('chat-input').value=''; updateSendBtn();
  renderHistoryList(document.getElementById('search-input').value);
}


function handleFiles(files){
  files.forEach(file=>{
    if(attachedFiles.length>=5){alert('Maximum 5 fichiers.');return;}
    const reader=new FileReader();
    reader.onload=ev=>{attachedFiles.push({name:file.name,type:file.type,base64:ev.target.result.split(',')[1]});renderFilePreviews();updateSendBtn();};
    reader.readAsDataURL(file);
  });
}
function renderFilePreviews(){
  const bar=document.getElementById('file-preview-bar'); bar.innerHTML='';
  if(!attachedFiles.length){bar.classList.remove('visible');return;}
  bar.classList.add('visible');
  attachedFiles.forEach((f,i)=>{
    const icon=f.type.startsWith('image')?'🖼️':f.type==='application/pdf'?'📄':'📝';
    const chip=document.createElement('div'); chip.className='file-chip';
    chip.innerHTML=`<span>${icon}</span><span class="chip-name">${escapeHtml(f.name.length>22?f.name.slice(0,20)+'…':f.name)}</span><button class="chip-remove" onclick="removeFile(${i})">✕</button>`;
    bar.appendChild(chip);
  });
}
function removeFile(i){attachedFiles.splice(i,1);renderFilePreviews();updateSendBtn();}
function updateSendBtn(){const ta=document.getElementById('chat-input');document.getElementById('send-btn').disabled=!(ta.value.trim()||attachedFiles.length)||isLoading;}


function sendSuggestion(text){document.getElementById('chat-input').value=text;sendMessage();}

async function sendMessage(){
  const ta = document.getElementById('chat-input');
  const text = ta.value.trim();
  if((!text && !attachedFiles.length) || isLoading) return;

  stopListening();
  if(window.speechSynthesis) window.speechSynthesis.cancel();

  const welcome = document.getElementById('welcome');
  if(welcome) welcome.remove();

  const displayText = [attachedFiles.map(f=>`📎 ${f.name}`).join('\n'), text].filter(Boolean).join('\n');
  appendBubble('user', displayText);

  const filesSnap = [...attachedFiles];
  attachedFiles = [];
  renderFilePreviews();
  ta.value = '';
  ta.style.height = 'auto';
  updateSendBtn();

  const typingId = 'typing-' + Date.now();
  appendTyping(typingId);
  isLoading = true;
  updateSendBtn();

  try {
    const res = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question:   text,
        user_id:    currentUser?.email || 'anonyme',
        historique: []
      })
    });

    const data = await res.json();

    let reply = data.reponse || "Desole, je n'ai pas pu generer une reponse.";

    if(data.sources && data.sources.length > 0 && userSettings.sources) {
      const sourcesText = data.sources
        .map(s => `📂 ${s.fichier} · ${s.categorie}`)
        .join('\n');
      reply += `\n\n${sourcesText}`;
    }

    if(data.fallback) {
      reply = `⚠️ ${data.reponse}`;
    }

    chatHistory.push({ role: 'user', content: text });
    chatHistory.push({ role: 'assistant', content: reply });

    removeTyping(typingId);
    appendBubble('ai', reply);

    if(userSettings.autoread) {
      setTimeout(() => {
        const lastBtn = document.querySelector('.tts-btn:last-of-type');
        speakText(reply, lastBtn || null);
      }, 300);
    }

    if(!activeConvId) {
      const title = (text || filesSnap[0]?.name || 'Question').slice(0, 48);
      activeConvId = addConversation(title, chatHistory) || null;
    } else {
      updateConversation(activeConvId, chatHistory);
    }

  } catch(err) {
    removeTyping(typingId);
    appendBubble('ai', '⚠️ Impossible de contacter le backend Medic IA. Verifiez que le serveur tourne sur http://localhost:8000');
    console.error('Erreur backend:', err);
  }

  isLoading = false;
  updateSendBtn();
}


function appendBubble(role,text){
  const msgs=document.getElementById('messages');
  const row=document.createElement('div'); row.className=`msg-row ${role}`;
  const initials=role==='ai'?'M':(currentUser?.name?.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase()||'DR');
  const bubbleContent=escapeHtml(text);

  const ttsBtnHtml = role==='ai'
    ? `<div style="margin-top:6px;"><button class="tts-btn" onclick="speakBubble(this, '${text.replace(/'/g,"\\'").replace(/\n/g,' ')}')">🔊 Écouter</button></div>`
    : '';
  row.innerHTML=`<div class="msg-avatar ${role==='ai'?'ai':'user-av'}">${initials}</div><div class="msg-bubble">${bubbleContent}${ttsBtnHtml}</div>`;
  msgs.appendChild(row); msgs.scrollTop=msgs.scrollHeight;
}

function speakBubble(btn, text) {
  speakText(text, btn);
}

function appendTyping(id){
  const msgs=document.getElementById('messages');
  const row=document.createElement('div'); row.className='msg-row ai'; row.id=id;
  row.innerHTML=`<div class="msg-avatar ai">M</div><div class="typing-bubble"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
  msgs.appendChild(row); msgs.scrollTop=msgs.scrollHeight;
}
function removeTyping(id){const el=document.getElementById(id);if(el)el.remove();}
function escapeHtml(str){return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');}


document.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('login-email').addEventListener('keydown',e=>{if(e.key==='Enter')handleLogin();});
  document.getElementById('login-pass').addEventListener('keydown',e=>{if(e.key==='Enter')handleLogin();});
  document.getElementById('reg-pass2').addEventListener('keydown',e=>{if(e.key==='Enter')handleRegister();});
  const ta=document.getElementById('chat-input');
  ta.addEventListener('input',()=>{ta.style.height='auto';ta.style.height=Math.min(ta.scrollHeight,120)+'px';updateSendBtn();});
  ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();if(!isLoading&&(ta.value.trim()||attachedFiles.length))sendMessage();}});
  document.getElementById('file-input').addEventListener('change',e=>{handleFiles(Array.from(e.target.files));e.target.value='';});
  const main=document.getElementById('main'),overlay=document.getElementById('drop-overlay');
  main.addEventListener('dragover',e=>{e.preventDefault();overlay.classList.add('active');});
  main.addEventListener('dragleave',e=>{if(!main.contains(e.relatedTarget))overlay.classList.remove('active');});
  main.addEventListener('drop',e=>{e.preventDefault();overlay.classList.remove('active');handleFiles(Array.from(e.dataTransfer.files));});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeSettings();closeAddUser();if(window.speechSynthesis)window.speechSynthesis.cancel();stopListening();}});
  document.getElementById('settings-modal').addEventListener('click',e=>{if(e.target===document.getElementById('settings-modal'))closeSettings();});
  document.getElementById('add-user-modal').addEventListener('click',e=>{if(e.target===document.getElementById('add-user-modal'))closeAddUser();});
});