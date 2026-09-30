// Unit tests for public/streak.js with simulated local dates. Run: node scripts/test-streak.mjs
import * as S from "../public/streak.js";
let pass = 0, fail = 0;
const t = (name, fn) => { try { fn(); pass++; console.log("ok  ", name); } catch (e) { fail++; console.log("FAIL", name, "→", e.message); } };
const eq = (a, b, m = "") => { if (JSON.stringify(a) !== JSON.stringify(b)) throw new Error(`${m} expected ${JSON.stringify(b)}, got ${JSON.stringify(a)}`); };
const day = (start, n) => S.addDays(start, n);
// Simulates opening the app on `d` and finishing a lesson.
const study = (g, d, kind = "lesson") => { S.reconcile(g, d); return S.recordActivity(g, d, kind); };
const open = (g, d) => S.reconcile(g, d);
const D0 = "2026-10-01";

t("increments one per day", () => {
  const g = S.newGame();
  for (let i = 0; i < 3; i++) study(g, day(D0, i));
  eq(S.streakInfo(g, day(D0, 2)).current, 3);
  eq(S.streakInfo(g, day(D0, 3)).current, 3, "next morning before studying, streak still shows");
});
t("no double counting: two lessons + review on one day", () => {
  const g = S.newGame();
  const e1 = study(g, D0); const e2 = study(g, D0); const e3 = study(g, D0, "review");
  eq(S.streakInfo(g, D0).current, 1); eq(e1.filter(e => e.type === "goal").length, 1); eq(e2.length + e3.length, 0);
  eq(g.active[D0], { lessons: 2, review: true });
});
t("midnight: 23:59 and 00:01 are two different local days", () => {
  const g = S.newGame();
  study(g, S.ymd(new Date(2026, 9, 5, 23, 59, 30)));
  study(g, S.ymd(new Date(2026, 9, 6, 0, 1, 0)));
  eq(Object.keys(g.active), ["2026-10-05", "2026-10-06"]); eq(S.streakInfo(g, "2026-10-06").current, 2);
});
t("DST change (US: 2026-11-01, 2027-03-14) doesn't break day math", () => {
  eq(S.addDays("2026-10-31", 1), "2026-11-01"); eq(S.addDays("2026-11-01", 1), "2026-11-02");
  eq(S.addDays("2027-03-13", 1), "2027-03-14"); eq(S.diffDays("2027-03-15", "2027-03-13"), 2);
  const g = S.newGame(); for (let i = 0; i < 5; i++) study(g, day("2027-03-12", i)); eq(S.streakInfo(g, "2027-03-16").current, 5);
});
t("reset after a missed day with no freezes", () => {
  const g = S.newGame();
  for (let i = 0; i < 4; i++) study(g, day(D0, i));
  const n = open(g, day(D0, 5)); // missed D0+4
  eq(n.map(x => x.type), ["reset"]); eq(n[0].was, 4);
  eq(S.streakInfo(g, day(D0, 5)).current, 0);
  study(g, day(D0, 5)); eq(S.streakInfo(g, day(D0, 5)).current, 1); eq(g.best, 4, "best streak kept");
  eq(open(g, day(D0, 5)).length, 0, "reopening the same day doesn't re-notify");
});
t("freeze earned at 7, applied to a single missed day, streak survives", () => {
  const g = S.newGame(); let earned = [];
  for (let i = 0; i < 7; i++) earned.push(...study(g, day(D0, i)).filter(e => e.type === "freezeEarned"));
  eq(g.freezes, 1); eq(earned.length, 1);
  const n = open(g, day(D0, 8)); // missed D0+7
  eq(n[0].type, "freezeUsed"); eq(n[0].days, [day(D0, 7)]); eq(g.freezes, 0);
  eq(S.streakInfo(g, day(D0, 8)).current, 7, "frozen day bridges the chain (not counted)");
  study(g, day(D0, 8)); eq(S.streakInfo(g, day(D0, 8)).current, 8);
});
t("freeze cap is 2 (21-day streak still = 2)", () => {
  const g = S.newGame(); for (let i = 0; i < 21; i++) study(g, day(D0, i)); eq(g.freezes, 2);
});
t("freeze not spent when the gap is longer than available freezes", () => {
  const g = S.newGame(); for (let i = 0; i < 7; i++) study(g, day(D0, i)); eq(g.freezes, 1);
  const n = open(g, day(D0, 9)); // missed 2 days, only 1 freeze
  eq(n.map(x => x.type), ["reset"]); eq(g.freezes, 1, "freeze kept"); eq(Object.keys(g.frozen).length, 0);
});
t("two freezes cover two missed days", () => {
  const g = S.newGame(); for (let i = 0; i < 14; i++) study(g, day(D0, i)); eq(g.freezes, 2);
  const n = open(g, day(D0, 16)); eq(n[0].type, "freezeUsed"); eq(n[0].days.length, 2); eq(g.freezes, 0);
  study(g, day(D0, 16)); eq(S.streakInfo(g, day(D0, 16)).current, 15);
});
t("freeze isn't re-awarded when the same streak length is reached twice in a day", () => {
  const g = S.newGame(); for (let i = 0; i < 7; i++) study(g, day(D0, i)); study(g, day(D0, 6)); eq(g.freezes, 1);
});
t("reconcile is idempotent and ignores a clock moved backwards", () => {
  const g = S.newGame(); for (let i = 0; i < 3; i++) study(g, day(D0, i));
  eq(open(g, day(D0, -5)).length, 0); eq(S.streakInfo(g, day(D0, 2)).current, 3);
});
t("milestone badges at 3, 7, 14, 30, 50, 60, 100 over a 100-day run", () => {
  const g = S.newGame(); const ctx = { units: [], completed: { x: 1 }, clean3: 0 }; const got = [];
  for (let i = 0; i < 100; i++) { const d = day(D0, i); study(g, d); got.push(...S.evaluateBadges(g, ctx, d).filter(b => b.def.id.startsWith("streak-")).map(b => [b.def.id, i + 1])); }
  eq(got, [["streak-3", 3], ["streak-7", 7], ["streak-14", 14], ["streak-30", 30], ["streak-50", 50], ["streak-60", 60], ["streak-100", 100]]);
  eq(g.best, 100);
});
t("perfect week = all 7 days of a Mon–Sun week", () => {
  const g = S.newGame(); const ctx = { units: [], completed: {}, clean3: 0 };
  const mon = "2026-10-05"; eq(S.weekday(mon), 0);
  for (let i = 1; i < 8; i++) study(g, day(mon, i)); // Tue..Mon: 7 days but spans two weeks
  eq(S.evaluateBadges(g, ctx, day(mon, 7)).some(b => b.def.id === "perfect-week"), false);
  for (let i = 8; i < 14; i++) study(g, day(mon, i)); // completes Mon 12 .. Sun 18
  eq(S.evaluateBadges(g, ctx, day(mon, 13)).some(b => b.def.id === "perfect-week"), true);
});
t("unit + habit badges, earned once", () => {
  const g = S.newGame(); const ctx = { units: [{ id: "u1", title: "U1", lessonIds: ["a", "b"] }], completed: { a: D0 }, clean3: 10, finalUnitId: "final" };
  let b = S.evaluateBadges(g, ctx, D0).map(x => x.def.id); eq(b.includes("unit-u1"), false); eq(b.includes("first-lesson") && b.includes("clean-10"), true);
  ctx.completed.b = D0; b = S.evaluateBadges(g, ctx, D0).map(x => x.def.id); eq(b, ["unit-u1"]);
  eq(S.evaluateBadges(g, ctx, D0).length, 0);
});
t("XP awarded once per key; levels and level-up event", () => {
  const g = S.newGame();
  eq(S.addXP(g, "lesson:u1l1", 50, D0).length, 1); eq(S.addXP(g, "lesson:u1l1", 50, D0).length, 0); eq(g.xp, 50);
  const ev = S.addXP(g, "big", 260, D0); eq(ev.map(e => e.type), ["xp", "levelUp"]); eq(ev[1].title, "Analyst");
  eq(S.levelFor(0).title, "Intern"); eq(S.levelFor(15000).title, "Head of Prime Risk"); eq(S.levelFor(15000).next, null);
  eq(S.exerciseXP(3, false), 40); eq(S.exerciseXP(3, true), 30); eq(S.exerciseXP(1, false), 20);
  eq(g.xpByDay[D0], 310);
});
t("streak at risk only in the evening when today isn't done", () => {
  const g = S.newGame(); study(g, D0);
  eq(S.atRisk(g, day(D0, 1), 17), null); eq(S.atRisk(g, day(D0, 1), 19).streak, 1);
  study(g, day(D0, 1)); eq(S.atRisk(g, day(D0, 1), 22), null);
  eq(S.atRisk(S.newGame(), D0, 21), null, "no streak, no nag");
});
t("migration from pre-streak progress keeps everything and back-fills days/XP", () => {
  const lessons = [{ id: "u1l1", exercises: [{ difficulty: 1 }, { difficulty: 3 }] }, { id: "u1cp", kind: "checkpoint", exercises: [] }];
  const P = { completed: { u1l1: "2026-09-28", u1cp: "2026-09-29" }, ex: { "u1l1:0": { passed: true, passedOn: "2026-09-28", attempts: 1 }, "u1l1:1": { passed: true, sawSol: true, passedOn: "2026-09-28", attempts: 3 }, "u1l1:9": { passed: true } }, days: ["2026-09-28", "2026-09-29"] };
  const snapshot = JSON.stringify(P);
  const g = S.migrate(P, lessons, "2026-09-30");
  eq(JSON.stringify(P), snapshot, "original progress untouched");
  eq(Object.keys(g.active).sort(), ["2026-09-28", "2026-09-29"]); eq(g.best, 2);
  eq(g.xp, 50 + 100 + 20 + 30); eq(S.streakInfo(g, "2026-09-30").current, 2);
  const g2 = S.normalize(JSON.parse(JSON.stringify(g))); eq(g2.xp, g.xp, "survives export/import round-trip");
});
console.log(`\nSTREAK TESTS: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
