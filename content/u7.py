from dsl import *

HIST = r'''import numpy as np
rng = np.random.default_rng(2026)
# 500 days of synthetic daily returns for ES, NQ, CL, ZN (fat-ish tails via Student-t)
C = np.array([[1, .9, .25, -.35], [.9, 1, .2, -.3], [.25, .2, 1, -.1], [-.35, -.3, -.1, 1]])
Z = rng.standard_t(4, size=(500, 4)) / np.sqrt(2)
R = Z @ np.linalg.cholesky(C).T * np.array([.011, .014, .021, .0045])
EXPOSURE = np.array([34.74e6, -16.08e6, -18.28e6, 88.50e6])   # $ exposure per product'''

unit("u7", "Market Risk: VaR, ES, Stress & Limits", "Historical and parametric VaR, expected shortfall, stress testing, large-trader and concentration limits, and Black-76 greeks for options on futures.")

lesson("u7l1", "Historical VaR",
"Compute a client's 1-day 99% historical VaR from 500 days of scenario returns — the number in every prime risk report.",
r'''
**Value at Risk (VaR)** at confidence c over horizon h: the loss that is exceeded only (1 − c) of the time.

**Historical simulation** (no distribution assumption):
1. Take N historical daily returns per risk factor (e.g. 500 days).
2. Apply each day's returns to **today's** exposures → N hypothetical P&Ls: `pnl = R @ exposure`.
3. VaR = −(the (1 − c) quantile of P&L). With numpy: `-np.percentile(pnl, 1)` for 99%.

Quantile conventions differ (interpolated percentile vs "the 5th worst of 500") — state yours. We use `np.percentile` default (linear interpolation).

Report VaR as a **positive** loss number. Scale to h days with √h (assumes i.i.d. returns — a simplification).

Strengths: captures fat tails and real correlations. Weaknesses: only as good as the window (a calm 2-year window misses 2020/2008), and it says nothing about *how bad* beyond the VaR — that's expected shortfall.
''',
examples=[("Historical VaR in 4 lines", HIST + r'''

pnl = R @ EXPOSURE
var99 = -np.percentile(pnl, 1)
print(f"1-day 99% VaR: ${var99:,.0f}")
print(f"10-day (sqrt-time): ${var99 * np.sqrt(10):,.0f}")
print("worst 5 days:", np.sort(pnl)[:5].round(-3))
''')],
quiz=[q("99% 1-day VaR = $2m means…", ["Max possible loss is $2m", "On ~1 day in 100 the loss is expected to exceed $2m", "Average loss is $2m", "You'll lose $2m tomorrow"], 1, "VaR is a quantile, not a worst case: losses beyond it happen ~1% of days and can be much larger.")],
exercises=[
ex("hist_var()", r'''
Write `hist_var(pnl, conf=0.99)` returning VaR as a **positive** number using `np.percentile(pnl, (1 − conf) × 100)`. Then compute `var99` and `var95` for the portfolio P&L.
''', HIST + r'''

def hist_var(pnl, conf=0.99):
    ...

pnl = R @ EXPOSURE
var99 = ...
var95 = ...
print(f"{var99:,.0f} {var95:,.0f}")
''', HIST + r'''

def hist_var(pnl, conf=0.99):
    return -np.percentile(pnl, (1 - conf) * 100)

pnl = R @ EXPOSURE
var99 = hist_var(pnl, 0.99)
var95 = hist_var(pnl, 0.95)
print(f"{var99:,.0f} {var95:,.0f}")
''', [("hist_var sign & quantile", r'''
import numpy as np
x = np.arange(-50, 50)            # 100 P&Ls
r = hist_var(x, 0.99)
assert r > 0, f"VaR should be reported as a positive loss; got {r}"
assert _close(r, -np.percentile(x, 1)), f"hist_var = {r}; expected {-np.percentile(x, 1)} — use the 1st percentile for 99%"
'''), ("portfolio VaR", r'''
import numpy as np
p = R @ EXPOSURE
assert _close(var99, -np.percentile(p, 1)), f"var99 = {var99:,.0f}; expected {-np.percentile(p, 1):,.0f} (pnl = R @ EXPOSURE)"
assert _close(var95, -np.percentile(p, 5)) and var95 < var99, "var95 should be smaller than var99"
''')], hints=["np.percentile(pnl, 1) is the 1% quantile (a negative number)", "Flip the sign to report a positive loss."],
wrong=HIST + r'''
def hist_var(pnl, conf=0.99):
    return np.percentile(pnl, conf * 100)
pnl = R @ EXPOSURE
var99 = hist_var(pnl, 0.99); var95 = hist_var(pnl, 0.95)
'''),
ex("VaR by account & diversification", r'''
Three accounts hold the exposures in `ACCTS` (rows = accounts, columns = products). Compute:
- `acct_var`: dict account → 99% historical VaR
- `firm_var`: VaR of the **combined** book
- `div_benefit` = Σ account VaRs − firm VaR (≥ 0 usually)
''', HIST + r'''
import pandas as pd
ACCTS = pd.DataFrame({"ES": [34.74e6, -17.37e6, 4.34e6], "NQ": [-16.08e6, 0, 0], "CL": [-18.28e6, 0, 6.58e6], "ZN": [0, 88.50e6, -16.59e6]},
                     index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])
acct_var = ...
firm_var = ...
div_benefit = ...
''', HIST + r'''
import pandas as pd
ACCTS = pd.DataFrame({"ES": [34.74e6, -17.37e6, 4.34e6], "NQ": [-16.08e6, 0, 0], "CL": [-18.28e6, 0, 6.58e6], "ZN": [0, 88.50e6, -16.59e6]},
                     index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])
acct_var = {a: -np.percentile(R @ row.values, 1) for a, row in ACCTS.iterrows()}
firm_var = -np.percentile(R @ ACCTS.sum().values, 1)
div_benefit = sum(acct_var.values()) - firm_var
''', [("acct_var", r'''
import numpy as np
for a, row in ACCTS.iterrows():
    exp = -np.percentile(R @ row.values, 1)
    assert _close(acct_var[a], exp), f"{a} VaR = {acct_var[a]:,.0f}; expected {exp:,.0f}"
'''), ("firm & diversification", r'''
import numpy as np
exp = -np.percentile(R @ ACCTS.sum().values, 1)
assert _close(firm_var, exp), f"firm_var = {firm_var:,.0f}; expected {exp:,.0f} — sum exposures across accounts FIRST, then compute VaR" + (" (VaR isn't additive)" if _close(firm_var, sum(acct_var.values())) else "")
assert _close(div_benefit, sum(acct_var.values()) - exp) and div_benefit > 0
''')], hints=["ACCTS.iterrows() yields (account, row)", "Firm exposure = ACCTS.sum() (sum down the rows)"],
wrong=HIST + r'''
import pandas as pd
ACCTS = pd.DataFrame({"ES": [34.74e6, -17.37e6, 4.34e6], "NQ": [-16.08e6, 0, 0], "CL": [-18.28e6, 0, 6.58e6], "ZN": [0, 88.50e6, -16.59e6]}, index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])
acct_var = {a: -np.percentile(R @ row.values, 1) for a, row in ACCTS.iterrows()}
firm_var = sum(acct_var.values())
div_benefit = 0.0
'''),
])

