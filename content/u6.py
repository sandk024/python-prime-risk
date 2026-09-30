from dsl import *

unit("u6", "Financing: Repo, Funding & FX Swaps", "Day counts, repo and reverse repo, funding cost and spread to SOFR, maturity ladders, netting and FX swap points.")

lesson("u6l1", "Day counts & money-market interest",
"Compute accrued interest and daily funding accruals correctly — ACT/360 vs ACT/365 is a real P&L break.",
r'''
Money-market interest is **simple interest**: interest = principal × rate × (days / basis).

| Convention | Used for |
|---|---|
| **ACT/360** | USD money markets: SOFR, repo, fed funds, T-bill yields; EUR (€STR) |
| **ACT/365F** | GBP (SONIA), JPY (TONA), AUD, CAD |
| 30/360 | many corporate bonds, swaps fixed legs |
| ACT/ACT | US Treasury coupons |

`days` = actual calendar days from start (inclusive) to end (exclusive): `(end - start).days`.

The same rate over a year pays more under ACT/360 (365/360 × rate). On a $1bn overnight book, confusing 360 vs 365 at 5% is ~$1,900 per day.

**Compounded SOFR** over a period (used in loans/FRNs) compounds daily — but repo interest on a term trade is simple interest at the agreed rate.
''',
examples=[("Same rate, different basis", r'''
from datetime import date
p, r = 100_000_000, 0.0530
start, end = date(2026, 9, 30), date(2026, 10, 30)
d = (end - start).days
print("days:", d)
print("ACT/360:", round(p * r * d / 360, 2))
print("ACT/365:", round(p * r * d / 365, 2))
''')],
quiz=[q("$50m overnight at 5.30% ACT/360, Friday to Monday. Interest?", ["$7,361", "$22,083", "$21,781", "$2,650,000"], 1, "Friday→Monday is 3 days: 50m × 0.053 × 3/360 = $22,083.")],
exercises=[
ex("interest()", r'''
Write `interest(principal, rate, start, end, basis="ACT/360")` supporting `"ACT/360"` and `"ACT/365"`; raise `ValueError` for any other basis. Return a float rounded to 2 dp.
''', r'''
from datetime import date

def interest(principal, rate, start, end, basis="ACT/360"):
    ...

print(interest(100_000_000, 0.053, date(2026, 9, 30), date(2026, 10, 30)))
''', r'''
from datetime import date

BASIS_DAYS = {"ACT/360": 360, "ACT/365": 365}

def interest(principal, rate, start, end, basis="ACT/360"):
    if basis not in BASIS_DAYS:
        raise ValueError(f"unsupported basis: {basis}")
    days = (end - start).days
    return round(principal * rate * days / BASIS_DAYS[basis], 2)

print(interest(100_000_000, 0.053, date(2026, 9, 30), date(2026, 10, 30)))
''', [("ACT/360", r'''
from datetime import date
r = interest(100_000_000, 0.053, date(2026, 9, 30), date(2026, 10, 30))
assert r == 441_666.67, f"got {r}; 100m × 5.3% × 30/360 = 441,666.67"
'''), ("ACT/365", r'''
from datetime import date
r = interest(80_000_000, 0.047, date(2026, 10, 2), date(2026, 10, 5), basis="ACT/365")
assert r == 30_904.11, f"got {r}; 80m × 4.7% × 3/365"
'''), ("bad basis", r'''
from datetime import date
try:
    interest(1, 0.05, date(2026, 1, 1), date(2026, 2, 1), basis="30/360")
    assert False, "basis '30/360' should raise ValueError (unsupported here)"
except ValueError:
    pass
''')], hints=["days = (end − start).days", "Map basis → 360 or 365 in a dict; raise ValueError if missing."],
wrong=r'''
def interest(principal, rate, start, end, basis="ACT/360"):
    return round(principal * rate * (end - start).days / 365, 2)
'''),
ex("Accrued-to-date across a book", r'''
For each deal in `deals` compute interest accrued from `start` to `min(asof, maturity)` (ACT/360; 0 if not started). Create `accrued` (dict deal_id → amount rounded to 2dp) and `total_accrued`.
''', r'''
from datetime import date
asof = date(2026, 9, 30)
deals = [
    {"id": "R1", "principal": 250_000_000, "rate": 0.0531, "start": date(2026, 9, 29), "maturity": date(2026, 9, 30)},
    {"id": "R2", "principal": 120_000_000, "rate": 0.0540, "start": date(2026, 9, 1),  "maturity": date(2026, 10, 1)},
    {"id": "R3", "principal":  75_000_000, "rate": 0.0525, "start": date(2026, 8, 15), "maturity": date(2026, 9, 15)},
    {"id": "R4", "principal":  60_000_000, "rate": 0.0550, "start": date(2026, 10, 2), "maturity": date(2026, 11, 2)},
]
accrued = {}
...
total_accrued = ...
''', r'''
from datetime import date
asof = date(2026, 9, 30)
deals = [
    {"id": "R1", "principal": 250_000_000, "rate": 0.0531, "start": date(2026, 9, 29), "maturity": date(2026, 9, 30)},
    {"id": "R2", "principal": 120_000_000, "rate": 0.0540, "start": date(2026, 9, 1),  "maturity": date(2026, 10, 1)},
    {"id": "R3", "principal":  75_000_000, "rate": 0.0525, "start": date(2026, 8, 15), "maturity": date(2026, 9, 15)},
    {"id": "R4", "principal":  60_000_000, "rate": 0.0550, "start": date(2026, 10, 2), "maturity": date(2026, 11, 2)},
]
accrued = {}
for d in deals:
    end = min(asof, d["maturity"])
    days = max(0, (end - d["start"]).days)
    accrued[d["id"]] = round(d["principal"] * d["rate"] * days / 360, 2)
total_accrued = sum(accrued.values())
''', [("per deal", r'''
assert accrued == {"R1": 36_875.0, "R2": 522_000.0, "R3": 339_062.5, "R4": 0.0}, f"accrued = {accrued}" + (" — R4 starts in the future → 0, not negative" if accrued.get("R4", 0) < 0 else "")
'''), ("total", r'''assert _close(total_accrued, 897_937.5), f"total_accrued = {total_accrued}"''')],
hints=["end = min(asof, maturity)", "days = max(0, (end − start).days)"],
wrong=r'''
from datetime import date
asof = date(2026, 9, 30)
deals = [{"id": "R1", "principal": 250_000_000, "rate": 0.0531, "start": date(2026, 9, 29), "maturity": date(2026, 9, 30)}, {"id": "R2", "principal": 120_000_000, "rate": 0.0540, "start": date(2026, 9, 1), "maturity": date(2026, 10, 1)}, {"id": "R3", "principal": 75_000_000, "rate": 0.0525, "start": date(2026, 8, 15), "maturity": date(2026, 9, 15)}, {"id": "R4", "principal": 60_000_000, "rate": 0.0550, "start": date(2026, 10, 2), "maturity": date(2026, 11, 2)}]
accrued = {d["id"]: round(d["principal"] * d["rate"] * (asof - d["start"]).days / 360, 2) for d in deals}
total_accrued = sum(accrued.values())
'''),
])

