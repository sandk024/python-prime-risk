// Streaks, freezes, XP, levels and badges. Pure logic: every function takes `today` ("YYYY-MM-DD", the
// device's LOCAL date) so it can be unit-tested with simulated dates (scripts/test-streak.mjs).
// State lives in progress.game (localStorage via the app).

export const LEVELS = [
  [0, "Intern"], [300, "Analyst"], [1000, "Associate"], [2500, "VP"],
  [5000, "Director"], [9000, "Managing Director"], [15000, "Head of Prime Risk"],
];
export const MILESTONES = [3, 7, 14, 30, 50, 60, 100];
export const FREEZE_CAP = 2, FREEZE_EVERY = 7;
export const XP = { lesson: 50, checkpoint: 100, final: 250, exPerStar: 10, noPeek: 10, reviewEx: 15, reviewQuiz: 5, reviewSet: 25 };

// ---- local-date helpers (calendar math in UTC so DST never adds/loses a day) ----
export const ymd = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const toUTC = (s) => { const [y, m, d] = s.split("-").map(Number); return Date.UTC(y, m - 1, d); };
const fromUTC = (t) => { const d = new Date(t); return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-${String(d.getUTCDate()).padStart(2, "0")}`; };
export const addDays = (s, n) => fromUTC(toUTC(s) + n * 86400000);
export const diffDays = (a, b) => Math.round((toUTC(a) - toUTC(b)) / 86400000); // a - b
export const weekday = (s) => (new Date(toUTC(s)).getUTCDay() + 6) % 7; // Mon=0 … Sun=6

export function newGame() {
  return { v: 1, active: {}, frozen: {}, freezes: 0, best: 0, xp: 0, xpByDay: {}, badges: {}, awarded: {},
    lastSeen: null, resetNotified: null, notices: [], goalCelebrated: null };
}
export function normalize(g) { return Object.assign(newGame(), g || {}); }

const covered = (g, d) => !!(g.active[d] || g.frozen[d]);

/** Current streak = active days in the unbroken chain ending today (or yesterday if today isn't done yet).
 *  Frozen days bridge the chain but don't add to the count. */
export function streakInfo(g, today) {
  const todayDone = !!g.active[today];
  let cur = todayDone ? today : addDays(today, -1);
  let n = 0, start = null, frozenUsed = 0;
  while (covered(g, cur)) { if (g.active[cur]) n++; else frozenUsed++; start = cur; cur = addDays(cur, -1); }
  if (n === 0) start = null;
  return { current: n, start, todayDone, frozenInChain: frozenUsed, best: Math.max(g.best || 0, n) };
}

function latestCoveredBefore(g, today) {
  let best = null;
  for (const d of [...Object.keys(g.active), ...Object.keys(g.frozen)]) if (d < today && (!best || d > best)) best = d;
  return best;
}

/** Run once when the app opens / the date changes. Spends freezes to cover missed days (one freeze per missed
 *  day, only if there are enough to cover the whole gap), otherwise records that the streak reset. */
export function reconcile(g, today) {
  const out = [];
  if (g.lastSeen && today <= g.lastSeen) return out; // same day, or device clock moved backwards: do nothing
  const last = latestCoveredBefore(g, today);
  if (last) {
    const missed = diffDays(today, last) - 1;
    const chain = streakInfo(g, addDays(last, 1)).current; // streak as it stood at `last`
    if (missed > 0 && chain > 0) {
      if (missed <= g.freezes) {
        const days = [];
        for (let i = 1; i <= missed; i++) { const d = addDays(last, i); g.frozen[d] = true; days.push(d); }
        g.freezes -= missed;
        out.push({ type: "freezeUsed", days, streak: chain, left: g.freezes });
      } else if (g.resetNotified !== last) {
        g.resetNotified = last;
        out.push({ type: "reset", was: chain });
      }
    }
  }
  g.lastSeen = today;
  g.notices.push(...out);
  return out;
}

/** Record a qualifying action ("lesson" or "review") on `today`. Returns events (goal met, milestones, freezes). */
export function recordActivity(g, today, kind) {
  const events = [];
  const was = !!g.active[today];
  const rec = g.active[today] || (g.active[today] = { lessons: 0, review: false });
  if (kind === "lesson") rec.lessons++;
  if (kind === "review") rec.review = true;
  delete g.frozen[today];
  if (was) return events; // the day already counted: no double counting
  const s = streakInfo(g, today);
  events.push({ type: "goal", streak: s.current });
  g.best = Math.max(g.best || 0, s.current);
  if (s.current > 0 && s.current % FREEZE_EVERY === 0) {
    const k = `freeze:${s.start}:${s.current}`;
    if (!g.awarded[k]) { g.awarded[k] = 1; if (g.freezes < FREEZE_CAP) { g.freezes++; events.push({ type: "freezeEarned", freezes: g.freezes, streak: s.current }); } }
  }
  return events;
}

export function levelFor(xp) {
  let i = 0; while (i + 1 < LEVELS.length && xp >= LEVELS[i + 1][0]) i++;
  const [lo, title] = LEVELS[i]; const next = LEVELS[i + 1];
  return { index: i, title, xp, floor: lo, next: next ? next[0] : null, nextTitle: next ? next[1] : null, pct: next ? (xp - lo) / (next[0] - lo) : 1 };
}

/** Award XP once per unique key. Returns events (xp, levelUp). */
export function addXP(g, key, amount, today) {
  if (!amount || g.awarded[key]) return [];
  const before = levelFor(g.xp).index;
  g.awarded[key] = 1; g.xp += amount; g.xpByDay[today] = (g.xpByDay[today] || 0) + amount;
  const after = levelFor(g.xp);
  const ev = [{ type: "xp", amount, key }];
  if (after.index > before) ev.push({ type: "levelUp", title: after.title, index: after.index });
  return ev;
}
export const exerciseXP = (difficulty, peeked) => XP.exPerStar * (difficulty || 1) + (peeked ? 0 : XP.noPeek);

// ---- badges ----
function perfectWeekProgress(g) {
  // best count of active days inside any Mon–Sun calendar week
  const weeks = {};
  for (const d of Object.keys(g.active)) { const monday = addDays(d, -weekday(d)); weeks[monday] = (weeks[monday] || 0) + 1; }
  return Math.max(0, ...Object.values(weeks));
}
/** ctx: { units:[{id,title,lessonIds}], completed:{lid:date}, clean3: n, finalId } */
export function badgeDefs(ctx) {
  const streakNames = { 3: "T+3 Settled", 7: "Weekly Margin Run", 14: "Two-Week Repo", 30: "Month-End Close", 50: "Half-Century", 60: "Sixty-Day Roll", 100: "Triple-Digit Streak" };
  const defs = MILESTONES.map(n => ({ id: `streak-${n}`, group: "Streaks", icon: n >= 50 ? "🏆" : n >= 14 ? "🔥" : "✨", title: streakNames[n], desc: `Reach a ${n}-day streak`, progress: (g) => [Math.min(g.best || 0, n), n] }));
  defs.push({ id: "perfect-week", group: "Streaks", icon: "📅", title: "Perfect Week", desc: "Study all 7 days of a Monday–Sunday week", progress: (g) => [Math.min(perfectWeekProgress(g), 7), 7] });
  defs.push({ id: "first-lesson", group: "Habits", icon: "🎯", title: "First Fill", desc: "Complete your first lesson", progress: () => [Math.min(Object.keys(ctx.completed).length, 1), 1] });
  const reviews = (g) => Object.values(g.active).filter(r => r.review).length;
  defs.push({ id: "review-1", group: "Habits", icon: "🔁", title: "Back-Office Ritual", desc: "Finish a daily Review set", progress: (g) => [Math.min(reviews(g), 1), 1] });
  defs.push({ id: "review-10", group: "Habits", icon: "🧾", title: "Recon Habit", desc: "Finish 10 daily Review sets", progress: (g) => [Math.min(reviews(g), 10), 10] });
  defs.push({ id: "clean-10", group: "Habits", icon: "🙈", title: "No Peeking", desc: "Pass 10 ★★★ exercises without viewing the solution", progress: () => [Math.min(ctx.clean3 || 0, 10), 10] });
  ctx.units.forEach((u, i) => {
    const isFinal = u.id === ctx.finalUnitId;
    defs.push({ id: `unit-${u.id}`, group: "Units", icon: isFinal ? "🎓" : "🏅", title: isFinal ? "Head of the Class" : `Unit ${i + 1} Complete`, desc: isFinal ? "Pass the final assessment" : u.title,
      progress: () => [u.lessonIds.filter(l => ctx.completed[l]).length, u.lessonIds.length] });
  });
  return defs;
}
/** Award any newly earned badges. Returns [{type:"badge", def}] */
export function evaluateBadges(g, ctx, today) {
  const out = [];
  for (const def of badgeDefs(ctx)) {
    if (g.badges[def.id]) continue;
    const [have, need] = def.progress(g);
    if (have >= need) { g.badges[def.id] = today; out.push({ type: "badge", def }); }
  }
  return out;
}

/** Build game state from pre-streak progress: lessons completed on a date make that date active; XP is
 *  back-filled for completed lessons/exercises. Existing progress fields are never modified. */
export function migrate(P, lessons, today) {
  const g = newGame();
  const byId = Object.fromEntries(lessons.map(l => [l.id, l]));
  for (const [lid, date] of Object.entries(P.completed || {})) {
    if (typeof date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(date)) continue;
    const rec = g.active[date] || (g.active[date] = { lessons: 0, review: false }); rec.lessons++;
    const l = byId[lid]; const amt = !l ? 0 : l.kind === "final" ? XP.final : l.kind === "checkpoint" ? XP.checkpoint : XP.lesson;
    addXP(g, `lesson:${lid}`, amt, date);
  }
  for (const [key, s] of Object.entries(P.ex || {})) {
    if (!s || !s.passed) continue;
    const [lid, i] = key.split(":"); const e = byId[lid] && byId[lid].exercises[+i]; if (!e) continue;
    addXP(g, `ex:${key}`, exerciseXP(e.difficulty, s.sawSol), s.passedOn || today);
  }
  // replay the history day by day so best streak and earned freezes are right
  const days = Object.keys(g.active).sort(); const act = g.active; g.active = {};
  for (const d of days) { reconcile(g, d); const rec = act[d]; recordActivity(g, d, "lesson"); g.active[d] = rec; }
  g.notices = []; g.lastSeen = null; g.resetNotified = null;
  return g;
}

/** Evening check: streak alive (yesterday or earlier) but today not done yet. */
export function atRisk(g, today, hour) {
  const s = streakInfo(g, today);
  return hour >= 18 && !s.todayDone && s.current > 0 ? { streak: s.current, freezes: g.freezes } : null;
}
