from dsl import *

unit("u1", "Python on a Trading Desk", "Use the basics from Python from Zero on real desk problems: notional and P&L, trade files, positions, margin rules. Each lesson adds a little new Python and explains it first.")

lesson("u1l1", "Notional & P&L: variables and numbers",
"Sanity-check a position's notional and a day's P&L before the morning risk call.",
r'''
> **New in this lesson** (everything else you met in Python from Zero)
>
> - **Desk words:** a **futures contract** is an agreement to buy or sell something (oil, a stock index) later at a price fixed today. The **multiplier** turns a price into dollars (1 ES contract = $50 per index point). **Notional** = price × multiplier × contracts: the total value controlled. **P&L** = profit and loss. **Long** = you bought; **short** = you sold, and you gain when the price falls.
> - **Two variables in one line:** `entry, exit_px = 71.40, 70.90` puts 71.40 in `entry` and 70.90 in `exit_px`.
> - **Format codes:** `{x:,.2f}` = thousands commas + 2 decimals (`5,850,250.00`).

You already know variables, `int`/`float` and arithmetic. Here's the desk version:

```python
price = 5850.25      # ES settlement
multiplier = 50      # $ per index point
contracts = 20
notional = price * multiplier * contracts
```

Reminder: `round(x, 2)` rounds; an f-string with a format code makes it readable: `f"{notional:,.2f}"` → `5,850,250.00`.

**Futures P&L** = (exit − entry) × contracts × multiplier. Short positions use a negative quantity, so the same formula works for both sides.

A **tick** is the smallest price step a contract can move. ES tick = 0.25 points = **$12.50** (0.25 × $50).

Heads-up: decimal numbers (floats) are stored approximately, so `0.1 + 0.2` shows `0.30000000000000004`. For money, round at the end when you report.
''',
examples=[("Notional of an ES position", r'''
price = 5850.25
multiplier = 50
contracts = 20
notional = price * multiplier * contracts
print(notional)
print(f"Notional: ${notional:,.2f}")
print("Per tick:", 0.25 * multiplier * contracts)
'''), ("Short P&L uses negative quantity", r'''
entry, exit_px = 71.40, 70.90   # crude oil, $/bbl
qty = -10                        # short 10 CL
pnl = (exit_px - entry) * qty * 1000
print(round(pnl, 2))             # positive: short made money
''')],
quiz=[q("What does this print?", ["3 1 8", "3.5 1 6", "3 0.5 8", "4 1 8"], 0,
        "`//` is floor division (7//2 = 3), `%` is the remainder (1), `**` is power (2³ = 8).",
        code=r'''print(7 // 2, 7 % 2, 2 ** 3)''')],
exercises=[
ex("Crude oil P&L", r'''
A client is **long 12 CL** (crude, 1,000 bbl per contract) bought at **71.40**. Today's settle is **72.15**.
Create a variable `pnl` with the dollar P&L.
''', r'''
entry = 71.40
settle = 72.15
contracts = 12
multiplier = 1000
pnl = ...  # your formula here
print(pnl)
''', r'''
entry = 71.40
settle = 72.15
contracts = 12
multiplier = 1000
pnl = (settle - entry) * contracts * multiplier
print(pnl)
''', [("pnl is correct", r'''
assert isinstance(pnl, (int, float)), "pnl should be a number — replace the ... with a formula"
assert not _close(pnl, 9.0), "You got 9.0 — you forgot the 1,000-barrel multiplier."
assert _close(pnl, 9000.0), f"pnl is {pnl}; expected 9000.0 = (72.15 - 71.40) × 12 × 1000"
''')], hints=["P&L = (settle − entry) × contracts × multiplier", "The price moved 0.75, so that's 0.75 × 12 × 1000."],
wrong=r'''
pnl = (72.15 - 71.40) * 12
'''),
ex("ES ticks on a short", r'''
A trader is **short 8 ES** from **5850.25** and covers at **5843.75**. ES tick = 0.25 points = $12.50.
Create `ticks` (number of ticks gained, positive) and `pnl_usd` (dollar P&L, positive = profit).
''', r'''
entry = 5850.25
exit_px = 5843.75
contracts = 8
tick_size = 0.25
tick_value = 12.50
ticks = ...
pnl_usd = ...
''', r'''
entry = 5850.25
exit_px = 5843.75
contracts = 8
tick_size = 0.25
tick_value = 12.50
ticks = (entry - exit_px) / tick_size
pnl_usd = ticks * tick_value * contracts
''', [("ticks", r'''
assert _close(ticks, 26), f"ticks = {ticks}; expected 26 = (5850.25 − 5843.75) / 0.25" + (" — sign is flipped: a short gains when price falls" if _close(ticks, -26) else "")
'''), ("pnl_usd", r'''
assert _close(pnl_usd, 2600), f"pnl_usd = {pnl_usd}; expected 2600 = 26 ticks × $12.50 × 8 contracts"
''')], hints=["For a short, gain = entry − exit.", "ticks × tick_value × contracts"],
wrong=r'''
ticks = (5843.75 - 5850.25) / 0.25
pnl_usd = ticks * 12.5 * 8
'''),
])