lesson("u6l2", "Repo & reverse repo: cash, haircuts, funding cost",
"Price repo trades and compute the book's daily funding cost, weighted-average rates and spread to SOFR.",
r'''
A **repo** is a collateralized loan: sell securities today, agree to buy them back later at a higher price.

From the **firm's** perspective:
- **Repo** = *borrow cash*, deliver collateral (funding a long bond inventory or client longs).
- **Reverse repo** = *lend cash*, receive collateral (financing client shorts / investing excess cash / sourcing specials).

Cash lent against collateral with a **haircut** h: cash = MV × (1 − h). (Some markets quote an *initial margin* m instead: cash = MV / (1 + m).)

**Repurchase price** = cash × (1 + rate × days / 360).

Venues: **tri-party** (the agent handles collateral), **bilateral/DVP**, **FICC-cleared** (sponsored / GC), and the SEC's **Treasury clearing mandate** is pushing much more repo into central clearing (phased through 2026–2027) — a direct balance-sheet and netting topic for an FCM/prime broker.

Book metrics: **weighted-average rate** (weights = cash), **net daily interest** (earned on reverse − paid on repo), **spread to SOFR** in bps.
''',
examples=[("One repo, end to end", r'''
mv, haircut, rate, days = 102_000_000, 0.02, 0.0532, 7
cash = mv * (1 - haircut)
repurchase = cash * (1 + rate * days / 360)
print(f"cash {cash:,.2f}  repurchase {repurchase:,.2f}  interest {repurchase - cash:,.2f}")
''')],
quiz=[q("A client is short $200m of USTs and the PB finances it. Which trade does the PB do to source the bonds?", ["Repo", "Reverse repo — lend cash, receive the bonds", "FX swap", "Nothing"], 1, "To borrow securities you reverse them in (lend cash against them); the bonds can be delivered on the client's short.")],
exercises=[
ex("repo_cash() and repurchase_price()", r'''
Write `repo_cash(mv, haircut)` and `repurchase_price(cash, rate, days, basis=360)`. Round both to 2 dp.
''', r'''
def repo_cash(mv, haircut):
    ...

def repurchase_price(cash, rate, days, basis=360):
    ...

c = repo_cash(102_000_000, 0.02)
print(c, repurchase_price(c, 0.0532, 7))
''', r'''
def repo_cash(mv, haircut):
    return round(mv * (1 - haircut), 2)

def repurchase_price(cash, rate, days, basis=360):
    return round(cash * (1 + rate * days / basis), 2)

c = repo_cash(102_000_000, 0.02)
print(c, repurchase_price(c, 0.0532, 7))
''', [("repo_cash", r'''
assert repo_cash(102_000_000, 0.02) == 99_960_000.0, f"got {repo_cash(102_000_000, 0.02)}" + (" — haircut reduces cash: mv × (1 − h)" if repo_cash(102_000_000, 0.02) > 102_000_000 else "")
'''), ("repurchase_price", r'''
r = repurchase_price(99_960_000.0, 0.0532, 7)
assert r == 100_063_403.07, f"got {r}; 99,960,000 × (1 + 0.0532 × 7/360)"
'''), ("basis param", r'''assert repurchase_price(10_000_000, 0.05, 365, basis=365) == 10_500_000.0''')],
hints=["cash = mv × (1 − haircut)", "cash × (1 + rate × days / basis)"],
wrong=r'''
def repo_cash(mv, haircut):
    return round(mv * (1 + haircut), 2)
def repurchase_price(cash, rate, days, basis=360):
    return round(cash * (1 + rate * days / 365), 2)
'''),
ex("Book funding metrics", r'''
From the `book` DataFrame (firm perspective: `REPO` borrows cash, `REVREPO` lends cash) compute:
- `wa_repo` / `wa_rev`: cash-weighted average rate of each side
- `daily_net_interest`: one day's interest earned on REVREPO minus paid on REPO (ACT/360), positive = net earnings
- `repo_spread_bps`: wa_repo minus SOFR, in bps (rounded to 1 dp)
''', r'''
import pandas as pd
SOFR = 0.0530
book = pd.DataFrame({
    "id": ["R1", "R2", "R3", "V1", "V2", "V3"],
    "side": ["REPO", "REPO", "REPO", "REVREPO", "REVREPO", "REVREPO"],
    "cpty": ["BANK-A", "MMF-1", "FICC", "HF-ALPHA", "HF-BETA", "FICC"],
    "cash": [400e6, 250e6, 350e6, 300e6, 150e6, 200e6],
    "rate": [0.0533, 0.0529, 0.0531, 0.0555, 0.0560, 0.0532]})
wa_repo = ...
wa_rev = ...
daily_net_interest = ...
repo_spread_bps = ...
''', r'''
import pandas as pd
SOFR = 0.0530
book = pd.DataFrame({
    "id": ["R1", "R2", "R3", "V1", "V2", "V3"],
    "side": ["REPO", "REPO", "REPO", "REVREPO", "REVREPO", "REVREPO"],
    "cpty": ["BANK-A", "MMF-1", "FICC", "HF-ALPHA", "HF-BETA", "FICC"],
    "cash": [400e6, 250e6, 350e6, 300e6, 150e6, 200e6],
    "rate": [0.0533, 0.0529, 0.0531, 0.0555, 0.0560, 0.0532]})
def wa(df):
    return (df["cash"] * df["rate"]).sum() / df["cash"].sum()
repo, rev = book[book["side"] == "REPO"], book[book["side"] == "REVREPO"]
wa_repo, wa_rev = wa(repo), wa(rev)
daily_net_interest = ((rev["cash"] * rev["rate"]).sum() - (repo["cash"] * repo["rate"]).sum()) / 360
repo_spread_bps = round((wa_repo - SOFR) * 10_000, 1)
''', [("weighted averages", r'''
assert _close(wa_repo, 0.05313), f"wa_repo = {wa_repo:.6f}; expected 0.053130 (cash-weighted, not a simple mean)"
assert _close(wa_rev, 0.0549076923, 1e-6), f"wa_rev = {wa_rev:.6f}"
'''), ("daily_net_interest", r'''
assert _close(daily_net_interest, -48_444.44, 1e-5), f"daily_net_interest = {daily_net_interest:,.2f}; earned on 650m reverse − paid on 1bn repo, /360" + (" — sign: earned minus paid" if _close(daily_net_interest, 48_444.44, 1e-5) else "")
'''), ("repo_spread_bps", r'''assert repo_spread_bps == 1.3, f"repo_spread_bps = {repo_spread_bps}; (0.05313 − 0.0530) × 10,000 = 1.3"''')],
hints=["Weighted average = Σ(cash × rate) / Σ cash per side", "One day ACT/360: Σ(cash × rate) / 360"],
wrong=r'''
import pandas as pd
SOFR = 0.0530
book = pd.DataFrame({"id": ["R1", "R2", "R3", "V1", "V2", "V3"], "side": ["REPO", "REPO", "REPO", "REVREPO", "REVREPO", "REVREPO"], "cash": [400e6, 250e6, 350e6, 300e6, 150e6, 200e6], "rate": [0.0533, 0.0529, 0.0531, 0.0555, 0.0560, 0.0532]})
wa_repo = book[book.side == "REPO"]["rate"].mean()
wa_rev = book[book.side == "REVREPO"]["rate"].mean()
daily_net_interest = (book[book.side == "REVREPO"]["cash"].sum() * wa_rev - book[book.side == "REPO"]["cash"].sum() * wa_repo) / 365
repo_spread_bps = round((wa_repo - SOFR) * 100, 1)
'''),
ex("Carry on a financed bond", r'''
A client is long $100m face of a UST at a clean price of 98.50 (ignore accrued) with a 4.25% coupon, financed in repo at 5.31% with a 2% haircut (the client funds the haircut with its own cash). Over **30 days** compute:
- `coupon_income` = face × coupon × 30/360 *(simplified; UST coupons are really ACT/ACT)*
- `repo_cost` = repo cash × 5.31% × 30/360
- `net_carry` = coupon_income − repo_cost
''', r'''
face, price, coupon = 100_000_000, 98.50, 0.0425
repo_rate, haircut, days = 0.0531, 0.02, 30
coupon_income = ...
repo_cost = ...
net_carry = ...
''', r'''
face, price, coupon = 100_000_000, 98.50, 0.0425
repo_rate, haircut, days = 0.0531, 0.02, 30
mv = face * price / 100
cash = mv * (1 - haircut)
coupon_income = face * coupon * days / 360
repo_cost = cash * repo_rate * days / 360
net_carry = coupon_income - repo_cost
''', [("coupon_income", r'''assert _close(coupon_income, 354_166.67, 1e-6), f"coupon_income = {coupon_income:,.2f}"'''),
("repo_cost", r'''
assert _close(repo_cost, 427_145.25, 1e-6), f"repo_cost = {repo_cost:,.2f}; repo cash = 100m × 98.50% × (1 − 2%) = 96,530,000" + (" — use market value (price/100), not face" if _close(repo_cost, 100e6 * 0.98 * 0.0531 * 30 / 360, 1e-6) else "")
'''), ("net_carry", r'''assert _close(net_carry, -72_978.58, 1e-5), f"net_carry = {net_carry:,.2f} — negative carry (inverted curve: repo > coupon yield)"''')],
hints=["Market value = face × price / 100", "Repo cash = MV × (1 − haircut)"],
wrong=r'''
face, price, coupon = 100_000_000, 98.50, 0.0425
coupon_income = face * coupon * 30 / 360
repo_cost = face * 0.0531 * 30 / 360
net_carry = coupon_income - repo_cost
'''),
])

