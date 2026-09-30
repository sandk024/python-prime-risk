from dsl import *

POS = r'''POS = """account,symbol,qty,price,prev_settle
HF-ALPHA,ES,120,5790.00,5850.25
HF-ALPHA,NQ,-40,20100.00,20410.50
HF-ALPHA,CL,-250,73.10,71.40
HF-BETA,ES,-60,5790.00,5850.25
HF-BETA,ZN,800,110.62,110.50
HF-BETA,GC,35,2655.0,2650.0
FO-GAMMA,ES,15,5790.00,5850.25
FO-GAMMA,CL,90,73.10,71.40
FO-GAMMA,ZN,-150,110.62,110.50
"""
MULT = {"ES": 50, "NQ": 20, "CL": 1000, "ZN": 1000, "GC": 100}'''

def P(code):  # prepend the shared positions data
    return POS + "\n" + code

unit("u3", "pandas & SQL-Style Thinking", "DataFrames for positions and trades: filter, derive, GROUP BY, JOIN, window functions, cleaning, TCA and automated reports.")

lesson("u3l1", "DataFrames: load the positions file",
"Load the daily positions file and answer the desk's quick questions in seconds instead of Excel filters.",
r'''
**pandas** is Excel/SQL for Python. A `DataFrame` is a table; each column is a `Series`.

```python
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))   # at work: pd.read_csv("positions.csv") or pd.read_excel(...)
df.head()        # first rows
df.shape         # (rows, cols)
df.dtypes        # column types
df["qty"]        # one column → Series
df[["account", "qty"]]   # several columns → DataFrame
```

**Filtering** with boolean masks — SQL `WHERE`:
```python
df[df["qty"] > 0]
df[(df["symbol"] == "ES") & (df["qty"] > 0)]    # & and |, with parentheses!
df[df["symbol"].isin(["ES", "NQ"])]
df.query("symbol == 'ES' and qty > 0")          # same, SQL-ish
```

Other quick answers: `df["account"].nunique()`, `df["symbol"].value_counts()`, `df.sort_values("qty", ascending=False)`, `df.loc[row_mask, "col"]`.
''',
examples=[("Explore", P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
print(df.shape)
print(df.head(3))
print(df["symbol"].value_counts())
print(df[(df["symbol"] == "ES") & (df["qty"] < 0)])
'''))],
quiz=[q("Which filter is correct in pandas?", ["df[df.qty > 0 and df.symbol == 'ES']", "df[(df.qty > 0) & (df.symbol == 'ES')]", "df[df.qty > 0 & df.symbol == 'ES']", "df.where(qty > 0, symbol == 'ES')"], 1, "Use `&`/`|` element-wise with each condition in parentheses; `and` doesn't work on Series.")],
exercises=[
ex("Quick questions", r'''
Load `POS` into `df`, then create:
- `es_long`: DataFrame of **ES** rows with qty > 0
- `n_accounts`: number of unique accounts
- `short_symbols`: **sorted list** of unique symbols that have any short (qty < 0) position
''', P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
es_long = ...
n_accounts = ...
short_symbols = ...
'''), P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
es_long = df[(df["symbol"] == "ES") & (df["qty"] > 0)]
n_accounts = df["account"].nunique()
short_symbols = sorted(df.loc[df["qty"] < 0, "symbol"].unique())
'''), [("es_long", r'''
import pandas as pd
assert isinstance(es_long, pd.DataFrame), "es_long should be a filtered DataFrame"
assert sorted(es_long["account"]) == ["FO-GAMMA", "HF-ALPHA"], f"es_long accounts = {list(es_long['account'])}"
'''), ("n_accounts", r'''assert n_accounts == 3, f"n_accounts = {n_accounts}" + (" — that's the row count; use .nunique()" if n_accounts == 9 else "")'''),
("short_symbols", r'''assert list(short_symbols) == ["CL", "ES", "NQ", "ZN"], f"short_symbols = {list(short_symbols)}"''')],
hints=["df[(cond1) & (cond2)]", "df.loc[df['qty'] < 0, 'symbol'].unique()"],
wrong=P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
es_long = df[df["symbol"] == "ES"]
n_accounts = len(df)
short_symbols = list(df.loc[df["qty"] < 0, "symbol"])
''')),
ex("Largest positions", r'''
Create `top3`: a **list of the 3 accounts+symbols** with the largest **absolute** qty, as strings like `"HF-BETA ZN"`, largest first.
''', P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
top3 = ...
print(top3)
'''), P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
top = df.assign(abs_qty=df["qty"].abs()).sort_values("abs_qty", ascending=False).head(3)
top3 = (top["account"] + " " + top["symbol"]).tolist()
print(top3)
'''), [("top3", r'''
assert list(top3) == ["HF-BETA ZN", "HF-ALPHA CL", "FO-GAMMA ZN"], f"top3 = {list(top3)}" + (" — sort by ABSOLUTE qty so big shorts count" if "HF-ALPHA ES" in list(top3) else "")
''')], hints=["df['qty'].abs()", "df.assign(abs_qty=...).sort_values('abs_qty', ascending=False).head(3)", "String columns can be added: df['account'] + ' ' + df['symbol']"],
wrong=P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
top = df.sort_values("qty", ascending=False).head(3)
top3 = (top["account"] + " " + top["symbol"]).tolist()
''')),
])

lesson("u3l2", "Derived columns: notional & P&L without loops",
"Add multiplier, notional, side and daily P&L columns to the positions file — vectorized, in 4 lines.",
r'''
Column math is **vectorized** — it applies to every row at once (fast, no loops):

```python
df["mult"] = df["symbol"].map(MULT)                     # lookup via dict
df["notional"] = df["qty"].abs() * df["price"] * df["mult"]
df["pnl"] = (df["price"] - df["prev_settle"]) * df["qty"] * df["mult"]
df["side"] = np.where(df["qty"] > 0, "LONG", "SHORT")    # vectorized if/else
```

- `.map(dict)` is a VLOOKUP; unmapped keys become `NaN` (check with `.isna()`!).
- `np.select([cond1, cond2], [a, b], default=c)` for multi-branch rules.
- `.round(2)`, `.astype(int)`, `.clip(lower=0)` (floor at zero — e.g. shortfall).
- Set values on a subset with `.loc`: `df.loc[df["qty"] < 0, "flag"] = "short"`.
- `df.assign(new=...)` returns a new DataFrame (nice in pipelines).

