// Module worker hosting Pyodide (self-hosted under ./pyodide/). Runs user code off the UI thread.
import { loadPyodide } from "./pyodide/pyodide.mjs";
let py;
const ready = (async () => {
  py = await loadPyodide({ indexURL: new URL("./pyodide/", self.location).href });
  const src = await (await fetch(new URL("./runner.py", self.location))).text();
  py.runPython(src);
  py.setStdin({ stdin: () => { throw new Error("input() isn't supported here — set the value in code instead."); } });
  self.postMessage({ type: "ready" });
})().catch(err => self.postMessage({ type: "fatal", error: String(err) }));

self.onmessage = async (e) => {
  const { id, code, tests, setup, kind } = e.data;
  try {
    await ready;
    if (kind === "preload") {
      await py.loadPackage(e.data.packages, { messageCallback: () => {} });
      self.postMessage({ id, type: "result", result: { ok: true } });
      return;
    }
    const all = code + "\n" + (setup || "") + "\n" + (tests || []).map(t => t.code).join("\n");
    if (/\b(import|from)\s+(pandas|numpy)/.test(all)) self.postMessage({ id, type: "status", status: "loading-packages" });
    await py.loadPackagesFromImports(all, { messageCallback: () => {} });
    self.postMessage({ id, type: "status", status: "running" });
    const res = py.globals.get("run")(code, tests ? JSON.stringify(tests) : "null", setup || "");
    self.postMessage({ id, type: "result", result: JSON.parse(res) });
  } catch (err) {
    self.postMessage({ id, type: "result", result: { stdout: "", error: String(err && err.message || err), results: [] } });
  }
};
