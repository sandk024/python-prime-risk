from dsl import *

CP_BODY = r'''
**Checkpoint.** Answer the questions without running code first (predict, then verify in a scratch example if unsure), then solve the mixed exercises. They combine several lessons from this unit, the way real desk tasks do.

Aim for all questions correct and both exercises passing without hints. Anything you miss goes into your daily **Review** queue.
'''

checkpoint("u1", "u1cp", "Checkpoint: Python foundations",
"Confirm you can read and write the everyday Python a risk analyst uses: numbers, strings, lists, dicts, functions and comprehensions.",
CP_BODY,
quiz=[
q("What does this print?", ["3 1 8", "3.5 1 8", "3 1 6", "4 1 8"], 0, "`//` is floor division, `%` is remainder, `**` is power.", code="print(7 // 2, 7 % 2, 2 ** 3)"),
q("What does this print?", ["1234567.89", "1,234,567.89", "1,234,567.891", "$1,234,567.89"], 1, "`,` adds thousands separators and `.2f` rounds to 2 decimals.", code='print(f"{1234567.891:,.2f}")'),
q("What is the result?", ["KeyError", "5", "0", "None"], 1, "`.get(key, default)` returns the default for a missing key, so 0 + 5.", code='positions = {"ES": 5}\npositions.get("NQ", 0) + positions["ES"]'),
q("What is the result?", ["[0, 2, 4]", "[0, 4, 8]", "[2, 6]", "[0, 4, 8, 12]"], 1, "Keep even x (0, 2, 4), then double them.", code="[x * 2 for x in range(5) if x % 2 == 0]"),
q("What is the result?", ["'ES'", "'CL'", "('CL', 5)", "5"], 1, "Sorted by descending quantity, the first tuple is ('CL', 5); [0] takes the symbol.", code='sorted([("ES", 3), ("CL", 5)], key=lambda t: -t[1])[0][0]'),
q("What is the result?", ["('ES', 'Z6')", "('ESZ', '6')", "('ES', '6')", "('E', 'Z6')"], 0, "`s[:2]` is the first two characters, `s[-2:]` the last two.", code='s = "ESZ6"\n(s[:2], s[-2:])'),
],
exercises=[
ex("Net positions from a messy blotter", r'''
Write `net_by_symbol(trades)` where each trade is `(symbol, side, qty)`. Symbols may have stray spaces and lower case; side is `"B"` or `"S"` (any case). Return a dict of **upper-case symbol -> net qty** (buys positive, sells negative), **dropping symbols that net to 0**.
''', r'''
def net_by_symbol(trades):
    ...

T = [("es", "B", 10), (" ES", "s", 4), ("CL ", "S", 3), ("nq", "b", 2), ("NQ", "S", 2)]
print(net_by_symbol(T))
''', r'''
def net_by_symbol(trades):
    net = {}
    for sym, side, qty in trades:
        s = sym.strip().upper()
        signed = qty if side.upper() == "B" else -qty
        net[s] = net.get(s, 0) + signed
    return {s: q for s, q in net.items() if q != 0}

T = [("es", "B", 10), (" ES", "s", 4), ("CL ", "S", 3), ("nq", "b", 2), ("NQ", "S", 2)]
print(net_by_symbol(T))
''', [("example", r'''
r = net_by_symbol([("es", "B", 10), (" ES", "s", 4), ("CL ", "S", 3), ("nq", "b", 2), ("NQ", "S", 2)])
assert r == {"ES": 6, "CL": -3}, f"got {r}" + (": drop symbols that net to 0" if "NQ" in r else "")
'''), ("empty", r'''assert net_by_symbol([]) == {}''')],
hints=["Normalize with .strip().upper() on both symbol and side.", "Filter at the end with a dict comprehension."],
wrong=r'''
def net_by_symbol(trades):
    net = {}
    for sym, side, qty in trades:
        net[sym.upper()] = net.get(sym.upper(), 0) + (qty if side == "B" else -qty)
    return net
''', difficulty=2),
ex("Margin calls, sorted", r'''
Write `margin_calls(accounts)` where each account is a dict with `id`, `equity`, `maintenance`, `initial`. An account whose equity is **below maintenance** gets a call back to **initial**: `initial - equity`. Return a list of `(id, call)` sorted by call descending (ties by id).
''', r'''
def margin_calls(accounts):
    ...

ACCTS = [
    {"id": "A1", "equity": 900_000, "maintenance": 1_000_000, "initial": 1_100_000},
    {"id": "B2", "equity": 1_050_000, "maintenance": 1_000_000, "initial": 1_100_000},
    {"id": "C3", "equity": 400_000, "maintenance": 500_000, "initial": 550_000},
    {"id": "D4", "equity": 2_000_000, "maintenance": 2_500_000, "initial": 2_750_000},
]
print(margin_calls(ACCTS))
''', r'''
def margin_calls(accounts):
    calls = [(a["id"], a["initial"] - a["equity"]) for a in accounts if a["equity"] < a["maintenance"]]
    return sorted(calls, key=lambda t: (-t[1], t[0]))

ACCTS = [
    {"id": "A1", "equity": 900_000, "maintenance": 1_000_000, "initial": 1_100_000},
    {"id": "B2", "equity": 1_050_000, "maintenance": 1_000_000, "initial": 1_100_000},
    {"id": "C3", "equity": 400_000, "maintenance": 500_000, "initial": 550_000},
    {"id": "D4", "equity": 2_000_000, "maintenance": 2_500_000, "initial": 2_750_000},
]
print(margin_calls(ACCTS))
''', [("example", r'''
r = margin_calls(ACCTS)
assert r == [("D4", 750_000), ("A1", 200_000), ("C3", 150_000)], f"got {r}" + (": B2 is above maintenance, so no call" if any(i == "B2" for i, _ in r) else "")
'''), ("ties by id", r'''
r = margin_calls([{"id": "Z", "equity": 0, "maintenance": 1, "initial": 5}, {"id": "A", "equity": 0, "maintenance": 1, "initial": 5}])
assert r == [("A", 5), ("Z", 5)], f"got {r}"
''')],
hints=["Filter with equity < maintenance; the call goes back to initial.", "sorted(..., key=lambda t: (-t[1], t[0]))"],
wrong=r'''
def margin_calls(accounts):
    return sorted([(a["id"], a["maintenance"] - a["equity"]) for a in accounts if a["equity"] < a["maintenance"]], key=lambda t: -t[1])
''', difficulty=3),
])

