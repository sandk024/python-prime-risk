from dsl import *

unit("u2", "Python Fluency Fundamentals", "Data structures & Big-O, functions, errors, files, datetimes, classes, typing, clean code and tests — the stuff interviewers probe.")

lesson("u2l1", "Data structures & Big-O: finding duplicate trades fast",
"Detect duplicate trade IDs and unmatched trades in a 2-million-row drop copy without waiting minutes.",
r'''
> **New in this lesson** (builds on Python from Zero and Python on a Trading Desk)
>
> - **Big-O:** a way to describe how much slower code gets as the data grows (explained below).
> - **`from collections import Counter`:** loads just one tool, `Counter`, from the `collections` module (like `import math`, but you then write `Counter(...)` instead of `collections.Counter(...)`).
> - **Generator expression:** `sum(1 for i in ids if i in s)` is a comprehension without the brackets, fed straight into `sum`. It counts the items that match.
> - **`_` as a name:** means "I don't need this value", e.g. `for _, sym in trades:`.
> - **Set operations:** `a - b`, `a & b`, `a ^ b` (below). **`time.time()`:** the current time in seconds, used to time code.
> - **Desk words:** a **drop copy** is the exchange's copy of every fill; **recon** (reconciliation) means checking two records agree.

Picking the right container is the #1 performance lever in everyday Python.

| Operation | list | set / dict |
|---|---|---|
| `x in c` | O(n) — scans | **O(1)** average — hash lookup |
| append / add | O(1) | O(1) |
| keeps order | yes | dict: insertion order; set: no |

**Big-O** describes how work grows with input size *n*. O(n²) — a loop inside a loop over the same data — is fine for 100 rows and hopeless for 2 million.

```python
# O(n²): for each id, scan the list again
dupes = [i for i in ids if ids.count(i) > 1]
# O(n): count once with a dict
from collections import Counter
dupes = [i for i, c in Counter(ids).items() if c > 1]
```

Handy tools in `collections`:
- `Counter(iterable)` — counts; `.most_common(3)`
- `defaultdict(list)` — dict that auto-creates missing values: `groups[acct].append(trade)`
- `deque` — fast append/pop from both ends (queues, rolling windows)

Set algebra is recon in one line: `a - b` (in a, not b), `a & b` (both), `a ^ b` (in exactly one).
''',
examples=[("Set algebra = reconciliation", r'''
internal = {"T1", "T2", "T3", "T5"}
clearing = {"T1", "T3", "T4", "T5"}
print("missing at clearing:", sorted(internal - clearing))
print("unknown to us:     ", sorted(clearing - internal))
print("matched:           ", sorted(internal & clearing))
'''), ("Why O(n) matters", r'''
import time
ids = list(range(20000))
t = time.time(); s = set(ids); hits = sum(1 for i in range(0, 40000, 2) if i in s); print("set :", round(time.time() - t, 4), "s")
t = time.time(); hits = sum(1 for i in range(0, 4000, 2) if i in ids); print("list:", round(time.time() - t, 4), "s  (on 10x FEWER lookups!)")
'''), ("defaultdict grouping", r'''
from collections import defaultdict, Counter
trades = [("HF-A", "ES"), ("HF-B", "CL"), ("HF-A", "NQ"), ("HF-A", "ES")]
by_acct = defaultdict(list)
for acct, sym in trades:
    by_acct[acct].append(sym)
print(dict(by_acct))
print(Counter(sym for _, sym in trades).most_common(1))
''')],
quiz=[q("You must check 1,000,000 trade IDs against a list of 500,000 clearing IDs. Best first step?", ["Sort both lists", "Convert the clearing IDs to a set", "Use a nested loop", "Use a pandas plot"], 1, "Building a set is O(n) once; each membership test is then O(1). Nested loops would be ~5×10¹¹ comparisons.")],
exercises=[
ex("find_duplicates(ids)", r'''
Write `find_duplicates(ids)` returning a **sorted list** of IDs that appear more than once. It must be O(n) (use `Counter` or a set), since it'll run on millions of rows.
''', r'''
from collections import Counter

def find_duplicates(ids):
    ...

print(find_duplicates(["T1", "T2", "T1", "T3", "T2", "T2"]))
''', r'''
from collections import Counter

def find_duplicates(ids):
    return sorted(i for i, c in Counter(ids).items() if c > 1)

print(find_duplicates(["T1", "T2", "T1", "T3", "T2", "T2"]))
''', [("basic", r'''
r = find_duplicates(["T1", "T2", "T1", "T3", "T2", "T2"])
assert r == ["T1", "T2"], f"got {r}" + (" — each duplicate ID should appear once in the output" if r and len(r) != len(set(r)) else "")
'''), ("no dupes", r'''assert find_duplicates(["A", "B"]) == [], "No duplicates → empty list"'''),
("large input", r'''
import time
ids = [f"T{i}" for i in range(20000)] + ["T5", "T19999"]
t = time.time(); r = find_duplicates(ids); dt = time.time() - t
assert r == ["T19999", "T5"], f"got {r[:5]}"
assert dt < 1.0, f"took {dt:.1f}s on 20k IDs — that's O(n²). Count in one pass with Counter."
''')], hints=["Counter(ids) gives {id: count}", "sorted(i for i, c in counts.items() if c > 1)"],
wrong=r'''
def find_duplicates(ids):
    return [i for i in ids if ids.count(i) > 1]
'''),
ex("Recon with sets", r'''
Write `recon_ids(internal, clearing)` returning a dict with three **sorted lists**:
`"missing_at_clearing"` (ours, not theirs), `"unknown_to_us"` (theirs, not ours), `"matched_count"` (an int).
''', r'''
def recon_ids(internal, clearing):
    ...

print(recon_ids(["T1", "T2", "T3"], ["T2", "T3", "T9"]))
''', r'''
def recon_ids(internal, clearing):
    a, b = set(internal), set(clearing)
    return {"missing_at_clearing": sorted(a - b),
            "unknown_to_us": sorted(b - a),
            "matched_count": len(a & b)}

print(recon_ids(["T1", "T2", "T3"], ["T2", "T3", "T9"]))
''', [("missing_at_clearing", r'''
r = recon_ids(["T1", "T2", "T3", "T7"], ["T2", "T3", "T9"])
assert r["missing_at_clearing"] == ["T1", "T7"], f"got {r.get('missing_at_clearing')}"
'''), ("unknown_to_us", r'''
r = recon_ids(["T1", "T2", "T3", "T7"], ["T2", "T3", "T9"])
assert r["unknown_to_us"] == ["T9"], f"got {r.get('unknown_to_us')} — this is clearing minus internal"
'''), ("matched_count", r'''
r = recon_ids(["T1", "T2", "T3", "T7", "T2"], ["T2", "T3", "T9"])
assert r["matched_count"] == 2, f"got {r.get('matched_count')} — count unique matched IDs (set intersection)"
''')], hints=["Convert both inputs to sets first.", "a - b, b - a, a & b"],
wrong=r'''
def recon_ids(internal, clearing):
    a, b = set(internal), set(clearing)
    return {"missing_at_clearing": sorted(a ^ b), "unknown_to_us": sorted(b - a), "matched_count": len([x for x in internal if x in b])}
'''),
])