lesson("u7l2", "Parametric (variance-covariance) VaR",
"Compute a fast parametric VaR from vols and correlations — and know when it understates risk.",
r'''
Assume portfolio P&L is **normal** with mean ≈ 0 and st.dev σₚ:

VaR = z_c × σₚ × √h,  σₚ = √(xᵀ Σ x)

| c | z |
|---|---|
| 95% | 1.645 |
| 99% | 2.326 |
| 97.5% | 1.960 |

Get z without scipy: `from statistics import NormalDist; NormalDist().inv_cdf(0.99)` → 2.3263.

Fast, smooth, easy to decompose (component VaR). But real returns have **fat tails**: with Student-t-like data, parametric 99% VaR is usually *below* historical VaR. Options (non-linear) break it too — use delta-gamma or full revaluation.
''',
examples=[("z-scores", r'''
from statistics import NormalDist
for c in [0.95, 0.975, 0.99, 0.999]:
    print(c, round(NormalDist().inv_cdf(c), 4))
''')],
quiz=[q("Daily $ vol of a book is $1.0m. 99% 10-day parametric VaR ≈", ["$2.33m", "$7.36m", "$23.3m", "$10m"], 1, "2.326 × 1.0m × √10 ≈ $7.36m.")],
exercises=[
ex("param_var()", r'''
Write `param_var(exposure, cov, conf=0.99, horizon=1)` = z × √(xᵀΣx) × √horizon using `NormalDist`. `exposure` is a numpy array, `cov` a covariance matrix of daily returns.
''', HIST + r'''
from statistics import NormalDist

def param_var(exposure, cov, conf=0.99, horizon=1):
    ...

cov = np.cov(R, rowvar=False)
print(f"{param_var(EXPOSURE, cov):,.0f}")
''', HIST + r'''
from statistics import NormalDist

def param_var(exposure, cov, conf=0.99, horizon=1):
    z = NormalDist().inv_cdf(conf)
    return z * np.sqrt(exposure @ cov @ exposure) * np.sqrt(horizon)

cov = np.cov(R, rowvar=False)
print(f"{param_var(EXPOSURE, cov):,.0f}")
''', [("1-day 99%", r'''
import numpy as np
from statistics import NormalDist
cov = np.cov(R, rowvar=False)
exp = NormalDist().inv_cdf(0.99) * np.sqrt(EXPOSURE @ cov @ EXPOSURE)
got = param_var(EXPOSURE, cov)
assert _close(got, exp), f"got {got:,.0f}; expected {exp:,.0f}" + (" — z × sigma, where sigma = sqrt(x' Σ x)" if _close(got, exp**2 / NormalDist().inv_cdf(0.99)) else "")
'''), ("horizon & conf", r'''
import numpy as np
from statistics import NormalDist
cov = np.cov(R, rowvar=False)
base = np.sqrt(EXPOSURE @ cov @ EXPOSURE)
assert _close(param_var(EXPOSURE, cov, 0.95, 10), NormalDist().inv_cdf(0.95) * base * np.sqrt(10)), "10-day scales by sqrt(10); 95% uses z = 1.645"
''')], hints=["z = NormalDist().inv_cdf(conf)", "sigma = np.sqrt(exposure @ cov @ exposure)"],
wrong=HIST + r'''
def param_var(exposure, cov, conf=0.99, horizon=1):
    return 2.326 * np.sqrt(exposure @ cov @ exposure) * horizon
'''),
ex("Parametric vs historical", r'''
Compute `hist99` (historical 99% VaR of `R @ EXPOSURE`), `param99` (parametric, using the sample covariance of R), and `ratio` = hist99 / param99. Then `fat_tails` = True if ratio > 1.
''', HIST + r'''
from statistics import NormalDist
hist99 = ...
param99 = ...
ratio = ...
fat_tails = ...
print(hist99, param99, ratio)
''', HIST + r'''
from statistics import NormalDist
pnl = R @ EXPOSURE
hist99 = -np.percentile(pnl, 1)
cov = np.cov(R, rowvar=False)
param99 = NormalDist().inv_cdf(0.99) * np.sqrt(EXPOSURE @ cov @ EXPOSURE)
ratio = hist99 / param99
fat_tails = bool(ratio > 1)
print(hist99, param99, ratio)
''', [("values", r'''
import numpy as np
from statistics import NormalDist
h = -np.percentile(R @ EXPOSURE, 1); p = NormalDist().inv_cdf(0.99) * np.sqrt(EXPOSURE @ np.cov(R, rowvar=False) @ EXPOSURE)
assert _close(hist99, h) and _close(param99, p), f"hist99 {hist99:,.0f} vs {h:,.0f}; param99 {param99:,.0f} vs {p:,.0f}"
'''), ("ratio & flag", r'''
assert _close(ratio, hist99 / param99) and fat_tails == (ratio > 1), f"ratio = {ratio}, fat_tails = {fat_tails}"
''')], hints=["Reuse your formulas from the two previous exercises."],
wrong=HIST + r'''
from statistics import NormalDist
hist99 = -np.percentile(R @ EXPOSURE, 1)
param99 = NormalDist().inv_cdf(0.99) * np.std(R @ EXPOSURE) ** 2
ratio = hist99 / param99
fat_tails = False
'''),
])

