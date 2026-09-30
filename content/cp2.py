from dsl import *
from cp1 import CP_BODY

checkpoint("u4", "u4cp", "Checkpoint: numpy for risk",
"Arrays, returns, volatility and correlation: the numeric core of every risk model.",
CP_BODY,
quiz=[
q("Shapes: `positions` is (3,), `shocks` is (16, 3). Shape of `shocks * positions`?", ["(3,)", "(16,)", "(16, 3)", "Error"], 2, "Broadcasting stretches (3,) across the 16 rows."),
q("Why are log returns convenient over multiple days?", ["They are always positive", "They add across time", "They equal simple returns", "They remove volatility"], 1, "The multi-day log return is the sum of daily log returns."),
q("Daily vol is 1.2%. Annualized vol with 252 trading days?", ["1.2% x 252 = 302%", "1.2% x sqrt(252) = 19.0%", "1.2% / 252", "1.2% x 12"], 1, "Volatility scales with the square root of time (under i.i.d. assumptions)."),
q("`r` has shape (250, 4) (days x assets). `r.std(axis=0, ddof=1)` returns?", ["One vol per day (250)", "One vol per asset (4)", "A single number", "A 4x4 matrix"], 1, "axis=0 collapses the rows (days)."),
q("Portfolio variance for weights w and covariance matrix S?", ["w + S", "w @ S @ w", "S / w", "sum(w) * trace(S)"], 1, "w'Sw. Portfolio vol is its square root."),
q("Two assets each 20% vol, correlation -1, 50/50 weights. Portfolio vol?", ["20%", "10%", "0%", "28%"], 2, "Perfectly negatively correlated equal positions cancel completely."),
],
exercises=[
ex("Scenario P&L matrix", r'''
`positions` holds deltas in $ per 1% move for 3 assets; `shocks` holds 5 scenarios x 3 assets of % moves. Compute `pnl` (one P&L per scenario, shape (5,)), `worst_idx` (index of the most negative) and `worst_loss` (a positive number). No Python loops.
''', r'''
import numpy as np
positions = np.array([120_000.0, -80_000.0, 50_000.0])
shocks = np.array([[-3.0, -2.0, 1.0],
                   [2.0, 1.5, -0.5],
                   [-5.0, 1.0, -2.0],
                   [0.5, -4.0, 3.0],
                   [-1.0, -1.0, -1.0]])
pnl = ...
worst_idx = ...
worst_loss = ...
print(pnl, worst_idx, worst_loss)
''', r'''
import numpy as np
positions = np.array([120_000.0, -80_000.0, 50_000.0])
shocks = np.array([[-3.0, -2.0, 1.0],
                   [2.0, 1.5, -0.5],
                   [-5.0, 1.0, -2.0],
                   [0.5, -4.0, 3.0],
                   [-1.0, -1.0, -1.0]])
pnl = shocks @ positions
worst_idx = int(np.argmin(pnl))
worst_loss = float(-pnl[worst_idx])
print(pnl, worst_idx, worst_loss)
''', [("pnl", r'''assert np.allclose(pnl, [-150_000, 95_000, -780_000, 530_000, -90_000]), f"pnl = {pnl}"'''),
("worst", r'''assert worst_idx == 2 and _close(worst_loss, 780_000), f"worst_idx = {worst_idx}, worst_loss = {worst_loss}"'''),
("no loops", r'''assert "for " not in _source, "Use a matrix product (shocks @ positions) instead of a loop"''')],
hints=["shocks @ positions multiplies each scenario row by the positions and sums.", "np.argmin gives the index of the smallest value."],
wrong=r'''
import numpy as np
positions = np.array([120_000.0, -80_000.0, 50_000.0])
shocks = np.array([[-3.0, -2.0, 1.0], [2.0, 1.5, -0.5], [-5.0, 1.0, -2.0], [0.5, -4.0, 3.0], [-1.0, -1.0, -1.0]])
pnl = (shocks * positions).sum(axis=0)
worst_idx = int(np.argmin(pnl))
worst_loss = float(pnl[worst_idx])
''', difficulty=2),
ex("EWMA volatility (RiskMetrics)", r'''
Write `ewma_vol(returns, lam=0.94)`: start with variance = the square of the first return, then for each **later** return r: `var = lam * var + (1 - lam) * r**2`. Return the final **annualized** vol: `sqrt(var * 252)`.
''', r'''
import numpy as np

def ewma_vol(returns, lam=0.94):
    ...

R = np.array([0.01, -0.02, 0.015, -0.03, 0.005])
print(round(ewma_vol(R), 6))
''', r'''
import numpy as np

def ewma_vol(returns, lam=0.94):
    var = returns[0] ** 2
    for r in returns[1:]:
        var = lam * var + (1 - lam) * r ** 2
    return float(np.sqrt(var * 252))

R = np.array([0.01, -0.02, 0.015, -0.03, 0.005])
print(round(ewma_vol(R), 6))
''', [("value", r'''
v = ewma_vol(np.array([0.01, -0.02, 0.015, -0.03, 0.005]))
var = 0.01 ** 2
for r in [-0.02, 0.015, -0.03, 0.005]:
    var = 0.94 * var + 0.06 * r * r
assert _close(v, (var * 252) ** 0.5), f"got {v}"
'''), ("constant returns", r'''assert _close(ewma_vol(np.array([0.01] * 10)), 0.01 * 252 ** 0.5), "Constant 1% returns -> daily vol 1%"''')],
hints=["Loop from the second element: for r in returns[1:]", "Annualize at the end: sqrt(var * 252)"],
wrong=r'''
import numpy as np
def ewma_vol(returns, lam=0.94):
    var = 0.0
    for r in returns:
        var = lam * var + (1 - lam) * r ** 2
    return float(np.sqrt(var) * 252)
''', difficulty=3),
])