lesson("u2l2", "Functions in depth: keyword args, lambdas, pitfalls",
"Build reusable helpers (bps conversion, slippage, ranking) that every script on the desk can import.",
r'''
> **New in this lesson** (builds on Python from Zero and Python on a Trading Desk)
>
> - **Desk words:** a **basis point (bp)** is 0.01% (1/10,000). **Slippage** = how far your fill price was from the price when the order arrived, in bps; positive means it cost you.
> - **Keyword arguments:** pass inputs by name, `f(side="SELL")`, so the order doesn't matter and the call explains itself.
> - **Returning several values:** `return total, worst` returns a tuple; unpack it with `t, w = f(x)`.
> - **`*args` / `**kwargs`:** collect any number of extra inputs (by position / by name).
> - **`None` checks:** `if book is None:` tests for Python's "nothing" value.
> - **Side effect:** anything a function does besides returning a value (printing, changing a list passed in).

```python
def slippage_bps(fill_px, arrival_px, side="BUY"):
    sign = 1 if side == "BUY" else -1
    return sign * (fill_px - arrival_px) / arrival_px * 10_000
```

- **Keyword arguments** make calls self-documenting: `slippage_bps(fill_px=101.2, arrival_px=101.0, side="SELL")`.
- **Return multiple values** as a tuple: `return total, worst` → `t, w = f(x)`.
- `*args` collects extra positional args, `**kwargs` extra keyword args.
- **lambda**: a tiny unnamed function, mostly for `key=`: `sorted(rows, key=lambda r: (-r["shortfall"], r["account"]))` → sort by shortfall desc, then account asc (tuples compare element by element).

**Pitfall — mutable default args.** Defaults are evaluated *once*, so a list default is shared between calls:

```python
def add(trade, book=[]):   # BUG
    book.append(trade); return book
```
Use `book=None` then `if book is None: book = []`.

**Pure functions** (output depends only on inputs, no side effects) are the easiest to test and reason about — aim for them in risk calcs.
''',
examples=[("Sort by two keys", r'''
rows = [("HF-B", 250_000), ("HF-A", 900_000), ("FO-C", 250_000), ("HF-D", 0)]
top = sorted(rows, key=lambda r: (-r[1], r[0]))
for acct, short in top:
    print(f"{acct:6} {short:>10,}")
''')],
quiz=[q("What prints?", ["[1] [2]", "[1] [1, 2]", "[1, 2] [1, 2]", "Error"], 1, "The default list is created once and shared, so the second call appends to the same list. Use `book=None`.",
        code=r'''
def add(x, book=[]):
    book.append(x)
    return book
print(add(1), end=" ")
print(add(2))
''')],
exercises=[
ex("slippage_bps()", r'''
Write `slippage_bps(fill_px, arrival_px, side="BUY")` returning slippage vs arrival in basis points where **positive = cost to the client**.
Buying above arrival is a cost; selling below arrival is a cost.
''', r'''
def slippage_bps(fill_px, arrival_px, side="BUY"):
    ...

print(slippage_bps(100.05, 100.00))           # 5 bps cost
print(slippage_bps(99.90, 100.00, side="SELL"))  # 10 bps cost
''', r'''
def slippage_bps(fill_px, arrival_px, side="BUY"):
    sign = 1 if side == "BUY" else -1
    return sign * (fill_px - arrival_px) / arrival_px * 10_000

print(slippage_bps(100.05, 100.00))
print(slippage_bps(99.90, 100.00, side="SELL"))
''', [("buy cost", r'''assert _close(slippage_bps(100.05, 100.00), 5.0), f"got {slippage_bps(100.05, 100.00)}"'''),
("sell cost", r'''
r = slippage_bps(99.90, 100.00, side="SELL")
assert _close(r, 10.0), f"got {r}" + (" — for a SELL, a lower fill is a cost, so flip the sign" if _close(r, -10.0) else "")
'''), ("improvement is negative", r'''assert _close(slippage_bps(100.10, 100.00, "SELL"), -10.0), "Selling above arrival is price improvement → negative"'''),
("keyword call", r'''assert _close(slippage_bps(arrival_px=50.0, fill_px=50.05, side="BUY"), 10.0)''')],
hints=["bps = (fill − arrival) / arrival × 10,000", "Multiply by −1 for SELL."],
wrong=r'''
def slippage_bps(fill_px, arrival_px, side="BUY"):
    return (fill_px - arrival_px) / arrival_px * 10_000
'''),
ex("top_n() with a safe default", r'''
Write `top_n(rows, n=3, exclude=None)`:
- `rows` is a list of `(account, shortfall)` tuples
- drop accounts listed in `exclude` (default: exclude nothing) and rows with shortfall ≤ 0
- return the top `n` sorted by shortfall **desc**, ties by account **asc**
''', r'''
def top_n(rows, n=3, exclude=None):
    ...

rows = [("HF-B", 250_000), ("HF-A", 900_000), ("FO-C", 250_000), ("HF-D", 0), ("HF-E", 400_000)]
print(top_n(rows))
''', r'''
def top_n(rows, n=3, exclude=None):
    if exclude is None:
        exclude = set()
    keep = [r for r in rows if r[1] > 0 and r[0] not in exclude]
    return sorted(keep, key=lambda r: (-r[1], r[0]))[:n]

rows = [("HF-B", 250_000), ("HF-A", 900_000), ("FO-C", 250_000), ("HF-D", 0), ("HF-E", 400_000)]
print(top_n(rows))
''', [("default n", r'''
rows = [("HF-B", 250_000), ("HF-A", 900_000), ("FO-C", 250_000), ("HF-D", 0), ("HF-E", 400_000)]
r = top_n(rows)
assert r == [("HF-A", 900_000), ("HF-E", 400_000), ("FO-C", 250_000)], f"got {r} — ties (250k) break by account name A→Z, so FO-C before HF-B"
'''), ("exclude", r'''
rows = [("HF-B", 250_000), ("HF-A", 900_000), ("FO-C", 250_000)]
assert top_n(rows, n=5, exclude={"HF-A"}) == [("FO-C", 250_000), ("HF-B", 250_000)]
'''), ("zero dropped", r'''assert top_n([("X", 0), ("Y", -5)]) == [], "Shortfall ≤ 0 means no call — drop those rows"''')],
hints=["key=lambda r: (-r[1], r[0])", "Use exclude=None and create the set inside the function."],
wrong=r'''
def top_n(rows, n=3, exclude=[]):
    return sorted([r for r in rows if r[0] not in exclude], key=lambda r: r[1], reverse=True)[:n]
'''),
])

