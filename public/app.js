import { createEditor, getText, setText, insert, exec } from "./editor.js";
import * as S from "./streak.js";

const $ = (s, el = document) => el.querySelector(s);
const h = (tag, attrs = {}, ...kids) => {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "html") el.innerHTML = v;
    else if (k === "class") el.className = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of kids.flat()) if (c != null && c !== false) el.append(c.nodeType ? c : document.createTextNode(String(c)));
  return el;
};
const app = $("#app");
const ymd = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const todayStr = () => ymd(new Date());
const addDays = (s, n) => { const [y, m, d] = s.split("-").map(Number); return ymd(new Date(y, m - 1, d + n)); };
function toast(msg, ms = 2200) { const t = $("#toast"); t.textContent = msg; t.hidden = false; clearTimeout(toast._t); toast._t = setTimeout(() => (t.hidden = true), ms); }
const linkBtn = (href, label, cls = "btn") => h("a", { class: `${cls} linkbtn`, href }, label);

// ---------- storage (every access guarded: private mode / quota errors must never break the app) ----------
const lsGet = (k) => { try { return localStorage.getItem(k); } catch { return null; } };
let saveWarned = false;
const lsSet = (k, v) => { try { localStorage.setItem(k, v); return true; } catch (e) { if (!saveWarned) { saveWarned = true; toast("⚠️ Couldn't save on this device (storage full or private mode). Export your progress from Settings.", 6000); } return false; } };

// ---------- progress ----------
const KEY = "ppr.progress.v1";
const blank = () => ({ version: 1, completed: {}, ex: {}, quiz: {}, last: null, days: [], created: todayStr(), review: null, rcode: {}, game: null });
let P = (() => { try { return Object.assign(blank(), JSON.parse(lsGet(KEY)) || {}); } catch { return blank(); } })();
const save = () => lsSet(KEY, JSON.stringify(P));
function touchDay() { const d = todayStr(); if (!P.days.includes(d)) { P.days.push(d); P.days.sort(); } save(); }


