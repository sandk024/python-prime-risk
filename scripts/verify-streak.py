"""Browser tests for the streak system with a simulated clock (Playwright page.clock), iPhone 14 viewport.
1) migration of pre-streak progress  2) evening 'at risk' banner  3) freeze notice after a missed day
4) daily goal -> confetti + toast; reduced-motion -> no confetti  5) badges screen renders."""
import sys, json, datetime as dt
from playwright.sync_api import sync_playwright
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/"
SHOTS = sys.argv[2] if len(sys.argv) > 2 else None
ok = 0
def check(cond, msg):
    global ok
    if not cond: raise SystemExit("FAIL: " + msg)
    ok += 1; print("ok  ", msg, flush=True)
def iso(d): return d.strftime("%Y-%m-%d")
with sync_playwright() as p:
    dev = dict(p.devices["iPhone 14"]); dev.pop("default_browser_type", None)
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    def ctx_at(when, reduced=False):
        c = b.new_context(**dev, reduced_motion="reduce" if reduced else "no-preference")
        pg = c.new_page(); pg.clock.install(time=when); return c, pg
    now = dt.datetime(2026, 10, 7, 20, 30)          # Wed evening, local time
    today, yday = now.date(), now.date() - dt.timedelta(days=1)
    # 1) migration: old-format progress (no game) with lessons completed on 3 consecutive days up to yesterday
    old = {"version": 1, "completed": {"u1l1": iso(yday - dt.timedelta(days=2)), "u1l2": iso(yday - dt.timedelta(days=1)), "u1l3": iso(yday)},
           "ex": {"u1l1:0": {"attempts": 1, "passed": True, "passedOn": iso(yday - dt.timedelta(days=2))}}, "quiz": {}, "last": "u1l3", "days": [iso(yday)], "created": "2026-10-01"}
    c, pg = ctx_at(now)
    pg.goto(URL); pg.evaluate("(o) => localStorage.setItem('ppr.progress.v1', JSON.stringify(o))", old); pg.reload()
    pg.wait_for_selector(".streakcard")
    P = pg.evaluate("JSON.parse(localStorage.getItem('ppr.progress.v1'))")
    check(P["completed"] == old["completed"] and P["ex"]["u1l1:0"]["passed"], "migration keeps completed lessons and exercises")
    check(sorted(P["game"]["active"]) == sorted(old["completed"].values()) and P["game"]["best"] == 3, f"migration back-fills active days + best streak (xp={P['game']['xp']})")
    check(pg.locator(".sc-num b").inner_text() == "3", "streak card shows 3-day streak")
    # 2) evening banner (today not done, 20:30)
    check(pg.locator(".notice.risk").count() == 1 and "3-day streak is at risk" in pg.locator(".notice.risk").inner_text(), "evening 'streak at risk' banner shown")
    check(pg.locator(".badge-tile").count() == 0 and "Badges" in pg.locator(".streakcard").inner_text(), "badges link on streak card")
    if SHOTS: pg.wait_for_timeout(400); pg.locator(".notice.risk").screenshot(path=f"{SHOTS}/streak-at-risk-banner.png")
    # 4) daily goal: complete a lesson today -> confetti + toast, banner gone, streak 4
    pg.evaluate("""() => { const P = JSON.parse(localStorage.getItem('ppr.progress.v1')); P.ex['u1l4:0'] = {attempts:1, passed:true}; localStorage.setItem('ppr.progress.v1', JSON.stringify(P)); }""")
    pg.goto(URL + "#/l/u1l4"); pg.reload(); pg.wait_for_selector("text=Mark lesson complete")
    pg.click("text=Mark lesson complete")
    pg.wait_for_selector("canvas.confetti", state="attached", timeout=3000)
    check(True, "confetti canvas shown when daily goal met")
    pg.wait_for_function("() => document.querySelector('#toast').textContent.includes('Daily goal met')", timeout=8000)
    check(True, "toast: " + pg.locator("#toast").inner_text())
    pg.clock.run_for(4000)
    pg.goto(URL + "#/"); pg.wait_for_selector(".streakcard")
    check(pg.locator(".sc-num b").inner_text() == "4" and pg.locator(".notice.risk").count() == 0, "streak 4 and banner gone after today's lesson")
    g = pg.evaluate("JSON.parse(localStorage.getItem('ppr.progress.v1')).game")
    check("first-lesson" in g["badges"] and "streak-3" in g["badges"], f"badges earned: {sorted(g['badges'])}")
    pg.click("text=Mark lesson complete") if pg.locator("text=Mark lesson complete").count() else None
    c.close()
    # 3) freeze: 7-day streak ending 2 days ago (1 freeze), open today -> freeze notice, streak kept
    c, pg = ctx_at(dt.datetime(2026, 10, 7, 9, 0))
    days = [iso(dt.date(2026, 10, 5) - dt.timedelta(days=i)) for i in range(7)]  # Sep 29..Oct 5, missed Oct 6
    game = {"v": 1, "active": {d: {"lessons": 1, "review": False} for d in days}, "frozen": {}, "freezes": 1, "best": 7, "xp": 700, "xpByDay": {d: 100 for d in days}, "badges": {}, "awarded": {}, "lastSeen": "2026-10-05", "notices": []}
    prog = {"version": 1, "completed": {}, "ex": {}, "quiz": {}, "days": days, "game": game}
    pg.goto(URL); pg.evaluate("(o) => localStorage.setItem('ppr.progress.v1', JSON.stringify(o))", prog); pg.reload(); pg.wait_for_selector(".streakcard")
    check(pg.locator(".notice.freeze").count() == 1 and "2026-10-06" in pg.locator(".notice.freeze").inner_text(), "freeze-used notice for the missed day")
    check(pg.locator(".sc-num b").inner_text() == "7" and "0" in pg.locator(".sc-side").inner_text(), "streak kept at 7, freezes now 0")
    check(pg.locator(".hm.frozen").count() >= 2, "heatmap marks the frozen day")
    pg.reload(); pg.wait_for_selector(".streakcard")
    check(pg.locator(".notice.freeze").count() == 0, "notice shown only once")
    c.close()
    # 4b) reduced motion: no confetti, toast still shown
    c, pg = ctx_at(dt.datetime(2026, 10, 7, 10, 0), reduced=True)
    pg.goto(URL + "#/l/u1l1"); pg.wait_for_selector("text=Mark lesson complete"); pg.click("text=Mark lesson complete")
    pg.wait_for_function("() => document.querySelector('#toast').textContent.includes('Daily goal met') || document.querySelector('#toast').textContent.includes('Lesson complete')", timeout=5000)
    pg.wait_for_timeout(300)
    check(pg.locator("canvas.confetti").count() == 0, "prefers-reduced-motion: no confetti")
    pg.goto(URL + "#/badges"); pg.wait_for_selector(".badge-tile")
    n_e, n_l = pg.locator(".badge-tile.earned").count(), pg.locator(".badge-tile.locked").count()
    check(n_e >= 1 and n_l >= 10 and pg.locator(".ladder li").count() == 7, f"badges screen: {n_e} earned, {n_l} locked, 7 level titles")
    c.close(); b.close()
print(f"\nSTREAK BROWSER TESTS: {ok} passed")