lesson("u2l3", "Error handling: one bad row shouldn't kill the report",
"Make the morning clearing-file load robust: skip and report bad rows instead of crashing at 6:45am.",
r'''
```python
try:
    qty = int(text)
except ValueError:
    print("bad qty:", text)
else:
    print("parsed ok")      # runs only if no exception
finally:
    print("always runs")    # cleanup
```

- Catch **specific** exceptions (`ValueError`, `KeyError`) — never a bare `except:` that hides bugs.
- **Raise** your own errors with a clear message: `raise ValueError(f"bad quantity: {text!r}")`. (`!r` shows quotes, so blanks are visible.)
- Pattern for files: **collect** errors with their line numbers and continue; report them at the end. Silent skipping is how breaks go unnoticed.

Common exceptions: `ValueError` (bad value, e.g. `int("abc")`), `KeyError` (missing dict key), `TypeError` (wrong type), `ZeroDivisionError`, `FileNotFoundError`.
''',
examples=[("Try it", r'''
for text in ["25", " 1,000 ", "abc", ""]:
    try:
        q = int(text.replace(",", ""))
    except ValueError as e:
        print(f"skip {text!r}: {e}")
    else:
        print("ok", q)
''')],
quiz=[q("Which is the best practice?", ["`except:` to catch everything", "`except Exception: pass`", "`except ValueError as e:` and log the row", "Never use try/except"], 2, "Catch the specific error you expect and record it; broad silent catches hide real bugs.")],
exercises=[
ex("parse_qty(text)", r'''
Write `parse_qty(text)` that:
- strips spaces and removes thousands commas (`" 1,000 "` → 1000); allows a leading minus
- raises `ValueError` with a message containing the original text if it isn't an integer
- raises `ValueError` if the quantity is 0 (a zero-qty trade is always a data error)
''', r'''
def parse_qty(text):
    ...

print(parse_qty(" 1,000 "))
''', r'''
def parse_qty(text):
    cleaned = text.strip().replace(",", "")
    try:
        q = int(cleaned)
    except ValueError:
        raise ValueError(f"bad quantity: {text!r}")
    if q == 0:
        raise ValueError(f"zero quantity: {text!r}")
    return q

print(parse_qty(" 1,000 "))
''', [("cleans input", r'''
assert parse_qty(" 1,000 ") == 1000 and parse_qty("-25") == -25, f"got {parse_qty(' 1,000 ')!r}"
'''), ("bad text raises ValueError", r'''
try:
    parse_qty("12x")
    assert False, "parse_qty('12x') should raise ValueError, but returned normally"
except ValueError as e:
    assert "12x" in str(e), f"Error message should include the bad text; got {str(e)!r}"
'''), ("zero raises", r'''
try:
    parse_qty("0")
    assert False, "parse_qty('0') should raise ValueError — zero-qty trades are data errors"
except ValueError:
    pass
''')], hints=["text.strip().replace(',', '')", "Wrap int(...) in try/except ValueError and re-raise with your own message."],
wrong=r'''
def parse_qty(text):
    try:
        return int(text.strip().replace(",", ""))
    except ValueError:
        return 0
'''),
ex("load_rows(lines)", r'''
Write `load_rows(lines)` → `(good, errors)`:
- `lines` are `"account,qty"` strings (no header)
- `good`: list of `(account, qty)` using `parse_qty` (provided)
- `errors`: list of `(line_number, message)` with **1-based** line numbers; include rows with the wrong number of fields (message of your choice)
''', r'''
def parse_qty(text):
    cleaned = text.strip().replace(",", "")
    try:
        q = int(cleaned)
    except ValueError:
        raise ValueError(f"bad quantity: {text!r}")
    if q == 0:
        raise ValueError(f"zero quantity: {text!r}")
    return q

def load_rows(lines):
    good, errors = [], []
    for n, line in enumerate(lines, start=1):
        ...
    return good, errors

print(load_rows(["HF-A,100", "HF-B,abc", "HF-C", "HF-D,-5"]))
''', r'''
def parse_qty(text):
    cleaned = text.strip().replace(",", "")
    try:
        q = int(cleaned)
    except ValueError:
        raise ValueError(f"bad quantity: {text!r}")
    if q == 0:
        raise ValueError(f"zero quantity: {text!r}")
    return q

def load_rows(lines):
    good, errors = [], []
    for n, line in enumerate(lines, start=1):
        parts = line.split(",")
        if len(parts) != 2:
            errors.append((n, f"expected 2 fields, got {len(parts)}"))
            continue
        try:
            good.append((parts[0].strip(), parse_qty(parts[1])))
        except ValueError as e:
            errors.append((n, str(e)))
    return good, errors

print(load_rows(["HF-A,100", "HF-B,abc", "HF-C", "HF-D,-5"]))
''', [("good rows", r'''
g, e = load_rows(["HF-A,100", "HF-B,abc", "HF-C", "HF-D,-5", "HF-E,0"])
assert g == [("HF-A", 100), ("HF-D", -5)], f"good = {g}"
'''), ("error line numbers", r'''
g, e = load_rows(["HF-A,100", "HF-B,abc", "HF-C", "HF-D,-5", "HF-E,0"])
nums = [x[0] for x in e]
assert nums == [2, 3, 5], f"error line numbers = {nums}; expected [2, 3, 5] (1-based; 'HF-C' has too few fields; qty 0 is invalid)"
'''), ("messages", r'''
g, e = load_rows(["HF-B,abc"])
assert e and "abc" in e[0][1], f"errors = {e} — keep parse_qty's message so ops can see the bad value"
''')], hints=["enumerate(lines, start=1) gives 1-based numbers", "Check len(parts) before parsing; wrap parse_qty in try/except ValueError as e."],
wrong=r'''
def load_rows(lines):
    good, errors = [], []
    for n, line in enumerate(lines):
        try:
            a, q = line.split(",")
            good.append((a, int(q)))
        except ValueError as e:
            errors.append((n, str(e)))
    return good, errors
'''),
])

