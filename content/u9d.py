from dsl import *
from u9a import TALK

KESTREL_CSV = '''client,counterparty,type,amount
HF-ALPHA,Kestrel Securities LLC,REVREPO,120000000
HF-ALPHA,KESTREL SEC.,COLLATERAL,95000000
HF-ALPHA,Kestral Securities,UNSETTLED,4000000
HF-BETA,Kestrel Securities LLC,REVREPO,60000000
HF-BETA,Kestrel Securities LLC,COLLATERAL,62000000
FO-GAMMA,Kestrel,UNSETTLED,7500000
FO-GAMMA,Osprey Capital,REVREPO,50000000
HF-DELTA,Kestrel Securities LLC,REVREPO,
HF-DELTA,Kestrel Securities LLC,REVREPO,30000000
HF-DELTA,Kestrel Securities LLC,COLLATERAL,12000000
'''

RESOLVE = r'''
import io, re
import numpy as np
import pandas as pd
ALIASES = {"kestral sec": "kestrel sec", "kestrel": "kestrel sec"}
def resolve(name):
    n = re.sub(r"[^a-z ]", "", str(name).lower())
    n = re.sub(r"\b(llc|inc|lp|ltd|corp)\b", "", n)
    n = n.replace("securities", "sec")
    n = " ".join(n.split())
    return ALIASES.get(n, n)
RAW = pd.read_csv(io.StringIO("""''' + KESTREL_CSV + '''"""))
'''