> pandas 3 uses **copy-on-write**: modifying a filtered slice doesn't change the original. Assign with `df.loc[mask, col] = ...` on the original.
''',
examples=[("Vectorized P&L", P(r'''
import io
import numpy as np
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
df["mult"] = df["symbol"].map(MULT)
df["pnl"] = (df["price"] - df["prev_settle"]) * df["qty"] * df["mult"]
df["side"] = np.where(df["qty"] > 0, "LONG", "SHORT")
print(df[["account", "symbol", "side", "pnl"]])
print("Firm P&L:", round(df["pnl"].sum(), 2))
'''))],
quiz=[q("`df['symbol'].map({'ES': 50})` on a row with symbol 'CL' gives…", ["0", "KeyError", "NaN", "'CL'"], 2, "Unmapped values become NaN — always check for NaN after a map/merge.")],
exercises=[
ex("Notional & P&L columns", r'''
Add columns `mult`, `notional` (gross: |qty| × price × mult) and `pnl` ((price − prev_settle) × qty × mult) to `df`.
''', P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
# add columns here
print(df.head())
'''), P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
df["mult"] = df["symbol"].map(MULT)
df["notional"] = df["qty"].abs() * df["price"] * df["mult"]
df["pnl"] = (df["price"] - df["prev_settle"]) * df["qty"] * df["mult"]
print(df.head())
'''), [("mult", r'''assert "mult" in df and df["mult"].tolist() == [50, 20, 1000, 50, 1000, 100, 50, 1000, 1000], "mult should map symbol → multiplier via MULT"'''),
("notional", r'''
r = df.loc[df["symbol"].eq("NQ"), "notional"].iloc[0]
assert _close(r, 16_080_000), f"HF-ALPHA NQ notional = {r}; expected 40 × 20,100 × 20 = 16,080,000 (use .abs() on qty)"
assert _close(df["notional"].sum(), 211_768_000.0), f"total notional = {df['notional'].sum():,.2f}"
'''), ("pnl", r'''
r = df.loc[(df["account"] == "HF-ALPHA") & (df["symbol"] == "CL"), "pnl"].iloc[0]
assert _close(r, -425_000), f"HF-ALPHA CL pnl = {r}; short 250 CL, +1.70 move → −425,000"
assert _close(df["pnl"].sum(), -154_037.5), f"firm pnl = {df['pnl'].sum():,.2f}"
''')], hints=["df['symbol'].map(MULT)", "df['qty'].abs() * df['price'] * df['mult']"],
wrong=P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
df["mult"] = df["symbol"].map(MULT)
df["notional"] = df["qty"] * df["price"] * df["mult"]
df["pnl"] = (df["prev_settle"] - df["price"]) * df["qty"] * df["mult"]
''')),
ex("Classify with np.select", r'''
Add a `bucket` column: `"LARGE"` if notional ≥ 25,000,000, `"MEDIUM"` if ≥ 5,000,000, else `"SMALL"`. Then `counts` = dict bucket → number of rows.
''', P(r'''
import io
import numpy as np
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
df["notional"] = df["qty"].abs() * df["price"] * df["symbol"].map(MULT)
df["bucket"] = ...
counts = ...
print(counts)
'''), P(r'''
import io
import numpy as np
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
df["notional"] = df["qty"].abs() * df["price"] * df["symbol"].map(MULT)
df["bucket"] = np.select([df["notional"] >= 25_000_000, df["notional"] >= 5_000_000], ["LARGE", "MEDIUM"], default="SMALL")
counts = df["bucket"].value_counts().to_dict()
print(counts)
'''), [("bucket", r'''
b = dict(zip(df["account"] + " " + df["symbol"], df["bucket"]))
assert b["HF-ALPHA ES"] == "LARGE" and b["HF-BETA ZN"] == "LARGE", f"HF-ALPHA ES (34.7m) and HF-BETA ZN (88.5m) should be LARGE; got {b['HF-ALPHA ES']}, {b['HF-BETA ZN']}"
assert b["HF-BETA GC"] == "MEDIUM" and b["FO-GAMMA ES"] == "SMALL", f"HF-BETA GC (9.29m) should be MEDIUM and FO-GAMMA ES (4.34m) SMALL; got {b['HF-BETA GC']}, {b['FO-GAMMA ES']}"
'''), ("counts", r'''
assert dict(counts) == {"LARGE": 2, "MEDIUM": 6, "SMALL": 1}, f"counts = {dict(counts)}"
''')], hints=["np.select([cond_large, cond_medium], ['LARGE', 'MEDIUM'], default='SMALL') — order matters: first match wins", "df['bucket'].value_counts().to_dict()"],
wrong=P(r'''
import io
import numpy as np
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
df["notional"] = df["qty"].abs() * df["price"] * df["symbol"].map(MULT)
df["bucket"] = np.select([df["notional"] >= 5_000_000, df["notional"] >= 25_000_000], ["MEDIUM", "LARGE"], default="SMALL")
counts = df["bucket"].value_counts().to_dict()
''')),
])

lesson("u3l3", "GROUP BY: exposure by account and product",
"Produce the morning risk-call table: gross/net exposure and P&L by account, and an account × product grid.",
r'''
`groupby` is SQL `GROUP BY`:

```sql
SELECT account, SUM(notional) AS gross, COUNT(*) AS n FROM pos GROUP BY account
```
```python
df.groupby("account").agg(gross=("notional", "sum"), n=("symbol", "size")).reset_index()
```

- `df.groupby("account")["pnl"].sum()` → a Series indexed by account.
- **Named aggregation** `agg(new_name=(column, func))` gives clean column names. Funcs: `"sum" "mean" "min" "max" "size" "count" "nunique" "first"`.
- Group by several keys: `groupby(["account", "symbol"])`.
- `.reset_index()` turns the group keys back into columns (for merging/exporting).
- **Pivot** (Excel pivot table): `df.pivot_table(index="account", columns="symbol", values="qty", aggfunc="sum", fill_value=0)`.

Net vs gross: **net** notional nets longs against shorts (signed); **gross** adds absolute values. Risk teams look at both — gross for balance-sheet/leverage, net for directional exposure.
''',
examples=[("Group & pivot", P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
df["mult"] = df["symbol"].map(MULT)
df["signed_notional"] = df["qty"] * df["price"] * df["mult"]
print(df.groupby("account")["signed_notional"].sum().round(0))
print(df.pivot_table(index="account", columns="symbol", values="qty", aggfunc="sum", fill_value=0))
'''))],
quiz=[q("Long 10 ES ($2.9m) and short 10 ES in another sub-account of the same client. Gross vs net notional?", ["Gross 0, net 5.8m", "Gross 5.8m, net 0", "Both 5.8m", "Both 0"], 1, "Gross adds absolute values; net offsets longs vs shorts.")],
exercises=[
ex("Account summary", r'''
Build `summary`: a DataFrame with **columns** `account, gross, net, pnl, n_positions` (one row per account), sorted by `gross` descending.
gross = Σ|notional|, net = Σ signed notional (qty × price × mult), pnl = Σ daily P&L.
''', P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
df["mult"] = df["symbol"].map(MULT)
df["signed"] = df["qty"] * df["price"] * df["mult"]
df["gross"] = df["signed"].abs()
df["pnl"] = (df["price"] - df["prev_settle"]) * df["qty"] * df["mult"]
summary = ...
print(summary)
'''), P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
df["mult"] = df["symbol"].map(MULT)
df["signed"] = df["qty"] * df["price"] * df["mult"]
df["gross"] = df["signed"].abs()
df["pnl"] = (df["price"] - df["prev_settle"]) * df["qty"] * df["mult"]
summary = (df.groupby("account")
             .agg(gross=("gross", "sum"), net=("signed", "sum"), pnl=("pnl", "sum"), n_positions=("symbol", "size"))
             .reset_index()
             .sort_values("gross", ascending=False))
print(summary)
'''), [("shape & columns", r'''
assert list(summary.columns) == ["account", "gross", "net", "pnl", "n_positions"], f"columns = {list(summary.columns)} — use named agg and .reset_index()"
assert len(summary) == 3
'''), ("order", r'''assert summary["account"].tolist() == ["HF-BETA", "HF-ALPHA", "FO-GAMMA"], f"order = {summary['account'].tolist()} — sort by gross descending"'''),
("values", r'''
s = summary.set_index("account")
assert _close(s.loc["HF-ALPHA", "gross"], 69_095_000), f"HF-ALPHA gross = {s.loc['HF-ALPHA','gross']:,.0f}"
assert _close(s.loc["HF-ALPHA", "net"], 385_000), f"HF-ALPHA net = {s.loc['HF-ALPHA','net']:,.0f} (34.74m − 16.08m − 18.275m)"
assert _close(s.loc["HF-BETA", "pnl"], 294_250), f"HF-BETA pnl = {s.loc['HF-BETA','pnl']:,.0f}"
assert s.loc["FO-GAMMA", "n_positions"] == 3
''')], hints=["df.groupby('account').agg(gross=('gross', 'sum'), net=('signed', 'sum'), ...)", ".reset_index().sort_values('gross', ascending=False)"],
wrong=P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
df["mult"] = df["symbol"].map(MULT)
df["signed"] = df["qty"] * df["price"] * df["mult"]
df["gross"] = df["signed"].abs()
df["pnl"] = (df["price"] - df["prev_settle"]) * df["qty"] * df["mult"]
summary = df.groupby("account").agg(gross=("gross", "sum"), net=("gross", "sum"), pnl=("pnl", "sum"), n_positions=("symbol", "size"))
''')),
ex("Account × product grid", r'''
Create `grid`: pivot table of **net qty** with accounts as rows and symbols as columns, missing = 0. Then `firm_net` = Series of net qty per symbol (column sums).
''', P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
grid = ...
firm_net = ...
print(grid)
'''), P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
grid = df.pivot_table(index="account", columns="symbol", values="qty", aggfunc="sum", fill_value=0)
firm_net = grid.sum()
print(grid)
'''), [("grid", r'''
assert grid.loc["HF-BETA", "ES"] == -60 and grid.loc["HF-BETA", "NQ"] == 0, "HF-BETA ES should be −60 and HF-BETA NQ 0 (fill_value=0)"
assert sorted(grid.columns) == ["CL", "ES", "GC", "NQ", "ZN"]
'''), ("firm_net", r'''assert firm_net["ES"] == 75 and firm_net["ZN"] == 650 and firm_net["CL"] == -160, f"firm_net = {dict(firm_net)}"''')],
hints=["pivot_table(index='account', columns='symbol', values='qty', aggfunc='sum', fill_value=0)", "grid.sum() sums each column"],
wrong=P(r'''
import io
import pandas as pd
df = pd.read_csv(io.StringIO(POS))
grid = df.pivot_table(index="account", columns="symbol", values="qty", aggfunc="sum")
firm_net = grid.sum(axis=1)
''')),
])