checkpoint("u2", "u2cp", "Checkpoint: Python fluency",
"Big-O, functions, errors, files, dates, classes, typing and tests: the fundamentals interviewers probe.",
CP_BODY,
quiz=[
q("Checking `x in collection` 1 million times against 100k ids. Which is fastest?", ["list", "tuple", "set", "string"], 2, "Set membership is O(1) on average; list/tuple is O(n)."),
q("What does this print?", ["[2]", "[1, 2]", "[]", "Error"], 1, "Default arguments are evaluated once, so the same list is reused. Use `acc=None`.", code="def add(x, acc=[]):\n    acc.append(x)\n    return acc\nadd(1)\nprint(add(2))"),
q("What prints?", ["bad, done", "ok, done", "ok", "done"], 1, "No exception, so `else` runs, then `finally` always runs.", code='try:\n    x = int("12")\nexcept ValueError:\n    print("bad")\nelse:\n    print("ok")\nfinally:\n    print("done")'),
q("What happens?", ["qty becomes 5", "FrozenInstanceError", "A new Trade is created", "Nothing"], 1, "`frozen=True` dataclasses are immutable; use `dataclasses.replace(t, qty=5)`.", code="from dataclasses import dataclass\n@dataclass(frozen=True)\nclass Trade:\n    qty: int\nt = Trade(1)\nt.qty = 5"),
q("What is `date(2026, 9, 30).weekday()`? (Sep 30, 2026 is a Wednesday)", ["2", "3", "4", "1"], 0, "Monday is 0, so Wednesday is 2. `isoweekday()` would give 3."),
q("Best way to catch a bug where `net_exposure` ignores short positions?", ["print statements", "A unit test with a short position and a known expected result", "Type hints", "A longer docstring"], 1, "Tests with targeted edge cases catch logic bugs; type hints don't."),
],
exercises=[
ex("Parse confirms with error reporting", r'''
Write `parse_confirms(text)` for CSV text with header `trade_id,symbol,qty,price`. Return `(trades, errors)`:
- `trades`: list of `Trade` dataclass objects (`trade_id: str, symbol: str, qty: int, price: float`)
- `errors`: list of strings `"line N: <reason>"` for rows that fail (N counts the header as line 1). Reasons: `"bad qty"` if qty isn't an int, `"bad price"` if price isn't a positive float.
''', r'''
import csv, io
from dataclasses import dataclass

@dataclass
class Trade:
    trade_id: str
    symbol: str
    qty: int
    price: float

def parse_confirms(text):
    ...

TEXT = """trade_id,symbol,qty,price
T1,ES,10,5790.25
T2,CL,ten,72.1
T3,ZN,-50,110.5
T4,NQ,3,-1
"""
trades, errors = parse_confirms(TEXT)
print(trades, errors)
''', r'''
import csv, io
from dataclasses import dataclass

@dataclass
class Trade:
    trade_id: str
    symbol: str
    qty: int
    price: float

def parse_confirms(text):
    trades, errors = [], []
    for n, row in enumerate(csv.DictReader(io.StringIO(text)), start=2):
        try:
            qty = int(row["qty"])
        except ValueError:
            errors.append(f"line {n}: bad qty")
            continue
        try:
            price = float(row["price"])
            if price <= 0:
                raise ValueError
        except ValueError:
            errors.append(f"line {n}: bad price")
            continue
        trades.append(Trade(row["trade_id"], row["symbol"], qty, price))
    return trades, errors

TEXT = """trade_id,symbol,qty,price
T1,ES,10,5790.25
T2,CL,ten,72.1
T3,ZN,-50,110.5
T4,NQ,3,-1
"""
trades, errors = parse_confirms(TEXT)
print(trades, errors)
''', [("trades", r'''
tr, er = parse_confirms(TEXT)
assert tr == [Trade("T1", "ES", 10, 5790.25), Trade("T3", "ZN", -50, 110.5)], f"trades = {tr}"
'''), ("errors", r'''
tr, er = parse_confirms(TEXT)
assert er == ["line 3: bad qty", "line 5: bad price"], f"errors = {er} (header is line 1)"
''')],
hints=["enumerate(csv.DictReader(...), start=2)", "Separate try/except blocks give separate reasons; `continue` skips the bad row."],
wrong=r'''
import csv, io
from dataclasses import dataclass
@dataclass
class Trade:
    trade_id: str
    symbol: str
    qty: int
    price: float
def parse_confirms(text):
    trades, errors = [], []
    for n, row in enumerate(csv.DictReader(io.StringIO(text)), start=1):
        try:
            trades.append(Trade(row["trade_id"], row["symbol"], int(row["qty"]), float(row["price"])))
        except ValueError:
            errors.append(f"line {n}: bad qty")
    return trades, errors
''', difficulty=2),
ex("Settlement date with holidays", r'''
Write `add_business_days(d, n, holidays)` returning the date `n` business days after `d`, skipping Saturdays, Sundays and any date in `holidays` (a set of `date`).
''', r'''
from datetime import date, timedelta

def add_business_days(d, n, holidays=frozenset()):
    ...

HOL = {date(2026, 11, 26), date(2026, 12, 25)}
print(add_business_days(date(2026, 11, 25), 2, HOL))
''', r'''
from datetime import date, timedelta

def add_business_days(d, n, holidays=frozenset()):
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5 and d not in holidays:
            n -= 1
    return d

HOL = {date(2026, 11, 26), date(2026, 12, 25)}
print(add_business_days(date(2026, 11, 25), 2, HOL))
''', [("Thanksgiving", r'''
r = add_business_days(date(2026, 11, 25), 2, {date(2026, 11, 26), date(2026, 12, 25)})
assert r == date(2026, 11, 30), f"got {r}: Wed + skip Thu holiday -> Fri (1), skip weekend -> Mon (2)"
'''), ("weekend", r'''assert add_business_days(date(2026, 10, 2), 1) == date(2026, 10, 5), "Friday + 1 business day = Monday"'''),
("zero", r'''assert add_business_days(date(2026, 10, 3), 0) == date(2026, 10, 3)''')],
hints=["Step one calendar day at a time; only count days that are weekdays and not holidays."],
wrong=r'''
from datetime import date, timedelta
def add_business_days(d, n, holidays=frozenset()):
    d = d + timedelta(days=n)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d
''', difficulty=2),
])