// ---------- theme ----------
const applyTheme = () => { const t = lsGet("ppr.theme") || "dark"; const eff = t === "system" ? (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark") : t; document.documentElement.dataset.theme = eff; const m = $('meta[name="theme-color"]'); if (m) m.content = eff === "light" ? "#f6f8fa" : "#0f1419"; };
applyTheme();
matchMedia("(prefers-color-scheme: light)").addEventListener?.("change", applyTheme);

// ---------- data ----------
let DATA, LESSONS = [], BYID = {};
async function loadData() {
  DATA = await (await fetch("lessons.json")).json();
  let n = 0;
  for (const u of DATA.units) for (const l of u.lessons) { l.unit = u; l.num = ++n; LESSONS.push(l); BYID[l.id] = l; }
}
const todayLesson = () => LESSONS.find(l => !P.completed[l.id]) || LESSONS[LESSONS.length - 1];

// ---------- Python worker (timeout, Stop, Retry) ----------
const RUN_LIMIT_MS = 20000;
let worker, workerReady = false, pyState = "loading", seq = 0; const pending = new Map();
const pyListeners = new Set();
function setPy(s) { pyState = s; pyListeners.forEach(f => f(s)); }
function failPending(msg) { for (const p of pending.values()) { clearTimeout(p.timer); p.resolve({ stdout: "", error: msg, results: [] }); } pending.clear(); }
function startWorker() {
  workerReady = false; setPy("loading");
  try { worker = new Worker("worker.js", { type: "module" }); } catch (e) { console.error(e); setPy("error"); return; }
  worker.onmessage = (e) => {
    const m = e.data;
    if (m.type === "ready") { workerReady = true; setPy("ready"); return; }
    if (m.type === "fatal") { console.error(m.error); setPy("error"); failPending("Python failed to load. Tap “Retry” next to the Python status."); return; }
    const p = pending.get(m.id); if (!p) return;
    if (m.type === "status") { p.onStatus && p.onStatus(m.status); if (m.status === "running") p.arm(); return; }
    if (m.type === "result") { clearTimeout(p.timer); pending.delete(m.id); p.resolve(m.result); }
  };
  worker.onerror = (e) => { console.error(e); setPy("error"); failPending("Python failed to load. Tap “Retry” next to the Python status."); };
}
function restartWorker(msg) { try { worker && worker.terminate(); } catch {} failPending(msg); startWorker(); }
const stopPy = () => restartWorker("⏹ Stopped. Python restarted; your code is still in the editor.");
function runPy(code, tests = null, setup = "", onStatus) {
  if (pyState === "error") return Promise.resolve({ stdout: "", error: "Python isn't loaded. Tap “Retry” next to the Python status.", results: [] });
  return new Promise((resolve) => {
    const id = ++seq;
    const p = { resolve, onStatus, timer: null, arm() { this.timer = setTimeout(() => restartWorker(`Stopped after ${RUN_LIMIT_MS / 1000} seconds. Is there an infinite loop (e.g. a while loop that never ends) or a very slow algorithm? Python restarted.`), RUN_LIMIT_MS); } };
    pending.set(id, p);
    worker.postMessage({ id, code, tests, setup });
  });
}

// ---------- symbol toolbar (iOS keyboard hides these) ----------
let activeView = null, blurTimer, offlineLoop = false;
const KEYS = [["⇥", () => insert(activeView, "    ")], ["⇤", () => exec(activeView, "indentLess")], ["(", "("], [")", ")"], ["[", "["], ["]", "]"], [":", ":"], ["=", "="], ['"', '"'], ["'", "'"], ["{", "{"], ["}", "}"], [",", ","], [".", "."], ["_", "_"], ["+", "+"], ["-", "-"], ["*", "*"], ["/", "/"], ["<", "<"], [">", ">"], ["#", "# "], ["f\"", () => insert(activeView, 'f""', 1)], ["←", () => exec(activeView, "left")], ["→", () => exec(activeView, "right")], ["↑", () => exec(activeView, "up")], ["↓", () => exec(activeView, "down")], ["undo", () => exec(activeView, "undo"), "w"], ["done", () => activeView && activeView.contentDOM.blur(), "w"]];
function buildBar() {
  const bar = $("#kbdbar");
  for (const [label, act, cls] of KEYS) {
    const b = h("button", { type: "button", class: cls || null, "aria-label": label }, label);
    // pointerdown + preventDefault keeps focus (and the iOS keyboard) in the editor
    b.addEventListener("pointerdown", (e) => { e.preventDefault(); if (!activeView) return; typeof act === "string" ? insert(activeView, act) : act(); });
    b.addEventListener("mousedown", e => e.preventDefault());
    bar.append(b);
  }
  const place = () => { const vv = window.visualViewport; if (!vv) return; const off = window.innerHeight - vv.height - vv.offsetTop; bar.style.transform = `translateY(${-Math.max(0, off)}px)`; };
  window.visualViewport && (visualViewport.addEventListener("resize", place), visualViewport.addEventListener("scroll", place));
}
const editorHooks = { onFocus: (v) => { clearTimeout(blurTimer); activeView = v; $("#kbdbar").hidden = false; }, onBlur: () => { blurTimer = setTimeout(() => { $("#kbdbar").hidden = true; activeView = null; }, 150); } };

// ---------- offline status ----------
let offlineReady = false;
async function checkOffline() {
  if (offlineLoop || offlineReady) return; offlineLoop = true;
  try { return await checkOffline2(); } finally { offlineLoop = false; }
}
async function checkOffline2() {
  const badge = $("#offlineBadge");
  if (!("serviceWorker" in navigator) || !window.PRECACHE || !window.caches) { badge.textContent = "Offline not supported"; return; }
  const all = [...PRECACHE.app, ...PRECACHE.pyodide];
  let have = 0;
  for (const u of all) if (await caches.match(new URL(u, location.href).href)) have++;
  const ctrl = !!navigator.serviceWorker.controller;
  if (have === all.length && ctrl) { offlineReady = true; badge.textContent = "✓ Ready for offline"; badge.className = "badge ready"; return true; }
  badge.textContent = `Saving for offline ${Math.round(100 * have / all.length)}%`; badge.className = "badge progress";
  setTimeout(checkOffline, 1500); return false;
}
$("#offlineBadge").addEventListener("click", () => toast(offlineReady ? `Saved on this device: ${PRECACHE.app.length + PRECACHE.pyodide.length} files, ~${Math.round(PRECACHE.bytes / 1e6)} MB (Python, numpy, pandas and all lessons). Works in airplane mode.` : "Keep the app open online until this says “Ready for offline”.", 4500));

// ---------- spaced review ----------
// Each exercise gets a Leitner box after it is passed. Box -> days until it's due again.
const INTERVALS = [1, 1, 3, 7, 14, 30, 60];
const REVIEW_SIZE = 8, REVIEW_QUIZ = 4;
const exKey = (l, i) => `${l.id}:${i}`;
function exOf(key) { const [lid, i] = key.split(":"); const l = BYID[lid]; return l && l.exercises[+i] ? { l, e: l.exercises[+i], i: +i } : null; }
function quizOf(key) { const [lid, i] = key.split(":"); const l = BYID[lid]; return l && l.quiz[+i] ? { l, q: l.quiz[+i], i: +i } : null; }
function dueDate(s) { if (s.due) return s.due; if (s.passedOn) return addDays(s.passedOn, 1); return null; }
function schedulePass(s, firstTry) {
  const today = todayStr();
  if (s.box == null) s.box = s.sawSol ? 0 : (firstTry ? 2 : 1); else s.box = Math.min(s.box + 1, INTERVALS.length - 1);
  s.due = addDays(today, INTERVALS[s.box]);
}
function scheduleLapse(s) { s.box = 1; s.due = addDays(todayStr(), 1); s.lapses = (s.lapses || 0) + 1; }
function reviewCandidates() {
  const today = todayStr();
  const missed = [], due = [];
  for (const [key, s] of Object.entries(P.ex)) {
    if (!exOf(key) || !s || !s.attempts) continue;
    if (!s.passed) missed.push([key, -s.attempts]);
    else { const d = dueDate(s); if (d && d <= today) due.push([key, d]); }
  }
  missed.sort((a, b) => a[1] - b[1]); due.sort((a, b) => (a[1] < b[1] ? -1 : 1));
  const quiz = Object.entries(P.quiz).filter(([k, v]) => { const x = quizOf(k); return x && v !== x.q.answer; }).map(([k]) => k);
  return { missed: missed.map(x => x[0]), due: due.map(x => x[0]), quiz };
}
function todaysReview() {
  const today = todayStr();
  if (!P.review || P.review.date !== today) {
    const c = reviewCandidates();
    const keys = [...c.missed, ...c.due.filter(k => !c.missed.includes(k))].slice(0, REVIEW_SIZE);
    P.review = { date: today, keys, quiz: c.quiz.slice(0, REVIEW_QUIZ), done: {}, extra: 0 };
    save();
  } else {
    // Same day: anything newly missed joins today's set right away.
    const c = reviewCandidates(); let changed = false;
    for (const k of c.missed) if (!P.review.keys.includes(k)) { P.review.keys.push(k); changed = true; }
    for (const k of c.quiz) if (!P.review.quiz.includes(k)) { P.review.quiz.push(k); changed = true; }
    if (changed) save();
  }
  return P.review;
}
// An item stays in today's list if it's done today, or still missed/due (e.g. not if it was fixed in the lesson meanwhile).
function exActive(r, k) { if (r.done[k]) return true; const s = P.ex[k]; if (!s || !exOf(k)) return false; if (!s.passed) return true; const d = dueDate(s); return (d && d <= todayStr()) || (r.extraKeys || []).includes(k); }
function quizActive(r, k) { if (r.done["q:" + k]) return true; const x = quizOf(k); return !!x && P.quiz[k] !== x.q.answer; }
function reviewCounts() { const r = todaysReview(); const items = [...r.keys.filter(k => exActive(r, k)), ...r.quiz.filter(k => quizActive(r, k)).map(k => "q:" + k)]; return { total: items.length, done: items.filter(k => r.done[k]).length }; }
function addExtraPractice(n = 5) {
  const r = todaysReview();
  const pool = Object.entries(P.ex).filter(([k, s]) => s && s.passed && exOf(k) && !r.keys.includes(k)).map(([k]) => k);
  for (let i = pool.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [pool[i], pool[j]] = [pool[j], pool[i]]; }
  const add = pool.slice(0, n); r.keys.push(...add); r.extraKeys = [...(r.extraKeys || []), ...add]; save(); return add.length;
}

// ---------- building blocks ----------
function lessonRow(l) {
  const cls = P.completed[l.id] ? "done" : (l === todayLesson() ? "today" : "");
  return h("li", { class: cls }, h("a", { href: `#/l/${l.id}` }, h("span", { class: "n" }, P.completed[l.id] ? "✓" : l.num),
    h("span", { class: "tt" }, l.title, h("br"), h("span", { class: "small muted" }, `~${l.minutes} min · ${l.exercises.length} ex`), " ",
      l.kind === "checkpoint" ? h("span", { class: "tag cp" }, "🏁 checkpoint") : null,
      l.kind === "final" ? h("span", { class: "tag final" }, "🎓 final") : null,
      l.work_html ? h("span", { class: "tag work" }, "💼 take to work") : null,
      l.timed ? h("span", { class: "tag timed" }, `⏱ ${l.timed} min`) : null)));
}
function pyBadge() {
  const el = h("span", { class: "pybadge small muted" });
  const f = (s) => el.replaceChildren(...(s === "ready" ? ["🐍 Python ready"] : s === "error"
    ? [h("span", { class: "bad" }, "⚠️ Python failed to load "), h("button", { class: "btn mini", type: "button", onclick: () => restartWorker("Restarting Python…") }, "↻ Retry")]
    : [h("span", { class: "spin", "aria-hidden": "true" }), " Starting Python…"]));
  f(pyState); pyListeners.add(f); return el;
}
const stars = (d) => h("span", { class: `diff d${d}`, title: ["", "Warm-up", "Core", "Stretch"][d] || "", "aria-label": `difficulty ${d} of 3` }, "★".repeat(d), h("span", { class: "off" }, "★".repeat(3 - d)));

function codeBlock(code, { key, tests, setup, onResult, allowCheck, store } = {}) {
  const bucket = () => (store === "review" ? (P.rcode = P.rcode || {}) : P.ex);
  const wrap = h("div", { class: "editor" }); const out = h("pre", { class: "out" }); const status = h("span", { class: "status" });
  const saved = key && bucket()[key] && bucket()[key].code;
  const view = createEditor(wrap, saved || code, { ...editorHooks, onChange: key ? (txt) => { const b = bucket(); b[key] = Object.assign(b[key] || {}, { code: txt }); save(); } : null });
  const results = h("ul", { class: "results" });
  let running = false;
  async function go(check) {
    if (running) return; running = true;
    touchDay();
    out.className = "out"; out.textContent = ""; results.replaceChildren();
    runBtn.disabled = true; if (checkBtn) checkBtn.disabled = true; stopBtn.hidden = false;
    status.textContent = workerReady ? "running…" : "waiting for Python…";
    const r = await runPy(getText(view), check ? tests : null, setup, (s) => status.textContent = s === "loading-packages" ? "loading pandas/numpy…" : "running…");
    running = false; status.textContent = ""; stopBtn.hidden = true; runBtn.disabled = false; if (checkBtn) checkBtn.disabled = false;
    out.textContent = r.stdout || (check || r.error ? "" : "(no output: use print() to see values)");
    if (r.error) { out.textContent += (r.stdout ? "\n" : "") + r.error; out.className = "out err"; }
    if (check) for (const t of r.results) results.append(h("li", { class: t.ok ? "pass" : "fail" }, (t.ok ? "✅ " : "❌ ") + t.name, t.msg ? h("div", { class: "m" }, t.msg) : null));
    onResult && onResult(r, check);
  }
  const runBtn = h("button", { class: "btn", type: "button", onclick: () => go(false) }, "▶ Run");
  const checkBtn = allowCheck ? h("button", { class: "btn primary", type: "button", onclick: () => go(true) }, "✓ Check") : null;
  const stopBtn = h("button", { class: "btn stop", type: "button", hidden: true, onclick: stopPy }, "⏹ Stop");
  const btns = h("div", { class: "row" }, runBtn, checkBtn, stopBtn,
    h("button", { class: "btn ghost icon", type: "button", "aria-label": "Reset code", title: "Reset code", onclick: () => { if (confirm("Reset this code to the original?")) setText(view, code); } }, "↺"), status);
  return { el: h("div", {}, wrap, btns, out, results), view, results };
}

function quizBlock(qz, key, { fresh = false, onAnswer } = {}) {
  const box = h("div", { class: "card quiz" }, h("div", { class: "prose", html: qz.q_html }), qz.code ? h("pre", { class: "out" }, qz.code) : null);
  const why = h("div", { class: "hint", hidden: true });
  const buttons = qz.options.map((o, i) => h("button", { class: "btn opt", type: "button", onclick: () => pick(i) }, o));
  function pick(i, silent) {
    buttons.forEach((b, j) => { b.classList.toggle("right", j === qz.answer); b.classList.toggle("wrong", j === i && i !== qz.answer); });
    why.hidden = false; why.textContent = (i === qz.answer ? "✅ Correct. " : "❌ Not quite. ") + qz.why;
    if (!silent) { P.quiz[key] = i; touchDay(); onAnswer && onAnswer(i === qz.answer); }
  }
  box.append(...buttons, why);
  if (!fresh && P.quiz[key] != null) pick(P.quiz[key], true);
  return box;
}

function fmt(s) { const m = Math.floor(Math.abs(s) / 60), ss = Math.abs(s) % 60; return `${s < 0 ? "+" : ""}${m}:${String(ss).padStart(2, "0")}`; }
function timerRow(minutes, label) {
  const el = h("span", { class: "timer" }, fmt(minutes * 60)); let t0 = null, iv = null;
  const tb = h("button", { class: "btn", type: "button", onclick: () => { if (iv) { clearInterval(iv); iv = null; tb.textContent = "⏱ Restart timer"; return; } t0 = Date.now(); tb.textContent = "⏹ Stop timer"; const tick = () => { if (!el.isConnected) { clearInterval(iv); iv = null; return; } const left = minutes * 60 - Math.floor((Date.now() - t0) / 1000); el.textContent = fmt(left); el.classList.toggle("over", left < 0); }; iv = setInterval(tick, 500); tick(); } }, "⏱ Start timer");
  return h("div", { class: "card timerbox" }, h("div", { class: "row" }, tb, el), h("div", { class: "small muted" }, label));
}

function exerciseBlock(l, e, i, onPass, { review = false, onReview } = {}) {
  const key = exKey(l, i); const st = () => (P.ex[key] = P.ex[key] || { attempts: 0, passed: false });
  let tries = 0, failedNow = false, sawNow = false, reported = false;
  const card = h("div", { class: `card exercise${review ? " review" : ""}` });
  const banner = h("div"); const hintsBox = h("div"); let hintIdx = 0;
  const solBtn = h("button", { class: "btn ghost", type: "button", onclick: showSol }, "Show solution");
  const hintBtn = h("button", { class: "btn ghost", type: "button", onclick: () => { if (hintIdx < e.hints.length) hintsBox.append(h("div", { class: "hint" }, `💡 ${e.hints[hintIdx++]}`)); if (hintIdx >= e.hints.length) hintBtn.disabled = true; } }, "💡 Hint");
  if (!e.hints.length) hintBtn.disabled = true;
  const used = () => (review ? tries : st().attempts);
  const updSol = () => { const ok = review ? tries >= 2 : (st().passed || st().attempts >= 2); const n = Math.max(0, 2 - used()); solBtn.disabled = !ok; solBtn.textContent = ok ? "Show solution" : `Solution (after ${n} more ${n === 1 ? "try" : "tries"})`; };
  const solBox = h("div");
  function showSol() {
    sawNow = true; const s = st(); if (!s.passed) s.sawSol = true; save();
    solBox.replaceChildren(h("div", { class: "small muted" }, "Reference solution. Compare with yours, then close it and retype from memory. It'll come back in Review."), h("pre", { class: "out" }, e.solution));
  }
  const title = h("h3", {}, `${review ? "" : `Exercise ${i + 1}: `}${e.title} `, stars(e.difficulty || 1), st().passed && !review ? h("span", { class: "okmark" }, " ✅") : null);
  const cb = codeBlock(review ? e.starter : e.starter, { key, tests: e.tests, setup: e.setup, allowCheck: true, store: review ? "review" : null, onResult: (r, check) => {
    if (!check) return;
    const s = st(); s.attempts++; tries++; let gained = 0;
    const ok = !r.error && r.results.length && r.results.every(t => t.ok);
    if (review) {
      if (ok && !reported) {
        reported = true;
        if (!s.passed) { s.passed = true; s.passedOn = todayStr(); }
        if (failedNow || sawNow) scheduleLapse(s); else schedulePass(s, false);
        s.lastReview = todayStr(); s.reviews = (s.reviews || 0) + 1;
        if (P.rcode) delete P.rcode[key];
        gained = award(`rv:${todayStr()}:${key}`, S.XP.reviewEx);
        onReview && onReview();
      } else if (!ok) failedNow = true;
    } else if (ok && !s.passed) { s.passed = true; s.passedOn = todayStr(); schedulePass(s, s.attempts === 1 && !s.sawSol); gained = award(`ex:${key}`, S.exerciseXP(e.difficulty, s.sawSol)); }
    banner.replaceChildren(h("div", { class: `banner ${ok ? "ok" : "bad"}` }, ok ? `✅ All ${r.results.length} checks passed!${review ? (failedNow || sawNow ? " It'll come back tomorrow." : ` Next review in ${INTERVALS[s.box]} days.`) : ""}${gained ? `  +${gained} XP` : ""}` : `${r.results.filter(t => t.ok).length}/${r.results.length} checks passed. Read the ❌ feedback, fix, and check again.`));
    save(); updSol(); if (ok && !review) onPass && onPass();
  } });
  card.append(...[title, h("div", { class: "prose", html: e.prompt_html }), cb.el, banner, hintsBox, h("div", { class: "row" }, hintBtn, solBtn), solBox]);
  updSol();
  return card;
}

// ---------- streaks, XP, badges ----------
let dayNow = todayStr();
function badgeCtx() {
  let clean3 = 0;
  for (const [k, s] of Object.entries(P.ex)) { if (!s || !s.passed || s.sawSol) continue; const x = exOf(k); if (x && x.e.difficulty === 3) clean3++; }
  return { units: DATA.units.map(u => ({ id: u.id, title: u.title, lessonIds: u.lessons.map(l => l.id) })), completed: P.completed, clean3, finalUnitId: "final" };
}
function ensureGame(silent) {
  if (!P.game || typeof P.game !== "object") P.game = S.migrate(P, LESSONS, todayStr()); // one-time, loss-free migration
  else P.game = S.normalize(P.game);
  S.reconcile(P.game, todayStr());
  const b = S.evaluateBadges(P.game, badgeCtx(), todayStr()); // badges already deserved by past progress: award quietly
  if (!silent) b.forEach(x => queueToast(`🏅 Badge unlocked: ${x.def.title}`));
}
// ---------- tangible rewards ----------
const rewardQ = [];
const money = (n) => n == null ? "" : n.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: n % 1 ? 2 : 0 });
const rwItem = (id) => P.game.rewards.items.find(x => x.id === id);
const rwDate = (d) => d === "earlier" ? "earlier" : d;
const unlockMsg = (r) => `Reward unlocked: ${r.name} - ask Chief of Staff to line it up`;
function claim(id) { if (S.claimReward(P.game, id, todayStr())) { save(); toast(`✓ Claimed: ${rwItem(id).name}`); } }
function showRewardModal() {
  if ($(".rw-modal")) return;
  const id = rewardQ.shift(); if (!id) return; const r = rwItem(id); if (!r) return;
  if (!reducedMotion()) confetti();
  const close = () => { m.remove(); if (rewardQ.length) setTimeout(showRewardModal, 300); else if (!location.hash || location.hash === "#/" || location.hash.startsWith("#/rewards")) route(); };
  const m = h("div", { class: "rw-modal", role: "dialog", "aria-modal": "true", "aria-labelledby": "rw-title" },
    h("div", { class: "rw-box" },
      h("div", { class: "rw-icon", "aria-hidden": "true" }, r.icon || "🎁"),
      h("div", { class: "small muted" }, `🔥 ${r.days}-day streak`),
      h("h2", { id: "rw-title" }, unlockMsg(r)),
      r.note ? h("p", { class: "small muted" }, r.note) : null,
      r.price != null ? h("p", { class: "small" }, `Budget: ${money(r.price)}`) : null,
      h("div", { class: "row" }, h("button", { class: "btn ok", onclick: () => { claim(id); close(); } }, "Mark claimed"), h("button", { class: "btn", onclick: close }, "Later"))));
  document.body.append(m); m.querySelector(".btn.ok").focus();
}
function rewardsCard() {
  const g = P.game, R = g.rewards, nx = S.nextReward(g, todayStr());
  const ready = R.items.filter(r => S.rewardState(g, r.id) === "unlocked");
  const claimed = R.items.filter(r => R.claimed[r.id]).length;
  return h("section", { class: "card rewardscard" },
    h("div", { class: "row between" }, h("b", {}, "🎁 Rewards"), h("span", { class: "small muted" }, `${claimed}/${R.items.length} claimed`)),
    ...ready.map(r => h("div", { class: "rw-ready" },
      h("div", {}, h("b", {}, `${r.icon} ${unlockMsg(r)}`), h("div", { class: "small muted" }, `Unlocked ${rwDate(R.unlocked[r.id])} · ${r.days}-day streak`)),
      h("button", { class: "btn ok mini", onclick: () => { claim(r.id); route(); } }, "Mark claimed"))),
    nx ? h("div", { class: "rw-next" },
      h("div", { class: "rw-icon sm", "aria-hidden": "true" }, nx.item.icon),
      h("div", { class: "rw-main" },
        h("div", { class: "small muted" }, "Next reward"),
        h("div", { class: "rw-name" }, nx.item.name),
        h("div", { class: "small muted" }, nx.toGo ? `${nx.toGo} day${nx.toGo === 1 ? "" : "s"} to go · ${nx.current}/${nx.item.days}-day streak` : "Unlocks with today's goal"),
        h("div", { class: "bar rw" }, h("i", { style: `width:${(nx.pct * 100).toFixed(1)}%` })))) :
      h("div", { class: "small muted mt8" }, "All four rewards unlocked. Legendary."),
    linkBtn("#/rewards", "All rewards →", "btn block mt8"));
}
function viewRewards(editId) {
  const g = P.game, R = g.rewards, cur = S.streakInfo(g, todayStr()).current;
  const row = (r) => {
    const st = S.rewardState(g, r.id);
    if (editId === r.id) {
      const f = (label, name, val, attrs = {}) => h("label", { class: "rw-field" }, h("span", { class: "small muted" }, label), h("input", { name, value: val ?? "", ...attrs }));
      const err = h("div", { class: "small bad", role: "alert" });
      const form = h("form", { class: "card rw-item editing", onsubmit: (ev) => { ev.preventDefault();
          const fd = new FormData(form); const res = S.editReward(g, r.id, { name: fd.get("name"), note: fd.get("note"), link: fd.get("link"), price: fd.get("price") });
          if (!res.ok) { err.textContent = res.error; return; } save(); toast("✓ Reward saved"); viewRewards(); } },
        h("div", { class: "small muted" }, `${r.icon} ${r.days}-day streak reward`),
        f("Name", "name", r.name, { required: true, maxlength: 80 }), f("Note (optional)", "note", r.note, { maxlength: 200 }),
        f("Link (optional)", "link", r.link, { type: "url", inputmode: "url", placeholder: "https://…" }),
        f("Price (optional)", "price", r.price ?? "", { inputmode: "decimal", placeholder: "e.g. 150" }), err,
        h("div", { class: "row" }, h("button", { class: "btn primary", type: "submit" }, "Save"), h("button", { class: "btn", type: "button", onclick: () => viewRewards() }, "Cancel"),
          h("button", { class: "btn ghost", type: "button", onclick: () => { S.resetReward(g, r.id); save(); viewRewards(); } }, "Default")));
      return form;
    }
    return h("div", { class: `card rw-item ${st}` },
      h("div", { class: "rw-head" }, h("div", { class: "rw-icon sm", "aria-hidden": "true" }, st === "locked" ? "🔒" : r.icon),
        h("div", { class: "rw-main" }, h("div", { class: "small muted" }, `${r.days}-day streak`), h("div", { class: "rw-name" }, r.name),
          r.note ? h("div", { class: "small muted" }, r.note) : null,
          h("div", { class: "small" }, r.price != null ? money(r.price) : null, r.price != null && r.link ? " · " : null, r.link ? h("a", { href: r.link, target: "_blank", rel: "noopener" }, "link ↗") : null)),
        h("span", { class: `pill st-${st}` }, st === "claimed" ? "Claimed" : st === "unlocked" ? "Unlocked" : "Locked")),
      st === "locked" ? h("div", { class: "rw-prog" }, h("div", { class: "bar rw" }, h("i", { style: `width:${(100 * Math.min(1, cur / r.days)).toFixed(1)}%` })), h("span", { class: "small muted" }, `${Math.min(cur, r.days)}/${r.days} · ${Math.max(0, r.days - cur)} to go`)) : null,
      st === "unlocked" ? h("div", { class: "small ok" }, `Unlocked ${rwDate(R.unlocked[r.id])} - ask Chief of Staff to line it up`) : null,
      st === "claimed" ? h("div", { class: "small ok" }, `✓ Claimed ${R.claimed[r.id]}`) : null,
      h("div", { class: "row mt8" },
        st === "unlocked" ? h("button", { class: "btn ok", onclick: () => { claim(r.id); viewRewards(); } }, "Mark claimed") : null,
        st === "claimed" ? h("button", { class: "btn ghost mini", onclick: () => { S.unclaimReward(g, r.id); save(); viewRewards(); } }, "Undo claim") : null,
        h("button", { class: "btn mini", onclick: () => viewRewards(r.id) }, "Edit")));
  };
  app.replaceChildren(
    h("nav", { class: "crumbs small muted" }, h("a", { href: "#/" }, "← Home")),
    h("h1", {}, "🎁 Rewards"),
    h("p", { class: "small muted" }, `Real rewards for your streak. Each unlocks once when your current streak reaches its milestone (freezes keep a streak alive) and stays unlocked even if the streak later breaks. Current streak: ${cur} day${cur === 1 ? "" : "s"}.`),
    ...R.items.map(row));
  if (editId) app.querySelector("input[name=name]")?.focus();
}
function checkDayRollover() {
  const t = todayStr(); if (t === dayNow) return;
  dayNow = t; S.reconcile(P.game, t); save();
  if (!location.hash || location.hash === "#/" || location.hash.startsWith("#/badges") || location.hash.startsWith("#/rewards")) route();
}
function handle(events) {
  const g = P.game;
  for (const e of events) {
    if (e.type === "goal" && g.goalCelebrated !== todayStr()) { g.goalCelebrated = todayStr(); celebrate(e.streak, !events.some(x => x.type === "reward")); }
    if (e.type === "freezeEarned") queueToast(`❄️ Streak freeze earned (${e.freezes}/${S.FREEZE_CAP}) for your ${e.streak}-day streak`);
    if (e.type === "levelUp") queueToast(`Level up: ${e.title}`, 2000);
    if (e.type === "reward") rewardQ.push(e.id);
  }
  if (rewardQ.length) setTimeout(showRewardModal, 900);
  for (const b of S.evaluateBadges(g, badgeCtx(), todayStr())) queueToast(`🏅 Badge unlocked: ${b.def.icon} ${b.def.title}`, 3200);
  save();
}
function award(key, amount) { const ev = S.addXP(P.game, key, amount, todayStr()); handle(ev); return ev.length ? amount : 0; }
function activity(kind) { handle(S.recordActivity(P.game, todayStr(), kind)); }