lesson("u3l4", "JOINs with merge: prices, specs and recon",
"Join positions to settlement prices and contract specs; catch positions with no price before they zero out your risk.",
r'''
`pd.merge` is SQL `JOIN`:

```python
pd.merge(positions, prices, on="symbol", how="left")         # LEFT JOIN
pd.merge(internal, clearing, on=["account", "symbol"], how="outer", suffixes=("_int", "_clr"), indicator=True)
```

- `how`: `"inner"` (only matches), `"left"` (keep all left rows), `"outer"` (keep everything), `"right"`.
- `indicator=True` adds `_merge` = `left_only` / `right_only` / `both` — perfect for recon.
- `validate="many_to_one"` raises if the right side has duplicate keys (catches double-counting from a duplicated price row!).
- **Anti-join** (rows in A with no match in B): merge with indicator, keep `_merge == "left_only"`.

After a left join, **always check for NaN** in joined columns — a missing price silently becomes zero risk if you `fillna(0)`.
''',
examples=[("Left join + anti-join", r'''
import pandas as pd
pos = pd.DataFrame({"account": ["A", "A", "B"], "symbol": ["ES", "RTY", "CL"], "qty": [10, 5, -3]})
px = pd.DataFrame({"symbol": ["ES", "CL"], "settle": [5790.0, 73.10]})
m = pos.merge(px, on="symbol", how="left", validate="many_to_one", indicator=True)
print(m)
print("No price:", m.loc[m["_merge"] == "left_only", "symbol"].tolist())
''')],
quiz=[q("Positions has 9 rows; the prices table accidentally has ES twice. After an inner merge on symbol, you'll likely see…", ["9 rows", "More than 9 rows — ES positions duplicated", "An automatic error", "Fewer rows"], 1, "Duplicate keys on the right multiply matching rows. Use validate='many_to_one' to make pandas raise instead.")],
exercises=[
ex("Price the book, find gaps", r'''
Left-join `pos` to `prices` on symbol → `priced`. Then:
- `missing_price`: sorted list of symbols with no settlement price
- `mv`: total signed market value (qty × settle × mult) of **priced** rows only, using `MULT`
''', r'''
import pandas as pd
MULT = {"ES": 50, "NQ": 20, "CL": 1000, "ZN": 1000, "GC": 100, "RTY": 50, "NG": 10000}
pos = pd.DataFrame({
    "account": ["HF-ALPHA", "HF-ALPHA", "HF-BETA", "HF-BETA", "FO-GAMMA", "FO-GAMMA"],
    "symbol":  ["ES", "RTY", "CL", "NG", "ES", "RTY"],
    "qty":     [120, 30, -250, 40, 15, -10]})
prices = pd.DataFrame({"symbol": ["ES", "CL", "ZN", "NQ"], "settle": [5790.0, 73.10, 110.62, 20100.0]})
priced = ...
missing_price = ...
mv = ...
''', r'''
import pandas as pd
MULT = {"ES": 50, "NQ": 20, "CL": 1000, "ZN": 1000, "GC": 100, "RTY": 50, "NG": 10000}
pos = pd.DataFrame({
    "account": ["HF-ALPHA", "HF-ALPHA", "HF-BETA", "HF-BETA", "FO-GAMMA", "FO-GAMMA"],
    "symbol":  ["ES", "RTY", "CL", "NG", "ES", "RTY"],
    "qty":     [120, 30, -250, 40, 15, -10]})
prices = pd.DataFrame({"symbol": ["ES", "CL", "ZN", "NQ"], "settle": [5790.0, 73.10, 110.62, 20100.0]})
priced = pos.merge(prices, on="symbol", how="left", validate="many_to_one")
missing_price = sorted(priced.loc[priced["settle"].isna(), "symbol"].unique())
ok = priced.dropna(subset=["settle"])
mv = (ok["qty"] * ok["settle"] * ok["symbol"].map(MULT)).sum()
''', [("priced keeps all positions", r'''assert len(priced) == 6, f"priced has {len(priced)} rows — use how='left' to keep every position"'''),
("missing_price", r'''assert list(missing_price) == ["NG", "RTY"], f"missing_price = {list(missing_price)}"'''),
("mv", r'''assert _close(mv, 20_807_500.0), f"mv = {mv:,.2f}; expected 135 ES × 5790 × 50 − 250 CL × 73.10 × 1000"''')],
hints=["pos.merge(prices, on='symbol', how='left')", "priced['settle'].isna()"],
wrong=r'''
import pandas as pd
MULT = {"ES": 50, "NQ": 20, "CL": 1000, "ZN": 1000, "GC": 100, "RTY": 50, "NG": 10000}
pos = pd.DataFrame({"account": ["HF-ALPHA"] * 6, "symbol": ["ES", "RTY", "CL", "NG", "ES", "RTY"], "qty": [120, 30, -250, 40, 15, -10]})
prices = pd.DataFrame({"symbol": ["ES", "CL", "ZN", "NQ"], "settle": [5790.0, 73.10, 110.62, 20100.0]})
priced = pos.merge(prices, on="symbol")
missing_price = []
mv = (priced["qty"] * priced["settle"] * priced["symbol"].map(MULT)).sum()
'''),
ex("Recon with an outer join", r'''
Outer-merge `internal` and `clearing` on `["account", "symbol"]` with suffixes `_int` / `_clr`, fill missing qty with 0, and produce `breaks`: rows where `qty_int != qty_clr`, with a `diff` column (int − clr). Sort by account, symbol and reset the index.
''', r'''
import pandas as pd
internal = pd.DataFrame({"account": ["HF-A", "HF-A", "HF-B", "HF-C"], "symbol": ["ES", "NQ", "CL", "ZN"], "qty": [10, -4, -5, 20]})
clearing = pd.DataFrame({"account": ["HF-A", "HF-A", "HF-C", "HF-D"], "symbol": ["ES", "NQ", "ZN", "GC"], "qty": [10, -2, 20, 3]})
breaks = ...
print(breaks)
''', r'''
import pandas as pd
internal = pd.DataFrame({"account": ["HF-A", "HF-A", "HF-B", "HF-C"], "symbol": ["ES", "NQ", "CL", "ZN"], "qty": [10, -4, -5, 20]})
clearing = pd.DataFrame({"account": ["HF-A", "HF-A", "HF-C", "HF-D"], "symbol": ["ES", "NQ", "ZN", "GC"], "qty": [10, -2, 20, 3]})
m = internal.merge(clearing, on=["account", "symbol"], how="outer", suffixes=("_int", "_clr"))
m[["qty_int", "qty_clr"]] = m[["qty_int", "qty_clr"]].fillna(0)
m["diff"] = m["qty_int"] - m["qty_clr"]
breaks = m[m["diff"] != 0].sort_values(["account", "symbol"]).reset_index(drop=True)
print(breaks)
''', [("break rows", r'''
got = list(zip(breaks["account"], breaks["symbol"]))
assert got == [("HF-A", "NQ"), ("HF-B", "CL"), ("HF-D", "GC")], f"breaks = {got}" + (" — use how='outer' so one-sided positions appear" if ("HF-D", "GC") not in got else "")
'''), ("diff", r'''assert breaks["diff"].tolist() == [-2, -5, -3], f"diff = {breaks['diff'].tolist()}"''')],
hints=["how='outer', suffixes=('_int', '_clr')", "Fill NaN quantities with 0 before comparing."],
wrong=r'''
import pandas as pd
internal = pd.DataFrame({"account": ["HF-A", "HF-A", "HF-B", "HF-C"], "symbol": ["ES", "NQ", "CL", "ZN"], "qty": [10, -4, -5, 20]})
clearing = pd.DataFrame({"account": ["HF-A", "HF-A", "HF-C", "HF-D"], "symbol": ["ES", "NQ", "ZN", "GC"], "qty": [10, -2, 20, 3]})
m = internal.merge(clearing, on=["account", "symbol"], how="inner", suffixes=("_int", "_clr"))
m["diff"] = m["qty_int"] - m["qty_clr"]
breaks = m[m["diff"] != 0].reset_index(drop=True)
'''),
])

