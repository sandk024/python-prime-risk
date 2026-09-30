from dsl import *

unit("u5", "Margin & Collateral", "Variation vs initial margin, SPAN-like scanning risk, spread charges, haircuts, cheapest-to-deliver allocation and shortfall reports — Clearing Lens, properly.")

lesson("u5l1", "Variation margin & margin calls",
"Compute each account's daily variation margin pays/collects and who gets a call back to initial margin.",
r'''
Futures are **marked to market daily**. **Variation margin (VM)** moves cash for yesterday-to-today settlement changes:

VM = (settleₜ − settleₜ₋₁) × qty × multiplier  (+ = account collects, − = account pays)

**Initial margin (IM)** is collateral posted up front to cover a potential future move over the liquidation period (set by the CCP, e.g. via SPAN/SPAN 2; FCMs can charge clients more).

**Maintenance vs initial**: CME sets a *maintenance* level; *initial* for speculative (non-hedge) accounts is typically **110%** of maintenance. When account equity falls **below maintenance**, the client is called back **up to initial**, not just to maintenance.

Equity (simplified) = collateral value + cumulative VM. For the FCM, calls not met by the deadline become a **credit exposure** — the CCP still collects from the FCM.
''',
examples=[("VM on a short", r'''
settle_prev, settle = 71.40, 73.10
qty, mult = -250, 1000
vm = (settle - settle_prev) * qty * mult
print(f"VM: {vm:,.0f}  → the account PAYS {abs(vm):,.0f}")
''')],
quiz=[q("Maintenance = $1.0m, initial = $1.1m. Equity drops to $0.95m. The call is for…", ["$50k (back to maintenance)", "$150k (back to initial)", "$0 — above 90%", "$1.1m"], 1, "Below maintenance triggers a call back up to the initial level: 1.1m − 0.95m = 150k.")],
exercises=[
ex("VM by account", r'''
Write `vm_by_account(positions, prev, settle, mult)` where positions is a list of `(account, symbol, qty)`. Return dict account → total VM (float), rounded to 2 dp.
''', r'''
positions = [("HF-ALPHA", "ES", 120), ("HF-ALPHA", "CL", -250), ("HF-BETA", "ES", -60), ("HF-BETA", "ZN", 800), ("FO-GAMMA", "CL", 90)]
prev   = {"ES": 5850.25, "CL": 71.40, "ZN": 110.50}
settle = {"ES": 5790.00, "CL": 73.10, "ZN": 110.62}
mult   = {"ES": 50, "CL": 1000, "ZN": 1000}

def vm_by_account(positions, prev, settle, mult):
    ...

print(vm_by_account(positions, prev, settle, mult))
''', r'''
positions = [("HF-ALPHA", "ES", 120), ("HF-ALPHA", "CL", -250), ("HF-BETA", "ES", -60), ("HF-BETA", "ZN", 800), ("FO-GAMMA", "CL", 90)]
prev   = {"ES": 5850.25, "CL": 71.40, "ZN": 110.50}
settle = {"ES": 5790.00, "CL": 73.10, "ZN": 110.62}
mult   = {"ES": 50, "CL": 1000, "ZN": 1000}

def vm_by_account(positions, prev, settle, mult):
    out = {}
    for acct, sym, qty in positions:
        vm = (settle[sym] - prev[sym]) * qty * mult[sym]
        out[acct] = out.get(acct, 0.0) + vm
    return {a: round(v, 2) for a, v in out.items()}

print(vm_by_account(positions, prev, settle, mult))
''', [("values", r'''
r = vm_by_account(positions, prev, settle, mult)
assert r == {"HF-ALPHA": -786500.0, "HF-BETA": 276750.0, "FO-GAMMA": 153000.0}, f"got {r}" + (" — sign flipped? Longs collect when price rises." if r.get("FO-GAMMA", 0) < 0 else "")
''')], hints=["vm = (settle[sym] − prev[sym]) × qty × mult[sym]", "Accumulate with out.get(acct, 0.0) + vm"],
wrong=r'''
def vm_by_account(positions, prev, settle, mult):
    out = {}
    for acct, sym, qty in positions:
        out[acct] = out.get(acct, 0.0) + (prev[sym] - settle[sym]) * qty * mult[sym]
    return out
positions = []; prev = settle = mult = {}
'''),
ex("Margin call to initial", r'''
Write `margin_call(equity, maintenance, initial_ratio=1.10)`:
- initial = maintenance × initial_ratio
- if equity < maintenance → return the amount to bring equity back to **initial**
- otherwise 0
''', r'''
def margin_call(equity, maintenance, initial_ratio=1.10):
    ...
''', r'''
def margin_call(equity, maintenance, initial_ratio=1.10):
    initial = maintenance * initial_ratio
    if equity < maintenance:
        return initial - equity
    return 0.0
''', [("below maintenance", r'''
r = margin_call(950_000, 1_000_000)
assert _close(r, 150_000), f"got {r}" + (" — call back to INITIAL (1.1m), not maintenance" if _close(r, 50_000) else "")
'''), ("between maintenance and initial", r'''assert margin_call(1_050_000, 1_000_000) == 0, "Equity above maintenance (even if below initial) → no call"'''),
("hedge account ratio 1.0", r'''assert _close(margin_call(800_000, 1_000_000, initial_ratio=1.0), 200_000)''')],
hints=["initial = maintenance × initial_ratio", "Only call when equity < maintenance."],
wrong=r'''
def margin_call(equity, maintenance, initial_ratio=1.10):
    return max(0, maintenance - equity)
'''),
])