lesson("u1l2", "Strings: decode symbols, format a confirm",
"Decode futures symbols like ESZ6 from an exchange file and print a clean trade confirm.",
r'''
> **New in this lesson** (everything else you met in Python from Zero)
>
> - **Desk words:** a futures **symbol** like `ESZ6` packs three things: the root (`ES` = S&P 500 futures), a **month code** letter (`Z` = December) and the year digit (`6` = 2026).
> - **String indexing:** strings use positions like lists: `sym[0]` is the first character, `sym[-1]` the last.
> - **Slicing:** `sym[start:stop]` takes a piece, from `start` up to but not including `stop`. Leave one out to go to the edge: `sym[:-2]` = everything except the last 2 characters. Works on lists too: `lines[1:]` = all but the first.
> - **`.index(x)`:** the position where `x` first appears. **`.split(",")`:** cuts text at each comma and gives a list of pieces. Also **`.replace(a, b)`** and **`.startswith(x)`**.

Like lists, strings are **indexed** from 0, and negative indexes count from the end.

```python
sym = "ESZ6"
sym[0]     # 'E'
sym[-1]    # '6'  (year)
sym[-2]    # 'Z'  (month code)
sym[:-2]   # 'ES' (root) — slicing [start:stop]
```

Futures **month codes**: F G H J K M N Q U V X Z = Jan…Dec. So `"FGHJKMNQUVXZ".index("Z") + 1` → 12.

Plus the ones you know: `.upper()`, `.strip()`, and `int("25")`, `float("5850.25")`, `str(25)`: text from a file always needs converting before math.

Format codes: `{x:.2f}` two decimals, `{x:,}` thousands commas, `{s:>8}` right-align in 8 characters (handy for tidy columns).
''',
examples=[("Decode a symbol", r'''
sym = "ZCH7"
root, month, year = sym[:-2], sym[-2], sym[-1]
month_num = "FGHJKMNQUVXZ".index(month) + 1
print(root, month_num, "202" + year)
'''), ("Split a CSV line", r'''
line = "SELL, NQZ6 ,5,20410.50,ACCT-0107"
parts = []
for p in line.split(","):
    parts.append(p.strip())   # remove stray spaces around each piece
print(parts)
qty = int(parts[2])
print(qty * 2)
''')],
quiz=[q("What is `\"ZNH7\"[-2]`?", ["'7'", "'H'", "'ZN'", "'N'"], 1, "Index −1 is the last char ('7'), −2 is the one before it ('H' = March).")],
exercises=[
ex("Parse a trade line", r'''
Split `line` into variables: `side` (str), `symbol` (str), `qty` (**int**), `price` (**float**), `account` (str).
''', r'''
line = "BUY,ESZ6,25,5850.25,ACCT-0042"
parts = line.split(",")
side = parts[0]
symbol = ...
qty = ...
price = ...
account = ...
''', r'''
line = "BUY,ESZ6,25,5850.25,ACCT-0042"
parts = line.split(",")
side = parts[0]
symbol = parts[1]
qty = int(parts[2])
price = float(parts[3])
account = parts[4]
''', [("side & symbol", r'''
assert side == "BUY" and symbol == "ESZ6", f"side={side!r}, symbol={symbol!r}"
'''), ("qty is an int", r'''
assert isinstance(qty, int), f"qty is {type(qty).__name__} {qty!r} — wrap it in int(...) so you can do math with it"
assert qty == 25
'''), ("price is a float", r'''
assert isinstance(price, float), f"price is {type(price).__name__} — use float(...)"
assert _close(price, 5850.25)
'''), ("account", r'''
assert account == "ACCT-0042", f"account={account!r}"
''')], hints=["parts is a list: parts[0], parts[1], …", "Text '25' isn't a number until you call int('25')."],
wrong=r'''
line = "BUY,ESZ6,25,5850.25,ACCT-0042"
side, symbol, qty, price, account = line.split(",")
'''),
ex("Build a confirm string", r'''
Using the variables given, create `confirm` exactly like:
`BUY 25 ESZ6 (Dec) @ 5850.25 for ACCT-0042`
The month name must be derived from the symbol's month code using `months`.
''', r'''
side, symbol, qty, price, account = "BUY", "ESZ6", 25, 5850.25, "ACCT-0042"
codes = "FGHJKMNQUVXZ"
months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
month_name = ...
confirm = ...
print(confirm)
''', r'''
side, symbol, qty, price, account = "BUY", "ESZ6", 25, 5850.25, "ACCT-0042"
codes = "FGHJKMNQUVXZ"
months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
month_name = months[codes.index(symbol[-2])]
confirm = f"{side} {qty} {symbol} ({month_name}) @ {price:.2f} for {account}"
print(confirm)
''', [("month_name", r'''
assert month_name == "Dec", f"month_name = {month_name!r}; Z is the 12th code → months[11]. Remember lists start at 0."
'''), ("confirm text", r'''
exp = "BUY 25 ESZ6 (Dec) @ 5850.25 for ACCT-0042"
assert confirm == exp, f"Got:\n{confirm!r}\nExpected:\n{exp!r}"
''')], hints=["codes.index('Z') is 11 — the position in the string.", "Use an f-string with {price:.2f}."],
wrong=r'''
side, symbol, qty, price, account = "BUY", "ESZ6", 25, 5850.25, "ACCT-0042"
months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
month_name = months["FGHJKMNQUVXZ".index(symbol[-2]) + 1] if False else "Nov"
confirm = f"{side} {qty} {symbol} ({month_name}) @ {price} for {account}"
'''),
])

