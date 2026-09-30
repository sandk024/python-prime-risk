"""Screenshots of the streak card + badges screen with a SEEDED DEMO history (clearly synthetic), iPhone 14."""
import sys, random, datetime as dt
from playwright.sync_api import sync_playwright
URL, OUT = sys.argv[1], sys.argv[2]
random.seed(4)
today = dt.date.today()
active, xpd = {}, {}
for i in range(1, 60):
    d = today - dt.timedelta(days=i)
    if i <= 11 or (i > 12 and random.random() < .75):
        k = d.isoformat(); active[k] = {"lessons": 1, "review": random.random() < .5}; xpd[k] = random.choice([60, 90, 160, 220, 340])
frozen = {(today - dt.timedelta(days=12)).isoformat(): True}
game = {"v": 1, "active": active, "frozen": frozen, "freezes": 1, "best": 23, "xp": 2860, "xpByDay": xpd,
        "badges": {"streak-3": "2026-08-10", "streak-7": "2026-08-14", "streak-14": "2026-09-02", "perfect-week": "2026-09-06", "first-lesson": "2026-08-08", "review-1": "2026-08-11", "unit-u1": "2026-08-20", "unit-u2": "2026-09-12"},
        "awarded": {}, "lastSeen": today.isoformat(), "notices": []}
with sync_playwright() as p:
    dev = dict(p.devices["iPhone 14"]); dev.pop("default_browser_type", None)
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome"); c = b.new_context(**dev); pg = c.new_page()
    pg.goto(URL); pg.wait_for_selector(".streakcard")
    pg.evaluate("(g) => { const P = JSON.parse(localStorage.getItem('ppr.progress.v1')); P.game = Object.assign(P.game || {}, g); localStorage.setItem('ppr.progress.v1', JSON.stringify(P)); }", game)
    pg.reload(); pg.wait_for_selector(".streakcard"); pg.wait_for_timeout(600)
    pg.locator(".streakcard").screenshot(path=f"{OUT}/streak-card-demo.png")
    pg.goto(URL + "#/badges"); pg.wait_for_selector(".badge-tile"); pg.wait_for_timeout(600)
    pg.screenshot(path=f"{OUT}/badges-screen-demo.png")
    pg.evaluate("window.scrollTo(0, 820)"); pg.wait_for_timeout(300); pg.screenshot(path=f"{OUT}/badges-screen-demo-2.png")
    b.close()