lesson("u5l2", "SPAN-like scanning risk",
"Rebuild the core of SPAN: revalue each position across price/vol scenarios and take the worst loss — what Clearing Lens simplifies.",
r'''
**SPAN** (Standard Portfolio Analysis of Risk) computes initial margin per *combined commodity* by revaluing the portfolio under **16 scenarios**:

- Price moves of 0, ±⅓, ±⅔, ±3/3 of the **price scan range (PSR)**, each with implied vol **up** and **down** by the **vol scan range** → 14 scenarios
- 2 **extreme** moves (a multiple of PSR) where only a fraction of the loss counts (it's for short deep-OTM options)

For each contract the CCP publishes a **risk array**: the loss per contract in each scenario (positive = loss). Portfolio scenario loss = Σ qty × risk array. **Scanning risk = max(0, worst scenario loss).**

This lesson uses a simplified, clearly-labelled version: extreme = **2 × PSR** with **35%** cover. Parameters vary by CCP/product; CME is also migrating products to **SPAN 2** (a VaR-based model with liquidity & concentration add-ons), so treat this as the concept, not the rulebook.

Because futures are linear, a futures-only book's scan risk is simply |net qty| × PSR × multiplier. Options make it non-linear — that's why the risk arrays matter.
''',
examples=[("The 16 scenarios (futures view)", r'''
PSR = 350.0   # ES points, illustrative
scen = []
for frac in [0, 1/3, -1/3, 2/3, -2/3, 1, -1]:
    for vol in ["up", "down"]:
        scen.append((frac * PSR, 1.0, vol))
scen += [(2 * PSR, 0.35, "extreme up"), (-2 * PSR, 0.35, "extreme down")]
for i, (move, w, v) in enumerate(scen, 1):
    print(f"{i:>2}: move {move:+8.1f} pts  weight {w:.2f}  vol {v}")
''')],
quiz=[q("A client is long 10 Dec ES and short 10 Mar ES. Pure scanning (netting months) shows ~0 risk. What SPAN component addresses this?", ["Short option minimum", "Intra-commodity (calendar) spread charge", "Inter-commodity credit", "Net option value"], 1, "Scanning treats months as perfectly correlated; the intra-commodity spread charge adds back calendar-spread risk.")],
exercises=[
ex("scenarios(psr)", r'''
Write `scenarios(psr, extreme_mult=2, cover=0.35)` returning a list of 16 `(price_move, weight)` tuples:
14 regular (fractions 0, ±1/3, ±2/3, ±1 of psr, **each twice** for vol up/down, weight 1.0) + 2 extreme (±extreme_mult × psr, weight = cover).
Then `futures_scan_risk(qty, psr, mult)` = max(0, max over scenarios of **loss** = −(move × qty × mult) × weight).
''', r'''
def scenarios(psr, extreme_mult=2, cover=0.35):
    ...

def futures_scan_risk(qty, psr, mult):
    ...

print(len(scenarios(350)), futures_scan_risk(-60, 350, 50))
''', r'''
def scenarios(psr, extreme_mult=2, cover=0.35):
    out = []
    for frac in [0, 1/3, -1/3, 2/3, -2/3, 1, -1]:
        out += [(frac * psr, 1.0), (frac * psr, 1.0)]      # vol up, vol down
    out += [(extreme_mult * psr, cover), (-extreme_mult * psr, cover)]
    return out

def futures_scan_risk(qty, psr, mult):
    losses = [-(move * qty * mult) * w for move, w in scenarios(psr)]
    return max(0.0, max(losses))

print(len(scenarios(350)), futures_scan_risk(-60, 350, 50))
''', [("16 scenarios", r'''
s = scenarios(300)
assert len(s) == 16, f"got {len(s)} scenarios; need 14 regular + 2 extreme"
assert sorted(round(m, 6) for m, w in s if w == 1.0) == sorted([round(f * 300, 6) for f in [0, 1/3, -1/3, 2/3, -2/3, 1, -1] for _ in range(2)])
assert sorted((round(m, 6), w) for m, w in s if w != 1.0) == [(-600.0, 0.35), (600.0, 0.35)], "extreme scenarios: ±2 × psr with weight 0.35"
'''), ("futures scan risk", r'''
r = futures_scan_risk(-60, 350, 50)
assert _close(r, 1_050_000), f"short 60 ES, PSR 350 → 60×350×50 = 1,050,000; got {r}"
assert _close(futures_scan_risk(120, 350, 50), 2_100_000)
'''), ("extreme dominates with bigger multiple", r'''
import inspect
assert "extreme_mult" in inspect.signature(scenarios).parameters
s = scenarios(100, extreme_mult=3, cover=0.35)
assert max(abs(m) for m, _ in s) == 300
''')], hints=["Loop over the 7 fractions and append two tuples each.", "loss = −(move × qty × mult) × weight; take the max, floor at 0."],
wrong=r'''
def scenarios(psr, extreme_mult=2, cover=0.35):
    out = [(f * psr, 1.0) for f in [0, 1/3, -1/3, 2/3, -2/3, 1, -1]]
    return out + [(extreme_mult * psr, cover), (-extreme_mult * psr, cover)]
def futures_scan_risk(qty, psr, mult):
    return max((move * qty * mult) * w for move, w in scenarios(psr))
'''),
ex("Portfolio scanning with risk arrays", r'''
Each contract has a 16-value **risk array** (loss per 1 long contract in each scenario; positive = loss). Compute:
- `port` = list of 16 portfolio scenario losses = Σ qty × risk array (use numpy)
- `scan_risk` = max(0, max(port))
- `worst_scenario` = 1-based scenario number of the worst loss
''', r'''
import numpy as np
# Risk arrays (USD loss per LONG contract), 16 scenarios — synthetic
RA = {
    "ES_FUT":      [0, 0, -5833, -5833, 5833, 5833, -11667, -11667, 11667, 11667, -17500, -17500, 17500, 17500, -12250, 12250],
    "ES_C6000":    [-310, 290, -2350, -1750, 1540, 2010, -4730, -4020, 3120, 3590, -7420, -6720, 4410, 4760, -6300, 1720],
    "ES_P5500":    [-420, 380, 2100, 2750, -2420, -1700, 4990, 5890, -3860, -3150, 8420, 9530, -4880, -4290, 7810, -1850],
}
positions = {"ES_FUT": -20, "ES_C6000": 50, "ES_P5500": -40}
port = ...
scan_risk = ...
worst_scenario = ...
''', r'''
import numpy as np
RA = {
    "ES_FUT":      [0, 0, -5833, -5833, 5833, 5833, -11667, -11667, 11667, 11667, -17500, -17500, 17500, 17500, -12250, 12250],
    "ES_C6000":    [-310, 290, -2350, -1750, 1540, 2010, -4730, -4020, 3120, 3590, -7420, -6720, 4410, 4760, -6300, 1720],
    "ES_P5500":    [-420, 380, 2100, 2750, -2420, -1700, 4990, 5890, -3860, -3150, 8420, 9530, -4880, -4290, 7810, -1850],
}
positions = {"ES_FUT": -20, "ES_C6000": 50, "ES_P5500": -40}
port = sum(q * np.array(RA[k], dtype=float) for k, q in positions.items())
scan_risk = max(0.0, float(port.max()))
worst_scenario = int(port.argmax()) + 1
''', [("port", r'''
import numpy as np
exp = sum(q * np.array(RA[k], dtype=float) for k, q in positions.items())
assert len(port) == 16 and np.allclose(port, exp), "port should be the element-wise sum of qty × risk array across contracts"
'''), ("scan_risk", r'''
assert _close(scan_risk, 77_060), f"scan_risk = {scan_risk}; expected 77,060 (risk arrays are LOSSES: take the max, not the min)"
'''), ("worst_scenario", r'''assert worst_scenario == 9, f"worst_scenario = {worst_scenario}; expected 9 (1-based: argmax() + 1)"''')],
hints=["port = sum(q * np.array(RA[k]) for k, q in positions.items())", "Loss is positive in a risk array → worst = port.max(); argmax() + 1 for 1-based"],
wrong=r'''
import numpy as np
RA = {"ES_FUT": [0, 0, -5833, -5833, 5833, 5833, -11667, -11667, 11667, 11667, -17500, -17500, 17500, 17500, -12250, 12250], "ES_C6000": [-310, 290, -2350, -1750, 1540, 2010, -4730, -4020, 3120, 3590, -7420, -6720, 4410, 4760, -6300, 1720], "ES_P5500": [-420, 380, 2100, 2750, -2420, -1700, 4990, 5890, -3860, -3150, 8420, 9530, -4880, -4290, 7810, -1850]}
positions = {"ES_FUT": -20, "ES_C6000": 50, "ES_P5500": -40}
port = sum(q * np.array(RA[k], dtype=float) for k, q in positions.items())
scan_risk = -float(port.min())
worst_scenario = int(port.argmin())
'''),
])

