/* THE SIGNAL 2026 — Guestbook JS */

// ── Topics (loaded from API) ────────────────────────────
let TOPICS = [];
let CODES  = {};

function getActiveTopicIdx() {
  const h = new Date().getHours();
  return TOPICS.findIndex(t => h >= t.time_start && h < t.time_end);
}

function updateTopicDisplay() {
  const idx = getActiveTopicIdx();
  const n   = TOPICS.length;

  for (let i = 0; i < n; i++) {
    const dot = document.getElementById(`tsd-${i}`);
    if (!dot) continue;
    dot.className = 'ts-dot';
    if (i < idx)      dot.classList.add('done');
    else if (i === idx) dot.classList.add('active');
  }

  const textEl = document.getElementById('topic-text');
  if (idx >= 0) {
    textEl.textContent = TOPICS[idx].topic_text;
    document.getElementById('msg').placeholder =
      (TOPICS[idx].hint || '') + '\n(Ctrl+Enter 빠른 전송)';
  } else {
    const h = new Date().getHours();
    const first = TOPICS[0];
    textEl.textContent = (first && h < first.time_start)
      ? `"오전 ${first.time_start}시부터 주제가 공개됩니다!"`
      : '"THE SIGNAL 방명록에 자유롭게 남겨주세요 📟"';
    document.getElementById('msg').placeholder =
      'THE SIGNAL에서의 추억을 남겨보세요...\n(Ctrl+Enter 빠른 전송)';
  }
}

// ── Render pager code selector ──────────────────────────
function renderCodeSelector(codes) {
  const container = document.getElementById('cs-body');
  if (!container) return;

  // Group by category
  const cats = {};
  codes.forEach(c => {
    const cat = c.category || '기타';
    if (!cats[cat]) cats[cat] = [];
    cats[cat].push(c);
    CODES[c.code] = `${c.korean} (${c.english})`;
  });

  let html = '<div class="cs-hd">📟 삐삐 코드 선택</div>';
  Object.entries(cats).forEach(([cat, items]) => {
    html += `<div class="cs-section-label">${esc(cat)}</div><div class="cs-grid">`;
    items.forEach(c => {
      html += `<div class="cs-item" onclick="selectCode('${esc(c.code)}')">
        <span class="cs-n">${esc(c.code)}</span>
        <span class="cs-m">${esc(c.korean)}</span>
      </div>`;
    });
    html += '</div>';
  });
  container.innerHTML = html;
}

// ── Clock ──────────────────────────────────────────────
function tick() {
  const n = new Date();
  const p = v => String(v).padStart(2, '0');
  document.getElementById('clock').textContent =
    `${p(n.getHours())}:${p(n.getMinutes())}:${p(n.getSeconds())}`;
  document.getElementById('cal').textContent =
    `${n.getFullYear()}.${p(n.getMonth()+1)}.${p(n.getDate())}`;
}
setInterval(tick, 1000);
tick();

// Update topic once per minute
setInterval(updateTopicDisplay, 60000);

// ── Char counter ───────────────────────────────────────
document.getElementById('msg').addEventListener('input', function () {
  document.getElementById('msgcnt').textContent = this.value.length;
});

// ── Escape helper ──────────────────────────────────────
function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}