lesson("u1l3", "Lists & loops: a week of desk P&L",
"Summarize a desk's daily P&L series: total, worst day, loss days, and max drawdown.",
r'''
> **New in this lesson** (everything else you met in Python from Zero)
>
> - **`enumerate(items, start=1)`:** loop and get a counter too: `for day, p in enumerate(daily_pnl, start=1):` gives `day` = 1, 2, 3… alongside each value `p`.
> - **Desk word:** **drawdown** = how far cumulative P&L has fallen from its best point so far (explained below).

Recap: a **list** holds items in order: `pnl = [12500, -8300, 4100]`; `len`, `sum`, `min`, `max`, `.append(x)`.

A **for loop** runs its indented block once per item:

```python
total = 0
for p in pnl:
    total = total + p   # or: total += p
```

`enumerate(pnl, start=1)` gives a counter with each value; `range(5)` gives 0..4.

**Max drawdown** = the largest drop from a running peak of cumulative P&L — a core risk stat for any strategy or client:

```
cumulative:  12.5k → 4.2k → 8.3k → -6.9k
peak:        12.5k   12.5k  12.5k   12.5k
drawdown:     0      8.3k   4.2k   19.4k  ← max
```
''',
examples=[("Running total with enumerate", r'''
daily_pnl = [12500, -8300, 4100, -15200, 9700]
running = 0
for day, p in enumerate(daily_pnl, start=1):
    running += p
    print(f"Day {day}: {p:>8,}  cumulative {running:>8,}")
''')],
quiz=[q("What does this print?", ["4 5", "3 5", "4 2", "5 5"], 0, "append adds 5 at the end → 4 items; x[-1] is the last item.",
        code=r'''
x = [3, 1, 2]
x.append(5)
print(len(x), x[-1])
''')],
exercises=[
ex("Weekly P&L stats", r'''
Using a `for` loop (not `sum`/`min`), compute `total`, `worst_day` (most negative value) and `loss_days` (count of negative days).
''', r'''
daily_pnl = [12500, -8300, 4100, -15200, 9700, 2300, -4100]
total = 0
worst_day = daily_pnl[0]
loss_days = 0
for p in daily_pnl:
    ...
print(total, worst_day, loss_days)
''', r'''
daily_pnl = [12500, -8300, 4100, -15200, 9700, 2300, -4100]
total = 0
worst_day = daily_pnl[0]
loss_days = 0
for p in daily_pnl:
    total += p
    if p < worst_day:
        worst_day = p
    if p < 0:
        loss_days += 1
print(total, worst_day, loss_days)
''', [("total", r'''assert total == 1000, f"total = {total}; expected 1000"'''),
      ("worst_day", r'''assert worst_day == -15200, f"worst_day = {worst_day}; expected -15200 (the smallest number)"'''),
      ("loss_days", r'''assert loss_days == 3, f"loss_days = {loss_days}; expected 3 negative days"''')],
hints=["Inside the loop: total += p", "Use `if p < worst_day:` to update the minimum, `if p < 0:` to count losses."],
wrong=r'''
daily_pnl = [12500, -8300, 4100, -15200, 9700, 2300, -4100]
total = 0; worst_day = 0; loss_days = 0
for p in daily_pnl:
    total += p
    if p < 0:
        loss_days += 1
        worst_day = p
'''),
ex("Max drawdown", r'''
Compute `max_dd`: the largest peak-to-trough drop in **cumulative** P&L (a positive number). Start `peak` at 0.
''', r'''
daily_pnl = [12500, -8300, 4100, -15200, 9700, 2300, -4100]
cum = 0
peak = 0
max_dd = 0
for p in daily_pnl:
    cum += p
    # update peak, then drawdown
    ...
print(max_dd)
''', r'''
daily_pnl = [12500, -8300, 4100, -15200, 9700, 2300, -4100]
cum = 0
peak = 0
max_dd = 0
for p in daily_pnl:
    cum += p
    if cum > peak:
        peak = cum
    dd = peak - cum
    if dd > max_dd:
        max_dd = dd
print(max_dd)
''', [("max_dd", r'''
assert max_dd != 15200, "15,200 is just the worst single day. Drawdown is measured on the cumulative P&L from its running peak."
assert max_dd == 19400, f"max_dd = {max_dd}; expected 19400 (peak 12,500 → trough −6,900)"
''')], hints=["peak = max(peak, cum)", "drawdown today = peak − cum; keep the largest."],
wrong=r'''
daily_pnl = [12500, -8300, 4100, -15200, 9700, 2300, -4100]
max_dd = -min(daily_pnl)
'''),
])