const toastQ = []; let toastBusy = false;
function queueToast(msg, ms = 2600) {
  toastQ.push([msg, ms]); if (toastBusy) return;
  const next = () => { const it = toastQ.shift(); if (!it) { toastBusy = false; return; } toastBusy = true; toast(it[0], it[1]); setTimeout(next, it[1] + 250); };
  next();
}
const reducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
function celebrate(streakN, burst = true) {
  queueToast(`🔥 Daily goal met: ${streakN}-day streak!`, 3000);
  if (burst && !reducedMotion()) confetti(); // skipped when a reward unlock brings its own celebration
}
function confetti() {
  const c = h("canvas", { class: "confetti", "aria-hidden": "true" }); document.body.append(c);
  const dpr = Math.min(2, devicePixelRatio || 1), W = innerWidth, H = innerHeight;
  c.width = W * dpr; c.height = H * dpr; const ctx = c.getContext("2d"); ctx.scale(dpr, dpr);
  const cs = getComputedStyle(document.documentElement);
  const colors = ["--accent", "--ok", "--warn", "--work", "--bad"].map(v => cs.getPropertyValue(v).trim() || "#58a6ff");
  const parts = Array.from({ length: 110 }, () => ({ x: W / 2 + (Math.random() - .5) * 80, y: H * .32, vx: (Math.random() - .5) * 9, vy: -Math.random() * 9 - 3, r: Math.random() * Math.PI, vr: (Math.random() - .5) * .3, w: 6 + Math.random() * 5, h: 3 + Math.random() * 4, col: colors[Math.floor(Math.random() * colors.length)] }));
  const t0 = performance.now(), DUR = 2200;
  (function frame(now) {
    const t = now - t0; ctx.clearRect(0, 0, W, H); ctx.globalAlpha = Math.max(0, 1 - Math.max(0, t - DUR * .6) / (DUR * .4));
    for (const p of parts) { p.vy += .28; p.vx *= .99; p.x += p.vx; p.y += p.vy; p.r += p.vr; ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.fillStyle = p.col; ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h); ctx.restore(); }
    if (t < DUR) requestAnimationFrame(frame); else c.remove();
  })(t0);
}

