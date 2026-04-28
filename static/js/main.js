// main.js — Operação Farda PDF Generator

const TOTAL_QUESTOES = 20;
let modoAtual = 'manual';
let brasaoSelecionado = '';
let destinoAtual = 'pdf';
let parseTimer = null;
let questoesGeradasIA = [];

document.addEventListener('DOMContentLoaded', () => {
  inicializarQuestoes();
  inicializarModoTabs();
  inicializarUpload();
  inicializarBrasoes();
  inicializarTextoCorrido();
  inicializarPreview();
  document.getElementById('btn-gerar').addEventListener('click', gerarPDF);
  const savedKey = localStorage.getItem('of_api_key');
  if (savedKey) document.getElementById('api-key').value = savedKey;
  const savedProvedor = localStorage.getItem('of_ia_provedor');
  if (savedProvedor) {
    document.getElementById('ia-provedor').value = savedProvedor;
    atualizarProvedorIA();
  }
  carregarDashboard();
  atualizarContador();
});

// ─── SEÇÕES ───────────────────────────────────────────────────
function mostrarSecao(id) {
  document.getElementById('secao-gerador').style.display = id === 'gerador' ? '' : 'none';
  document.getElementById('secao-agenda').style.display  = id === 'agenda'  ? '' : 'none';
  document.querySelectorAll('.header-tab').forEach(t => {
    t.classList.toggle('ativo', t.getAttribute('onclick').includes(id));
  });
}

// ─── PERFIS ───────────────────────────────────────────────────
function carregarPerfil(id) {
  const el = document.querySelector(`.perfil-item[data-id="${id}"]`);
  if (!el) return;
  document.getElementById('concurso').value = el.dataset.concurso || '';
  const banca = el.dataset.banca || '';
  const bancaSelect = document.getElementById('banca');
  for (let opt of bancaSelect.options) { if (opt.value === banca) { bancaSelect.value = banca; break; } }
  const brasao = el.dataset.brasao || '';
  if (brasao) {
    document.querySelectorAll('.brasao-item').forEach(b => {
      b.classList.toggle('ativo', b.dataset.arquivo === brasao);
    });
    brasaoSelecionado = brasao;
  }
  document.querySelectorAll('.perfil-item').forEach(p => p.classList.remove('ativo'));
  el.classList.add('ativo');
  atualizarPreview();
  showToast(`Perfil "${el.querySelector('.perfil-nome').textContent}" carregado!`, 'sucesso');
}

function toggleNovoPerfil() {
  document.getElementById('form-novo-perfil').classList.toggle('visivel');
}

// ─── EDITAR PERFIL ────────────────────────────────────────────
function editarPerfil(id) {
  const el = document.querySelector(`.perfil-item[data-id="${id}"]`);
  if (!el) return;
  const nome    = el.querySelector('.perfil-nome').textContent;
  const concurso = el.dataset.concurso || '';
  const banca   = el.dataset.banca || '';
  const brasao  = el.dataset.brasao || '';

  // Preencher form de edição inline
  document.getElementById('perfil-nome').value     = nome;
  document.getElementById('perfil-concurso').value = concurso;
  const bancaEl = document.getElementById('perfil-banca');
  for (let opt of bancaEl.options) { if (opt.value === banca) { bancaEl.value = banca; break; } }
  const brasaoEl = document.getElementById('perfil-brasao');
  for (let opt of brasaoEl.options) { if (opt.value === brasao) { brasaoEl.value = brasao; break; } }

  // Mudar botão de salvar para modo edição
  const form = document.getElementById('form-novo-perfil');
  form.dataset.editandoId = id;
  form.classList.add('visivel');
  const btn = form.querySelector('button');
  btn.querySelector('.btn-text').textContent = '💾 Atualizar Perfil';
}

