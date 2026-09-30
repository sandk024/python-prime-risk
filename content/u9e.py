from dsl import *
from u9a import TALK

LAUNCH_SETUP = r'''
import io
import pandas as pd
LAUNCHES = pd.read_csv(io.StringIO("""date,booster,pad,mission
2026-01-05,B1080,SLC-40,Starlink
2026-01-19,B1077,LC-39A,Commercial
2026-02-02,B1080,SLC-40,Starlink
2026-02-20,B1085,SLC-40,Starlink
2026-03-01,B1077,SLC-40,Starlink
2026-03-28,B1080,SLC-40,Rideshare
2026-04-11,B1085,LC-39A,Commercial
2026-04-29,B1080,SLC-40,Starlink
2026-05-15,B1077,SLC-40,Starlink
2026-06-02,B1085,SLC-40,Starlink
2026-07-02,B1080,LC-39A,Commercial
"""))
'''

PO_SETUP = r'''
import io
import numpy as np
import pandas as pd
ASOF = pd.Timestamp("2026-09-30")
POS = pd.read_csv(io.StringIO("""po,supplier,part,ordered,promised,delivered
P1,AeroCast,valve,2026-06-01,2026-07-01,2026-06-28
P2,AeroCast,valve,2026-06-15,2026-07-15,2026-07-22
P3,AeroCast,manifold,2026-07-01,2026-08-15,
P4,Nordic Alloys,sheet,2026-06-10,2026-07-10,2026-07-09
P5,Nordic Alloys,sheet,2026-07-10,2026-08-10,2026-08-10
P6,Nordic Alloys,bar,2026-08-20,2026-10-20,
P7,Helix Avionics,board,2026-05-01,2026-06-15,2026-07-30
P8,Helix Avionics,board,2026-07-01,2026-08-15,2026-08-12
P9,Helix Avionics,harness,2026-08-01,2026-09-15,
"""), parse_dates=["ordered", "promised", "delivered"])
'''

OPEN_SETUP = r'''
import io
import pandas as pd
LAUNCH_DATE = pd.Timestamp("2026-11-01")
SLIP_DAYS = {"AeroCast": 12, "Nordic Alloys": 0, "Helix Avionics": 30}
BOM = {"manifold": 1, "bar": 4, "harness": 2, "valve": 6}
OPEN = pd.read_csv(io.StringIO("""po,supplier,part,promised,delivered
P2,AeroCast,valve,2026-07-15,2026-07-22
P3,AeroCast,manifold,2026-10-10,
P6,Nordic Alloys,bar,2026-10-16,
P9,Helix Avionics,harness,2026-09-25,
P10,Helix Avionics,antenna,2026-12-01,
"""), parse_dates=["promised", "delivered"])
'''