lesson("u9l8", "Palantir-style: decompose an ambiguous problem",
"Deployment Strategist / FDE interviews hand you a vague business question and messy data. Structure it, clean it, answer it, and explain the tradeoffs.",
r'''
Typical prompt: *"A counterparty, Kestrel Securities, may be failing. Which of our clients are most exposed, and what should the desk do first?"*

A structure that works (say it out loud, then write it at the top of your notebook):

1. **Clarify the goal & decision**: Who is the user (head of risk)? What decision (call clients? cut limits?) and by when?
2. **Define metrics**: exposure = net amount owed to us via Kestrel (repo cash lent + unsettled receivables - collateral held), by client.
3. **Inventory data & gaps**: a trades file with inconsistent counterparty names, collateral rows, missing values. State assumptions explicitly.
4. **Clean**: entity resolution (normalize names), types, duplicates. **Count what you drop.**
5. **Compute & rank**: groupby client; top N; sanity checks (do totals reconcile?).
6. **Communicate**: the answer in one sentence, the table, assumptions, risks, next steps ("confirm the legal-entity mapping with ops; refresh at 2pm").

Interviewers look for structure before code, explicit assumptions, pragmatic 80/20 tradeoffs, and a crisp recommendation. Saying "with more time I'd..." is good, not weak.
''',
talk=r'''
Script for the first 2 minutes: "Let me make sure I understand the decision this supports... I'll define exposure as X; here's what I need from the data; I see these quality issues; I'll make these assumptions and flag them; then I'll rank clients and sanity-check totals. Does that match what you're looking for?"

Tradeoffs to volunteer: exact vs fuzzy name matching (false merges vs misses); gross vs net of collateral; point-in-time vs intraday; speed vs completeness for a first answer.
''', timed=20,
examples=[("Messy names to one entity", r'''
import re
names = ["Kestrel Securities LLC", "KESTREL SEC.", "Kestrel Securities, L.L.C.", "Kestral Securities", "Osprey Capital"]
def norm(n):
    n = re.sub(r"[^a-z ]", "", n.lower())
    n = re.sub(r"\b(llc|inc|lp|ltd)\b", "", n)
    n = n.replace("securities", "sec")
    return " ".join(n.split())
for n in names:
    print(f"{n!r:32} -> {norm(n)!r}")
print("'kestral sec' is a typo: exact normalization misses it. difflib fuzzy matching could catch it, at the risk of false merges.")
'''), ("Fuzzy matching with difflib", r'''
import difflib
known = ["kestrel sec", "osprey capital", "heron"]
for raw in ["kestral sec", "osprey capitol", "falcon"]:
    print(raw, "->", difflib.get_close_matches(raw, known, n=1, cutoff=0.85))
''')],
quiz=[q("First thing to do with an ambiguous business question in a Palantir interview?", ["Start coding immediately", "Clarify the decision, user and metric; state assumptions", "Ask for a bigger dataset", "Build a dashboard"], 1, "Structure first. The interviewer is grading how you decompose ambiguity."),
q("Your fuzzy matcher merges 'Kestrel Sec' with 'Kestrel Bank' (a different legal entity). What's the risk?", ["None", "Overstated exposure to the failing entity and wrong calls to clients", "Slower code", "Memory usage"], 1, "False merges misstate exposure. Say how you'd review low-confidence matches (e.g. manual review queue).")],
exercises=[
ex("Resolve the counterparty", r'''
Write `resolve(name)` that maps raw counterparty names to a canonical entity:
- lower-case; remove everything except letters and spaces; remove the words `llc, inc, lp, ltd, corp`; replace `securities` with `sec`; collapse spaces
- then apply `ALIASES` (known typo/alias -> canonical) if the normalized name is a key

Return the canonical string.
''', r'''
import re
ALIASES = {"kestral sec": "kestrel sec", "kestrel": "kestrel sec"}

def resolve(name):
    ...

for n in ["Kestrel Securities LLC", "KESTREL SEC.", "Kestrel Securities, L.L.C.", "Kestral Securities", "Kestrel", "Osprey Capital Inc."]:
    print(n, "->", resolve(n))
''', r'''
import re
ALIASES = {"kestral sec": "kestrel sec", "kestrel": "kestrel sec"}

def resolve(name):
    n = re.sub(r"[^a-z ]", "", name.lower())
    n = re.sub(r"\b(llc|inc|lp|ltd|corp)\b", "", n)
    n = n.replace("securities", "sec")
    n = " ".join(n.split())
    return ALIASES.get(n, n)

for n in ["Kestrel Securities LLC", "KESTREL SEC.", "Kestrel Securities, L.L.C.", "Kestral Securities", "Kestrel", "Osprey Capital Inc."]:
    print(n, "->", resolve(n))
''', [("variants", r'''
got = {n: resolve(n) for n in ["Kestrel Securities LLC", "KESTREL SEC.", "Kestrel Securities, L.L.C.", "Kestral Securities", "Kestrel"]}
bad = {k: v for k, v in got.items() if v != "kestrel sec"}
assert not bad, f"these didn't resolve to 'kestrel sec': {bad}"
'''), ("other entities untouched", r'''assert resolve("Osprey Capital Inc.") == "osprey capital" and resolve("Heron Corp") == "heron", f"got {resolve('Osprey Capital Inc.')!r}, {resolve('Heron Corp')!r}"''')],
hints=["re.sub(r'[^a-z ]', '', name.lower()) removes punctuation, so 'L.L.C.' becomes 'llc'", "Then re.sub(r'\\b(llc|inc|lp|ltd|corp)\\b', '', n) and ' '.join(n.split())"],
wrong=r'''
ALIASES = {"kestral sec": "kestrel sec", "kestrel": "kestrel sec"}
def resolve(name):
    n = name.lower().replace(" llc", "").replace(".", "").replace("securities", "sec").strip()
    return ALIASES.get(n, n)
'''),
ex("Exposure to the failing counterparty", r'''
`resolve` and `RAW` are provided. Compute `exposure`: a Series indexed by client of **net exposure to Kestrel** = sum of `REVREPO` + sum of `UNSETTLED` - sum of `COLLATERAL`, floored at 0, **only for rows whose counterparty resolves to `"kestrel sec"`**. Drop rows with a missing amount (count them in `n_dropped`). Sort descending and drop zero-exposure clients.
''', RESOLVE + r'''
exposure = ...
n_dropped = ...
print(exposure, n_dropped)
''', RESOLVE + r'''
df = RAW.dropna(subset=["amount"])
n_dropped = len(RAW) - len(df)
df = df[df["counterparty"].map(resolve) == "kestrel sec"]
sign = np.where(df["type"] == "COLLATERAL", -1, 1)
net = (df["amount"] * sign).groupby(df["client"]).sum().clip(lower=0)
exposure = net[net > 0].sort_values(ascending=False)
print(exposure, n_dropped)
''', [("exposure", r'''
e = {k: float(v) for k, v in exposure.items()}
hint = ""
if e.get("HF-ALPHA") == 25_000_000.0: hint = ": include the typo 'Kestral' via resolve()"
if e.get("FO-GAMMA", 0) > 7.5e6: hint = ": Osprey isn't Kestrel"
assert e == {"HF-ALPHA": 29_000_000.0, "HF-DELTA": 18_000_000.0, "FO-GAMMA": 7_500_000.0}, f"exposure = {e}{hint}"
assert list(exposure.index) == ["HF-ALPHA", "HF-DELTA", "FO-GAMMA"], "Sort descending"
'''), ("n_dropped", r'''assert n_dropped == 1, f"n_dropped = {n_dropped}; one row has a missing amount. Always report what you dropped."''')],
hints=["Filter rows where df['counterparty'].map(resolve) == 'kestrel sec'", "sign = -1 for COLLATERAL, +1 otherwise; groupby client; clip at 0"],
wrong=RESOLVE + r'''
df = RAW[RAW["counterparty"].str.contains("Kestrel")]
exposure = df.groupby("client")["amount"].sum().sort_values(ascending=False)
n_dropped = 0
'''),
ex("Write the recommendation", r'''
Write `recommend(exposure, collateral_excess)` returning one string per client, in exposure order:
`"<client>: exposure $<X>m, excess $<Y>m -> <ACTION>"` with amounts in millions to 1 dp and ACTION = `CALL NOW` if exposure > excess, `MONITOR` if exposure > 50% of excess, else `OK`. A client missing from `collateral_excess` has excess 0.
''', r'''
import pandas as pd
EXPOSURE = pd.Series({"HF-ALPHA": 29_000_000.0, "HF-DELTA": 18_000_000.0, "FO-GAMMA": 7_500_000.0})
EXCESS = {"HF-ALPHA": 40_000_000.0, "HF-DELTA": 12_500_000.0, "FO-GAMMA": 30_000_000.0}

def recommend(exposure, collateral_excess):
    ...

print("\n".join(recommend(EXPOSURE, EXCESS)))
''', r'''
import pandas as pd
EXPOSURE = pd.Series({"HF-ALPHA": 29_000_000.0, "HF-DELTA": 18_000_000.0, "FO-GAMMA": 7_500_000.0})
EXCESS = {"HF-ALPHA": 40_000_000.0, "HF-DELTA": 12_500_000.0, "FO-GAMMA": 30_000_000.0}

def recommend(exposure, collateral_excess):
    out = []
    for client, x in exposure.items():
        y = collateral_excess.get(client, 0.0)
        action = "CALL NOW" if x > y else ("MONITOR" if x > 0.5 * y else "OK")
        out.append(f"{client}: exposure ${x / 1e6:.1f}m, excess ${y / 1e6:.1f}m -> {action}")
    return out

print("\n".join(recommend(EXPOSURE, EXCESS)))
''', [("lines", r'''
got = recommend(EXPOSURE, EXCESS)
exp = ["HF-ALPHA: exposure $29.0m, excess $40.0m -> MONITOR", "HF-DELTA: exposure $18.0m, excess $12.5m -> CALL NOW", "FO-GAMMA: exposure $7.5m, excess $30.0m -> OK"]
assert got == exp, "got:\n" + "\n".join(map(str, got)) + "\nexpected:\n" + "\n".join(exp)
'''), ("missing excess = 0", r'''
import pandas as pd
assert recommend(pd.Series({"X": 1e6}), {}) == ["X: exposure $1.0m, excess $0.0m -> CALL NOW"]
''')], hints=["collateral_excess.get(client, 0.0)", "f'{x / 1e6:.1f}'"],
wrong=r'''
def recommend(exposure, collateral_excess):
    return [f"{c}: exposure ${x/1e6:.1f}m, excess ${collateral_excess.get(c, 0)/1e6:.1f}m -> {'CALL NOW' if x > collateral_excess.get(c, 0) else 'OK'}" for c, x in exposure.items()]
'''),
])