lesson("u7l3", "Expected shortfall (CVaR)",
"Report how bad losses are *beyond* VaR — the measure FRTB and most CCP models now favor.",
r'''
**Expected shortfall (ES)** at c = the **average loss in the worst (1 − c) of scenarios**. With N scenarios, average the worst k = ⌈N × (1 − c)⌉ outcomes (robust even when many P&Ls are tied):

```python
k = math.ceil(round(len(pnl) * (1 - c), 9))
es = -np.sort(pnl)[:k].mean()
```

- ES ≥ VaR always (it averages the tail beyond VaR).
- ES is **subadditive** (coherent): ES(A + B) ≤ ES(A) + ES(B). VaR can violate this.
- Basel **FRTB** replaced 99% VaR with **97.5% ES**; CME's SPAN 2 and many CCP models use historical VaR/ES-style measures with stress periods.

**Floating-point gotcha:** `1 - 0.95` is `0.050000000000000044`, so `100 * (1 - 0.95)` is slightly above 5 and `ceil` gives 6. Round first: `math.ceil(round(N * (1 - c), 9))`.

With 500 scenarios, 97.5% ES averages ~13 worst days — noisy. Mention that in any report: tail estimates have wide error bars.
''',
examples=[("VaR vs ES", HIST + r'''

pnl = R @ EXPOSURE
import math
for c in [0.99, 0.975]:
    k = math.ceil(round(len(pnl) * (1 - c), 9))
    print(f"{c:.1%}  VaR {-np.percentile(pnl, (1 - c) * 100):>12,.0f}   ES {-np.sort(pnl)[:k].mean():>12,.0f}   tail days {k}")
''')],
quiz=[q("Which statement is true?", ["ES ≤ VaR", "ES ≥ VaR at the same confidence", "ES ignores the tail", "ES = VaR for all distributions"], 1, "ES averages losses at or beyond the VaR threshold, so it's at least as large.")],
exercises=[
ex("expected_shortfall()", r'''
Write `expected_shortfall(pnl, conf=0.975)` returning a positive number: minus the mean of the worst k = ⌈N × (1 − conf)⌉ P&Ls.
''', HIST + r'''

def expected_shortfall(pnl, conf=0.975):
    ...

pnl = R @ EXPOSURE
print(f"{expected_shortfall(pnl):,.0f}")
''', HIST + r'''

import math

def expected_shortfall(pnl, conf=0.975):
    pnl = np.sort(np.asarray(pnl, dtype=float))
    k = math.ceil(round(len(pnl) * (1 - conf), 9))
    return -pnl[:k].mean()

pnl = R @ EXPOSURE
print(f"{expected_shortfall(pnl):,.0f}")
''', [("simple case", r'''
import numpy as np
x = np.array([-100, -50, -10, 0, 5, 10, 20, 30, 40, 50] * 10, dtype=float)
got = expected_shortfall(x, 0.9)
assert _close(got, 100.0), f"worst 10% of these 100 values are all −100 → ES 100; got {got}"
'''), ("portfolio", r'''
import numpy as np
p = R @ EXPOSURE; t = np.percentile(p, 2.5); exp = -np.sort(p)[:13].mean()
got = expected_shortfall(p)
assert _close(got, exp), f"ES = {got:,.0f}; expected {exp:,.0f} (mean of the worst 13 of 500)" + (" — that's VaR, not the average beyond it" if _close(got, -t) else "")
'''), ("ES ≥ VaR", r'''
import numpy as np
p = R @ EXPOSURE
assert expected_shortfall(p, 0.99) >= -np.percentile(p, 1)
''')], hints=["k = math.ceil(round(len(pnl) * (1 - conf), 9))  (round guards against float error)", "-np.sort(pnl)[:k].mean()"],
wrong=HIST + r'''
def expected_shortfall(pnl, conf=0.975):
    return -np.percentile(pnl, (1 - conf) * 100)
'''),
ex("Subadditivity check", r'''
Two desks A and B have P&L vectors `a` and `b` (a toy example with rare defaults). Compute 95% `var_a, var_b, var_ab` (historical, VaR of a+b) and the same for ES (`es_a, es_b, es_ab`). Then set `var_subadditive = var_ab <= var_a + var_b` and `es_subadditive` likewise.
''', r'''
import numpy as np
# 100 scenarios: each desk loses 100 in a different 4 scenarios (4% probability each), else earns 1
a = np.ones(100); a[[3, 17, 42, 88]] = -100
b = np.ones(100); b[[9, 25, 61, 77]] = -100
def hvar(x, c): return -np.percentile(x, (1 - c) * 100)
def es(x, c):
    k = int(np.ceil(round(len(x) * (1 - c), 9))); return -np.sort(x)[:k].mean()
var_a = var_b = var_ab = None
es_a = es_b = es_ab = None
var_subadditive = es_subadditive = None
''', r'''
import numpy as np
a = np.ones(100); a[[3, 17, 42, 88]] = -100
b = np.ones(100); b[[9, 25, 61, 77]] = -100
def hvar(x, c): return -np.percentile(x, (1 - c) * 100)
def es(x, c):
    k = int(np.ceil(round(len(x) * (1 - c), 9))); return -np.sort(x)[:k].mean()
var_a, var_b, var_ab = hvar(a, .95), hvar(b, .95), hvar(a + b, .95)
es_a, es_b, es_ab = es(a, .95), es(b, .95), es(a + b, .95)
var_subadditive = bool(var_ab <= var_a + var_b)
es_subadditive = bool(es_ab <= es_a + es_b)
''', [("VaR breaks subadditivity here", r'''
assert var_a is not None and _close(var_a, -1.0) and _close(var_ab, 99.0), f"var_a = {var_a}, var_ab = {var_ab}: each desk's 4%-probability loss is rarer than the 5% cutoff, so its 95% VaR doesn't see it (VaR = −1, a gain!); combined, the 8% loss probability puts −99 at the 5th percentile"
assert var_subadditive is False, "VaR(A+B) = 99 > VaR(A)+VaR(B) = −2 → VaR is NOT subadditive in this example"
'''), ("ES is subadditive", r'''
assert es_subadditive is True and es_ab <= es_a + es_b, f"es_a {es_a}, es_b {es_b}, es_ab {es_ab}"
''')], hints=["Just call hvar(...) and es(...) with c = 0.95; compare with <=."],
wrong=r'''
import numpy as np
a = np.ones(100); a[[3, 17, 42, 88]] = -100
b = np.ones(100); b[[9, 25, 61, 77]] = -100
var_a = var_b = 80.2; var_ab = 99.0
es_a = es_b = 100.0; es_ab = 100.0
var_subadditive = True; es_subadditive = True
'''),
])

