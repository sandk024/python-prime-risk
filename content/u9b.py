from dsl import *
from u9a import TALK

lesson("u9l3", "Two pointers & sorting",
"Merging sorted blotters, reconciling two sorted files and pairing trades are two-pointer problems.",
r'''
**Two pointers** walk through one or two sorted sequences without nested loops:

- **Merge two sorted lists** (our trades vs the street's, both sorted by trade id): advance whichever pointer has the smaller item. O(n + m).
- **Pair with target sum in a sorted list**: one pointer at each end; move left up if the sum is too small, right down if too big. O(n).
- **In-place dedupe of a sorted list**: a slow "write" pointer and a fast "read" pointer.

If the input isn't sorted, sorting first (O(n log n)) often unlocks a two-pointer solution. Mention that `sorted(..., key=...)` is **stable**: equal keys keep their input order.
''',
talk=TALK, timed=15,
examples=[("Recon two sorted id lists", r'''
ours = [101, 103, 104, 108]
theirs = [101, 102, 104, 108, 109]
i = j = 0
while i < len(ours) and j < len(theirs):
    if ours[i] == theirs[j]: i += 1; j += 1
    elif ours[i] < theirs[j]: print("only ours:", ours[i]); i += 1
    else: print("only theirs:", theirs[j]); j += 1
print("leftover ours:", ours[i:], "theirs:", theirs[j:])
''')],
quiz=[q("Two sorted lists of 1m trade ids each. Complexity of a two-pointer recon?", ["O(n^2)", "O(n log n)", "O(n + m)", "O(1)"], 2, "Each pointer only moves forward.")],
exercises=[
ex("merge_sorted()", r'''
Merge two sorted lists into one sorted list **without** `sorted()` / `.sort()`.
''', r'''
def merge_sorted(a, b):
    ...

print(merge_sorted([1, 4, 9], [2, 3, 10, 11]))
''', r'''
def merge_sorted(a, b):
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i]); i += 1
        else:
            out.append(b[j]); j += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out

print(merge_sorted([1, 4, 9], [2, 3, 10, 11]))
''', [("example", r'''assert merge_sorted([1, 4, 9], [2, 3, 10, 11]) == [1, 2, 3, 4, 9, 10, 11], f"got {merge_sorted([1, 4, 9], [2, 3, 10, 11])}"'''),
("edge cases", r'''assert merge_sorted([], [1, 2]) == [1, 2] and merge_sorted([3], []) == [3] and merge_sorted([1, 1], [1]) == [1, 1, 1], "Handle empty lists and duplicates"'''),
("no sort()", r'''import re
assert not re.search(r"(?<![\w])sorted\(|\.sort\(", _source), "Solve it with two pointers: no sorted()/sort()"''')],
hints=["Two indices i, j; append the smaller; then extend with the leftovers."],
wrong=r'''
def merge_sorted(a, b):
    out = []
    for x, y in zip(a, b):
        out += [min(x, y), max(x, y)]
    return out
'''),
ex("pair_sum_sorted()", r'''
Given a **sorted** list of quantities and a target, return `True` if two different elements sum to target, with O(1) extra space (pointers from both ends).
''', r'''
def pair_sum_sorted(nums, target):
    ...

print(pair_sum_sorted([5, 10, 25, 40, 60], 65))
''', r'''
def pair_sum_sorted(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        s = nums[lo] + nums[hi]
        if s == target:
            return True
        if s < target:
            lo += 1
        else:
            hi -= 1
    return False

print(pair_sum_sorted([5, 10, 25, 40, 60], 65))
''', [("found", r'''assert pair_sum_sorted([5, 10, 25, 40, 60], 65) is True'''),
("not found", r'''assert pair_sum_sorted([5, 10, 25, 40, 60], 90) is False and pair_sum_sorted([50], 100) is False, "Can't use the same element twice"'''),
("negatives", r'''assert pair_sum_sorted([-30, -10, 0, 20, 45], 10) is True''')],
hints=["lo = 0, hi = len - 1; move lo up if the sum is too small, hi down if too big."],
wrong=r'''
def pair_sum_sorted(nums, target):
    return any(target - x in nums for x in nums)
'''),
ex("dedupe_sorted()", r'''
Remove duplicates **in place** from a sorted list and return the count `k` of unique values; the first `k` elements must be the unique values in order.
''', r'''
def dedupe_sorted(nums):
    ...

x = [101, 101, 102, 104, 104, 104, 108]
k = dedupe_sorted(x)
print(k, x[:k])
''', r'''
def dedupe_sorted(nums):
    if not nums:
        return 0
    w = 1
    for r in range(1, len(nums)):
        if nums[r] != nums[w - 1]:
            nums[w] = nums[r]
            w += 1
    return w

x = [101, 101, 102, 104, 104, 104, 108]
k = dedupe_sorted(x)
print(k, x[:k])
''', [("example", r'''
x = [101, 101, 102, 104, 104, 104, 108]; k = dedupe_sorted(x)
assert k == 4 and x[:k] == [101, 102, 104, 108], f"k = {k}, x[:k] = {x[:k]}"
'''), ("in place", r'''
x = [1, 1, 2]; ident = id(x); k = dedupe_sorted(x)
assert id(x) == ident and x[:k] == [1, 2], "Modify the same list object (in place)"
'''), ("empty & single", r'''assert dedupe_sorted([]) == 0 and dedupe_sorted([7]) == 1''')],
hints=["A write pointer w starts at 1; copy nums[r] to nums[w] when it differs from nums[w - 1]."],
wrong=r'''
def dedupe_sorted(nums):
    return len(set(nums))
'''),
])