lesson("u9l9", "SpaceX-style analytics: cadence & supply chain",
"Business, finance and supply-chain analyst rounds use operational data: launch cadence, fleet reuse, supplier lead times and on-time delivery.",
r'''
SpaceX business/ops analytics interviews typically give a small operational dataset and ask practical questions quickly. **All data here is synthetic.**

Common asks and the pandas move:
- **Cadence**: launches per month/quarter: `dt.to_period("Q")` + `value_counts()`, or `resample("QE")` on a DatetimeIndex.
- **Turnaround**: days between consecutive flights of the same booster: sort, then `groupby("booster")["date"].diff()`.
- **Reuse**: flights per booster, max reuse: `value_counts()`.
- **Supply chain**: supplier on-time rate (delivered <= promised), average lead time (delivered - ordered), parts that will be late for a launch: date math + `map` + filters.

Communicate like an analyst: a one-line answer, the number, then a caveat ("small sample", "one outlier drives the mean; the median is 51 days").
''',
talk=r'''
Say: "Let me check the shape and dtypes first... dates are strings, so I'll parse them... there are 3 missing delivery dates; I'll treat those as not yet delivered, and late if past the promise date." Then answer, then caveat. Offer a follow-up: "With more time I'd break turnaround down by pad and mission type."
''', timed=20,
examples=[("Quarterly cadence", r'''
import pandas as pd
d = pd.to_datetime(["2026-01-05", "2026-01-19", "2026-02-02", "2026-04-11", "2026-04-29", "2026-05-15", "2026-07-02"])
s = pd.Series(1, index=d)
print(s.resample("QE").sum())
''')],
quiz=[q("Booster turnaround times (days): 21, 25, 27, 29, 160. Which summary best describes typical turnaround?", ["Mean = 52.4 days", "Median = 27 days", "Max = 160 days", "Sum = 262 days"], 1, "One refurbishment outlier inflates the mean; the median is the typical value (report the outlier separately).")],
exercises=[
ex("Launch cadence & booster turnaround", r'''
From `LAUNCHES` compute:
- `per_quarter`: Series of launch counts per calendar quarter, labelled like `"2026Q1"` (use `dt.to_period("Q").astype(str)`), sorted by quarter
- `turnaround`: Series of days between consecutive flights of the same booster (drop the NaN first flights)
- `median_turnaround` (float) and `most_flown` (booster with the most flights; ties go to the smallest id)
''', LAUNCH_SETUP + r'''
per_quarter = ...
turnaround = ...
median_turnaround = ...
most_flown = ...
''', LAUNCH_SETUP + r'''
df = LAUNCHES.assign(date=pd.to_datetime(LAUNCHES["date"])).sort_values(["booster", "date"])
per_quarter = df["date"].dt.to_period("Q").astype(str).value_counts().sort_index()
turnaround = df.groupby("booster")["date"].diff().dt.days.dropna()
median_turnaround = float(turnaround.median())
counts = df["booster"].value_counts()
most_flown = sorted(counts[counts == counts.max()].index)[0]
print(per_quarter, turnaround.tolist(), median_turnaround, most_flown)
''', [("per_quarter", r'''
d = {str(k): int(v) for k, v in per_quarter.items()}
assert d == {"2026Q1": 6, "2026Q2": 4, "2026Q3": 1}, f"per_quarter = {d}"
'''), ("turnaround", r'''
t = sorted(int(x) for x in turnaround)
assert t == [28, 32, 41, 50, 52, 54, 64, 75], f"turnaround = {t}: diff within each booster after sorting by date"
assert median_turnaround == 51.0, f"median_turnaround = {median_turnaround}"
'''), ("most_flown", r'''assert most_flown == "B1080", f"most_flown = {most_flown}"''')],
hints=["pd.to_datetime, then sort by ['booster', 'date']", "df.groupby('booster')['date'].diff().dt.days"],
wrong=LAUNCH_SETUP + r'''
df = LAUNCHES.assign(date=pd.to_datetime(LAUNCHES["date"]))
per_quarter = df["date"].dt.month.value_counts()
turnaround = df["date"].diff().dt.days.dropna()
median_turnaround = float(turnaround.mean())
most_flown = df["booster"].iloc[0]
'''),
ex("Supplier scorecard", r'''
From `POS` (purchase orders) compute `scorecard`: a DataFrame indexed by supplier with columns
- `orders`: count of POs
- `on_time_rate`: share delivered <= promised, computed over **due** orders only: delivered orders, plus undelivered orders whose promise date is before `ASOF` (those count as late). Undelivered orders not yet due are excluded.
- `avg_lead_days`: mean of (delivered - ordered) in days, delivered orders only

Sort by `on_time_rate` ascending.
''', PO_SETUP + r'''
scorecard = ...
print(scorecard)
''', PO_SETUP + r'''
df = POS.copy()
delivered = df["delivered"].notna()
due = delivered | (df["promised"] < ASOF)
df["on_time"] = delivered & (df["delivered"] <= df["promised"])
df["lead"] = (df["delivered"] - df["ordered"]).dt.days
scorecard = pd.DataFrame({
    "orders": df.groupby("supplier").size(),
    "on_time_rate": df[due].groupby("supplier")["on_time"].mean(),
    "avg_lead_days": df[delivered].groupby("supplier")["lead"].mean(),
}).sort_values("on_time_rate", kind="stable")
print(scorecard)
''', [("structure", r'''
assert list(scorecard.columns) == ["orders", "on_time_rate", "avg_lead_days"], f"columns = {list(scorecard.columns)}"
assert scorecard["orders"].to_dict() == {"AeroCast": 3, "Helix Avionics": 3, "Nordic Alloys": 3}, f"orders = {scorecard['orders'].to_dict()}"
'''), ("on_time_rate", r'''
r = {k: round(float(v), 4) for k, v in scorecard["on_time_rate"].items()}
assert r == {"AeroCast": 0.3333, "Helix Avionics": 0.3333, "Nordic Alloys": 1.0}, f"on_time_rate = {r}: P3 and P9 are overdue & undelivered (late); P6 isn't due yet (excluded)"
'''), ("avg_lead_days", r'''
r = {k: round(float(v), 2) for k, v in scorecard["avg_lead_days"].items()}
assert r == {"AeroCast": 32.0, "Helix Avionics": 66.0, "Nordic Alloys": 30.0}, f"avg_lead_days = {r} (delivered orders only)"
'''), ("sorted", r'''assert list(scorecard["on_time_rate"]) == sorted(scorecard["on_time_rate"]), "Sort by on_time_rate ascending"''')],
hints=["due = delivered OR promised < ASOF; compute the rate over due orders only", "on_time = delivered AND delivered <= promised"],
wrong=PO_SETUP + r'''
d = POS.dropna(subset=["delivered"]).copy()
d["on_time"] = d["delivered"] <= d["promised"]
d["lead"] = (d["delivered"] - d["ordered"]).dt.days
scorecard = d.groupby("supplier").agg(orders=("po", "size"), on_time_rate=("on_time", "mean"), avg_lead_days=("lead", "mean")).sort_values("on_time_rate")
'''),
ex("Parts at risk for a launch", r'''
A launch on `LAUNCH_DATE` needs the parts in `BOM`. Each **undelivered** PO for a BOM part is expected on `promised + the supplier's average slip` (`SLIP_DAYS`). Return `at_risk`: a sorted list of parts whose expected arrival is **after** `LAUNCH_DATE - 14 days` (the integration buffer). Delivered parts and non-BOM parts are never at risk.
''', OPEN_SETUP + r'''
at_risk = ...
print(at_risk)
''', OPEN_SETUP + r'''
cutoff = LAUNCH_DATE - pd.Timedelta(days=14)
o = OPEN[OPEN["delivered"].isna() & OPEN["part"].isin(list(BOM))].copy()
o["expected"] = o["promised"] + pd.to_timedelta(o["supplier"].map(SLIP_DAYS), unit="D")
at_risk = sorted(o.loc[o["expected"] > cutoff, "part"])
print(o[["part", "promised", "expected"]], "cutoff:", cutoff.date(), at_risk)
''', [("at_risk", r'''
r = list(at_risk)
msg = f"at_risk = {r}; cutoff = Oct 18. manifold Oct 10 + 12 = Oct 22 (late), bar Oct 16 + 0 (ok), harness Sep 25 + 30 = Oct 25 (late)"
if "antenna" in r: msg += "; antenna isn't in the BOM"
assert r == ["harness", "manifold"], msg
''')], hints=["cutoff = LAUNCH_DATE - pd.Timedelta(days=14)", "expected = promised + pd.to_timedelta(slip_series, unit='D')"],
wrong=OPEN_SETUP + r'''
cutoff = LAUNCH_DATE - pd.Timedelta(days=14)
o = OPEN[OPEN["delivered"].isna()]
at_risk = sorted(o.loc[o["promised"] > cutoff, "part"])
'''),
])