lesson("u5l3", "Spread charges, credits & the short option minimum",
"Turn scanning risk into a full (simplified) SPAN requirement: add calendar-spread charges, subtract inter-commodity credits, apply the SOM floor.",
r'''
SPAN total for a combined commodity (simplified order):

1. **Scanning risk** (worst scenario loss)
2. **+ Intra-commodity spread charge**: scanning nets all months as if perfectly correlated; add a charge per calendar spread. Spreads formed = min(total long contracts, total short contracts) across months.
3. **+ Spot/delivery month charge** (near expiry — skipped here)
4. **− Inter-commodity spread credit**: offsetting positions in correlated products (ES vs NQ, ZN vs ZF, CL vs HO) earn a credit, a % of the smaller leg's risk.
5. **Floor: short option minimum (SOM)** = short option contracts × a per-contract minimum (covers deep-OTM shorts that scan as riskless).

Requirement = max(scan + intra − inter, SOM). Then long option value can offset (net option value) — skipped here.

These are the levers clients argue about: "why is my calendar spread charged so much?" — now you can compute it.
''',
examples=[("Spreads formed", r'''
months = {"ESZ6": 30, "ESH7": -18, "ESM7": -5}
longs = sum(q for q in months.values() if q > 0)
shorts = -sum(q for q in months.values() if q < 0)
print("longs", longs, "shorts", shorts, "→ spreads", min(longs, shorts), "net", longs - shorts)
''')],
quiz=[q("Why does a short deep-OTM put need the short option minimum?", ["It has large delta", "Scanning shows almost no loss, but a gap move could be huge", "Exchange fees", "It's a spread"], 1, "Deep OTM shorts barely move within the scan range but carry tail risk; SOM puts a floor on the requirement.")],
exercises=[
ex("intra_spread_charge()", r'''
Write `intra_spread_charge(month_positions, charge_per_spread)` where month_positions maps contract month → qty. Return spreads formed × charge.
''', r'''
def intra_spread_charge(month_positions, charge_per_spread):
    ...

print(intra_spread_charge({"ESZ6": 30, "ESH7": -18, "ESM7": -5}, 800))
''', r'''
def intra_spread_charge(month_positions, charge_per_spread):
    longs = sum(q for q in month_positions.values() if q > 0)
    shorts = -sum(q for q in month_positions.values() if q < 0)
    return min(longs, shorts) * charge_per_spread

print(intra_spread_charge({"ESZ6": 30, "ESH7": -18, "ESM7": -5}, 800))
''', [("basic", r'''
r = intra_spread_charge({"ESZ6": 30, "ESH7": -18, "ESM7": -5}, 800)
assert r == 18_400, f"got {r}; spreads = min(30 long, 23 short) = 23 → 23 × 800" + (" — you used net qty" if r == 7 * 800 else "")
'''), ("one-sided", r'''assert intra_spread_charge({"CLZ6": 10, "CLF7": 5}, 1500) == 0, "All long → no spreads"'''),
("more shorts than longs", r'''assert intra_spread_charge({"CLZ6": 4, "CLF7": -9, "CLG7": -2}, 1500) == 6_000''')],
hints=["Sum positive quantities, sum |negative| quantities, take the min."],
wrong=r'''
def intra_spread_charge(month_positions, charge_per_spread):
    return abs(sum(month_positions.values())) * charge_per_spread
'''),
ex("span_requirement()", r'''
Write `span_requirement(scan, intra, inter_credit_rate, other_leg_scan, short_options, som_per_contract)`:
- inter credit = inter_credit_rate × min(scan, other_leg_scan)  *(simplified)*
- som = short_options × som_per_contract
- return max(scan + intra − inter credit, som)
''', r'''
def span_requirement(scan, intra, inter_credit_rate, other_leg_scan, short_options, som_per_contract):
    ...

print(span_requirement(1_050_000, 18_400, 0.50, 400_000, 0, 150))
''', r'''
def span_requirement(scan, intra, inter_credit_rate, other_leg_scan, short_options, som_per_contract):
    inter = inter_credit_rate * min(scan, other_leg_scan)
    som = short_options * som_per_contract
    return max(scan + intra - inter, som)

print(span_requirement(1_050_000, 18_400, 0.50, 400_000, 0, 150))
''', [("with credit", r'''
r = span_requirement(1_050_000, 18_400, 0.50, 400_000, 0, 150)
assert _close(r, 868_400), f"got {r}; 1,050,000 + 18,400 − 0.5 × min(1,050,000, 400,000)"
'''), ("SOM floor binds", r'''
r = span_requirement(2_000, 0, 0.0, 0, 200, 150)
assert _close(r, 30_000), f"got {r}; 200 short options × 150 = 30,000 floor"
'''), ("no other leg", r'''assert _close(span_requirement(500_000, 0, 0.6, 0, 0, 0), 500_000)''')],
hints=["inter = rate × min(scan, other_leg_scan)", "return max(scan + intra − inter, som)"],
wrong=r'''
def span_requirement(scan, intra, inter_credit_rate, other_leg_scan, short_options, som_per_contract):
    return scan + intra - inter_credit_rate * other_leg_scan
'''),
])

