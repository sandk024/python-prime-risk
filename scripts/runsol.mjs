import { loadPyodide } from "pyodide"; import fs from "fs";
const [id, idx, extra] = process.argv.slice(2);
const data = JSON.parse(fs.readFileSync("public/lessons.json", "utf8"));
const l = data.units.flatMap(u => u.lessons).find(l => l.id === id);
const py = await loadPyodide({ indexURL: new URL("../public/pyodide/", import.meta.url).pathname });
const code = l.exercises[+idx].solution + "\n" + (extra || "");
await py.loadPackagesFromImports(code, { messageCallback: () => {} });
py.setStdout({ batched: s => console.log(s) });
py.runPython(code);