ATTR_SETUP = r'''
import io
import pandas as pd
MULT = {"ES": 50, "CL": 1000, "ZN": 1000}
MARKS = {"ES": 5795.0, "CL": 72.90, "ZN": 110.70}
TRADES = pd.read_csv(io.StringIO("""trade_id,desk,symbol,qty,price
T1,delta-one,ES,10,5790.00
T2,Delta-One ,ES,-4,5798.00
T3,rates,ZN,200,110.62
T3,rates,ZN,250,110.62
T4,commodities,CL,-30,73.10
T5,COMMODITIES,CL,10,72.80
"""))
'''

lesson("u9l10", "Mock interview (timed)",
"A realistic 30-minute mixed round: one algorithm problem and one data problem, graded on correctness and clarity.",
r'''
**Format**: start the timer, read both prompts, then talk through a plan for each *before* coding (write it as comments first). Aim for about 12 minutes per problem, leaving time to test edge cases.

The rubric interviewers commonly use:
- **Communication**: clarified requirements, narrated the approach, stated complexity
- **Problem solving**: found an efficient approach, handled edge cases
- **Code quality**: readable names, small functions, no dead code
- **Verification**: tested with examples, caught their own bugs

Afterwards, write down what took longest, what you'd say differently, and one pattern to review. Redo this lesson on different days; the Review queue will bring it back.
''',
talk=TALK, timed=30,
examples=[("Plan-as-comments template", r'''
def solve(data):
    # 1. Clarify: input = list of (account, breach_minutes); output = top 3 accounts
    # 2. Approach: aggregate with a dict (O(n)), then heapq.nlargest (O(n log k))
    # 3. Edge cases: empty input, ties -> alphabetical
    pass
print("Write the plan first, then fill it in.")
''')],
quiz=[q("You finished early with a working solution. Best use of the remaining time?", ["Stop talking", "Walk through edge cases, state complexity, suggest improvements", "Rewrite it in another language", "Ask for the next question immediately"], 1, "Verification and evaluation are graded; use the time to show them.")],
exercises=[
ex("Problem 1: rate-limit breaches", r'''
An order gateway allows at most `limit` orders per client in any **rolling 60-second window** (the window ending at t is (t-60, t]). Given time-sorted `(t_seconds, client)` events, return a **sorted list** of clients who ever exceeded the limit. Aim for O(n) with a deque per client.
''', r'''
from collections import defaultdict, deque

def breaching_clients(events, limit):
    ...

E = [(0, "A"), (10, "A"), (20, "B"), (30, "A"), (59, "A"), (61, "A"), (65, "B"), (70, "A"), (125, "A")]
print(breaching_clients(E, 3))
''', r'''
from collections import defaultdict, deque

def breaching_clients(events, limit):
    windows = defaultdict(deque)
    breached = set()
    for t, client in events:
        w = windows[client]
        w.append(t)
        while w and w[0] <= t - 60:
            w.popleft()
        if len(w) > limit:
            breached.add(client)
    return sorted(breached)

E = [(0, "A"), (10, "A"), (20, "B"), (30, "A"), (59, "A"), (61, "A"), (65, "B"), (70, "A"), (125, "A")]
print(breaching_clients(E, 3))
''', [("example", r'''
E = [(0, "A"), (10, "A"), (20, "B"), (30, "A"), (59, "A"), (61, "A"), (65, "B"), (70, "A"), (125, "A")]
r = breaching_clients(E, 3)
assert r == ["A"], f"got {r}; A has 4 orders in (-1, 59]"
'''), ("window boundary", r'''
assert breaching_clients([(0, "X"), (30, "X"), (60, "X")], 2) == [], "At t=60 the window is (0, 60]: the order at t=0 has dropped out"
assert breaching_clients([(0, "X"), (30, "X"), (59, "X")], 2) == ["X"]
'''), ("scale", r'''
import time
E = [(i, f"C{i % 50}") for i in range(100000)]
t = time.time(); r = breaching_clients(E, 2); dt = time.time() - t
assert r == [] and dt < 2.0, f"r = {r[:3]}..., took {dt:.2f}s: pop old timestamps from a per-client deque instead of rescanning"
''')], hints=["Per-client deque of timestamps; pop from the left while w[0] <= t - 60.", "If len(w) > limit, record the client."],
wrong=r'''
def breaching_clients(events, limit):
    from collections import defaultdict, deque
    windows = defaultdict(deque); out = set()
    for t, c in events:
        w = windows[c]; w.append(t)
        while w and w[0] < t - 60:
            w.popleft()
        if len(w) > limit: out.add(c)
    return sorted(out)
'''),
ex("Problem 2: desk P&L attribution", r'''
`TRADES` is messy: desk names have mixed case and stray spaces, and a corrected trade reappears with the same trade_id (keep the **last** one). Using `MARKS` (end-of-day prices) and `MULT`, compute `attribution`: a DataFrame indexed by **upper-case, stripped desk** with columns `traded_notional` (sum of qty x price x mult) and `mtm_pnl` (sum of qty x (mark - price) x mult), sorted by mtm_pnl descending.
''', ATTR_SETUP + r'''
attribution = ...
print(attribution)
''', ATTR_SETUP + r'''
t = TRADES.drop_duplicates(subset=["trade_id"], keep="last").copy()
t["desk"] = t["desk"].str.strip().str.upper()
m = t["symbol"].map(MULT)
t["traded_notional"] = t["qty"] * t["price"] * m
t["mtm_pnl"] = t["qty"] * (t["symbol"].map(MARKS) - t["price"]) * m
attribution = t.groupby("desk")[["traded_notional", "mtm_pnl"]].sum().sort_values("mtm_pnl", ascending=False)
print(attribution)
''', [("desks", r'''assert sorted(attribution.index) == ["COMMODITIES", "DELTA-ONE", "RATES"], f"index = {list(attribution.index)}: normalize desk names (strip + upper)"'''),
("mtm_pnl", r'''
r = {k: round(float(v), 2) for k, v in attribution["mtm_pnl"].items()}
hint = ": T3 appears twice; keep only the last version" if r.get("RATES", 0) > 20_000 else ""
assert r == {"RATES": 20_000.0, "COMMODITIES": 7_000.0, "DELTA-ONE": 3_100.0}, f"mtm_pnl = {r}{hint}"
assert list(attribution.index) == ["RATES", "COMMODITIES", "DELTA-ONE"], "Sort by mtm_pnl descending"
'''), ("traded_notional", r'''assert _close(attribution.loc["DELTA-ONE", "traded_notional"], 1_735_400.0), f"DELTA-ONE traded_notional = {attribution.loc['DELTA-ONE', 'traded_notional']:,.0f}"''')],
hints=["drop_duplicates(subset=['trade_id'], keep='last')", "mtm = qty x (mark - price) x mult"],
wrong=ATTR_SETUP + r'''
t = TRADES.copy()
t["desk"] = t["desk"].str.upper()
m = t["symbol"].map(MULT)
t["traded_notional"] = t["qty"] * t["price"] * m
t["mtm_pnl"] = t["qty"] * (t["symbol"].map(MARKS) - t["price"]) * m
attribution = t.groupby("desk")[["traded_notional", "mtm_pnl"]].sum().sort_values("mtm_pnl", ascending=False)
'''),
])