function homeNotices() {
  const g = P.game, out = [];
  for (const n of g.notices.splice(0)) { // shown once
    if (n.type === "freezeUsed") out.push(h("div", { class: "card notice freeze" }, h("b", {}, `❄️ Streak freeze used`), h("div", { class: "small" }, `You missed ${n.days.length === 1 ? "a day" : `${n.days.length} days`} (${n.days.join(", ")}), so a freeze kept your ${n.streak}-day streak alive. ${n.left} left.`)));
    if (n.type === "reset") out.push(h("div", { class: "card notice reset" }, h("b", {}, "Streak reset"), h("div", { class: "small" }, `Your ${n.was}-day streak ended. Your best is still saved. One lesson or today's review starts a new one.`)));
  }
  if (out.length) save();
  const risk = S.atRisk(g, todayStr(), new Date().getHours());
  if (risk) out.unshift(h("div", { class: "card notice risk" }, h("b", {}, `⚠️ Your ${risk.streak}-day streak is at risk`),
    h("div", { class: "small" }, `Finish a lesson or today's review before midnight.${risk.freezes ? ` (If you miss today, 1 of your ${risk.freezes} freeze${risk.freezes > 1 ? "s" : ""} will cover it.)` : ""}`),
    h("div", { class: "row mt8" }, linkBtn(`#/l/${todayLesson().id}`, "Today's lesson", "btn primary"), linkBtn("#/review", "Review"))));
  return out;
}