async function salvarNovoPerfil() {
  const nome = document.getElementById('perfil-nome').value.trim();
  if (!nome) return showToast('Informe o nome do perfil', 'erro');
  const brasaoSelect = document.getElementById('perfil-brasao').value;
  const brasaoFinal = brasaoSelect || brasaoSelecionado;
  const dados = {
    nome,
    concurso: document.getElementById('perfil-concurso').value.trim() || document.getElementById('concurso').value.trim(),
    banca: document.getElementById('perfil-banca').value || document.getElementById('banca').value,
    brasao: brasaoFinal,
    icone: '🎯', cor: '#39FF14',
  };

  const form = document.getElementById('form-novo-perfil');
  const editandoId = form.dataset.editandoId;

  let res;
  if (editandoId) {
    res = await fetch(`/perfis/${editandoId}`, { method: 'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify(dados) });
  } else {
    res = await fetch('/perfis', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(dados) });
  }
  const data = await res.json();
  if (data.erro) return showToast(data.erro, 'erro');
  atualizarGridPerfis(data.perfis);
  form.classList.remove('visivel');
  form.dataset.editandoId = '';
  document.getElementById('perfil-nome').value = '';
  document.getElementById('perfil-concurso').value = '';
  form.querySelector('button .btn-text').textContent = 'Salvar Perfil';
  showToast(editandoId ? 'Perfil atualizado!' : 'Perfil salvo!', 'sucesso');
}

async function deletarPerfil(id) {
  const res = await fetch(`/perfis/${id}`, { method: 'DELETE' });
  const data = await res.json();
  atualizarGridPerfis(data.perfis);
  showToast('Perfil removido', 'sucesso');
}

function atualizarGridPerfis(perfis) {
  const grid = document.getElementById('perfis-grid');
  grid.innerHTML = perfis.map(p => `
    <div class="perfil-item" onclick="carregarPerfil('${p.id}')"
         data-id="${p.id}" data-concurso="${p.concurso || ''}"
         data-banca="${p.banca || ''}" data-brasao="${p.brasao || ''}"
         style="border-color:${p.cor}20;">
      <span class="perfil-icone">${p.icone}</span>
      <span class="perfil-nome">${p.nome}</span>
      <div class="perfil-btns">
        <button class="perfil-edit" onclick="event.stopPropagation();editarPerfil('${p.id}')" title="Editar">✏️</button>
        <button class="perfil-del" onclick="event.stopPropagation();deletarPerfil('${p.id}')" title="Remover">✕</button>
      </div>
    </div>
  `).join('');
}

// ─── CONTADOR DE QUESTÕES ─────────────────────────────────────
function atualizarContador() {
  let total = 0;
  for (let i = 1; i <= TOTAL_QUESTOES; i++) {
    if (document.getElementById(`enunciado-${i}`)?.value.trim()) total++;
  }
  const el = document.getElementById('contador-questoes');
  if (el) {
    el.textContent = `${total}/${TOTAL_QUESTOES} questões preenchidas`;
    el.style.color = total === 0 ? '#666' : total >= 10 ? '#39FF14' : '#f0a500';
  }
}

// ─── DASHBOARD ────────────────────────────────────────────────
async function carregarDashboard() {
  try {
    const res = await fetch('/dashboard');
    const d = await res.json();
    const el = document.getElementById('dashboard-stats');
    if (!el) return;

    const destNomes = { grupo: '📱 WhatsApp', pdf: '📄 PDF Público', plataforma: '🏆 Plataforma' };
    const destHtml = Object.entries(d.por_destino || {})
      .map(([k, v]) => `<span class="dash-badge">${destNomes[k]||k}: <strong>${v}</strong></span>`).join('');

    const discHtml = (d.por_disciplina || []).slice(0, 6)
      .map(([disc, qtd]) => `<div class="dash-disc-bar">
        <span>${disc}</span><strong>${qtd}</strong>
      </div>`).join('');

    el.innerHTML = `
      <div class="dash-numeros">
        <div class="dash-num"><span>${d.total_pdfs || 0}</span><small>PDFs gerados</small></div>
        <div class="dash-num"><span>${d.total_questoes || 0}</span><small>Questões criadas</small></div>
      </div>
      ${destHtml ? `<div class="dash-destinos">${destHtml}</div>` : ''}
      ${discHtml ? `<div class="dash-disciplinas"><p>Top disciplinas:</p>${discHtml}</div>` : ''}
      ${!d.total_pdfs ? '<p style="color:#666;font-size:0.85rem;text-align:center;">Nenhum PDF gerado ainda.</p>' : ''}
    `;
  } catch(e) { /* silencioso */ }
}

// ─── DESTINO ──────────────────────────────────────────────────
function selecionarDestino(el, destino) {
  document.querySelectorAll('.destino-item').forEach(d => d.classList.remove('ativo'));
  el.classList.add('ativo');
  destinoAtual = destino;
  atualizarPreview();
}

// ─── PREVIEW ──────────────────────────────────────────────────
function inicializarPreview() {
  ['concurso','banca'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', atualizarPreview);
    if (el) el.addEventListener('change', atualizarPreview);
  });
  atualizarPreview();
}

