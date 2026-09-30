from dsl import *

TALK = r'''
Use **UMPIRE** out loud. Interviewers grade your process as much as the code:

1. **Understand**: restate the problem; ask about input size, duplicates, empty input, negatives, ties, return format.
2. **Match**: "this looks like a hash-map / two-pointer / BFS problem because..."
3. **Plan**: describe the approach and its Big-O *before* typing. Mention brute force first, then the better one.
4. **Implement**: clean names, small helpers, narrate as you go.
5. **Review**: walk a small example by hand; check edge cases.
6. **Evaluate**: state time/space complexity and what you'd improve.

Useful phrases: "Let me confirm the edge cases...", "Brute force is O(n^2); a dict of seen values gets O(n)", "I'll test an empty list and a single element."
'''

unit("u9", "Interview Prep: Palantir, SpaceX & Coding Rounds", "Timed LeetCode-style patterns (hash maps, heaps, two pointers, stacks, intervals, sliding windows, BFS), Palantir-style decomposition, SpaceX-style analytics and a mock interview.")

lesson("u9l1", "Interview method + hash maps",
"Two-sum style matching is everywhere: pairing fills to an order, matching breaks, finding offsetting trades.",
r'''
**Hash maps (dict/set)** turn "search the list again" (O(n)) into "look it up" (O(1)). The classic:

> Given fill quantities and a target, return indices of two fills that sum to the target.

Brute force checks every pair: O(n^2). Better: one pass, remembering each value's index in a dict; for each x, check whether `target - x` was seen.

```python
def two_sum(nums, target):
    seen = {}                      # value -> index
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []
```

Signals for a hash map: *pairs summing to...*, *first unique...*, *group by...*, *count occurrences*, *have we seen this before?*
''',
talk=TALK, timed=15,
examples=[("Counting & grouping", r'''
from collections import Counter, defaultdict
syms = ["ES", "NQ", "ES", "CL", "ES", "NQ"]
print(Counter(syms).most_common(2))
groups = defaultdict(list)
for i, s in enumerate(syms):
    groups[s].append(i)
print(dict(groups))
''')],
quiz=[q("Time complexity of the one-pass dict two_sum?", ["O(n^2)", "O(n log n)", "O(n)", "O(1)"], 2, "One pass with O(1) average lookups: O(n) time, O(n) space.")],
exercises=[
ex("two_sum()", r'''
Return the indices `[i, j]` (i < j) of the two fills that sum to `target`, or `[]` if none. Must be O(n): it's tested on 5,000 fills.
''', r'''
def two_sum(nums, target):
    ...

print(two_sum([120, 35, 80, 65], 100))
''', r'''
def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []

print(two_sum([120, 35, 80, 65], 100))
''', [("example", r'''assert two_sum([120, 35, 80, 65], 100) == [1, 3], f"got {two_sum([120, 35, 80, 65], 100)}"'''),
("duplicates", r'''assert two_sum([50, 10, 50], 100) == [0, 2], "Two equal elements are fine, but don't use one element twice"'''),
("none", r'''assert two_sum([1, 2, 3], 100) == [], "No pair -> []"'''),
("O(n) on 5,000", r'''
import time
nums = list(range(1, 5001)); t = time.time(); r = two_sum(nums, 9999); dt = time.time() - t
assert r == [4998, 4999], f"got {r}"
assert dt < 1.0, f"took {dt:.2f}s: that's O(n^2). Use a dict of seen values."
''')], hints=["Store value -> index as you go.", "Check `target - x in seen` BEFORE adding x."],
wrong=r'''
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
'''),
ex("first_unique()", r'''
Return the **first** symbol in the list that appears exactly once, or `None`.
''', r'''
def first_unique(symbols):
    ...

print(first_unique(["ES", "NQ", "ES", "CL", "NQ", "ZN"]))
''', r'''
from collections import Counter

def first_unique(symbols):
    counts = Counter(symbols)
    for s in symbols:
        if counts[s] == 1:
            return s
    return None

print(first_unique(["ES", "NQ", "ES", "CL", "NQ", "ZN"]))
''', [("example", r'''assert first_unique(["ES", "NQ", "ES", "CL", "NQ", "ZN"]) == "CL"'''),
("none", r'''assert first_unique(["ES", "ES"]) is None and first_unique([]) is None, "No unique symbol -> None"'''),
("order matters", r'''assert first_unique(["ZN", "CL", "ZN"]) == "CL"'''),
("input order, not alphabetical", r'''assert first_unique(["ZN", "CL", "CL", "AA"]) == "ZN"''')],
hints=["Count first (Counter), then scan in original order."],
wrong=r'''
def first_unique(symbols):
    counts = {}
    for s in symbols:
        counts[s] = counts.get(s, 0) + 1
    uniques = sorted(s for s, c in counts.items() if c == 1)
    return uniques[0] if uniques else None
'''),
ex("group_by_key()", r'''
Counterparty names arrive in inconsistent formats. Group trade ids by a **normalized** name: lower-case, remove `.` and `,`, and drop a trailing `llc`, `inc` or `lp` word. Return dict normalized_name -> list of trade ids in input order.
''', r'''
def normalize(name):
    ...

def group_by_key(trades):
    ...

TRADES = [("T1", "Alpha Capital LLC"), ("T2", "ALPHA CAPITAL"), ("T3", "Beta Partners, L.P."), ("T4", "alpha capital, llc."), ("T5", "Beta Partners LP")]
print(group_by_key(TRADES))
''', r'''
def normalize(name):
    words = name.lower().replace(".", "").replace(",", "").split()
    if words and words[-1] in {"llc", "inc", "lp"}:
        words = words[:-1]
    return " ".join(words)

def group_by_key(trades):
    groups = {}
    for tid, name in trades:
        groups.setdefault(normalize(name), []).append(tid)
    return groups

TRADES = [("T1", "Alpha Capital LLC"), ("T2", "ALPHA CAPITAL"), ("T3", "Beta Partners, L.P."), ("T4", "alpha capital, llc."), ("T5", "Beta Partners LP")]
print(group_by_key(TRADES))
''', [("normalize", r'''
assert normalize("Beta Partners, L.P.") == "beta partners", f"got {normalize('Beta Partners, L.P.')!r}: remove '.' and ',' first so 'L.P.' becomes 'lp'"
assert normalize("Inc Holdings") == "inc holdings", "Only drop the suffix at the END"
'''), ("groups", r'''
r = group_by_key([("T1", "Alpha Capital LLC"), ("T2", "ALPHA CAPITAL"), ("T3", "Beta Partners, L.P."), ("T4", "alpha capital, llc."), ("T5", "Beta Partners LP")])
assert r == {"alpha capital": ["T1", "T2", "T4"], "beta partners": ["T3", "T5"]}, f"got {r}"
''')], hints=["Clean punctuation, split into words, drop the last word if it's a suffix.", "dict.setdefault(key, []).append(tid)"],
wrong=r'''
def normalize(name):
    return name.lower().replace(" llc", "").replace(" lp", "").replace(" inc", "").strip()
def group_by_key(trades):
    g = {}
    for tid, name in trades:
        g.setdefault(normalize(name), []).append(tid)
    return g
'''),
])