lesson("u5l4", "Collateral: haircuts, eligibility & concentration",
"Value a client's collateral pool the way the CCP or FCM does — haircuts by asset and tenor, FX add-ons and concentration caps.",
r'''
Not all collateral is worth its market value. The **haircut** covers the risk the collateral itself falls in value before it can be liquidated.

Illustrative schedule (real schedules are CCP/FCM-specific — always use the current published one):

| Asset | Haircut |
|---|---|
| USD cash | 0% |
| UST < 1y / 1–5y / 5–10y / >10y | 0.5% / 2% / 3% / 5% |
| Agency / GSE | 4% |
| G7 sovereign (non-USD) | + FX haircut (e.g. +5%) on top of the tenor haircut |
| Large-cap equities (if eligible) | 20–30% |
| Gold | 15% |

**Eligibility**: some assets aren't accepted at all (e.g. corporate bonds at many CCPs, or equities for certain margin types).
**Concentration limits** cap how much of the requirement one asset class can cover (e.g. equities ≤ 40% of the requirement) — value above the cap gets **no credit**.

Collateral value = Σ MV × (1 − haircut), after eligibility and caps.
''',
examples=[("Tenor bucket lookup", r'''
def ust_haircut(years):
    for limit, hc in [(1, 0.005), (5, 0.02), (10, 0.03)]:
        if years < limit:
            return hc
    return 0.05
for y in [0.25, 3, 7, 25]:
    print(y, ust_haircut(y))
''')],
quiz=[q("A client posts €10m Bunds (3y). Tenor haircut 2%, FX add-on 5%. Collateral value in EUR terms?", ["€9.8m", "€9.3m", "€9.5m", "€10m"], 1, "Haircuts add here: 10 × (1 − 0.02 − 0.05) = €9.3m (then convert at spot).")],
exercises=[
ex("haircut_for(asset)", r'''
Write `haircut_for(asset)` using the schedule above. `asset` is a dict with `type` (`"CASH"`, `"UST"`, `"AGENCY"`, `"SOVEREIGN"`, `"EQUITY"`, `"GOLD"`, other), `years` (tenor, for bonds) and `ccy`.
- CASH: 0 if ccy is USD, else the FX add-on (0.05)
- UST: tenor buckets; SOVEREIGN: UST tenor bucket + 0.05 FX add-on when ccy ≠ USD
- AGENCY 0.04, EQUITY 0.25, GOLD 0.15
- anything else: return `None` (ineligible)
''', r'''
FX_ADDON = 0.05

def haircut_for(asset):
    ...

print(haircut_for({"type": "UST", "years": 7, "ccy": "USD"}))
''', r'''
FX_ADDON = 0.05
UST_BUCKETS = [(1, 0.005), (5, 0.02), (10, 0.03)]

def _tenor_haircut(years):
    for limit, hc in UST_BUCKETS:
        if years < limit:
            return hc
    return 0.05

def haircut_for(asset):
    t, ccy = asset["type"], asset.get("ccy", "USD")
    fx = FX_ADDON if ccy != "USD" else 0.0
    if t == "CASH":
        return fx
    if t == "UST":
        return _tenor_haircut(asset["years"])
    if t == "SOVEREIGN":
        return _tenor_haircut(asset["years"]) + fx
    return {"AGENCY": 0.04, "EQUITY": 0.25, "GOLD": 0.15}.get(t)

print(haircut_for({"type": "UST", "years": 7, "ccy": "USD"}))
''', [("UST buckets", r'''
got = [haircut_for({"type": "UST", "years": y, "ccy": "USD"}) for y in (0.5, 1, 4.9, 5, 9.99, 10, 30)]
assert got == [0.005, 0.02, 0.02, 0.03, 0.03, 0.05, 0.05], f"got {got} — bucket edges: <1y, <5y, <10y, else"
'''), ("cash & FX", r'''
assert haircut_for({"type": "CASH", "ccy": "USD"}) == 0
assert haircut_for({"type": "CASH", "ccy": "EUR"}) == 0.05
r = haircut_for({"type": "SOVEREIGN", "years": 3, "ccy": "EUR"})
assert abs(r - 0.07) < 1e-12, f"3y Bund: 2% tenor + 5% FX = 7%; got {r}"
'''), ("others & ineligible", r'''
assert haircut_for({"type": "EQUITY", "ccy": "USD"}) == 0.25 and haircut_for({"type": "GOLD", "ccy": "USD"}) == 0.15
assert haircut_for({"type": "CORP", "years": 5, "ccy": "USD"}) is None, "Corporate bonds are ineligible here → None"
''')], hints=["Write a helper for the tenor buckets: loop over [(1, .005), (5, .02), (10, .03)], else .05", "Return None for unknown types: dict.get(t) does that for free."],
wrong=r'''
def haircut_for(asset):
    t = asset["type"]
    if t == "CASH": return 0
    if t in ("UST", "SOVEREIGN"):
        y = asset["years"]
        return 0.005 if y <= 1 else 0.02 if y <= 5 else 0.03 if y <= 10 else 0.05
    return {"AGENCY": 0.04, "EQUITY": 0.25, "GOLD": 0.15}.get(t, 0.25)
'''),
ex("pool_value() with a concentration cap", r'''
Write `pool_value(assets, requirement, equity_cap=0.40)` returning the total collateral value (in USD) where:
- each asset's value = `mv_usd` × (1 − haircut) using `haircut_for` (provided); ineligible assets count 0
- total **EQUITY** credit is capped at `equity_cap × requirement`
''', r'''
FX_ADDON = 0.05
def _tenor(y):
    return 0.005 if y < 1 else 0.02 if y < 5 else 0.03 if y < 10 else 0.05
def haircut_for(a):
    fx = FX_ADDON if a.get("ccy", "USD") != "USD" else 0.0
    t = a["type"]
    if t == "CASH": return fx
    if t == "UST": return _tenor(a["years"])
    if t == "SOVEREIGN": return _tenor(a["years"]) + fx
    return {"AGENCY": 0.04, "EQUITY": 0.25, "GOLD": 0.15}.get(t)

def pool_value(assets, requirement, equity_cap=0.40):
    ...

ASSETS = [
    {"type": "CASH", "ccy": "USD", "mv_usd": 2_000_000},
    {"type": "UST", "years": 7, "ccy": "USD", "mv_usd": 10_000_000},
    {"type": "SOVEREIGN", "years": 3, "ccy": "EUR", "mv_usd": 5_000_000},
    {"type": "EQUITY", "ccy": "USD", "mv_usd": 12_000_000},
    {"type": "CORP", "years": 4, "ccy": "USD", "mv_usd": 3_000_000},
]
print(pool_value(ASSETS, 20_000_000))
''', r'''
FX_ADDON = 0.05
def _tenor(y):
    return 0.005 if y < 1 else 0.02 if y < 5 else 0.03 if y < 10 else 0.05
def haircut_for(a):
    fx = FX_ADDON if a.get("ccy", "USD") != "USD" else 0.0
    t = a["type"]
    if t == "CASH": return fx
    if t == "UST": return _tenor(a["years"])
    if t == "SOVEREIGN": return _tenor(a["years"]) + fx
    return {"AGENCY": 0.04, "EQUITY": 0.25, "GOLD": 0.15}.get(t)

def pool_value(assets, requirement, equity_cap=0.40):
    equity, other = 0.0, 0.0
    for a in assets:
        hc = haircut_for(a)
        if hc is None:
            continue
        v = a["mv_usd"] * (1 - hc)
        if a["type"] == "EQUITY":
            equity += v
        else:
            other += v
    return other + min(equity, equity_cap * requirement)

ASSETS = [
    {"type": "CASH", "ccy": "USD", "mv_usd": 2_000_000},
    {"type": "UST", "years": 7, "ccy": "USD", "mv_usd": 10_000_000},
    {"type": "SOVEREIGN", "years": 3, "ccy": "EUR", "mv_usd": 5_000_000},
    {"type": "EQUITY", "ccy": "USD", "mv_usd": 12_000_000},
    {"type": "CORP", "years": 4, "ccy": "USD", "mv_usd": 3_000_000},
]
print(pool_value(ASSETS, 20_000_000))
''', [("capped", r'''
r = pool_value(ASSETS, 20_000_000)
assert _close(r, 24_350_000), f"got {r:,.0f}; cash 2.0m + UST 9.7m + Bund 4.65m + equity min(9.0m, 8.0m cap) = 24.35m" + (" — did you include the CORP bond? It's ineligible." if _close(r, 24_350_000 + 3_000_000 * 0.75) else "")
'''), ("cap not binding", r'''
r = pool_value(ASSETS, 30_000_000)
assert _close(r, 25_350_000), f"with a 30m requirement the equity cap is 12m, so all 9.0m counts → 25.35m; got {r:,.0f}"
'''), ("no assets", r'''assert pool_value([], 1_000_000) == 0''')],
hints=["Track equity value separately from everything else.", "total = other + min(equity, equity_cap × requirement)"],
wrong=r'''
FX_ADDON = 0.05
def haircut_for(a):
    return {"CASH": 0.0, "UST": 0.03, "SOVEREIGN": 0.07, "AGENCY": 0.04, "EQUITY": 0.25, "GOLD": 0.15}.get(a["type"], 0.25)
def pool_value(assets, requirement, equity_cap=0.40):
    return sum(a["mv_usd"] * (1 - haircut_for(a)) for a in assets)
ASSETS = [{"type": "CASH", "ccy": "USD", "mv_usd": 2_000_000}, {"type": "UST", "years": 7, "ccy": "USD", "mv_usd": 10_000_000}, {"type": "SOVEREIGN", "years": 3, "ccy": "EUR", "mv_usd": 5_000_000}, {"type": "EQUITY", "ccy": "USD", "mv_usd": 12_000_000}, {"type": "CORP", "years": 4, "ccy": "USD", "mv_usd": 3_000_000}]
'''),
])