function heatmap(g, today, weeks = 20) {
  const start = S.addDays(today, -S.weekday(today) - 7 * (weeks - 1));
  const grid = h("div", { class: "hm-grid", role: "img", "aria-label": `Activity over the last ${weeks} weeks` });
  const months = h("div", { class: "hm-months" }); let lastM = null;
  const lvl = (d) => { const x = g.xpByDay[d] || 0; if (!g.active[d]) return x ? 1 : 0; return x >= 300 ? 4 : x >= 150 ? 3 : x >= 60 ? 2 : 1; };
  for (let w = 0; w < weeks; w++) {
    const monday = S.addDays(start, 7 * w); const m = +monday.slice(5, 7);
    months.append(h("span", {}, m !== lastM ? ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][m - 1] : "")); lastM = m;
    for (let dI = 0; dI < 7; dI++) {
      const d = S.addDays(monday, dI);
      if (d > today) { grid.append(h("i", { class: "hm future" })); continue; }
      const cls = g.frozen[d] ? "frozen" : g.active[d] ? `l${lvl(d)}` : "l0";
      grid.append(h("i", { class: `hm ${cls}${d === today ? " today" : ""}`, title: `${d}${g.active[d] ? ` · active · ${g.xpByDay[d] || 0} XP` : g.frozen[d] ? " · freeze used" : ""}` }));
    }
  }
  const nActive = Object.keys(g.active).length;
  return h("div", { class: "heatmap" }, months, grid,
    h("div", { class: "hm-legend small muted" }, h("span", {}, `${nActive} active day${nActive === 1 ? "" : "s"}`), h("span", { class: "hm-key" }, "Less ", ...[0, 1, 2, 3, 4].map(i => h("i", { class: `hm l${i}` })), " More ", h("i", { class: "hm frozen" }), " freeze")));
}

function streakCard() {
  const g = P.game, t = todayStr(), s = S.streakInfo(g, t), lv = S.levelFor(g.xp);
  const defs = S.badgeDefs(badgeCtx()); const earned = defs.filter(d => g.badges[d.id]).length;
  return h("section", { class: `card streakcard${s.todayDone ? " done" : ""}${s.current ? " lit" : ""}` },
    h("div", { class: "sc-top" },
      h("div", { class: "flame", "aria-hidden": "true" }, "🔥"),
      h("div", { class: "sc-num" }, h("b", {}, s.current), h("span", {}, "day streak")),
      h("div", { class: "sc-side" }, h("div", {}, h("span", { class: "muted" }, "Best "), h("b", {}, s.best)), h("div", { title: "Streak freezes: earn 1 per 7-day streak (max 2). Each covers one missed day automatically." }, "❄️ ", h("b", {}, g.freezes), h("span", { class: "muted" }, `/${S.FREEZE_CAP}`)))),
    h("div", { class: `goal${s.todayDone ? " ok" : ""}` }, s.todayDone ? "✓ Today's goal done. See you tomorrow!" : "○ Today's goal: finish 1 lesson or today's Review"),
    heatmap(g, t),
    h("div", { class: "row between level-line" }, h("span", { class: "small muted" }, `${g.xp.toLocaleString()} XP · level: ${lv.title}`), h("a", { class: "small", href: "#/badges" }, `Badges ${earned}/${defs.length} →`)));
}