// ── Format time ────────────────────────────────────────
function fmtTime(str) {
  const d = new Date(str + 'Z');
  const p = v => String(v).padStart(2, '0');
  return `${p(d.getMonth()+1)}.${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

// ── Build reply card HTML ──────────────────────────────
function replyCardHtml(r) {
  return `
    <div class="reply-card">
      <div class="card-hd">
        <span class="card-name">${esc(r.name)}</span>
        <span class="card-time">${fmtTime(r.time)}</span>
      </div>
      <div class="card-msg">${esc(r.message)}</div>
      <div class="card-actions">
        <button class="like-btn${r.liked ? ' liked' : ''}"
                onclick="toggleLike(${r.id}, this)">
          ${r.liked ? '♥' : '♡'}&nbsp;<span class="like-cnt">${r.likes}</span>
        </button>
      </div>
    </div>`;
}

// ── Build comment card element ─────────────────────────
function makeCard(c, replies) {
  const el = document.createElement('div');
  el.className = 'card';
  el.id = `card-${c.id}`;

  const repliesHtml = (replies || []).map(replyCardHtml).join('');

  el.innerHTML = `
    <div class="card-hd">
      <span class="card-name">${esc(c.name)}</span>
      <span class="card-time">${fmtTime(c.time)}</span>
    </div>
    <div class="card-msg">${esc(c.message)}</div>
    <div class="card-actions">
      <button class="like-btn${c.liked ? ' liked' : ''}"
              onclick="toggleLike(${c.id}, this)">
        ${c.liked ? '♥' : '♡'}&nbsp;<span class="like-cnt">${c.likes}</span>
      </button>
      <button class="reply-btn" onclick="toggleReplyForm(${c.id})">↩ 답글</button>
    </div>
    <div class="reply-form hidden" id="rf-${c.id}">
      <div class="rf-row">
        <input type="text" id="rn-${c.id}" class="inp sm rf-name"
               placeholder="이름" maxlength="20" autocomplete="off">
        <input type="text" id="rm-${c.id}" class="inp sm rf-msg"
               placeholder="답글 내용..." maxlength="150" autocomplete="off"
               onkeydown="if(event.ctrlKey&&event.key==='Enter')submitReply(${c.id})">
      </div>
      <div class="rf-btns">
        <button class="btn primary" onclick="submitReply(${c.id})">↩ 답글 달기</button>
        <button class="btn" onclick="toggleReplyForm(${c.id})">취소</button>
      </div>
    </div>
    <div class="replies" id="replies-${c.id}">${repliesHtml}</div>
  `;
  return el;
}

// ── Build / patch feed (no full redraw = no flicker) ──
let totalCount = 0;

function buildFeed(comments) {
  const feed = document.getElementById('feed');
  const prevScroll = feed.scrollTop;

  // Remove placeholder on first real load
  feed.querySelector('.loading-msg, .empty-msg')?.remove();

  if (!comments.length) {
    if (!feed.querySelector('.empty-msg')) {
      feed.innerHTML = '<div class="empty-msg">아직 방명록이 없어요 📟<br>첫 번째를 남겨보세요!</div>';
    }
    document.getElementById('cntbadge').textContent = '';
    totalCount = 0;
    return;
  }

  // Group replies under parents
  const top = comments.filter(c => !c.parent_id);
  top.sort((a, b) => b.id - a.id); // newest first
  const replyMap = {};
  comments.filter(c => c.parent_id).forEach(c => {
    (replyMap[c.parent_id] = replyMap[c.parent_id] || []).push(c);
  });

  const newIdSet = new Set(top.map(c => c.id));

  // Remove cards that no longer exist
  [...feed.querySelectorAll('.card[id^="card-"]')].forEach(el => {
    if (!newIdSet.has(parseInt(el.id.replace('card-', '')))) el.remove();
  });

  // Patch existing cards; insert new ones at correct position
  let anchor = null;
  top.forEach((c, i) => {
    const existing = document.getElementById(`card-${c.id}`);
    if (existing) {
      // Patch like count only (no DOM teardown)
      const cnt = existing.querySelector('.like-cnt');
      if (cnt && cnt.textContent != c.likes) cnt.textContent = c.likes;
      // Patch replies if changed
      const repliesEl = document.getElementById(`replies-${c.id}`);
      if (repliesEl) {
        const newHtml = (replyMap[c.id] || []).map(replyCardHtml).join('');
        if (repliesEl.innerHTML !== newHtml) repliesEl.innerHTML = newHtml;
      }
      anchor = existing;
    } else {
      const el = makeCard(c, replyMap[c.id]);
      if (i === 0) feed.prepend(el);
      else if (anchor) anchor.after(el);
      else feed.append(el);
      anchor = el;
    }
  });

  totalCount = top.length;
  document.getElementById('cntbadge').textContent = `(${totalCount}개)`;
  feed.scrollTop = prevScroll;
}

// ── Load comments (full rebuild) ───────────────────────
async function loadComments() {
  try {
    const data = await fetch('/the_signal/api/comments').then(r => r.json());
    if (Array.isArray(data)) buildFeed(data);
  } catch { /* silent */ }
}

// ── Submit loading dialog — modem terminal ─────────────
function showSubmitLoading() {
  const overlay = document.createElement('div');
  overlay.className = 'submit-overlay';
  overlay.innerHTML = `
    <div class="submit-dlg">
      <div class="tbar">
        <div class="tbar-l">
          <span class="tbar-icon">📡</span>
          <span class="tbar-txt" id="sdlg-title">방명록 등록 중...</span>
        </div>
      </div>
      <div class="submit-terminal" id="sdlg-term">
        <span class="st-cursor" id="sdlg-cursor">█</span>
      </div>
      <div class="submit-bar-row">
        <div class="submit-bar-wrap"><div class="submit-bar" id="sdlg-bar"></div></div>
        <span class="submit-pct" id="sdlg-pct">0%</span>
      </div>
      <div class="submit-human" id="sdlg-human">잠시만 기다려주세요...</div>
    </div>`;
  document.body.appendChild(overlay);

  const term   = document.getElementById('sdlg-term');
  const cursor = document.getElementById('sdlg-cursor');
  const bar    = document.getElementById('sdlg-bar');
  const pct    = document.getElementById('sdlg-pct');
  const human  = document.getElementById('sdlg-human');

  const timers = [];
  let alive = true;

  function addLine(text, cls, delay) {
    const t = setTimeout(() => {
      if (!alive) return;
      const ln = document.createElement('span');
      ln.className = 'st-line' + (cls ? ' ' + cls : '');
      ln.textContent = text;
      term.insertBefore(ln, cursor);
    }, delay);
    timers.push(t);
  }

  // Modem handshake sequence
  addLine('> ATH0',                              '',       0);
  addLine('OK',                                  'st-ok',  240);
  addLine('> ATDT signal.korea.ac.kr',          '',       490);
  addLine('CARRIER 56600',                       'st-dim', 760);
  addLine('CONNECT 56600/ARQ/V90/LAPM/V42BIS',  'st-conn',900);
  addLine('',                                    '',       1060);
  addLine('> POST /api/guestbook HTTP/1.1',     '',       1060);
  addLine('> Host: signal.korea.ac.kr',         'st-dim', 1200);
  addLine('> Content-Type: application/json',   'st-dim', 1220);
  addLine('> Uploading payload... 1337 bytes',  '',       1370);

  // Progress bar
  [[16,240],[38,620],[62,960],[83,1340]].forEach(([p,d]) => {
    const t = setTimeout(() => {
      if (!alive) return;
      bar.style.width = p + '%';
      pct.textContent = p + '%';
    }, d);
    timers.push(t);
  });

  // Human-readable status
  [[0,'서버에 연결하고 있어요...'],
   [900,'연결됨! 데이터를 전송 중...'],
   [1060,'방명록을 등록하고 있어요 📡']
  ].forEach(([d, msg]) => {
    const t = setTimeout(() => { if (alive) human.textContent = msg; }, d);
    timers.push(t);
  });

  return { overlay, bar, pct, human, term, cursor,
    stop() { alive = false; timers.forEach(clearTimeout); } };
}

function finishSubmitLoading(ld, success) {
  ld.stop();

  const ln = document.createElement('span');
  ln.className = 'st-line ' + (success ? 'st-ok' : 'st-err');
  ln.textContent = success
    ? '> HTTP/1.1 200 OK — UPLOAD COMPLETE'
    : '> HTTP/1.1 500 ERROR — CONNECTION FAILED';
  ld.term.insertBefore(ln, ld.cursor);
  ld.cursor.style.animation = 'none';
  ld.cursor.style.opacity   = '0';

  ld.bar.style.width = '100%';
  ld.pct.textContent = '100%';
  ld.bar.classList.add(success ? 'done' : 'error');
  if (!success) {
    ld.pct.style.color = '#e03838';
    ld.pct.style.textShadow = '0 0 4px rgba(224,56,56,.4)';
  }

  const title = document.getElementById('sdlg-title');
  if (title) title.textContent = success ? '등록 완료!' : '오류 발생';
  ld.human.textContent = success
    ? '등록 완료! 방명록이 올라갔어요 🎉'
    : '전송에 실패했어요 ⚠️';

  setTimeout(() => ld.overlay.remove(), 1300);
}

// ── Submit comment ─────────────────────────────────────
async function submitComment() {
  const name    = document.getElementById('name').value.trim();
  const message = document.getElementById('msg').value.trim();
  if (!name)    { showDlg('알림', '이름을 입력해주세요', 'ℹ️'); return; }
  if (!message) { showDlg('알림', '메시지를 입력해주세요', 'ℹ️'); return; }

  const btn = document.getElementById('sendbtn');
  btn.disabled = true;
  const ld = showSubmitLoading();
  const t0 = Date.now();

  try {
    const res = await fetch('/the_signal/api/comments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, message }),
    });
    const data = await res.json();
    // Ensure dialog shows for at least 1.4s so animation is visible
    await new Promise(r => setTimeout(r, Math.max(0, 1400 - (Date.now() - t0))));

    if (data.success) {
      document.getElementById('msg').value = '';
      document.getElementById('msgcnt').textContent = '0';
      finishSubmitLoading(ld, true);
      setStatus('gb-status', '전송 완료!', 3000);
      setTimeout(loadComments, 1200);
    } else {
      finishSubmitLoading(ld, false);
      setTimeout(() => showDlg('오류', data.error || '전송에 실패했습니다', '⚠️'), 1200);
    }
  } catch {
    finishSubmitLoading(ld, false);
    setTimeout(() => showDlg('오류', '서버에 연결할 수 없습니다', '⚠️'), 1200);
  } finally {
    btn.disabled = false;
  }
}

// ── Like toggle ────────────────────────────────────────
async function toggleLike(id, btnEl) {
  try {
    const res  = await fetch(`/the_signal/api/comments/${id}/like`, { method: 'POST' });
    const data = await res.json();
    if (data.liked !== undefined) {
      btnEl.className = `like-btn${data.liked ? ' liked' : ''}`;
      btnEl.innerHTML = `${data.liked ? '♥' : '♡'}&nbsp;<span class="like-cnt">${data.likes}</span>`;
    }
  } catch { /* silent */ }
}

// ── Reply loading dialog — pager LCD style ─────────────
function showReplyLoading() {
  const overlay = document.createElement('div');
  overlay.className = 'reply-overlay';
  overlay.innerHTML = `
    <div class="reply-dlg">
      <div class="tbar">
        <div class="tbar-l">
          <span class="tbar-icon">📟</span>
          <span class="tbar-name" id="rdlg-title">답글 전송 중...</span>
        </div>
      </div>
      <div class="reply-terminal" id="rdlg-term">
        <span class="rt-cursor" id="rdlg-cursor">█</span>
      </div>
      <div class="reply-bar-row">
        <div class="reply-bar-wrap"><div class="reply-bar" id="rdlg-bar"></div></div>
        <span class="reply-pct" id="rdlg-pct">0%</span>
      </div>
      <div class="reply-human" id="rdlg-human">잠시만 기다려주세요...</div>
    </div>`;
  document.body.appendChild(overlay);

  const term   = document.getElementById('rdlg-term');
  const cursor = document.getElementById('rdlg-cursor');
  const bar    = document.getElementById('rdlg-bar');
  const pct    = document.getElementById('rdlg-pct');
  const human  = document.getElementById('rdlg-human');

  const timers = [];
  let alive = true;

  function addLine(text, cls, delay) {
    const t = setTimeout(() => {
      if (!alive) return;
      const ln = document.createElement('span');
      ln.className = 'rt-line' + (cls ? ' ' + cls : '');
      ln.textContent = text;
      term.insertBefore(ln, cursor);
    }, delay);
    timers.push(t);
  }

  // Pager beep sequence
  addLine('> REPLY.CMD /send',     '',      0);
  addLine('SIGNAL OK  ▌▌▌',        'rt-ok', 200);
  addLine('> TRANSMITTING...',     '',      420);
  addLine('> payload: 1 reply',    'rt-dim',600);

  // Progress
  [[22,160],[55,380],[80,600]].forEach(([p,d]) => {
    const t = setTimeout(() => {
      if (!alive) return;
      bar.style.width = p + '%';
      pct.textContent = p + '%';
    }, d);
    timers.push(t);
  });

  [[0,'신호를 확인하고 있어요...'],
   [420,'답글을 전송하고 있어요 📟']
  ].forEach(([d, msg]) => {
    const t = setTimeout(() => { if (alive) human.textContent = msg; }, d);
    timers.push(t);
  });

  return { overlay, bar, pct, human, term, cursor,
    stop() { alive = false; timers.forEach(clearTimeout); } };
}

function finishReplyLoading(ld, success) {
  ld.stop();

  const ln = document.createElement('span');
  ln.className = 'rt-line ' + (success ? 'rt-ok' : 'rt-err');
  ln.textContent = success ? '> DELIVERED ✓' : '> FAILED ✗';
  ld.term.insertBefore(ln, ld.cursor);
  ld.cursor.style.animation = 'none';
  ld.cursor.style.opacity   = '0';

  ld.bar.style.width = '100%';
  ld.pct.textContent = '100%';
  ld.bar.classList.add(success ? 'done' : 'error');

  const title = document.getElementById('rdlg-title');
  if (title) title.textContent = success ? '전송 완료!' : '오류 발생';
  ld.human.textContent = success ? '답글이 등록되었어요 ✓' : '전송에 실패했어요 ⚠️';

  setTimeout(() => ld.overlay.remove(), 1000);
}

// ── Reply form ─────────────────────────────────────────
function toggleReplyForm(id) {
  const form = document.getElementById(`rf-${id}`);
  if (!form) return;
  form.classList.toggle('hidden');
  if (!form.classList.contains('hidden')) {
    const ni = document.getElementById(`rn-${id}`);
    if (ni) ni.focus();
  }
}

async function submitReply(parentId) {
  const nameEl = document.getElementById(`rn-${parentId}`);
  const msgEl  = document.getElementById(`rm-${parentId}`);
  const name    = nameEl ? nameEl.value.trim() : '';
  const message = msgEl  ? msgEl.value.trim()  : '';

  if (!name)    { showDlg('알림', '이름을 입력해주세요', 'ℹ️'); return; }
  if (!message) { showDlg('알림', '답글 내용을 입력해주세요', 'ℹ️'); return; }

  const ld = showReplyLoading();
  const t0 = Date.now();

  try {
    const res = await fetch('/the_signal/api/comments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, message, parent_id: parentId }),
    });
    const data = await res.json();
    await new Promise(r => setTimeout(r, Math.max(0, 800 - (Date.now() - t0))));

    if (data.success) {
      finishReplyLoading(ld, true);
      if (nameEl) nameEl.value = '';
      if (msgEl)  msgEl.value  = '';
      toggleReplyForm(parentId);
      setTimeout(loadComments, 900);
    } else {
      finishReplyLoading(ld, false);
      setTimeout(() => showDlg('오류', data.error || '등록에 실패했습니다', '⚠️'), 900);
    }
  } catch {
    finishReplyLoading(ld, false);
    setTimeout(() => showDlg('오류', '서버에 연결할 수 없습니다', '⚠️'), 900);
  }
}

// ── Pager codes (populated by renderCodeSelector) ─────

function updatePreview() {
  const code = document.getElementById('bcode').value.trim();
  const lcd  = document.getElementById('lcd-body');
  if (!code) {
    lcd.className = 'lcd-preview dim';
    lcd.textContent = '코드를 입력하면 미리보기 표시';
    return;
  }
  const m = CODES[code];
  lcd.className = 'lcd-preview';
  lcd.textContent = m ? `[${code}] → ${m}` : `[${code}] → 비밀 코드 🔒`;
}

function selectCode(code) {
  document.getElementById('bcode').value = code;
  updatePreview();
  document.getElementById('bcode').focus();
  toast(`코드 ${code} 선택됨`, 'ok');
}

// ── Send beep ──────────────────────────────────────────
async function sendBeep() {
  const email   = document.getElementById('bemail').value.trim();
  const code    = document.getElementById('bcode').value.trim();
  const sender  = document.getElementById('bsender').value.trim() || 'THE SIGNAL';
  const comment = document.getElementById('bcomment').value.trim();

  if (!email)  { showDlg('알림', '이메일 주소를 입력해주세요', 'ℹ️'); return; }
  if (!code)   { showDlg('알림', '삐삐 코드를 입력해주세요', 'ℹ️'); return; }

  const btn = document.getElementById('beepbtn');
  btn.textContent = 'SENDING...'; btn.disabled = true;
  setStatus('beep-status', '발송 중...');

  try {
    const res = await fetch('/the_signal/api/send-beep', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, code, sender_name: sender, comment }),
    });
    const data = await res.json();
    if (data.success) {
      toast('삐삐가 발송되었어요! 📟', 'ok');
      ['bemail','bcode','bsender','bcomment'].forEach(id => {
        document.getElementById(id).value = '';
      });
      updatePreview();
      setStatus('beep-status', '발송 완료!', 3000);
    } else {
      showDlg('오류', data.error || '발송에 실패했습니다', '⚠️');
      setStatus('beep-status', '발송 실패');
    }
  } catch { showDlg('오류', '서버에 연결할 수 없습니다', '⚠️'); }
  finally { btn.textContent = 'SEND BEEP ▶'; btn.disabled = false; }
}

// ── Tab switch ─────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('on'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('on'));
  document.querySelector(`.tab[data-tab="${name}"]`).classList.add('on');
  document.getElementById(`pane-${name}`).classList.add('on');
}

// ── Toast ──────────────────────────────────────────────
let toastT;
function toast(msg, type = '') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast show${type ? ' ' + type : ''}`;
  clearTimeout(toastT);
  toastT = setTimeout(() => el.classList.remove('show'), 3200);
}