lesson("u2l4", "Files: CSV and JSON in and out",
"Read the clearing statement CSV and write a JSON summary your dashboard (or Foundry pipeline) can load.",
r'''
Python's built-in `csv` module handles quoting and commas inside fields correctly — don't hand-split real files.

```python
import csv
with open("positions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["account", "symbol", "qty"])
    w.writeheader()
    w.writerows(rows)                 # rows: list of dicts

with open("positions.csv") as f:
    rows = list(csv.DictReader(f))    # every value comes back as a STRING
```

`with open(...)` closes the file automatically, even on error. Modes: `"r"` read, `"w"` overwrite, `"a"` append.

**JSON** maps to dicts/lists: `json.dumps(obj, indent=2)` → string, `json.loads(s)` → object; `json.dump(obj, f)` / `json.load(f)` for files.

`io.StringIO(text)` makes a string behave like a file — great for tests and for this app. (Yes, this browser Python has a real virtual filesystem, so `open()` works here too.)
''',
examples=[("Round-trip a CSV", r'''
import csv, io, json
text = 'account,symbol,qty\nHF-A,ES,10\n"FUND, LP",CL,-5\n'
rows = list(csv.DictReader(io.StringIO(text)))
print(rows[1])       # note: comma inside quotes handled
print(json.dumps({"n": len(rows), "accounts": [r["account"] for r in rows]}, indent=2))
''')],
quiz=[q("After `csv.DictReader`, what type is `row[\"qty\"]` for the value 10?", ["int", "float", "str", "Decimal"], 2, "CSV is text — every field comes back as a string. Convert with int()/float().")],
exercises=[
ex("Write & read positions.csv", r'''
Write `write_positions(path, rows)` (rows = list of dicts with keys account, symbol, qty) using `csv.DictWriter` with a header, and `read_positions(path)` returning the list of dicts with **qty as int**.
''', r'''
import csv

def write_positions(path, rows):
    ...

def read_positions(path):
    ...

write_positions("positions.csv", [{"account": "HF-A", "symbol": "ES", "qty": 10}])
print(open("positions.csv").read())
print(read_positions("positions.csv"))
''', r'''
import csv

def write_positions(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["account", "symbol", "qty"])
        w.writeheader()
        w.writerows(rows)

def read_positions(path):
    with open(path) as f:
        return [{**r, "qty": int(r["qty"])} for r in csv.DictReader(f)]

write_positions("positions.csv", [{"account": "HF-A", "symbol": "ES", "qty": 10}])
print(open("positions.csv").read())
print(read_positions("positions.csv"))
''', [("file has header", r'''
write_positions("t_pos.csv", [{"account": "X", "symbol": "NQ", "qty": -3}, {"account": "FUND, LP", "symbol": "CL", "qty": 7}])
first = open("t_pos.csv").read().splitlines()[0]
assert first == "account,symbol,qty", f"first line = {first!r}"
'''), ("round trip with int qty", r'''
rows = [{"account": "X", "symbol": "NQ", "qty": -3}, {"account": "FUND, LP", "symbol": "CL", "qty": 7}]
write_positions("t_pos2.csv", rows)
back = read_positions("t_pos2.csv")
assert back == rows, f"read back {back}" + (" — qty must be converted to int" if back and isinstance(back[0].get("qty"), str) else "")
''')], hints=["with open(path, 'w', newline='') as f:", "{**r, 'qty': int(r['qty'])} copies a dict and overrides one key"],
wrong=r'''
def write_positions(path, rows):
    with open(path, "w") as f:
        f.write("account,symbol,qty\n")
        for r in rows:
            f.write(f"{r['account']},{r['symbol']},{r['qty']}\n")
def read_positions(path):
    import csv
    return list(csv.DictReader(open(path)))
'''),
ex("summary_json(rows)", r'''
Write `summary_json(rows)` returning a **JSON string** with keys:
`"accounts"` (number of unique accounts), `"gross_qty"` (sum of |qty|), `"by_symbol"` (dict symbol → net qty).
''', r'''
import json

def summary_json(rows):
    ...

rows = [{"account": "A", "symbol": "ES", "qty": 10}, {"account": "B", "symbol": "ES", "qty": -4}, {"account": "A", "symbol": "CL", "qty": -2}]
print(summary_json(rows))
''', r'''
import json

def summary_json(rows):
    by_symbol = {}
    for r in rows:
        by_symbol[r["symbol"]] = by_symbol.get(r["symbol"], 0) + r["qty"]
    return json.dumps({"accounts": len({r["account"] for r in rows}),
                       "gross_qty": sum(abs(r["qty"]) for r in rows),
                       "by_symbol": by_symbol})

rows = [{"account": "A", "symbol": "ES", "qty": 10}, {"account": "B", "symbol": "ES", "qty": -4}, {"account": "A", "symbol": "CL", "qty": -2}]
print(summary_json(rows))
''', [("returns a string", r'''
rows = [{"account": "A", "symbol": "ES", "qty": 10}, {"account": "B", "symbol": "ES", "qty": -4}, {"account": "A", "symbol": "CL", "qty": -2}]
s = summary_json(rows)
assert isinstance(s, str), f"Return json.dumps(...) — a string — not a {type(s).__name__}"
'''), ("content", r'''
import json
rows = [{"account": "A", "symbol": "ES", "qty": 10}, {"account": "B", "symbol": "ES", "qty": -4}, {"account": "A", "symbol": "CL", "qty": -2}]
d = json.loads(summary_json(rows))
assert d["accounts"] == 2, f"accounts = {d.get('accounts')}"
assert d["gross_qty"] == 16, f"gross_qty = {d.get('gross_qty')} (sum of absolute quantities)"
assert d["by_symbol"] == {"ES": 6, "CL": -2}, f"by_symbol = {d.get('by_symbol')}"
''')], hints=["len({r['account'] for r in rows})", "json.dumps(dict)"],
wrong=r'''
def summary_json(rows):
    return {"accounts": len(rows), "gross_qty": sum(r["qty"] for r in rows), "by_symbol": {}}
'''),
])

lesson("u2l5", "Dates & times: settlement, expiries, business days",
"Compute settlement dates, futures expiries and days-to-expiry for the positions and financing reports.",
r'''
```python
from datetime import date, datetime, timedelta
d = date(2026, 10, 9)
d + timedelta(days=3)          # date(2026, 10, 12)
d.weekday()                    # Mon=0 … Fri=4, Sat=5, Sun=6
(date(2026, 12, 18) - d).days  # 70  → int days between
datetime.strptime("2026-10-09 14:30", "%Y-%m-%d %H:%M")   # parse
d.strftime("%d-%b-%Y")         # '09-Oct-2026'  format
```

**Business days**: skip weekends *and* the right holiday calendar. Holidays differ by market — e.g. Columbus Day (Oct 12, 2026) is a SIFMA bond-market holiday but US equity and CME equity futures trade. Always pass the calendar in as a parameter.

**Settlement**: US equities and corporate bonds settle **T+1** (since May 2024); USTs typically T+1; FX spot T+2 for most pairs (USD/CAD T+1).

**Equity index futures & options** (ES, NQ) expire on the **third Friday** of the contract month (quarterlies Mar/Jun/Sep/Dec).

Time zones: use timezone-aware datetimes (`zoneinfo.ZoneInfo("America/New_York")`) whenever timestamps cross systems — CME Globex uses Central Time.
''',
examples=[("Walk forward business days", r'''
from datetime import date, timedelta
d = date(2026, 10, 9)   # Friday
for i in range(4):
    d += timedelta(days=1)
    print(d, d.strftime("%a"), "weekend" if d.weekday() >= 5 else "")
''')],
quiz=[q("`date(2026, 10, 10).weekday()` returns 5. What day is Oct 10, 2026?", ["Friday", "Saturday", "Sunday", "Thursday"], 1, "Monday is 0, so 5 is Saturday.")],
exercises=[
ex("add_business_days()", r'''
Write `add_business_days(d, n, holidays=())` returning the date `n` business days after `d` (skip Sat/Sun and any date in `holidays`). Assume n ≥ 0.
''', r'''
from datetime import date, timedelta

def add_business_days(d, n, holidays=()):
    ...

print(add_business_days(date(2026, 10, 9), 1))
''', r'''
from datetime import date, timedelta

def add_business_days(d, n, holidays=()):
    hol = set(holidays)
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5 and d not in hol:
            n -= 1
    return d

print(add_business_days(date(2026, 10, 9), 1))
''', [("over a weekend", r'''
from datetime import date
r = add_business_days(date(2026, 10, 9), 1)
assert r == date(2026, 10, 12), f"Fri Oct 9 + 1 business day should be Mon Oct 12; got {r}"
'''), ("with a holiday (bond-market calendar)", r'''
from datetime import date
r = add_business_days(date(2026, 10, 9), 1, holidays={date(2026, 10, 12)})
assert r == date(2026, 10, 13), f"With Oct 12 a holiday → Tue Oct 13; got {r}"
'''), ("n=0 and multi-day", r'''
from datetime import date
assert add_business_days(date(2026, 10, 7), 0) == date(2026, 10, 7)
r = add_business_days(date(2026, 12, 23), 3, holidays=[date(2026, 12, 25)])
assert r == date(2026, 12, 29), f"Dec 23 + 3 bd skipping Christmas and the weekend → Dec 29; got {r}"
''')], hints=["Loop: step one calendar day at a time; only count it if weekday() < 5 and not a holiday."],
wrong=r'''
from datetime import timedelta
def add_business_days(d, n, holidays=()):
    d = d + timedelta(days=n)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d
'''),
ex("third_friday() and days_to_expiry()", r'''
Write `third_friday(year, month)` → `date` of the 3rd Friday, and `days_to_expiry(as_of, year, month)` → calendar days from `as_of` to that date.
''', r'''
from datetime import date, timedelta

def third_friday(year, month):
    ...

def days_to_expiry(as_of, year, month):
    ...

print(third_friday(2026, 12))
''', r'''
from datetime import date, timedelta

def third_friday(year, month):
    d = date(year, month, 1)
    offset = (4 - d.weekday()) % 7        # days until first Friday
    return d + timedelta(days=offset + 14)

def days_to_expiry(as_of, year, month):
    return (third_friday(year, month) - as_of).days

print(third_friday(2026, 12))
''', [("Dec 2026 ES expiry", r'''
from datetime import date
assert third_friday(2026, 12) == date(2026, 12, 18), f"got {third_friday(2026, 12)}"
'''), ("month starting on a Friday", r'''
from datetime import date
r = third_friday(2027, 1)
assert r == date(2027, 1, 15), f"Jan 1 2027 is a Friday, so the 3rd Friday is Jan 15; got {r}"
'''), ("more months", r'''
from datetime import date
got = [third_friday(2026, m).day for m in (3, 6, 9)]
assert got == [20, 19, 18], f"3rd Fridays of Mar/Jun/Sep 2026 should be the 20th/19th/18th; got {got}. If the 1st is after Friday, (4 - weekday) goes negative — use % 7."
'''), ("days_to_expiry", r'''
from datetime import date
assert days_to_expiry(date(2026, 9, 30), 2026, 12) == 79, f"got {days_to_expiry(date(2026, 9, 30), 2026, 12)}"
''')], hints=["Friday is weekday 4. Days to first Friday: (4 − first.weekday()) % 7", "Then add 14 days."],
wrong=r'''
from datetime import date, timedelta
def third_friday(year, month):
    d = date(year, month, 1)
    return d + timedelta(days=(4 - d.weekday()) + 14)
def days_to_expiry(as_of, year, month):
    return (third_friday(year, month) - as_of).days
'''),
])