lesson("u7l4", "Stress testing",
"Apply named stress scenarios to every account and rank who loses most relative to their collateral.",
r'''
VaR describes "normal bad days". **Stress tests** ask "what if *this* happens?":

- **Historical**: replay a real episode (e.g. Mar-2020 dash for cash, Oct-1987, 2022 gilt/LDI crisis).
- **Hypothetical**: designed shocks ("ES −12%, vol +20 pts, UST 10y −40 bp, crude −30%").
- **Reverse stress**: what shock would wipe out this client's collateral?

Mechanics are just matrix math: **scenario shocks (% moves) × exposures ($)** → stress P&L per account per scenario. Then compare the worst loss to the account's **collateral/excess** — stress loss > excess means the account would be under water.

The shocks below are **synthetic** and illustrative, not calibrated to real events.
''',
examples=[("Shock × exposure", r'''
import pandas as pd
shocks = pd.DataFrame({"ES": [-0.12, 0.05], "CL": [-0.30, 0.15]}, index=["crash", "oil_spike"])
expo = pd.DataFrame({"ES": [34.7e6, -17.4e6], "CL": [-18.3e6, 6.6e6]}, index=["HF-A", "HF-B"])
print((expo @ shocks.T).round(-3))   # accounts × scenarios
''')],
quiz=[q("An account's worst stress loss is $12m and its collateral excess is $4m. Interpretation?", ["It's fine", "Under that scenario it would be ~$8m under-collateralized — a credit exposure for the PB/FCM", "It must be closed today", "VaR is wrong"], 1, "Stress loss beyond excess = potential uncovered loss; that drives house margin add-ons and limit discussions.")],
exercises=[
ex("Stress matrix", r'''
Compute `stress` = DataFrame of stress P&L (rows = accounts, columns = scenarios) using matrix multiplication, then `worst` = DataFrame with columns `worst_scenario` and `worst_loss` (positive number) per account.
''', r'''
import pandas as pd
SHOCKS = pd.DataFrame({
    "ES": [-0.12, -0.05, 0.04, -0.20], "NQ": [-0.15, -0.06, 0.06, -0.25],
    "CL": [-0.30, 0.25, -0.10, -0.40], "ZN": [0.025, -0.03, -0.01, 0.04]},
    index=["equity_crash", "stagflation", "soft_landing", "gfc_style"])
EXPO = pd.DataFrame({"ES": [34.74e6, -17.37e6, 4.34e6], "NQ": [-16.08e6, 0, 0], "CL": [-18.28e6, 0, 6.58e6], "ZN": [0, 88.50e6, -16.59e6]},
                    index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])
stress = ...
worst = ...
print(stress.round(-3))
''', r'''
import pandas as pd
SHOCKS = pd.DataFrame({
    "ES": [-0.12, -0.05, 0.04, -0.20], "NQ": [-0.15, -0.06, 0.06, -0.25],
    "CL": [-0.30, 0.25, -0.10, -0.40], "ZN": [0.025, -0.03, -0.01, 0.04]},
    index=["equity_crash", "stagflation", "soft_landing", "gfc_style"])
EXPO = pd.DataFrame({"ES": [34.74e6, -17.37e6, 4.34e6], "NQ": [-16.08e6, 0, 0], "CL": [-18.28e6, 0, 6.58e6], "ZN": [0, 88.50e6, -16.59e6]},
                    index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])
stress = EXPO @ SHOCKS.T
worst = pd.DataFrame({"worst_scenario": stress.idxmin(axis=1), "worst_loss": -stress.min(axis=1)})
print(stress.round(-3))
''', [("stress", r'''
assert stress.shape == (3, 4) and list(stress.columns) == list(SHOCKS.index), "stress should be accounts × scenarios: EXPO @ SHOCKS.T"
assert _close(stress.loc["HF-ALPHA", "equity_crash"], -12_000.0 * 0 + (34.74e6 * -0.12 + -16.08e6 * -0.15 + -18.28e6 * -0.30)), f"HF-ALPHA equity_crash = {stress.loc['HF-ALPHA','equity_crash']:,.0f}"
'''), ("worst", r'''
w = worst
assert w.loc["HF-BETA", "worst_scenario"] == "stagflation" and _close(w.loc["HF-BETA", "worst_loss"], 1_786_500), f"HF-BETA worst = {dict(w.loc['HF-BETA'])}"
assert w.loc["FO-GAMMA", "worst_scenario"] == "gfc_style" and _close(w.loc["FO-GAMMA", "worst_loss"], 4_163_600), f"FO-GAMMA worst = {dict(w.loc['FO-GAMMA'])}"
assert (w["worst_loss"] > 0).all(), "worst_loss should be positive"
''')], hints=["EXPO @ SHOCKS.T aligns product columns", "stress.idxmin(axis=1), -stress.min(axis=1)"],
wrong=r'''
import pandas as pd
SHOCKS = pd.DataFrame({"ES": [-0.12, -0.05, 0.04, -0.20], "NQ": [-0.15, -0.06, 0.06, -0.25], "CL": [-0.30, 0.25, -0.10, -0.40], "ZN": [0.025, -0.03, -0.01, 0.04]}, index=["equity_crash", "stagflation", "soft_landing", "gfc_style"])
EXPO = pd.DataFrame({"ES": [34.74e6, -17.37e6, 4.34e6], "NQ": [-16.08e6, 0, 0], "CL": [-18.28e6, 0, 6.58e6], "ZN": [0, 88.50e6, -16.59e6]}, index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])
stress = EXPO.abs() @ SHOCKS.T
worst = pd.DataFrame({"worst_scenario": stress.idxmax(axis=1), "worst_loss": stress.max(axis=1)})
'''),
ex("Stress vs excess", r'''
Join `worst` with each account's collateral `excess` and compute `uncovered` = max(0, worst_loss − excess). Return `flagged`: list of accounts with uncovered > 0, sorted by uncovered descending.
''', r'''
import pandas as pd
worst = pd.DataFrame({"worst_scenario": ["gfc_style", "stagflation", "gfc_style"], "worst_loss": [5_386_000.0, 1_786_500.0, 4_163_600.0]},
                     index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])
excess = pd.Series({"HF-ALPHA": 6_000_000.0, "HF-BETA": 900_000.0, "FO-GAMMA": 1_500_000.0})
flagged = ...
''', r'''
import pandas as pd
worst = pd.DataFrame({"worst_scenario": ["gfc_style", "stagflation", "gfc_style"], "worst_loss": [5_386_000.0, 1_786_500.0, 4_163_600.0]},
                     index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])
excess = pd.Series({"HF-ALPHA": 6_000_000.0, "HF-BETA": 900_000.0, "FO-GAMMA": 1_500_000.0})
df = worst.assign(excess=excess)
df["uncovered"] = (df["worst_loss"] - df["excess"]).clip(lower=0)
flagged = df[df["uncovered"] > 0].sort_values("uncovered", ascending=False).index.tolist()
''', [("flagged", r'''assert flagged == ["FO-GAMMA", "HF-BETA"], f"flagged = {flagged}; FO-GAMMA uncovered 2.66m, HF-BETA 0.89m, HF-ALPHA covered"''')],
hints=["worst.assign(excess=excess) aligns on the index", "(worst_loss − excess).clip(lower=0)"],
wrong=r'''
import pandas as pd
worst = pd.DataFrame({"worst_scenario": ["gfc_style", "stagflation", "gfc_style"], "worst_loss": [5_386_000.0, 1_786_500.0, 4_163_600.0]}, index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])
flagged = worst.sort_values("worst_loss", ascending=False).index.tolist()
'''),
])

