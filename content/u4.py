from dsl import *

unit("u4", "numpy: Returns, Volatility & Correlation", "Vectorized math for scenario revaluation, log returns, annualized and rolling vol, correlation and portfolio vol.")

lesson("u4l1", "numpy arrays: revalue positions under scenarios",
"Revalue a book under 16 price scenarios in one line — the engine inside every margin and stress calc.",
r'''
`numpy` arrays are fast, fixed-type grids of numbers. Math applies element-wise:

```python
import numpy as np
qty = np.array([120, -40, -250])           # ES, NQ, CL
mult = np.array([50, 20, 1000])
price = np.array([5790.0, 20100.0, 73.10])
dollar_per_pt = qty * mult                 # element-wise → [6000, -800, -250000]
```

**Broadcasting**: shapes stretch to match. A `(16, 3)` matrix of price moves times a `(3,)` vector multiplies each row.

**Matrix multiply** `@`: `moves @ dollar_per_pt` gives one P&L per scenario (sums across products).

Handy: `.sum() .mean() .std(ddof=1) .min() .argmin()`, `np.where(cond, a, b)`, boolean masks `arr[arr < 0]`, `np.linspace(-1, 1, 7)`, `np.outer(a, b)`, `arr.shape`, `arr.reshape(...)`.

Rule of thumb: if you're writing a `for` loop over numbers, numpy probably has a one-liner.
''',
examples=[("Scenario grid", r'''
import numpy as np
dollar_per_pt = np.array([120 * 50, -40 * 20, -250 * 1000])   # ES, NQ, CL
scan = np.array([350.0, 1400.0, 6.0])                         # price scan range per product (points)
fractions = np.array([-1, -2/3, -1/3, 0, 1/3, 2/3, 1])
moves = np.outer(fractions, scan)          # (7, 3): each row = one scenario's moves
pnl = moves @ dollar_per_pt                 # (7,)
for f, p in zip(fractions, pnl):
    print(f"{f:+.2f} × range → {p:>14,.0f}")
print("worst:", pnl.min())
''')],
quiz=[q("`np.array([1, 2, 3]) * np.array([10, 20, 30])` gives…", ["140", "[10, 40, 90]", "[[10,20,30],[20,40,60],[30,60,90]]", "Error"], 1, "`*` is element-wise. Use `@` for a dot product (which would give 140).")],
exercises=[
ex("Scenario P&L", r'''
Given `moves` (5 scenarios × 3 products, in price points) and positions, compute:
- `dollar_per_pt` = qty × mult (array)
- `pnl` = P&L per scenario (array of 5), using `@`
- `worst_idx` = index of the worst scenario, `worst_loss` = its loss as a **positive** number
''', r'''
import numpy as np
qty = np.array([120, -40, -250])      # ES, NQ, CL
mult = np.array([50, 20, 1000])
moves = np.array([
    [-150.0, -600.0, -2.5],   # risk-off
    [ 150.0,  600.0,  2.5],   # risk-on
    [-150.0,  -50.0,  4.0],   # oil shock
    [   0.0,  400.0,  0.0],   # tech rally
    [ -60.0, -300.0, -1.0],   # mild sell-off
])
dollar_per_pt = ...
pnl = ...
worst_idx = ...
worst_loss = ...
print(pnl)
''', r'''
import numpy as np
qty = np.array([120, -40, -250])
mult = np.array([50, 20, 1000])
moves = np.array([
    [-150.0, -600.0, -2.5],
    [ 150.0,  600.0,  2.5],
    [-150.0,  -50.0,  4.0],
    [   0.0,  400.0,  0.0],
    [ -60.0, -300.0, -1.0],
])
dollar_per_pt = qty * mult
pnl = moves @ dollar_per_pt
worst_idx = int(pnl.argmin())
worst_loss = -pnl.min()
print(pnl)
''', [("dollar_per_pt", r'''assert list(dollar_per_pt) == [6000, -800, -250000], f"dollar_per_pt = {list(dollar_per_pt)}"'''),
("pnl", r'''
import numpy as np
exp = [205000.0, -205000.0, -1860000.0, -320000.0, 130000.0]
assert np.allclose(pnl, exp), f"pnl = {[float(v) for v in np.round(pnl)]}; expected {exp}. Each scenario row · dollar_per_pt → use moves @ dollar_per_pt"
'''), ("worst", r'''
assert worst_idx == 2, f"worst_idx = {worst_idx} — use argmin"
assert _close(worst_loss, 1_860_000), f"worst_loss = {worst_loss}; should be positive 1,860,000"
''')], hints=["dollar_per_pt = qty * mult", "pnl = moves @ dollar_per_pt; pnl.argmin()"],
wrong=r'''
import numpy as np
qty = np.array([120, -40, -250]); mult = np.array([50, 20, 1000])
moves = np.array([[-150.0, -600.0, -2.5], [150.0, 600.0, 2.5], [-150.0, -50.0, 4.0], [0.0, 400.0, 0.0], [-60.0, -300.0, -1.0]])
dollar_per_pt = qty * mult
pnl = (moves * dollar_per_pt).sum(axis=0)
worst_idx = int(pnl.argmin()); worst_loss = pnl.min()
'''),
ex("Masks & where", r'''
`pnl` holds 250 days of simulated desk P&L. Compute:
- `n_loss_days` (count of days < 0)
- `avg_loss` (mean of the losing days, a negative number)
- `capped` = array where losses worse than −2,000,000 are replaced with −2,000,000 (use `np.where` or `np.maximum`)
''', r'''
import numpy as np
rng = np.random.default_rng(42)
pnl = rng.normal(50_000, 900_000, 250)
n_loss_days = ...
avg_loss = ...
capped = ...
''', r'''
import numpy as np
rng = np.random.default_rng(42)
pnl = rng.normal(50_000, 900_000, 250)
n_loss_days = int((pnl < 0).sum())
avg_loss = pnl[pnl < 0].mean()
capped = np.where(pnl < -2_000_000, -2_000_000, pnl)
''', [("n_loss_days", r'''
import numpy as np
exp = int((pnl < 0).sum())
assert n_loss_days == exp, f"n_loss_days = {n_loss_days}; expected {exp} — (pnl < 0).sum() counts True values"
'''), ("avg_loss", r'''
exp = pnl[pnl < 0].mean()
assert _close(avg_loss, exp), f"avg_loss = {avg_loss:,.0f}; expected {exp:,.0f} (mean of only the negative days)"
'''), ("capped", r'''
import numpy as np
assert capped.shape == pnl.shape, "capped should have the same length as pnl"
assert capped.min() >= -2_000_000 and np.allclose(capped[pnl >= -2e6], pnl[pnl >= -2e6]), "Only values below −2m should change"
''')], hints=["Boolean mask: pnl[pnl < 0]", "np.where(pnl < -2_000_000, -2_000_000, pnl)"],
wrong=r'''
import numpy as np
rng = np.random.default_rng(42)
pnl = rng.normal(50_000, 900_000, 250)
n_loss_days = len(pnl[pnl <= 0])
avg_loss = np.where(pnl < 0, pnl, 0).mean()
capped = np.clip(pnl, -2_000_000, 2_000_000)
'''),
])