checkpoint("u5", "u5cp", "Checkpoint: margin & collateral",
"Variation margin, initial margin, haircuts and calls: the core of FCM and prime risk.",
CP_BODY,
quiz=[
q("Variation margin is...", ["A fixed deposit set by the exchange", "The daily mark-to-market gain/loss settled in cash", "A haircut on bonds", "A credit line"], 1, "VM moves daily P&L; IM covers potential future loss."),
q("Equity falls below maintenance margin. The call is usually back to...", ["Maintenance", "Initial margin", "Zero", "Half of initial"], 1, "Futures calls restore the account to the initial (performance bond) requirement."),
q("$10m of a corporate bond with a 15% haircut counts as collateral worth?", ["$10m", "$8.5m", "$11.5m", "$1.5m"], 1, "Collateral value = market value x (1 - haircut)."),
q("SPAN-style scanning risk takes...", ["The average of 16 scenario losses", "The worst of the scenario losses", "The sum of all losses", "The best case"], 1, "Scanning risk is the largest loss across the price/vol scenarios (simplified model in this course)."),
q("An intercommodity spread credit (e.g. ZN vs ZF) does what to margin?", ["Increases it", "Reduces it for offsetting correlated positions", "Doesn't change it", "Doubles it"], 1, "Credits recognize that correlated offsetting positions carry less risk."),
q("Why cap how much of one issuer counts as collateral?", ["Tax reasons", "Concentration: one issuer defaulting would wipe out coverage", "It's cheaper", "Exchanges forbid bonds"], 1, "Concentration limits keep collateral diversified and liquid."),
],
exercises=[
ex("Collateral value with eligibility & a concentration cap", r'''
Write `collateral_value(items, haircuts, cap=0.40)`. Each item is `(asset_class, issuer, market_value)`. Ineligible asset classes (not in `haircuts`) count 0. After haircuts, **no single issuer may count for more than `cap` x the total post-haircut value of eligible items**; excess over the cap is disallowed. Return the total counted value. (Apply the cap once, using the pre-cap total.)
''', r'''
HAIRCUTS = {"CASH": 0.0, "UST": 0.02, "CORP": 0.15}

def collateral_value(items, haircuts, cap=0.40):
    ...

ITEMS = [("CASH", "USD", 2_000_000), ("UST", "US", 3_000_000), ("CORP", "ACME", 6_000_000), ("EQUITY", "ACME", 1_000_000)]
print(collateral_value(ITEMS, HAIRCUTS))
''', r'''
HAIRCUTS = {"CASH": 0.0, "UST": 0.02, "CORP": 0.15}

def collateral_value(items, haircuts, cap=0.40):
    by_issuer = {}
    for cls, issuer, mv in items:
        if cls not in haircuts:
            continue
        by_issuer[issuer] = by_issuer.get(issuer, 0.0) + mv * (1 - haircuts[cls])
    total = sum(by_issuer.values())
    limit = cap * total
    return sum(min(v, limit) for v in by_issuer.values())

ITEMS = [("CASH", "USD", 2_000_000), ("UST", "US", 3_000_000), ("CORP", "ACME", 6_000_000), ("EQUITY", "ACME", 1_000_000)]
print(collateral_value(ITEMS, HAIRCUTS))
''', [("example", r'''
v = collateral_value(ITEMS, HAIRCUTS)
# post-haircut: USD 2.0m, US 2.94m, ACME 5.1m -> total 10.04m, cap 4.016m -> ACME counted at 4.016m
assert _close(v, 2_000_000 + 2_940_000 + 4_016_000), f"got {v:,.0f}"
'''), ("no cap binding", r'''assert _close(collateral_value([("CASH", "USD", 1e6), ("UST", "US", 1e6)], HAIRCUTS, cap=0.6), 1e6 + 0.98e6)''')],
hints=["Aggregate post-haircut value by issuer first.", "limit = cap x total; counted = sum(min(v, limit))"],
wrong=r'''
HAIRCUTS = {"CASH": 0.0, "UST": 0.02, "CORP": 0.15}
def collateral_value(items, haircuts, cap=0.40):
    return sum(mv * (1 - haircuts.get(cls, 0)) for cls, issuer, mv in items)
''', difficulty=3),
ex("Call with minimum transfer amount & rounding", r'''
Write `margin_call(requirement, collateral_value, mta=250_000, rounding=10_000)`: the deficit is `requirement - collateral_value`. If the deficit is **at most** `mta`, return 0. Otherwise round the deficit **up** to the nearest `rounding` and return it.
''', r'''
import math

def margin_call(requirement, collateral_value, mta=250_000, rounding=10_000):
    ...

print(margin_call(10_000_000, 9_512_345))
''', r'''
import math

def margin_call(requirement, collateral_value, mta=250_000, rounding=10_000):
    deficit = requirement - collateral_value
    if deficit <= mta:
        return 0
    return math.ceil(deficit / rounding) * rounding

print(margin_call(10_000_000, 9_512_345))
''', [("rounds up", r'''assert margin_call(10_000_000, 9_512_345) == 490_000, f"got {margin_call(10_000_000, 9_512_345)}: deficit 487,655 rounds UP to 490,000"'''),
("below MTA", r'''assert margin_call(10_000_000, 9_800_000) == 0 and margin_call(10_000_000, 9_750_000) == 0, "Deficits at or below the MTA -> no call"'''),
("surplus", r'''assert margin_call(1_000_000, 5_000_000) == 0''')],
hints=["math.ceil(deficit / rounding) * rounding"],
wrong=r'''
def margin_call(requirement, collateral_value, mta=250_000, rounding=10_000):
    deficit = requirement - collateral_value
    if deficit < mta:
        return 0
    return round(deficit / rounding) * rounding
''', difficulty=2),
])