lesson("u5l5", "Collateral optimization: greedy cheapest-to-deliver",
"Decide which assets to post to cover a margin requirement at the lowest funding cost — daily work on a prime financing desk.",
r'''
Every asset has an **opportunity cost** of posting it (what you'd earn by repo-ing it out or using it elsewhere), expressed in bps per year of market value. Posting it earns **credit** = MV × (1 − haircut).

So the cost per $1 of **credit** is `cost_bps / (1 − haircut)`. Greedy algorithm:

1. Compute effective cost for each eligible asset.
2. Sort ascending (cheapest first).
3. Take from each asset until the requirement is covered — the last one partially.

Because assets are divisible (you can post part of a bond position), this is the **fractional knapsack** problem and greedy-by-ratio is **optimal**. With lot sizes, concentration limits or multiple CCPs it becomes a linear/integer program (e.g. `scipy.optimize.linprog`, PuLP) — a good interview talking point.

Operational constraints to mention: settlement cut-offs, substitution rights, and wrong-way risk (don't post a client's own-issuer securities).
''',
examples=[("Effective cost ranking", r'''
assets = [("CASH_USD", 0.0, 45.0), ("UST_2Y", 0.02, 8.0), ("AGENCY", 0.04, 12.0), ("EQ_BASKET", 0.25, 5.0)]
for name, hc, cost in sorted(assets, key=lambda a: a[2] / (1 - a[1])):
    print(f"{name:10} haircut {hc:.0%}  cost {cost:>4} bps  → {cost / (1 - hc):6.2f} bps per $ of credit")
''')],
quiz=[q("Cash costs 45 bps (you could invest it at SOFR+), a UST costs 8 bps with a 2% haircut. Which do you post first?", ["Cash — no haircut", "UST — 8.16 bps per $ credit is far cheaper", "Split 50/50", "Whichever is larger"], 1, "Compare cost per unit of credit: 8/(0.98) ≈ 8.2 bps vs 45 bps.")],
exercises=[
ex("allocate(assets, requirement)", r'''
Write `allocate(assets, requirement)` where assets are dicts `{id, mv, haircut, cost_bps}`. Return `(allocations, shortfall)`:
- `allocations`: list of `(id, mv_used, credit)` in the order used, cheapest cost per credit first (ties → id ascending); skip assets once covered
- `shortfall`: remaining uncovered requirement (0 if covered)
Round mv_used and credit to 2 dp.
''', r'''
ASSETS = [
    {"id": "CASH_USD",  "mv": 5_000_000,  "haircut": 0.00, "cost_bps": 45.0},
    {"id": "UST_2Y",    "mv": 8_000_000,  "haircut": 0.02, "cost_bps": 8.0},
    {"id": "UST_10Y",   "mv": 6_000_000,  "haircut": 0.03, "cost_bps": 7.0},
    {"id": "AGENCY",    "mv": 4_000_000,  "haircut": 0.04, "cost_bps": 12.0},
    {"id": "EQ_BASKET", "mv": 10_000_000, "haircut": 0.25, "cost_bps": 5.0},
]

def allocate(assets, requirement):
    ...

for a in allocate(ASSETS, 20_000_000)[0]:
    print(a)
''', r'''
ASSETS = [
    {"id": "CASH_USD",  "mv": 5_000_000,  "haircut": 0.00, "cost_bps": 45.0},
    {"id": "UST_2Y",    "mv": 8_000_000,  "haircut": 0.02, "cost_bps": 8.0},
    {"id": "UST_10Y",   "mv": 6_000_000,  "haircut": 0.03, "cost_bps": 7.0},
    {"id": "AGENCY",    "mv": 4_000_000,  "haircut": 0.04, "cost_bps": 12.0},
    {"id": "EQ_BASKET", "mv": 10_000_000, "haircut": 0.25, "cost_bps": 5.0},
]

def allocate(assets, requirement):
    order = sorted(assets, key=lambda a: (a["cost_bps"] / (1 - a["haircut"]), a["id"]))
    need = requirement
    out = []
    for a in order:
        if need <= 0:
            break
        credit_avail = a["mv"] * (1 - a["haircut"])
        credit = min(credit_avail, need)
        mv_used = credit / (1 - a["haircut"])
        out.append((a["id"], round(mv_used, 2), round(credit, 2)))
        need -= credit
    return out, round(max(need, 0.0), 2)

for a in allocate(ASSETS, 20_000_000)[0]:
    print(a)
''', [("order", r'''
al, s = allocate(ASSETS, 20_000_000)
ids = [a[0] for a in al]
assert ids == ["EQ_BASKET", "UST_10Y", "UST_2Y"], f"used {ids}; ranking by cost/(1−haircut): EQ 6.67, UST10 7.22, UST2 8.16, AGENCY 12.5, CASH 45" + (" — rank by cost per $ of CREDIT, not raw cost" if ids[:1] == ["EQ_BASKET"] and ids[1:2] != ["UST_10Y"] else "")
'''), ("amounts", r'''
al, s = allocate(ASSETS, 20_000_000)
d = {a[0]: a for a in al}
assert _close(d["EQ_BASKET"][2], 7_500_000) and _close(d["UST_10Y"][2], 5_820_000), f"credits: {[(a[0], a[2]) for a in al]}"
assert _close(d["UST_2Y"][2], 6_680_000) and _close(d["UST_2Y"][1], 6_816_326.53), f"UST_2Y should be partial: credit 6,680,000 → mv 6,816,326.53; got {d['UST_2Y']}"
assert s == 0
'''), ("shortfall", r'''
al, s = allocate(ASSETS, 40_000_000)
assert _close(s, 40_000_000 - 30_000_000 * 0 - (7_500_000 + 5_820_000 + 7_840_000 + 3_840_000 + 5_000_000)), f"shortfall = {s}; total available credit is 30,000,000"
''')], hints=["sorted(assets, key=lambda a: (a['cost_bps'] / (1 - a['haircut']), a['id']))", "credit = min(available credit, need); mv_used = credit / (1 − haircut)"],
wrong=r'''
def allocate(assets, requirement):
    need, out = requirement, []
    for a in sorted(assets, key=lambda a: a["cost_bps"]):
        if need <= 0: break
        take = min(a["mv"], need)
        out.append((a["id"], take, take * (1 - a["haircut"])))
        need -= take
    return out, max(need, 0)
ASSETS = [{"id": "CASH_USD", "mv": 5_000_000, "haircut": 0.00, "cost_bps": 45.0}, {"id": "UST_2Y", "mv": 8_000_000, "haircut": 0.02, "cost_bps": 8.0}, {"id": "UST_10Y", "mv": 6_000_000, "haircut": 0.03, "cost_bps": 7.0}, {"id": "AGENCY", "mv": 4_000_000, "haircut": 0.04, "cost_bps": 12.0}, {"id": "EQ_BASKET", "mv": 10_000_000, "haircut": 0.25, "cost_bps": 5.0}]
'''),
ex("Annual cost & savings", r'''
Write `annual_cost(allocations, assets)` = Σ mv_used × cost_bps / 10,000 (USD per year).
Then compute `savings` = cost of posting **cash first, then the rest in list order** (the naive way: `naive` allocation provided) minus the optimized cost.
''', r'''
ASSETS = [
    {"id": "CASH_USD",  "mv": 5_000_000,  "haircut": 0.00, "cost_bps": 45.0},
    {"id": "UST_2Y",    "mv": 8_000_000,  "haircut": 0.02, "cost_bps": 8.0},
    {"id": "UST_10Y",   "mv": 6_000_000,  "haircut": 0.03, "cost_bps": 7.0},
    {"id": "AGENCY",    "mv": 4_000_000,  "haircut": 0.04, "cost_bps": 12.0},
    {"id": "EQ_BASKET", "mv": 10_000_000, "haircut": 0.25, "cost_bps": 5.0},
]
optimized = [("EQ_BASKET", 10_000_000.0, 7_500_000.0), ("UST_10Y", 6_000_000.0, 5_820_000.0), ("UST_2Y", 6_816_326.53, 6_680_000.0)]
naive = [("CASH_USD", 5_000_000.0, 5_000_000.0), ("UST_2Y", 8_000_000.0, 7_840_000.0), ("UST_10Y", 6_000_000.0, 5_820_000.0), ("AGENCY", 1_395_833.33, 1_340_000.0)]

def annual_cost(allocations, assets):
    ...

savings = ...
print(round(savings, 2))
''', r'''
ASSETS = [
    {"id": "CASH_USD",  "mv": 5_000_000,  "haircut": 0.00, "cost_bps": 45.0},
    {"id": "UST_2Y",    "mv": 8_000_000,  "haircut": 0.02, "cost_bps": 8.0},
    {"id": "UST_10Y",   "mv": 6_000_000,  "haircut": 0.03, "cost_bps": 7.0},
    {"id": "AGENCY",    "mv": 4_000_000,  "haircut": 0.04, "cost_bps": 12.0},
    {"id": "EQ_BASKET", "mv": 10_000_000, "haircut": 0.25, "cost_bps": 5.0},
]
optimized = [("EQ_BASKET", 10_000_000.0, 7_500_000.0), ("UST_10Y", 6_000_000.0, 5_820_000.0), ("UST_2Y", 6_816_326.53, 6_680_000.0)]
naive = [("CASH_USD", 5_000_000.0, 5_000_000.0), ("UST_2Y", 8_000_000.0, 7_840_000.0), ("UST_10Y", 6_000_000.0, 5_820_000.0), ("AGENCY", 1_395_833.33, 1_340_000.0)]

def annual_cost(allocations, assets):
    cost = {a["id"]: a["cost_bps"] for a in assets}
    return sum(mv * cost[i] / 10_000 for i, mv, _credit in allocations)

savings = annual_cost(naive, ASSETS) - annual_cost(optimized, ASSETS)
print(round(savings, 2))
''', [("annual_cost", r'''
r = annual_cost(optimized, ASSETS)
assert _close(r, 14_653.06, 1e-5), f"optimized cost = {r:,.2f}; expected 14,653.06 = 10m×5bp + 6m×7bp + 6.816m×8bp" + (" — divide bps by 10,000" if r > 1e6 else "")
'''), ("savings", r'''assert _close(savings, 20_121.94, 1e-5), f"savings = {savings:,.2f}; expected naive 34,775.00 − optimized 14,653.06 = 20,121.94"
''')], hints=["Build a dict id → cost_bps first", "Cost uses MV used (not credit)"],
wrong=r'''
ASSETS = [{"id": "CASH_USD", "mv": 5_000_000, "haircut": 0.00, "cost_bps": 45.0}, {"id": "UST_2Y", "mv": 8_000_000, "haircut": 0.02, "cost_bps": 8.0}, {"id": "UST_10Y", "mv": 6_000_000, "haircut": 0.03, "cost_bps": 7.0}, {"id": "AGENCY", "mv": 4_000_000, "haircut": 0.04, "cost_bps": 12.0}, {"id": "EQ_BASKET", "mv": 10_000_000, "haircut": 0.25, "cost_bps": 5.0}]
optimized = [("EQ_BASKET", 10_000_000.0, 7_500_000.0), ("UST_10Y", 6_000_000.0, 5_820_000.0), ("UST_2Y", 6_816_326.53, 6_680_000.0)]
naive = [("CASH_USD", 5_000_000.0, 5_000_000.0), ("UST_2Y", 8_000_000.0, 7_840_000.0), ("UST_10Y", 6_000_000.0, 5_820_000.0), ("AGENCY", 1_395_833.33, 1_340_000.0)]
def annual_cost(allocations, assets):
    cost = {a["id"]: a["cost_bps"] for a in assets}
    return sum(credit * cost[i] / 100 for i, mv, credit in allocations)
savings = annual_cost(naive, ASSETS) - annual_cost(optimized, ASSETS)
'''),
])

