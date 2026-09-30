from dsl import *

DATA = r'''import io
import numpy as np
import pandas as pd
ACCOUNTS = pd.read_csv(io.StringIO("""account,client,netting
A1,ALPHA CAPITAL,True
A2,ALPHA CAPITAL,True
B1,BETA PARTNERS,False
G1,GAMMA FAMILY OFFICE,False
G2,GAMMA FAMILY OFFICE,False
"""))
POSITIONS = pd.read_csv(io.StringIO("""account,symbol,qty
A1,ES,120
A1,NQ,-40
A1,CL,-250
A2,ES,-30
B1,ZN,800
B1,ES,-60
B1,GC,35
G1,CL,90
G1,ZN,-150
G2,ES,15
G2,NG,-40
"""))
PRODUCTS = pd.DataFrame({
    "symbol": ["ES", "NQ", "CL", "ZN", "GC", "NG"],
    "mult":   [50, 20, 1000, 1000, 100, 10000],
    "settle": [5790.0, 20100.0, 73.10, 110.62, 2655.0, 2.85],
    "scan_range_pct": [0.06, 0.07, 0.12, 0.02, 0.07, 0.20],   # simplified margin: % of notional
    "open_interest": [2_100_000, 250_000, 1_600_000, 4_500_000, 480_000, 1_300_000]})
COLLATERAL = pd.read_csv(io.StringIO("""account,asset,mv,haircut
A1,UST_2Y,14000000,0.02
A1,CASH,2000000,0.0
A2,CASH,300000,0.0
B1,UST_10Y,9000000,0.03
B1,EQ,3000000,0.25
G1,CASH,2500000,0.0
G2,UST_5Y,350000,0.02
"""))
SHOCKS = pd.DataFrame({
    "ES": [-0.12, -0.05, -0.20], "NQ": [-0.15, -0.06, -0.25], "CL": [-0.30, 0.25, -0.40],
    "ZN": [0.025, -0.03, 0.04], "GC": [0.05, 0.10, 0.08], "NG": [0.30, 0.40, -0.25]},
    index=["equity_crash", "stagflation", "gfc_style"])'''

unit("u8", "Capstone: Prime Risk Report", "Build a small end-to-end prime brokerage risk report — exposures, margin surplus/deficit, limits, stress — and turn it into a portfolio piece.")