lesson("u6l3", "The maturity ladder",
"Show how much funding matures in each bucket — the rollover-risk view treasury and regulators ask for.",
r'''
A **maturity ladder** buckets trades by days to maturity and nets funding needs:

| Bucket | Meaning |
|---|---|
| O/N | overnight / open (1 day) |
| 2–7d | this week |
| 8–30d | this month |
| 31–90d | this quarter |
| >90d | term |

For each bucket: **repo maturing** (cash you must re-borrow), **reverse maturing** (cash coming back), **net gap** = reverse − repo, and the **cumulative gap**. A large negative near-dated cumulative gap = heavy rollover risk (think Sept 2019 repo spike, quarter-ends).

`pd.cut(days, bins=[0, 1, 7, 30, 90, np.inf], labels=[...])` assigns buckets; bins are right-inclusive by default: (0,1], (1,7], …

Term funding costs more but reduces rollover risk — the classic treasury trade-off.
''',
examples=[("pd.cut", r'''
import numpy as np
import pandas as pd
days = pd.Series([1, 3, 7, 8, 45, 120])
print(pd.cut(days, bins=[0, 1, 7, 30, 90, np.inf], labels=["O/N", "2-7d", "8-30d", "31-90d", ">90d"]).tolist())
''')],
quiz=[q("With bins [0, 1, 7, 30, …] and default right=True, a trade maturing in exactly 7 days lands in…", ["O/N", "2–7d", "8–30d", "Error"], 1, "Intervals are (1, 7] — right-inclusive, so 7 goes in 2–7d.")],
exercises=[
ex("Bucket the book", r'''
Add `days` (maturity − asof in days) and `bucket` (labels `O/N, 2-7d, 8-30d, 31-90d, >90d` via `pd.cut`) columns to `book`.
''', r'''
import numpy as np
import pandas as pd
asof = pd.Timestamp("2026-09-30")
book = pd.DataFrame({
    "id": ["R1", "R2", "R3", "R4", "R5", "V1", "V2", "V3", "V4"],
    "side": ["REPO"] * 5 + ["REVREPO"] * 4,
    "cash": [400e6, 250e6, 350e6, 150e6, 200e6, 300e6, 150e6, 200e6, 100e6],
    "maturity": pd.to_datetime(["2026-10-01", "2026-10-07", "2026-10-30", "2026-12-15", "2027-03-31",
                                "2026-10-01", "2026-10-02", "2026-11-13", "2026-10-07"])})
LABELS = ["O/N", "2-7d", "8-30d", "31-90d", ">90d"]
''', r'''
import numpy as np
import pandas as pd
asof = pd.Timestamp("2026-09-30")
book = pd.DataFrame({
    "id": ["R1", "R2", "R3", "R4", "R5", "V1", "V2", "V3", "V4"],
    "side": ["REPO"] * 5 + ["REVREPO"] * 4,
    "cash": [400e6, 250e6, 350e6, 150e6, 200e6, 300e6, 150e6, 200e6, 100e6],
    "maturity": pd.to_datetime(["2026-10-01", "2026-10-07", "2026-10-30", "2026-12-15", "2027-03-31",
                                "2026-10-01", "2026-10-02", "2026-11-13", "2026-10-07"])})
LABELS = ["O/N", "2-7d", "8-30d", "31-90d", ">90d"]
book["days"] = (book["maturity"] - asof).dt.days
book["bucket"] = pd.cut(book["days"], bins=[0, 1, 7, 30, 90, np.inf], labels=LABELS)
''', [("days", r'''assert book["days"].tolist() == [1, 7, 30, 76, 182, 1, 2, 44, 7], f"days = {book['days'].tolist()}"'''),
("bucket", r'''
got = [str(b) for b in book["bucket"]]
assert got == ["O/N", "2-7d", "8-30d", "31-90d", ">90d", "O/N", "2-7d", "31-90d", "2-7d"], f"bucket = {got}"
''')], hints=["(book['maturity'] − asof).dt.days", "pd.cut(book['days'], bins=[0, 1, 7, 30, 90, np.inf], labels=LABELS)"],
wrong=r'''
import numpy as np
import pandas as pd
asof = pd.Timestamp("2026-09-30")
book = pd.DataFrame({"id": ["R1", "R2", "R3", "R4", "R5", "V1", "V2", "V3", "V4"], "side": ["REPO"] * 5 + ["REVREPO"] * 4, "cash": [400e6, 250e6, 350e6, 150e6, 200e6, 300e6, 150e6, 200e6, 100e6], "maturity": pd.to_datetime(["2026-10-01", "2026-10-07", "2026-10-30", "2026-12-15", "2027-03-31", "2026-10-01", "2026-10-02", "2026-11-13", "2026-10-07"])})
book["days"] = (book["maturity"] - asof).dt.days
book["bucket"] = pd.cut(book["days"], bins=[0, 1, 7, 30, 90, np.inf], labels=["O/N", "2-7d", "8-30d", "31-90d", ">90d"], right=False)
'''),
ex("Ladder with cumulative gap", r'''
Build `ladder`: DataFrame indexed by bucket (all 5, in order) with columns `REPO`, `REVREPO` (cash maturing, in $m), `gap` = REVREPO − REPO, `cum_gap` = running sum of gap. Then `worst_bucket` = bucket with the most negative `cum_gap`.
''', r'''
import numpy as np
import pandas as pd
book = pd.DataFrame({
    "side": ["REPO"] * 5 + ["REVREPO"] * 4,
    "cash": [400e6, 250e6, 350e6, 150e6, 200e6, 300e6, 150e6, 200e6, 100e6],
    "bucket": pd.Categorical(["O/N", "2-7d", "8-30d", "31-90d", ">90d", "O/N", "2-7d", "31-90d", "2-7d"],
                             categories=["O/N", "2-7d", "8-30d", "31-90d", ">90d"], ordered=True)})
ladder = ...
worst_bucket = ...
print(ladder)
''', r'''
import numpy as np
import pandas as pd
book = pd.DataFrame({
    "side": ["REPO"] * 5 + ["REVREPO"] * 4,
    "cash": [400e6, 250e6, 350e6, 150e6, 200e6, 300e6, 150e6, 200e6, 100e6],
    "bucket": pd.Categorical(["O/N", "2-7d", "8-30d", "31-90d", ">90d", "O/N", "2-7d", "31-90d", "2-7d"],
                             categories=["O/N", "2-7d", "8-30d", "31-90d", ">90d"], ordered=True)})
ladder = (book.pivot_table(index="bucket", columns="side", values="cash", aggfunc="sum", fill_value=0, observed=False) / 1e6)
ladder = ladder[["REPO", "REVREPO"]]
ladder["gap"] = ladder["REVREPO"] - ladder["REPO"]
ladder["cum_gap"] = ladder["gap"].cumsum()
worst_bucket = ladder["cum_gap"].idxmin()
print(ladder)
''', [("structure", r'''
assert [str(i) for i in ladder.index] == ["O/N", "2-7d", "8-30d", "31-90d", ">90d"], f"index = {list(ladder.index)} — keep all buckets in order"
assert list(ladder.columns)[:4] == ["REPO", "REVREPO", "gap", "cum_gap"], f"columns = {list(ladder.columns)}"
'''), ("values ($m)", r'''
assert ladder["gap"].tolist() == [-100.0, 0.0, -350.0, 50.0, -200.0], f"gap = {ladder['gap'].tolist()} (in $m)"
assert ladder["cum_gap"].tolist() == [-100.0, -100.0, -450.0, -400.0, -600.0], f"cum_gap = {ladder['cum_gap'].tolist()}"
'''), ("worst_bucket", r'''assert str(worst_bucket) == ">90d", f"worst_bucket = {worst_bucket}"''')],
hints=["pivot_table(index='bucket', columns='side', values='cash', aggfunc='sum', fill_value=0, observed=False)", "Divide by 1e6; gap.cumsum(); idxmin()"],
wrong=r'''
import pandas as pd
book = pd.DataFrame({"side": ["REPO"] * 5 + ["REVREPO"] * 4, "cash": [400e6, 250e6, 350e6, 150e6, 200e6, 300e6, 150e6, 200e6, 100e6], "bucket": ["O/N", "2-7d", "8-30d", "31-90d", ">90d", "O/N", "2-7d", "31-90d", "2-7d"]})
ladder = book.pivot_table(index="bucket", columns="side", values="cash", aggfunc="sum", fill_value=0) / 1e6
ladder["gap"] = ladder["REPO"] - ladder["REVREPO"]
ladder["cum_gap"] = ladder["gap"].cumsum()
worst_bucket = ladder["cum_gap"].idxmin()
'''),
])