lesson("u5l6", "Margin shortfall by account (Clearing Lens in pandas)",
"Show which accounts are actually short collateral after haircuts — and whether a client's surplus in one account can cover another.",
r'''
This is the Clearing Lens question: *which accounts are actually short?* Two joins and a groupby:

1. **Requirements** per account (from your scanning calc or the CCP/FCM file).
2. **Collateral** per account: MV × (1 − haircut), summed.
3. **Excess/deficit** = collateral value − requirement (negative = short).

**Netting across accounts** is a legal question, not a math one. A client's surplus in one account can only offset another account's deficit if agreements allow it (same legal entity, cross-margining/netting agreement). Otherwise each deficit is called separately — and the FCM must fund the CCP in the meantime.

In SQL this is `LEFT JOIN` + `GROUP BY` + `CASE WHEN`; in pandas, `merge` + `groupby` + `clip`.
''',
examples=[("clip for deficits", r'''
import pandas as pd
x = pd.Series([250_000, -1_200_000, 0, -40_000], index=["A", "B", "C", "D"])
print("deficits:", (-x).clip(lower=0).to_dict())
''')],
quiz=[q("Client X: account 1 excess +$3m, account 2 deficit −$2m, no netting agreement. Call amount?", ["$0", "$1m", "$2m", "$5m"], 2, "Without a netting agreement the $2m deficit is called on its own; the surplus can't be used.")],
exercises=[
ex("Account excess/deficit", r'''
Build `acct` DataFrame with columns `account, client, requirement, collateral_value, excess` (one row per account in `req`, including accounts with **no collateral**), sorted by excess ascending (worst first).
collateral_value = Σ mv × (1 − haircut) per account.
''', r'''
import pandas as pd
req = pd.DataFrame({"account": ["A1", "A2", "B1", "C1", "C2"],
                    "client":  ["ALPHA", "ALPHA", "BETA", "GAMMA", "GAMMA"],
                    "requirement": [12.0e6, 4.0e6, 9.5e6, 3.0e6, 1.2e6]})
coll = pd.DataFrame({"account": ["A1", "A1", "A2", "B1", "B1", "C1"],
                     "asset": ["UST_2Y", "CASH", "EQ", "UST_10Y", "AGENCY", "CASH"],
                     "mv": [8.0e6, 5.0e6, 4.0e6, 6.0e6, 3.5e6, 3.4e6],
                     "haircut": [0.02, 0.0, 0.25, 0.03, 0.04, 0.0]})
acct = ...
print(acct)
''', r'''
import pandas as pd
req = pd.DataFrame({"account": ["A1", "A2", "B1", "C1", "C2"],
                    "client":  ["ALPHA", "ALPHA", "BETA", "GAMMA", "GAMMA"],
                    "requirement": [12.0e6, 4.0e6, 9.5e6, 3.0e6, 1.2e6]})
coll = pd.DataFrame({"account": ["A1", "A1", "A2", "B1", "B1", "C1"],
                     "asset": ["UST_2Y", "CASH", "EQ", "UST_10Y", "AGENCY", "CASH"],
                     "mv": [8.0e6, 5.0e6, 4.0e6, 6.0e6, 3.5e6, 3.4e6],
                     "haircut": [0.02, 0.0, 0.25, 0.03, 0.04, 0.0]})
cv = (coll.assign(value=coll["mv"] * (1 - coll["haircut"]))
          .groupby("account", as_index=False)["value"].sum()
          .rename(columns={"value": "collateral_value"}))
acct = req.merge(cv, on="account", how="left")
acct["collateral_value"] = acct["collateral_value"].fillna(0.0)
acct["excess"] = acct["collateral_value"] - acct["requirement"]
acct = acct.sort_values("excess").reset_index(drop=True)
print(acct)
''', [("columns & rows", r'''
assert list(acct.columns) == ["account", "client", "requirement", "collateral_value", "excess"], f"columns = {list(acct.columns)}"
assert len(acct) == 5, f"{len(acct)} rows — keep C2 (no collateral) with a LEFT join"
'''), ("values", r'''
a = acct.set_index("account")
assert _close(a.loc["A1", "collateral_value"], 12_840_000), f"A1 collateral = {a.loc['A1','collateral_value']:,.0f}"
assert _close(a.loc["C2", "excess"], -1_200_000), f"C2 excess = {a.loc['C2','excess']} — no collateral → fill 0"
assert _close(a.loc["B1", "excess"], -320_000), f"B1 excess = {a.loc['B1','excess']:,.0f}"
'''), ("sorted worst first", r'''assert acct["account"].tolist() == ["C2", "A2", "B1", "C1", "A1"], f"order = {acct['account'].tolist()}"''')],
hints=["coll.assign(value=mv × (1 − haircut)).groupby('account', as_index=False)['value'].sum()", "req.merge(..., how='left') then fillna(0)"],
wrong=r'''
import pandas as pd
req = pd.DataFrame({"account": ["A1", "A2", "B1", "C1", "C2"], "client": ["ALPHA", "ALPHA", "BETA", "GAMMA", "GAMMA"], "requirement": [12.0e6, 4.0e6, 9.5e6, 3.0e6, 1.2e6]})
coll = pd.DataFrame({"account": ["A1", "A1", "A2", "B1", "B1", "C1"], "asset": ["UST_2Y", "CASH", "EQ", "UST_10Y", "AGENCY", "CASH"], "mv": [8.0e6, 5.0e6, 4.0e6, 6.0e6, 3.5e6, 3.4e6], "haircut": [0.02, 0.0, 0.25, 0.03, 0.04, 0.0]})
cv = coll.groupby("account", as_index=False)["mv"].sum().rename(columns={"mv": "collateral_value"})
acct = req.merge(cv, on="account")
acct["excess"] = acct["collateral_value"] - acct["requirement"]
acct = acct.sort_values("excess").reset_index(drop=True)
'''),
ex("Client-level calls with netting agreements", r'''
Using `acct` (provided) and `netting` (client → True/False), compute `calls`: a Series indexed by client with the amount to call:
- if the client has a netting agreement: call = max(0, −Σ excess across its accounts)
- otherwise: call = Σ of each account's deficit (max(0, −excess))
Include every client (0 if nothing due), sorted by index.
''', r'''
import pandas as pd
acct = pd.DataFrame({"account": ["C2", "A2", "B1", "C1", "A1"], "client": ["GAMMA", "ALPHA", "BETA", "GAMMA", "ALPHA"],
                     "excess": [-1_200_000.0, -1_000_000.0, -320_000.0, 400_000.0, 840_000.0]})
netting = {"ALPHA": True, "BETA": False, "GAMMA": False}
calls = ...
print(calls)
''', r'''
import pandas as pd
acct = pd.DataFrame({"account": ["C2", "A2", "B1", "C1", "A1"], "client": ["GAMMA", "ALPHA", "BETA", "GAMMA", "ALPHA"],
                     "excess": [-1_200_000.0, -1_000_000.0, -320_000.0, 400_000.0, 840_000.0]})
netting = {"ALPHA": True, "BETA": False, "GAMMA": False}
acct["deficit"] = (-acct["excess"]).clip(lower=0)
g = acct.groupby("client").agg(net=("excess", "sum"), gross_def=("deficit", "sum"))
calls = pd.Series({c: max(0.0, -row["net"]) if netting.get(c, False) else row["gross_def"] for c, row in g.iterrows()}).sort_index()
print(calls)
''', [("ALPHA nets", r'''assert _close(calls["ALPHA"], 160_000), f"ALPHA (netting) = {calls['ALPHA']:,.0f}; −1.0m + 0.84m → call 160k"'''),
("GAMMA doesn't net", r'''assert _close(calls["GAMMA"], 1_200_000), f"GAMMA (no netting) = {calls['GAMMA']:,.0f}; C1's surplus can't cover C2 → 1.2m" + (" — you netted GAMMA" if _close(calls['GAMMA'], 800_000) else "")'''),
("all clients, sorted", r'''assert list(calls.index) == ["ALPHA", "BETA", "GAMMA"] and _close(calls["BETA"], 320_000)''')],
hints=["deficit = (−excess).clip(lower=0)", "Group by client: net excess sum and deficit sum; choose per client based on netting."],
wrong=r'''
import pandas as pd
acct = pd.DataFrame({"account": ["C2", "A2", "B1", "C1", "A1"], "client": ["GAMMA", "ALPHA", "BETA", "GAMMA", "ALPHA"], "excess": [-1_200_000.0, -1_000_000.0, -320_000.0, 400_000.0, 840_000.0]})
netting = {"ALPHA": True, "BETA": False, "GAMMA": False}
calls = (-acct.groupby("client")["excess"].sum()).clip(lower=0).sort_index()
'''),
])