lesson("u9l2", "Heaps & top-k",
"Top-k questions (largest exposures, most active symbols, merging sorted feeds) are interview staples and daily risk tasks.",
r'''
A **heap** keeps the smallest item at index 0 with O(log n) push/pop. Python's `heapq` is a min-heap on a list.

- `heapq.nlargest(k, items, key=...)` / `nsmallest`: O(n log k); great for top-k.
- Keep a heap of size k: push each item, pop when size > k, so the heap holds the k largest.
- `heapq.merge(*sorted_iterables)` merges sorted streams lazily (e.g. time-sorted fills from several venues).
- For max-heap behaviour, push negatives: `heappush(h, (-value, name))`.

Sorting everything is O(n log n), fine for n = 10^5; heaps matter when n is huge or streaming. **Say the tradeoff out loud.**

Ties: define them explicitly (e.g. alphabetical). Interviewers love asking.
''',
talk=TALK, timed=15,
examples=[("Heap basics", r'''
import heapq
h = []
for x in [5, 1, 8, 3, 9, 2]:
    heapq.heappush(h, x)
print(h[0], heapq.heappop(h), h[0])
print(heapq.nlargest(3, [("ES", 34.7), ("ZN", 88.5), ("CL", 18.3), ("NQ", 16.1)], key=lambda t: t[1]))
print(list(heapq.merge([1, 4, 9], [2, 3, 10], [5])))
''')],
quiz=[q("Top 10 of 50 million streaming exposures with limited memory. Best approach?", ["Sort all 50m", "Min-heap of size 10", "Nested loops", "Convert to a set"], 1, "A size-k min-heap uses O(k) memory and O(n log k) time.")],
exercises=[
ex("top_k_frequent()", r'''
Return the `k` most frequent symbols, most frequent first; break ties alphabetically.
''', r'''
def top_k_frequent(symbols, k):
    ...

print(top_k_frequent(["ES", "NQ", "ES", "CL", "NQ", "ZN", "ES", "CL"], 2))
''', r'''
import heapq
from collections import Counter

def top_k_frequent(symbols, k):
    counts = Counter(symbols)
    return [s for s, _ in heapq.nsmallest(k, counts.items(), key=lambda kv: (-kv[1], kv[0]))]

print(top_k_frequent(["ES", "NQ", "ES", "CL", "NQ", "ZN", "ES", "CL"], 2))
''', [("example", r'''
r = top_k_frequent(["ES", "NQ", "ES", "CL", "NQ", "ZN", "ES", "CL"], 2)
assert r == ["ES", "CL"], f"got {r}: ES x3, then CL x2 and NQ x2 tie -> alphabetical: CL"
'''), ("k larger than unique", r'''assert top_k_frequent(["A", "B", "A"], 5) == ["A", "B"]'''),
("empty", r'''assert top_k_frequent([], 3) == []''')],
hints=["Counter(symbols).items() gives (symbol, count)", "Sort/nsmallest by key (-count, symbol)"],
wrong=r'''
from collections import Counter
def top_k_frequent(symbols, k):
    return [s for s, _ in Counter(symbols).most_common(k)]
'''),
ex("k_largest_stream()", r'''
Implement `k_largest_stream(stream, k)` with a **size-k min-heap** (don't sort the whole stream). `stream` yields `(exposure, account)`. Return the k largest, sorted by exposure descending (ties: account ascending).
''', r'''
import heapq

def k_largest_stream(stream, k):
    heap = []
    ...

print(k_largest_stream([(34.7, "A1"), (88.5, "B1"), (18.3, "G1"), (88.5, "A2"), (5.0, "G2")], 3))
''', r'''
import heapq

def k_largest_stream(stream, k):
    heap = []
    for exp, acct in stream:
        # on ties the alphabetically smaller account should rank HIGHER, so invert its characters
        item = (exp, [-ord(c) for c in acct], acct)
        if len(heap) < k:
            heapq.heappush(heap, item)
        elif item > heap[0]:
            heapq.heapreplace(heap, item)
    return [(e, a) for e, _, a in sorted(heap, reverse=True)]

print(k_largest_stream([(34.7, "A1"), (88.5, "B1"), (18.3, "G1"), (88.5, "A2"), (5.0, "G2")], 3))
''', [("example", r'''
r = k_largest_stream([(34.7, "A1"), (88.5, "B1"), (18.3, "G1"), (88.5, "A2"), (5.0, "G2")], 3)
assert r == [(88.5, "A2"), (88.5, "B1"), (34.7, "A1")], f"got {r}: ties by account ascending"
'''), ("uses a heap", r'''
src = _source
assert "heap" in src and "sorted(stream" not in src and "stream.sort" not in src, "Use heapq with a size-k heap rather than sorting the whole stream"
'''), ("big stream", r'''
import random
random.seed(1)
data = [(random.random(), f"X{i}") for i in range(20000)]
assert k_largest_stream(iter(data), 5) == sorted(data, key=lambda t: (-t[0], t[1]))[:5], "Must work on a one-pass iterator"
''')], hints=["Push until the heap has k items; afterwards replace the root when a bigger item arrives.", "For ties, build a comparable tuple so the 'better' account compares larger."],
wrong=r'''
import heapq
def k_largest_stream(stream, k):
    heap = []
    for item in stream:
        heapq.heappush(heap, item)
    return heapq.nlargest(k, heap)
'''),
ex("merge_feeds()", r'''
Merge several **time-sorted** lists of fills `(ts, venue, qty)` into one time-sorted list with `heapq.merge`. Return `(merged, first_ts_over)` where first_ts_over is the first timestamp at which the **cumulative qty** exceeds `limit` (or None).
''', r'''
import heapq

def merge_feeds(feeds, limit):
    ...

A = [(1, "CME", 5), (4, "CME", 10), (9, "CME", 3)]
B = [(2, "ICE", 7), (3, "ICE", 2), (10, "ICE", 8)]
print(merge_feeds([A, B], 20))
''', r'''
import heapq

def merge_feeds(feeds, limit):
    merged = list(heapq.merge(*feeds))
    total = 0
    first = None
    for ts, venue, qty in merged:
        total += qty
        if total > limit and first is None:
            first = ts
    return merged, first

A = [(1, "CME", 5), (4, "CME", 10), (9, "CME", 3)]
B = [(2, "ICE", 7), (3, "ICE", 2), (10, "ICE", 8)]
print(merge_feeds([A, B], 20))
''', [("merged order", r'''
A = [(1, "CME", 5), (4, "CME", 10), (9, "CME", 3)]; B = [(2, "ICE", 7), (3, "ICE", 2), (10, "ICE", 8)]
m, f = merge_feeds([A, B], 20)
assert [t[0] for t in m] == [1, 2, 3, 4, 9, 10], f"timestamps = {[t[0] for t in m]}"
'''), ("first breach", r'''
A = [(1, "CME", 5), (4, "CME", 10), (9, "CME", 3)]; B = [(2, "ICE", 7), (3, "ICE", 2), (10, "ICE", 8)]
m, f = merge_feeds([A, B], 20)
assert f == 4, f"cumulative 5, 12, 14, 24 -> first exceeds 20 at ts 4; got {f}"
assert merge_feeds([A, B], 1000)[1] is None
''')], hints=["list(heapq.merge(*feeds))", "Track a running total; record the first ts where total > limit."],
wrong=r'''
def merge_feeds(feeds, limit):
    merged = [x for f in feeds for x in f]
    total = 0
    for ts, v, q in merged:
        total += q
        if total >= limit:
            return merged, ts
    return merged, None
'''),
])