lesson("u3l5", "Window functions: running positions, shares, day-over-day",
"Show each account's running position through the day, its share of firm exposure, and day-over-day margin changes.",
r'''
SQL **window functions** compute per-row values *within* a group without collapsing rows:

| SQL | pandas |
|---|---|
| `SUM(qty) OVER (PARTITION BY acct ORDER BY ts)` | `df.sort_values("ts").groupby("acct")["qty"].cumsum()` |
| `SUM(x) OVER (PARTITION BY acct)` | `df.groupby("acct")["x"].transform("sum")` |
| `RANK() OVER (PARTITION BY acct ORDER BY x DESC)` | `df.groupby("acct")["x"].rank(ascending=False, method="first")` |
| `LAG(x) OVER (PARTITION BY acct ORDER BY d)` | `df.groupby("acct")["x"].shift(1)` |
| `AVG(x) OVER (… ROWS 4 PRECEDING)` | `df.groupby("acct")["x"].rolling(5).mean()` / `s.rolling(5).mean()` |

`transform` returns a result aligned to the original rows — ideal for "share of total" columns.

Dates: `pd.to_datetime(df["ts"])`, then `.dt.date`, `.dt.hour`, and `s.resample("W-FRI").last()` on a date index.

**Always sort** before cumsum/shift/rolling — window results depend on order.
''',
examples=[("Running position per account", r'''
import pandas as pd
t = pd.DataFrame({"ts": ["09:31", "09:45", "10:02", "10:15", "11:30"],
                  "account": ["A", "B", "A", "A", "B"], "qty": [10, -5, 5, -12, 5]})
t = t.sort_values("ts")
t["position"] = t.groupby("account")["qty"].cumsum()
t["acct_total_traded"] = t.groupby("account")["qty"].transform(lambda s: s.abs().sum())
print(t)
''')],
quiz=[q("Which returns one value per ORIGINAL row (same length as df)?", ["df.groupby('a')['x'].sum()", "df.groupby('a')['x'].transform('sum')", "df.groupby('a').size()", "df.pivot_table(...)"], 1, "transform broadcasts the group result back to every row; sum() collapses to one row per group.")],
exercises=[
ex("Running position & share of exposure", r'''
On `trades` (already sorted by time):
- add `position`: running net qty per **account + symbol**
- add `share`: each row's |qty| as a fraction of that **account's** total |qty| traded (use `transform`)
''', r'''
import pandas as pd
trades = pd.DataFrame({
    "ts": pd.to_datetime(["2026-09-30 09:31", "2026-09-30 09:45", "2026-09-30 10:02", "2026-09-30 10:15", "2026-09-30 11:30", "2026-09-30 13:05"]),
    "account": ["HF-A", "HF-B", "HF-A", "HF-A", "HF-B", "HF-A"],
    "symbol":  ["ES", "ES", "ES", "NQ", "ES", "ES"],
    "qty":     [10, -5, 5, -8, 5, -12]})
trades["abs_qty"] = trades["qty"].abs()
# add position and share
print(trades)
''', r'''
import pandas as pd
trades = pd.DataFrame({
    "ts": pd.to_datetime(["2026-09-30 09:31", "2026-09-30 09:45", "2026-09-30 10:02", "2026-09-30 10:15", "2026-09-30 11:30", "2026-09-30 13:05"]),
    "account": ["HF-A", "HF-B", "HF-A", "HF-A", "HF-B", "HF-A"],
    "symbol":  ["ES", "ES", "ES", "NQ", "ES", "ES"],
    "qty":     [10, -5, 5, -8, 5, -12]})
trades["abs_qty"] = trades["qty"].abs()
trades["position"] = trades.groupby(["account", "symbol"])["qty"].cumsum()
trades["share"] = trades["abs_qty"] / trades.groupby("account")["abs_qty"].transform("sum")
print(trades)
''', [("position", r'''
assert trades["position"].tolist() == [10, -5, 15, -8, 0, 3], f"position = {trades['position'].tolist()} — group by BOTH account and symbol"
'''), ("share", r'''
s = trades["share"].round(4).tolist()
assert s == [0.2857, 0.5, 0.1429, 0.2286, 0.5, 0.3429], f"share = {s} — HF-A traded |10|+|5|+|8|+|12| = 35"
''')], hints=["trades.groupby(['account', 'symbol'])['qty'].cumsum()", "trades.groupby('account')['abs_qty'].transform('sum')"],
wrong=r'''
import pandas as pd
trades = pd.DataFrame({"ts": range(6), "account": ["HF-A", "HF-B", "HF-A", "HF-A", "HF-B", "HF-A"], "symbol": ["ES", "ES", "ES", "NQ", "ES", "ES"], "qty": [10, -5, 5, -8, 5, -12]})
trades["abs_qty"] = trades["qty"].abs()
trades["position"] = trades.groupby("account")["qty"].cumsum()
trades["share"] = trades["abs_qty"] / trades["abs_qty"].sum()
'''),
ex("Day-over-day margin change (LAG)", r'''
`req` holds daily initial margin requirement per account. Add:
- `change`: requirement minus the **previous day's** requirement for the same account (first day NaN)
- `rank`: within each date, rank accounts by requirement descending (1 = largest), as int

Then `jumps`: rows where `change` > 25% of the previous day's requirement.
''', r'''
import pandas as pd
req = pd.DataFrame({
    "date": pd.to_datetime(["2026-09-28"] * 3 + ["2026-09-29"] * 3 + ["2026-09-30"] * 3),
    "account": ["HF-A", "HF-B", "FO-C"] * 3,
    "im": [12.0e6, 8.0e6, 2.0e6, 12.5e6, 10.5e6, 2.1e6, 16.0e6, 10.0e6, 2.0e6]})
req = req.sort_values(["account", "date"])
# change, rank, jumps
''', r'''
import pandas as pd
req = pd.DataFrame({
    "date": pd.to_datetime(["2026-09-28"] * 3 + ["2026-09-29"] * 3 + ["2026-09-30"] * 3),
    "account": ["HF-A", "HF-B", "FO-C"] * 3,
    "im": [12.0e6, 8.0e6, 2.0e6, 12.5e6, 10.5e6, 2.1e6, 16.0e6, 10.0e6, 2.0e6]})
req = req.sort_values(["account", "date"])
prev = req.groupby("account")["im"].shift(1)
req["change"] = req["im"] - prev
req["rank"] = req.groupby("date")["im"].rank(ascending=False, method="first").astype(int)
jumps = req[req["change"] > 0.25 * prev]
''', [("change", r'''
r = req.set_index(["account", "date"])["change"]
import pandas as pd
assert pd.isna(r[("HF-A", pd.Timestamp("2026-09-28"))]), "First day per account should be NaN (no previous day)"
assert _close(r[("HF-A", pd.Timestamp("2026-09-30"))], 3.5e6), f"HF-A 9/30 change = {r[('HF-A', pd.Timestamp('2026-09-30'))]} — shift within each account"
'''), ("rank", r'''
import pandas as pd
x = req[req["date"] == pd.Timestamp("2026-09-29")].set_index("account")["rank"]
assert x["HF-A"] == 1 and x["HF-B"] == 2 and x["FO-C"] == 3, f"ranks on 9/29 = {dict(x)}"
'''), ("jumps", r'''
got = sorted(zip(jumps["account"], jumps["date"].dt.strftime("%m-%d")))
assert got == [("HF-A", "09-30"), ("HF-B", "09-29")], f"jumps = {got} (HF-B +31% on 9/29, HF-A +28% on 9/30)"
''')], hints=["prev = req.groupby('account')['im'].shift(1)", "req.groupby('date')['im'].rank(ascending=False, method='first')"],
wrong=r'''
import pandas as pd
req = pd.DataFrame({"date": pd.to_datetime(["2026-09-28"] * 3 + ["2026-09-29"] * 3 + ["2026-09-30"] * 3), "account": ["HF-A", "HF-B", "FO-C"] * 3, "im": [12.0e6, 8.0e6, 2.0e6, 12.5e6, 10.5e6, 2.1e6, 16.0e6, 10.0e6, 2.0e6]})
req["change"] = req["im"].diff()
req["rank"] = req["im"].rank(ascending=False).astype(int)
jumps = req[req["change"] > 0.25 * req["im"]]
'''),
])

