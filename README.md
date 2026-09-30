# Python for Prime Risk

An offline-first iPhone PWA that teaches Python through prime brokerage, FCM/clearing, financing and market-risk use cases, with a full interview-prep track.

**Live app:** https://sandk024.github.io/python-prime-risk/ (open it in Safari, wait for "✓ Ready for offline", then Share → Add to Home Screen)

- 71 lessons across 10 units: 157 auto-checked exercises (★/★★/★★★), 8 unit checkpoints and a timed final assessment
- Real Python in the browser: Pyodide 314.0.7 (Python 3.14) with numpy and pandas, self-hosted and precached (~22.5 MB)
- Daily spaced **Review** (missed exercises and spaced repeats at 1 → 3 → 7 → 14 → 30 → 60 days)
- Code runs in a Web Worker with a Stop button, a 20 s timeout and Retry on load failure
- Progress is stored in localStorage, with JSON export and import

## Build

```bash
npm install                      # pyodide, codemirror, esbuild
python3 -m venv .venv && .venv/bin/pip install markdown
# copy pyodide core + numpy/pandas wheels into public/pyodide (see scripts)
./build.sh                       # content -> lessons.json, bundle editor, generate sw.js + precache
node scripts/validate.mjs        # runs every example + checks every exercise's solution/starter/wrong answer
python3 scripts/verify2.py <url> # Playwright iPhone 14: online -> offline reload -> pandas lesson run + check
```

Content lives in `content/*.py`, written in a small DSL (`content/dsl.py`). All data is synthetic.