function atualizarPreview() {
  const concurso  = document.getElementById('concurso')?.value || '—';
  const banca     = document.getElementById('banca')?.value || '—';
  const destinos  = { grupo:'📱 Grupo WhatsApp', pdf:'📄 PDF Público', plataforma:'🏆 Plataforma Premium' };

  // Coletar disciplinas
  const discs = new Set();
  if (modoAtual === 'manual') {
    for (let i = 1; i <= TOTAL_QUESTOES; i++) {
      const d = document.getElementById(`disc-${i}`)?.value;
      if (d) discs.add(d);
    }
  } else if (modoAtual === 'texto') {
    const texto = document.getElementById('texto-corrido')?.value || '';
    const matches = texto.matchAll(/\[DISCIPLINA\s*:\s*([^\]]+)\]/gi);
    for (const m of matches) discs.add(m[1].trim());
  }

  // Contar questões
  let totalQ = 0;
  if (modoAtual === 'manual') {
    for (let i = 1; i <= TOTAL_QUESTOES; i++) {
      if (document.getElementById(`enunciado-${i}`)?.value.trim()) totalQ++;
    }
  } else if (modoAtual === 'texto') {
    const matches = document.getElementById('texto-corrido')?.value.matchAll(/^\s*\d+\s*[.)]\s+/gm);
    if (matches) totalQ = [...matches].length;
  }

  document.getElementById('pv-concurso').textContent    = concurso;
  document.getElementById('pv-banca').textContent       = banca;
  document.getElementById('pv-disciplinas').textContent = discs.size ? [...discs].join(', ') : '—';
  document.getElementById('pv-destino').textContent     = destinos[destinoAtual] || '—';
  document.getElementById('pv-questoes').textContent    = totalQ ? `${totalQ} questões` : '—';

  const pvBrasao = document.getElementById('pv-brasao');
  if (brasaoSelecionado) {
    pvBrasao.src = `/static/logos/brasoes/${brasaoSelecionado}?t=${Date.now()}`;
    pvBrasao.style.display = 'block';
  } else {
    pvBrasao.style.display = 'none';
  }
}

// ─── AGENDAMENTO ──────────────────────────────────────────────
function toggleAgendar() {
  const form = document.getElementById('form-agendar');
  form.classList.toggle('visivel', document.getElementById('chk-agendar').checked);
}

async function deletarAgenda(id) {
  await fetch(`/agenda/${id}`, { method: 'DELETE' });
  const el = document.getElementById(`ag-${id}`);
  if (el) el.remove();
  showToast('Removido da agenda', 'sucesso');
}

// ─── QUESTÕES MANUAIS ─────────────────────────────────────────
function inicializarQuestoes() {
  const grid = document.getElementById('questoes-grid');
  grid.innerHTML = '';
  for (let i = 1; i <= TOTAL_QUESTOES; i++) grid.appendChild(criarCardQuestao(i));
  document.querySelector('.questao-card').classList.add('aberta');
  document.querySelector('.questao-card .questao-body').style.display = 'flex';
}