lesson("u3l6", "Cleaning messy data",
"The executing broker's file has spaces, commas in numbers, duplicate rows and blanks — clean it before trusting any number.",
r'''
Real data is messy. Budget time for it, and **count what you drop** — a cleaning step that silently removes 10% of trades is a bug.

```python
df["account"] = df["account"].str.strip().str.upper()
df["qty"] = pd.to_numeric(df["qty"].str.replace(",", ""), errors="coerce")  # bad → NaN
df = df.dropna(subset=["qty"])
df = df.drop_duplicates()                       # exact duplicate rows
df = df.drop_duplicates(subset=["trade_id"], keep="last")   # latest amendment wins
df["price"] = df["price"].fillna(df["price"].median())   # only if justified!
df = df.rename(columns={"Acct ": "account"})
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
```

Checklist: headers → whitespace/case → numeric types → dates → duplicates → missing values → outliers (e.g. price 10× the median) → **reconcile row counts** before/after.

This is the heart of Palantir-style work: most of the value is in making messy source data trustworthy.
''',
examples=[("Clean a messy file", r'''
import io
import pandas as pd
raw = """ Trade ID ,Acct , Qty,Price
T1, hf-alpha ,"1,200",5790.25
T2,HF-BETA,-60,5790.00
T2,HF-BETA,-60,5790.00
T3,FO-GAMMA,abc,73.10
"""
df = pd.read_csv(io.StringIO(raw), dtype=str)
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
print(df.columns.tolist())
df["acct"] = df["acct"].str.strip().str.upper()
df["qty"] = pd.to_numeric(df["qty"].str.replace(",", "").str.strip(), errors="coerce")
print(df)
''')],
quiz=[q("`pd.to_numeric(s, errors='coerce')` does what with 'abc'?", ["Raises ValueError", "Returns 0", "Returns NaN", "Leaves 'abc'"], 2, "coerce converts unparseable values to NaN so you can find/count/drop them.")],
exercises=[
ex("clean_fills(raw)", r'''
Write `clean_fills(raw)` returning `(clean_df, n_dropped)`:
1. read with `dtype=str`; normalize headers to lower_snake_case
2. strip + upper-case `account`; `qty` → numeric (remove commas); `price` → numeric
3. drop rows with missing qty or price, then drop duplicate `trade_id` keeping the **last**
4. `n_dropped` = original rows − final rows
Final `qty` should be int.
''', r'''
import io
import pandas as pd
RAW = """ Trade ID ,Account, Qty ,Price
T1, hf-alpha ,"1,200",5790.25
T2,HF-BETA,-60,5790.00
T2,HF-BETA,-65,5790.00
T3,FO-GAMMA,abc,73.10
T4,fo-gamma ,90,
T5,HF-ALPHA,-250,73.12
"""

def clean_fills(raw):
    df = pd.read_csv(io.StringIO(raw), dtype=str)
    ...
    return df, n_dropped

clean, n = clean_fills(RAW)
print(clean, n)
''', r'''
import io
import pandas as pd
RAW = """ Trade ID ,Account, Qty ,Price
T1, hf-alpha ,"1,200",5790.25
T2,HF-BETA,-60,5790.00
T2,HF-BETA,-65,5790.00
T3,FO-GAMMA,abc,73.10
T4,fo-gamma ,90,
T5,HF-ALPHA,-250,73.12
"""

def clean_fills(raw):
    df = pd.read_csv(io.StringIO(raw), dtype=str)
    n0 = len(df)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["trade_id"] = df["trade_id"].str.strip()
    df["account"] = df["account"].str.strip().str.upper()
    df["qty"] = pd.to_numeric(df["qty"].str.replace(",", "").str.strip(), errors="coerce")
    df["price"] = pd.to_numeric(df["price"].str.strip(), errors="coerce")
    df = df.dropna(subset=["qty", "price"])
    df = df.drop_duplicates(subset=["trade_id"], keep="last").reset_index(drop=True)
    df["qty"] = df["qty"].astype(int)
    return df, n0 - len(df)

clean, n = clean_fills(RAW)
print(clean, n)
''', [("columns", r'''
c, n = clean_fills(RAW)
assert list(c.columns) == ["trade_id", "account", "qty", "price"], f"columns = {list(c.columns)}"
'''), ("rows kept", r'''
c, n = clean_fills(RAW)
assert c["trade_id"].tolist() == ["T1", "T2", "T5"], f"kept {c['trade_id'].tolist()} — T3 (qty 'abc') and T4 (no price) dropped; T2 keeps the LAST version"
'''), ("values", r'''
c, n = clean_fills(RAW)
r = c.set_index("trade_id")
assert r.loc["T1", "account"] == "HF-ALPHA" and r.loc["T1", "qty"] == 1200, f"T1 = {dict(r.loc['T1'])}"
assert r.loc["T2", "qty"] == -65, "T2 should keep the last amendment (−65)"
assert str(c["qty"].dtype).startswith("int"), f"qty dtype = {c['qty'].dtype}; convert with .astype(int)"
'''), ("n_dropped", r'''
c, n = clean_fills(RAW)
assert n == 3, f"n_dropped = {n}; 6 rows in, 3 out"
''')], hints=["df.columns.str.strip().str.lower().str.replace(' ', '_')", "pd.to_numeric(..., errors='coerce') then dropna(subset=[...])", "drop_duplicates(subset=['trade_id'], keep='last')"],
wrong=r'''
import io
import pandas as pd
RAW = """ Trade ID ,Account, Qty ,Price
T1, hf-alpha ,"1,200",5790.25
T2,HF-BETA,-60,5790.00
T2,HF-BETA,-65,5790.00
T3,FO-GAMMA,abc,73.10
T4,fo-gamma ,90,
T5,HF-ALPHA,-250,73.12
"""
def clean_fills(raw):
    df = pd.read_csv(io.StringIO(raw), dtype=str)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["account"] = df["account"].str.upper()
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna().drop_duplicates()
    return df, 0
'''),
ex("Flag price outliers", r'''
Add a boolean column `outlier` to `fills`: True when the fill price is more than **5%** away from the **median price for that symbol** (use `groupby(...).transform("median")`). Then `bad_ids` = list of flagged trade_ids.
''', r'''
import pandas as pd
fills = pd.DataFrame({"trade_id": ["T1", "T2", "T3", "T4", "T5", "T6", "T7"],
                      "symbol": ["ES", "ES", "ES", "CL", "CL", "CL", "ES"],
                      "price": [5790.25, 5791.00, 579.03, 73.10, 73.12, 77.95, 5789.75]})
''', r'''
import pandas as pd
fills = pd.DataFrame({"trade_id": ["T1", "T2", "T3", "T4", "T5", "T6", "T7"],
                      "symbol": ["ES", "ES", "ES", "CL", "CL", "CL", "ES"],
                      "price": [5790.25, 5791.00, 579.03, 73.10, 73.12, 77.95, 5789.75]})
med = fills.groupby("symbol")["price"].transform("median")
fills["outlier"] = (fills["price"] / med - 1).abs() > 0.05
bad_ids = fills.loc[fills["outlier"], "trade_id"].tolist()
''', [("outlier", r'''assert "outlier" in fills and fills["outlier"].dtype == bool, "Add a boolean 'outlier' column"'''),
("bad_ids", r'''assert bad_ids == ["T3", "T6"], f"bad_ids = {bad_ids} — T3 is a decimal-shift error (579.03), T6 is 6.6% above the CL median"''')],
hints=["med = fills.groupby('symbol')['price'].transform('median')", "(price / med − 1).abs() > 0.05"],
wrong=r'''
import pandas as pd
fills = pd.DataFrame({"trade_id": ["T1", "T2", "T3", "T4", "T5", "T6", "T7"], "symbol": ["ES", "ES", "ES", "CL", "CL", "CL", "ES"], "price": [5790.25, 5791.00, 579.03, 73.10, 73.12, 77.95, 5789.75]})
med = fills["price"].median()
fills["outlier"] = (fills["price"] / med - 1).abs() > 0.05
bad_ids = fills.loc[fills["outlier"], "trade_id"].tolist()
'''),
])

