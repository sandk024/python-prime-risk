// Validates every exercise: reference solution passes all tests, plausible wrong answer fails with feedback,
// starter code does not pass; every example runs without error; quiz answers valid.
import { loadPyodide } from "pyodide";
import fs from "fs";
const data = JSON.parse(fs.readFileSync("public/lessons.json", "utf8"));
const only = process.argv[2];
const py = await loadPyodide({ indexURL: new URL("../public/pyodide/", import.meta.url).pathname });
py.runPython(fs.readFileSync("public/runner.py", "utf8"));
const run = py.globals.get("run");
async function R(code, tests, setup = "") {
  await py.loadPackagesFromImports(code + "\n" + (tests ? tests.map(t => t.code).join("\n") : ""), { messageCallback: () => {} });
  return JSON.parse(run(code, tests ? JSON.stringify(tests) : "null", setup || ""));
}
let fails = 0, nex = 0, nexamples = 0, lines = [];
for (const u of data.units) for (const l of u.lessons) {
  if (only && !l.id.startsWith(only)) continue;
  for (const [i, e] of l.examples.entries()) {
    nexamples++;
    const code = typeof e === "string" ? e : e.code;
    const r = await R(code, null);
    if (r.error) { fails++; lines.push(`FAIL ${l.id} example ${i}: ${r.error}`); }
  }
  for (const [i, c] of (l.chunks || []).entries()) {
    if (!c.code) continue;
    nexamples++;
    const r = await R(c.code, null);
    if (c.error && !r.error) { fails++; lines.push(`FAIL ${l.id} chunk ${i}: meant to show an error but ran cleanly`); }
    if (!c.error && r.error) { fails++; lines.push(`FAIL ${l.id} chunk ${i}: ${r.error}`); }
    if (!c.error && !r.stdout.trim()) { fails++; lines.push(`FAIL ${l.id} chunk ${i}: example prints nothing`); }
  }
  for (const qz of l.quiz) if (!(qz.answer >= 0 && qz.answer < qz.options.length)) { fails++; lines.push(`FAIL ${l.id} quiz answer index`); }
  for (const [i, e] of l.exercises.entries()) {
    nex++;
    const tag = `${l.id} ex${i + 1} "${e.title}"`;
    const s = await R(e.solution, e.tests, e.setup);
    const sOk = !s.error && s.results.every(r => r.ok);
    if (!sOk) { fails++; lines.push(`FAIL ${tag} solution: ${s.error || JSON.stringify(s.results.filter(r => !r.ok))}`); }
    if (!e.wrong) { fails++; lines.push(`FAIL ${tag}: no wrong answer`); }
    else {
      const w = await R(e.wrong, e.tests, e.setup);
      const failed = w.results.filter(r => !r.ok);
      if (!w.error && failed.length === 0) { fails++; lines.push(`FAIL ${tag} wrong answer PASSED`); }
      else if (failed.some(r => !r.msg)) { fails++; lines.push(`FAIL ${tag} wrong answer: empty feedback`); }
      else lines.push(`ok   ${tag}  solution ${s.results.length}/${s.results.length} pass; wrong ${failed.length}/${w.results.length} fail → "${(w.error || failed[0].msg).split("\n")[0].slice(0, 90)}"`);
    }
    const st = await R(e.starter, e.tests, e.setup);
    if (!st.error && st.results.every(r => r.ok)) { fails++; lines.push(`FAIL ${tag} starter already passes`); }
  }
}
console.log(lines.join("\n"));
console.log(`\nSUMMARY exercises=${nex} examples=${nexamples} failures=${fails}`);
process.exit(fails ? 1 : 0);