lesson("u7l5", "Large-trader & concentration limits",
"Monitor positions against CFTC reportable levels, open-interest concentration and house limits — daily compliance and risk work at an FCM.",
r'''
Three kinds of position checks run daily at an FCM / clearing risk team:

1. **Regulatory reporting levels** — the CFTC large-trader program (17 CFR Part 15) requires FCMs to report accounts at/above a **reportable level** per contract (e.g. hundreds or a few thousand contracts, set per product). Always check the current table; the numbers used here are **illustrative**.
2. **Speculative position limits** — federal/exchange limits on spot-month and (for some) all-months positions; **accountability levels** trigger exchange inquiries.
3. **Concentration** — a position that's a large % of **open interest** can't be liquidated quickly; CCPs add concentration/liquidity add-ons (SPAN 2 does this explicitly). House limits often trigger at e.g. 5–10% of OI.

Positions are aggregated by **beneficial owner** across accounts ("aggregation rules") — splitting across accounts doesn't avoid limits.

Output: utilization = |position| / limit; status OK / WARN (≥ 80%) / BREACH (> 100%).
''',
examples=[("Aggregation across accounts", r'''
import pandas as pd
pos = pd.DataFrame({"owner": ["ALPHA", "ALPHA", "BETA"], "account": ["A1", "A2", "B1"], "symbol": ["ZC", "ZC", "ZC"], "qty": [3_000, 2_500, -900]})
print(pos.groupby(["owner", "symbol"])["qty"].sum())
''')],
quiz=[q("A client holds 600 lots of ZC in each of three accounts under the same beneficial owner; reportable level is 1,000 (illustrative). Reportable?", ["No — each account is under 1,000", "Yes — aggregated 1,800 ≥ 1,000", "Only one account", "Depends on price"], 1, "Reporting and limits apply to aggregated positions of the same owner.")],
exercises=[
ex("Reportable positions", r'''
Aggregate `pos` by owner and symbol (net qty), join `REPORTABLE` levels, and produce `reportable`: DataFrame of owner/symbol rows where |net qty| ≥ level, columns `owner, symbol, qty, level`, sorted by owner then symbol, index reset.
''', r'''
import pandas as pd
REPORTABLE = pd.DataFrame({"symbol": ["ES", "ZN", "CL", "ZC"], "level": [1_000, 2_000, 350, 250]})   # illustrative only
pos = pd.DataFrame({
    "owner":   ["ALPHA", "ALPHA", "ALPHA", "BETA", "BETA", "GAMMA", "GAMMA", "GAMMA"],
    "account": ["A1", "A2", "A1", "B1", "B1", "G1", "G2", "G2"],
    "symbol":  ["ES", "ES", "CL", "ZN", "ES", "ZC", "ZC", "CL"],
    "qty":     [700, 450, -250, 2_400, -60, 150, 120, 90]})
reportable = ...
print(reportable)
''', r'''
import pandas as pd
REPORTABLE = pd.DataFrame({"symbol": ["ES", "ZN", "CL", "ZC"], "level": [1_000, 2_000, 350, 250]})
pos = pd.DataFrame({
    "owner":   ["ALPHA", "ALPHA", "ALPHA", "BETA", "BETA", "GAMMA", "GAMMA", "GAMMA"],
    "account": ["A1", "A2", "A1", "B1", "B1", "G1", "G2", "G2"],
    "symbol":  ["ES", "ES", "CL", "ZN", "ES", "ZC", "ZC", "CL"],
    "qty":     [700, 450, -250, 2_400, -60, 150, 120, 90]})
agg = pos.groupby(["owner", "symbol"], as_index=False)["qty"].sum().merge(REPORTABLE, on="symbol", how="left")
reportable = agg[agg["qty"].abs() >= agg["level"]].sort_values(["owner", "symbol"]).reset_index(drop=True)[["owner", "symbol", "qty", "level"]]
print(reportable)
''', [("rows", r'''
got = list(zip(reportable["owner"], reportable["symbol"]))
assert got == [("ALPHA", "ES"), ("BETA", "ZN"), ("GAMMA", "ZC")], f"reportable = {got}" + (" — aggregate by owner across accounts first" if ("GAMMA", "ZC") not in got else "")
'''), ("qty", r'''assert reportable["qty"].tolist() == [1150, 2400, 270], f"qty = {reportable['qty'].tolist()}"''')],
hints=["pos.groupby(['owner', 'symbol'], as_index=False)['qty'].sum()", "merge with REPORTABLE, filter abs(qty) >= level"],
wrong=r'''
import pandas as pd
REPORTABLE = pd.DataFrame({"symbol": ["ES", "ZN", "CL", "ZC"], "level": [1_000, 2_000, 350, 250]})
pos = pd.DataFrame({"owner": ["ALPHA", "ALPHA", "ALPHA", "BETA", "BETA", "GAMMA", "GAMMA", "GAMMA"], "account": ["A1", "A2", "A1", "B1", "B1", "G1", "G2", "G2"], "symbol": ["ES", "ES", "CL", "ZN", "ES", "ZC", "ZC", "CL"], "qty": [700, 450, -250, 2_400, -60, 150, 120, 90]})
m = pos.merge(REPORTABLE, on="symbol")
reportable = m[m["qty"].abs() >= m["level"]].reset_index(drop=True)[["owner", "symbol", "qty", "level"]]
'''),
ex("Limit utilization & OI concentration", r'''
For each owner/symbol in `agg`, compute `util` = |qty| / house_limit, `oi_pct` = |qty| / open_interest, and `status`: `"BREACH"` if util > 1 **or** oi_pct > 0.10; `"WARN"` if util ≥ 0.8 or oi_pct > 0.05; else `"OK"`. Then `alerts` = DataFrame of non-OK rows sorted by util desc.
''', r'''
import numpy as np
import pandas as pd
agg = pd.DataFrame({"owner": ["ALPHA", "ALPHA", "BETA", "GAMMA", "GAMMA"], "symbol": ["ES", "CL", "ZN", "ZC", "CL"], "qty": [1150, -250, 2400, 270, 90]})
LIMITS = pd.DataFrame({"symbol": ["ES", "CL", "ZN", "ZC"], "house_limit": [1_500, 400, 5_000, 300], "open_interest": [2_100_000, 1_600_000, 4_500_000, 4_000]})
''', r'''
import numpy as np
import pandas as pd
agg = pd.DataFrame({"owner": ["ALPHA", "ALPHA", "BETA", "GAMMA", "GAMMA"], "symbol": ["ES", "CL", "ZN", "ZC", "CL"], "qty": [1150, -250, 2400, 270, 90]})
LIMITS = pd.DataFrame({"symbol": ["ES", "CL", "ZN", "ZC"], "house_limit": [1_500, 400, 5_000, 300], "open_interest": [2_100_000, 1_600_000, 4_500_000, 4_000]})
agg = agg.merge(LIMITS, on="symbol", how="left")
agg["util"] = agg["qty"].abs() / agg["house_limit"]
agg["oi_pct"] = agg["qty"].abs() / agg["open_interest"]
agg["status"] = np.select([(agg["util"] > 1) | (agg["oi_pct"] > 0.10), (agg["util"] >= 0.8) | (agg["oi_pct"] > 0.05)], ["BREACH", "WARN"], default="OK")
alerts = agg[agg["status"] != "OK"].sort_values("util", ascending=False)
''', [("status", r'''
s = dict(zip(agg["owner"] + " " + agg["symbol"], agg["status"]))
assert s["ALPHA ES"] == "OK" and s["BETA ZN"] == "OK", f"statuses = {s}"
'''), ("alerts", r'''
got = list(zip(alerts["owner"], alerts["symbol"], alerts["status"]))
assert got == [("GAMMA", "ZC", "WARN")], f"alerts = {got}; GAMMA ZC: util 0.90 (≥ 0.8) and 6.75% of OI (> 5%) → WARN"
''')], hints=["Merge LIMITS on symbol first.", "np.select([breach_cond, warn_cond], ['BREACH', 'WARN'], default='OK') — use | for 'or' with parentheses."],
wrong=r'''
import numpy as np
import pandas as pd
agg = pd.DataFrame({"owner": ["ALPHA", "ALPHA", "BETA", "GAMMA", "GAMMA"], "symbol": ["ES", "CL", "ZN", "ZC", "CL"], "qty": [1150, -250, 2400, 270, 90]})
LIMITS = pd.DataFrame({"symbol": ["ES", "CL", "ZN", "ZC"], "house_limit": [1_500, 400, 5_000, 300], "open_interest": [2_100_000, 1_600_000, 4_500_000, 4_000]})
agg = agg.merge(LIMITS, on="symbol", how="left")
agg["util"] = agg["qty"] / agg["house_limit"]
agg["oi_pct"] = agg["qty"] / agg["open_interest"]
agg["status"] = np.where(agg["util"] > 1, "BREACH", "OK")
alerts = agg[agg["status"] != "OK"]
'''),
])