lesson("u6l4", "Netting & the balance sheet",
"Quantify how much balance sheet repo netting saves — the constraint behind every financing desk's pricing.",
r'''
Repo and reverse repo both sit on the balance sheet **gross** unless netting criteria are met. Under US GAAP (ASC 210-20-45-11, "FIN 41") a repo and reverse repo can be presented **net** when, among other conditions, they have:

- the **same counterparty**
- the **same explicit settlement (maturity) date**
- a master netting agreement, and settlement through the same system (e.g. Fedwire / FICC)

That's why **FICC-cleared** repo is so valuable: FICC becomes the single counterparty for everything, enabling netting. The leverage ratio / SLR and G-SIB scores make balance sheet expensive, so desks price netting-friendly trades tighter.

Simplified rule for this lesson: net within each `(counterparty, maturity)` group; the net amount stays on the balance sheet.

Gross BS = Σ |cash| of all trades; Net BS = Σ over groups of |Σ repo cash − Σ reverse cash|.
''',
examples=[("Group and net", r'''
trades = [("FICC", "2026-10-01", "REPO", 500), ("FICC", "2026-10-01", "REV", 350), ("BANK-A", "2026-10-01", "REV", 200)]
from collections import defaultdict
g = defaultdict(float)
for c, m, side, cash in trades:
    g[(c, m)] += cash if side == "REPO" else -cash
print(dict(g), "net BS:", sum(abs(v) for v in g.values()), "gross BS:", sum(t[3] for t in trades))
''')],
quiz=[q("Repo $300m with BANK-A maturing Oct 1, reverse $300m with BANK-A maturing Oct 8. Under the simplified rule, net BS impact?", ["$0", "$300m", "$600m", "$150m"], 2, "Different maturity dates → can't net → both stay gross: $600m.")],
exercises=[
ex("Net balance sheet", r'''
Write `balance_sheet(trades)` returning `(gross, net)` in $ where trades is a DataFrame with `cpty, maturity, side ("REPO"/"REVREPO"), cash`.
''', r'''
import pandas as pd
TRADES = pd.DataFrame({
    "cpty": ["FICC", "FICC", "FICC", "BANK-A", "BANK-A", "MMF-1", "HF-ALPHA"],
    "maturity": ["2026-10-01", "2026-10-01", "2026-10-07", "2026-10-01", "2026-10-08", "2026-10-01", "2026-10-01"],
    "side": ["REPO", "REVREPO", "REVREPO", "REPO", "REVREPO", "REPO", "REVREPO"],
    "cash": [500e6, 350e6, 120e6, 300e6, 300e6, 250e6, 180e6]})

def balance_sheet(trades):
    ...

print(balance_sheet(TRADES))
''', r'''
import numpy as np
import pandas as pd
TRADES = pd.DataFrame({
    "cpty": ["FICC", "FICC", "FICC", "BANK-A", "BANK-A", "MMF-1", "HF-ALPHA"],
    "maturity": ["2026-10-01", "2026-10-01", "2026-10-07", "2026-10-01", "2026-10-08", "2026-10-01", "2026-10-01"],
    "side": ["REPO", "REVREPO", "REVREPO", "REPO", "REVREPO", "REPO", "REVREPO"],
    "cash": [500e6, 350e6, 120e6, 300e6, 300e6, 250e6, 180e6]})

def balance_sheet(trades):
    signed = np.where(trades["side"] == "REPO", trades["cash"], -trades["cash"])
    gross = trades["cash"].sum()
    net = trades.assign(signed=signed).groupby(["cpty", "maturity"])["signed"].sum().abs().sum()
    return float(gross), float(net)

print(balance_sheet(TRADES))
''', [("gross", r'''
g, n = balance_sheet(TRADES)
assert _close(g, 2_000_000_000), f"gross = {g:,.0f}"
'''), ("net", r'''
g, n = balance_sheet(TRADES)
assert _close(n, 1_300_000_000), f"net = {n:,.0f}; only FICC 10/01 nets (500 − 350 = 150m); everything else stays gross" + (" — group by BOTH counterparty and maturity" if _close(n, 1_000_000_000) or _close(n, 1_180_000_000) else "")
''')], hints=["signed = +cash for REPO, −cash for REVREPO", "groupby(['cpty', 'maturity'])['signed'].sum().abs().sum()"],
wrong=r'''
import numpy as np
import pandas as pd
TRADES = pd.DataFrame({"cpty": ["FICC", "FICC", "FICC", "BANK-A", "BANK-A", "MMF-1", "HF-ALPHA"], "maturity": ["2026-10-01", "2026-10-01", "2026-10-07", "2026-10-01", "2026-10-08", "2026-10-01", "2026-10-01"], "side": ["REPO", "REVREPO", "REVREPO", "REPO", "REVREPO", "REPO", "REVREPO"], "cash": [500e6, 350e6, 120e6, 300e6, 300e6, 250e6, 180e6]})
def balance_sheet(trades):
    signed = np.where(trades["side"] == "REPO", trades["cash"], -trades["cash"])
    return float(trades["cash"].sum()), float(trades.assign(s=signed).groupby("cpty")["s"].sum().abs().sum())
'''),
ex("What-if: move a trade to FICC", r'''
Treasury asks: if we **novate HF-ALPHA's reverse repo to FICC** (same maturity), how much balance sheet do we save? Compute `saving` = current net − new net using `balance_sheet` (provided).
''', r'''
import numpy as np
import pandas as pd
TRADES = pd.DataFrame({
    "cpty": ["FICC", "FICC", "FICC", "BANK-A", "BANK-A", "MMF-1", "HF-ALPHA"],
    "maturity": ["2026-10-01", "2026-10-01", "2026-10-07", "2026-10-01", "2026-10-08", "2026-10-01", "2026-10-01"],
    "side": ["REPO", "REVREPO", "REVREPO", "REPO", "REVREPO", "REPO", "REVREPO"],
    "cash": [500e6, 350e6, 120e6, 300e6, 300e6, 250e6, 180e6]})
def balance_sheet(trades):
    signed = np.where(trades["side"] == "REPO", trades["cash"], -trades["cash"])
    return float(trades["cash"].sum()), float(trades.assign(signed=signed).groupby(["cpty", "maturity"])["signed"].sum().abs().sum())

new = TRADES.copy()
# change HF-ALPHA to FICC in `new` (don't modify TRADES)
saving = ...
print(saving)
''', r'''
import numpy as np
import pandas as pd
TRADES = pd.DataFrame({
    "cpty": ["FICC", "FICC", "FICC", "BANK-A", "BANK-A", "MMF-1", "HF-ALPHA"],
    "maturity": ["2026-10-01", "2026-10-01", "2026-10-07", "2026-10-01", "2026-10-08", "2026-10-01", "2026-10-01"],
    "side": ["REPO", "REVREPO", "REVREPO", "REPO", "REVREPO", "REPO", "REVREPO"],
    "cash": [500e6, 350e6, 120e6, 300e6, 300e6, 250e6, 180e6]})
def balance_sheet(trades):
    signed = np.where(trades["side"] == "REPO", trades["cash"], -trades["cash"])
    return float(trades["cash"].sum()), float(trades.assign(signed=signed).groupby(["cpty", "maturity"])["signed"].sum().abs().sum())

new = TRADES.copy()
new.loc[new["cpty"] == "HF-ALPHA", "cpty"] = "FICC"
saving = balance_sheet(TRADES)[1] - balance_sheet(new)[1]
print(saving)
''', [("original untouched", r'''assert (TRADES["cpty"] == "HF-ALPHA").sum() == 1, "Don't modify TRADES — change the copy `new`"'''),
("saving", r'''
assert _close(saving, 300_000_000), f"saving = {saving:,.0f}; FICC 10/01 becomes 500 − 350 − 180 = −30 → |30m| instead of 150m + 180m = 330m → saves 300m"
''')], hints=["new.loc[new['cpty'] == 'HF-ALPHA', 'cpty'] = 'FICC'", "saving = old net − new net"],
wrong=r'''
import numpy as np
import pandas as pd
TRADES = pd.DataFrame({"cpty": ["FICC", "FICC", "FICC", "BANK-A", "BANK-A", "MMF-1", "HF-ALPHA"], "maturity": ["2026-10-01", "2026-10-01", "2026-10-07", "2026-10-01", "2026-10-08", "2026-10-01", "2026-10-01"], "side": ["REPO", "REVREPO", "REVREPO", "REPO", "REVREPO", "REPO", "REVREPO"], "cash": [500e6, 350e6, 120e6, 300e6, 300e6, 250e6, 180e6]})
TRADES.loc[TRADES["cpty"] == "HF-ALPHA", "cpty"] = "FICC"
saving = 180e6
'''),
])