lesson("u1l4", "Dicts: contract specs & net positions",
"Look up contract multipliers and net fills into positions — the core of every position file.",
r'''
> **New in this lesson** (everything else you met in Python from Zero)
>
> - **Tuple:** a fixed group of values in round brackets, `("ES", 25)`. Like a list, but it can't be changed after it's made.
> - **Unpacking in a loop:** `for sym, qty in fills:` takes each tuple and splits it into two variables.
> - **`abs(x)`:** the size of a number without its sign (`abs(-5)` is 5). **`d.values()`:** just the values of a dict, e.g. `sum(d.values())`.
> - **`del d[key]`** removes a pair.

Recap: a **dict** maps keys to values, perfect for lookups:

```python
multiplier = {"ES": 50, "NQ": 20, "CL": 1000, "ZN": 1000, "ZC": 50}
multiplier["CL"]           # 1000
multiplier.get("GC", 0)    # 0 — default instead of KeyError
multiplier["GC"] = 100     # add / update
"ES" in multiplier         # True
for sym, m in multiplier.items():
    print(sym, m)
```

(ZC corn is quoted in cents/bu: 5,000 bu × $0.01 = **$50 per cent**.)

A **tuple** is a fixed group: `("ES", 25)`. Unpack it: `sym, qty = ("ES", 25)`.

Netting pattern — the most common dict idiom in risk code:

```python
net = {}
for sym, qty in fills:
    net[sym] = net.get(sym, 0) + qty
```
''',
examples=[("Net a blotter", r'''
fills = [("ES", 10), ("NQ", -5), ("ES", -4), ("CL", 3), ("ES", 2)]
net = {}
for sym, qty in fills:
    net[sym] = net.get(sym, 0) + qty
print(net)
''')],
quiz=[q("What prints?", ["KeyError", "0", "None", "20"], 1, "`.get(key, default)` returns the default when the key is missing.",
        code=r'''
d = {"ES": 50}
print(d.get("NQ", 0))
''')],
exercises=[
ex("Net positions", r'''
Build dict `net` mapping symbol → net quantity from `fills`. Then **remove symbols whose net is 0** (flat positions shouldn't appear on the report).
''', r'''
fills = [("ES", 10), ("NQ", -5), ("ES", -4), ("CL", 3), ("ES", 2), ("CL", -3), ("ZN", -20)]
net = {}
...
print(net)
''', r'''
fills = [("ES", 10), ("NQ", -5), ("ES", -4), ("CL", 3), ("ES", 2), ("CL", -3), ("ZN", -20)]
net = {}
for sym, qty in fills:
    net[sym] = net.get(sym, 0) + qty
flat = []
for sym, qty in net.items():
    if qty == 0:
        flat.append(sym)       # remember which ones are flat
for sym in flat:
    del net[sym]               # then remove them
print(net)
''', [("values", r'''
assert net.get("ES") == 8 and net.get("NQ") == -5 and net.get("ZN") == -20, f"net = {net}"
'''), ("flat removed", r'''
assert "CL" not in net, "CL nets to 0 (bought 3, sold 3) — remove it."
''')], hints=["net[sym] = net.get(sym, 0) + qty", "Collect the flat symbols in a list, then `del net[sym]` each one (don't delete while looping over the same dict)."],
wrong=r'''
fills = [("ES", 10), ("NQ", -5), ("ES", -4), ("CL", 3), ("ES", 2), ("CL", -3), ("ZN", -20)]
net = {}
for sym, qty in fills:
    net[sym] = qty
'''),
ex("Gross notional by symbol", r'''
Create `notional` mapping symbol → **gross** notional = |qty| × price × multiplier, and `gross_total` = sum of all of them.
''', r'''
net = {"ES": 8, "NQ": -5, "ZN": -20}
price = {"ES": 5850.25, "NQ": 20410.50, "ZN": 110.515625}
multiplier = {"ES": 50, "NQ": 20, "ZN": 1000}
notional = {}
...
gross_total = ...
''', r'''
net = {"ES": 8, "NQ": -5, "ZN": -20}
price = {"ES": 5850.25, "NQ": 20410.50, "ZN": 110.515625}
multiplier = {"ES": 50, "NQ": 20, "ZN": 1000}
notional = {}
for sym, qty in net.items():
    notional[sym] = abs(qty) * price[sym] * multiplier[sym]
gross_total = sum(notional.values())
''', [("per symbol", r'''
assert _close(notional["ES"], 2340100.0), f"ES notional {notional.get('ES')}; expected 8 × 5850.25 × 50 = 2,340,100"
assert _close(notional["NQ"], 2041050.0), f"NQ notional {notional.get('NQ')} — gross notional uses abs(qty), so shorts are positive"
assert _close(notional["ZN"], 2210312.5)
'''), ("gross_total", r'''
assert _close(gross_total, 6591462.5), f"gross_total = {gross_total}; expected 6,591,462.50"
''')], hints=["Loop over net.items()", "abs(-5) is 5"],
wrong=r'''
net = {"ES": 8, "NQ": -5, "ZN": -20}
price = {"ES": 5850.25, "NQ": 20410.50, "ZN": 110.515625}
multiplier = {"ES": 50, "NQ": 20, "ZN": 1000}
notional = {s: q * price[s] * multiplier[s] for s, q in net.items()}
gross_total = sum(notional.values())
'''),
])