lesson("u9l4", "Stacks & queues: brackets and FIFO P&L",
"FIFO lot matching for realized P&L is a queue problem; nested structures (brackets, parsing) are stack problems.",
r'''
- **Stack** (LIFO): a `list` with `.append()` / `.pop()`. Use it for matching/nesting (brackets, undo, parsing) and **monotonic stacks** ("next greater element").
- **Queue** (FIFO): `collections.deque` with `.append()` / `.popleft()`, O(1) at both ends (a list's `pop(0)` is O(n)).

**FIFO realized P&L**: keep open lots in a deque. A sell closes the oldest buy lots first (partially if needed); realized P&L = sum of (sell - buy) x qty x multiplier. Tax lots and many accounting systems use FIFO; futures desks also see average-cost methods, so ask which one the interviewer means.
''',
talk=TALK, timed=15,
examples=[("deque as a queue", r'''
from collections import deque
q = deque([("lot1", 10), ("lot2", 5)])
q.append(("lot3", 7))
print(q.popleft(), list(q))
''')],
quiz=[q("Why use deque instead of list for a FIFO queue?", ["deque is sorted", "popleft() is O(1); list.pop(0) is O(n)", "lists can't hold tuples", "No difference"], 1, "Removing from the front of a list shifts every element.")],
exercises=[
ex("valid_brackets()", r'''
Return True if every `(`, `[`, `{` is closed in the right order (other characters are ignored).
''', r'''
def valid_brackets(s):
    ...

print(valid_brackets("sum([x[i] for i in range(3)])"))
''', r'''
def valid_brackets(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack

print(valid_brackets("sum([x[i] for i in range(3)])"))
''', [("valid", r'''assert valid_brackets("sum([x[i] for i in range(3)])") and valid_brackets("") and valid_brackets("{a: [1, (2)]}")'''),
("wrong order", r'''assert not valid_brackets("([)]"), "([)] closes in the wrong order -> False"'''),
("unclosed / extra", r'''assert not valid_brackets("((") and not valid_brackets("())"), "Unclosed or extra closers -> False"''')],
hints=["Push openers; on a closer, pop and check it matches.", "At the end the stack must be empty."],
wrong=r'''
def valid_brackets(s):
    return s.count("(") == s.count(")") and s.count("[") == s.count("]") and s.count("{") == s.count("}")
'''),
ex("fifo_realized_pnl()", r'''
Trades are `(side, qty, price)` for one futures contract (long-only inventory; sells never exceed the open position). Return realized P&L using **FIFO** lot matching and multiplier `mult`.
''', r'''
from collections import deque

def fifo_realized_pnl(trades, mult=50):
    ...

T = [("BUY", 10, 5790.0), ("BUY", 5, 5800.0), ("SELL", 12, 5810.0), ("BUY", 4, 5780.0), ("SELL", 7, 5795.0)]
print(fifo_realized_pnl(T))
''', r'''
from collections import deque

def fifo_realized_pnl(trades, mult=50):
    lots = deque()
    pnl = 0.0
    for side, qty, px in trades:
        if side == "BUY":
            lots.append([qty, px])
            continue
        remaining = qty
        while remaining > 0:
            lot = lots[0]
            take = min(remaining, lot[0])
            pnl += (px - lot[1]) * take * mult
            lot[0] -= take
            remaining -= take
            if lot[0] == 0:
                lots.popleft()
    return pnl

T = [("BUY", 10, 5790.0), ("BUY", 5, 5800.0), ("SELL", 12, 5810.0), ("BUY", 4, 5780.0), ("SELL", 7, 5795.0)]
print(fifo_realized_pnl(T))
''', [("example", r'''
T = [("BUY", 10, 5790.0), ("BUY", 5, 5800.0), ("SELL", 12, 5810.0), ("BUY", 4, 5780.0), ("SELL", 7, 5795.0)]
r = fifo_realized_pnl(T)
assert _close(r, 13_250.0), f"got {r:,.0f}; FIFO: sell 12 = 10@5790 + 2@5800 (+220 pts); sell 7 = 3@5800 + 4@5780 (+45 pts) -> 265 x 50 = 13,250"
'''), ("partial lot", r'''assert _close(fifo_realized_pnl([("BUY", 3, 100.0), ("SELL", 1, 101.0)], mult=1000), 1000.0)'''),
("no sells", r'''assert fifo_realized_pnl([("BUY", 3, 100.0)]) == 0'''),
("oldest lot first", r'''
r = fifo_realized_pnl([("BUY", 1, 100.0), ("BUY", 1, 110.0), ("SELL", 1, 120.0)], mult=1)
assert _close(r, 20.0), f"got {r}: FIFO closes the 100 lot first (+20). {'That is LIFO (newest first).' if _close(r, 10.0) else ''}"
''')],
hints=["Keep lots as [qty, price] in a deque; reduce the front lot's qty on partial fills.", "while remaining > 0: take = min(remaining, lots[0][0])"],
wrong=r'''
def fifo_realized_pnl(trades, mult=50):
    lots = []
    pnl = 0.0
    for side, qty, px in trades:
        if side == "BUY":
            lots.append([qty, px]); continue
        remaining = qty
        while remaining > 0:
            lot = lots[-1]
            take = min(remaining, lot[0]); pnl += (px - lot[1]) * take * mult
            lot[0] -= take; remaining -= take
            if lot[0] == 0: lots.pop()
    return pnl
'''),
ex("days_until_higher() (monotonic stack)", r'''
For each day's settlement price, return how many days until a **strictly higher** price (0 if never). O(n) with a monotonic stack of indices.
''', r'''
def days_until_higher(prices):
    ...

print(days_until_higher([71.4, 70.9, 72.1, 71.8, 71.5, 73.0, 72.2]))
''', r'''
def days_until_higher(prices):
    out = [0] * len(prices)
    stack = []                       # indices still waiting for a higher price
    for i, p in enumerate(prices):
        while stack and prices[stack[-1]] < p:
            j = stack.pop()
            out[j] = i - j
        stack.append(i)
    return out

print(days_until_higher([71.4, 70.9, 72.1, 71.8, 71.5, 73.0, 72.2]))
''', [("example", r'''
r = days_until_higher([71.4, 70.9, 72.1, 71.8, 71.5, 73.0, 72.2])
assert r == [2, 1, 3, 2, 1, 0, 0], f"got {r}"
'''), ("flat", r'''assert days_until_higher([5, 5, 5]) == [0, 0, 0], "Strictly higher only"'''),
("O(n) on 30k", r'''
import time
p = list(range(30000, 0, -1)) + [10**9]
t = time.time(); r = days_until_higher(p); dt = time.time() - t
assert r[0] == 30000 and dt < 1.0, f"took {dt:.2f}s: use a stack so each index is pushed/popped once"
''')], hints=["Keep a stack of indices whose answer is unknown.", "When a higher price arrives, pop and fill in answers."],
wrong=r'''
def days_until_higher(prices):
    out = []
    for i, p in enumerate(prices):
        d = 0
        for j in range(i + 1, len(prices)):
            if prices[j] > p:
                d = j - i; break
        out.append(d)
    return out
'''),
])
