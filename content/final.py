from dsl import *

unit("final", "Final Assessment", "A timed, mixed exam across the whole course. Pass all 8 exercises to earn the course certificate badge.")

FA_POS = r'''
import io
import numpy as np
import pandas as pd
POS = pd.read_csv(io.StringIO("""account,symbol,qty
A1,ES,20
A1,ZN,-100
B2,CL,-40
B2,ES,-5
C3,GC,15
C3,ZN,60
"""))
SPECS = pd.DataFrame({"symbol": ["ES", "ZN", "CL", "GC"],
                      "price": [5800.0, 110.5, 72.0, 2650.0],
                      "mult": [50, 1000, 1000, 100],
                      "im_rate": [0.06, 0.02, 0.10, 0.07]})
COLL = {"A1": 2_600_000.0, "B2": 150_000.0, "C3": 600_000.0}
'''

lesson("fa1", "Final assessment (timed, 60 min)",
"Prove it end to end: the same mix of Python, pandas, numpy, margin, financing, risk and algorithms you'd face on the desk or in an interview.",
r'''
**Rules**
- Start the 60-minute timer. Work through the questions, then the 8 exercises in any order.
- Hints are available, but try each exercise cold first. The solution unlocks after 2 attempts, but using it means you should redo the exercise from the Review queue later.
- **Passing** = all 8 exercises checked green. Your score (exercises passed without viewing the solution) is shown in the progress summary.

Difficulty rises roughly in order: ★ fluency, ★★ applied analytics, ★★★ interview-grade.
''',
timed=60, minutes=60, kind="final",
quiz=[
q("What is the output?", ["[1, 2, 3]", "[3, 2, 1]", "None", "Error"], 2, "`list.sort()` sorts in place and returns None.", code="print([3, 1, 2].sort())"),
q("A dict lookup is O(1) on average. Looking up 1m keys in a dict of 10m entries is about...", ["O(1)", "O(1m)", "O(10m)", "O(10m x 1m)"], 1, "1m operations of O(1) each."),
q("`df.groupby('acct')['x'].transform('sum')` returns...", ["One row per account", "A Series aligned to the original rows", "A scalar", "A DataFrame of sums"], 1, "transform broadcasts group results back to each row."),
q("Annualized vol is 16%. Approximate daily vol?", ["1%", "0.06%", "4%", "16%"], 0, "16% / sqrt(256) = 1% (the classic trader's rule of thumb)."),
q("A client's equity is above maintenance but below initial. What happens?", ["Margin call to initial", "No call, but no new risk-increasing trades without adding margin (per FCM policy)", "Liquidation", "Account closed"], 1, "Calls trigger below maintenance; between maintenance and initial the account is restricted by typical policies."),
q("Repo at 5.3% ACT/360 vs a 5.3% ACT/365 loan. Which pays more interest for the same days?", ["ACT/360", "ACT/365", "Equal", "Depends on the principal"], 0, "Dividing by 360 gives a larger year fraction."),
q("Historical 99% VaR from 250 days uses roughly which observation?", ["The worst", "The 2nd-3rd worst", "The 25th worst", "The median"], 1, "1% of 250 = 2.5 observations; numpy interpolates between the 2nd and 3rd worst."),
q("Best first step in a Palantir-style case with messy data?", ["Write a regex", "Clarify the decision and define the metric, then state assumptions", "Train a model", "Ask for clean data"], 1, "Structure beats speed."),
],
exercises=[
ex("1. Parse & aggregate fills", r'''
`LINES` holds raw fill strings like `"ES|B|10|5790.25"` (symbol, side, qty, price). Some lines are blank or malformed (wrong number of fields or non-numeric values); skip them. Return a dict **symbol -> (net_qty, vwap)** where vwap is the volume-weighted average price over **all** fills for that symbol (buys and sells, by absolute qty), rounded to 4 dp.
''', r'''
LINES = ["ES|B|10|5790.25", "ES|S|4|5792.00", "", "CL|S|3|72.10", "garbage", "CL|S|x|72.0", "ES|B|6|5788.50", "ZN|B|100|110.5|extra"]

def fills_summary(lines):
    ...

print(fills_summary(LINES))
''', r'''
LINES = ["ES|B|10|5790.25", "ES|S|4|5792.00", "", "CL|S|3|72.10", "garbage", "CL|S|x|72.0", "ES|B|6|5788.50", "ZN|B|100|110.5|extra"]

def fills_summary(lines):
    agg = {}
    for line in lines:
        parts = line.split("|")
        if len(parts) != 4:
            continue
        sym, side, q, px = parts
        try:
            q, px = int(q), float(px)
        except ValueError:
            continue
        net, vol, notional = agg.get(sym, (0, 0, 0.0))
        agg[sym] = (net + (q if side == "B" else -q), vol + q, notional + q * px)
    return {s: (net, round(notional / vol, 4)) for s, (net, vol, notional) in agg.items()}

print(fills_summary(LINES))
''', [("result", r'''
r = fills_summary(LINES)
assert set(r) == {"ES", "CL"}, f"symbols = {set(r)}: skip malformed lines (ZN has 5 fields)"
assert r["ES"][0] == 12 and abs(r["ES"][1] - round((10 * 5790.25 + 4 * 5792.0 + 6 * 5788.5) / 20, 4)) < 1e-9, f"ES = {r['ES']}"
assert r["CL"] == (-3, 72.1), f"CL = {r['CL']}"
''')],
hints=["split('|') and check len(parts) == 4", "Track net qty, total absolute qty and total notional per symbol."],
wrong=r'''
def fills_summary(lines):
    out = {}
    for line in lines:
        try:
            s, side, q, px = line.split("|")
            out[s] = (int(q), float(px))
        except ValueError:
            pass
    return out
''', difficulty=1),
ex("2. A validated Position class", r'''
Write a `@dataclass` `Position(symbol: str, qty: int, price: float, mult: int)` that raises `ValueError` in `__post_init__` if `mult <= 0` or `price <= 0`, and has a property `notional` (qty x price x mult) and a method `shock(pct)` returning the P&L for a `pct` % price move.
''', r'''
from dataclasses import dataclass

@dataclass
class Position:
    ...

p = Position("ES", -3, 5800.0, 50)
print(p.notional, p.shock(-2))
''', r'''
from dataclasses import dataclass

@dataclass
class Position:
    symbol: str
    qty: int
    price: float
    mult: int

    def __post_init__(self):
        if self.mult <= 0 or self.price <= 0:
            raise ValueError(f"invalid position {self.symbol}: price and mult must be positive")

    @property
    def notional(self):
        return self.qty * self.price * self.mult

    def shock(self, pct):
        return self.notional * pct / 100

p = Position("ES", -3, 5800.0, 50)
print(p.notional, p.shock(-2))
''', [("values", r'''
p = Position("ES", -3, 5800.0, 50)
assert _close(p.notional, -870_000) and _close(p.shock(-2), 17_400), f"notional = {p.notional}, shock(-2) = {p.shock(-2)}: a short gains when price falls"
'''), ("validation", r'''
for bad in [("X", 1, 0.0, 50), ("X", 1, 10.0, 0)]:
    try:
        Position(*bad)
    except ValueError:
        continue
    raise AssertionError(f"Position{bad} should raise ValueError")
'''), ("is a dataclass", r'''
import dataclasses
assert dataclasses.is_dataclass(Position), "Use @dataclass"
assert isinstance(Position.__dict__.get("notional"), property), "notional should be a @property (p.notional, not p.notional())"
''')],
hints=["Validation goes in __post_init__.", "@property def notional(self): ..."],
wrong=r'''
from dataclasses import dataclass
@dataclass
class Position:
    symbol: str
    qty: int
    price: float
    mult: int
    def notional(self):
        return abs(self.qty) * self.price * self.mult
    def shock(self, pct):
        return abs(self.qty) * self.price * self.mult * pct / 100
''', difficulty=1),
ex("3. Margin by account (pandas)", r'''
Join `POS` to `SPECS`, compute each row's `im` = |qty| x price x mult x im_rate, then build `report`: a DataFrame indexed by account with columns `im` (sum), `collateral` (from `COLL`), `excess` (collateral - im) and `call` (max(0, -excess)), sorted by `excess` ascending.
''', FA_POS + r'''
report = ...
print(report)
''', FA_POS + r'''
df = POS.merge(SPECS, on="symbol", how="left", validate="many_to_one")
df["im"] = df["qty"].abs() * df["price"] * df["mult"] * df["im_rate"]
report = df.groupby("account")[["im"]].sum()
report["collateral"] = report.index.map(COLL)
report["excess"] = report["collateral"] - report["im"]
report["call"] = (-report["excess"]).clip(lower=0)
report = report.sort_values("excess")
print(report)
''', [("im", r'''
r = report["im"].round(2).to_dict()
assert r == {"A1": 569_000.0, "B2": 375_000.0, "C3": 410_850.0}, f"im = {r}"
'''), ("calls", r'''
assert list(report.index) == ["B2", "C3", "A1"], f"order = {list(report.index)}"
assert report["call"].round(2).to_dict() == {"B2": 225_000.0, "C3": 0.0, "A1": 0.0}, f"call = {report['call'].to_dict()}"
''')],
hints=["POS.merge(SPECS, on='symbol')", "call = (-excess).clip(lower=0)"],
wrong=FA_POS + r'''
df = POS.merge(SPECS, on="symbol")
df["im"] = df["qty"] * df["price"] * df["mult"] * df["im_rate"]
report = df.groupby("account")[["im"]].sum()
report["collateral"] = report.index.map(COLL)
report["excess"] = report["collateral"] - report["im"]
report["call"] = (-report["excess"]).clip(lower=0)
report = report.sort_values("excess")
''', difficulty=2),
ex("4. Rolling vol regime (numpy/pandas)", r'''
From the price series `PX`, compute daily **log** returns, a 20-day rolling standard deviation annualized with sqrt(252) (`vol`), and `regime`: a Series that is `"HIGH"` where vol > 1.5 x the median of the non-NaN vol values, else `"NORMAL"` (NaN vol -> `"NORMAL"`). Also set `n_high` = number of HIGH days.
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(11)
r = np.concatenate([rng.normal(0, 0.008, 120), rng.normal(0, 0.03, 30), rng.normal(0, 0.008, 50)])
PX = pd.Series(100 * np.exp(np.cumsum(r)))
vol = ...
regime = ...
n_high = ...
print(n_high)
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(11)
r = np.concatenate([rng.normal(0, 0.008, 120), rng.normal(0, 0.03, 30), rng.normal(0, 0.008, 50)])
PX = pd.Series(100 * np.exp(np.cumsum(r)))
rets = np.log(PX).diff()
vol = rets.rolling(20).std() * np.sqrt(252)
threshold = 1.5 * vol.median()
regime = pd.Series(np.where(vol > threshold, "HIGH", "NORMAL"), index=PX.index)
n_high = int((regime == "HIGH").sum())
print(n_high)
''', [("vol", r'''
exp = np.log(PX).diff().rolling(20).std() * np.sqrt(252)
assert np.allclose(vol.dropna(), exp.dropna()), "vol = rolling(20) std of log returns x sqrt(252)"
'''), ("regime", r'''
exp = np.log(PX).diff().rolling(20).std() * np.sqrt(252)
e = int((exp > 1.5 * exp.median()).sum())
assert n_high == e and len(regime) == len(PX), f"n_high = {n_high}, expected {e}"
assert 20 <= n_high <= 60, "The high-vol burst should show up as a HIGH regime"
''')],
hints=["np.log(PX).diff()", "np.where(vol > threshold, 'HIGH', 'NORMAL'); NaN > x is False"],
wrong=r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(11)
r = np.concatenate([rng.normal(0, 0.008, 120), rng.normal(0, 0.03, 30), rng.normal(0, 0.008, 50)])
PX = pd.Series(100 * np.exp(np.cumsum(r)))
vol = PX.pct_change().rolling(20).std() * 252
regime = pd.Series(np.where(vol > vol.mean(), "HIGH", "NORMAL"))
n_high = int((regime == "HIGH").sum())
''', difficulty=2),
ex("5. Repo book weighted-average rate", r'''
`BOOK` lists repo trades `(side, cash, rate, days)` where side is `"REPO"` (we borrow cash) or `"REVREPO"` (we lend). Return a dict with `borrow_wa` and `lend_wa` (cash-weighted average rates, rounded to 5 dp) and `net_carry` = total interest earned on REVREPO minus total paid on REPO, ACT/360, rounded to 2 dp.
''', r'''
BOOK = [("REVREPO", 250_000_000, 0.0545, 1), ("REVREPO", 100_000_000, 0.0560, 7),
        ("REPO", 200_000_000, 0.0530, 1), ("REPO", 120_000_000, 0.0535, 7)]

def repo_book(book):
    ...

print(repo_book(BOOK))
''', r'''
BOOK = [("REVREPO", 250_000_000, 0.0545, 1), ("REVREPO", 100_000_000, 0.0560, 7),
        ("REPO", 200_000_000, 0.0530, 1), ("REPO", 120_000_000, 0.0535, 7)]

def repo_book(book):
    def wa(side):
        rows = [(c, r) for s, c, r, d in book if s == side]
        total = sum(c for c, _ in rows)
        return round(sum(c * r for c, r in rows) / total, 5) if total else 0.0
    interest = lambda side: sum(c * r * d / 360 for s, c, r, d in book if s == side)
    return {"borrow_wa": wa("REPO"), "lend_wa": wa("REVREPO"),
            "net_carry": round(interest("REVREPO") - interest("REPO"), 2)}

print(repo_book(BOOK))
''', [("wa rates", r'''
r = repo_book(BOOK)
assert r["borrow_wa"] == round((200e6 * 0.053 + 120e6 * 0.0535) / 320e6, 5) and r["lend_wa"] == round((250e6 * 0.0545 + 100e6 * 0.056) / 350e6, 5), f"got {r}"
'''), ("carry", r'''
r = repo_book(BOOK)
exp = round(250e6 * 0.0545 / 360 + 100e6 * 0.056 * 7 / 360 - 200e6 * 0.053 / 360 - 120e6 * 0.0535 * 7 / 360, 2)
assert r["net_carry"] == exp, f"net_carry = {r['net_carry']}, expected {exp}"
''')],
hints=["Weighted average = sum(cash x rate) / sum(cash) per side", "interest = cash x rate x days / 360"],
wrong=r'''
def repo_book(book):
    rep = [r for s, c, r, d in book if s == "REPO"]; rev = [r for s, c, r, d in book if s == "REVREPO"]
    return {"borrow_wa": round(sum(rep) / len(rep), 5), "lend_wa": round(sum(rev) / len(rev), 5), "net_carry": 0.0}
''', difficulty=2),
ex("6. VaR, ES and limit breach", r'''
`PNL` is a 500-scenario P&L vector for the book. Compute 99% historical `var99` (course convention, positive), 97.5% `es975` (mean of the worst ceil(N x 2.5%) outcomes, positive; round before ceil), and `breach` = True if **either** var99 > `VAR_LIMIT` or es975 > `ES_LIMIT`.
''', r'''
import math
import numpy as np
rng = np.random.default_rng(3)
PNL = rng.standard_t(4, 500) * 400_000
VAR_LIMIT, ES_LIMIT = 1_500_000, 1_500_000
var99 = ...
es975 = ...
breach = ...
print(f"{var99:,.0f} {es975:,.0f} {breach}")
''', r'''
import math
import numpy as np
rng = np.random.default_rng(3)
PNL = rng.standard_t(4, 500) * 400_000
VAR_LIMIT, ES_LIMIT = 1_500_000, 1_500_000
var99 = float(-np.percentile(PNL, 1))
k = math.ceil(round(len(PNL) * (1 - 0.975), 9))
es975 = float(-np.sort(PNL)[:k].mean())
breach = bool(var99 > VAR_LIMIT or es975 > ES_LIMIT)
print(f"{var99:,.0f} {es975:,.0f} {breach}")
''', [("var", r'''assert _close(var99, -np.percentile(PNL, 1)), f"var99 = {var99:,.0f}"'''),
("es", r'''assert _close(es975, -np.sort(PNL)[:13].mean()), f"es975 = {es975:,.0f}; expected the mean of the worst 13 of 500"'''),
("breach", r'''
exp = (-np.percentile(PNL, 1) > VAR_LIMIT) or (-np.sort(PNL)[:13].mean() > ES_LIMIT)
assert breach == exp, f"breach = {breach}"
''')],
hints=["-np.percentile(PNL, 1)", "k = ceil(round(500 x 0.025, 9)) = 13"],
wrong=r'''
import numpy as np
rng = np.random.default_rng(3)
PNL = rng.standard_t(4, 500) * 400_000
VAR_LIMIT, ES_LIMIT = 1_500_000, 1_500_000
var99 = float(np.percentile(PNL, 99))
es975 = var99
breach = var99 > VAR_LIMIT
''', difficulty=2),
ex("7. Merge trading halts", r'''
Given halts per symbol as `(symbol, start_min, end_min)` (minutes since midnight, may overlap), return a dict **symbol -> total halted minutes** (merged, no double counting) and the symbol with the most halted time as `worst` (ties: alphabetical). Return `(totals, worst)`.
''', r'''
def halt_summary(halts):
    ...

H = [("ES", 600, 605), ("ES", 603, 610), ("CL", 700, 715), ("ES", 800, 803), ("CL", 710, 712), ("ZN", 900, 913)]
print(halt_summary(H))
''', r'''
def halt_summary(halts):
    by_sym = {}
    for s, a, b in halts:
        by_sym.setdefault(s, []).append((a, b))
    totals = {}
    for s, ivs in by_sym.items():
        total, cur = 0, None
        for a, b in sorted(ivs):
            if cur and a <= cur[1]:
                cur[1] = max(cur[1], b)
            else:
                if cur:
                    total += cur[1] - cur[0]
                cur = [a, b]
        totals[s] = total + (cur[1] - cur[0])
    worst = min(totals, key=lambda s: (-totals[s], s)) if totals else None
    return totals, worst

H = [("ES", 600, 605), ("ES", 603, 610), ("CL", 700, 715), ("ES", 800, 803), ("CL", 710, 712), ("ZN", 900, 913)]
print(halt_summary(H))
''', [("totals", r'''
t, w = halt_summary(H)
assert t == {"ES": 13, "CL": 15, "ZN": 13}, f"totals = {t}: merge overlaps within each symbol"
assert w == "CL", f"worst = {w}"
'''), ("ties & empty", r'''
assert halt_summary([("B", 0, 5), ("A", 10, 15)])[1] == "A"
assert halt_summary([]) == ({}, None)
''')],
hints=["Group intervals by symbol, then merge each group.", "worst = min(totals, key=lambda s: (-totals[s], s))"],
wrong=r'''
def halt_summary(halts):
    t = {}
    for s, a, b in halts:
        t[s] = t.get(s, 0) + (b - a)
    return t, max(t, key=t.get) if t else None
''', difficulty=3),
ex("8. Contagion within two hops", r'''
`EXPOSURES` lists directed credit exposures `(lender, borrower, amount)`: the lender loses `amount` if the borrower defaults. If `DEFAULTER` fails, find every entity that lends to it **directly or through one intermediary** (i.e. within 2 hops following edges backwards from the defaulter). Return a sorted list of `(entity, hops)`, sorted by hops then name.
''', r'''
from collections import defaultdict, deque
EXPOSURES = [("BANK-A", "KESTREL", 50), ("HF-1", "BANK-A", 20), ("MMF-1", "KESTREL", 10),
             ("PENSION", "HF-1", 5), ("HF-2", "MMF-1", 8), ("BANK-B", "HF-9", 30)]
DEFAULTER = "KESTREL"

def contagion(exposures, defaulter, max_hops=2):
    ...

print(contagion(EXPOSURES, DEFAULTER))
''', r'''
from collections import defaultdict, deque
EXPOSURES = [("BANK-A", "KESTREL", 50), ("HF-1", "BANK-A", 20), ("MMF-1", "KESTREL", 10),
             ("PENSION", "HF-1", 5), ("HF-2", "MMF-1", 8), ("BANK-B", "HF-9", 30)]
DEFAULTER = "KESTREL"

def contagion(exposures, defaulter, max_hops=2):
    lenders_to = defaultdict(list)          # borrower -> lenders
    for lender, borrower, _ in exposures:
        lenders_to[borrower].append(lender)
    dist = {defaulter: 0}
    q = deque([defaulter])
    while q:
        n = q.popleft()
        if dist[n] == max_hops:
            continue
        for l in lenders_to[n]:
            if l not in dist:
                dist[l] = dist[n] + 1
                q.append(l)
    return sorted(((e, h) for e, h in dist.items() if e != defaulter), key=lambda t: (t[1], t[0]))

print(contagion(EXPOSURES, DEFAULTER))
''', [("two hops", r'''
r = contagion(EXPOSURES, DEFAULTER)
assert r == [("BANK-A", 1), ("MMF-1", 1), ("HF-1", 2), ("HF-2", 2)], f"got {r}" + (": PENSION is 3 hops away" if any(e == "PENSION" for e, _ in r) else "")
'''), ("direction matters", r'''
r = contagion([("A", "B", 1)], "A")
assert r == [], "A lends to B; if A defaults, B isn't hurt (edges point lender -> borrower)"
''')],
hints=["Build borrower -> [lenders] and BFS from the defaulter.", "Stop expanding at max_hops."],
wrong=r'''
def contagion(exposures, defaulter, max_hops=2):
    out = set()
    for l, b, _ in exposures:
        if b == defaulter or l == defaulter:
            out.add((l if b == defaulter else b, 1))
    return sorted(out, key=lambda t: (t[1], t[0]))
''', difficulty=3),
])