// ── Status line ────────────────────────────────────────
const stTimers = {};
function setStatus(id, msg, reset = 0) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  if (reset) {
    clearTimeout(stTimers[id]);
    stTimers[id] = setTimeout(() => {
      el.textContent = id === 'gb-status' ? '준비됨' : '삐삐 발송 준비됨';
    }, reset);
  }
}

// ── Dialog ─────────────────────────────────────────────
function showDlg(title, msg, icon = 'ℹ️') {
  document.getElementById('dlg-title').textContent   = title;
  document.getElementById('dlg-msg').textContent     = msg;
  document.getElementById('dlg-icon').textContent    = icon;
  document.getElementById('dlg-icon-tb').textContent = icon;
  document.getElementById('dlg-overlay').classList.remove('hidden');
}
function closeDlg() {
  document.getElementById('dlg-overlay').classList.add('hidden');
}
document.getElementById('dlg-overlay').addEventListener('click', e => {
  if (e.target === e.currentTarget) closeDlg();
});

// Ctrl+Enter to post
document.getElementById('msg').addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === 'Enter') submitComment();
});

// ── Boot ───────────────────────────────────────────────
async function init() {
  try {
    const [topicsRes, codesRes] = await Promise.all([
      fetch('/the_signal/api/topics'),
      fetch('/the_signal/api/pager-codes'),
    ]);
    TOPICS = await topicsRes.json();
    const codes = await codesRes.json();
    renderCodeSelector(codes);
  } catch { /* silent — fallback to empty */ }
  updateTopicDisplay();
}

init();
loadComments();
setInterval(loadComments, 10000);