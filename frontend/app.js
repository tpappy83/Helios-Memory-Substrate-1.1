/* ═══════════════════════════════════════════════════════
   Helios — frontend (v0.2) — pipeline-driven UX
   Three execution modes, auto-detected:
     1. LIVE        — talks to local FastAPI /chat/stream SSE
     2. BROWSER-DIRECT — uses user's OpenRouter key from localStorage,
                         runs full Helios pipeline in JS, persists memories locally
     3. DEMO        — full pipeline simulation with mock LLM
═══════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ─── Constants ──────────────────────────────────────
  const STAGES = ['ingest', 'score', 'read', 'modify', 'write', 'store'];
  const SESSION_ID = 'default';
  const NAMESPACE = 'default';
  const STORAGE_K = {
    memories:    'helios.memories.v1',
    audit:       'helios.audit.v1',
    llmKey:      'helios.llm_key.v1',
    llmModel:    'helios.llm_model.v1',
  };
  const DEFAULT_FREE_MODEL = 'google/gemini-2.0-flash-exp:free';

  // Tiering formulas — ported VERBATIM from core/tiering.py
  // (Helios v4.1 spec lines 54, 173-186, 193-197)
  const TIERING = {
    ALPHA: 0.3, PROMOTE: 0.65, DEMOTE: 0.35,
    W_SIM: 0.55, W_VAL: 0.20, W_REC: 0.10, W_TIER: 0.10, W_DRIFT: 0.05,
    TIER_BONUS: { hot: 1.0, cold: 0.3 },
    RECENCY_TAU: 600.0,
  };
  const computeDrift   = (cycles, reads) => 0.02 + 0.01 * cycles + 0.001 * reads;
  const computeRecency = (ts, now) => Math.exp(-((now ?? Date.now()/1000) - ts) / TIERING.RECENCY_TAU);
  const computeFinal   = (sim, val, rec, tierBonus, drift) =>
    TIERING.W_SIM*sim + TIERING.W_VAL*val + TIERING.W_REC*rec + TIERING.W_TIER*tierBonus - TIERING.W_DRIFT*drift;
  const updateTempEMA  = (prev, score) => TIERING.ALPHA * score + (1 - TIERING.ALPHA) * prev;

  // ─── Element refs ──────────────────────────────────
  const $ = (id) => document.getElementById(id);
  const form = $('chat-form'), input = $('chat-input'), sendBtn = $('send-btn');
  const chatLog = $('chat-log'), emptyState = $('chat-empty');
  const connStatus = $('conn-status'), demoBanner = $('demo-banner'), demoBannerText = $('demo-banner-text');
  const modal = $('llm-modal'), modalClose = $('llm-modal-close');
  const llmForm = $('llm-form'), llmKeyInput = $('llm-key-input'), llmModelInput = $('llm-model-input');
  const llmDisconnect = $('llm-disconnect'), llmClearMem = $('llm-clear-memories');
  const stageEls = Object.fromEntries(STAGES.map(s =>
    [s, document.querySelector(`.stage[data-stage="${s}"]`)]
  ));
  const statusNs = $('status-namespace');
  const statusRecords = $('status-records'), statusTiers = $('status-tiers'), statusLatency = $('status-latency');

  // ─── State ─────────────────────────────────────────
  let mode = 'pending';   // 'live' | 'direct' | 'demo'
  const apiBase = window.location.pathname.startsWith('/ui')
    ? '' : 'http://localhost:8000';

  // ─── localStorage helpers ──────────────────────────
  const Store = {
    getMemories() {
      try { return JSON.parse(localStorage.getItem(STORAGE_K.memories) || '[]'); }
      catch { return []; }
    },
    setMemories(arr) { localStorage.setItem(STORAGE_K.memories, JSON.stringify(arr)); },
    getAudit() {
      try { return JSON.parse(localStorage.getItem(STORAGE_K.audit) || '[]'); }
      catch { return []; }
    },
    setAudit(arr) { localStorage.setItem(STORAGE_K.audit, JSON.stringify(arr.slice(-200))); },
    getKey()      { return localStorage.getItem(STORAGE_K.llmKey) || ''; },
    setKey(k)     { localStorage.setItem(STORAGE_K.llmKey, k); },
    clearKey()    { localStorage.removeItem(STORAGE_K.llmKey); },
    getModel()    { return localStorage.getItem(STORAGE_K.llmModel) || DEFAULT_FREE_MODEL; },
    setModel(m)   { localStorage.setItem(STORAGE_K.llmModel, m || DEFAULT_FREE_MODEL); },
    clearAll() {
      localStorage.removeItem(STORAGE_K.memories);
      localStorage.removeItem(STORAGE_K.audit);
    },
  };

  // ─── Memory model (mirrors core/memory.Memory) ────
  function newMemoryId() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
  }
  function createMemory({content, type, importance, metadata}) {
    return {
      id: newMemoryId(),
      type, content,
      importance: importance ?? 0.5,
      timestamp: Date.now() / 1000,
      namespace: NAMESPACE,
      tier: 'cold',
      temperature: 0.5,
      read_count: 0,
      compression_cycles: 0,
      last_accessed: null,
      metadata: metadata || {},
    };
  }
  function writeAudit(entry) {
    const log = Store.getAudit();
    log.push({ ...entry, id: log.length + 1, timestamp: Date.now() / 1000 });
    Store.setAudit(log);
  }

  // ─── FTS-like keyword candidates (mirrors core.memory.keyword_candidates) ──
  function ftsCandidates(query, memories, k = 25) {
    const tokens = query.toLowerCase().split(/\W+/).filter(t => t.length > 2);
    if (!tokens.length) return [];
    const scored = [];
    for (const m of memories) {
      const content = m.content.toLowerCase();
      let hits = 0;
      for (const t of tokens) if (content.includes(t)) hits++;
      if (hits > 0) scored.push({ m, hits });
    }
    scored.sort((a, b) => b.hits - a.hits);
    return scored.slice(0, k).map(x => x.m);
  }

  // ─── Mock heuristic classifier (used when no real LLM) ────
  function mockClassify(text) {
    const lower = text.toLowerCase();
    let type = 'observation', importance = 0.5;
    if (lower.includes('decided') || lower.includes('chose') || lower.includes('chosen'))
      { type = 'decision'; importance = 0.7; }
    else if (lower.includes('happened') || lower.includes('occurred') || lower.includes('shipped'))
      { type = 'event'; importance = 0.6; }
    else if (lower.includes('summary') || lower.includes('overall'))
      { type = 'summary'; importance = 0.5; }
    const queryLike = lower.startsWith('what') || lower.startsWith('how') || lower.startsWith('why') || lower.includes('?');
    if (queryLike) { type = 'observation'; importance = 0.4; }
    return { type, importance, metadata: {} };
  }

  function mockRerank(query, candidates, topK = 5) {
    const qTokens = new Set(query.toLowerCase().split(/\W+/));
    const out = candidates.map(m => {
      const cTokens = new Set(m.content.toLowerCase().split(/\W+/));
      let overlap = 0;
      for (const t of qTokens) if (cTokens.has(t)) overlap++;
      return { id: m.id, score: overlap / Math.max(qTokens.size, 1) };
    }).sort((a, b) => b.score - a.score);
    return out.slice(0, topK).map(x => [x.id, x.score]);
  }

  function mockReply(message, retrieved) {
    if (retrieved.length === 0) {
      return `Helios indexed your message. No prior context retrieved. Configure a real LLM to get a generative response.`;
    }
    const top = retrieved[0];
    return `Helios retrieved ${retrieved.length} relevant memor${retrieved.length===1?'y':'ies'}. The strongest match is a ${top.type}: "${top.content.slice(0, 100)}..."`;
  }

  // ─── OpenRouter direct calls (BROWSER-DIRECT mode) ────
  const CLASSIFY_SYS = `You are Helios's memory classifier. Read the user's message and return STRICT JSON with three fields:
- "type": one of "event", "state", "summary", "decision", "observation". Default "observation".
- "importance": a float in [0,1]. Decisions and rationale-backed events ~0.7; routine observations ~0.4; pure questions ~0.3.
- "metadata": object with optional "topic" (1-3 words), "entities" (string list).
Return ONLY the JSON object.`;

  const RERANK_SYS = `You are Helios's memory reranker. Score each candidate memory's relevance to the user's query on a 0.0 to 1.0 scale. Return STRICT JSON: an object with key "scores" mapping each candidate id (string) to its float score. Higher = more relevant.`;

  async function openRouterCall({ messages, model, temperature = 0, max_tokens = 400, json = false, stream = false }) {
    const key = Store.getKey();
    if (!key) throw new Error('no_key');
    const body = {
      model: model || Store.getModel(),
      messages,
      temperature,
      max_tokens,
    };
    if (json) body.response_format = { type: 'json_object' };
    if (stream) body.stream = true;

    const resp = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${key}`,
        'HTTP-Referer': window.location.origin,
        'X-Title': 'Helios memory demo',
      },
      body: JSON.stringify(body),
    });
    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`openrouter_${resp.status}: ${errText.slice(0, 200)}`);
    }
    return resp;
  }

  function parseJsonTolerant(raw) {
    if (!raw) return {};
    let s = raw.trim().replace(/^```(?:json)?/i, '').replace(/```$/, '').trim();
    try { return JSON.parse(s); } catch { return {}; }
  }

  async function realClassify(text) {
    const resp = await openRouterCall({
      messages: [{role: 'system', content: CLASSIFY_SYS}, {role: 'user', content: text}],
      json: true, max_tokens: 200,
    });
    const data = await resp.json();
    const raw = data.choices?.[0]?.message?.content || '{}';
    const parsed = parseJsonTolerant(raw);
    const validTypes = ['event','state','summary','decision','observation'];
    return {
      type: validTypes.includes(parsed.type) ? parsed.type : 'observation',
      importance: Math.min(1, Math.max(0, Number(parsed.importance ?? 0.5))),
      metadata: parsed.metadata && typeof parsed.metadata === 'object' ? parsed.metadata : {},
    };
  }

  async function realRerank(query, candidates) {
    if (!candidates.length) return [];
    const cand = candidates.slice(0, 25).map(m => `- id=${m.id.slice(0,12)}: [${m.type}] ${m.content.slice(0,140)}`).join('\n');
    const resp = await openRouterCall({
      messages: [
        {role: 'system', content: RERANK_SYS},
        {role: 'user', content: `Query: ${query}\n\nCandidates:\n${cand}`},
      ],
      json: true, max_tokens: 600,
    });
    const data = await resp.json();
    const raw = data.choices?.[0]?.message?.content || '{}';
    const parsed = parseJsonTolerant(raw);
    const scores = parsed.scores && typeof parsed.scores === 'object' ? parsed.scores : {};
    const out = candidates.map(m => {
      const short = m.id.slice(0, 12);
      const s = scores[short] ?? scores[m.id] ?? 0;
      return [m.id, Number(s) || 0];
    });
    out.sort((a, b) => b[1] - a[1]);
    return out;
  }

  async function* realChatStream(message, retrieved) {
    const sys = `You are Helios, a memory-grounded assistant. Use retrieved memories below when relevant.\n\nRetrieved memories:\n` +
      retrieved.map(m => `- [${m.type}] ${m.content}`).join('\n');
    const resp = await openRouterCall({
      messages: [{role: 'system', content: sys}, {role: 'user', content: message}],
      temperature: 0.3, max_tokens: 800, stream: true,
    });
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split('\n');
      buf = lines.pop() || '';
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const d = line.slice(6).trim();
        if (d === '[DONE]') return;
        try {
          const j = JSON.parse(d);
          const tok = j.choices?.[0]?.delta?.content;
          if (tok) yield tok;
        } catch { /* ignore partial */ }
      }
    }
  }

  // ─── Pipeline UI ───────────────────────────────────
  function resetPipeline() {
    for (const s of STAGES) {
      const el = stageEls[s];
      el.classList.remove('running', 'complete', 'error');
      el.querySelector('.stage-status').textContent = 'idle';
      const d = el.querySelector('.stage-data');
      d.hidden = true; d.innerHTML = '';
    }
  }
  function updateStage(name, status, data) {
    const el = stageEls[name]; if (!el) return;
    el.classList.remove('running', 'complete', 'error');
    if (status === 'running') {
      el.classList.add('running');
      el.querySelector('.stage-status').textContent = 'running';
    } else if (status === 'complete') {
      el.classList.add('complete');
      el.querySelector('.stage-status').textContent = 'ok';
      if (data) renderStageData(el, data);
    } else if (status === 'error') {
      el.classList.add('error');
      el.querySelector('.stage-status').textContent = 'error';
    }
  }
  function renderStageData(el, data) {
    const d = el.querySelector('.stage-data');
    d.innerHTML = '';
    for (const [k, v] of Object.entries(data)) {
      const key = document.createElement('span'); key.className = 'k'; key.textContent = k;
      const val = document.createElement('span'); val.className = 'v';
      val.textContent = (typeof v === 'object') ? JSON.stringify(v) : String(v);
      d.appendChild(key); d.appendChild(val);
    }
    d.hidden = false;
  }

  // ─── Chat UI ───────────────────────────────────────
  function hideEmptyState() { if (emptyState) emptyState.style.display = 'none'; }

  function appendUserMessage(text) {
    hideEmptyState();
    const li = document.createElement('li');
    li.className = 'msg user';
    const meta = document.createElement('div'); meta.className = 'msg-meta';
    const lbl = document.createElement('span'); lbl.textContent = 'you'; meta.appendChild(lbl);
    const body = document.createElement('div'); body.className = 'msg-body'; body.textContent = text;
    li.appendChild(meta); li.appendChild(body);
    chatLog.appendChild(li); li.scrollIntoView({behavior: 'smooth', block: 'end'});
    return li;
  }
  function setUserPill(li, type, importance) {
    const meta = li.querySelector('.msg-meta');
    meta.innerHTML = '';
    if (type) {
      const pill = document.createElement('span');
      pill.className = 'type-pill'; pill.textContent = type;
      meta.appendChild(pill);
    }
    if (importance !== null && importance !== undefined) {
      const imp = document.createElement('span');
      imp.className = 'importance'; imp.textContent = `importance ${importance.toFixed(2)}`;
      meta.appendChild(imp);
    }
  }
  function appendAssistantMessage(text = '') {
    const li = document.createElement('li');
    li.className = 'msg assistant';
    const meta = document.createElement('div'); meta.className = 'msg-meta';
    const tag = document.createElement('span'); tag.textContent = 'helios'; meta.appendChild(tag);
    const body = document.createElement('div'); body.className = 'msg-body'; body.textContent = text;
    li.appendChild(meta); li.appendChild(body);
    chatLog.appendChild(li); li.scrollIntoView({behavior: 'smooth', block: 'end'});
    return li;
  }
  function setAssistantFooter(li, parts) {
    let footer = li.querySelector('.msg-footer');
    if (!footer) {
      footer = document.createElement('div');
      footer.className = 'msg-footer';
      li.appendChild(footer);
    }
    footer.textContent = parts.filter(Boolean).join(' · ');
  }

  // ─── Status bar ────────────────────────────────────
  function refreshStatus() {
    statusNs.textContent = NAMESPACE;
    if (mode === 'live') {
      // Stats from API
      fetch(`${apiBase}/stats`).then(r => r.json()).then(d => {
        statusRecords.textContent = d.record_count;
        const t = d.tier_distribution || {};
        statusTiers.textContent = `cold:${t.cold||0} hot:${t.hot||0}`;
      }).catch(() => {});
    } else {
      const mems = Store.getMemories();
      statusRecords.textContent = mems.length;
      const cold = mems.filter(m => m.tier === 'cold').length;
      const hot  = mems.filter(m => m.tier === 'hot').length;
      statusTiers.textContent = `cold:${cold} hot:${hot}`;
    }
  }

  // ─── Mode detection + connect handling ─────────────
  function setConn(state, label) {
    connStatus.classList.remove('conn-live', 'conn-direct', 'conn-demo', 'conn-pending');
    connStatus.classList.add(`conn-${state}`);
    connStatus.querySelector('.conn-label').textContent = label || state;
  }
  function setMode(newMode) {
    mode = newMode;
    if (mode === 'live') {
      setConn('live', 'live');
      demoBanner.hidden = true;
    } else if (mode === 'direct') {
      setConn('direct', 'direct llm');
      demoBanner.hidden = true;
    } else {
      setConn('demo', 'demo');
      demoBanner.hidden = false;
      demoBannerText.textContent = 'Demo mode — click to use a real LLM';
    }
    refreshStatus();
  }

  async function detectMode() {
    setConn('pending', 'detecting');
    // First try local API
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 800);
      const r = await fetch(`${apiBase}/health`, { signal: ctrl.signal });
      clearTimeout(t);
      if (r.ok) { setMode('live'); return; }
    } catch (_) { /* fall through */ }
    // Else check for stored key
    if (Store.getKey()) { setMode('direct'); return; }
    // Else demo
    setMode('demo');
  }

  // ─── Send dispatchers ──────────────────────────────
  async function send(message) {
    if (!message.trim()) return;
    resetPipeline();
    const userLi = appendUserMessage(message);
    const t0 = performance.now();
    sending = true; sendBtn.classList.add('sending'); sendBtn.disabled = true;
    input.value = ''; autoResize();

    try {
      if (mode === 'live')   await sendLive(message, userLi, t0);
      else if (mode === 'direct') await sendDirect(message, userLi, t0);
      else                   await sendDemo(message, userLi, t0);
    } catch (err) {
      console.error('send failed', err);
      const a = appendAssistantMessage(`[error: ${err.message}]`);
      setAssistantFooter(a, [`${Math.round(performance.now() - t0)}ms`]);
    } finally {
      sending = false;
      sendBtn.classList.remove('sending');
      updateSendBtn();
      input.focus();
      refreshStatus();
    }
  }

  // ─── LIVE mode (FastAPI SSE) ──────────────────────
  async function sendLive(message, userLi, t0) {
    const resp = await fetch(`${apiBase}/chat/stream`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message, session_id: SESSION_ID}),
    });
    if (!resp.ok || !resp.body) throw new Error(`HTTP ${resp.status}`);
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    let assistantLi = null, assistantText = '';
    let memoryId = null;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const blocks = buf.split('\n\n');
      buf = blocks.pop() || '';
      for (const block of blocks) {
        const dataLine = block.split('\n').find(l => l.startsWith('data: '));
        if (!dataLine) continue;
        let ev; try { ev = JSON.parse(dataLine.slice(6)); } catch { continue; }
        if (ev.type === 'stage') {
          updateStage(ev.stage, ev.status, ev.data || null);
          if (ev.stage === 'score' && ev.status === 'complete' && ev.data) {
            setUserPill(userLi, ev.data.memory_type, ev.data.importance);
          }
        } else if (ev.type === 'classified') {
          memoryId = ev.memory_id;
        } else if (ev.type === 'token') {
          assistantText += ev.content;
          if (!assistantLi) assistantLi = appendAssistantMessage();
          assistantLi.querySelector('.msg-body').textContent = assistantText;
        } else if (ev.type === 'done') {
          const latency = ev.latency_ms ?? (performance.now() - t0);
          if (!assistantLi) assistantLi = appendAssistantMessage(ev.content || assistantText);
          assistantLi.querySelector('.msg-body').textContent = ev.content || assistantText;
          setAssistantFooter(assistantLi, [
            `${Math.round(latency)}ms`,
            `stored as ${(ev.memory_id || memoryId || '').slice(0, 8)}`,
          ]);
          statusLatency.textContent = `${Math.round(latency)}ms`;
        }
      }
    }
  }

  // ─── BROWSER-DIRECT mode (OpenRouter from JS + localStorage memory) ───
  async function sendDirect(message, userLi, t0) {
    const now = Date.now() / 1000;
    let memories = Store.getMemories();

    // ── INGEST ───────────────────────────────
    updateStage('ingest', 'running');
    updateStage('ingest', 'complete', { chars: message.length, namespace: NAMESPACE });

    // ── SCORE ───────────────────────────────
    updateStage('score', 'running');
    let cls;
    try { cls = await realClassify(message); }
    catch (err) { console.warn('classify failed, using mock:', err.message); cls = mockClassify(message); }
    updateStage('score', 'complete', { memory_type: cls.type, importance: cls.importance });
    setUserPill(userLi, cls.type, cls.importance);

    // ── READ ─────────────────────────────────
    updateStage('read', 'running');
    const candidates = ftsCandidates(message, memories, 25);
    let scored = [];
    if (candidates.length > 0) {
      try { scored = await realRerank(message, candidates); }
      catch (err) { console.warn('rerank failed, using mock:', err.message); scored = mockRerank(message, candidates); }
    }
    updateStage('read', 'complete', { fts_candidates: candidates.length, reranked: scored.length });

    // ── MODIFY (tier-aware feedback) ─────────
    updateStage('modify', 'running');
    let promoted = 0, demoted = 0;
    if (scored.length > 0) {
      const byId = Object.fromEntries(memories.map(m => [m.id, m]));
      const topK = scored.slice(0, 20);
      for (const [mid, sim] of topK) {
        const m = byId[mid]; if (!m) continue;
        const recency = computeRecency(m.timestamp, now);
        const drift   = computeDrift(m.compression_cycles, m.read_count);
        const tierB   = TIERING.TIER_BONUS[m.tier] ?? TIERING.TIER_BONUS.cold;
        const finalScore = computeFinal(sim, m.importance, recency, tierB, drift);
        m.temperature = updateTempEMA(m.temperature, finalScore);
        m.read_count += 1; m.last_accessed = now;
        if (m.temperature > TIERING.PROMOTE && m.tier !== 'hot') {
          m.tier = 'hot'; m.compression_cycles += 1; promoted += 1;
        } else if (m.temperature < TIERING.DEMOTE && m.tier !== 'cold') {
          m.tier = 'cold'; m.compression_cycles += 1; demoted += 1;
        }
      }
    }
    updateStage('modify', 'complete', { top_k_updated: Math.min(scored.length, 20), promoted, demoted });

    // ── WRITE ────────────────────────────────
    updateStage('write', 'running');
    const newMem = createMemory({content: message, type: cls.type, importance: cls.importance, metadata: cls.metadata});
    memories.push(newMem);
    Store.setMemories(memories);
    updateStage('write', 'complete', { memory_id: newMem.id.slice(0, 8) });

    // ── STORE (audit log) ────────────────────
    updateStage('store', 'running');
    writeAudit({
      actor_ref: 'default', namespace: NAMESPACE,
      action: 'memory.write', target_kind: 'memory_record',
      target_ref: newMem.id, reason: `type=${cls.type}`,
    });
    updateStage('store', 'complete', { tier: newMem.tier, temperature: newMem.temperature, audit_logged: true });

    // ── Generative response (real LLM stream) ─
    const retrieved = scored.slice(0, 3).map(([mid]) => memories.find(m => m.id === mid)).filter(Boolean);
    const assistantLi = appendAssistantMessage();
    let assistantText = '';
    try {
      for await (const tok of realChatStream(message, retrieved)) {
        assistantText += tok;
        assistantLi.querySelector('.msg-body').textContent = assistantText;
      }
    } catch (err) {
      console.warn('chat stream failed, falling back to mock:', err.message);
      assistantText = mockReply(message, retrieved);
      assistantLi.querySelector('.msg-body').textContent = assistantText;
    }
    const latency = performance.now() - t0;
    setAssistantFooter(assistantLi, [`${Math.round(latency)}ms`, `stored as ${newMem.id.slice(0,8)}`, `retrieved ${retrieved.length}`]);
    statusLatency.textContent = `${Math.round(latency)}ms`;
  }

  // ─── DEMO mode (full simulation) ──────────────────
  async function sendDemo(message, userLi, t0) {
    const sleep = (ms) => new Promise(r => setTimeout(r, ms));
    const now = Date.now() / 1000;
    let memories = Store.getMemories();
    const cls = mockClassify(message);
    const newMem = createMemory({content: message, type: cls.type, importance: cls.importance});

    updateStage('ingest', 'running'); await sleep(12);
    updateStage('ingest', 'complete', { chars: message.length, namespace: NAMESPACE });
    await sleep(40);

    updateStage('score', 'running'); await sleep(140);
    updateStage('score', 'complete', { memory_type: cls.type, importance: cls.importance });
    setUserPill(userLi, cls.type, cls.importance);
    await sleep(30);

    updateStage('read', 'running'); await sleep(60);
    const candidates = ftsCandidates(message, memories, 25);
    const scored = mockRerank(message, candidates);
    updateStage('read', 'complete', { fts_candidates: candidates.length, reranked: scored.length });
    await sleep(30);

    updateStage('modify', 'running'); await sleep(18);
    let promoted = 0, demoted = 0;
    const byId = Object.fromEntries(memories.map(m => [m.id, m]));
    for (const [mid, sim] of scored.slice(0, 20)) {
      const m = byId[mid]; if (!m) continue;
      const recency = computeRecency(m.timestamp, now);
      const drift = computeDrift(m.compression_cycles, m.read_count);
      const tierB = TIERING.TIER_BONUS[m.tier] ?? TIERING.TIER_BONUS.cold;
      const finalScore = computeFinal(sim, m.importance, recency, tierB, drift);
      m.temperature = updateTempEMA(m.temperature, finalScore);
      m.read_count += 1; m.last_accessed = now;
      if (m.temperature > TIERING.PROMOTE && m.tier !== 'hot') { m.tier='hot'; m.compression_cycles++; promoted++; }
      else if (m.temperature < TIERING.DEMOTE && m.tier !== 'cold') { m.tier='cold'; m.compression_cycles++; demoted++; }
    }
    updateStage('modify', 'complete', { top_k_updated: Math.min(scored.length, 20), promoted, demoted });
    await sleep(20);

    updateStage('write', 'running'); await sleep(15);
    memories.push(newMem);
    Store.setMemories(memories);
    updateStage('write', 'complete', { memory_id: newMem.id.slice(0, 8) });
    await sleep(20);

    updateStage('store', 'running'); await sleep(8);
    writeAudit({actor_ref:'default', namespace: NAMESPACE, action:'memory.write', target_kind:'memory_record', target_ref: newMem.id, reason:`type=${cls.type}`});
    updateStage('store', 'complete', { tier: newMem.tier, temperature: newMem.temperature, audit_logged: true });
    await sleep(40);

    const retrieved = scored.slice(0, 3).map(([mid]) => memories.find(m => m.id === mid)).filter(Boolean);
    const reply = mockReply(message, retrieved);
    const assistantLi = appendAssistantMessage(reply);
    const latency = performance.now() - t0;
    setAssistantFooter(assistantLi, [`${Math.round(latency)}ms`, `stored as ${newMem.id.slice(0,8)}`, `retrieved ${retrieved.length}`]);
    statusLatency.textContent = `${Math.round(latency)}ms`;
  }

  // ─── Connect LLM modal ─────────────────────────────
  function openModal() {
    llmKeyInput.value = Store.getKey();
    llmModelInput.value = Store.getModel() === DEFAULT_FREE_MODEL ? '' : Store.getModel();
    modal.hidden = false;
    setTimeout(() => llmKeyInput.focus(), 50);
  }
  function closeModal() { modal.hidden = true; }
  // Settings reachable from: demo banner (when in demo mode) + connection pill (always)
  demoBanner.addEventListener('click', openModal);
  connStatus.addEventListener('click', openModal);
  modalClose.addEventListener('click', closeModal);
  modal.querySelector('.modal-overlay').addEventListener('click', closeModal);
  llmForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const key = llmKeyInput.value.trim();
    const model = llmModelInput.value.trim();
    if (!key) return;
    Store.setKey(key);
    if (model) Store.setModel(model);
    closeModal();
    setMode('direct');
  });
  llmDisconnect.addEventListener('click', () => {
    Store.clearKey();
    closeModal();
    detectMode();
  });
  llmClearMem.addEventListener('click', () => {
    if (confirm('Clear all stored memories and audit log?')) {
      Store.clearAll();
      chatLog.innerHTML = '';
      if (emptyState) emptyState.style.display = '';
      resetPipeline();
      refreshStatus();
    }
  });

  // ─── Input handling ────────────────────────────────
  let sending = false;
  function autoResize() {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 200) + 'px';
  }
  function updateSendBtn() { sendBtn.disabled = !input.value.trim() || sending; }
  input.addEventListener('input', () => { autoResize(); updateSendBtn(); });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input.value); }
  });
  form.addEventListener('submit', (e) => { e.preventDefault(); send(input.value); });
  document.querySelectorAll('.suggestion').forEach(btn => {
    btn.addEventListener('click', () => {
      const msg = btn.getAttribute('data-msg');
      input.value = msg; autoResize(); updateSendBtn();
      send(msg);
    });
  });

  // ─── Boot ──────────────────────────────────────────
  (async () => {
    await detectMode();
    setInterval(refreshStatus, 5000);
    input.focus();
  })();

})();