function criarCardQuestao(num) {
  const card = document.createElement('div');
  card.className = 'questao-card';
  card.dataset.num = num;
  const discOptions = window.DISCIPLINAS.map(d => `<option value="${d}">${d}</option>`).join('');
  card.innerHTML = `
    <div class="questao-header" onclick="toggleQuestao(${num})">
      <span class="questao-num">${num}</span>
      <span class="questao-disc-badge" id="disc-badge-${num}"></span>
      <span class="questao-preview" id="preview-${num}">Clique para preencher...</span>
      <span class="questao-toggle">▼</span>
    </div>
    <div class="questao-body" id="body-${num}">
      <div>
        <label>Disciplina desta questão</label>
        <select id="disc-${num}" onchange="atualizarDiscBadge(${num}); atualizarPreview()">
          <option value="">— Mesma do bloco anterior —</option>${discOptions}
        </select>
      </div>
      <div>
        <label>Enunciado da questão</label>
        <textarea id="enunciado-${num}" rows="3" placeholder="Digite o enunciado aqui..."
          oninput="atualizarPreview(${num}); atualizarContador()"></textarea>
      </div>
      <div class="alt-grid">
        ${['A','B','C','D','E'].map(l => `
          <span class="alt-label">${l}</span>
          <input type="text" id="alt-${num}-${l}" placeholder="Alternativa ${l}...">
        `).join('')}
      </div>
      <button class="apoio-toggle" onclick="toggleApoio(${num})">+ Adicionar texto de apoio</button>
      <div class="apoio-campos" id="apoio-campos-${num}">
        <div>
          <label>Instrução</label>
          <input type="text" id="label-apoio-${num}" placeholder="Atenção: Para responder às questões...">
        </div>
        <div>
          <label>Texto de apoio</label>
          <textarea id="texto-apoio-${num}" rows="4" placeholder="Cole o texto base aqui..."></textarea>
        </div>
      </div>
    </div>`;
  return card;
}

function atualizarDiscBadge(num) {
  const disc = document.getElementById(`disc-${num}`)?.value;
  const badge = document.getElementById(`disc-badge-${num}`);
  if (badge) { badge.textContent = disc || ''; badge.style.display = disc ? 'inline-block' : 'none'; }
}

function toggleQuestao(num) {
  const card = document.querySelector(`.questao-card[data-num="${num}"]`);
  const body = document.getElementById(`body-${num}`);
  const isAberta = card.classList.contains('aberta');
  card.classList.toggle('aberta', !isAberta);
  body.style.display = isAberta ? 'none' : 'flex';
}

function atualizarPreview(num) {
  if (num) {
    const enunciado = document.getElementById(`enunciado-${num}`)?.value;
    const prev = document.getElementById(`preview-${num}`);
    if (prev) {
      prev.textContent = enunciado ? (enunciado.length > 60 ? enunciado.substring(0,60)+'...' : enunciado) : 'Clique para preencher...';
      prev.style.color = enunciado ? '#ccc' : '#888';
    }
  }
  // Sempre atualizar o card de preview
  setTimeout(() => {
    const concurso = document.getElementById('concurso')?.value || '—';
    const banca = document.getElementById('banca')?.value || '—';
    const destinos = { grupo:'📱 Grupo WhatsApp', pdf:'📄 PDF Público', plataforma:'🏆 Plataforma Premium' };
    const discs = new Set();
    for (let i = 1; i <= TOTAL_QUESTOES; i++) {
      const d = document.getElementById(`disc-${i}`)?.value;
      if (d) discs.add(d);
    }
    let totalQ = 0;
    for (let i = 1; i <= TOTAL_QUESTOES; i++) {
      if (document.getElementById(`enunciado-${i}`)?.value.trim()) totalQ++;
    }
    document.getElementById('pv-concurso').textContent    = concurso;
    document.getElementById('pv-banca').textContent       = banca;
    document.getElementById('pv-disciplinas').textContent = discs.size ? [...discs].join(', ') : '—';
    document.getElementById('pv-destino').textContent     = destinos[destinoAtual] || '—';
    document.getElementById('pv-questoes').textContent    = totalQ ? `${totalQ} questões` : '—';
  }, 50);
}

