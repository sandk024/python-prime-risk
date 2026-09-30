import { loadPyodide } from "pyodide";
import fs from "fs";
const t0=Date.now();
const py = await loadPyodide({ indexURL: new URL("../public/pyodide/", import.meta.url).pathname });
await py.loadPackage(["numpy","pandas"]);
py.runPython(fs.readFileSync("public/runner.py","utf8"));
const run = py.globals.get("run");
console.log(run("import pandas as pd, numpy as np\nprint(pd.__version__, np.__version__)\nx=1/0", "[]"));
console.log("ms", Date.now()-t0);
