"""Browser tests for tangible Rewards with a simulated clock (Playwright page.clock), iPhone 14 viewport.
Usage: python3 scripts/verify-rewards.py URL [SHOTSDIR]"""
import sys, json, datetime as dt
from playwright.sync_api import sync_playwright
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/"
SHOTS = sys.argv[2] if len(sys.argv) > 2 else None
ok = 0
def check(cond, msg):
    global ok
    if not cond: raise SystemExit("FAIL: " + msg)
    ok += 1; print("ok  ", msg, flush=True)
iso = lambda d: d.strftime("%Y-%m-%d")
MSG = "Reward unlocked: Race nutrition box (gels/chews) - ask Chief of Staff to line it up"
with sync_playwright() as p:
    dev = dict(p.devices["iPhone 14"]); dev.pop("default_browser_type", None)
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    errors = []
    def ctx_at(when, reduced=False, state=None):
        c = b.new_context(**dev, reduced_motion="reduce" if reduced else "no-preference", storage_state=state)
        pg = c.new_page(); pg.on("pageerror", lambda e: errors.append(str(e))); pg.clock.install(time=when); return c, pg
    def seed(pg, prog):
        pg.goto(URL); pg.wait_for_selector(".rewardscard"); pg.wait_for_timeout(500)
        pg.evaluate("(o) => localStorage.setItem('ppr.progress.v1', JSON.stringify(o))", prog); pg.reload(); pg.wait_for_selector(".rewardscard")
    store = lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('ppr.progress.v1'))")
    now = dt.datetime(2026, 10, 7, 19, 0); today = now.date()
    # pre-rewards game (previous build's format, no `rewards` key): 6-day streak ending yesterday
    days = [iso(today - dt.timedelta(days=i)) for i in range(1, 7)]
    game = {"v": 1, "active": {d: {"lessons": 1, "review": False} for d in days}, "frozen": {}, "freezes": 0, "best": 6, "xp": 600,
            "xpByDay": {d: 100 for d in days}, "badges": {"first-lesson": days[-1], "streak-3": days[-3]}, "awarded": {}, "lastSeen": days[0], "notices": []}
    prog = {"version": 1, "completed": {f"u1l{i+1}": d for i, d in enumerate(reversed(days))}, "ex": {}, "quiz": {}, "days": days, "game": game}
    c, pg = ctx_at(now); seed(pg, prog)
    P = store(pg); R = P["game"]["rewards"]
    check([r["days"] for r in R["items"]] == [7, 30, 60, 100] and R["unlocked"] == {} and P["game"]["xp"] == 600 and P["completed"] == prog["completed"], "migration: defaults added, nothing unlocked, XP/progress kept")
    card = pg.locator(".rewardscard").inner_text()
    check("Race nutrition box" in card and "1 day to go" in card and "6/7" in card, "home: next reward, days to go (" + card.split("\n")[3] + ")")
    w = pg.evaluate("document.querySelector('.rewardscard .bar.rw i').style.width")
    check(w.startswith("85.7"), f"home: progress bar {w}")
    order = pg.evaluate("[...document.querySelectorAll('#app > section, #app > a')].map(e => e.className)")
    check(order.index(next(x for x in order if "rewardscard" in x)) < order.index(next(x for x in order if "streakcard" in x)), "rewards card sits above the streak card")
    sc = pg.locator(".streakcard").inner_text()
    check("level: Analyst" in sc and pg.locator(".streakcard .level-line .small.muted").count() == 1 and pg.locator(".streakcard .bar.xp").count() == 0, "level is secondary small text (no XP bar on home)")
    # hit the 7th day
    pg.evaluate("() => { const P = JSON.parse(localStorage.getItem('ppr.progress.v1')); P.ex['u1l7:0'] = {attempts:1, passed:true}; localStorage.setItem('ppr.progress.v1', JSON.stringify(P)); }")
    pg.goto(URL + "#/l/u1l7"); pg.reload(); pg.wait_for_selector("text=Mark lesson complete"); pg.click("text=Mark lesson complete")
    pg.wait_for_selector(".rw-modal", timeout=5000)
    check(MSG in pg.locator(".rw-modal").inner_text(), "unlock celebration: " + MSG)
    check(pg.locator("canvas.confetti").count() >= 1, "confetti on unlock")
    check(store(pg)["game"]["rewards"]["unlocked"] == {"r7": iso(today)}, "r7 unlocked once, dated today")
    pg.click(".rw-modal >> text=Later"); pg.clock.run_for(3000)
    pg.goto(URL + "#/"); pg.wait_for_selector(".rewardscard")
    card = pg.locator(".rewardscard").inner_text()
    check(MSG in card and pg.locator(".rewardscard >> text=Mark claimed").count() == 1 and "New pair of trail running shoes" in card and "23 days to go" in card, "home: unlocked reward with Mark claimed + next reward shoes 23 to go")
    # rewards screen
    pg.click("text=All rewards →"); pg.wait_for_selector(".rw-item")
    st = pg.evaluate("[...document.querySelectorAll('.rw-item')].map(e => e.className.split(' ').pop())")
    check(st == ["unlocked", "locked", "locked", "locked"], f"rewards screen states {st}")
    check("Black Canyon 100k (Feb 13, 2027)" in pg.locator(".rw-item").nth(2).inner_text(), "60-day note mentions Black Canyon 100k")
    # edit shoes: bad price, then good
    pg.locator(".rw-item").nth(1).locator("text=Edit").click()
    pg.fill("input[name=name]", "Hoka Speedgoat 6"); pg.fill("input[name=price]", "cheap"); pg.click("form.rw-item >> text=Save")
    check("Price must be a number" in pg.locator("form.rw-item [role=alert]").inner_text(), "edit validation error shown")
    pg.fill("input[name=price]", "$155"); pg.fill("input[name=note]", "size 10.5, wide"); pg.fill("input[name=link]", "https://www.rei.com/"); pg.click("form.rw-item >> text=Save")
    pg.wait_for_selector(".rw-item:not(form) >> text=Hoka Speedgoat 6")
    t1 = pg.locator(".rw-item").nth(1).inner_text()
    check("$155" in t1 and "size 10.5, wide" in t1 and pg.locator(".rw-item").nth(1).locator("a[href='https://www.rei.com/']").count() == 1, "edit saved: name, note, price, link")
    # claim
    pg.locator(".rw-item").nth(0).locator("text=Mark claimed").click()
    check(f"Claimed {iso(today)}" in pg.locator(".rw-item").nth(0).inner_text(), "Mark claimed records the date")
    pg.reload(); pg.wait_for_selector(".rw-item")
    check(pg.evaluate("[...document.querySelectorAll('.rw-item')].map(e => e.className.split(' ').pop())")[0] == "claimed" and "Hoka Speedgoat 6" in pg.locator(".rw-item").nth(1).inner_text(), "claim + edit persist across reload")
    if SHOTS: pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(300); pg.screenshot(path=f"{SHOTS}/rewards-screen.png", full_page=True)
    pg.goto(URL + "#/"); pg.wait_for_selector(".rewardscard")
    check(pg.locator(".rewardscard >> text=Mark claimed").count() == 0 and "Hoka Speedgoat 6" in pg.locator(".rewardscard").inner_text(), "home: claimed reward gone from card; next reward shows edited name")
    if SHOTS: pg.wait_for_timeout(300); pg.locator(".rewardscard").screenshot(path=f"{SHOTS}/rewards-home.png")
    exported = json.dumps(store(pg))
    state = c.storage_state(); c.close()
    # streak break 5 days later: reward stays claimed
    c, pg = ctx_at(dt.datetime(2026, 10, 12, 9, 0), state=state); pg.goto(URL); pg.wait_for_selector(".rewardscard")
    check(pg.locator(".notice.reset").count() == 1 and pg.locator(".sc-num b").inner_text() == "0", "streak reset after missed days")
    P = store(pg)["game"]
    check(P["rewards"]["claimed"] == {"r7": iso(today)} and P["rewards"]["unlocked"] == {"r7": iso(today)}, "reward stays unlocked/claimed after the streak breaks")
    # import the export into a fresh device
    c.close(); c, pg = ctx_at(dt.datetime(2026, 10, 12, 9, 0)); pg.goto(URL + "#/settings"); pg.wait_for_selector("textarea.io")
    pg.fill("textarea.io", exported); pg.click("button.btn.primary:has-text(\"Import\")"); pg.wait_for_selector(".rewardscard")
    R = store(pg)["game"]["rewards"]
    check(R["claimed"] == {"r7": iso(today)} and R["items"][1]["name"] == "Hoka Speedgoat 6" and R["items"][1]["price"] == 155, "export/import carries rewards, edits and claim dates")
    c.close()
    # reduced motion: modal without confetti
    c, pg = ctx_at(now, reduced=True); seed(pg, prog)
    pg.evaluate("() => { const P = JSON.parse(localStorage.getItem('ppr.progress.v1')); P.ex['u1l7:0'] = {attempts:1, passed:true}; localStorage.setItem('ppr.progress.v1', JSON.stringify(P)); }")
    pg.goto(URL + "#/l/u1l7"); pg.reload(); pg.wait_for_selector("text=Mark lesson complete"); pg.click("text=Mark lesson complete")
    pg.wait_for_selector(".rw-modal", timeout=5000); pg.wait_for_timeout(300)
    check(pg.locator("canvas.confetti").count() == 0, "prefers-reduced-motion: modal, no confetti")
    pg.click(".rw-modal >> text=Mark claimed")
    check(store(pg)["game"]["rewards"]["claimed"].get("r7") == iso(today) and pg.locator(".rw-modal").count() == 0, "Mark claimed from the celebration dialog")
    c.close()
    check(not errors, f"no page errors {errors}")
print(f"\nREWARD BROWSER TESTS: {ok} passed")