lesson("u2l6", "Classes & dataclasses: modeling positions and accounts",
"Model positions and accounts as objects so notional, P&L and margin logic lives in one tested place.",
r'''
A **class** bundles data with the functions (methods) that act on it. `@dataclass` writes the boilerplate (`__init__`, `__repr__`, `__eq__`) for you:

```python
from dataclasses import dataclass, field

@dataclass
class Position:
    account: str
    symbol: str
    qty: int
    price: float
    multiplier: float

    def __post_init__(self):            # runs after __init__: validate
        if self.multiplier <= 0:
            raise ValueError("multiplier must be positive")

    @property
    def notional(self) -> float:        # accessed like an attribute: p.notional
        return abs(self.qty) * self.price * self.multiplier

    def pnl(self, new_price: float) -> float:
        return (new_price - self.price) * self.qty * self.multiplier
```

- `self` is the instance. Methods are functions that receive it first.
- Mutable defaults need `field(default_factory=list)` (same pitfall as function defaults).
- `@dataclass(frozen=True)` makes instances immutable — good for trades/events.

When to use a class vs a dict: once several functions pass the same bundle of fields around, or you want validation in one place, make it a dataclass. For large tables, use pandas.
''',
examples=[("A frozen Trade", r'''
from dataclasses import dataclass
@dataclass(frozen=True)
class Trade:
    trade_id: str
    symbol: str
    qty: int
t = Trade("T1", "ES", 10)
print(t)
try:
    t.qty = 99
except Exception as e:
    print(type(e).__name__, "- trades are immutable events")
''')],
quiz=[q("Why `field(default_factory=list)` instead of `positions: list = []` in a dataclass?", ["It's faster", "So each instance gets its own new list", "Lists aren't allowed in dataclasses", "To make it immutable"], 1, "A plain `[]` default would be shared by every instance (dataclasses actually refuse it for this reason).")],
exercises=[
ex("Position dataclass", r'''
Complete `Position` with: a `notional` **property** (gross), a `pnl(new_price)` method, and validation in `__post_init__` raising `ValueError` if `multiplier <= 0`.
''', r'''
from dataclasses import dataclass

@dataclass
class Position:
    account: str
    symbol: str
    qty: int
    price: float
    multiplier: float

    # add __post_init__, notional property, pnl method

p = Position("HF-A", "CL", -10, 71.40, 1000)
print(p)
''', r'''
from dataclasses import dataclass

@dataclass
class Position:
    account: str
    symbol: str
    qty: int
    price: float
    multiplier: float

    def __post_init__(self):
        if self.multiplier <= 0:
            raise ValueError("multiplier must be positive")

    @property
    def notional(self):
        return abs(self.qty) * self.price * self.multiplier

    def pnl(self, new_price):
        return (new_price - self.price) * self.qty * self.multiplier

p = Position("HF-A", "CL", -10, 71.40, 1000)
print(p)
''', [("notional property", r'''
p = Position("HF-A", "CL", -10, 71.40, 1000)
assert not callable(getattr(p, "notional", None)), "notional should be a @property (p.notional, no parentheses)"
assert _close(p.notional, 714000.0), f"notional = {p.notional}; gross notional uses abs(qty)"
'''), ("pnl", r'''
p = Position("HF-A", "CL", -10, 71.40, 1000)
assert _close(p.pnl(70.90), 5000.0), f"short 10 CL from 71.40 → 70.90 should make +5,000; got {p.pnl(70.90)}"
'''), ("validation", r'''
try:
    Position("X", "ES", 1, 5000.0, 0)
    assert False, "Position(..., multiplier=0) should raise ValueError in __post_init__"
except ValueError:
    pass
''')], hints=["@property above def notional(self):", "def __post_init__(self): if self.multiplier <= 0: raise ValueError(...)"],
wrong=r'''
from dataclasses import dataclass
@dataclass
class Position:
    account: str
    symbol: str
    qty: int
    price: float
    multiplier: float
    def notional(self):
        return self.qty * self.price * self.multiplier
    def pnl(self, new_price):
        return (new_price - self.price) * self.qty * self.multiplier
'''),
ex("Account with a list of positions", r'''
Write dataclass `Account(name, positions=[])` using `field(default_factory=list)`, with methods `add(position)`, `gross_notional()` and `pnl(prices)` where `prices` maps symbol → new price. `Position` is provided.
''', r'''
from dataclasses import dataclass, field

@dataclass
class Position:
    account: str
    symbol: str
    qty: int
    price: float
    multiplier: float
    @property
    def notional(self):
        return abs(self.qty) * self.price * self.multiplier
    def pnl(self, new_price):
        return (new_price - self.price) * self.qty * self.multiplier

@dataclass
class Account:
    name: str
    # positions field here

acct = Account("HF-A")
''', r'''
from dataclasses import dataclass, field

@dataclass
class Position:
    account: str
    symbol: str
    qty: int
    price: float
    multiplier: float
    @property
    def notional(self):
        return abs(self.qty) * self.price * self.multiplier
    def pnl(self, new_price):
        return (new_price - self.price) * self.qty * self.multiplier

@dataclass
class Account:
    name: str
    positions: list = field(default_factory=list)

    def add(self, position):
        self.positions.append(position)

    def gross_notional(self):
        return sum(p.notional for p in self.positions)

    def pnl(self, prices):
        return sum(p.pnl(prices[p.symbol]) for p in self.positions)

acct = Account("HF-A")
''', [("independent lists", r'''
a, b = Account("A"), Account("B")
a.add(Position("A", "ES", 2, 5000.0, 50))
assert len(b.positions) == 0, "Adding to account A changed account B — use field(default_factory=list)"
'''), ("gross_notional", r'''
a = Account("A")
a.add(Position("A", "ES", 2, 5000.0, 50)); a.add(Position("A", "CL", -3, 70.0, 1000))
assert _close(a.gross_notional(), 710000.0), f"got {a.gross_notional()}"
'''), ("pnl", r'''
a = Account("A")
a.add(Position("A", "ES", 2, 5000.0, 50)); a.add(Position("A", "CL", -3, 70.0, 1000))
r = a.pnl({"ES": 4990.0, "CL": 69.0})
assert _close(r, 2000.0), f"ES: −10×2×50 = −1,000; CL: −1×−3×1000 = +3,000 → +2,000; got {r}"
''')], hints=["positions: list = field(default_factory=list)", "sum(p.pnl(prices[p.symbol]) for p in self.positions)"],
wrong=r'''
from dataclasses import dataclass
@dataclass
class Position:
    account: str
    symbol: str
    qty: int
    price: float
    multiplier: float
    @property
    def notional(self): return abs(self.qty) * self.price * self.multiplier
    def pnl(self, new_price): return (new_price - self.price) * self.qty * self.multiplier
SHARED = []
@dataclass
class Account:
    name: str
    def __post_init__(self):
        self.positions = SHARED
    def add(self, p): self.positions.append(p)
    def gross_notional(self): return sum(p.notional for p in self.positions)
    def pnl(self, prices): return sum(p.pnl(prices[p.symbol]) for p in self.positions)
'''),
])