function viewBadges() {
  const g = P.game, lv = S.levelFor(g.xp), s = S.streakInfo(g, todayStr());
  const defs = S.badgeDefs(badgeCtx()); const earned = defs.filter(d => g.badges[d.id]).length;
  const tile = (d) => { const [have, need] = d.progress(g); const got = g.badges[d.id];
    return h("div", { class: `badge-tile${got ? " earned" : " locked"}` },
      h("div", { class: "bi", "aria-hidden": "true" }, got ? d.icon : "🔒"), h("div", { class: "bt" }, d.title), h("div", { class: "bd small muted" }, d.desc),
      got ? h("div", { class: "small ok" }, `Earned ${got}`) : h("div", { class: "bp" }, h("div", { class: "bar" }, h("i", { style: `width:${(100 * have / need).toFixed(0)}%` })), h("span", { class: "small muted" }, `${have}/${need}`))); };
  const groups = [...new Set(defs.map(d => d.group))];
  app.replaceChildren(
    h("nav", { class: "crumbs small muted" }, h("a", { href: "#/" }, "← Home")),
    h("h1", {}, "🏅 Badges"),
    h("div", { class: "card row between small" }, h("span", {}, `🔥 ${s.current}-day streak · best ${s.best}`), h("span", {}, `❄️ ${g.freezes}/${S.FREEZE_CAP} freezes`), h("b", {}, `${earned}/${defs.length} earned`)),
    linkBtn("#/rewards", "🎁 See your real rewards →", "btn block"),
    ...groups.flatMap(gr => [h("div", { class: "sec-title" }, gr), h("div", { class: "badge-grid" }, defs.filter(d => d.group === gr).map(tile))]),
    h("details", { class: "card levelcard small muted" },
      h("summary", {}, `XP ${g.xp.toLocaleString()} · level: ${lv.title}${lv.next ? ` (${(lv.next - g.xp).toLocaleString()} XP to ${lv.nextTitle})` : ""}`),
      h("ol", { class: "ladder small" }, S.LEVELS.map(([x, t], i) => h("li", { class: i < lv.index ? "past" : i === lv.index ? "now" : "" }, h("span", {}, t), h("span", { class: "muted" }, `${x.toLocaleString()} XP`)))),
      h("p", {}, `How XP works: lesson ${S.XP.lesson} · checkpoint ${S.XP.checkpoint} · final ${S.XP.final} · exercise ${S.XP.exPerStar} per ★ (+${S.XP.noPeek} if you didn't view the solution) · review exercise ${S.XP.reviewEx} · review question ${S.XP.reviewQuiz} · full review set +${S.XP.reviewSet}.`)),
  );
}

// ---------- views ----------
function viewHome() {
  const t = todayLesson(); const doneToday = Object.values(P.completed).includes(todayStr());
  const last = P.last && BYID[P.last] && !P.completed[P.last] && P.last !== t.id ? BYID[P.last] : null;
  const nDone = Object.keys(P.completed).filter(k => BYID[k]).length; const nEx = Object.values(P.ex).filter(e => e && e.passed).length;
  const totalEx = LESSONS.reduce((a, l) => a + l.exercises.length, 0);
  const rc = reviewCounts(); const left = rc.total - rc.done;
  app.replaceChildren(
    ...homeNotices(),
    h("section", { class: "card hero" },
      h("div", { class: "kicker" }, doneToday ? "Today's lesson is done 🎉 Keep going?" : "Today's lesson"),
      h("h1", {}, `${t.num}. ${t.title}`),
      h("p", { class: "muted small" }, `${t.unit.title} · ~${t.minutes} min · ${t.exercises.length} exercises`),
      h("p", { class: "small use-line" }, "💼 ", t.use),
      linkBtn(`#/l/${t.id}`, P.last === t.id ? "Continue →" : "Start →", "btn primary block"),
      last ? linkBtn(`#/l/${last.id}`, `Continue where you left off: ${last.num}. ${last.title}`, "btn block mt8") : null,
      h("div", { class: "overall" }, h("div", { class: "bar" }, h("i", { style: `width:${(100 * nDone / LESSONS.length).toFixed(1)}%` })), h("span", { class: "small muted" }, `Course ${Math.round(100 * nDone / LESSONS.length)}% · `, pyBadge()))),
    h("a", { class: `card reviewcard${left ? " due" : ""}`, href: "#/review" },
      h("div", { class: "rv-l" }, h("b", {}, "🔁 Daily review"),
        h("span", { class: "small muted" }, rc.total ? (left ? `${left} to do today: missed exercises + spaced repeats` : "All done for today ✓ Tap for extra practice") : "Exercises come back 1, 3, 7, 14 and 30 days after you pass them")),
      h("span", { class: "pill" }, left ? String(left) : "✓")),
    rewardsCard(),
    streakCard(),
    h("div", { class: "sec-title" }, "Curriculum ", h("span", { class: "legend" }, `${nDone}/${LESSONS.length} lessons · ${nEx}/${totalEx} exercises · ${P.days.length} days studied`)),
    ...DATA.units.map((u, i) => {
      const done = u.lessons.filter(l => P.completed[l.id]).length;
      const open = u.lessons.includes(t);
      const label = u.id === "final" ? "🎓 Final" : `Unit ${i + 1}`;
      return h("details", { class: "card unit", open: open || null },
        h("summary", {}, h("span", { class: "t" }, `${label} · ${u.title}`), h("span", { class: "small muted" }, `${done}/${u.lessons.length} lessons · ${u.blurb}`), h("div", { class: "bar" }, h("i", { style: `width:${100 * done / u.lessons.length}%` }))),
        h("ul", { class: "lessons" }, u.lessons.map(lessonRow)));
    }),
    h("div", { class: "row mt12" }, linkBtn("#/projects", "💼 Take-it-to-work projects"), linkBtn("#/settings", "⚙️ Progress & settings")),
  );
}