lesson("u4l2", "Returns: simple vs log",
"Turn settlement price histories into returns — the input to every vol, VaR and correlation number.",
r'''
- **Simple return**: r = Pₜ / Pₜ₋₁ − 1. Aggregates across *assets* (portfolio return = weighted sum).
- **Log return**: ℓ = ln(Pₜ / Pₜ₋₁). Aggregates across *time*: the multi-day log return is the **sum** of daily log returns. Total simple return = exp(Σℓ) − 1.
- For small moves they're nearly equal (ln(1.01) ≈ 0.00995).

```python
p = np.array([5850.25, 5790.00, 5812.50, 5768.75])
simple = p[1:] / p[:-1] - 1          # or np.diff(p) / p[:-1]
logret = np.diff(np.log(p))
```
pandas: `s.pct_change()` and `np.log(s).diff()` (first value is NaN — `.dropna()`).

For **futures**, a "return" on price ignores that no cash was invested; risk systems often use **price changes in points** (× multiplier = $) for margin and VaR on futures, and returns for vol comparisons. Watch for **roll** jumps when stitching contract months.
''',
examples=[("Log returns add up", r'''
import numpy as np
p = np.array([5850.25, 5790.00, 5812.50, 5768.75, 5801.00])
lr = np.diff(np.log(p))
print("daily log returns:", np.round(lr, 5))
print("sum of logs     :", round(lr.sum(), 6), " vs ln(P_end/P_start):", round(np.log(p[-1] / p[0]), 6))
print("total simple    :", round(np.exp(lr.sum()) - 1, 6), " vs", round(p[-1] / p[0] - 1, 6))
''')],
quiz=[q("A price goes 100 → 110 → 100. Sum of daily simple returns vs log returns?", ["Both 0", "Simple ≈ +0.0091, log = 0", "Simple = 0, log ≈ +0.0091", "Both +0.0091"], 1, "+10% then −9.09% sums to +0.91% even though you're flat; log returns sum to exactly 0.")],
exercises=[
ex("Compute returns", r'''
From `prices` (numpy array), compute `simple` and `logret` arrays (length n−1), and `total_from_logs` = total simple return over the period computed **from the log returns**.
''', r'''
import numpy as np
prices = np.array([71.40, 73.10, 72.55, 70.90, 71.85, 74.20, 73.65])   # CL settles
simple = ...
logret = ...
total_from_logs = ...
''', r'''
import numpy as np
prices = np.array([71.40, 73.10, 72.55, 70.90, 71.85, 74.20, 73.65])
simple = prices[1:] / prices[:-1] - 1
logret = np.diff(np.log(prices))
total_from_logs = np.exp(logret.sum()) - 1
''', [("simple", r'''
import numpy as np
exp = np.diff(prices) / prices[:-1]
assert len(simple) == 6 and np.allclose(simple, exp), f"simple = {np.round(simple, 5)}"
'''), ("logret", r'''
import numpy as np
assert len(logret) == 6, f"logret should have 6 values; got {len(logret)}"
assert np.allclose(logret, np.log(prices[1:] / prices[:-1])), "logret should be ln(P_t / P_t-1)" + (" — you computed log(P_t) - P_t-1?" if False else "")
'''), ("total_from_logs", r'''
exp = 73.65 / 71.40 - 1
assert _close(total_from_logs, exp), f"total_from_logs = {total_from_logs:.6f}; expected {exp:.6f} = exp(sum of logs) − 1" + (" — you summed log returns but forgot exp(...) − 1" if _close(total_from_logs, float(__import__('numpy').log(73.65/71.40))) else "")
''')], hints=["prices[1:] / prices[:-1] - 1", "np.diff(np.log(prices))", "np.exp(logret.sum()) - 1"],
wrong=r'''
import numpy as np
prices = np.array([71.40, 73.10, 72.55, 70.90, 71.85, 74.20, 73.65])
simple = prices[1:] / prices[:-1] - 1
logret = np.log(prices[1:] / prices[:-1])
total_from_logs = logret.sum()
'''),
ex("Returns in pandas", r'''
`px` is a DataFrame of daily settles (columns ES, NQ, CL). Create `rets` = daily **log** returns with the first (NaN) row dropped, and `worst_day` = dict product → the **date string** (YYYY-MM-DD) of its worst log return.
''', r'''
import numpy as np
import pandas as pd
px = pd.DataFrame({
    "ES": [5850.25, 5790.00, 5812.50, 5768.75, 5801.00, 5833.25],
    "NQ": [20410.5, 20100.0, 20250.0, 19980.0, 20120.0, 20300.0],
    "CL": [71.40, 73.10, 72.55, 70.90, 71.85, 74.20]},
    index=pd.bdate_range("2026-09-21", periods=6))
rets = ...
worst_day = ...
''', r'''
import numpy as np
import pandas as pd
px = pd.DataFrame({
    "ES": [5850.25, 5790.00, 5812.50, 5768.75, 5801.00, 5833.25],
    "NQ": [20410.5, 20100.0, 20250.0, 19980.0, 20120.0, 20300.0],
    "CL": [71.40, 73.10, 72.55, 70.90, 71.85, 74.20]},
    index=pd.bdate_range("2026-09-21", periods=6))
rets = np.log(px).diff().dropna()
worst_day = {c: rets[c].idxmin().strftime("%Y-%m-%d") for c in rets.columns}
''', [("rets", r'''
import numpy as np
assert rets.shape == (5, 3), f"rets shape = {rets.shape}; drop the first NaN row"
assert np.allclose(rets["ES"].iloc[0], np.log(5790.00 / 5850.25)), "rets should be LOG returns"
'''), ("worst_day", r'''assert worst_day == {"ES": "2026-09-22", "NQ": "2026-09-22", "CL": "2026-09-24"}, f"worst_day = {worst_day}"''')],
hints=["np.log(px).diff().dropna()", "rets[c].idxmin() returns the date index label; .strftime('%Y-%m-%d')"],
wrong=r'''
import numpy as np
import pandas as pd
px = pd.DataFrame({"ES": [5850.25, 5790.00, 5812.50, 5768.75, 5801.00, 5833.25], "NQ": [20410.5, 20100.0, 20250.0, 19980.0, 20120.0, 20300.0], "CL": [71.40, 73.10, 72.55, 70.90, 71.85, 74.20]}, index=pd.bdate_range("2026-09-21", periods=6))
rets = px.pct_change()
worst_day = {c: str(rets[c].idxmax())[:10] for c in rets.columns}
'''),
])