lesson("u2l7", "Type hints & clean code",
"Write risk scripts a colleague (or reviewer at Palantir) can read, trust and extend.",
r'''
**Type hints** document intent and let editors/linters (mypy, pyright) catch bugs. Python doesn't enforce them at runtime.

```python
from typing import Optional

def collateral_value(market_value: float, haircut: float) -> float:
    """Post-haircut value. haircut is a fraction, e.g. 0.02 for 2%."""
    return market_value * (1 - haircut)

def find_account(accounts: dict[str, float], name: str) -> Optional[float]:
    return accounts.get(name)   # may be None
```

Clean-code habits that interviewers notice:
- **Names say what, units included**: `haircut_pct` vs `haircut_frac`, `notional_usd`, `days_to_maturity` — not `x`, `tmp`, `d2`.
- **No magic numbers**: `DAYS_IN_YEAR_ACT360 = 360` at the top.
- **Small functions** that do one thing; **early returns** instead of deep nesting.
- **Docstrings** on anything non-obvious (units, conventions, sign).
- Don't repeat yourself — but don't abstract before the second copy.
- Format with `black`/`ruff` at work; this editor won't, so keep 4-space indents.
''',
examples=[("Before → after", r'''
# before
def f(a, b):
    r = 0
    for x in a:
        if x[2] in b:
            if b[x[2]]:
                r = r + x[1] * (1 - 0.02)
    return r

# after
UST_HAIRCUT = 0.02

def eligible_collateral_value(holdings: list[tuple[str, float, str]], eligible: dict[str, bool]) -> float:
    """Sum post-haircut market value of holdings whose asset type is eligible."""
    total = 0.0
    for _name, market_value, asset_type in holdings:
        if not eligible.get(asset_type, False):
            continue
        total += market_value * (1 - UST_HAIRCUT)
    return total

h = [("T 4.25 2030", 1_000_000.0, "UST"), ("AAPL", 500_000.0, "EQUITY")]
print(f(h, {"UST": True, "EQUITY": False}), eligible_collateral_value(h, {"UST": True, "EQUITY": False}))
''')],
quiz=[q("Which name is best for a haircut of 2% stored as 0.02?", ["h", "haircut", "haircut_frac", "HAIRCUT_PERCENT"], 2, "It says the unit: a fraction (0.02), not percent (2). Ambiguous units cause real losses.")],
exercises=[
ex("Refactor into clean, typed functions", r'''
Rewrite the messy `calc` below as two typed functions with docstrings:
- `haircut_value(market_value: float, haircut_frac: float) -> float`
- `pool_value(assets: list[dict], schedule: dict[str, float]) -> float` — sum of haircut values; assets whose `type` is **not in** `schedule` are ineligible (contribute 0).

Same results as `calc`. Type hints are checked!
''', r'''
def calc(a, s):
    t = 0
    for i in a:
        if i["type"] in s:
            t = t + i["mv"] * (1 - s[i["type"]])
    return t

SCHEDULE = {"CASH": 0.0, "UST": 0.02, "AGENCY": 0.04, "EQUITY": 0.20}
ASSETS = [{"type": "UST", "mv": 10_000_000}, {"type": "EQUITY", "mv": 2_000_000}, {"type": "CORP", "mv": 1_000_000}]
print(calc(ASSETS, SCHEDULE))

# your clean version:
''', r'''
SCHEDULE = {"CASH": 0.0, "UST": 0.02, "AGENCY": 0.04, "EQUITY": 0.20}
ASSETS = [{"type": "UST", "mv": 10_000_000}, {"type": "EQUITY", "mv": 2_000_000}, {"type": "CORP", "mv": 1_000_000}]

def haircut_value(market_value: float, haircut_frac: float) -> float:
    """Market value after applying a haircut given as a fraction (0.02 = 2%)."""
    return market_value * (1 - haircut_frac)

def pool_value(assets: list[dict], schedule: dict[str, float]) -> float:
    """Post-haircut value of eligible assets; types missing from the schedule count as 0."""
    total = 0.0
    for asset in assets:
        haircut = schedule.get(asset["type"])
        if haircut is None:
            continue
        total += haircut_value(asset["mv"], haircut)
    return total

print(pool_value(ASSETS, SCHEDULE))
''', [("haircut_value", r'''assert _close(haircut_value(1_000_000, 0.02), 980_000), f"got {haircut_value(1_000_000, 0.02)}"'''),
("pool_value", r'''
S = {"CASH": 0.0, "UST": 0.02, "EQUITY": 0.20}
A = [{"type": "UST", "mv": 10_000_000}, {"type": "EQUITY", "mv": 2_000_000}, {"type": "CORP", "mv": 1_000_000}, {"type": "CASH", "mv": 500}]
assert _close(pool_value(A, S), 11_400_500), f"got {pool_value(A, S)}"
'''), ("type hints & docstrings", r'''
import inspect
for fn in (haircut_value, pool_value):
    ann = fn.__annotations__
    assert "return" in ann and len(ann) >= 3, f"{fn.__name__} needs type hints on all parameters and the return value"
    assert inspect.getdoc(fn), f"{fn.__name__} needs a docstring"
''')], hints=["def haircut_value(market_value: float, haircut_frac: float) -> float:", 'First line inside the function: """One-line description."""'],
wrong=r'''
def haircut_value(market_value, haircut_frac):
    return market_value * (1 - haircut_frac)
def pool_value(assets, schedule):
    return sum(haircut_value(a["mv"], schedule.get(a["type"], 0)) for a in assets)
'''),
ex("Early returns", r'''
Rewrite `status` as `margin_flag(equity: float, requirement: float, mta: float = 10_000) -> str` using **early returns** (no nested ifs). Same outputs:
`"NO_REQ"` if requirement is 0, `"CALL"` if shortfall ≥ mta, `"SMALL_SHORT"` if 0 < shortfall < mta, else `"OK"`.
''', r'''
def status(e, r, m=10000):
    if r != 0:
        if r - e > 0:
            if r - e >= m:
                return "CALL"
            else:
                return "SMALL_SHORT"
        else:
            return "OK"
    else:
        return "NO_REQ"

def margin_flag(equity: float, requirement: float, mta: float = 10_000) -> str:
    ...
''', r'''
def margin_flag(equity: float, requirement: float, mta: float = 10_000) -> str:
    """Classify an account's margin position vs its requirement."""
    if requirement == 0:
        return "NO_REQ"
    shortfall = requirement - equity
    if shortfall >= mta:
        return "CALL"
    if shortfall > 0:
        return "SMALL_SHORT"
    return "OK"
''', [("cases", r'''
cases = [((0, 0), "NO_REQ"), ((5, 0), "NO_REQ"), ((80_000, 100_000), "CALL"), ((95_000, 100_000), "SMALL_SHORT"), ((100_000, 100_000), "OK"), ((90_000, 100_000), "CALL")]
for (e, r), exp in cases:
    got = margin_flag(e, r)
    assert got == exp, f"margin_flag({e}, {r}) = {got!r}; expected {exp!r}"
'''), ("custom mta", r'''assert margin_flag(95_000, 100_000, mta=5_000) == "CALL"''')],
hints=["Handle requirement == 0 first and return.", "Compute shortfall once, then two ifs and a final return."],
wrong=r'''
def margin_flag(equity, requirement, mta=10_000):
    shortfall = requirement - equity
    if shortfall > mta: return "CALL"
    if shortfall > 0: return "SMALL_SHORT"
    if requirement == 0: return "NO_REQ"
    return "OK"
'''),
])

