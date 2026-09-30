from dsl import *
from u9a import TALK

lesson("u9l5", "Intervals: outages, halts and concurrent orders",
"Merge overlapping outage windows for an SLA report, or find peak concurrent working orders.",
r'''
Almost every interval problem starts with **sorting by start time**.

- **Merge overlapping intervals**: sort by start; if the next start <= current end, extend the end; otherwise start a new interval. O(n log n).
- **Max concurrency** ("minimum meeting rooms"): split into events (+1 at start, -1 at end), sort, sweep and track the running count. Decide how to order a start and an end at the same time. Does [9,10) overlap [10,11)? Usually no, so process ends first.
- **Total covered time** = sum of merged interval lengths.

Real uses: venue outage windows, trading halts, overlapping order lifetimes (peak working orders), margin-call deadline windows.
''',
talk=TALK, timed=15,
examples=[("Sweep line", r'''
orders = [(9.5, 10.0), (9.75, 11.0), (10.0, 10.5), (13.0, 14.0)]
events = sorted([(s, 1) for s, e in orders] + [(e, -1) for s, e in orders])   # -1 sorts before +1 at the same time
cur = peak = 0
for t, d in events:
    cur += d; peak = max(peak, cur)
print("peak concurrent orders:", peak)
''')],
quiz=[q("First step for merging overlapping intervals?", ["Sort by end time", "Sort by start time", "Use a stack of ends", "Binary search"], 1, "Sorting by start lets you merge in a single pass.")],
exercises=[
ex("merge_intervals()", r'''
Merge overlapping `[start, end]` outage windows (touching intervals like [1,3] and [3,5] **do** merge). Return a sorted list of lists.
''', r'''
def merge_intervals(intervals):
    ...

print(merge_intervals([[9, 10], [1, 3], [2, 6], [8, 9], [15, 18]]))
''', r'''
def merge_intervals(intervals):
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out

print(merge_intervals([[9, 10], [1, 3], [2, 6], [8, 9], [15, 18]]))
''', [("example", r'''
r = merge_intervals([[9, 10], [1, 3], [2, 6], [8, 9], [15, 18]])
assert r == [[1, 6], [8, 10], [15, 18]], f"got {r}"
'''), ("contained & empty", r'''assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]] and merge_intervals([]) == [], "A contained interval shouldn't shrink the end (use max)"''')],
hints=["for s, e in sorted(intervals):", "If s <= last end: last end = max(last end, e)"],
wrong=r'''
def merge_intervals(intervals):
    out = []
    for s, e in sorted(intervals):
        if out and s < out[-1][1]:
            out[-1][1] = e
        else:
            out.append([s, e])
    return out
'''),
ex("peak_concurrency()", r'''
Given order lifetimes `(start, end)` (end exclusive: an order ending at 10 and one starting at 10 do **not** overlap), return the maximum number of simultaneously working orders.
''', r'''
def peak_concurrency(orders):
    ...

print(peak_concurrency([(9.5, 10.0), (9.75, 11.0), (10.0, 10.5), (13.0, 14.0)]))
''', r'''
def peak_concurrency(orders):
    events = [(s, 1) for s, e in orders] + [(e, -1) for s, e in orders]
    events.sort()                  # at equal times, -1 (end) sorts before +1 (start)
    cur = peak = 0
    for _, d in events:
        cur += d
        peak = max(peak, cur)
    return peak

print(peak_concurrency([(9.5, 10.0), (9.75, 11.0), (10.0, 10.5), (13.0, 14.0)]))
''', [("example", r'''assert peak_concurrency([(9.5, 10.0), (9.75, 11.0), (10.0, 10.5), (13.0, 14.0)]) == 2'''),
("touching don't overlap", r'''assert peak_concurrency([(1, 2), (2, 3), (3, 4)]) == 1, "End-exclusive: [1,2) and [2,3) don't overlap"'''),
("nested", r'''assert peak_concurrency([(1, 10), (2, 9), (3, 8), (4, 5)]) == 4 and peak_concurrency([]) == 0''')],
hints=["Make (time, +1) for starts and (time, -1) for ends; sort; sweep."],
wrong=r'''
def peak_concurrency(orders):
    events = sorted([(s, 1) for s, e in orders] + [(e, 2) for s, e in orders])
    cur = peak = 0
    for t, d in events:
        cur += 1 if d == 1 else -1
        peak = max(peak, cur)
    return peak
'''),
ex("downtime_minutes()", r'''
Venue outage windows arrive as `("HH:MM", "HH:MM")` strings and may overlap. Return total **distinct** minutes of downtime.
''', r'''
def downtime_minutes(windows):
    ...

print(downtime_minutes([("09:30", "09:45"), ("09:40", "10:00"), ("13:00", "13:05")]))
''', r'''
def to_min(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)

def downtime_minutes(windows):
    merged = []
    for s, e in sorted((to_min(a), to_min(b)) for a, b in windows):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return sum(e - s for s, e in merged)

print(downtime_minutes([("09:30", "09:45"), ("09:40", "10:00"), ("13:00", "13:05")]))
''', [("example", r'''assert downtime_minutes([("09:30", "09:45"), ("09:40", "10:00"), ("13:00", "13:05")]) == 35, "09:30-10:00 merged (30) + 5"'''),
("empty & contained", r'''assert downtime_minutes([]) == 0 and downtime_minutes([("10:00", "11:00"), ("10:15", "10:30")]) == 60''')],
hints=["Convert HH:MM to minutes, merge intervals, sum lengths."],
wrong=r'''
def downtime_minutes(windows):
    t = 0
    for a, b in windows:
        t += (int(b[:2]) * 60 + int(b[3:])) - (int(a[:2]) * 60 + int(a[3:]))
    return t
'''),
])