lesson("u7l6", "Options on futures: Black-76 & greeks",
"Price options on futures and compute delta/gamma/vega so option positions can be expressed in futures-equivalents for risk and margin.",
r'''
Options on futures (e.g. ES options, OZN, LO on CL) are priced with **Black-76**:

d₁ = [ln(F/K) + σ²T/2] / (σ√T),  d₂ = d₁ − σ√T

Call = e^(−rT) [F·N(d₁) − K·N(d₂)],  Put = e^(−rT) [K·N(−d₂) − F·N(−d₁)]

Greeks (per option, in price units):
- **Delta** call = e^(−rT) N(d₁), put = −e^(−rT) N(−d₁) — futures-equivalents per option
- **Gamma** = e^(−rT) n(d₁) / (F σ √T)
- **Vega** = e^(−rT) F n(d₁) √T (per 1.00 vol; divide by 100 for per vol point)

N = normal CDF, n = normal PDF: `NormalDist().cdf(x)`, `NormalDist().pdf(x)`.

Position delta in futures-equivalent contracts = qty × delta (× option multiplier / futures multiplier if they differ). Note: many CME options on futures are futures-style or premium-paid with r ≈ discounting; using e^(−rT) is the standard Black-76 form.
''',
examples=[("ATM ES call", r'''
from math import log, sqrt, exp
from statistics import NormalDist
N = NormalDist().cdf
F, K, T, sigma, r = 5790.0, 5800.0, 30 / 365, 0.18, 0.053
d1 = (log(F / K) + 0.5 * sigma**2 * T) / (sigma * sqrt(T)); d2 = d1 - sigma * sqrt(T)
call = exp(-r * T) * (F * N(d1) - K * N(d2))
print(f"call {call:.2f} pts = ${call * 50:,.0f} per contract; delta {exp(-r*T)*N(d1):.3f}")
''')],
quiz=[q("A client is short 200 ES puts with delta −0.30 each. Futures-equivalent delta?", ["−60", "+60", "−200", "+200"], 1, "−200 × −0.30 = +60: short puts are long delta.")],
exercises=[
ex("black76()", r'''
Write `black76(F, K, T, sigma, r, kind="call")` returning the option price. Support `"call"` and `"put"`.
''', r'''
from math import log, sqrt, exp
from statistics import NormalDist
N = NormalDist().cdf

def black76(F, K, T, sigma, r, kind="call"):
    ...

print(black76(5790.0, 5800.0, 30 / 365, 0.18, 0.053))
''', r'''
from math import log, sqrt, exp
from statistics import NormalDist
N = NormalDist().cdf

def black76(F, K, T, sigma, r, kind="call"):
    d1 = (log(F / K) + 0.5 * sigma**2 * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    df = exp(-r * T)
    if kind == "call":
        return df * (F * N(d1) - K * N(d2))
    return df * (K * N(-d2) - F * N(-d1))

print(black76(5790.0, 5800.0, 30 / 365, 0.18, 0.053))
''', [("call", r'''
c = black76(5790.0, 5800.0, 30 / 365, 0.18, 0.053)
assert abs(c - 113.86) < 0.05, f"call = {c:.4f}; expected ≈ 113.86"
'''), ("put-call parity", r'''
from math import exp
F, K, T, s, r = 72.35, 70.0, 0.25, 0.35, 0.05
c = black76(F, K, T, s, r, "call"); p = black76(F, K, T, s, r, "put")
assert abs((c - p) - exp(-r * T) * (F - K)) < 1e-9, f"C − P should equal e^(−rT)(F − K); got {c - p:.6f} vs {exp(-r*T)*(F-K):.6f}"
''')], hints=["d1 = (ln(F/K) + σ²T/2) / (σ√T); d2 = d1 − σ√T", "Put = e^(−rT)(K·N(−d2) − F·N(−d1))"],
wrong=r'''
from math import log, sqrt, exp
from statistics import NormalDist
N = NormalDist().cdf
def black76(F, K, T, sigma, r, kind="call"):
    d1 = (log(F / K) + sigma**2 * T) / (sigma * sqrt(T)); d2 = d1 - sigma * sqrt(T)
    if kind == "call": return F * N(d1) - K * N(d2)
    return K * N(-d2) - F * N(-d1)
'''),
ex("Greeks & futures-equivalent delta", r'''
Write `greeks(F, K, T, sigma, r, kind)` returning a dict with `delta`, `gamma`, `vega` (vega per **1 vol point**, i.e. /100). Then compute `book_delta`: futures-equivalent delta of `book` (qty × delta, summed), rounded to 1 dp.
''', r'''
from math import log, sqrt, exp
from statistics import NormalDist
N, n = NormalDist().cdf, NormalDist().pdf

def greeks(F, K, T, sigma, r, kind="call"):
    ...

F, T, r = 5790.0, 30 / 365, 0.053
book = [  # (qty, strike, vol, kind)
    (-200, 5500.0, 0.22, "put"),
    (150, 6000.0, 0.15, "call"),
    (-40, 5800.0, 0.18, "call"),
]
book_delta = ...
print(book_delta)
''', r'''
from math import log, sqrt, exp
from statistics import NormalDist
N, n = NormalDist().cdf, NormalDist().pdf

def greeks(F, K, T, sigma, r, kind="call"):
    d1 = (log(F / K) + 0.5 * sigma**2 * T) / (sigma * sqrt(T))
    df = exp(-r * T)
    delta = df * N(d1) if kind == "call" else -df * N(-d1)
    gamma = df * n(d1) / (F * sigma * sqrt(T))
    vega = df * F * n(d1) * sqrt(T) / 100
    return {"delta": delta, "gamma": gamma, "vega": vega}

F, T, r = 5790.0, 30 / 365, 0.053
book = [
    (-200, 5500.0, 0.22, "put"),
    (150, 6000.0, 0.15, "call"),
    (-40, 5800.0, 0.18, "call"),
]
book_delta = round(sum(q * greeks(F, K, T, s, r, kind)["delta"] for q, K, s, kind in book), 1)
print(book_delta)
''', [("ATM call greeks", r'''
g = greeks(5790.0, 5800.0, 30 / 365, 0.18, 0.053, "call")
assert abs(g["delta"] - 0.4948) < 0.0005, f"delta = {g['delta']:.4f}; expected ≈ 0.4948 (remember the e^(−rT) discount)"
assert abs(g["gamma"] - 0.0013294) < 2e-6, f"gamma = {g['gamma']:.7f}"
assert abs(g["vega"] - 6.593) < 0.01, f"vega = {g['vega']:.3f} — per vol POINT (divide by 100)"
'''), ("put delta negative", r'''
g = greeks(5790.0, 5500.0, 30 / 365, 0.22, 0.053, "put")
assert g["delta"] < 0, f"put delta should be negative; got {g['delta']}"
'''), ("book_delta", r'''
assert abs(book_delta - 51.1) < 0.15, f"book_delta = {book_delta}; short puts add POSITIVE delta"
''')], hints=["Call delta = e^(−rT)N(d1); put = −e^(−rT)N(−d1)", "sum(q * greeks(...)['delta'] for q, K, s, kind in book)"],
wrong=r'''
from math import log, sqrt, exp
from statistics import NormalDist
N, n = NormalDist().cdf, NormalDist().pdf
def greeks(F, K, T, sigma, r, kind="call"):
    d1 = (log(F / K) + 0.5 * sigma**2 * T) / (sigma * sqrt(T))
    delta = N(d1) if kind == "call" else N(-d1)
    return {"delta": delta, "gamma": n(d1) / (F * sigma * sqrt(T)), "vega": F * n(d1) * sqrt(T)}
F, T, r = 5790.0, 30 / 365, 0.053
book = [(-200, 5500.0, 0.22, "put"), (150, 6000.0, 0.15, "call"), (-40, 5800.0, 0.18, "call")]
book_delta = round(sum(q * greeks(F, K, T, s, r, kind)["delta"] for q, K, s, kind in book), 1)
'''),
])