lesson("u2l8", "Testing: prove your margin math before anyone relies on it",
"Write tests that catch the sign flips and missing multipliers that cause real breaks.",
r'''
A test calls your function with known inputs and **asserts** the expected output.

```python
def vm(prev_settle, settle, qty, multiplier):
    return (settle - prev_settle) * qty * multiplier

def test_long_gains_when_price_rises():
    assert vm(100.0, 101.0, 2, 1000) == 2000

def test_short_loses_when_price_rises():
    assert vm(100.0, 101.0, -2, 1000) == -2000
```

At work you'd put these in `test_margin.py` and run `pytest` — it finds every `test_*` function and reports failures. Here, the checker plays pytest.

What to test:
- the **happy path** (a normal case)
- **signs** (long vs short, pay vs collect)
- **edge cases**: zero, empty input, exactly-at-threshold, missing keys
- **units** (multiplier, bps vs fraction, ACT/360)

Floats: compare with tolerance — `math.isclose(a, b)` or `pytest.approx(b)` — never `==` for computed decimals like 0.1 + 0.2.

Arrange → Act → Assert. One behavior per test; name it after the behavior.
''',
examples=[("A mini test runner", r'''
import math
def vm(prev_settle, settle, qty, multiplier):
    return (settle - prev_settle) * qty * multiplier

def test_long():  assert vm(100.0, 101.0, 2, 1000) == 2000
def test_short(): assert vm(100.0, 101.0, -2, 1000) == -2000
def test_float(): assert math.isclose(vm(0.1, 0.3, 1, 1), 0.2)

for t in [test_long, test_short, test_float]:
    try:
        t(); print("PASS", t.__name__)
    except AssertionError:
        print("FAIL", t.__name__)
''')],
quiz=[q("`0.1 + 0.2 == 0.3` evaluates to…", ["True", "False", "Error", "Depends on the OS"], 1, "Binary floating point: 0.1 + 0.2 = 0.30000000000000004. Use math.isclose in tests.")],
exercises=[
ex("Write tests that catch bugs", r'''
Write **at least 3** `test_...` functions for `vm(prev_settle, settle, qty, multiplier)`.
The checker runs your tests against the correct `vm` (all must pass) and against **three buggy versions** — your tests must catch each one (sign flip, ignored multiplier, ignored quantity).
''', r'''
def vm(prev_settle, settle, qty, multiplier):
    """Variation margin: + means the account receives cash."""
    return (settle - prev_settle) * qty * multiplier

def test_long_gains():
    assert vm(100.0, 101.0, 1, 1) == 1.0   # improve me!
''', r'''
def vm(prev_settle, settle, qty, multiplier):
    """Variation margin: + means the account receives cash."""
    return (settle - prev_settle) * qty * multiplier

def test_long_gains():
    assert vm(100.0, 101.0, 2, 1000) == 2000

def test_short_loses_when_price_rises():
    assert vm(100.0, 101.0, -2, 1000) == -2000

def test_no_move_no_vm():
    assert vm(100.0, 100.0, 5, 1000) == 0
''', [("your tests pass on correct vm", r'''
tests = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
assert len(tests) >= 3, f"Found {len(tests)} test_ functions; write at least 3"
_good = lambda p, s, q, m: (s - p) * q * m
globals()["vm"] = _good
for t in tests:
    try:
        t()
    except AssertionError:
        raise AssertionError(f"{t.__name__} fails against the CORRECT vm — check your expected value")
'''), ("catch: sign flipped", r'''
tests = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
globals()["vm"] = lambda p, s, q, m: (p - s) * q * m
caught = False
for t in tests:
    try: t()
    except Exception: caught = True
globals()["vm"] = lambda p, s, q, m: (s - p) * q * m
assert caught, "None of your tests failed when vm had its sign flipped. Test that a long gains when price rises (non-zero move)."
'''), ("catch: multiplier ignored", r'''
tests = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
globals()["vm"] = lambda p, s, q, m: (s - p) * q
caught = False
for t in tests:
    try: t()
    except Exception: caught = True
globals()["vm"] = lambda p, s, q, m: (s - p) * q * m
assert caught, "Your tests didn't catch a vm that ignores the multiplier. Use a multiplier other than 1 (e.g. 1000)."
'''), ("catch: qty ignored", r'''
tests = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
globals()["vm"] = lambda p, s, q, m: (s - p) * m
caught = False
for t in tests:
    try: t()
    except Exception: caught = True
globals()["vm"] = lambda p, s, q, m: (s - p) * q * m
assert caught, "Your tests didn't catch a vm that ignores quantity. Use qty other than 1, and test a short (negative qty)."
''')], hints=["Use realistic numbers: qty=2, multiplier=1000.", "Include a short position (negative qty)."],
wrong=r'''
def vm(prev_settle, settle, qty, multiplier):
    return (settle - prev_settle) * qty * multiplier
def test_a(): assert vm(100.0, 101.0, 1, 1) == 1.0
def test_b(): assert vm(100.0, 100.0, 1, 1) == 0
def test_c(): assert vm(5.0, 6.0, 1, 1) > 0
'''),
ex("Find and fix the bug", r'''
`avg_price(fills)` should return the **quantity-weighted** average fill price. The provided tests fail. Fix the function (keep the name and signature). Fills are `(qty, price)`; qty is always positive.
''', r'''
def avg_price(fills):
    total = 0
    for qty, price in fills:
        total += price
    return total / len(fills)

def test_weighted():
    assert abs(avg_price([(100, 10.0), (300, 11.0)]) - 10.75) < 1e-9

def test_empty():
    assert avg_price([]) is None
''', r'''
def avg_price(fills):
    total_qty = sum(q for q, _ in fills)
    if total_qty == 0:
        return None
    return sum(q * p for q, p in fills) / total_qty

def test_weighted():
    assert abs(avg_price([(100, 10.0), (300, 11.0)]) - 10.75) < 1e-9

def test_empty():
    assert avg_price([]) is None
''', [("weighted average", r'''
r = avg_price([(100, 10.0), (300, 11.0)])
assert r is not None and abs(r - 10.75) < 1e-9, f"got {r}; expected 10.75 = (100×10 + 300×11) / 400" + (" — you're averaging prices, not weighting by qty" if r == 10.5 else "")
'''), ("empty input", r'''
try:
    r = avg_price([])
except ZeroDivisionError:
    raise AssertionError("avg_price([]) crashed with ZeroDivisionError — return None for no fills")
assert r is None, f"avg_price([]) = {r!r}; expected None"
'''), ("hidden case", r'''assert abs(avg_price([(1, 100.0), (1, 102.0), (2, 101.0)]) - 101.0) < 1e-9''')],
hints=["Weighted avg = Σ(qty × price) / Σ qty", "Check for zero total quantity first."],
wrong=r'''
def avg_price(fills):
    if not fills:
        return None
    return sum(p for _, p in fills) / len(fills)
'''),
])