checkpoint("u6", "u6cp", "Checkpoint: financing, repo & FX swaps",
"Day counts, repo cash flows, netting and FX forwards: how a prime broker funds its book.",
CP_BODY,
quiz=[
q("$50m at 5.30% ACT/360 for 7 days. Interest?", ["$51,528", "$50,822", "$37,100", "$5,300"], 0, "50m x 0.053 x 7/360 = $51,527.78."),
q("In a **reverse repo**, the prime broker...", ["Borrows cash against its bonds", "Lends cash and receives securities as collateral", "Sells bonds outright", "Buys FX forward"], 1, "Reverse repo = the cash lender's side; it finances clients' long positions."),
q("$100m market value of Treasuries with a 2% haircut. Cash lent in the repo?", ["$100m", "$98m", "$102m", "$2m"], 1, "Cash = MV x (1 - haircut)."),
q("Why can a PB net repo and reverse repo with the same counterparty on its balance sheet?", ["Always allowed", "Only if criteria like same counterparty, same settlement date and a legal right of offset are met", "Never", "Only for FX"], 1, "Balance-sheet netting (e.g. FIN 41 / IFRS offset rules) requires specific conditions."),
q("USD rates above EUR rates. The EURUSD forward vs spot is...", ["Lower", "Higher", "Equal", "Undefined"], 1, "F = S x (1 + r_USD t)/(1 + r_EUR t): the higher-yielding currency trades at a forward discount, so EURUSD forward is above spot."),
q("Swap points are...", ["Forward - spot, in pips", "Spot / forward", "The bid-ask spread", "The repo rate"], 0, "Points = (F - S) / pip size."),
],
exercises=[
ex("Repo cash flows", r'''
Write `repo_trade(mv, haircut, rate, days)` returning a dict with `cash` (MV x (1 - haircut)), `interest` (cash x rate x days/360) and `repurchase` (cash + interest), all rounded to 2 decimals.
''', r'''
def repo_trade(mv, haircut, rate, days):
    ...

print(repo_trade(100_000_000, 0.02, 0.0531, 7))
''', r'''
def repo_trade(mv, haircut, rate, days):
    cash = mv * (1 - haircut)
    interest = cash * rate * days / 360
    return {"cash": round(cash, 2), "interest": round(interest, 2), "repurchase": round(cash + interest, 2)}

print(repo_trade(100_000_000, 0.02, 0.0531, 7))
''', [("example", r'''
r = repo_trade(100_000_000, 0.02, 0.0531, 7)
assert r == {"cash": 98_000_000.0, "interest": 101_185.0, "repurchase": 98_101_185.0}, f"got {r}"
'''), ("zero haircut", r'''assert repo_trade(1_000_000, 0.0, 0.036, 360)["interest"] == 36_000.0''')],
hints=["ACT/360: interest = cash x rate x days / 360"],
wrong=r'''
def repo_trade(mv, haircut, rate, days):
    interest = mv * rate * days / 365
    return {"cash": mv * (1 - haircut), "interest": round(interest, 2), "repurchase": round(mv + interest, 2)}
''', difficulty=1),
ex("FX forward & swap points", r'''
Write `fx_forward(spot, r_base, r_quote, days)` = `spot x (1 + r_quote x days/360) / (1 + r_base x days/360)` and `swap_points(spot, fwd, pip=0.0001)` = `(fwd - spot) / pip` rounded to 1 decimal. For EURUSD, base = EUR, quote = USD.
''', r'''
def fx_forward(spot, r_base, r_quote, days):
    ...

def swap_points(spot, fwd, pip=0.0001):
    ...

f = fx_forward(1.0850, 0.0215, 0.0430, 90)
print(round(f, 5), swap_points(1.0850, f))
''', r'''
def fx_forward(spot, r_base, r_quote, days):
    return spot * (1 + r_quote * days / 360) / (1 + r_base * days / 360)

def swap_points(spot, fwd, pip=0.0001):
    return round((fwd - spot) / pip, 1)

f = fx_forward(1.0850, 0.0215, 0.0430, 90)
print(round(f, 5), swap_points(1.0850, f))
''', [("forward", r'''
f = fx_forward(1.0850, 0.0215, 0.0430, 90)
assert abs(f - 1.0850 * 1.01075 / 1.005375) < 1e-9, f"got {f}" + (": base and quote rates are swapped" if f < 1.085 else "")
'''), ("points", r'''
f = fx_forward(1.0850, 0.0215, 0.0430, 90)
assert swap_points(1.0850, f) == 58.0, f"got {swap_points(1.0850, f)}"
assert swap_points(150.00, 149.20, pip=0.01) == -80.0, "USDJPY pips are 0.01"
''')],
hints=["The quote-currency rate goes in the numerator.", "points = (fwd - spot) / pip, rounded to 1 dp"],
wrong=r'''
def fx_forward(spot, r_base, r_quote, days):
    return spot * (1 + r_base * days / 360) / (1 + r_quote * days / 360)
def swap_points(spot, fwd, pip=0.0001):
    return round((fwd - spot) / pip, 1)
''', difficulty=2),
])