lesson("u8l1", "Capstone 1: exposures & margin surplus/deficit",
"Build the first half of a client risk report from raw files: exposures by client and margin surplus/deficit by account.",
r'''
You now have every tool you need. The capstone data (all synthetic) has five tables: `ACCOUNTS`, `POSITIONS`, `PRODUCTS`, `COLLATERAL`, `SHOCKS`.

**Part 1 deliverables**
1. `enrich(positions, products)` → positions with `notional` (signed = qty × settle × mult) and `margin` (|notional| × scan_range_pct — a deliberately simplified stand-in for SPAN).
2. `account_margin(pos, collateral, accounts)` → per account: `client, requirement, collateral_value, excess`.

Work in small functions; each builds on the previous. This is exactly how you'd structure it in a repo (`risk/exposures.py`, `risk/margin.py`) with tests for each.

> Design note to say in an interview: "margin" here is a placeholder model; in production you'd plug in CCP SPAN/SPAN 2 requirements or a house model, and keep the interface the same.
''',
examples=[("Peek at the data", DATA + r'''

print(POSITIONS.merge(PRODUCTS, on="symbol").head())
print(COLLATERAL.groupby("account")["mv"].sum())
''')],
quiz=[q("Why pass DataFrames into functions instead of using the global tables inside them?", ["Speed", "Testability and reuse — you can feed test data or tomorrow's files", "Python requires it", "Less typing"], 1, "Explicit inputs make functions pure and testable.")],
exercises=[
ex("enrich()", r'''
Write `enrich(positions, products)` returning positions merged with products plus columns `notional` (signed) and `margin` (|notional| × scan_range_pct). Keep all positions (left join); validate many-to-one.
''', DATA + r'''

def enrich(positions, products):
    ...

pos = enrich(POSITIONS, PRODUCTS)
print(pos[["account", "symbol", "notional", "margin"]])
''', DATA + r'''

def enrich(positions, products):
    df = positions.merge(products, on="symbol", how="left", validate="many_to_one")
    df["notional"] = df["qty"] * df["settle"] * df["mult"]
    df["margin"] = df["notional"].abs() * df["scan_range_pct"]
    return df

pos = enrich(POSITIONS, PRODUCTS)
print(pos[["account", "symbol", "notional", "margin"]])
''', [("shape", r'''
p = enrich(POSITIONS, PRODUCTS)
assert len(p) == len(POSITIONS) and {"notional", "margin"} <= set(p.columns), "keep every position and add notional & margin"
'''), ("values", r'''
p = enrich(POSITIONS, PRODUCTS).set_index(["account", "symbol"])
assert _close(p.loc[("A1", "CL"), "notional"], -18_275_000), f"A1 CL notional = {p.loc[('A1','CL'),'notional']:,.0f} (signed)"
assert _close(p.loc[("A1", "CL"), "margin"], 2_193_000), f"A1 CL margin = {p.loc[('A1','CL'),'margin']:,.0f} = |notional| × 12%"
assert _close(p["margin"].sum(), 10_996_585.0), f"total margin = {p['margin'].sum():,.0f}"
''')], hints=["positions.merge(products, on='symbol', how='left', validate='many_to_one')", "margin uses .abs() of notional"],
wrong=DATA + r'''
def enrich(positions, products):
    df = positions.merge(products, on="symbol")
    df["notional"] = df["qty"] * df["settle"] * df["mult"]
    df["margin"] = df["notional"] * df["scan_range_pct"]
    return df
'''),
ex("account_margin()", r'''
Write `account_margin(pos, collateral, accounts)` returning a DataFrame indexed by account (all accounts in `accounts`) with columns `client, requirement, collateral_value, excess`, sorted by excess ascending. requirement = Σ margin; collateral_value = Σ mv × (1 − haircut).
''', DATA + r'''

def enrich(positions, products):
    df = positions.merge(products, on="symbol", how="left", validate="many_to_one")
    df["notional"] = df["qty"] * df["settle"] * df["mult"]
    df["margin"] = df["notional"].abs() * df["scan_range_pct"]
    return df

def account_margin(pos, collateral, accounts):
    ...

print(account_margin(enrich(POSITIONS, PRODUCTS), COLLATERAL, ACCOUNTS))
''', DATA + r'''

def enrich(positions, products):
    df = positions.merge(products, on="symbol", how="left", validate="many_to_one")
    df["notional"] = df["qty"] * df["settle"] * df["mult"]
    df["margin"] = df["notional"].abs() * df["scan_range_pct"]
    return df

def account_margin(pos, collateral, accounts):
    req = pos.groupby("account")["margin"].sum().rename("requirement")
    cv = (collateral["mv"] * (1 - collateral["haircut"])).groupby(collateral["account"]).sum().rename("collateral_value")
    out = accounts.set_index("account")[["client"]].join(req).join(cv).fillna({"requirement": 0.0, "collateral_value": 0.0})
    out["excess"] = out["collateral_value"] - out["requirement"]
    return out.sort_values("excess")

print(account_margin(enrich(POSITIONS, PRODUCTS), COLLATERAL, ACCOUNTS))
''', [("structure", r'''
m = account_margin(enrich(POSITIONS, PRODUCTS), COLLATERAL, ACCOUNTS)
assert list(m.columns) == ["client", "requirement", "collateral_value", "excess"], f"columns = {list(m.columns)}"
assert sorted(m.index) == ["A1", "A2", "B1", "G1", "G2"], f"index = {list(m.index)}"
'''), ("values", r'''
m = account_margin(enrich(POSITIONS, PRODUCTS), COLLATERAL, ACCOUNTS)
assert _close(m.loc["B1", "requirement"], 3_462_595.0), f"B1 requirement = {m.loc['B1','requirement']:,.0f}"
assert _close(m.loc["B1", "collateral_value"], 10_980_000), f"B1 collateral = {m.loc['B1','collateral_value']:,.0f}"
assert _close(m.loc["G2", "excess"], 343_000 - (15 * 5790 * 50 * 0.06 + 40 * 2.85 * 10000 * 0.20)), f"G2 excess = {m.loc['G2','excess']:,.0f}"
'''), ("sorted", r'''
m = account_margin(enrich(POSITIONS, PRODUCTS), COLLATERAL, ACCOUNTS)
assert list(m["excess"]) == sorted(m["excess"]), "sort by excess ascending (worst first)"
assert m.index[0] == "A2", f"worst account should be A2; got {m.index[0]}"
''')], hints=["pos.groupby('account')['margin'].sum()", "accounts.set_index('account')[['client']].join(req).join(cv)"],
wrong=DATA + r'''
def enrich(positions, products):
    df = positions.merge(products, on="symbol", how="left")
    df["notional"] = df["qty"] * df["settle"] * df["mult"]; df["margin"] = df["notional"].abs() * df["scan_range_pct"]
    return df
def account_margin(pos, collateral, accounts):
    req = pos.groupby("account")["margin"].sum().rename("requirement")
    cv = collateral.groupby("account")["mv"].sum().rename("collateral_value")
    out = accounts.set_index("account")[["client"]].join(req).join(cv)
    out["excess"] = out["collateral_value"] - out["requirement"]
    return out
'''),
])

