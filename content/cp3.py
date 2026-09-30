from dsl import *
from cp1 import CP_BODY

checkpoint("u7", "u7cp", "Checkpoint: market risk",
"VaR, expected shortfall, stress tests, limits and option greeks: the daily risk report.",
CP_BODY,
quiz=[
q("99% 1-day VaR of $3m means...", ["You can't lose more than $3m", "On about 1 day in 100, losses are expected to exceed $3m", "The average loss is $3m", "Tomorrow you lose $3m"], 1, "VaR is a quantile, not a worst case."),
q("Expected shortfall at the same confidence is always...", ["Smaller than VaR", "At least as large as VaR", "Equal to VaR", "Unrelated"], 1, "ES averages the losses beyond the VaR point, so ES >= VaR."),
q("1-day VaR is $2m. The square-root-of-time 10-day VaR?", ["$20m", "$6.3m", "$2m", "$4m"], 1, "2m x sqrt(10) = $6.32m (assumes i.i.d. returns and a constant position)."),
q("Which measure is subadditive (diversification never increases it)?", ["Historical VaR", "Expected shortfall", "Both", "Neither"], 1, "ES is coherent; VaR can violate subadditivity."),
q("Delta of a deep in-the-money call on a future (Black-76, near zero rates)?", ["About 0", "About 0.5", "About 1", "About -1"], 2, "Deep ITM calls move almost one-for-one with the future."),
q("Why run stress tests in addition to VaR?", ["They're required to be smaller", "They capture extreme or unprecedented moves outside the historical window", "They replace margin", "They're faster"], 1, "Stress tests probe tail scenarios that VaR's window may not contain."),
],
exercises=[
ex("VaR and ES from scenario P&L", r'''
Write `var_es(pnl, conf)` returning `(var, es)` as positive numbers using the course conventions:
- VaR = `-np.percentile(pnl, 100 * (1 - conf))`
- ES = the negative mean of the worst `k = ceil(N x (1 - conf))` outcomes (round before `ceil` to avoid float error, as in the ES lesson)
''', r'''
import math
import numpy as np

def var_es(pnl, conf=0.99):
    ...

rng = np.random.default_rng(7)
PNL = rng.normal(0, 1_000_000, 500)
print(var_es(PNL, 0.99))
''', r'''
import math
import numpy as np

def var_es(pnl, conf=0.99):
    pnl = np.asarray(pnl, dtype=float)
    var = -np.percentile(pnl, 100 * (1 - conf))
    k = math.ceil(round(len(pnl) * (1 - conf), 9))
    es = -np.sort(pnl)[:k].mean()
    return float(var), float(es)

rng = np.random.default_rng(7)
PNL = rng.normal(0, 1_000_000, 500)
print(var_es(PNL, 0.99))
''', [("small example", r'''
v, e = var_es(list(range(-10, 90)), 0.95)
assert _close(v, -np.percentile(np.arange(-10, 90), 5)), f"var = {v}"
assert _close(e, 8.0), f"es = {e}: worst 5 of 100 are -10..-6, mean -8 -> 8"
'''), ("ES >= VaR", r'''
v, e = var_es(PNL, 0.99)
assert e >= v > 0, f"var = {v:,.0f}, es = {e:,.0f}"
''')],
hints=["np.sort(pnl)[:k] gives the k worst outcomes", "math.ceil(round(len(pnl) * (1 - conf), 9))"],
wrong=r'''
import numpy as np
def var_es(pnl, conf=0.99):
    pnl = np.asarray(pnl, dtype=float)
    var = np.percentile(pnl, 100 * conf)
    return float(var), float(pnl.mean())
''', difficulty=2),
ex("Limit utilization report", r'''
Write `limit_report(usage, limits, warn=0.8)` where both are dicts desk -> amount. Return a list of `(desk, utilization, status)` for every desk in `limits`, sorted by utilization descending, where utilization = usage / limit rounded to 3 dp (missing usage = 0), status = `"BREACH"` if > 1, `"WARN"` if >= warn, else `"OK"`.
''', r'''
def limit_report(usage, limits, warn=0.8):
    ...

USAGE = {"rates": 42_000_000, "equity": 18_500_000, "commods": 9_000_000}
LIMITS = {"rates": 40_000_000, "equity": 22_000_000, "commods": 15_000_000, "fx": 10_000_000}
for row in limit_report(USAGE, LIMITS):
    print(row)
''', r'''
def limit_report(usage, limits, warn=0.8):
    rows = []
    for desk, lim in limits.items():
        u = round(usage.get(desk, 0) / lim, 3)
        status = "BREACH" if u > 1 else ("WARN" if u >= warn else "OK")
        rows.append((desk, u, status))
    return sorted(rows, key=lambda r: -r[1])

USAGE = {"rates": 42_000_000, "equity": 18_500_000, "commods": 9_000_000}
LIMITS = {"rates": 40_000_000, "equity": 22_000_000, "commods": 15_000_000, "fx": 10_000_000}
for row in limit_report(USAGE, LIMITS):
    print(row)
''', [("rows", r'''
r = limit_report(USAGE, LIMITS)
assert r == [("rates", 1.05, "BREACH"), ("equity", 0.841, "WARN"), ("commods", 0.6, "OK"), ("fx", 0.0, "OK")], f"got {r}"
'''), ("exactly at limit", r'''assert limit_report({"x": 100}, {"x": 100}) == [("x", 1.0, "WARN")], "Exactly 100% is not a breach (> 1)"''')],
hints=["usage.get(desk, 0)", "Check BREACH first, then WARN."],
wrong=r'''
def limit_report(usage, limits, warn=0.8):
    rows = [(d, round(u / limits[d], 3), "BREACH" if u >= limits[d] else "OK") for d, u in usage.items()]
    return sorted(rows, key=lambda r: -r[1])
''', difficulty=2),
])