lesson("u4l3", "Volatility: annualized and rolling",
"Measure each product's volatility and spot when it's rising — the trigger for margin increases.",
r'''
**Volatility** = standard deviation of returns.

```python
daily_vol = rets.std(ddof=1)            # sample std (pandas default ddof=1; numpy default ddof=0!)
annual_vol = daily_vol * np.sqrt(252)   # ~252 trading days/year
```

The √time rule assumes independent returns: vol over *h* days ≈ daily vol × √h. So a 2-day margin period of risk scales 1-day risk by √2 ≈ 1.41.

**Rolling vol** shows regime changes: `rets.rolling(20).std() * np.sqrt(252)`. **EWMA** vol (RiskMetrics λ = 0.94) reacts faster: `rets.ewm(alpha=1-0.94).std()`.

In dollar terms for futures: daily $ vol ≈ price × daily vol × multiplier × contracts.

CCPs raise margins when realized vol jumps (and many use floors/anti-procyclicality buffers so margins don't spike too violently — a hot topic after March 2020 and the 2022 nickel/energy moves).
''',
examples=[("Daily → annual, numpy vs pandas ddof", r'''
import numpy as np
import pandas as pd
r = np.array([0.012, -0.008, 0.004, -0.015, 0.009, 0.002, -0.011])
print("numpy default ddof=0:", r.std())
print("sample ddof=1       :", r.std(ddof=1), " == pandas:", pd.Series(r).std())
print("annualized          :", r.std(ddof=1) * np.sqrt(252))
''')],
quiz=[q("Daily vol is 1.2%. Approximate 10-day vol (independent returns)?", ["12%", "3.8%", "1.2%", "0.12%"], 1, "1.2% × √10 ≈ 3.79%.")],
exercises=[
ex("ann_vol() and dollar vol", r'''
Write `ann_vol(prices)` that takes a list/array of prices and returns **annualized** vol of **log** returns (sample std, ddof=1, 252 days).
Then compute `dollar_vol_1d` for a position of **-250 CL** (mult 1000) at the last price: |qty| × mult × last price × daily vol.
''', r'''
import numpy as np
cl = [71.40, 73.10, 72.55, 70.90, 71.85, 74.20, 73.65, 72.10, 72.95, 71.60, 72.35]

def ann_vol(prices):
    ...

dollar_vol_1d = ...
print(ann_vol(cl), dollar_vol_1d)
''', r'''
import numpy as np
cl = [71.40, 73.10, 72.55, 70.90, 71.85, 74.20, 73.65, 72.10, 72.95, 71.60, 72.35]

def ann_vol(prices):
    lr = np.diff(np.log(np.asarray(prices, dtype=float)))
    return lr.std(ddof=1) * np.sqrt(252)

daily = ann_vol(cl) / np.sqrt(252)
dollar_vol_1d = 250 * 1000 * cl[-1] * daily
print(ann_vol(cl), dollar_vol_1d)
''', [("ann_vol", r'''
import numpy as np
lr = np.diff(np.log(cl)); exp = lr.std(ddof=1) * np.sqrt(252)
got = ann_vol(cl)
msg = f"ann_vol = {got:.4f}; expected {exp:.4f}"
if _close(got, lr.std(ddof=0) * np.sqrt(252)): msg += " — numpy's std defaults to ddof=0; use ddof=1"
if _close(got, lr.std(ddof=1)): msg += " — you forgot × sqrt(252)"
assert _close(got, exp), msg
'''), ("hidden series", r'''
import numpy as np
p = [100, 101, 99.5, 100.2, 102.0]
assert _close(ann_vol(p), np.diff(np.log(p)).std(ddof=1) * np.sqrt(252))
'''), ("dollar_vol_1d", r'''
import numpy as np
exp = 250 * 1000 * 72.35 * np.diff(np.log(cl)).std(ddof=1)
assert _close(dollar_vol_1d, exp, 1e-4), f"dollar_vol_1d = {dollar_vol_1d:,.0f}; expected ≈ {exp:,.0f} (use DAILY vol, positive)"
''')], hints=["lr = np.diff(np.log(prices)); lr.std(ddof=1) * np.sqrt(252)", "Daily vol = annual / sqrt(252)"],
wrong=r'''
import numpy as np
cl = [71.40, 73.10, 72.55, 70.90, 71.85, 74.20, 73.65, 72.10, 72.95, 71.60, 72.35]
def ann_vol(prices):
    return np.diff(np.log(prices)).std() * np.sqrt(252)
dollar_vol_1d = -250 * 1000 * cl[-1] * ann_vol(cl)
'''),
ex("Rolling vol spike", r'''
`rets` is a Series of 120 daily log returns (synthetic: calm, then a volatile regime). Compute:
- `vol20` = 20-day rolling annualized vol
- `spike_start` = the **first date** where vol20 exceeds **30%** (a `Timestamp`)
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(7)
r = np.concatenate([rng.normal(0, 0.009, 80), rng.normal(0, 0.028, 40)])
rets = pd.Series(r, index=pd.bdate_range("2026-04-01", periods=120))
vol20 = ...
spike_start = ...
print(spike_start)
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(7)
r = np.concatenate([rng.normal(0, 0.009, 80), rng.normal(0, 0.028, 40)])
rets = pd.Series(r, index=pd.bdate_range("2026-04-01", periods=120))
vol20 = rets.rolling(20).std() * np.sqrt(252)
spike_start = vol20[vol20 > 0.30].index[0]
print(spike_start)
''', [("vol20", r'''
import numpy as np
exp = rets.rolling(20).std() * np.sqrt(252)
assert len(vol20) == 120 and np.allclose(vol20.dropna(), exp.dropna()), "vol20 should be rets.rolling(20).std() * sqrt(252)"
'''), ("spike_start", r'''
import numpy as np
exp = (rets.rolling(20).std() * np.sqrt(252))
exp = exp[exp > 0.30].index[0]
assert spike_start == exp, f"spike_start = {spike_start}; expected {exp.date()}"
''')], hints=["rets.rolling(20).std() * np.sqrt(252)", "vol20[vol20 > 0.30].index[0]"],
wrong=r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(7)
r = np.concatenate([rng.normal(0, 0.009, 80), rng.normal(0, 0.028, 40)])
rets = pd.Series(r, index=pd.bdate_range("2026-04-01", periods=120))
vol20 = rets.rolling(20).std()
spike_start = rets.index[80]
'''),
])

lesson("u4l4", "Correlation & portfolio volatility",
"Quantify how much ES/NQ hedges really offset, and compute the book's dollar vol from a covariance matrix.",
r'''
**Correlation** ρ ∈ [−1, 1] measures co-movement. `np.corrcoef(a, b)[0, 1]` or `rets.corr()` in pandas.

**Portfolio volatility** needs the covariance matrix Σ (`np.cov(rets.T)` or `rets.cov()`):

σ²ₚ = xᵀ Σ x, where x = **dollar exposures** (or weights)

```python
x = np.array([34.7e6, -16.1e6])     # $ exposure: long ES, short NQ
cov = rets.cov().values              # daily covariance of returns
port_vol = np.sqrt(x @ cov @ x)      # daily $ vol
```

A long ES / short NQ book with ρ ≈ 0.9 has far less risk than the gross suggests — that's exactly why SPAN gives **inter-commodity spread credits** between correlated products. But correlations **break down in stress** (they tend to go to 1 in a sell-off, or flip), so risk managers stress them.
''',
examples=[("Hedge benefit", r'''
import numpy as np
vol = np.array([0.011, 0.014])        # daily vol ES, NQ
for rho in [0.0, 0.5, 0.9, 0.99]:
    cov = np.array([[vol[0]**2, rho*vol[0]*vol[1]], [rho*vol[0]*vol[1], vol[1]**2]])
    x = np.array([34.7e6, -16.1e6])
    print(f"rho={rho:.2f}  daily $ vol = {np.sqrt(x @ cov @ x):>12,.0f}")
''')],
quiz=[q("Long $10m ES and short $10m NQ with ρ = 0.95 and equal vols. Portfolio vol vs a single $10m leg?", ["Double", "About the same", "Much smaller (~32%)", "Zero"], 2, "σₚ = σ·10m·√(2 − 2ρ) = σ·10m·√0.1 ≈ 0.32× one leg.")],
exercises=[
ex("Correlation matrix", r'''
From `rets` (DataFrame of daily returns for ES, NQ, CL, ZN), compute `corr` (correlation matrix DataFrame), `es_nq` (the ES–NQ correlation as float) and `best_hedge_for_es`: the product (other than ES) **most negatively** correlated with ES.
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(11)
z = rng.standard_normal((250, 4))
L = np.linalg.cholesky(np.array([[1, .9, .2, -.4], [.9, 1, .15, -.35], [.2, .15, 1, -.1], [-.4, -.35, -.1, 1]]))
rets = pd.DataFrame(z @ L.T * np.array([.011, .014, .022, .004]), columns=["ES", "NQ", "CL", "ZN"])
corr = ...
es_nq = ...
best_hedge_for_es = ...
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(11)
z = rng.standard_normal((250, 4))
L = np.linalg.cholesky(np.array([[1, .9, .2, -.4], [.9, 1, .15, -.35], [.2, .15, 1, -.1], [-.4, -.35, -.1, 1]]))
rets = pd.DataFrame(z @ L.T * np.array([.011, .014, .022, .004]), columns=["ES", "NQ", "CL", "ZN"])
corr = rets.corr()
es_nq = float(corr.loc["ES", "NQ"])
best_hedge_for_es = corr["ES"].drop("ES").idxmin()
''', [("corr", r'''
import numpy as np
assert corr.shape == (4, 4) and np.allclose(np.diag(corr), 1), "corr should be the 4×4 matrix from rets.corr()"
'''), ("es_nq", r'''assert _close(es_nq, float(rets.corr().loc["ES", "NQ"])), f"es_nq = {es_nq}"'''),
("best_hedge_for_es", r'''assert best_hedge_for_es == "ZN", f"best_hedge_for_es = {best_hedge_for_es!r} — drop ES itself (ρ=1) and take idxmin"''')],
hints=["rets.corr()", "corr['ES'].drop('ES').idxmin()"],
wrong=r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(11)
rets = pd.DataFrame(rng.standard_normal((250, 4)), columns=["ES", "NQ", "CL", "ZN"])
corr = rets.corr()
es_nq = float(corr.loc["ES", "NQ"])
best_hedge_for_es = corr["ES"].idxmax()
'''),
ex("Portfolio $ vol", r'''
Using the same `rets` and dollar exposures `x`, compute:
- `port_vol` = daily portfolio $ vol = √(xᵀΣx) with Σ = sample covariance of returns
- `standalone` = sum of each leg's standalone daily $ vol (|xᵢ| × σᵢ)
- `diversification` = 1 − port_vol / standalone
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(11)
z = rng.standard_normal((250, 4))
L = np.linalg.cholesky(np.array([[1, .9, .2, -.4], [.9, 1, .15, -.35], [.2, .15, 1, -.1], [-.4, -.35, -.1, 1]]))
rets = pd.DataFrame(z @ L.T * np.array([.011, .014, .022, .004]), columns=["ES", "NQ", "CL", "ZN"])
x = np.array([34.74e6, -16.08e6, -18.28e6, 88.50e6])   # $ exposure ES, NQ, CL, ZN
port_vol = ...
standalone = ...
diversification = ...
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(11)
z = rng.standard_normal((250, 4))
L = np.linalg.cholesky(np.array([[1, .9, .2, -.4], [.9, 1, .15, -.35], [.2, .15, 1, -.1], [-.4, -.35, -.1, 1]]))
rets = pd.DataFrame(z @ L.T * np.array([.011, .014, .022, .004]), columns=["ES", "NQ", "CL", "ZN"])
x = np.array([34.74e6, -16.08e6, -18.28e6, 88.50e6])
cov = rets.cov().values
port_vol = float(np.sqrt(x @ cov @ x))
standalone = float((np.abs(x) * rets.std().values).sum())
diversification = 1 - port_vol / standalone
''', [("port_vol", r'''
import numpy as np
exp = np.sqrt(x @ rets.cov().values @ x)
assert _close(port_vol, exp), f"port_vol = {port_vol:,.0f}; expected {exp:,.0f}" + (" — take the square root" if _close(port_vol, exp**2) else "")
'''), ("standalone & diversification", r'''
import numpy as np
s = (np.abs(x) * rets.std().values).sum()
assert _close(standalone, s), f"standalone = {standalone:,.0f}; expected {s:,.0f} (use |x|)"
assert 0 < diversification < 1 and _close(diversification, 1 - np.sqrt(x @ rets.cov().values @ x) / s)
''')], hints=["cov = rets.cov().values; np.sqrt(x @ cov @ x)", "(np.abs(x) * rets.std().values).sum()"],
wrong=r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(11)
z = rng.standard_normal((250, 4))
L = np.linalg.cholesky(np.array([[1, .9, .2, -.4], [.9, 1, .15, -.35], [.2, .15, 1, -.1], [-.4, -.35, -.1, 1]]))
rets = pd.DataFrame(z @ L.T * np.array([.011, .014, .022, .004]), columns=["ES", "NQ", "CL", "ZN"])
x = np.array([34.74e6, -16.08e6, -18.28e6, 88.50e6])
port_vol = float(x @ rets.cov().values @ x)
standalone = float((x * rets.std().values).sum())
diversification = 1 - port_vol / standalone
'''),
])

lesson("u4l5", "Take it to work: volatility regime monitor",
"Flag products whose short-term vol has jumped versus long-term — an early warning for margin calls and client stress.",
r'''
A simple, robust monitor used on many risk desks:

- **Short window** (e.g. 20d) vs **long window** (e.g. 60d) annualized vol per product.
- **Ratio** = vol20 / vol60. Ratio > 1.5 → **ALERT** (regime change); > 1.2 → **WATCH**.
- Report the latest row per product, sorted by ratio.

Design choices to mention in an interview: window lengths (reactivity vs noise), EWMA instead of rolling, using **absolute** thresholds too (a 1.5× jump from 5% vol matters less than from 30%), and data quality (roll gaps masquerading as vol spikes).
''',
examples=[("Latest row of a rolling calc", r'''
import numpy as np
import pandas as pd
s = pd.Series(np.arange(10.0))
print(s.rolling(3).mean().iloc[-1], s.rolling(3).mean().dropna().tail(2).tolist())
''')],
quiz=[q("vol20 = 18%, vol60 = 12%. Ratio and status with thresholds 1.2 / 1.5?", ["1.5, ALERT", "1.5, WATCH", "0.67, OK", "6, ALERT"], 1, "18/12 = 1.5, which is > 1.2 but not > 1.5 → WATCH.")],
exercises=[
ex("vol_monitor(rets)", r'''
Write `vol_monitor(rets, short=20, long=60)` taking a DataFrame of daily log returns (one column per product) and returning a DataFrame indexed by product with columns `vol_short`, `vol_long`, `ratio`, `status`, using the **latest** values, sorted by ratio descending.
Status: `"ALERT"` if ratio > 1.5, `"WATCH"` if ratio > 1.2, else `"OK"`. Vols annualized with √252.
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(3)
n = 150
rets = pd.DataFrame({
    "ES": np.r_[rng.normal(0, .010, n - 20), rng.normal(0, .040, 20)],
    "CL": rng.normal(0, .020, n),
    "ZN": np.r_[rng.normal(0, .004, n - 20), rng.normal(0, .0055, 20)],
    "GC": np.r_[rng.normal(0, .012, n - 20), rng.normal(0, .007, 20)]},
    index=pd.bdate_range("2026-03-02", periods=n))

def vol_monitor(rets, short=20, long=60):
    ...

print(vol_monitor(rets))
''', r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(3)
n = 150
rets = pd.DataFrame({
    "ES": np.r_[rng.normal(0, .010, n - 20), rng.normal(0, .040, 20)],
    "CL": rng.normal(0, .020, n),
    "ZN": np.r_[rng.normal(0, .004, n - 20), rng.normal(0, .0055, 20)],
    "GC": np.r_[rng.normal(0, .012, n - 20), rng.normal(0, .007, 20)]},
    index=pd.bdate_range("2026-03-02", periods=n))

def vol_monitor(rets, short=20, long=60):
    vs = rets.rolling(short).std().iloc[-1] * np.sqrt(252)
    vl = rets.rolling(long).std().iloc[-1] * np.sqrt(252)
    out = pd.DataFrame({"vol_short": vs, "vol_long": vl})
    out["ratio"] = out["vol_short"] / out["vol_long"]
    out["status"] = np.select([out["ratio"] > 1.5, out["ratio"] > 1.2], ["ALERT", "WATCH"], default="OK")
    return out.sort_values("ratio", ascending=False)

print(vol_monitor(rets))
''', [("structure", r'''
m = vol_monitor(rets)
assert list(m.columns) == ["vol_short", "vol_long", "ratio", "status"], f"columns = {list(m.columns)}"
assert sorted(m.index) == ["CL", "ES", "GC", "ZN"], "index should be the product names"
'''), ("values", r'''
import numpy as np
m = vol_monitor(rets)
exp = rets.tail(20).std()["ES"] * np.sqrt(252)
assert _close(m.loc["ES", "vol_short"], exp), f"ES vol_short = {m.loc['ES','vol_short']:.4f}; expected {exp:.4f} (latest 20d, annualized)"
'''), ("status & order", r'''
m = vol_monitor(rets)
assert list(m["ratio"]) == sorted(m["ratio"], reverse=True), f"order = {list(m.index)} — sort by ratio desc"
for prod, row in m.iterrows():
    exp = "ALERT" if row["ratio"] > 1.5 else ("WATCH" if row["ratio"] > 1.2 else "OK")
    assert row["status"] == exp, f"{prod}: ratio {row['ratio']:.2f} should be {exp}, got {row['status']}"
assert m.index[0] == "ES" and m.loc["ES", "status"] == "ALERT", f"ES should top the list as ALERT; statuses = {m['status'].to_dict()}"
'''), ("custom windows", r'''
m = vol_monitor(rets, short=10, long=100)
import numpy as np
assert _close(m.loc["CL", "vol_long"], rets["CL"].tail(100).std() * np.sqrt(252))
''')], hints=["rets.rolling(short).std().iloc[-1] gives the latest value for every column", "np.select([ratio > 1.5, ratio > 1.2], ['ALERT', 'WATCH'], default='OK')"],
wrong=r'''
import numpy as np
import pandas as pd
rng = np.random.default_rng(3)
n = 150
rets = pd.DataFrame({"ES": np.r_[rng.normal(0, .010, n - 20), rng.normal(0, .040, 20)], "CL": rng.normal(0, .020, n), "ZN": np.r_[rng.normal(0, .004, n - 20), rng.normal(0, .0055, 20)], "GC": np.r_[rng.normal(0, .012, n - 20), rng.normal(0, .007, 20)]}, index=pd.bdate_range("2026-03-02", periods=n))
def vol_monitor(rets, short=20, long=60):
    vs = rets.rolling(short).std().mean() * np.sqrt(252)
    vl = rets.rolling(long).std().mean() * np.sqrt(252)
    out = pd.DataFrame({"vol_short": vs, "vol_long": vl})
    out["ratio"] = out["vol_short"] / out["vol_long"]
    out["status"] = np.where(out["ratio"] > 1.5, "ALERT", "OK")
    return out
'''),
],
work=r'''
**Take it to work — Vol regime monitor**
- Pull 1 year of daily settles for the products your clients trade most (front-month, roll-adjusted).
- Run `vol_monitor` daily; add EWMA vol and an absolute-level threshold.
- Join to client positions to list which accounts are most exposed to the ALERT products — send to sales/risk before the CCP margin change hits.
- Stretch: backtest — did ALERTs precede CME margin increases?
''')