function viewLesson(id) {
  const l = BYID[id]; if (!l) return viewHome();
  P.last = id; save();
  const idx = LESSONS.indexOf(l); const prev = LESSONS[idx - 1], next = LESSONS[idx + 1];
  const completeBtn = h("button", { class: "btn block", type: "button" });
  const updComplete = () => { const d = !!P.completed[id]; completeBtn.textContent = d ? "✓ Lesson complete" : "Mark lesson complete"; completeBtn.className = d ? "btn ok block" : "btn primary block"; };
  const scoreEl = h("div");
  const updScore = () => {
    if (!l.kind) return;
    const st = l.exercises.map((_, i) => P.ex[exKey(l, i)] || {});
    const passed = st.filter(s => s.passed).length, clean = st.filter(s => s.passed && !s.sawSol).length;
    const qs = l.quiz.filter((q, i) => P.quiz[`${l.id}:${i}`] === q.answer).length;
    scoreEl.replaceChildren(h("div", { class: `card score ${passed === l.exercises.length ? "pass" : ""}` },
      h("b", {}, l.kind === "final" ? "🎓 Final assessment score" : "🏁 Checkpoint score"),
      h("div", { class: "scoregrid" },
        h("div", {}, h("b", {}, `${passed}/${l.exercises.length}`), h("span", {}, "exercises passed")),
        h("div", {}, h("b", {}, `${clean}/${l.exercises.length}`), h("span", {}, "without solution")),
        h("div", {}, h("b", {}, `${qs}/${l.quiz.length}`), h("span", {}, "questions right"))),
      passed === l.exercises.length ? h("div", { class: "small ok" }, l.kind === "final" ? "Passed. Congratulations, you've completed the course! 🎉" : "Checkpoint passed ✓") : h("div", { class: "small muted" }, "Pass every exercise to clear this. Misses go into your daily Review.")));
  };
  const complete = (auto) => { if (!P.completed[id]) { P.completed[id] = todayStr(); touchDay(); updComplete(); queueToast(auto ? "🎉 All exercises passed: lesson complete!" : "Lesson complete ✓");
    award(`lesson:${id}`, l.kind === "final" ? S.XP.final : l.kind === "checkpoint" ? S.XP.checkpoint : S.XP.lesson); activity("lesson"); } };
  completeBtn.onclick = () => { if (P.completed[id]) { if (confirm("Mark as not complete?")) { delete P.completed[id]; save(); updComplete(); } } else complete(false); };
  updComplete(); updScore();
  const onPass = () => { updScore(); if (l.exercises.every((_, i) => P.ex[exKey(l, i)] && P.ex[exKey(l, i)].passed)) complete(true); };
  const unitNo = DATA.units.indexOf(l.unit) + 1;
  app.replaceChildren(...[
    h("nav", { class: "crumbs small muted" }, h("a", { href: "#/" }, "← Home"), ` · ${l.unit.id === "final" ? "Final" : `Unit ${unitNo}`}: ${l.unit.title}`),
    h("h1", {}, `${l.num}. ${l.title}`),
    h("div", { class: "row small muted meta" }, `⏱ ~${l.minutes} min`, h("span", {}, `${l.exercises.length} exercises`), l.timed ? h("span", { class: "tag timed" }, `Timed: ${l.timed} min`) : null, pyBadge()),
    l.kind === "checkpoint" ? h("div", { class: "card cpbanner" }, h("b", {}, "🏁 Unit checkpoint"), h("div", { class: "small" }, "Mixed questions and exercises covering this unit. Try without hints first.")) : null,
    l.kind === "final" ? h("div", { class: "card cpbanner final" }, h("b", {}, "🎓 Final assessment"), h("div", { class: "small" }, "Eight exercises across the whole course, 60 minutes. Start the timer below when you're ready.")) : null,
    scoreEl,
    h("div", { class: "card use" }, h("b", {}, "💼 At work: "), l.use),
    h("div", { class: "card prose", html: l.body_html }),
    l.talk_html ? h("div", { class: "card prose talk", html: "<b>🗣 Talk it through</b>" + l.talk_html }) : null,
    l.examples.length ? h("div", { class: "sec-title" }, "Worked examples: edit & run") : null,
    ...l.examples.map(e => { const c = typeof e === "string" ? { code: e } : e; return h("div", { class: "card" }, c.title ? h("h3", {}, c.title) : null, codeBlock(c.code).el); }),
    l.quiz.length ? h("div", { class: "sec-title" }, l.kind ? "Questions" : "Quick check") : null,
    ...l.quiz.map((qz, i) => quizBlock(qz, `${l.id}:${i}`, { onAnswer: updScore })),
    h("div", { class: "sec-title" }, "Exercises: auto-checked ", h("span", { class: "legend" }, "★ warm-up · ★★ core · ★★★ stretch")),
    l.timed ? timerRow(l.timed, l.kind === "final" ? "Exam clock: 60 minutes for all eight exercises." : `Aim for ~${l.timed} min per problem. Say your plan out loud before typing.`) : null,
    ...l.exercises.map((e, i) => exerciseBlock(l, e, i, onPass)),
    l.work_html ? h("div", { class: "card prose work", html: l.work_html }) : null,
    completeBtn,
    h("div", { class: "navrow" }, prev ? linkBtn(`#/l/${prev.id}`, "← Prev") : null, next ? linkBtn(`#/l/${next.id}`, "Next →") : null),
  ].filter(Boolean));
}

function viewReview() {
  const r = todaysReview();
  const c = reviewCounts();
  const prog = h("div", { class: "bar big" }, h("i", { style: `width:${c.total ? (100 * c.done / c.total).toFixed(1) : 0}%` }));
  const counter = h("span", { class: "small muted" }, `${c.done}/${c.total} done today`);
  const refresh = () => { const cc = reviewCounts(); prog.firstChild.style.width = `${cc.total ? (100 * cc.done / cc.total).toFixed(1) : 0}%`; counter.textContent = `${cc.done}/${cc.total} done today`; if (cc.total && cc.done === cc.total) { doneBox.hidden = false; award(`rvset:${todayStr()}`, S.XP.reviewSet); activity("review"); } };
  const passedAny = Object.values(P.ex).some(s => s && s.passed);
  const extraBtn = () => h("button", { class: "btn", type: "button", onclick: () => { const n = addExtraPractice(5); if (!n) toast("Pass some exercises first, then they'll show up here."); viewReview(); } }, "➕ 5 more for extra practice");
  const doneBox = h("div", { class: "card banner-card", hidden: !(c.total && c.done === c.total) }, h("b", {}, "🎉 Review complete for today."), h("p", { class: "small muted" }, "Spaced repetition works best a little every day. Come back tomorrow for the next set."), passedAny ? extraBtn() : null);
  const items = [];
  for (const key of r.keys) {
    if (r.done[key] || !exActive(r, key)) continue;
    const x = exOf(key); if (!x) continue;
    const s = P.ex[key] || {};
    const why = !s.passed ? "Missed" : `Passed ${s.lastReview || s.passedOn || "earlier"} · box ${s.box ?? 1}`;
    items.push(h("div", { class: "rv-item" }, h("div", { class: "ctx small muted" }, h("span", { class: `tag ${!s.passed ? "missed" : "spaced"}` }, !s.passed ? "↺ missed" : "⏳ spaced repeat"), ` ${why} · from `, h("a", { href: `#/l/${x.l.id}` }, `${x.l.num}. ${x.l.title}`)),
      exerciseBlock(x.l, x.e, x.i, null, { review: true, onReview: () => { r.done[key] = true; save(); refresh(); } })));
  }
  for (const k of r.quiz) {
    if (r.done["q:" + k] || !quizActive(r, k)) continue;
    const x = quizOf(k); if (!x) continue;
    items.push(h("div", { class: "rv-item" }, h("div", { class: "ctx small muted" }, h("span", { class: "tag missed" }, "? question"), " from ", h("a", { href: `#/l/${x.l.id}` }, `${x.l.num}. ${x.l.title}`)),
      quizBlock(x.q, k, { fresh: true, onAnswer: (ok) => { if (ok) { r.done["q:" + k] = true; award(`rvq:${todayStr()}:${k}`, S.XP.reviewQuiz); save(); refresh(); } } })));
  }
  const doneList = [...r.keys.filter(k => r.done[k]).map(k => exOf(k)).filter(Boolean).map(x => h("li", {}, "✓ ", x.e.title, h("span", { class: "muted" }, ` · ${x.l.title}`))),
    ...r.quiz.filter(k => r.done["q:" + k]).map(k => quizOf(k)).filter(Boolean).map(x => h("li", {}, "✓ Question · ", h("span", { class: "muted" }, x.l.title)))];
  app.replaceChildren(...[
    h("nav", { class: "crumbs small muted" }, h("a", { href: "#/" }, "← Home")),
    h("h1", {}, "🔁 Daily review"),
    h("p", { class: "small muted" }, "Today's set mixes exercises you missed with ones you passed days ago (spaced 1 → 3 → 7 → 14 → 30 → 60 days). Solve them from a blank starter; a clean pass pushes the next review further out, a miss brings it back tomorrow."),
    h("div", { class: "card" }, h("div", { class: "row between" }, h("b", {}, "Today"), counter), prog),
    c.total === 0 ? h("div", { class: "card banner-card" }, h("b", {}, "Nothing due yet."), h("p", { class: "small muted" }, "Complete lesson exercises and they'll show up here: missed ones right away, passed ones after 1, 3, 7, 14 and 30 days."), passedAny ? extraBtn() : linkBtn(`#/l/${todayLesson().id}`, "Go to today's lesson →", "btn primary block")) : null,
    doneBox,
    ...items,
    doneList.length ? h("div", { class: "sec-title" }, "Done today") : null,
    doneList.length ? h("ul", { class: "card donelist small" }, doneList) : null,
  ].filter(Boolean));
}

function viewProjects() {
  app.replaceChildren(h("nav", { class: "crumbs small" }, h("a", { href: "#/" }, "← Home")), h("h1", {}, "💼 Take-it-to-work projects"),
    h("p", { class: "muted" }, "Mini-projects to adapt with real (sanitized) data at a prime broker or FCM. Each builds on its unit."),
    ...LESSONS.filter(l => l.work_html).map(l => h("div", { class: "card prose work" }, h("div", { class: "small muted" }, `Lesson ${l.num} · ${l.unit.title}`), h("div", { html: l.work_html }), h("a", { href: `#/l/${l.id}` }, "Open lesson →"))));
}