function toggleApoio(num) {
  const campos = document.getElementById(`apoio-campos-${num}`);
  campos.classList.toggle('visivel');
  const btn = campos.previousElementSibling;
  btn.textContent = campos.classList.contains('visivel') ? '− Remover texto de apoio' : '+ Adicionar texto de apoio';
}

// ─── MODO TABS ────────────────────────────────────────────────
function inicializarModoTabs() {
  document.querySelectorAll('.modo-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      modoAtual = tab.dataset.modo;
      document.querySelectorAll('.modo-tab').forEach(t => t.classList.remove('ativo'));
      tab.classList.add('ativo');
      document.getElementById('modo-manual').classList.toggle('oculto', modoAtual !== 'manual');
      document.getElementById('modo-texto').classList.toggle('visivel', modoAtual === 'texto');
      document.getElementById('modo-ia').classList.toggle('visivel', modoAtual === 'ia');
      atualizarPreview();
    });
  });
}

// ─── TEXTO CORRIDO ────────────────────────────────────────────
function inicializarTextoCorrido() {
  const ta = document.getElementById('texto-corrido');
  if (ta) ta.addEventListener('input', () => {
    clearTimeout(parseTimer);
    parseTimer = setTimeout(parsearPrevia, 600);
    atualizarPreview();
  });
}

async function parsearPrevia() {
  const texto = document.getElementById('texto-corrido')?.value;
  const preview = document.getElementById('preview-parse');
  if (!texto?.trim()) { preview?.classList.remove('visivel'); return; }
  try {
    const res = await fetch('/parsear', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({texto}) });
    const data = await res.json();
    if (!preview) return;
    preview.innerHTML = data.total === 0
      ? `<h4>⚠ Nenhuma questão reconhecida</h4><p class="preview-item">Verifique o formato.</p>`
      : `<h4>✓ ${data.total} questão(ões) reconhecida(s)</h4>${data.questoes.map(q=>`
          <div class="preview-item">
            <span class="preview-ok">Q${q.num} · ${q.total_alts} alts${q.disciplina?' · '+q.disciplina:''}</span>
            ${q.enunciado}
          </div>`).join('')}`;
    preview.classList.add('visivel');
    // Atualizar preview config
    const qcount = document.getElementById('pv-questoes');
    if (qcount) qcount.textContent = `${data.total} questões`;
  } catch(e) { console.error(e); }
}

// ─── BRASÕES ──────────────────────────────────────────────────
function inicializarBrasoes() {
  document.querySelectorAll('.brasao-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.brasao-item').forEach(i => i.classList.remove('ativo'));
      item.classList.add('ativo');
      brasaoSelecionado = item.dataset.arquivo;
      atualizarPreview();
    });
  });
  const primeiro = document.querySelector('.brasao-item');
  if (primeiro) { primeiro.classList.add('ativo'); brasaoSelecionado = primeiro.dataset.arquivo; }
}

function selecionarBrasao(el, arquivo) {
  document.querySelectorAll('.brasao-item').forEach(i => i.classList.remove('ativo'));
  el.classList.add('ativo');
  brasaoSelecionado = arquivo;
  atualizarPreview();
}

function atualizarGridBrasoes(brasoes) {
  const grid = document.getElementById('brasao-grid');
  grid.innerHTML = brasoes.map(b => `
    <div class="brasao-item ${b.arquivo===brasaoSelecionado?'ativo':''}" data-arquivo="${b.arquivo}"
         onclick="selecionarBrasao(this,'${b.arquivo}')">
      <img src="/static/logos/brasoes/${b.arquivo}?t=${Date.now()}" alt="${b.nome}">
      <span>${b.nome}</span>
    </div>`).join('');
}

// ─── UPLOAD ───────────────────────────────────────────────────
function inicializarUpload() {
  const zone = document.getElementById('upload-zone');
  const input = document.getElementById('upload-input');
  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('drag-over'); if(e.dataTransfer.files.length){input.files=e.dataTransfer.files;mostrarNomePM();} });
  input.addEventListener('change', () => { if(input.files.length) mostrarNomePM(); });
}