lesson("u9l6", "Sliding windows & binary search",
"Rolling-window worst losses, best entry/exit and 'when did we first breach?' lookups on sorted timestamps.",
r'''
**Sliding window**: keep a running aggregate as the window moves instead of recomputing. Fixed window: add the new element, subtract the one leaving. O(n). Variable window: expand the right edge, shrink the left while a condition is violated.

**Best time to buy & sell** (one trade): track the minimum price so far and the best `price - min_so_far`. O(n).

**Binary search** on sorted data is O(log n). Use `bisect`:
- `bisect_left(a, x)`: first index with a[i] >= x
- `bisect_right(a, x)`: first index with a[i] > x

Uses: first timestamp >= 10:00 in a sorted tick log; count trades in a time range (`bisect_right(hi) - bisect_left(lo)`); first day a monotone cumulative loss crosses a threshold.
''',
talk=TALK, timed=15,
examples=[("bisect", r'''
from bisect import bisect_left, bisect_right
ts = [930, 931, 935, 1000, 1000, 1015, 1100]
print(bisect_left(ts, 1000), bisect_right(ts, 1000))
print("trades 10:00-10:30:", bisect_right(ts, 1030) - bisect_left(ts, 1000))
''')],
quiz=[q("Sorted list of 1 billion timestamps. Worst-case steps for bisect?", ["~30", "~1,000", "~1 million", "1 billion"], 0, "log2(10^9) is about 30.")],
exercises=[
ex("worst_k_day_pnl()", r'''
Return the **worst (most negative) sum of any k consecutive days** of P&L in O(n) with a sliding window. Assume len(pnl) >= k >= 1.
''', r'''
def worst_k_day_pnl(pnl, k):
    ...

print(worst_k_day_pnl([12, -8, 4, -15, 9, 2, -4, -11, 3], 3))
''', r'''
def worst_k_day_pnl(pnl, k):
    window = sum(pnl[:k])
    worst = window
    for i in range(k, len(pnl)):
        window += pnl[i] - pnl[i - k]
        worst = min(worst, window)
    return worst

print(worst_k_day_pnl([12, -8, 4, -15, 9, 2, -4, -11, 3], 3))
''', [("example", r'''r = worst_k_day_pnl([12, -8, 4, -15, 9, 2, -4, -11, 3], 3); assert r == -19, f"got {r}; the window [-8, 4, -15] = -19"'''),
("k = n and k = 1", r'''assert worst_k_day_pnl([1, -2, 3], 3) == 2 and worst_k_day_pnl([5, -7, 2], 1) == -7, "Include the last window too"'''),
("O(n)", r'''
import time
p = [((i * 7919) % 201) - 100 for i in range(200000)]
t = time.time(); worst_k_day_pnl(p, 5000); dt = time.time() - t
assert dt < 1.5, f"took {dt:.2f}s: slide the window (add new, subtract old) instead of re-summing"
''')], hints=["Start with sum(pnl[:k]); each step add pnl[i] and subtract pnl[i - k]."],
wrong=r'''
def worst_k_day_pnl(pnl, k):
    return min(sum(pnl[i:i + k]) for i in range(len(pnl) - k))
'''),
ex("best_trade()", r'''
Given daily prices, return `(buy_day, sell_day, profit)` for the single best buy-then-sell (buy_day < sell_day), or `(None, None, 0)` if no profit is possible. On ties keep the **earliest** pair.
''', r'''
def best_trade(prices):
    ...

print(best_trade([71.4, 70.9, 72.1, 69.8, 71.5, 73.0, 72.2]))
''', r'''
def best_trade(prices):
    best = (None, None, 0)
    min_i = 0
    for i in range(1, len(prices)):
        if prices[i] < prices[min_i]:
            min_i = i
        profit = prices[i] - prices[min_i]
        if profit > best[2]:
            best = (min_i, i, profit)
    return best

print(best_trade([71.4, 70.9, 72.1, 69.8, 71.5, 73.0, 72.2]))
''', [("example", r'''
b, s, p = best_trade([71.4, 70.9, 72.1, 69.8, 71.5, 73.0, 72.2])
assert (b, s) == (3, 5) and abs(p - 3.2) < 1e-9, f"got {(b, s, p)}"
'''), ("min after max", r'''
b, s, p = best_trade([10, 30, 5, 12])
assert (b, s, p) == (0, 1, 20), f"got {(b, s, p)}: the global min (5) comes after the max, so buy 10 sell 30"
'''), ("falling market", r'''assert best_trade([5, 4, 3]) == (None, None, 0) and best_trade([]) == (None, None, 0)''')],
hints=["Track the index of the minimum price so far.", "profit = price - min_so_far; keep the best."],
wrong=r'''
def best_trade(prices):
    if not prices: return (None, None, 0)
    b = prices.index(min(prices)); s = prices.index(max(prices))
    return (b, s, prices[s] - prices[b]) if s > b else (None, None, 0)
'''),
ex("trades_in_window()", r'''
`ts` is a **sorted** list of trade timestamps (HHMM ints). Write `trades_in_window(ts, start, end)` returning the count with start <= t <= end in O(log n) using `bisect`, and `first_at_or_after(ts, t)` returning the first timestamp >= t (or None).
''', r'''
from bisect import bisect_left, bisect_right

def trades_in_window(ts, start, end):
    ...

def first_at_or_after(ts, t):
    ...

TS = [930, 931, 935, 1000, 1000, 1015, 1100]
print(trades_in_window(TS, 1000, 1030), first_at_or_after(TS, 1001))
''', r'''
from bisect import bisect_left, bisect_right

def trades_in_window(ts, start, end):
    return bisect_right(ts, end) - bisect_left(ts, start)

def first_at_or_after(ts, t):
    i = bisect_left(ts, t)
    return ts[i] if i < len(ts) else None

TS = [930, 931, 935, 1000, 1000, 1015, 1100]
print(trades_in_window(TS, 1000, 1030), first_at_or_after(TS, 1001))
''', [("window", r'''
TS = [930, 931, 935, 1000, 1000, 1015, 1100]
assert trades_in_window(TS, 1000, 1030) == 3 and trades_in_window(TS, 900, 929) == 0 and trades_in_window(TS, 930, 1100) == 7, "Inclusive on both ends"
'''), ("first_at_or_after", r'''
TS = [930, 931, 935, 1000, 1000, 1015, 1100]
assert first_at_or_after(TS, 1001) == 1015 and first_at_or_after(TS, 1000) == 1000 and first_at_or_after(TS, 1200) is None
'''), ("uses bisect", r'''assert "bisect_" in _source.split("def trades_in_window")[1].split("def ")[0], "Use bisect for O(log n)"''')],
hints=["count = bisect_right(ts, end) - bisect_left(ts, start)", "i = bisect_left(ts, t); check i < len(ts)"],
wrong=r'''
def trades_in_window(ts, start, end):
    return len([t for t in ts if start < t < end])
def first_at_or_after(ts, t):
    return next((x for x in ts if x > t), None)
'''),
])

