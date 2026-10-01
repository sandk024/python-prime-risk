// Curriculum checks for the beginner rework. Run: node scripts/test-curriculum.mjs
import fs from "fs";
const data = JSON.parse(fs.readFileSync("public/lessons.json", "utf8"));
const before = JSON.parse(fs.readFileSync("scripts/fixture-lesson-ids-v1.json", "utf8")); // ids/exercises before the rework
let pass = 0, fail = 0;
const t = (name, fn) => { try { fn(); pass++; console.log("ok  ", name); } catch (e) { fail++; console.log("FAIL", name, "→", e.message); } };
const ok = (c, m) => { if (!c) throw new Error(m); };
const L = data.units.flatMap(u => u.lessons.map(l => ({ ...l, unit: u.id })));
const byId = Object.fromEntries(L.map(l => [l.id, l]));
const u0 = data.units[0];
t("first unit is 'Python from Zero' (u0) and the first lesson is u0l1", () => { ok(u0.id === "u0" && u0.title === "Python from Zero", u0.title); ok(L[0].id === "u0l1", L[0].id); });
t("12-15 beginner lessons, then 'Python on a Trading Desk'", () => { ok(u0.lessons.length >= 12 && u0.lessons.length <= 15, u0.lessons.length); ok(data.units[1].id === "u1" && data.units[1].title === "Python on a Trading Desk", data.units[1].title); });
t("every pre-existing lesson id still exists, same unit, same exercises in the same order (progress/review keys stay valid)", () => {
  for (const [id, b] of Object.entries(before)) { const l = byId[id]; ok(l, `missing ${id}`); ok(l.unit === b.unit, `${id} moved unit`); ok(JSON.stringify(l.exercises.map(e => e.title)) === JSON.stringify(b.exercises), `${id} exercises changed`); }
});
t("lesson ids are unique", () => ok(new Set(L.map(l => l.id)).size === L.length, "duplicate id"));
for (const l of u0.lessons) t(`${l.id} '${l.title}': learn line, chunks with runnable code, 1 predict question, 2-4 exercises, recap, ~10 min`, () => {
  ok(l.learn && !l.learn.includes("\n"), "missing one-line learn");
  ok(l.recap && !l.recap.includes("\n"), "missing one-line recap");
  ok(l.chunks.length >= 2 && l.chunks.some(c => c.code), "needs small chunks with runnable examples");
  ok(l.quiz.length === 1, "one predict-the-output question");
  ok(l.exercises.length >= 2 && l.exercises.length <= 4, `${l.exercises.length} exercises`);
  ok(l.minutes <= 15, `${l.minutes} min`);
  for (const e of l.exercises) {
    const code = e.solution.split("\n").filter(x => x.trim() && !x.trim().startsWith("#"));
    const commented = code.filter(x => x.includes("#")).length;
    ok(commented / code.length >= 0.5, `"${e.title}" solution should explain its lines with comments (${commented}/${code.length})`);
    ok(!e.starter.includes("..."), `"${e.title}" starter uses ... (unexplained syntax)`);
    ok(e.hints.length >= 1, `"${e.title}" needs a hint`);
  }
});
t("no finance jargon in Python from Zero (light trading flavour only: price/quantity/buy/sell)", () => {
  const jargon = /notional|P&L|margin|futures|multiplier|\btick|basis point|\bbps?\b|drawdown|collateral|clearing|SOFR|\brepo\b|\bVaR\b/;
  for (const l of u0.lessons) {
    const text = [l.title, l.learn, l.recap, ...l.chunks.map(c => (c.html || "") + (c.code || "")), ...l.exercises.map(e => e.prompt_html + e.starter), ...l.quiz.map(q => q.q_html + (q.code || ""))].join(" ");
    const m = text.match(jargon); ok(!m, `${l.id} uses '${m && m[0]}'`);
  }
});
t("beginner starters only use syntax taught up to that lesson (no comprehensions, lambda, import, try)", () => {
  for (const l of u0.lessons) for (const e of l.exercises) ok(!/lambda|\bimport\b|\btry:|\[[^\]]+ for [^\]]+ in /.test(e.starter), `${l.id} "${e.title}"`);
});
t("predict answers are not always the first option", () => ok(new Set(u0.lessons.map(l => l.quiz[0].answer)).size > 1, "all answers at the same index"));
t("trading-desk lessons define new Python before using it", () => { for (const id of ["u1l1", "u1l2", "u1l3", "u1l4", "u1l5", "u1l6", "u1l7"]) ok(byId[id].body_html.includes("New in this lesson"), id); });
t("trading-desk examples/solutions avoid syntax not yet introduced (no comprehension before u1l6, no one-line if/else before u1l5)", () => {
  for (const id of ["u1l1", "u1l2", "u1l3", "u1l4"]) { const l = byId[id]; const code = [...l.examples.map(e => e.code || e), ...l.exercises.flatMap(e => [e.starter, e.solution])].join("\n");
    ok(!/\[[^\]\n]+ for [^\]\n]+ in [^\]\n]+\]|\{[^}\n]+ for [^}\n]+ in [^}\n]+\}/.test(code), `${id} uses a comprehension`); ok(!/ if [^\n:]+ else /.test(code), `${id} uses a one-line if/else`); ok(!/lambda/.test(code), `${id} uses lambda`); }
});
console.log(`\nCURRICULUM TESTS: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