lesson("u3l7", "TCA: execution-quality summary",
"Build a client's monthly execution-quality report: slippage vs arrival, VWAP comparison and participation by algo and broker.",
r'''
**Transaction cost analysis** measures how well orders were executed.

- **Arrival price** = mid when the order reached the desk. **Implementation shortfall / arrival slippage** (bps) = side × (avg fill − arrival) / arrival × 10,000; positive = cost.
- **VWAP slippage**: avg fill vs the market VWAP over the order's life. Easy to "beat" by trading passively — so always pair it with arrival.
- **Participation rate** = order qty / market volume over the order's life. High participation → more impact.
- Aggregate with **quantity- or notional-weighted** averages, not simple means — a 1-lot order shouldn't count as much as a 500-lot order.

```python
w_avg = (df["slip_bps"] * df["notional"]).sum() / df["notional"].sum()
```

For a quick weighted mean per group, compute the weighted numerator column first, then `groupby(...).sum()` and divide.

In futures, quote slippage in **ticks** too — traders think in ticks (ES tick = 0.25).
''',
examples=[("Weighted vs simple mean", r'''
import pandas as pd
o = pd.DataFrame({"algo": ["VWAP", "VWAP", "SNIPER"], "qty": [500, 5, 100], "slip_bps": [1.0, 40.0, 3.0]})
print("simple :", o.groupby("algo")["slip_bps"].mean().round(2).to_dict())
o["w"] = o["slip_bps"] * o["qty"]
g = o.groupby("algo")[["w", "qty"]].sum()
print("weighted:", (g["w"] / g["qty"]).round(2).to_dict())
''')],
quiz=[q("An algo shows −2 bps vs VWAP but +9 bps vs arrival on a strongly trending day. The best read?", ["Great execution", "It traded passively as price ran away — real cost vs decision price was 9 bps", "VWAP numbers are wrong", "Arrival is irrelevant"], 1, "VWAP benchmarks drift with the market; arrival slippage captures the cost of delay in a trend.")],
exercises=[
ex("Order-level slippage", r'''
Add columns to `orders`:
- `slip_bps`: side-aware arrival slippage in bps (BUY: fill above arrival = cost; SELL: fill below = cost)
- `slip_ticks`: side-aware slippage in ticks using `TICK` per symbol
- `participation`: qty / market_volume
''', r'''
import pandas as pd
TICK = {"ES": 0.25, "NQ": 0.25, "CL": 0.01, "ZN": 1 / 64}
orders = pd.DataFrame({
    "order_id": ["O1", "O2", "O3", "O4", "O5", "O6"],
    "algo": ["VWAP", "VWAP", "SNIPER", "POV", "SNIPER", "POV"],
    "broker": ["BRK-X", "BRK-Y", "BRK-X", "BRK-Y", "BRK-Y", "BRK-X"],
    "symbol": ["ES", "ES", "CL", "NQ", "ZN", "CL"],
    "side": ["BUY", "SELL", "BUY", "SELL", "BUY", "SELL"],
    "qty": [500, 200, 150, 80, 1000, 300],
    "arrival": [5790.00, 5791.50, 73.10, 20105.00, 110.625, 73.20],
    "avg_fill": [5790.75, 5790.25, 73.13, 20101.25, 110.640625, 73.21],
    "market_volume": [9000, 5000, 1500, 1600, 20000, 2400]})
''', r'''
import numpy as np
import pandas as pd
TICK = {"ES": 0.25, "NQ": 0.25, "CL": 0.01, "ZN": 1 / 64}
orders = pd.DataFrame({
    "order_id": ["O1", "O2", "O3", "O4", "O5", "O6"],
    "algo": ["VWAP", "VWAP", "SNIPER", "POV", "SNIPER", "POV"],
    "broker": ["BRK-X", "BRK-Y", "BRK-X", "BRK-Y", "BRK-Y", "BRK-X"],
    "symbol": ["ES", "ES", "CL", "NQ", "ZN", "CL"],
    "side": ["BUY", "SELL", "BUY", "SELL", "BUY", "SELL"],
    "qty": [500, 200, 150, 80, 1000, 300],
    "arrival": [5790.00, 5791.50, 73.10, 20105.00, 110.625, 73.20],
    "avg_fill": [5790.75, 5790.25, 73.13, 20101.25, 110.640625, 73.21],
    "market_volume": [9000, 5000, 1500, 1600, 20000, 2400]})
sign = np.where(orders["side"] == "BUY", 1, -1)
diff = sign * (orders["avg_fill"] - orders["arrival"])
orders["slip_bps"] = diff / orders["arrival"] * 10_000
orders["slip_ticks"] = diff / orders["symbol"].map(TICK)
orders["participation"] = orders["qty"] / orders["market_volume"]
''', [("slip_bps", r'''
s = orders.set_index("order_id")["slip_bps"].round(3)
assert _close(s["O1"], 1.295), f"O1 slip = {s['O1']}"
assert _close(s["O2"], 2.158), f"O2 (SELL filled below arrival) should be a +2.158 bps cost; got {s['O2']}"
assert _close(s["O6"], -1.366), f"O6 (SELL filled above arrival) is improvement → negative; got {s['O6']}"
'''), ("slip_ticks", r'''
t = orders.set_index("order_id")["slip_ticks"].round(6)
assert t.tolist() == [3.0, 5.0, 3.0, 15.0, 1.0, -1.0], f"slip_ticks = {t.tolist()}"
'''), ("participation", r'''assert _close(orders["participation"].iloc[0], 500 / 9000)''')],
hints=["sign = np.where(orders['side'] == 'BUY', 1, -1)", "ticks = sign × (fill − arrival) / tick size"],
wrong=r'''
import pandas as pd
TICK = {"ES": 0.25, "NQ": 0.25, "CL": 0.01, "ZN": 1 / 64}
orders = pd.DataFrame({"order_id": ["O1", "O2", "O3", "O4", "O5", "O6"], "symbol": ["ES", "ES", "CL", "NQ", "ZN", "CL"], "side": ["BUY", "SELL", "BUY", "SELL", "BUY", "SELL"], "qty": [500, 200, 150, 80, 1000, 300], "arrival": [5790.00, 5791.50, 73.10, 20105.00, 110.625, 73.20], "avg_fill": [5790.75, 5790.25, 73.13, 20101.25, 110.640625, 73.21], "market_volume": [9000, 5000, 1500, 1600, 20000, 2400]})
orders["slip_bps"] = (orders["avg_fill"] - orders["arrival"]) / orders["arrival"] * 10_000
orders["slip_ticks"] = (orders["avg_fill"] - orders["arrival"]) / orders["symbol"].map(TICK)
orders["participation"] = orders["market_volume"] / orders["qty"]
'''),
ex("Weighted slippage by algo", r'''
Using `orders` with `slip_bps` and a `notional` column (provided), build `by_algo`: Series of **notional-weighted** average slip_bps per algo (rounded to 2 dp), and `best_algo` = algo with the lowest weighted slippage.
''', r'''
import numpy as np
import pandas as pd
MULT = {"ES": 50, "NQ": 20, "CL": 1000, "ZN": 1000}
orders = pd.DataFrame({
    "algo": ["VWAP", "VWAP", "SNIPER", "POV", "SNIPER", "POV"],
    "symbol": ["ES", "ES", "CL", "NQ", "ZN", "CL"],
    "qty": [500, 200, 150, 80, 1000, 300],
    "arrival": [5790.00, 5791.50, 73.10, 20105.00, 110.625, 73.20],
    "slip_bps": [1.295, 2.158, 4.104, 1.865, 1.412, -1.366]})
orders["notional"] = orders["qty"] * orders["arrival"] * orders["symbol"].map(MULT)
by_algo = ...
best_algo = ...
print(by_algo)
''', r'''
import numpy as np
import pandas as pd
MULT = {"ES": 50, "NQ": 20, "CL": 1000, "ZN": 1000}
orders = pd.DataFrame({
    "algo": ["VWAP", "VWAP", "SNIPER", "POV", "SNIPER", "POV"],
    "symbol": ["ES", "ES", "CL", "NQ", "ZN", "CL"],
    "qty": [500, 200, 150, 80, 1000, 300],
    "arrival": [5790.00, 5791.50, 73.10, 20105.00, 110.625, 73.20],
    "slip_bps": [1.295, 2.158, 4.104, 1.865, 1.412, -1.366]})
orders["notional"] = orders["qty"] * orders["arrival"] * orders["symbol"].map(MULT)
orders["w"] = orders["slip_bps"] * orders["notional"]
g = orders.groupby("algo")[["w", "notional"]].sum()
by_algo = (g["w"] / g["notional"]).round(2)
best_algo = by_algo.idxmin()
print(by_algo)
''', [("by_algo", r'''
d = {k: round(float(v), 2) for k, v in dict(by_algo).items()}
assert d == {"POV": 0.55, "SNIPER": 1.65, "VWAP": 1.54}, f"by_algo = {d}" + (" — that's the simple mean; weight by notional" if abs(d.get("VWAP", 0) - 1.73) < 0.01 else "")
'''), ("best_algo", r'''assert best_algo == "POV", f"best_algo = {best_algo!r}"''')],
hints=["Make a column w = slip_bps × notional", "groupby('algo')[['w', 'notional']].sum(), then divide; .idxmin() gives the label of the min"],
wrong=r'''
import pandas as pd
orders = pd.DataFrame({"algo": ["VWAP", "VWAP", "SNIPER", "POV", "SNIPER", "POV"], "slip_bps": [1.295, 2.158, 4.104, 1.865, 1.412, -1.366]})
by_algo = orders.groupby("algo")["slip_bps"].mean().round(2)
best_algo = by_algo.idxmin()
'''),
],
work=r'''
**Take it to work — Client execution-quality (TCA) pack**
- Pull a month of a client's parent orders (arrival mid, avg fill, qty, side, algo, broker, market volume).
- Compute arrival slippage in bps and ticks, participation, and notional-weighted averages by algo, broker, product and order-size bucket.
- Add a "worst 10 orders" table with timestamps so sales can walk the client through outliers.
- Export to CSV/Excel; it's a ready-made talking point for client reviews in ETD sales.
''')