lesson("u9l7", "Graphs & BFS: entity networks",
"Map counterparty and entity relationships: who is within 2 hops of a failing firm? A very Palantir-flavored problem.",
r'''
A **graph** is nodes plus edges. Represent it as an **adjacency list**, `dict[node, list[node]]` (build with `defaultdict(list)`; add both directions for undirected edges).

**BFS** (breadth-first search) explores level by level with a queue, which gives the shortest path in **hops** on unweighted graphs:

```python
from collections import deque
def bfs(graph, start):
    dist = {start: 0}
    q = deque([start])
    while q:
        node = q.popleft()
        for nb in graph[node]:
            if nb not in dist:
                dist[nb] = dist[node] + 1
                q.append(nb)
    return dist
```

**Connected components**: run BFS from every unvisited node. Uses: grouping accounts that share an address/tax id (entity resolution), contagion ("which clients are within 2 hops of a defaulting counterparty?"), clusters in a grid.

DFS (stack/recursion) also finds components; BFS is the default for fewest hops. Complexity: O(V + E).
''',
talk=TALK, timed=15,
examples=[("Adjacency list + BFS", r'''
from collections import defaultdict, deque
edges = [("HF-ALPHA", "PRIME-X"), ("PRIME-X", "BANK-A"), ("BANK-A", "MMF-1"), ("HF-BETA", "MMF-1")]
g = defaultdict(list)
for a, b in edges:
    g[a].append(b); g[b].append(a)
dist = {"HF-ALPHA": 0}; q = deque(["HF-ALPHA"])
while q:
    n = q.popleft()
    for nb in g[n]:
        if nb not in dist:
            dist[nb] = dist[n] + 1; q.append(nb)
print(dist)
''')],
quiz=[q("Why BFS (not DFS) for fewest hops in an unweighted graph?", ["BFS uses less memory", "BFS visits nodes in order of distance, so the first visit is via a shortest path", "DFS can't handle cycles", "No reason"], 1, "Level-by-level exploration guarantees the first time you reach a node is a shortest path.")],
exercises=[
ex("within_hops()", r'''
Given undirected `edges` and a `start` node, return the **sorted list** of nodes reachable within `max_hops` (excluding start).
''', r'''
from collections import defaultdict, deque

def within_hops(edges, start, max_hops):
    ...

E = [("DEFAULTER", "BANK-A"), ("BANK-A", "HF-ALPHA"), ("HF-ALPHA", "FO-GAMMA"), ("DEFAULTER", "MMF-1"), ("MMF-1", "HF-BETA"), ("HF-DELTA", "BANK-Z")]
print(within_hops(E, "DEFAULTER", 2))
''', r'''
from collections import defaultdict, deque

def within_hops(edges, start, max_hops):
    g = defaultdict(list)
    for a, b in edges:
        g[a].append(b)
        g[b].append(a)
    dist = {start: 0}
    q = deque([start])
    while q:
        n = q.popleft()
        if dist[n] == max_hops:
            continue
        for nb in g[n]:
            if nb not in dist:
                dist[nb] = dist[n] + 1
                q.append(nb)
    return sorted(n for n in dist if n != start)

E = [("DEFAULTER", "BANK-A"), ("BANK-A", "HF-ALPHA"), ("HF-ALPHA", "FO-GAMMA"), ("DEFAULTER", "MMF-1"), ("MMF-1", "HF-BETA"), ("HF-DELTA", "BANK-Z")]
print(within_hops(E, "DEFAULTER", 2))
''', [("2 hops", r'''
E = [("DEFAULTER", "BANK-A"), ("BANK-A", "HF-ALPHA"), ("HF-ALPHA", "FO-GAMMA"), ("DEFAULTER", "MMF-1"), ("MMF-1", "HF-BETA"), ("HF-DELTA", "BANK-Z")]
r = within_hops(E, "DEFAULTER", 2)
assert r == ["BANK-A", "HF-ALPHA", "HF-BETA", "MMF-1"], f"got {r}" + (": FO-GAMMA is 3 hops away" if "FO-GAMMA" in r else "")
'''), ("cycles & 1 hop", r'''
E = [("A", "B"), ("B", "C"), ("C", "A"), ("C", "D")]
assert within_hops(E, "A", 1) == ["B", "C"] and within_hops(E, "A", 5) == ["B", "C", "D"], "Handle cycles (track visited)"
'''), ("isolated start", r'''assert within_hops([("A", "B")], "Z", 3) == []''')],
hints=["Build an undirected adjacency list with defaultdict(list).", "BFS with a dist dict; don't expand nodes already at max_hops."],
wrong=r'''
def within_hops(edges, start, max_hops):
    out = set()
    for a, b in edges:
        if a == start: out.add(b)
        if b == start: out.add(a)
    return sorted(out)
'''),
ex("entity_groups() (connected components)", r'''
Accounts that share any **identifier** (tax id, address, phone) belong to the same economic entity. `links` is a list of `(account, identifier)`. Return a sorted list of groups, each a sorted list of accounts (accounts only, not identifiers).
''', r'''
from collections import defaultdict, deque

def entity_groups(links):
    ...

L = [("A1", "tax:111"), ("A2", "tax:111"), ("A2", "addr:5 Main"), ("A3", "addr:5 Main"), ("B1", "tax:222"), ("C1", "phone:555"), ("C2", "phone:555"), ("D1", "tax:999")]
print(entity_groups(L))
''', r'''
from collections import defaultdict, deque

def entity_groups(links):
    g = defaultdict(set)
    accounts = set()
    for acct, ident in links:
        a, i = ("acct", acct), ("id", ident)
        g[a].add(i); g[i].add(a)
        accounts.add(a)
    seen, groups = set(), []
    for start in accounts:
        if start in seen:
            continue
        comp = []
        q = deque([start]); seen.add(start)
        while q:
            n = q.popleft()
            if n[0] == "acct":
                comp.append(n[1])
            for nb in g[n]:
                if nb not in seen:
                    seen.add(nb); q.append(nb)
        groups.append(sorted(comp))
    return sorted(groups)

L = [("A1", "tax:111"), ("A2", "tax:111"), ("A2", "addr:5 Main"), ("A3", "addr:5 Main"), ("B1", "tax:222"), ("C1", "phone:555"), ("C2", "phone:555"), ("D1", "tax:999")]
print(entity_groups(L))
''', [("groups", r'''
L = [("A1", "tax:111"), ("A2", "tax:111"), ("A2", "addr:5 Main"), ("A3", "addr:5 Main"), ("B1", "tax:222"), ("C1", "phone:555"), ("C2", "phone:555"), ("D1", "tax:999")]
r = entity_groups(L)
assert r == [["A1", "A2", "A3"], ["B1"], ["C1", "C2"], ["D1"]], f"got {r}" + (": A1 and A3 are linked transitively through A2" if ["A1", "A2"] in r else "")
'''), ("empty", r'''assert entity_groups([]) == []''')],
hints=["Make a bipartite graph: account nodes <-> identifier nodes.", "BFS from each unseen account; collect the account nodes in the component."],
wrong=r'''
def entity_groups(links):
    by_id = {}
    for a, i in links:
        by_id.setdefault(i, set()).add(a)
    return sorted(sorted(s) for s in {frozenset(v) for v in by_id.values()})
'''),
ex("count_clusters() (grid BFS)", r'''
A heat-map grid marks limit breaches as `1` (desk x hour). Count connected breach clusters (4-directional adjacency; diagonals don't connect).
''', r'''
from collections import deque

def count_clusters(grid):
    ...

G = [[1, 1, 0, 0, 0],
     [0, 1, 0, 0, 1],
     [1, 0, 0, 1, 1],
     [0, 0, 0, 0, 0],
     [1, 0, 1, 0, 1]]
print(count_clusters(G))
''', r'''
from collections import deque

def count_clusters(grid):
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    seen = set()
    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1 and (r, c) not in seen:
                count += 1
                q = deque([(r, c)]); seen.add((r, c))
                while q:
                    y, x = q.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < rows and 0 <= nx < cols and grid[ny][nx] == 1 and (ny, nx) not in seen:
                            seen.add((ny, nx)); q.append((ny, nx))
    return count

G = [[1, 1, 0, 0, 0],
     [0, 1, 0, 0, 1],
     [1, 0, 0, 1, 1],
     [0, 0, 0, 0, 0],
     [1, 0, 1, 0, 1]]
print(count_clusters(G))
''', [("example", r'''
G = [[1, 1, 0, 0, 0], [0, 1, 0, 0, 1], [1, 0, 0, 1, 1], [0, 0, 0, 0, 0], [1, 0, 1, 0, 1]]
r = count_clusters(G)
assert r == 6, f"got {r}" + (": diagonal cells are NOT connected" if r == 5 else "")
'''), ("U shape", r'''assert count_clusters([[1, 0, 1], [1, 0, 1], [1, 1, 1]]) == 1, "A U-shaped cluster is one cluster"'''),
("edge cases", r'''assert count_clusters([]) == 0 and count_clusters([[0]]) == 0 and count_clusters([[1, 1], [1, 1]]) == 1''')],
hints=["Loop over cells; on an unseen 1, BFS its whole cluster and count += 1.", "Neighbors: up/down/left/right with bounds checks."],
wrong=r'''
def count_clusters(grid):
    n = 0
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 1 and not (c > 0 and row[c - 1] == 1) and not (r > 0 and grid[r - 1][c] == 1):
                n += 1
    return n
'''),
])