function mostrarNomePM() {
  const input = document.getElementById('upload-input');
  if (input.files[0]) {
    document.getElementById('upload-zone').querySelector('p').innerHTML = `<strong>${input.files[0].name}</strong>`;
    document.getElementById('upload-nome-pm').classList.add('visivel');
  }
}

async function enviarBrasao() {
  const input = document.getElementById('upload-input');
  const nomePM = document.getElementById('nome-pm-input').value.trim();
  if (!input.files[0]) return showToast('Selecione um arquivo', 'erro');
  if (!nomePM) return showToast('Informe o nome da PM', 'erro');
  const formData = new FormData();
  formData.append('brasao', input.files[0]);
  formData.append('nome_pm', nomePM);
  const res = await fetch('/upload-brasao', { method:'POST', body:formData });
  const data = await res.json();
  if (data.erro) return showToast(data.erro, 'erro');
  brasaoSelecionado = data.arquivo;
  atualizarGridBrasoes(data.brasoes);
  showToast(`Brasão "${data.nome}" adicionado!`, 'sucesso');
  input.value = '';
  document.getElementById('nome-pm-input').value = '';
  document.getElementById('upload-nome-pm').classList.remove('visivel');
  document.getElementById('upload-zone').querySelector('p').innerHTML = 'Arraste ou <strong>clique</strong> para enviar';
}