lesson("u6l5", "FX spot, forwards & swap points",
"Price FX forwards and swap points, and back out the implied USD funding rate from an FX swap — how an FCM funds non-USD collateral.",
r'''
**Covered interest parity** links spot S, forward F and the two currencies' rates (quote convention BASE/QUOTE, e.g. EUR/USD = USD per EUR):

F = S × (1 + r_quote × d / B_quote) / (1 + r_base × d / B_base)

- EUR and USD money markets are ACT/360; GBP and JPY use ACT/365.
- **Forward points** = (F − S) × 10,000 for most pairs (× 100 for JPY pairs). Higher-yielding currency trades at a forward *discount*.
- An **FX swap** = spot leg + opposite forward leg. Selling EUR spot / buying it back forward = borrowing USD against EUR. The **implied USD rate**:

r_usd_implied = ((F / S) × (1 + r_eur × d/360) − 1) × 360/d

The gap between implied and actual USD rates is the **cross-currency basis** — when USD is scarce (quarter/year-end), implied USD funding via FX swaps gets expensive. Treasury desks compare repo funding vs FX-swap funding daily.
''',
examples=[("EUR/USD 3-month forward", r'''
S, r_usd, r_eur, d = 1.0850, 0.0530, 0.0200, 91
F = S * (1 + r_usd * d / 360) / (1 + r_eur * d / 360)
print(f"F = {F:.5f}, points = {(F - S) * 10_000:.1f}")
''')],
quiz=[q("USD rates 5.3%, EUR rates 2.0%. EUR/USD forward points are…", ["Negative (EUR at a discount)", "Positive (EUR at a premium)", "Zero", "Can't tell"], 1, "USD (quote) yields more, so F > S: EUR trades at a forward premium, points positive.")],
exercises=[
ex("fx_forward() & points", r'''
Write `fx_forward(spot, r_base, r_quote, days, basis_base=360, basis_quote=360)` and `points(spot, fwd, pip=1e-4)` = (fwd − spot) / pip. Round forward to 5 dp and points to 1 dp.
''', r'''
def fx_forward(spot, r_base, r_quote, days, basis_base=360, basis_quote=360):
    ...

def points(spot, fwd, pip=1e-4):
    ...

f = fx_forward(1.0850, 0.02, 0.053, 91)
print(f, points(1.0850, f))
''', r'''
def fx_forward(spot, r_base, r_quote, days, basis_base=360, basis_quote=360):
    return round(spot * (1 + r_quote * days / basis_quote) / (1 + r_base * days / basis_base), 5)

def points(spot, fwd, pip=1e-4):
    return round((fwd - spot) / pip, 1)

f = fx_forward(1.0850, 0.02, 0.053, 91)
print(f, points(1.0850, f))
''', [("EUR/USD", r'''
f = fx_forward(1.0850, 0.02, 0.053, 91)
assert f == 1.09401, f"got {f}; base = EUR (2%), quote = USD (5.3%)" + (" — rates are swapped" if f < 1.085 else "")
assert points(1.0850, f) == 90.1, f"points = {points(1.0850, f)}"
'''), ("USD/JPY with ACT/365 for JPY", r'''
f = fx_forward(148.50, 0.053, 0.005, 182, basis_base=360, basis_quote=365)
assert f == 144.98543, f"got {f}; base USD ACT/360, quote JPY ACT/365"
assert points(148.50, f, pip=0.01) == -351.5
''')], hints=["F = S × (1 + r_quote × d/B_quote) / (1 + r_base × d/B_base)", "points = (F − S) / pip"],
wrong=r'''
def fx_forward(spot, r_base, r_quote, days, basis_base=360, basis_quote=360):
    return round(spot * (1 + r_base * days / 360) / (1 + r_quote * days / 360), 5)
def points(spot, fwd, pip=1e-4):
    return round((fwd - spot) * 10000, 1)
'''),
ex("Implied USD rate & basis", r'''
Given market spot/forward for EUR/USD, compute `implied_usd` (implied USD rate from the FX swap, ACT/360 both) and `basis_bps` = (implied_usd − actual USD rate) × 10,000, rounded to 1 dp. Then `cheaper` = `"FX_SWAP"` if implied < repo rate else `"REPO"`.
''', r'''
spot, fwd, days = 1.0850, 1.09450, 91
r_eur, usd_rate, repo_rate = 0.0200, 0.0530, 0.0536
implied_usd = ...
basis_bps = ...
cheaper = ...
''', r'''
spot, fwd, days = 1.0850, 1.09450, 91
r_eur, usd_rate, repo_rate = 0.0200, 0.0530, 0.0536
implied_usd = ((fwd / spot) * (1 + r_eur * days / 360) - 1) * 360 / days
basis_bps = round((implied_usd - usd_rate) * 10_000, 1)
cheaper = "FX_SWAP" if implied_usd < repo_rate else "REPO"
''', [("implied_usd", r'''assert _close(implied_usd, 0.0548134, 1e-5), f"implied_usd = {implied_usd:.6f}; expected ≈ 0.054813"'''),
("basis_bps", r'''assert basis_bps == 18.1, f"basis_bps = {basis_bps}; USD via FX swap costs ~18.1 bp over the cash rate here"'''),
("cheaper", r'''assert cheaper == "REPO", f"cheaper = {cheaper!r}; implied 5.48% > repo 5.36%"''')],
hints=["Rearrange F = S(1 + r_usd·d/360)/(1 + r_eur·d/360) for r_usd", "basis = (implied − actual) × 10,000"],
wrong=r'''
spot, fwd, days = 1.0850, 1.09450, 91
r_eur, usd_rate, repo_rate = 0.0200, 0.0530, 0.0536
implied_usd = (fwd / spot - 1) * 360 / days
basis_bps = round((implied_usd - usd_rate) * 100, 1)
cheaper = "FX_SWAP" if implied_usd < repo_rate else "REPO"
'''),
])