let swReg = null;
function viewSettings() {
  const ta = h("textarea", { class: "io", placeholder: "Paste exported progress JSON here to import" });
  const theme = lsGet("ppr.theme") || "dark";
  const seg = h("div", { class: "seg", role: "group", "aria-label": "Theme" }, ...["dark", "light", "system"].map(t => h("button", { class: `btn ${t === theme ? "on" : ""}`, type: "button", onclick: () => { lsSet("ppr.theme", t); applyTheme(); viewSettings(); } }, t[0].toUpperCase() + t.slice(1))));
  const boxes = [0, 0, 0, 0, 0, 0, 0]; let missed = 0;
  for (const s of Object.values(P.ex)) { if (!s || !s.attempts) continue; if (!s.passed) missed++; else boxes[Math.min(s.box ?? 1, 6)]++; }
  app.replaceChildren(h("nav", { class: "crumbs small" }, h("a", { href: "#/" }, "← Home")), h("h1", {}, "Progress & settings"),
    h("div", { class: "card" }, h("h3", {}, "Theme"), seg),
    h("div", { class: "card" }, h("h3", {}, "Memory strength"), h("p", { class: "small muted" }, `Missed: ${missed} · learning (≤3 days): ${boxes[0] + boxes[1] + boxes[2]} · solid (7–14 days): ${boxes[3] + boxes[4]} · mastered (30+ days): ${boxes[5] + boxes[6]}`)),
    h("div", { class: "card" }, h("h3", {}, "Export progress"), h("p", { class: "small muted" }, "Progress lives on this device only (localStorage). The export includes lessons, exercises, review schedule, streak, rewards (including your edits and claim dates), XP and badges."),
      h("div", { class: "row" },
        h("button", { class: "btn", type: "button", onclick: () => { const blob = new Blob([JSON.stringify(P, null, 1)], { type: "application/json" }); const a = h("a", { href: URL.createObjectURL(blob), download: `pyrisk-progress-${todayStr()}.json` }); document.body.append(a); a.click(); a.remove(); } }, "⬇ Download JSON"),
        h("button", { class: "btn", type: "button", onclick: async () => { try { await navigator.clipboard.writeText(JSON.stringify(P)); toast("Copied progress JSON"); } catch { ta.value = JSON.stringify(P); toast("Copy it from the box below"); } } }, "📋 Copy"))),
    h("div", { class: "card" }, h("h3", {}, "Import progress"), ta,
      h("div", { class: "row mt8" },
        h("label", { class: "btn", style: "text-align:center" }, "📁 Choose file", h("input", { type: "file", accept: "application/json,.json", hidden: true, onchange: async (e) => { try { ta.value = await e.target.files[0].text(); } catch { toast("Couldn't read that file"); } } })),
        h("button", { class: "btn primary", type: "button", onclick: () => { try { const d = JSON.parse(ta.value); if (!d || typeof d.completed !== "object" || typeof d.ex !== "object") throw 0; P = Object.assign(blank(), d, { review: null }); ensureGame(true); save(); toast("Progress imported ✓"); location.hash = "#/"; } catch { toast("That doesn't look like a progress export"); } } }, "Import"))),
    h("div", { class: "card" }, h("h3", {}, "Offline & updates"), h("p", { class: "small muted" }, `After one online load, everything (Python ${PRECACHE.pyodideVersion}, numpy, pandas, all ${LESSONS.length} lessons) is stored on this device, about ${Math.round(PRECACHE.bytes / 1e6)} MB. On iPhone, add it to the Home Screen (Share → Add to Home Screen). iOS can still occasionally clear website data, so if the offline badge ever isn't green, open the app once online.`),
      h("div", { class: "row" },
        h("button", { class: "btn", type: "button", onclick: async () => { let r = false; try { r = navigator.storage && navigator.storage.persist ? await navigator.storage.persist() : false; } catch {} toast(r ? "Storage marked persistent ✓" : "Persistent storage not granted (normal in a Safari tab; install to the Home Screen)", 4000); } }, "Request persistent storage"),
        h("button", { class: "btn", type: "button", onclick: async () => { if (!swReg) return toast("Service worker not active"); try { await swReg.update(); toast(swReg.waiting || swReg.installing ? "Downloading update…" : "You're on the latest version"); } catch { toast("Couldn't check (offline?)"); } } }, "Check for updates"))),
    h("div", { class: "card" }, h("h3", {}, "Reset"), h("button", { class: "btn danger", type: "button", onclick: () => { if (confirm("Erase all progress on this device?")) { P = blank(); ensureGame(true); save(); toast("Progress reset"); location.hash = "#/"; } } }, "Reset all progress")),
    h("p", { class: "small muted" }, `Build ${PRECACHE.version}. Synthetic data only: for learning, not production risk.`));
}

function route() {
  $("#kbdbar").hidden = true; activeView = null; pyListeners.clear();
  const hash = location.hash || "#/"; const m = hash.match(/^#\/l\/(\w+)/);
  try {
    if (m) viewLesson(m[1]); else if (hash.startsWith("#/review")) viewReview(); else if (hash.startsWith("#/badges")) viewBadges(); else if (hash.startsWith("#/rewards")) viewRewards(); else if (hash.startsWith("#/projects")) viewProjects(); else if (hash.startsWith("#/settings")) viewSettings(); else viewHome();
  } catch (e) { console.error(e); app.replaceChildren(h("div", { class: "card" }, h("b", {}, "Something went wrong rendering this page."), h("pre", { class: "out err" }, String(e && e.stack || e)), linkBtn("#/", "← Home"))); }
  window.scrollTo(0, 0);
}

// ---------- service worker: install, offline status, safe update flow ----------
let updating = false, reloaded = false;
function showUpdate(reg) {
  const bar = $("#updatebar"); bar.hidden = false;
  bar.onclick = async () => {
    if (updating) return;
    bar.textContent = "Updating…"; updating = true;
    let w = reg.waiting;
    for (let i = 0; !w && i < 20; i++) { await new Promise(r => setTimeout(r, 250)); w = reg.waiting; }
    if (w) w.postMessage("skipWaiting"); else location.reload(); // user-initiated, so never a loop
  };
}
async function setupSW() {
  if (!("serviceWorker" in navigator)) { checkOffline(); return; }
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (updating && !reloaded) { reloaded = true; location.reload(); return; } // only reload when the user asked for the update
    checkOffline();
  });
  try {
    swReg = await navigator.serviceWorker.register("sw.js");
    if (swReg.waiting && navigator.serviceWorker.controller) showUpdate(swReg);
    const track = (nw) => nw && nw.addEventListener("statechange", () => { if (nw.state === "installed" && navigator.serviceWorker.controller) showUpdate(swReg); });
    if (swReg.installing && navigator.serviceWorker.controller) track(swReg.installing);
    swReg.addEventListener("updatefound", () => track(swReg.installing));
    document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible" && navigator.onLine) swReg.update().catch(() => {}); });
  } catch (e) { console.warn("SW registration failed", e); }
  checkOffline();
  try { if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {}); } catch {}
}

(async function init() {
  buildBar();
  startWorker();
  try { await loadData(); } catch (e) { app.replaceChildren(h("div", { class: "card" }, h("b", {}, "Couldn't load lessons."), h("p", { class: "small muted" }, "Connect once to download the course, then it works offline."), h("button", { class: "btn primary", type: "button", onclick: () => location.reload() }, "Retry"))); setupSW(); return; }
  ensureGame(true); save();
  window.addEventListener("hashchange", route);
  route();
  setupSW();
  // Local-midnight rollover: re-run the day check while the app stays open, and when it returns to the foreground.
  setInterval(checkDayRollover, 30000);
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") checkDayRollover(); });
})();