lesson("u2l9", "Take it to work: position recon vs the clearing statement",
"Reconcile the internal position book against the CCP/clearing broker statement and produce a breaks report.",
r'''
Position reconciliation is daily bread at any FCM or prime broker: your books vs the clearing house (or executing broker) statement. Breaks come from late trades, give-ups not yet accepted, wrong account allocations, and fat-fingered quantities.

Plan (say this out loud in an interview):
1. **Normalize** both sides into `{(account, symbol): qty}`.
2. **Union of keys** — a position on only one side is a break too.
3. **Classify**: `MISSING_INTERNAL`, `MISSING_CLEARING`, or `QTY_BREAK`.
4. **Sort** so the biggest problems are first (by |diff|, then key for stable output).
5. **Report** a short summary line + the table.

Edge cases: zero positions (treat missing == 0), duplicate rows (sum them), case/whitespace in account IDs.
''',
examples=[("Union of keys", r'''
a = {("HF-A", "ES"): 10, ("HF-B", "CL"): -5}
b = {("HF-A", "ES"): 10, ("HF-C", "ZN"): 20}
for k in sorted(a.keys() | b.keys()):
    print(k, a.get(k, 0), b.get(k, 0))
''')],
quiz=[q("Internal shows HF-B CL −5; clearing has no HF-B CL row. Classification?", ["QTY_BREAK", "MISSING_CLEARING", "MISSING_INTERNAL", "Not a break"], 1, "We have it, clearing doesn't → it's missing at clearing (e.g. a give-up not yet accepted).")],
exercises=[
ex("to_book(rows)", r'''
Write `to_book(rows)` turning a list of `(account, symbol, qty)` into `{(ACCOUNT, SYMBOL): qty}` — **upper-case & strip** account and symbol, and **sum** duplicates.
''', r'''
def to_book(rows):
    ...

print(to_book([(" hf-a", "es", 10), ("HF-A", "ES ", -3), ("HF-B", "CL", 5)]))
''', r'''
def to_book(rows):
    book = {}
    for acct, sym, qty in rows:
        key = (acct.strip().upper(), sym.strip().upper())
        book[key] = book.get(key, 0) + qty
    return book

print(to_book([(" hf-a", "es", 10), ("HF-A", "ES ", -3), ("HF-B", "CL", 5)]))
''', [("normalized & summed", r'''
r = to_book([(" hf-a", "es", 10), ("HF-A", "ES ", -3), ("HF-B", "CL", 5)])
assert r == {("HF-A", "ES"): 7, ("HF-B", "CL"): 5}, f"got {r}"
''')], hints=["key = (acct.strip().upper(), sym.strip().upper())"],
wrong=r'''
def to_book(rows):
    return {(a.upper(), s.upper()): q for a, s, q in rows}
'''),
ex("breaks(internal, clearing)", r'''
Write `breaks(internal, clearing)` taking two books and returning a list of dicts
`{"account", "symbol", "internal", "clearing", "diff", "type"}` for every mismatch, where `diff = internal − clearing`, missing = 0, and `type` is `MISSING_CLEARING` (clearing is 0), `MISSING_INTERNAL` (internal is 0) or `QTY_BREAK`.
Sort by `abs(diff)` descending, then account, then symbol.
''', r'''
def breaks(internal, clearing):
    out = []
    ...
    return out

internal = {("HF-A", "ES"): 10, ("HF-A", "NQ"): -4, ("HF-B", "CL"): -5, ("HF-C", "ZN"): 20}
clearing = {("HF-A", "ES"): 10, ("HF-A", "NQ"): -2, ("HF-C", "ZN"): 20, ("HF-D", "GC"): 3}
for b in breaks(internal, clearing):
    print(b)
''', r'''
def breaks(internal, clearing):
    out = []
    for key in internal.keys() | clearing.keys():
        i, c = internal.get(key, 0), clearing.get(key, 0)
        if i == c:
            continue
        kind = "MISSING_CLEARING" if c == 0 else ("MISSING_INTERNAL" if i == 0 else "QTY_BREAK")
        out.append({"account": key[0], "symbol": key[1], "internal": i, "clearing": c, "diff": i - c, "type": kind})
    out.sort(key=lambda b: (-abs(b["diff"]), b["account"], b["symbol"]))
    return out

internal = {("HF-A", "ES"): 10, ("HF-A", "NQ"): -4, ("HF-B", "CL"): -5, ("HF-C", "ZN"): 20}
clearing = {("HF-A", "ES"): 10, ("HF-A", "NQ"): -2, ("HF-C", "ZN"): 20, ("HF-D", "GC"): 3}
for b in breaks(internal, clearing):
    print(b)
''', [("finds all breaks", r'''
internal = {("HF-A", "ES"): 10, ("HF-A", "NQ"): -4, ("HF-B", "CL"): -5, ("HF-C", "ZN"): 20}
clearing = {("HF-A", "ES"): 10, ("HF-A", "NQ"): -2, ("HF-C", "ZN"): 20, ("HF-D", "GC"): 3}
r = breaks(internal, clearing)
keys = [(b["account"], b["symbol"]) for b in r]
assert set(keys) == {("HF-A", "NQ"), ("HF-B", "CL"), ("HF-D", "GC")}, f"found {keys}" + (" — HF-D GC exists only at clearing; iterate over the UNION of keys" if ("HF-D", "GC") not in keys else "")
'''), ("types & diffs", r'''
internal = {("HF-A", "NQ"): -4, ("HF-B", "CL"): -5}
clearing = {("HF-A", "NQ"): -2, ("HF-D", "GC"): 3}
r = {(b["account"], b["symbol"]): b for b in breaks(internal, clearing)}
assert r[("HF-B", "CL")]["type"] == "MISSING_CLEARING" and r[("HF-B", "CL")]["diff"] == -5, f"HF-B CL: {r[('HF-B','CL')]}"
assert r[("HF-D", "GC")]["type"] == "MISSING_INTERNAL" and r[("HF-D", "GC")]["diff"] == -3, f"HF-D GC: {r[('HF-D','GC')]}"
assert r[("HF-A", "NQ")]["type"] == "QTY_BREAK" and r[("HF-A", "NQ")]["diff"] == -2, f"HF-A NQ: {r[('HF-A','NQ')]}"
'''), ("sorted by size", r'''
internal = {("HF-A", "NQ"): -4, ("HF-B", "CL"): -5}
clearing = {("HF-A", "NQ"): -2, ("HF-D", "GC"): 3}
order = [b["account"] for b in breaks(internal, clearing)]
assert order == ["HF-B", "HF-D", "HF-A"], f"order = {order}; sort by abs(diff) desc (5, 3, 2)"
''')], hints=["for key in internal.keys() | clearing.keys():", "out.sort(key=lambda b: (-abs(b['diff']), b['account'], b['symbol']))"],
wrong=r'''
def breaks(internal, clearing):
    out = []
    for key, i in internal.items():
        c = clearing.get(key, 0)
        if i != c:
            out.append({"account": key[0], "symbol": key[1], "internal": i, "clearing": c, "diff": i - c, "type": "QTY_BREAK"})
    return out
'''),
],
work=r'''
**Take it to work — Daily position recon**
- Load your internal positions extract and the clearing statement (CSV/Excel) with `csv` or pandas; build both books with `to_book`.
- Run `breaks()`; write the result to `breaks_YYYYMMDD.csv` and print a one-line summary (`3 breaks, largest HF-B CL −5`).
- Add a tolerance map for products where fractional/lot differences are expected.
- Stretch: persist yesterday's breaks and flag **aged** breaks (open > 1 day) — that's what ops managers and auditors ask for.
''')