checkpoint("u9", "u9cp", "Checkpoint: pattern recognition",
"Before an onsite, make sure you can name the pattern within 60 seconds of reading a prompt.",
CP_BODY,
quiz=[
q("\"Find two trades whose notionals sum to X.\" Unsorted input. Pattern?", ["Hash map of seen values", "BFS", "Heap", "Intervals"], 0, "One pass with a dict: O(n)."),
q("\"Top 5 accounts by exposure from a 50m-row stream.\" Pattern?", ["Sort everything", "Size-k min-heap", "Two pointers", "Stack"], 1, "O(n log k) time, O(k) memory."),
q("\"Total minutes a venue was down, given overlapping outage windows.\" Pattern?", ["Merge intervals", "Binary search", "Hash map", "DFS"], 0, "Sort by start, merge, sum lengths."),
q("\"Fewest hops from client A to a defaulting firm through a network of exposures.\" Pattern?", ["DFS", "BFS", "Heap", "Sliding window"], 1, "BFS gives shortest paths on unweighted graphs."),
q("\"Worst 5-day P&L window.\" Pattern?", ["Sliding window", "Heap", "Graph", "Stack"], 0, "Add the new day, drop the old one: O(n)."),
q("\"For each day, how many days until a higher price?\" Pattern?", ["Monotonic stack", "Queue", "Binary search", "Union-find"], 0, "Each index is pushed and popped once: O(n)."),
],
exercises=[
ex("Longest profitable streak", r'''
Return `(start, length)` for the longest run of consecutive days with P&L **> 0** (earliest on ties), or `(None, 0)` if there are none.
''', r'''
def longest_streak(pnl):
    ...

print(longest_streak([5, -2, 3, 4, 1, -1, 2, 2, 2, 0, 7]))
''', r'''
def longest_streak(pnl):
    best = (None, 0)
    start = None
    for i, x in enumerate(pnl + [0]):
        if x > 0:
            if start is None:
                start = i
        elif start is not None:
            if i - start > best[1]:
                best = (start, i - start)
            start = None
    return best

print(longest_streak([5, -2, 3, 4, 1, -1, 2, 2, 2, 0, 7]))
''', [("example", r'''assert longest_streak([5, -2, 3, 4, 1, -1, 2, 2, 2, 0, 7]) == (2, 3), f"got {longest_streak([5, -2, 3, 4, 1, -1, 2, 2, 2, 0, 7])}: earliest of the two length-3 runs"'''),
("zero breaks a streak", r'''assert longest_streak([1, 0, 1, 1]) == (2, 2)'''),
("streak at the end", r'''assert longest_streak([-1, 1, 1, 1]) == (1, 3), "Don't forget a streak that runs to the last day"'''),
("none", r'''assert longest_streak([]) == (None, 0) and longest_streak([-1, 0]) == (None, 0)''')],
hints=["Track where the current run started; close it when you hit a non-positive day.", "Appending a sentinel 0 closes a run at the end."],
wrong=r'''
def longest_streak(pnl):
    best = (None, 0); start = None
    for i, x in enumerate(pnl):
        if x > 0:
            if start is None: start = i
        elif start is not None:
            if i - start >= best[1]: best = (start, i - start)
            start = None
    return best
''', difficulty=2),
ex("Top-k counterparties by net exposure", r'''
`trades` is a list of `(counterparty, exposure)` with repeats (exposures can be negative). Aggregate net exposure per counterparty and return the top `k` as `(counterparty, net)` by net descending (ties by name), using `heapq`. Exclude counterparties with net <= 0.
''', r'''
import heapq

def top_counterparties(trades, k):
    ...

T = [("KESTREL", 40), ("OSPREY", 25), ("HERON", -5), ("KESTREL", -15), ("FALCON", 25), ("HERON", 3), ("EGRET", 10)]
print(top_counterparties(T, 3))
''', r'''
import heapq

def top_counterparties(trades, k):
    net = {}
    for cp, x in trades:
        net[cp] = net.get(cp, 0) + x
    positive = [(cp, v) for cp, v in net.items() if v > 0]
    return heapq.nsmallest(k, positive, key=lambda t: (-t[1], t[0]))

T = [("KESTREL", 40), ("OSPREY", 25), ("HERON", -5), ("KESTREL", -15), ("FALCON", 25), ("HERON", 3), ("EGRET", 10)]
print(top_counterparties(T, 3))
''', [("example", r'''
r = top_counterparties(T, 3)
assert r == [("FALCON", 25), ("KESTREL", 25), ("OSPREY", 25)], f"got {r}: KESTREL nets 40 - 15 = 25; ties by name"
'''), ("excludes non-positive", r'''assert top_counterparties([("A", -1), ("B", 0)], 2) == []'''),
("uses heapq", r'''assert "heapq." in _source, "Use heapq (nlargest/nsmallest or a heap)"''')],
hints=["Aggregate with a dict first.", "heapq.nsmallest(k, items, key=lambda t: (-t[1], t[0]))"],
wrong=r'''
import heapq
def top_counterparties(trades, k):
    return heapq.nlargest(k, trades, key=lambda t: t[1])
''', difficulty=2),
])