lesson("u6l6", "Take it to work: the funding report",
"Produce the financing desk's daily funding report: cost, spread, ladder, counterparty concentration.",
r'''
A daily funding pack answers four questions:

1. **What did funding cost?** Daily interest paid/earned, WA rates, spread to SOFR.
2. **When does it mature?** Maturity ladder + cumulative gap.
3. **Who funds us?** Top counterparties as % of repo borrowing — concentration limits (e.g. no single lender > 25%). Money-market funds can pull on quarter-ends.
4. **What changed?** vs yesterday.

Build each as a function returning a DataFrame; assemble into a dict; export. Same pattern you'll reuse in the capstone.
''',
examples=[("Share of total", r'''
import pandas as pd
s = pd.Series({"BANK-A": 400, "MMF-1": 250, "FICC": 350})
print((s / s.sum()).round(3).sort_values(ascending=False))
''')],
quiz=[q("One money-market fund provides 32% of your repo funding and the limit is 25%. Best first action?", ["Ignore until it matures", "Flag the breach and plan to term-out / diversify lenders", "Delete the trade", "Increase the limit"], 1, "Concentration breaches are reported and remediated with a plan (diversify lenders, term out), not ignored.")],
exercises=[
ex("Counterparty concentration", r'''
Write `concentration(book, limit=0.25)` returning a DataFrame (index = cpty) of **REPO** borrowing with columns `cash`, `share` (of total repo cash), `breach` (share > limit), sorted by share desc.
''', r'''
import pandas as pd
BOOK = pd.DataFrame({
    "side": ["REPO", "REPO", "REPO", "REPO", "REPO", "REVREPO"],
    "cpty": ["MMF-1", "BANK-A", "FICC", "MMF-1", "MMF-2", "HF-ALPHA"],
    "cash": [250e6, 300e6, 350e6, 150e6, 150e6, 300e6]})

def concentration(book, limit=0.25):
    ...

print(concentration(BOOK))
''', r'''
import pandas as pd
BOOK = pd.DataFrame({
    "side": ["REPO", "REPO", "REPO", "REPO", "REPO", "REVREPO"],
    "cpty": ["MMF-1", "BANK-A", "FICC", "MMF-1", "MMF-2", "HF-ALPHA"],
    "cash": [250e6, 300e6, 350e6, 150e6, 150e6, 300e6]})

def concentration(book, limit=0.25):
    repo = book[book["side"] == "REPO"]
    out = repo.groupby("cpty")[["cash"]].sum()
    out["share"] = out["cash"] / out["cash"].sum()
    out["breach"] = out["share"] > limit
    return out.sort_values("share", ascending=False)

print(concentration(BOOK))
''', [("REPO only & aggregated", r'''
c = concentration(BOOK)
assert "HF-ALPHA" not in c.index, "Only REPO (borrowing) counts toward funding concentration"
assert _close(c.loc["MMF-1", "cash"], 400e6), f"MMF-1 cash = {c.loc['MMF-1','cash']:,.0f} — sum both trades"
'''), ("share & breach", r'''
c = concentration(BOOK)
assert list(c.index) == ["MMF-1", "FICC", "BANK-A", "MMF-2"], f"order = {list(c.index)}"
assert _close(c.loc["MMF-1", "share"], 400 / 1200) and bool(c.loc["MMF-1", "breach"]) and bool(c.loc["FICC", "breach"]), "MMF-1 (33%) and FICC (29%) breach 25%"
assert not bool(c.loc["BANK-A", "breach"]), "BANK-A is exactly 25% → not a breach (>)"
''')], hints=["Filter side == 'REPO' first", "groupby('cpty')[['cash']].sum() keeps a DataFrame"],
wrong=r'''
import pandas as pd
BOOK = pd.DataFrame({"side": ["REPO", "REPO", "REPO", "REPO", "REPO", "REVREPO"], "cpty": ["MMF-1", "BANK-A", "FICC", "MMF-1", "MMF-2", "HF-ALPHA"], "cash": [250e6, 300e6, 350e6, 150e6, 150e6, 300e6]})
def concentration(book, limit=0.25):
    out = book.groupby("cpty")[["cash"]].sum()
    out["share"] = out["cash"] / out["cash"].sum()
    out["breach"] = out["share"] >= limit
    return out.sort_values("share", ascending=False)
'''),
ex("funding_report()", r'''
Write `funding_report(book, sofr)` returning a **dict** with:
- `"daily_cost"`: one day's interest **paid** on REPO minus **earned** on REVREPO (ACT/360), rounded to 2 dp (positive = net cost)
- `"wa_repo_bps_vs_sofr"`: (cash-weighted REPO rate − sofr) × 10,000, rounded to 1 dp
- `"on_share"`: fraction of REPO cash maturing in ≤ 1 day (`days` column), rounded to 3 dp
''', r'''
import pandas as pd
BOOK = pd.DataFrame({
    "side": ["REPO", "REPO", "REPO", "REVREPO", "REVREPO"],
    "cash": [400e6, 250e6, 350e6, 300e6, 150e6],
    "rate": [0.0533, 0.0529, 0.0531, 0.0555, 0.0560],
    "days": [1, 1, 30, 1, 14]})

def funding_report(book, sofr):
    ...

print(funding_report(BOOK, 0.0530))
''', r'''
import pandas as pd
BOOK = pd.DataFrame({
    "side": ["REPO", "REPO", "REPO", "REVREPO", "REVREPO"],
    "cash": [400e6, 250e6, 350e6, 300e6, 150e6],
    "rate": [0.0533, 0.0529, 0.0531, 0.0555, 0.0560],
    "days": [1, 1, 30, 1, 14]})

def funding_report(book, sofr):
    repo = book[book["side"] == "REPO"]
    rev = book[book["side"] == "REVREPO"]
    paid = (repo["cash"] * repo["rate"]).sum() / 360
    earned = (rev["cash"] * rev["rate"]).sum() / 360
    wa = (repo["cash"] * repo["rate"]).sum() / repo["cash"].sum()
    return {"daily_cost": round(paid - earned, 2),
            "wa_repo_bps_vs_sofr": round((wa - sofr) * 10_000, 1),
            "on_share": round(repo.loc[repo["days"] <= 1, "cash"].sum() / repo["cash"].sum(), 3)}

print(funding_report(BOOK, 0.0530))
''', [("keys", r'''
r = funding_report(BOOK, 0.0530)
assert isinstance(r, dict) and set(r) == {"daily_cost", "wa_repo_bps_vs_sofr", "on_share"}, f"got {r}"
'''), ("values", r'''
r = funding_report(BOOK, 0.0530)
assert _close(r["daily_cost"], 78_000.0, 1e-6), f"daily_cost = {r['daily_cost']}"
assert r["wa_repo_bps_vs_sofr"] == 1.3, f"wa_repo_bps_vs_sofr = {r['wa_repo_bps_vs_sofr']}"
assert r["on_share"] == 0.65, f"on_share = {r['on_share']} — 650m of 1,000m repo is overnight"
''')], hints=["Split the book into repo and rev first.", "on_share = repo cash with days ≤ 1 / total repo cash"],
wrong=r'''
import pandas as pd
def funding_report(book, sofr):
    paid = (book["cash"] * book["rate"]).sum() / 360
    return {"daily_cost": round(paid, 2), "wa_repo_bps_vs_sofr": round((book["rate"].mean() - sofr) * 10_000, 1), "on_share": round((book["days"] <= 1).mean(), 3)}
BOOK = pd.DataFrame({"side": ["REPO", "REPO", "REPO", "REVREPO", "REVREPO"], "cash": [400e6, 250e6, 350e6, 300e6, 150e6], "rate": [0.0533, 0.0529, 0.0531, 0.0555, 0.0560], "days": [1, 1, 30, 1, 14]})
'''),
],
work=r'''
**Take it to work — Daily repo funding report**
- Inputs: the repo/reverse repo blotter (side, counterparty, cash, rate, start, maturity, venue: tri-party / bilateral / FICC).
- Tables: WA rates and spread to SOFR by venue; daily net interest; maturity ladder with cumulative gap; lender concentration vs limits; gross vs net balance sheet with netting opportunities (what if we novate to FICC?).
- Stretch: compare repo vs FX-swap funding for non-USD collateral using implied rates, and flag quarter-end maturities.
''')