// ─── GERAR PDF ────────────────────────────────────────────────
let _gerandoPDF = false; // guarda contra duplo clique
async function gerarPDF() {
  if (_gerandoPDF) return;
  _gerandoPDF = true;

  const btn = document.getElementById('btn-gerar');
  const concurso = document.getElementById('concurso').value.trim();
  const banca    = document.getElementById('banca').value;
  const agendar  = document.getElementById('chk-agendar').checked;
  const dataAg   = document.getElementById('data-agenda').value;
  const nomeAg   = document.getElementById('nome-agenda').value.trim();

  if (!concurso) { showToast('Informe o nome do concurso', 'erro'); _gerandoPDF = false; return; }
  if (agendar && !dataAg) { showToast('Selecione uma data para o agendamento', 'erro'); _gerandoPDF = false; return; }

  let payload = { concurso, banca, brasao: brasaoSelecionado, modo: modoAtual,
                  destino: destinoAtual, agendar, data_agenda: dataAg, nome_agenda: nomeAg,
                  embaralhar: document.getElementById('chk-embaralhar')?.checked || false };

  if (modoAtual === 'texto') {
    const texto = document.getElementById('texto-corrido').value.trim();
    if (!texto) { showToast('Cole as questões no campo de texto', 'erro'); _gerandoPDF = false; return; }
    payload.texto_corrido = texto;
  } else {
    const questoes = [];
    for (let i = 1; i <= TOTAL_QUESTOES; i++) {
      const enunciado = document.getElementById(`enunciado-${i}`)?.value.trim();
      if (!enunciado) continue;
      questoes.push({
        num: i, enunciado,
        disciplina: document.getElementById(`disc-${i}`)?.value.trim() || null,
        alt_A: document.getElementById(`alt-${i}-A`)?.value.trim() || '',
        alt_B: document.getElementById(`alt-${i}-B`)?.value.trim() || '',
        alt_C: document.getElementById(`alt-${i}-C`)?.value.trim() || '',
        alt_D: document.getElementById(`alt-${i}-D`)?.value.trim() || '',
        alt_E: document.getElementById(`alt-${i}-E`)?.value.trim() || '',
        texto_apoio: document.getElementById(`texto-apoio-${i}`)?.value.trim() || null,
        label_apoio: document.getElementById(`label-apoio-${i}`)?.value.trim() || null,
      });
    }
    if (!questoes.length) { showToast('Preencha pelo menos uma questão', 'erro'); _gerandoPDF = false; return; }
    payload.questoes = questoes;
  }

  btn.classList.add('loading'); btn.disabled = true;

  try {
    const res = await fetch('/gerar', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) });

    if (agendar) {
      // Para agendamento, servidor sempre retorna JSON
      let data;
      try { data = await res.json(); } catch(e) { throw new Error('Resposta inválida do servidor'); }
      if (!res.ok || data.erro) throw new Error(data.erro || 'Erro ao agendar PDF');
      showToast(`PDF salvo na agenda: "${data.nome}"`, 'sucesso');
      // Recarregar agenda
      const agRes = await fetch('/agenda');
      const agData = await agRes.json();
      atualizarAgenda(agData);
      setTimeout(() => mostrarSecao('agenda'), 1500);
      return;
    }

    if (!res.ok) {
      let err;
      try { err = await res.json(); } catch(e) { err = { erro: 'Erro ao gerar PDF' }; }
      throw new Error(err.erro || 'Erro ao gerar PDF');
    }

    const blob = await res.blob();
    if (blob.size < 100) { throw new Error('PDF gerado está vazio. Verifique as questões.'); }
    const url  = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `OF_${concurso.replace(/\s+/g,'_')}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    showToast('PDF gerado com sucesso!', 'sucesso');
  } catch(e) {
    showToast(e.message || 'Erro inesperado', 'erro');
  } finally {
    btn.classList.remove('loading'); btn.disabled = false;
    _gerandoPDF = false;
  }
}

// ─── AGENDA UPDATE ────────────────────────────────────────────
function atualizarAgenda(agData) {
  // Recarrega a página da agenda com novos dados sem reload completo
  const secao = document.getElementById('secao-agenda');
  if (!secao) return;
  const pendEl = secao.querySelector('.agenda-pendentes');
  const baixEl = secao.querySelector('.agenda-baixados');
  if (pendEl) pendEl.innerHTML = (agData.pendentes || []).map(renderAgItem).join('') || '<p style="color:#666;font-size:0.85rem;">Nenhum agendamento pendente.</p>';
  if (baixEl) baixEl.innerHTML = (agData.baixados || []).map(renderAgItem).join('') || '<p style="color:#666;font-size:0.85rem;">Nenhum PDF baixado ainda.</p>';
}
function renderAgItem(item) {
  return `<div class="agenda-item" id="ag-${item.id}">
    <div class="agenda-info">
      <strong>${item.nome}</strong>
      <span>${item.concurso} · ${item.disciplina}</span>
      <span>${item.data} · ${item.destino}</span>
    </div>
    <div class="agenda-acoes">
      <a href="/agenda/${item.id}/download" class="btn-download-ag" onclick="marcarBaixadoUI('${item.id}')">⬇ Baixar</a>
      <button onclick="deletarAgenda('${item.id}')" class="btn-del-agenda">✕</button>
    </div>
  </div>`;
}
function marcarBaixadoUI(id) {
  fetch(`/agenda/${id}/baixado`, { method: 'POST' });
}

// ─── IA MULTI-PROVEDOR ────────────────────────────────────────
function atualizarProvedorIA() {
  const provedor = document.getElementById('ia-provedor').value;
  const hints = {
    anthropic: 'Obtenha em <strong>console.anthropic.com</strong> → API Keys.',
    openai: 'Obtenha em <strong>platform.openai.com</strong> → API Keys.',
    gemini: 'Obtenha em <strong>aistudio.google.com</strong> → Get API Key.',
    openrouter: 'Obtenha em <strong>openrouter.ai</strong> → Keys.',
  };
  const placeholders = {
    anthropic: 'sk-ant-api03-...',
    openai: 'sk-...',
    gemini: 'AIza...',
    openrouter: 'sk-or-...',
  };
  document.getElementById('api-hint-texto').innerHTML = hints[provedor] || '';
  document.getElementById('api-key').placeholder = placeholders[provedor] || 'Cole sua API Key aqui';
  document.getElementById('openrouter-model-wrap').style.display = provedor === 'openrouter' ? 'block' : 'none';
  localStorage.setItem('of_ia_provedor', provedor);
}

// ─── IA ───────────────────────────────────────────────────────
function toggleApiKey() {
  const input = document.getElementById('api-key');
  input.type = input.type === 'password' ? 'text' : 'password';
}

async function gerarComIA() {
  const btn        = document.getElementById('btn-ia');
  const apiKey     = document.getElementById('api-key').value.trim();
  const provedor   = document.getElementById('ia-provedor').value;
  const disciplina = document.getElementById('ia-disciplina').value;
  const topico     = document.getElementById('ia-topico').value.trim();
  const quantidade = document.getElementById('ia-quantidade').value;
  const dificuldade = document.getElementById('ia-dificuldade').value;
  const concurso   = document.getElementById('concurso').value.trim() || 'Concurso';
  const banca      = document.getElementById('banca').value;
  const modelo     = document.getElementById('openrouter-model')?.value.trim() || '';

  if (!apiKey) return showToast('Informe sua API Key', 'erro');
  if (!disciplina) return showToast('Selecione uma disciplina', 'erro');

  localStorage.setItem('of_api_key', apiKey);
  btn.classList.add('loading'); btn.disabled = true;
  document.getElementById('ia-resultado').classList.remove('visivel');

  try {
    const res = await fetch('/gerar-ia', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ api_key:apiKey, provedor, modelo, disciplina, banca, topico,
                             quantidade:parseInt(quantidade), dificuldade, concurso, destino: destinoAtual })
    });
    const data = await res.json();
    if (data.erro) { showToast(data.erro, 'erro'); return; }
    questoesGeradasIA = data.questoes;
    mostrarPreviewIA(questoesGeradasIA, disciplina);
    showToast(`${questoesGeradasIA.length} questões geradas!`, 'sucesso');
  } catch(e) {
    showToast('Erro de conexão.', 'erro');
  } finally {
    btn.classList.add('loading'); btn.disabled = true;
    btn.classList.remove('loading'); btn.disabled = false;
  }
}

function mostrarPreviewIA(questoes, disciplina) {
  const resultado = document.getElementById('ia-resultado');
  resultado.innerHTML = `
    <div class="ia-resultado-header">
      <span>✅ ${questoes.length} questões prontas — ${disciplina}</span>
      <button class="btn-usar-questoes" onclick="usarQuestoesIA()">Usar no PDF →</button>
    </div>
    ${questoes.map(q => `
      <div class="ia-questao-preview">
        <div class="ia-questao-num">Questão ${q.num} · ${disciplina}</div>
        <div class="ia-questao-enun">${q.enunciado.length>120?q.enunciado.substring(0,120)+'...':q.enunciado}</div>
        <div class="ia-questao-alts">${q.alternativas.map(a=>`(${a.letra}) ${a.texto.length>60?a.texto.substring(0,60)+'...':a.texto}`).join('<br>')}</div>
      </div>`).join('')}`;
  resultado.classList.add('visivel');
}

function usarQuestoesIA() {
  if (!questoesGeradasIA.length) return;
  const disciplina = questoesGeradasIA[0]?.disciplina || '';
  let texto = `[DISCIPLINA: ${disciplina}]\n\n`;
  questoesGeradasIA.forEach(q => {
    texto += `${q.num}. ${q.enunciado}\n\n`;
    q.alternativas.forEach(a => { texto += `(${a.letra}) ${a.texto}\n`; });
    texto += '\n';
  });
  document.getElementById('texto-corrido').value = texto;
  parsearPrevia();
  document.querySelectorAll('.modo-tab').forEach(t => t.classList.toggle('ativo', t.dataset.modo==='texto'));
  modoAtual = 'texto';
  document.getElementById('modo-manual').classList.add('oculto');
  document.getElementById('modo-ia').classList.remove('visivel');
  document.getElementById('modo-texto').classList.add('visivel');
  showToast('Questões carregadas! Revise e gere o PDF.', 'sucesso');
}

// ─── TOAST ────────────────────────────────────────────────────
let toastTimer = null;
function showToast(msg, tipo='sucesso') {
  const toast = document.getElementById('toast');
  toast.querySelector('.toast-icon').textContent = tipo==='sucesso' ? '✅' : '❌';
  toast.querySelector('.toast-msg').textContent  = msg;
  toast.className = `toast ${tipo} visivel`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('visivel'), 3500);
}