lesson("u3l8", "Take it to work: automate the daily Excel report",
"Replace the copy-paste Excel morning report with a script that builds the tables and writes the file in one click.",
r'''
The pattern for replacing a manual spreadsheet:

1. **Inputs** — read the same files you'd open in Excel (`pd.read_csv`, `pd.read_excel`).
2. **Transform** — one function per table (positions, exposures, breaks…), each returning a DataFrame.
3. **Output** — write CSV/Excel with a date in the filename; keep formatting minimal and consistent.

```python
def build_report(pos, prices, mult) -> pd.DataFrame: ...
report.to_csv(f"risk_{asof:%Y%m%d}.csv", index=False)

# at work, multi-sheet Excel (needs: pip install openpyxl)
with pd.ExcelWriter(f"risk_{asof:%Y%m%d}.xlsx") as xw:
    summary.to_excel(xw, sheet_name="Summary", index=False)
    detail.to_excel(xw, sheet_name="Detail", index=False)
```

Round only at the output step, name columns for humans (`"Gross Notional ($)"`), and sort so the most important rows are on top. Schedule it (cron / Windows Task Scheduler / Airflow) and you've automated a daily task — a strong resume bullet with a measurable result ("saved 45 min/day").

(`openpyxl` isn't bundled in this offline app, so we'll output CSV here.)
''',
examples=[("DataFrame → CSV text", r'''
import pandas as pd
df = pd.DataFrame({"Account": ["HF-A", "HF-B"], "Gross Notional ($)": [69_100_000.0, 97_816_500.0]})
print(df.to_csv(index=False))
''')],
quiz=[q("Best place to round numbers in an automated report?", ["When reading inputs", "In every intermediate step", "Only at the final output/formatting step", "Never"], 2, "Rounding early compounds errors; round once when presenting.")],
exercises=[
ex("build_report()", r'''
Write `build_report(pos, prices, mult)` returning a DataFrame with columns
`["Account", "Symbol", "Qty", "Settle", "Notional", "Daily P&L"]`:
- join positions to prices (left join on symbol); Notional = |qty| × settle × mult; Daily P&L = (settle − prev_settle) × qty × mult
- round Notional and Daily P&L to 0 dp; sort by Account, then Notional descending; reset the index.
''', r'''
import pandas as pd
MULT = {"ES": 50, "NQ": 20, "CL": 1000, "ZN": 1000}
POS = pd.DataFrame({"account": ["HF-BETA", "HF-ALPHA", "HF-ALPHA", "HF-BETA"], "symbol": ["ZN", "ES", "CL", "ES"], "qty": [800, 120, -250, -60]})
PRICES = pd.DataFrame({"symbol": ["ES", "CL", "ZN"], "settle": [5790.0, 73.10, 110.62], "prev_settle": [5850.25, 71.40, 110.50]})

def build_report(pos, prices, mult):
    ...

print(build_report(POS, PRICES, MULT))
''', r'''
import pandas as pd
MULT = {"ES": 50, "NQ": 20, "CL": 1000, "ZN": 1000}
POS = pd.DataFrame({"account": ["HF-BETA", "HF-ALPHA", "HF-ALPHA", "HF-BETA"], "symbol": ["ZN", "ES", "CL", "ES"], "qty": [800, 120, -250, -60]})
PRICES = pd.DataFrame({"symbol": ["ES", "CL", "ZN"], "settle": [5790.0, 73.10, 110.62], "prev_settle": [5850.25, 71.40, 110.50]})

def build_report(pos, prices, mult):
    df = pos.merge(prices, on="symbol", how="left")
    m = df["symbol"].map(mult)
    out = pd.DataFrame({
        "Account": df["account"], "Symbol": df["symbol"], "Qty": df["qty"], "Settle": df["settle"],
        "Notional": (df["qty"].abs() * df["settle"] * m).round(0),
        "Daily P&L": ((df["settle"] - df["prev_settle"]) * df["qty"] * m).round(0)})
    return out.sort_values(["Account", "Notional"], ascending=[True, False]).reset_index(drop=True)

print(build_report(POS, PRICES, MULT))
''', [("columns", r'''
r = build_report(POS, PRICES, MULT)
assert list(r.columns) == ["Account", "Symbol", "Qty", "Settle", "Notional", "Daily P&L"], f"columns = {list(r.columns)}"
'''), ("order", r'''
r = build_report(POS, PRICES, MULT)
assert list(zip(r["Account"], r["Symbol"])) == [("HF-ALPHA", "ES"), ("HF-ALPHA", "CL"), ("HF-BETA", "ZN"), ("HF-BETA", "ES")], f"order = {list(zip(r['Account'], r['Symbol']))} — Account A→Z, then Notional high→low"
'''), ("values", r'''
r = build_report(POS, PRICES, MULT).set_index(["Account", "Symbol"])
assert r.loc[("HF-BETA", "ZN"), "Notional"] == 88_496_000, f"HF-BETA ZN Notional = {r.loc[('HF-BETA','ZN'),'Notional']}"
assert r.loc[("HF-ALPHA", "CL"), "Daily P&L"] == -425_000
assert r.loc[("HF-BETA", "ES"), "Daily P&L"] == 180_750
''')], hints=["pos.merge(prices, on='symbol', how='left')", "sort_values(['Account', 'Notional'], ascending=[True, False])"],
wrong=r'''
import pandas as pd
def build_report(pos, prices, mult):
    df = pos.merge(prices, on="symbol", how="left")
    m = df["symbol"].map(mult)
    out = pd.DataFrame({"Account": df["account"], "Symbol": df["symbol"], "Qty": df["qty"], "Settle": df["settle"], "Notional": (df["qty"] * df["settle"] * m).round(0), "Daily P&L": ((df["settle"] - df["prev_settle"]) * df["qty"] * m).round(0)})
    return out.sort_values(["Account", "Notional"]).reset_index(drop=True)
MULT = {"ES": 50, "NQ": 20, "CL": 1000, "ZN": 1000}
POS = pd.DataFrame({"account": ["HF-BETA", "HF-ALPHA", "HF-ALPHA", "HF-BETA"], "symbol": ["ZN", "ES", "CL", "ES"], "qty": [800, 120, -250, -60]})
PRICES = pd.DataFrame({"symbol": ["ES", "CL", "ZN"], "settle": [5790.0, 73.10, 110.62], "prev_settle": [5850.25, 71.40, 110.50]})
'''),
ex("Write the file + totals row", r'''
Write `save_report(report, asof)` that appends a **TOTAL** row (Account = "TOTAL", Notional and Daily P&L summed, other columns empty/NaN), writes it to `risk_YYYYMMDD.csv` (e.g. `risk_20260930.csv`) without the index, and returns the filename.
`build_report` and data are provided.
''', r'''
import pandas as pd
from datetime import date
MULT = {"ES": 50, "CL": 1000, "ZN": 1000}
POS = pd.DataFrame({"account": ["HF-BETA", "HF-ALPHA", "HF-ALPHA"], "symbol": ["ZN", "ES", "CL"], "qty": [800, 120, -250]})
PRICES = pd.DataFrame({"symbol": ["ES", "CL", "ZN"], "settle": [5790.0, 73.10, 110.62], "prev_settle": [5850.25, 71.40, 110.50]})
def build_report(pos, prices, mult):
    df = pos.merge(prices, on="symbol", how="left"); m = df["symbol"].map(mult)
    return pd.DataFrame({"Account": df["account"], "Symbol": df["symbol"], "Qty": df["qty"], "Settle": df["settle"],
        "Notional": (df["qty"].abs() * df["settle"] * m).round(0), "Daily P&L": ((df["settle"] - df["prev_settle"]) * df["qty"] * m).round(0)})

def save_report(report, asof):
    ...

fname = save_report(build_report(POS, PRICES, MULT), date(2026, 9, 30))
print(open(fname).read())
''', r'''
import pandas as pd
from datetime import date
MULT = {"ES": 50, "CL": 1000, "ZN": 1000}
POS = pd.DataFrame({"account": ["HF-BETA", "HF-ALPHA", "HF-ALPHA"], "symbol": ["ZN", "ES", "CL"], "qty": [800, 120, -250]})
PRICES = pd.DataFrame({"symbol": ["ES", "CL", "ZN"], "settle": [5790.0, 73.10, 110.62], "prev_settle": [5850.25, 71.40, 110.50]})
def build_report(pos, prices, mult):
    df = pos.merge(prices, on="symbol", how="left"); m = df["symbol"].map(mult)
    return pd.DataFrame({"Account": df["account"], "Symbol": df["symbol"], "Qty": df["qty"], "Settle": df["settle"],
        "Notional": (df["qty"].abs() * df["settle"] * m).round(0), "Daily P&L": ((df["settle"] - df["prev_settle"]) * df["qty"] * m).round(0)})

def save_report(report, asof):
    total = pd.DataFrame([{"Account": "TOTAL", "Notional": report["Notional"].sum(), "Daily P&L": report["Daily P&L"].sum()}])
    out = pd.concat([report, total], ignore_index=True)
    fname = f"risk_{asof:%Y%m%d}.csv"
    out.to_csv(fname, index=False)
    return fname

fname = save_report(build_report(POS, PRICES, MULT), date(2026, 9, 30))
print(open(fname).read())
''', [("filename", r'''
from datetime import date
f = save_report(build_report(POS, PRICES, MULT), date(2026, 9, 30))
assert f == "risk_20260930.csv", f"filename = {f!r}"
'''), ("file contents", r'''
import pandas as pd
from datetime import date
f = save_report(build_report(POS, PRICES, MULT), date(2026, 9, 30))
back = pd.read_csv(f)
assert list(back.columns) == ["Account", "Symbol", "Qty", "Settle", "Notional", "Daily P&L"], f"columns = {list(back.columns)} — write with index=False"
assert back["Account"].iloc[-1] == "TOTAL", "Last row should be TOTAL"
assert back["Notional"].iloc[-1] == 141_511_000 and back["Daily P&L"].iloc[-1] == -690_500, f"TOTAL row = {back.iloc[-1].to_dict()}"
assert len(back) == 4
''')], hints=["pd.concat([report, total_df], ignore_index=True)", "f'risk_{asof:%Y%m%d}.csv' formats a date inside an f-string"],
wrong=r'''
import pandas as pd
from datetime import date
MULT = {"ES": 50, "CL": 1000, "ZN": 1000}
POS = pd.DataFrame({"account": ["HF-BETA", "HF-ALPHA", "HF-ALPHA"], "symbol": ["ZN", "ES", "CL"], "qty": [800, 120, -250]})
PRICES = pd.DataFrame({"symbol": ["ES", "CL", "ZN"], "settle": [5790.0, 73.10, 110.62], "prev_settle": [5850.25, 71.40, 110.50]})
def build_report(pos, prices, mult):
    df = pos.merge(prices, on="symbol", how="left"); m = df["symbol"].map(mult)
    return pd.DataFrame({"Account": df["account"], "Symbol": df["symbol"], "Qty": df["qty"], "Settle": df["settle"], "Notional": (df["qty"].abs() * df["settle"] * m).round(0), "Daily P&L": ((df["settle"] - df["prev_settle"]) * df["qty"] * m).round(0)})
def save_report(report, asof):
    fname = f"risk_{asof}.csv"
    report.to_csv(fname)
    return fname
'''),
],
work=r'''
**Take it to work — Automated morning risk report**
- Pick one spreadsheet you rebuild every morning (positions/P&L/exposure by account).
- Rebuild each tab as a function returning a DataFrame; write all tabs with `pd.ExcelWriter` (`pip install openpyxl`) to `risk_YYYYMMDD.xlsx`.
- Add a "checks" tab: row counts in vs out, positions with no price, NaNs — so you trust it more than the manual version.
- Schedule it and track the time saved; that number goes on your resume.
''')