lesson("u7l7", "Take it to work: daily limit monitor & VaR/stress report",
"Combine VaR, ES, stress and limits into one daily risk-limit monitor with a clear breach list.",
r'''
A risk-limit framework per client typically includes:

| Metric | Example limit |
|---|---|
| 1-day 99% VaR | $5m |
| 97.5% ES | $7m |
| Worst stress loss | ≤ 150% of collateral excess |
| Concentration | ≤ 10% of OI |

The monitor computes each metric, its **utilization**, and a **status**; the report lists breaches first. Keep the logic in small pure functions (easy to test) and one orchestrator function that assembles the table — the same structure a Foundry pipeline or Airflow DAG would use.
''',
examples=[("Utilization table", r'''
import pandas as pd
m = pd.DataFrame({"metric": ["VaR99", "ES975"], "value": [4.2e6, 7.6e6], "limit": [5e6, 7e6]})
m["util"] = m["value"] / m["limit"]
print(m.assign(status=m["util"].map(lambda u: "BREACH" if u > 1 else "WARN" if u >= .8 else "OK")))
''')],
quiz=[q("Why keep metric calculations as small pure functions with an orchestrator on top?", ["Faster to type", "Each piece can be unit-tested and reused; the pipeline stays readable", "Python requires it", "It uses less memory"], 1, "Separation makes testing and change safe — exactly what reviewers look for.")],
exercises=[
ex("limit_monitor()", r'''
Write `limit_monitor(pnl_by_acct, limits)`:
- `pnl_by_acct`: dict account → numpy array of scenario P&Ls
- `limits`: DataFrame indexed by account with columns `var_limit`, `es_limit`
Return a DataFrame indexed by account with columns `var99, es975, var_util, es_util, status` where status = `"BREACH"` if any util > 1, `"WARN"` if any ≥ 0.8, else `"OK"`; sorted by the **max** of the two utils descending.
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(5)
PNL = {"HF-ALPHA": rng.standard_t(4, 500) * 1.1e6, "HF-BETA": rng.standard_t(4, 500) * 0.35e6, "FO-GAMMA": rng.standard_t(4, 500) * 0.6e6}
LIMITS = pd.DataFrame({"var_limit": [4.0e6, 2.0e6, 2.0e6], "es_limit": [5.5e6, 3.0e6, 2.6e6]}, index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])

def limit_monitor(pnl_by_acct, limits):
    ...

print(limit_monitor(PNL, LIMITS))
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(5)
PNL = {"HF-ALPHA": rng.standard_t(4, 500) * 1.1e6, "HF-BETA": rng.standard_t(4, 500) * 0.35e6, "FO-GAMMA": rng.standard_t(4, 500) * 0.6e6}
LIMITS = pd.DataFrame({"var_limit": [4.0e6, 2.0e6, 2.0e6], "es_limit": [5.5e6, 3.0e6, 2.6e6]}, index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])

def var(p, c): return -np.percentile(p, (1 - c) * 100)
def es(p, c):
    k = int(np.ceil(round(len(p) * (1 - c), 9))); return -np.sort(p)[:k].mean()

def limit_monitor(pnl_by_acct, limits):
    rows = {a: {"var99": var(p, .99), "es975": es(p, .975)} for a, p in pnl_by_acct.items()}
    df = pd.DataFrame(rows).T.join(limits)
    df["var_util"] = df["var99"] / df["var_limit"]
    df["es_util"] = df["es975"] / df["es_limit"]
    mx = df[["var_util", "es_util"]].max(axis=1)
    df["status"] = np.select([mx > 1, mx >= 0.8], ["BREACH", "WARN"], default="OK")
    return df.loc[mx.sort_values(ascending=False).index, ["var99", "es975", "var_util", "es_util", "status"]]

print(limit_monitor(PNL, LIMITS))
''', [("columns", r'''
m = limit_monitor(PNL, LIMITS)
assert list(m.columns) == ["var99", "es975", "var_util", "es_util", "status"], f"columns = {list(m.columns)}"
'''), ("metrics", r'''
import numpy as np
m = limit_monitor(PNL, LIMITS)
p = PNL["FO-GAMMA"]; t = np.percentile(p, 2.5)
assert _close(m.loc["FO-GAMMA", "var99"], -np.percentile(p, 1)), "var99 should be historical 99% VaR"
assert _close(m.loc["FO-GAMMA", "es975"], -np.sort(p)[:13].mean()), "es975 should be 97.5% ES (mean of the worst 13 of 500)"
'''), ("status & order", r'''
m = limit_monitor(PNL, LIMITS)
mx = m[["var_util", "es_util"]].max(axis=1)
assert list(mx) == sorted(mx, reverse=True), "sort by the max utilization descending"
for a, row in m.iterrows():
    u = max(row["var_util"], row["es_util"])
    exp = "BREACH" if u > 1 else "WARN" if u >= .8 else "OK"
    assert row["status"] == exp, f"{a}: max util {u:.2f} → {exp}, got {row['status']}"
''')], hints=["Build a dict of metrics per account → pd.DataFrame(rows).T", "mx = df[['var_util', 'es_util']].max(axis=1)"],
wrong=r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(5)
PNL = {"HF-ALPHA": rng.standard_t(4, 500) * 1.1e6, "HF-BETA": rng.standard_t(4, 500) * 0.35e6, "FO-GAMMA": rng.standard_t(4, 500) * 0.6e6}
LIMITS = pd.DataFrame({"var_limit": [4.0e6, 2.0e6, 2.0e6], "es_limit": [5.5e6, 3.0e6, 2.6e6]}, index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])
def limit_monitor(pnl_by_acct, limits):
    rows = {a: {"var99": np.std(p) * 2.33, "es975": np.std(p) * 2.33} for a, p in pnl_by_acct.items()}
    df = pd.DataFrame(rows).T.join(limits)
    df["var_util"] = df["var99"] / df["var_limit"]; df["es_util"] = df["es975"] / df["es_limit"]
    df["status"] = np.where(df["var_util"] > 1, "BREACH", "OK")
    return df[["var99", "es975", "var_util", "es_util", "status"]]
'''),
ex("One-line risk summary", r'''
Write `risk_summary(monitor)` returning a string like:
`3 accounts | 1 BREACH, 1 WARN | worst: HF-ALPHA (ES 112%)`
where worst = the first row (already sorted) and the percentage is its **larger** utilization (label `VaR` or `ES`, whichever is larger), rounded to a whole percent.
''', r'''
import pandas as pd
MON = pd.DataFrame({"var99": [3.9e6, 1.1e6, 1.2e6], "es975": [6.2e6, 1.7e6, 1.4e6],
                    "var_util": [0.975, 0.55, 0.60], "es_util": [1.127, 0.567, 0.538], "status": ["BREACH", "OK", "WARN"]},
                   index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])

def risk_summary(monitor):
    ...

print(risk_summary(MON))
''', r'''
import pandas as pd
MON = pd.DataFrame({"var99": [3.9e6, 1.1e6, 1.2e6], "es975": [6.2e6, 1.7e6, 1.4e6],
                    "var_util": [0.975, 0.55, 0.60], "es_util": [1.127, 0.567, 0.538], "status": ["BREACH", "OK", "WARN"]},
                   index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])