lesson("u1l5", "Conditionals & functions: the margin-call rule",
"Encode the desk's margin-call rule once, so it's applied identically every day.",
r'''
> **New in this lesson** (everything else you met in Python from Zero)
>
> - **Desk words:** **equity** = what an account is worth today; the **margin requirement** = the minimum the clearing broker needs it to hold. Below that, the client gets a **margin call** (a demand for more cash).
> - **Default values:** `def call_amount(equity, req, mta=10_000):` means `mta` is optional; if the caller leaves it out it's 10,000. (`10_000` is just 10000; underscores make big numbers readable.)
> - **`import math`** loads Python's math toolbox (a **module**); then `math.ceil(x)` rounds **up** to a whole number (`math.ceil(12.1)` is 13).
> - **One-line if/else:** `status = "OK" if u < 0.8 else "WARN"` is a compact `if/else` that produces a value.
> - **Docstring:** a `"""text"""` string on the first line of a function that explains what it does.
> - **Percent format:** `{u:.0%}` shows 0.85 as `85%`.

Recap: `if / elif / else` choose a branch; combine conditions with `and`, `or`, `not`.

Recap: a **function** packages logic with inputs (parameters) and an output (`return`):

```python
def notional(price, qty, multiplier):
    """Gross notional in USD."""
    return abs(qty) * price * multiplier

notional(5850.25, -8, 50)   # 2340100.0
```

`return` hands a value back to the caller; `print` only displays it. Functions without `return` give `None`.

**Default arguments** make parameters optional: `def call_amount(equity, req, mta=10_000)`.

Margin-call conventions you'll encode:
- **Minimum transfer amount (MTA)** — calls smaller than this aren't made.
- **Rounding** — call amounts are commonly rounded *up* to a round number (e.g. nearest $1,000). `math.ceil(x / 1000) * 1000`.
''',
examples=[("A status function", r'''
def utilization(used, limit):
    if limit <= 0:
        return None
    return used / limit

for used in [40, 85, 120]:
    u = utilization(used, 100)
    if u > 1:
        status = "BREACH"
    elif u >= 0.8:
        status = "WARN"
    else:
        status = "OK"
    print(used, f"{u:.0%}", status)
''')],
quiz=[q("A function ends with `print(x)` but no `return`. What does `y = f()` store in y?", ["x", "None", "An error", "The printed text"], 1, "Without `return`, a function returns `None`. Printing ≠ returning.")],
exercises=[
ex("margin_status()", r'''
Write `margin_status(equity, requirement)` returning:
- `"CALL"` if equity < requirement
- `"WARNING"` if equity < 110% of requirement
- `"OK"` otherwise
''', r'''
def margin_status(equity, requirement):
    ...

print(margin_status(950_000, 1_000_000))
''', r'''
def margin_status(equity, requirement):
    if equity < requirement:
        return "CALL"
    elif equity < 1.10 * requirement:
        return "WARNING"
    return "OK"

print(margin_status(950_000, 1_000_000))
''', [("CALL", r'''assert margin_status(950_000, 1_000_000) == "CALL", f"950k vs 1m req gave {margin_status(950_000, 1_000_000)!r}"'''),
      ("WARNING", r'''assert margin_status(1_050_000, 1_000_000) == "WARNING", f"1.05m vs 1m gave {margin_status(1_050_000, 1_000_000)!r}"'''),
      ("OK", r'''assert margin_status(2_000_000, 1_000_000) == "OK"'''),
      ("boundary: equity == requirement", r'''assert margin_status(1_000_000, 1_000_000) == "WARNING", "Exactly at requirement is not a call (not <), but it is under 110% → WARNING"''')],
hints=["Check the CALL condition first, then WARNING.", "Remember to `return` the string, not print it."],
wrong=r'''
def margin_status(equity, requirement):
    if equity <= requirement:
        return "CALL"
    if equity < 1.1 * requirement:
        return "WARNING"
    return "OK"
'''),
ex("call_amount() with MTA and rounding", r'''
Write `call_amount(equity, requirement, mta=10_000)`:
- shortfall = requirement − equity
- if shortfall ≤ 0 or shortfall < mta → return 0
- else return shortfall **rounded up** to the nearest 1,000
''', r'''
import math

def call_amount(equity, requirement, mta=10_000):
    ...
''', r'''
import math

def call_amount(equity, requirement, mta=10_000):
    shortfall = requirement - equity
    if shortfall <= 0 or shortfall < mta:
        return 0
    return math.ceil(shortfall / 1000) * 1000
''', [("simple call", r'''assert call_amount(950_000, 1_000_000) == 50_000'''),
      ("below MTA", r'''assert call_amount(995_000, 1_000_000) == 0, "5k shortfall is under the 10k MTA → no call"'''),
      ("surplus", r'''assert call_amount(1_200_000, 1_000_000) == 0, "Surplus → 0, not a negative call"'''),
      ("round up", r'''
r = call_amount(900_000, 912_345)
assert r == 13_000, f"shortfall 12,345 should round UP to 13,000; got {r}" + (" (use math.ceil, not round)" if r == 12_000 else "")
'''),
      ("custom mta", r'''assert call_amount(990_000, 1_000_000, mta=5_000) == 10_000''')],
hints=["math.ceil(12.345) is 13", "math.ceil(shortfall / 1000) * 1000"],
wrong=r'''
def call_amount(equity, requirement, mta=10_000):
    s = requirement - equity
    if s < mta:
        return 0
    return round(s, -3)
'''),
])