lesson("u8l2", "Capstone 2: limits, stress & the assembled report",
"Finish the report: client-level calls, stress losses vs excess, concentration flags, and a single build_report() entry point.",
r'''
**Part 2 deliverables**
1. `client_calls(acct_margin, accounts)` — respects netting flags (u5l6).
2. `stress_by_account(pos, shocks)` — stress P&L per account per scenario and worst loss (u7l4).
3. `build_report(...)` — orchestrates everything and returns a **dict of DataFrames** plus a one-line `summary` string.

A dict of DataFrames is a great interface: easy to test, easy to export (`for name, df in report.items(): df.to_csv(...)`), and easy to render later (Streamlit, Dash, or a Foundry workshop).
''',
examples=[("Dict of DataFrames → files", r'''
import pandas as pd
report = {"summary_table": pd.DataFrame({"a": [1]}), "breaches": pd.DataFrame({"b": [2]})}
for name, df in report.items():
    df.to_csv(f"{name}.csv", index=False)
    print("wrote", f"{name}.csv")
''')],
quiz=[q("Accounts G1 (excess +$1.0m) and G2 (−$0.3m) belong to a client with **no** netting agreement. Call?", ["$0", "$0.3m", "$0.7m", "$1.3m"], 1, "Without netting, G2's deficit is called on its own.")],
exercises=[
ex("stress_by_account()", r'''
Write `stress_by_account(pos, shocks)` where `pos` is the enriched positions (with signed `notional`). Return a DataFrame indexed by account with one column per scenario (stress P&L = Σ notional × shock) plus `worst_loss` (the worst loss as a positive number, floored at 0) and `worst_scenario`.
''', DATA + r'''

def enrich(positions, products):
    df = positions.merge(products, on="symbol", how="left", validate="many_to_one")
    df["notional"] = df["qty"] * df["settle"] * df["mult"]
    df["margin"] = df["notional"].abs() * df["scan_range_pct"]
    return df

def stress_by_account(pos, shocks):
    ...

print(stress_by_account(enrich(POSITIONS, PRODUCTS), SHOCKS).round(-3))
''', DATA + r'''

def enrich(positions, products):
    df = positions.merge(products, on="symbol", how="left", validate="many_to_one")
    df["notional"] = df["qty"] * df["settle"] * df["mult"]
    df["margin"] = df["notional"].abs() * df["scan_range_pct"]
    return df

def stress_by_account(pos, shocks):
    expo = pos.pivot_table(index="account", columns="symbol", values="notional", aggfunc="sum", fill_value=0.0)
    expo = expo.reindex(columns=shocks.columns, fill_value=0.0)
    out = expo @ shocks.T
    scen = list(shocks.index)
    out["worst_loss"] = (-out[scen].min(axis=1)).clip(lower=0)
    out["worst_scenario"] = out[scen].idxmin(axis=1)
    return out

print(stress_by_account(enrich(POSITIONS, PRODUCTS), SHOCKS).round(-3))
''', [("structure", r'''
s = stress_by_account(enrich(POSITIONS, PRODUCTS), SHOCKS)
assert {"equity_crash", "stagflation", "gfc_style", "worst_loss", "worst_scenario"} <= set(s.columns), f"columns = {list(s.columns)}"
assert sorted(s.index) == ["A1", "A2", "B1", "G1", "G2"]
'''), ("values", r'''
s = stress_by_account(enrich(POSITIONS, PRODUCTS), SHOCKS)
assert _close(s.loc["A1", "equity_crash"], 34_740_000 * -0.12 + -16_080_000 * -0.15 + -18_275_000 * -0.30), f"A1 equity_crash = {s.loc['A1','equity_crash']:,.0f}"
assert s.loc["G2", "worst_scenario"] == "equity_crash" and _close(s.loc["G2", "worst_loss"], 4_342_500 * 0.12 + 1_140_000 * 0.30), f"G2 worst = {s.loc['G2','worst_scenario']} {s.loc['G2','worst_loss']:,.0f}"
assert (s["worst_loss"] >= 0).all() and s.loc["A2", "worst_loss"] == 0, "worst_loss is floored at 0 (A2 gains in every scenario)"
''')], hints=["Pivot notional to accounts × symbols, reindex to shocks.columns", "expo @ shocks.T; then min/idxmin across scenario columns"],
wrong=DATA + r'''
def enrich(positions, products):
    df = positions.merge(products, on="symbol", how="left")
    df["notional"] = df["qty"] * df["settle"] * df["mult"]; df["margin"] = df["notional"].abs() * df["scan_range_pct"]
    return df
def stress_by_account(pos, shocks):
    expo = pos.pivot_table(index="account", columns="symbol", values="notional", aggfunc="sum", fill_value=0.0).abs()
    expo = expo.reindex(columns=shocks.columns, fill_value=0.0)
    out = expo @ shocks.T
    out["worst_loss"] = -out.min(axis=1); out["worst_scenario"] = out.iloc[:, :3].idxmin(axis=1)
    return out
'''),
ex("build_report()", r'''
Write `build_report(accounts, positions, products, collateral, shocks)` returning a dict with keys:
- `"accounts"`: account_margin table (provided function) joined with `worst_loss` from stress, plus `stress_uncovered` = max(0, worst_loss − max(excess, 0))
- `"calls"`: Series client → call amount (netting rules as in u5l6) — only clients with call > 0
- `"concentration"`: DataFrame of symbols where |firm net qty| / open_interest > 0.0001 (i.e. > 0.01%), columns `symbol, net_qty, oi_pct`
- `"summary"`: string `"{n} clients | calls {k} totaling ${total:,.0f} | worst stress: {account} ${loss:,.0f}"` where the worst account is the one with the largest `worst_loss`
''', DATA + r'''

def enrich(positions, products):
    df = positions.merge(products, on="symbol", how="left", validate="many_to_one")
    df["notional"] = df["qty"] * df["settle"] * df["mult"]
    df["margin"] = df["notional"].abs() * df["scan_range_pct"]
    return df

def account_margin(pos, collateral, accounts):
    req = pos.groupby("account")["margin"].sum().rename("requirement")
    cv = (collateral["mv"] * (1 - collateral["haircut"])).groupby(collateral["account"]).sum().rename("collateral_value")
    out = accounts.set_index("account")[["client"]].join(req).join(cv).fillna({"requirement": 0.0, "collateral_value": 0.0})
    out["excess"] = out["collateral_value"] - out["requirement"]
    return out.sort_values("excess")

def stress_by_account(pos, shocks):
    expo = pos.pivot_table(index="account", columns="symbol", values="notional", aggfunc="sum", fill_value=0.0).reindex(columns=shocks.columns, fill_value=0.0)
    out = expo @ shocks.T
    scen = list(shocks.index)
    out["worst_loss"] = (-out[scen].min(axis=1)).clip(lower=0)
    out["worst_scenario"] = out[scen].idxmin(axis=1)
    return out

def build_report(accounts, positions, products, collateral, shocks):
    ...

rep = build_report(ACCOUNTS, POSITIONS, PRODUCTS, COLLATERAL, SHOCKS)
print(rep["summary"])
''', DATA + r'''

def enrich(positions, products):
    df = positions.merge(products, on="symbol", how="left", validate="many_to_one")
    df["notional"] = df["qty"] * df["settle"] * df["mult"]
    df["margin"] = df["notional"].abs() * df["scan_range_pct"]
    return df

def account_margin(pos, collateral, accounts):
    req = pos.groupby("account")["margin"].sum().rename("requirement")
    cv = (collateral["mv"] * (1 - collateral["haircut"])).groupby(collateral["account"]).sum().rename("collateral_value")
    out = accounts.set_index("account")[["client"]].join(req).join(cv).fillna({"requirement": 0.0, "collateral_value": 0.0})
    out["excess"] = out["collateral_value"] - out["requirement"]
    return out.sort_values("excess")

def stress_by_account(pos, shocks):
    expo = pos.pivot_table(index="account", columns="symbol", values="notional", aggfunc="sum", fill_value=0.0).reindex(columns=shocks.columns, fill_value=0.0)
    out = expo @ shocks.T
    scen = list(shocks.index)
    out["worst_loss"] = (-out[scen].min(axis=1)).clip(lower=0)
    out["worst_scenario"] = out[scen].idxmin(axis=1)
    return out

def client_calls(acct, accounts):
    df = acct.join(accounts.set_index("account")[["netting"]])
    df["deficit"] = (-df["excess"]).clip(lower=0)
    calls = {}
    for client, g in df.groupby("client"):
        calls[client] = max(0.0, -g["excess"].sum()) if bool(g["netting"].iloc[0]) else g["deficit"].sum()
    s = pd.Series(calls)
    return s[s > 0].sort_values(ascending=False)

def build_report(accounts, positions, products, collateral, shocks):
    pos = enrich(positions, products)
    acct = account_margin(pos, collateral, accounts)
    st = stress_by_account(pos, shocks)
    acct = acct.join(st[["worst_loss"]]).fillna({"worst_loss": 0.0})
    acct["stress_uncovered"] = (acct["worst_loss"] - acct["excess"].clip(lower=0)).clip(lower=0)
    calls = client_calls(acct, accounts)
    firm = pos.groupby("symbol").agg(net_qty=("qty", "sum"), oi=("open_interest", "first")).reset_index()
    firm["oi_pct"] = firm["net_qty"].abs() / firm["oi"]
    conc = firm.loc[firm["oi_pct"] > 0.0001, ["symbol", "net_qty", "oi_pct"]].reset_index(drop=True)
    w = acct["worst_loss"].idxmax()
    summary = (f"{accounts['client'].nunique()} clients | calls {len(calls)} totaling ${calls.sum():,.0f} | "
               f"worst stress: {w} ${acct.loc[w, 'worst_loss']:,.0f}")
    return {"accounts": acct, "calls": calls, "concentration": conc, "summary": summary}

rep = build_report(ACCOUNTS, POSITIONS, PRODUCTS, COLLATERAL, SHOCKS)
print(rep["summary"])
''', [("keys", r'''
rep = build_report(ACCOUNTS, POSITIONS, PRODUCTS, COLLATERAL, SHOCKS)
assert set(rep) == {"accounts", "calls", "concentration", "summary"}, f"keys = {set(rep)}"
'''), ("accounts table", r'''
rep = build_report(ACCOUNTS, POSITIONS, PRODUCTS, COLLATERAL, SHOCKS)
a = rep["accounts"]
assert {"requirement", "collateral_value", "excess", "worst_loss", "stress_uncovered"} <= set(a.columns), f"columns = {list(a.columns)}"
assert (a["stress_uncovered"] >= 0).all()
assert _close(a.loc["G2", "stress_uncovered"], a.loc["G2", "worst_loss"]), "G2 has negative excess → uncovered = its full worst_loss"
'''), ("calls", r'''
rep = build_report(ACCOUNTS, POSITIONS, PRODUCTS, COLLATERAL, SHOCKS)
c = rep["calls"]
assert "BETA PARTNERS" not in c.index, "BETA has surplus → no call"
assert "GAMMA FAMILY OFFICE" in c.index and "ALPHA CAPITAL" not in c.index, f"calls = {c.to_dict()} — ALPHA nets A1's surplus against A2; GAMMA can't net"
'''), ("concentration & summary", r'''
rep = build_report(ACCOUNTS, POSITIONS, PRODUCTS, COLLATERAL, SHOCKS)
assert rep["concentration"]["symbol"].tolist() == ["NQ", "ZN"], f"concentration symbols = {rep['concentration']['symbol'].tolist()}"
s = rep["summary"]
assert s == "3 clients | calls 1 totaling $145,550 | worst stress: A1 $5,340,950", f"summary = {s!r}"
''')], hints=["Reuse the provided functions; write client_calls() like u5l6.", "firm = pos.groupby('symbol').agg(net_qty=('qty','sum'), oi=('open_interest','first'))"],
wrong=DATA + r'''
def build_report(accounts, positions, products, collateral, shocks):
    return {"accounts": accounts, "calls": pd.Series(dtype=float), "concentration": pd.DataFrame(), "summary": "report"}
'''),
])