RECON_SETUP = r'''
import io
import pandas as pd
OURS = pd.read_csv(io.StringIO("""trade_id,account,symbol,qty
T1,A1,ES,10
T2,A1,CL,-5
T3,B2,ZN,200
T4,B2,ES,-3
"""))
STREET = pd.read_csv(io.StringIO("""trade_id,symbol,qty
T1,ES,10
T2,CL,-6
T4,ES,-3
T5,NQ,2
"""))
'''

POS_SETUP = r'''
import io
import pandas as pd
POS = pd.read_csv(io.StringIO("""account,symbol,notional
A1,ES,12000000
A1,CL,-3000000
A1,ZN,5000000
B2,ES,-8000000
B2,NQ,2000000
C3,GC,1000000
"""))
'''

checkpoint("u3", "u3cp", "Checkpoint: pandas & SQL-style thinking",
"Joins, group-bys, window functions and cleaning: the daily recon and reporting toolkit.",
CP_BODY,
quiz=[
q("`left` has 4 rows with unique keys. `right` has 3 rows, and key K (which appears once in `left`) appears twice in `right`. How many rows does `left.merge(right, on='key', how='left')` return?", ["4", "5", "3", "7"], 1, "A key duplicated on the right duplicates the matching left row: 4 + 1 = 5. Check `validate='one_to_one'` to catch this."),
q("SQL `SELECT account, SUM(notional) FROM pos GROUP BY account` in pandas?", ["pos.sum('account')", "pos.groupby('account')['notional'].sum()", "pos.pivot('account')", "pos.agg('account')"], 1, "groupby + column + aggregation."),
q("You need each row's share of its account's gross notional. Which method keeps the original row count?", ["agg", "transform", "apply with reset_index", "pivot_table"], 1, "`groupby(...).transform('sum')` broadcasts the group result back to every row."),
q("What is `pd.Series([1.0, None, 3.0]).sum()`?", ["NaN", "4.0", "Error", "None"], 1, "pandas skips NaN in sum by default (skipna=True). Know this when a missing mark silently shrinks a total."),
q("The SQL window `SUM(pnl) OVER (PARTITION BY desk ORDER BY date)` in pandas?", ["df.groupby('desk')['pnl'].cumsum() after sorting by date", "df['pnl'].rolling(3).sum()", "df.groupby('date')['pnl'].sum()", "df.pivot_table(values='pnl')"], 0, "Sort by the ORDER BY columns, then a grouped cumsum."),
q("`merge(..., indicator=True)` adds `_merge`. A row only in the right table has value?", ["'left_only'", "'right_only'", "'both'", "NaN"], 1, "Used for recon: left_only = missing at the street, right_only = missing in our books."),
],
exercises=[
ex("Trade recon breaks", r'''
Reconcile `OURS` vs `STREET` on `trade_id`. Return `breaks`: a DataFrame with columns `trade_id, issue` sorted by trade_id, where issue is `"missing at street"`, `"missing in ours"`, or `"qty mismatch"` (when both sides have the trade but qty differs).
''', RECON_SETUP + r'''
breaks = ...
print(breaks)
''', RECON_SETUP + r'''
m = OURS.merge(STREET, on="trade_id", how="outer", suffixes=("_ours", "_street"), indicator=True)
m["issue"] = None
m.loc[m["_merge"] == "left_only", "issue"] = "missing at street"
m.loc[m["_merge"] == "right_only", "issue"] = "missing in ours"
m.loc[(m["_merge"] == "both") & (m["qty_ours"] != m["qty_street"]), "issue"] = "qty mismatch"
breaks = m.loc[m["issue"].notna(), ["trade_id", "issue"]].sort_values("trade_id").reset_index(drop=True)
print(breaks)
''', [("breaks", r'''
got = list(breaks[["trade_id", "issue"]].itertuples(index=False, name=None))
exp = [("T2", "qty mismatch"), ("T3", "missing at street"), ("T5", "missing in ours")]
assert got == exp, f"got {got}"
'''), ("columns", r'''assert list(breaks.columns) == ["trade_id", "issue"], f"columns = {list(breaks.columns)}"''')],
hints=["merge(how='outer', indicator=True, suffixes=('_ours', '_street'))", "Use .loc with boolean masks to set the issue column."],
wrong=RECON_SETUP + r'''
m = OURS.merge(STREET, on="trade_id", how="inner", suffixes=("_ours", "_street"))
breaks = m.loc[m["qty_ours"] != m["qty_street"], ["trade_id"]].assign(issue="qty mismatch")
''', difficulty=2),
ex("Concentration: share of gross by account", r'''
Add a column `share` to a copy of `POS`: each row's **absolute** notional divided by its account's **gross** (sum of absolute notional). Then build `top`: a DataFrame with one row per account (the row with the largest share), columns `account, symbol, share`, sorted by share descending.
''', POS_SETUP + r'''
pos = POS.copy()
top = ...
print(top)
''', POS_SETUP + r'''
pos = POS.copy()
pos["gross"] = pos["notional"].abs()
pos["share"] = pos["gross"] / pos.groupby("account")["gross"].transform("sum")
top = (pos.sort_values("share", ascending=False)
          .drop_duplicates("account")[["account", "symbol", "share"]]
          .reset_index(drop=True))
print(top)
''', [("shares", r'''
assert "share" in pos.columns and _close(pos.loc[1, "share"], 0.15), f"A1 CL share should be 3m / 20m = 0.15; got {pos.loc[1, 'share'] if 'share' in pos.columns else 'missing'}"
'''), ("top", r'''
got = [(a, s, round(float(x), 4)) for a, s, x in top[["account", "symbol", "share"]].itertuples(index=False, name=None)]
assert got == [("C3", "GC", 1.0), ("B2", "ES", 0.8), ("A1", "ES", 0.6)], f"got {got}"
''')],
hints=["pos.groupby('account')['gross'].transform('sum') keeps the row count", "Sort by share descending, then drop_duplicates('account') keeps the top row per account"],
wrong=POS_SETUP + r'''
pos = POS.copy()
pos["share"] = pos["notional"] / pos.groupby("account")["notional"].transform("sum")
top = pos.sort_values("share", ascending=False).drop_duplicates("account")[["account", "symbol", "share"]]
''', difficulty=3),
])