lesson("u1l6", "Comprehensions, sorting & zip",
"Filter a fill blotter and build lookup tables in one readable line each.",
r'''
> **New in this lesson** (everything else you met in Python from Zero)
>
> - **Comprehensions:** a one-line way to build a list, set or dict from a loop (explained right below).
> - **Set:** curly braces with single values, `{"A", "B"}`: an unordered collection with no duplicates.
> - **`lambda`:** a tiny unnamed function written inline: `lambda f: f["qty"]` does the same as `def get_qty(f): return f["qty"]`.
> - **`sorted(items, key=..., reverse=True)` / `max(items, key=...)`:** sort, or pick the biggest, by whatever `key` returns for each item.
> - **`zip(a, b)`:** walks two lists side by side; `dict(zip(keys, values))` pairs them into a dict.

A **list comprehension** builds a list from a loop in one line:

```python
big = [f["id"] for f in fills if f["qty"] >= 100]
```
Read it as: "f['id'] for each f in fills, if qty ≥ 100".

Also: **dict** comprehension `{k: v for ...}` and **set** comprehension `{x for ...}` (unique values).

**Sorting**: `sorted(items, key=..., reverse=True)`. The `key` is a function applied to each item — often a `lambda`:
```python
sorted(fills, key=lambda f: f["qty"], reverse=True)
```

`zip(a, b)` walks two lists together; `any(...)` / `all(...)` test conditions across items.

Use comprehensions for simple transforms; switch back to a normal loop when logic needs more than one `if`.
''',
examples=[("Blotter one-liners", r'''
fills = [
    {"id": "T1", "acct": "HF-ALPHA", "sym": "ES", "qty": 150, "px": 5850.25},
    {"id": "T2", "acct": "HF-BETA",  "sym": "NQ", "qty": 20,  "px": 20410.5},
    {"id": "T3", "acct": "HF-ALPHA", "sym": "CL", "qty": 300, "px": 71.40},
]
print([f["id"] for f in fills if f["qty"] >= 100])
print({f["acct"] for f in fills})
print(sorted(fills, key=lambda f: f["qty"], reverse=True)[0]["id"])
syms, pxs = ["ES", "NQ"], [5850.25, 20410.5]
print(dict(zip(syms, pxs)))
''')],
quiz=[q("What does `[x * 2 for x in range(4) if x % 2 == 1]` produce?", ["[2, 6]", "[0, 2, 4, 6]", "[1, 3]", "[2, 4, 6]"], 0, "range(4) = 0,1,2,3; odd ones are 1 and 3; doubled → [2, 6].")],
exercises=[
ex("Filter the blotter", r'''
Create:
- `big_fills`: list of trade ids with qty ≥ 100, in original order
- `accounts`: **sorted list** of unique account names
- `largest`: the id of the fill with the largest **notional** (qty × px × mult[sym])
''', r'''
mult = {"ES": 50, "NQ": 20, "CL": 1000}
fills = [
    {"id": "T1", "acct": "HF-ALPHA", "sym": "ES", "qty": 150, "px": 5850.25},
    {"id": "T2", "acct": "HF-BETA",  "sym": "NQ", "qty": 20,  "px": 20410.5},
    {"id": "T3", "acct": "HF-ALPHA", "sym": "CL", "qty": 300, "px": 71.40},
    {"id": "T4", "acct": "FO-GAMMA", "sym": "ES", "qty": 5,   "px": 5851.00},
    {"id": "T5", "acct": "HF-BETA",  "sym": "CL", "qty": 120, "px": 71.10},
]
big_fills = ...
accounts = ...
largest = ...
''', r'''
mult = {"ES": 50, "NQ": 20, "CL": 1000}
fills = [
    {"id": "T1", "acct": "HF-ALPHA", "sym": "ES", "qty": 150, "px": 5850.25},
    {"id": "T2", "acct": "HF-BETA",  "sym": "NQ", "qty": 20,  "px": 20410.5},
    {"id": "T3", "acct": "HF-ALPHA", "sym": "CL", "qty": 300, "px": 71.40},
    {"id": "T4", "acct": "FO-GAMMA", "sym": "ES", "qty": 5,   "px": 5851.00},
    {"id": "T5", "acct": "HF-BETA",  "sym": "CL", "qty": 120, "px": 71.10},
]
big_fills = [f["id"] for f in fills if f["qty"] >= 100]
accounts = sorted({f["acct"] for f in fills})
largest = max(fills, key=lambda f: f["qty"] * f["px"] * mult[f["sym"]])["id"]
''', [("big_fills", r'''assert big_fills == ["T1", "T3", "T5"], f"big_fills = {big_fills}"'''),
      ("accounts", r'''
assert isinstance(accounts, list), "accounts should be a list — wrap the set in sorted(...)"
assert accounts == ["FO-GAMMA", "HF-ALPHA", "HF-BETA"], f"accounts = {accounts}"
'''),
      ("largest", r'''
assert largest != "T3", "T3 has the biggest qty×px but CL notional is 300×71.40×1000 = 21.4m vs ES 150×5850.25×50 = 43.9m. Include the multiplier."
assert largest == "T1", f"largest = {largest!r}"
''')],
hints=["sorted() on a set returns a list.", "max(fills, key=lambda f: ...) returns the whole dict; take ['id']."],
wrong=r'''
mult = {"ES": 50, "NQ": 20, "CL": 1000}
fills = [
    {"id": "T1", "acct": "HF-ALPHA", "sym": "ES", "qty": 150, "px": 5850.25},
    {"id": "T2", "acct": "HF-BETA",  "sym": "NQ", "qty": 20,  "px": 20410.5},
    {"id": "T3", "acct": "HF-ALPHA", "sym": "CL", "qty": 300, "px": 71.40},
    {"id": "T4", "acct": "FO-GAMMA", "sym": "ES", "qty": 5,   "px": 5851.00},
    {"id": "T5", "acct": "HF-BETA",  "sym": "CL", "qty": 120, "px": 71.10},
]
big_fills = [f["id"] for f in fills if f["qty"] > 100]
accounts = {f["acct"] for f in fills}
largest = max(fills, key=lambda f: f["qty"] * f["px"])["id"]
'''),
ex("Lookup table with zip", r'''
Build `settle` = dict symbol → settlement price using `zip`, then `moves` = dict of symbol → price change (settle − prev) **only for symbols that moved more than 1%** in absolute terms.
''', r'''
symbols = ["ES", "NQ", "CL", "ZN", "GC"]
prev    = [5850.25, 20410.5, 71.40, 110.50, 2650.0]
today   = [5790.00, 20100.0, 73.10, 110.62, 2655.0]
settle = ...
prev_d = dict(zip(symbols, prev))
moves = ...
print(moves)
''', r'''
symbols = ["ES", "NQ", "CL", "ZN", "GC"]
prev    = [5850.25, 20410.5, 71.40, 110.50, 2650.0]
today   = [5790.00, 20100.0, 73.10, 110.62, 2655.0]
settle = dict(zip(symbols, today))
prev_d = dict(zip(symbols, prev))
moves = {s: settle[s] - prev_d[s] for s in symbols if abs(settle[s] / prev_d[s] - 1) > 0.01}
print(moves)
''', [("settle", r'''assert settle == {"ES": 5790.0, "NQ": 20100.0, "CL": 73.1, "ZN": 110.62, "GC": 2655.0}, f"settle = {settle}"'''),
      ("moves keys", r'''assert sorted(moves) == ["CL", "ES", "NQ"], f"moves keys = {sorted(moves)}; ES −1.03%, NQ −1.52%, CL +2.38% moved >1%"'''),
      ("moves values", r'''assert _close(moves["ES"], -60.25) and _close(moves["CL"], 1.7), f"moves = {moves}"''')],
hints=["dict(zip(keys, values))", "Percent move = settle/prev − 1; compare abs(...) > 0.01"],
wrong=r'''
symbols = ["ES", "NQ", "CL", "ZN", "GC"]
prev    = [5850.25, 20410.5, 71.40, 110.50, 2650.0]
today   = [5790.00, 20100.0, 73.10, 110.62, 2655.0]
settle = dict(zip(symbols, today))
prev_d = dict(zip(symbols, prev))
moves = {s: settle[s] - prev_d[s] for s in symbols if settle[s] / prev_d[s] - 1 > 0.01}
'''),
])