lesson("u8l3", "Capstone 3: make it a portfolio piece",
"Turn the capstone (and Clearing Lens) into a GitHub repo that proves you can write production-minded Python.",
r'''
Interviewers (Palantir, SpaceX, hedge funds) skim a repo in 2 minutes. Make those minutes count:

**Repo layout**
```
prime-risk-report/
  README.md            # problem, screenshot, how to run, design choices
  pyproject.toml       # deps: pandas, numpy, pytest
  risk/
    exposures.py       # enrich()
    margin.py          # account_margin(), client_calls()
    stress.py          # stress_by_account()
    report.py          # build_report(), CLI entry point
  tests/
    test_margin.py     # pytest: signs, netting, edge cases
  data/sample/*.csv    # synthetic inputs only — never client data
```

**README must answer**: What problem? (who is short collateral, which clients breach stress) · How to run (`python -m risk.report data/sample`) · Design choices & simplifications (simplified margin model, netting rules) · What you'd do next (SPAN 2 feed, scheduling, dashboard).

**Talking points** (practice out loud): "I spent six years in clearing/financing risk; I built this to automate the questions I used to answer in Excel: … The trickiest part was netting rules; I encoded them as data (a netting flag per client) and tested both branches."

Never include real client names, positions or SG data — synthetic only, and check your employer's policies.
''',
examples=[("Generate a README table from a DataFrame", r'''
import pandas as pd
df = pd.DataFrame({"account": ["A2", "G2"], "excess": [-0.3e6, -0.1e6]})
lines = ["| account | excess |", "|---|---|"] + [f"| {r.account} | {r.excess:,.0f} |" for r in df.itertuples()]
print("\n".join(lines))
''')],
quiz=[q("Best one-line pitch for the repo in an interview?", ["\"I know pandas.\"", "\"I automated a daily margin-shortfall and stress report I used to do in Excel — 5 input files to a tested report in one command.\"", "\"It's a script.\"", "\"I followed a tutorial.\""], 1, "Lead with the business problem and the measurable outcome, then the tech.")],
exercises=[
ex("Markdown table helper", r'''
Write `to_markdown_table(df, float_fmt="{:,.0f}")` returning a GitHub-markdown table string (header row, `|---|` separator row, one row per record). Floats use `float_fmt`; other values use `str()`. Rows joined with `"\n"`.
''', r'''
import pandas as pd

def to_markdown_table(df, float_fmt="{:,.0f}"):
    ...

print(to_markdown_table(pd.DataFrame({"account": ["A2", "G2"], "excess": [-300000.0, -104500.5]})))
''', r'''
import pandas as pd

def to_markdown_table(df, float_fmt="{:,.0f}"):
    def fmt(v):
        return float_fmt.format(v) if isinstance(v, float) else str(v)
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines)

print(to_markdown_table(pd.DataFrame({"account": ["A2", "G2"], "excess": [-300000.0, -104500.5]})))
''', [("table", r'''
import pandas as pd
got = to_markdown_table(pd.DataFrame({"account": ["A2", "G2"], "excess": [-300000.0, -104500.5]}))
exp = "| account | excess |\n|---|---|\n| A2 | -300,000 |\n| G2 | -104,500 |"
assert got == exp, f"got:\n{got}\n\nexpected:\n{exp}"
'''), ("ints and custom format", r'''
import pandas as pd
got = to_markdown_table(pd.DataFrame({"sym": ["ES"], "qty": [5], "px": [5790.25]}), float_fmt="{:.2f}")
assert got.splitlines()[2] == "| ES | 5 | 5790.25 |", got
''')], hints=["Header: '| ' + ' | '.join(df.columns) + ' |'", "df.itertuples(index=False) yields plain tuples; Python floats from numpy are np.float64 — which is a subclass of float, so isinstance works."],
wrong=r'''
def to_markdown_table(df, float_fmt="{:,.0f}"):
    return df.to_string()
'''),
ex("Tests for the report", r'''
Write **at least 3** pytest-style `test_` functions for `client_calls(acct, accounts)` (provided). The checker runs them against the correct implementation (must pass) and two buggy versions: one that **always nets** and one that **never nets**. Your tests must catch both.
''', r'''
import pandas as pd

def client_calls(acct, accounts):
    df = acct.join(accounts.set_index("account")[["netting"]])
    df["deficit"] = (-df["excess"]).clip(lower=0)
    calls = {}
    for client, g in df.groupby("client"):
        calls[client] = max(0.0, -g["excess"].sum()) if bool(g["netting"].iloc[0]) else g["deficit"].sum()
    s = pd.Series(calls)
    return s[s > 0].sort_values(ascending=False)

def make(rows):
    """rows: list of (account, client, excess, netting) -> (acct, accounts)"""
    accounts = pd.DataFrame([(a, c, n) for a, c, e, n in rows], columns=["account", "client", "netting"])
    acct = pd.DataFrame([(a, c, e) for a, c, e, n in rows], columns=["account", "client", "excess"]).set_index("account")
    return acct, accounts

def test_example():
    acct, accounts = make([("X1", "X", -100.0, False)])
    assert client_calls(acct, accounts)["X"] == 100.0
''', r'''
import pandas as pd

def client_calls(acct, accounts):
    df = acct.join(accounts.set_index("account")[["netting"]])
    df["deficit"] = (-df["excess"]).clip(lower=0)
    calls = {}
    for client, g in df.groupby("client"):
        calls[client] = max(0.0, -g["excess"].sum()) if bool(g["netting"].iloc[0]) else g["deficit"].sum()
    s = pd.Series(calls)
    return s[s > 0].sort_values(ascending=False)

def make(rows):
    accounts = pd.DataFrame([(a, c, n) for a, c, e, n in rows], columns=["account", "client", "netting"])
    acct = pd.DataFrame([(a, c, e) for a, c, e, n in rows], columns=["account", "client", "excess"]).set_index("account")
    return acct, accounts

def test_netting_client_offsets_surplus():
    acct, accounts = make([("A1", "A", 300.0, True), ("A2", "A", -500.0, True)])
    assert client_calls(acct, accounts)["A"] == 200.0

def test_non_netting_client_pays_each_deficit():
    acct, accounts = make([("G1", "G", 300.0, False), ("G2", "G", -500.0, False)])
    assert client_calls(acct, accounts)["G"] == 500.0

def test_no_call_when_net_surplus():
    acct, accounts = make([("A1", "A", 800.0, True), ("A2", "A", -500.0, True)])
    assert "A" not in client_calls(acct, accounts).index
''', [("your tests pass on the correct code", r'''
tests = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
assert len(tests) >= 3, f"Found {len(tests)} test_ functions; write at least 3"
for t in tests:
    try:
        t()
    except AssertionError:
        raise AssertionError(f"{t.__name__} fails against the CORRECT client_calls — check the expected value")
'''), ("catch: always nets", r'''
import pandas as pd
_good = client_calls
def _always(acct, accounts):
    s = (-acct.groupby("client")["excess"].sum()).clip(lower=0)
    return s[s > 0].sort_values(ascending=False)
globals()["client_calls"] = _always
caught = False
for k, t in list(globals().items()):
    if k.startswith("test_") and callable(t):
        try: t()
        except Exception: caught = True
globals()["client_calls"] = _good
assert caught, "No test failed when netting was applied to EVERY client. Add a non-netting client with a surplus account and a deficit account."
'''), ("catch: never nets", r'''
import pandas as pd
_good = client_calls
def _never(acct, accounts):
    s = (-acct["excess"]).clip(lower=0).groupby(acct["client"]).sum()
    return s[s > 0].sort_values(ascending=False)
globals()["client_calls"] = _never
caught = False
for k, t in list(globals().items()):
    if k.startswith("test_") and callable(t):
        try: t()
        except Exception: caught = True
globals()["client_calls"] = _good
assert caught, "No test failed when netting was IGNORED. Add a netting client whose surplus offsets a deficit."
''')], hints=["Use make([...]) to build tiny inputs.", "One netting client with +300 / −500 → call 200; one non-netting → 500."],
wrong=r'''
import pandas as pd
def client_calls(acct, accounts):
    df = acct.join(accounts.set_index("account")[["netting"]])
    df["deficit"] = (-df["excess"]).clip(lower=0)
    calls = {c: (max(0.0, -g["excess"].sum()) if bool(g["netting"].iloc[0]) else g["deficit"].sum()) for c, g in df.groupby("client")}
    s = pd.Series(calls); return s[s > 0]
def make(rows):
    accounts = pd.DataFrame([(a, c, n) for a, c, e, n in rows], columns=["account", "client", "netting"])
    acct = pd.DataFrame([(a, c, e) for a, c, e, n in rows], columns=["account", "client", "excess"]).set_index("account")
    return acct, accounts
def test_one():
    acct, accounts = make([("X1", "X", -100.0, False)]); assert client_calls(acct, accounts)["X"] == 100.0
def test_two():
    acct, accounts = make([("Y1", "Y", -50.0, True)]); assert client_calls(acct, accounts)["Y"] == 50.0
def test_three():
    acct, accounts = make([("Z1", "Z", 10.0, True)]); assert "Z" not in client_calls(acct, accounts).index
'''),
],
work=r'''
**Take it to work — Portfolio repo: prime-risk-report (and Clearing Lens v2)**
- Create a public GitHub repo with the layout in this lesson, synthetic data only, `pytest` tests and a GitHub Actions workflow that runs them.
- README: problem → screenshot of the report → how to run → design choices → next steps. Link it on your resume and LinkedIn.
- Add a 90-second walkthrough you can give out loud (problem, approach, a tradeoff, what you'd do with more time).
- Stretch: a Streamlit page that renders `build_report()`; a CLI `python -m risk.report --asof 2026-09-30`.
''')