lesson("u5l7", "Take it to work: the margin call report",
"Produce the morning margin-call report: who owes what by when, with MTA and rounding applied, plus a draft call notice.",
r'''
The finished product combines everything from this unit:

| Step | Source |
|---|---|
| Requirement per account | scanning + charges (u5l2–3) or the CCP/FCM file |
| Collateral value | haircuts & caps (u5l4) |
| Excess / deficit | merge + groupby (u5l6) |
| Call amount | MTA & rounding rules (u1l5) |
| Output | sorted table + notice text |

Rules used here: **MTA $250,000**, round calls **up to the nearest $10,000**, deadline **T+0 by 13:00 ET** (illustrative — real terms live in each client agreement).

Always generate the notice as a **draft** for a human to review and send — automated sending of margin calls without review is how mistakes reach clients.
''',
examples=[("Rounding up to 10k", r'''
import math
for s in [260_001, 1_200_000, 249_999]:
    print(s, "→", math.ceil(s / 10_000) * 10_000 if s >= 250_000 else 0)
''')],
quiz=[q("Deficit is $249,500 with a $250k MTA. What happens today?", ["Call $250k", "Call $249.5k", "No call, but monitor", "Liquidate"], 2, "Below MTA no call is issued — but it should show on the watch list.")],
exercises=[
ex("call_report(acct)", r'''
Write `call_report(acct, mta=250_000, round_to=10_000)` returning a DataFrame of accounts to call with columns `account, client, deficit, call_amount`:
- deficit = max(0, −excess); keep rows where deficit ≥ mta
- call_amount = deficit rounded **up** to `round_to` (int)
- sort by call_amount desc, then account asc; reset the index
''', r'''
import math
import pandas as pd
ACCT = pd.DataFrame({"account": ["C2", "A2", "B1", "C1", "A1", "D1"], "client": ["GAMMA", "ALPHA", "BETA", "GAMMA", "ALPHA", "DELTA"],
                     "excess": [-1_200_000.0, -1_004_321.0, -249_500.0, 400_000.0, 840_000.0, -250_000.0]})

def call_report(acct, mta=250_000, round_to=10_000):
    ...

print(call_report(ACCT))
''', r'''
import math
import pandas as pd
ACCT = pd.DataFrame({"account": ["C2", "A2", "B1", "C1", "A1", "D1"], "client": ["GAMMA", "ALPHA", "BETA", "GAMMA", "ALPHA", "DELTA"],
                     "excess": [-1_200_000.0, -1_004_321.0, -249_500.0, 400_000.0, 840_000.0, -250_000.0]})

def call_report(acct, mta=250_000, round_to=10_000):
    df = acct.copy()
    df["deficit"] = (-df["excess"]).clip(lower=0)
    df = df[df["deficit"] >= mta].copy()
    df["call_amount"] = df["deficit"].apply(lambda d: int(math.ceil(d / round_to) * round_to))
    df = df.sort_values(["call_amount", "account"], ascending=[False, True]).reset_index(drop=True)
    return df[["account", "client", "deficit", "call_amount"]]

print(call_report(ACCT))
''', [("rows", r'''
r = call_report(ACCT)
assert r["account"].tolist() == ["C2", "A2", "D1"], f"accounts = {r['account'].tolist()} — B1 (249.5k) is under the MTA; D1 is exactly at the MTA (≥) so it's called"
'''), ("amounts", r'''
r = call_report(ACCT)
assert r["call_amount"].tolist() == [1_200_000, 1_010_000, 250_000], f"call_amount = {r['call_amount'].tolist()} — round UP to 10k"
assert list(r.columns) == ["account", "client", "deficit", "call_amount"]
'''), ("params", r'''
r = call_report(ACCT, mta=100_000, round_to=50_000)
assert r["call_amount"].tolist() == [1_200_000, 1_050_000, 250_000, 250_000], f"got {r['call_amount'].tolist()}"
''')], hints=["deficit = (−excess).clip(lower=0)", "math.ceil(d / round_to) * round_to"],
wrong=r'''
import pandas as pd
ACCT = pd.DataFrame({"account": ["C2", "A2", "B1", "C1", "A1", "D1"], "client": ["GAMMA", "ALPHA", "BETA", "GAMMA", "ALPHA", "DELTA"], "excess": [-1_200_000.0, -1_004_321.0, -249_500.0, 400_000.0, 840_000.0, -250_000.0]})
def call_report(acct, mta=250_000, round_to=10_000):
    df = acct.copy()
    df["deficit"] = -df["excess"]
    df = df[df["deficit"] > mta].copy()
    df["call_amount"] = (df["deficit"] / round_to).round().astype(int) * round_to
    return df.sort_values("call_amount", ascending=False).reset_index(drop=True)[["account", "client", "deficit", "call_amount"]]
'''),
ex("Draft the call notice", r'''
Write `call_notice(row, asof)` returning the **draft** text (a string) for one call, exactly:
```
DRAFT - for review before sending
Margin call - GAMMA / C2 - 2026-09-30
Amount due: USD 1,200,000
Deadline: 2026-09-30 13:00 ET
```
`row` is a dict with keys account, client, call_amount; `asof` is a `date`.
''', r'''
from datetime import date

def call_notice(row, asof):
    ...

print(call_notice({"account": "C2", "client": "GAMMA", "call_amount": 1_200_000}, date(2026, 9, 30)))
''', r'''
from datetime import date

def call_notice(row, asof):
    d = asof.isoformat()
    return "\n".join([
        "DRAFT - for review before sending",
        f"Margin call - {row['client']} / {row['account']} - {d}",
        f"Amount due: USD {row['call_amount']:,}",
        f"Deadline: {d} 13:00 ET",
    ])

print(call_notice({"account": "C2", "client": "GAMMA", "call_amount": 1_200_000}, date(2026, 9, 30)))
''', [("exact text", r'''
from datetime import date
got = call_notice({"account": "C2", "client": "GAMMA", "call_amount": 1_200_000}, date(2026, 9, 30))
exp = "DRAFT - for review before sending\nMargin call - GAMMA / C2 - 2026-09-30\nAmount due: USD 1,200,000\nDeadline: 2026-09-30 13:00 ET"
assert got.strip() == exp, "Text differs. Got:\n" + got + "\n\nExpected:\n" + exp
'''), ("another row", r'''
from datetime import date
got = call_notice({"account": "A2", "client": "ALPHA", "call_amount": 1_010_000}, date(2026, 10, 1))
assert "USD 1,010,000" in got and "ALPHA / A2 - 2026-10-01" in got, got
''')], hints=["f\"{amount:,}\" adds thousands separators", "'\\n'.join([...lines...])"],
wrong=r'''
def call_notice(row, asof):
    return f"Margin call - {row['client']} / {row['account']} - {asof}\nAmount due: USD {row['call_amount']}\nDeadline: {asof} 13:00 ET"
'''),
],
work=r'''
**Take it to work — Daily margin call & shortfall report (Clearing Lens v2)**
- Inputs: CCP/FCM requirement file per account, collateral holdings with haircuts, client netting flags.
- Output 1: account-level excess/deficit table (worst first) + client-level call amounts respecting netting agreements.
- Output 2: `call_report` with MTA/rounding and **draft** notices for a human to send.
- Output 3: watch list — deficits under MTA and accounts with < 10% excess.
- Stretch: plug in the greedy allocator to recommend which collateral the client should post (cheapest-to-deliver), and put the whole thing in the Clearing Lens repo with tests.
''')