lesson("u1l7", "Take it to work: parse the daily trades file",
"Every morning, turn the overnight trade file into net positions per account and symbol, and flag bad rows.",
r'''
> **New in this lesson** (everything else you met in Python from Zero)
>
> - **Triple quotes** `"""..."""` make a string that spans several lines (like a small file pasted into the code).
> - **`text.splitlines()`:** cuts text into a list of lines.
> - **`continue`:** inside a loop, skip the rest of this round and go to the next item.
> - **Empty text counts as False:** `if not line.strip():` is True for a blank line.
> - **Tuple keys:** a dict key can be a tuple like `("HF-ALPHA", "ES")`, which lets you group by two things at once.

Real files are text: a header row, then comma-separated rows, sometimes with blank lines or junk. The pattern:

1. `text.strip().splitlines()` → list of lines
2. skip the header, skip blanks
3. `line.split(",")` and convert types
4. accumulate into a dict keyed by a **tuple** `(account, symbol)`

Tuples can be dict keys because they're immutable — that's how you do a "group by two columns" in plain Python.

We'll break it into two **small functions** — one parses, one aggregates. Small functions are easier to test and reuse (you'll swap the parser when the file format changes, without touching the aggregation).
''',
examples=[("Tuple keys", r'''
pos = {}
for acct, sym, q in [("A", "ES", 5), ("B", "ES", 2), ("A", "ES", -1)]:
    key = (acct, sym)
    pos[key] = pos.get(key, 0) + q
print(pos)
''')],
quiz=[q("Why can `(\"HF-A\", \"ES\")` be a dict key but `[\"HF-A\", \"ES\"]` can't?", ["Lists are too slow", "Tuples are immutable (hashable); lists can change", "Lists can't hold strings", "It can, both work"], 1, "Dict keys must be hashable, i.e. immutable. Tuples are; lists aren't.")],
exercises=[
ex("parse_trades(text)", r'''
Write `parse_trades(text)` returning a list of dicts with keys `account, side, symbol, qty (int), price (float)`.
Skip the header and blank lines.
''', r'''
TRADES = """account,side,symbol,qty,price
HF-ALPHA,BUY,ES,10,5850.25
HF-ALPHA,SELL,ES,4,5852.00

HF-BETA,SELL,CL,15,71.40
HF-ALPHA,BUY,ZN,20,110.50
HF-BETA,BUY,CL,15,71.10
FO-GAMMA,BUY,ES,3,5849.75
"""

def parse_trades(text):
    rows = []
    lines = text.strip().splitlines()
    for line in lines[1:]:
        ...
    return rows

print(parse_trades(TRADES)[:2])
''', r'''
TRADES = """account,side,symbol,qty,price
HF-ALPHA,BUY,ES,10,5850.25
HF-ALPHA,SELL,ES,4,5852.00

HF-BETA,SELL,CL,15,71.40
HF-ALPHA,BUY,ZN,20,110.50
HF-BETA,BUY,CL,15,71.10
FO-GAMMA,BUY,ES,3,5849.75
"""

def parse_trades(text):
    rows = []
    lines = text.strip().splitlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        account, side, symbol, qty, price = line.split(",")
        rows.append({"account": account, "side": side, "symbol": symbol,
                     "qty": int(qty), "price": float(price)})
    return rows

print(parse_trades(TRADES)[:2])
''', [("row count", r'''
r = parse_trades(TRADES)
assert len(r) == 6, f"Got {len(r)} rows; expected 6 (header and blank line skipped)"
'''), ("types", r'''
r = parse_trades(TRADES)[0]
assert r == {"account": "HF-ALPHA", "side": "BUY", "symbol": "ES", "qty": 10, "price": 5850.25}, f"first row = {r}"
'''), ("hidden file", r'''
r = parse_trades("account,side,symbol,qty,price\nX,SELL,NQ,2,20000.5\n")
assert r == [{"account": "X", "side": "SELL", "symbol": "NQ", "qty": 2, "price": 20000.5}], f"got {r}"
''')], hints=["`if not line.strip(): continue` skips blanks", "Unpack: account, side, symbol, qty, price = line.split(',')"],
wrong=r'''
TRADES = ""
def parse_trades(text):
    rows = []
    for line in text.strip().splitlines():
        if line.strip():
            a, s, sym, q, p = line.split(",")
            rows.append({"account": a, "side": s, "symbol": sym, "qty": q, "price": p})
    return rows
'''),
ex("positions(trades)", r'''
Write `positions(trades)` → dict `{(account, symbol): net_qty}` where BUY adds and SELL subtracts. Drop keys that net to zero.
(`parse_trades` and `TRADES` are provided.)
''', r'''
TRADES = """account,side,symbol,qty,price
HF-ALPHA,BUY,ES,10,5850.25
HF-ALPHA,SELL,ES,4,5852.00
HF-BETA,SELL,CL,15,71.40
HF-ALPHA,BUY,ZN,20,110.50
HF-BETA,BUY,CL,15,71.10
FO-GAMMA,BUY,ES,3,5849.75
"""
def parse_trades(text):
    rows = []
    for line in text.strip().splitlines()[1:]:
        if line.strip():
            a, s, sym, q, p = line.split(",")
            rows.append({"account": a, "side": s, "symbol": sym, "qty": int(q), "price": float(p)})
    return rows

def positions(trades):
    pos = {}
    ...
    return pos

print(positions(parse_trades(TRADES)))
''', r'''
TRADES = """account,side,symbol,qty,price
HF-ALPHA,BUY,ES,10,5850.25
HF-ALPHA,SELL,ES,4,5852.00
HF-BETA,SELL,CL,15,71.40
HF-ALPHA,BUY,ZN,20,110.50
HF-BETA,BUY,CL,15,71.10
FO-GAMMA,BUY,ES,3,5849.75
"""
def parse_trades(text):
    rows = []
    for line in text.strip().splitlines()[1:]:
        if line.strip():
            a, s, sym, q, p = line.split(",")
            rows.append({"account": a, "side": s, "symbol": sym, "qty": int(q), "price": float(p)})
    return rows

def positions(trades):
    pos = {}
    for t in trades:
        if t["side"] == "BUY":
            signed = t["qty"]          # buying adds
        else:
            signed = -t["qty"]         # selling subtracts
        key = (t["account"], t["symbol"])
        pos[key] = pos.get(key, 0) + signed
    return {k: v for k, v in pos.items() if v != 0}   # keep only non-zero positions

print(positions(parse_trades(TRADES)))
''', [("netting", r'''
p = positions(parse_trades(TRADES))
assert p.get(("HF-ALPHA", "ES")) == 6, f"HF-ALPHA ES should be 10 − 4 = 6; got {p.get(('HF-ALPHA','ES'))}. Are SELLs negative?"
assert p.get(("HF-ALPHA", "ZN")) == 20 and p.get(("FO-GAMMA", "ES")) == 3
'''), ("flat dropped", r'''
p = positions(parse_trades(TRADES))
assert ("HF-BETA", "CL") not in p, "HF-BETA sold 15 and bought 15 CL → flat, drop it"
'''), ("keys are tuples", r'''
p = positions([{"account": "Z", "side": "SELL", "symbol": "NQ", "qty": 2, "price": 1.0}])
assert p == {("Z", "NQ"): -2}, f"got {p}"
''')], hints=["if t['side'] == 'BUY': signed = t['qty'], else: signed = -t['qty']", "key = (t['account'], t['symbol'])"],
wrong=r'''
TRADES = ""
def parse_trades(text): return []
def positions(trades):
    pos = {}
    for t in trades:
        key = (t["account"], t["symbol"])
        pos[key] = pos.get(key, 0) + t["qty"]
    return pos
'''),
],
work=r'''
**Take it to work — Morning trade-file parser**
- Point `parse_trades` at a sanitized export of your overnight trades / drop-copy file (`open("trades.csv").read()`).
- Add a `bad_rows` list: wrap each row in `try/except ValueError` (coming up in the next unit) and report line numbers you skipped.
- Compare `positions(today)` against yesterday's positions + today's trades and print any differences.
- Output: a CSV of net positions by account/symbol you can paste into the risk deck.
''')