def risk_summary(monitor):
    counts = monitor["status"].value_counts()
    top = monitor.index[0]
    row = monitor.iloc[0]
    label, u = ("VaR", row["var_util"]) if row["var_util"] >= row["es_util"] else ("ES", row["es_util"])
    return f"{len(monitor)} accounts | {counts.get('BREACH', 0)} BREACH, {counts.get('WARN', 0)} WARN | worst: {top} ({label} {u:.0%})"

print(risk_summary(MON))
''', [("text", r'''
got = risk_summary(MON)
exp = "3 accounts | 1 BREACH, 1 WARN | worst: HF-ALPHA (ES 113%)"
assert got == exp, f"got:\n{got}\nexpected:\n{exp}"
'''), ("no breaches", r'''
import pandas as pd
m = pd.DataFrame({"var_util": [0.5], "es_util": [0.4], "status": ["OK"]}, index=["X"])
got = risk_summary(m)
assert got == "1 accounts | 0 BREACH, 0 WARN | worst: X (VaR 50%)", got
''')], hints=["monitor['status'].value_counts().get('BREACH', 0)", "f'{0.5:.0%}' → '50%'"],
wrong=r'''
import pandas as pd
MON = pd.DataFrame({"var99": [3.9e6, 1.1e6, 1.2e6], "es975": [6.2e6, 1.7e6, 1.4e6], "var_util": [0.975, 0.55, 0.60], "es_util": [1.127, 0.567, 0.538], "status": ["BREACH", "OK", "WARN"]}, index=["HF-ALPHA", "HF-BETA", "FO-GAMMA"])
def risk_summary(monitor):
    return f"{len(monitor)} accounts | worst: {monitor.index[0]}"
'''),
],
work=r'''
**Take it to work — Daily risk-limit monitor (VaR / ES / stress / concentration)**
- Build scenario P&L per client from 2 years of product returns × today's exposures (+ a stress window like Mar-2020 appended).
- Compute VaR99, ES97.5, worst named stress vs collateral excess, and OI concentration; compare to per-client limits.
- Output: breach/warn table (worst first), one-line summary for the morning email, and a CSV archive for trend charts.
- Stretch: add option positions via Black-76 deltas (or full revaluation) so the client's options book is captured.
''')
