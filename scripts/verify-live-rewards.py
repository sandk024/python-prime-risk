"""Live end-to-end for Rewards: an EXISTING install (previous build + streak data with no rewards) receives the new build through the
service-worker update flow, progress migrates without loss, then everything is re-verified OFFLINE at iPhone viewport."""
import sys, json, time, datetime as dt, urllib.request
from playwright.sync_api import sync_playwright
URL, NEW, SHOTS = sys.argv[1], sys.argv[2], sys.argv[3]
def log(*a): print(*a, flush=True)
def live_sw_version():
    try: return urllib.request.urlopen(URL + f"sw.js?nocache={time.time()}", timeout=20).read().decode()
    except Exception as e: return ""
yday = (dt.date.today() - dt.timedelta(days=1)).isoformat()
T = dt.date.today(); days = [(T - dt.timedelta(days=i)).isoformat() for i in range(1, 7)]  # 6-day streak ending yesterday
game = {"v": 1, "active": {d: {"lessons": 1, "review": False} for d in days}, "frozen": {}, "freezes": 0, "best": 6, "xp": 600, "xpByDay": {d: 100 for d in days},
        "badges": {"first-lesson": days[-1], "streak-3": days[-3]}, "awarded": {}, "lastSeen": days[0], "resetNotified": None, "notices": [], "goalCelebrated": days[0]}
old = {"version": 1, "completed": {f"u1l{i+1}": d for i, d in enumerate(reversed(days))}, "ex": {"u1l1:0": {"attempts": 1, "passed": True, "passedOn": days[-1]}},
       "quiz": {"u1l1:0": 1}, "last": "u1l6", "days": days, "created": days[-1], "game": game}
MSG = "Reward unlocked: Race nutrition box (gels/chews) - ask Chief of Staff to line it up"
with sync_playwright() as p:
    dev = dict(p.devices["iPhone 14"]); dev.pop("default_browser_type", None)
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    ctx = b.new_context(**dev, color_scheme="dark"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    navs = []; pg.on("framenavigated", lambda f: navs.append(f.url) if f == pg.main_frame else None)
    pg.goto(URL); pg.wait_for_selector("text=Ready for offline", timeout=240000)
    v_old = pg.evaluate("PRECACHE.version"); log(f"[installed] old build {v_old} ready for offline")
    pg.evaluate("(o) => localStorage.setItem('ppr.progress.v1', JSON.stringify(o))", old)
    pg.reload(); pg.wait_for_selector("text=Today")
    log(f"[installed] seeded previous-build progress: 6-day streak ending {days[0]}, 600 XP, no rewards data")
    t0 = time.time()
    while f'"version":"{NEW}"' not in live_sw_version():
        if time.time() - t0 > 900: raise SystemExit("new build never appeared on the live URL")
        time.sleep(15)
    log(f"[deploy] live sw.js now serves {NEW} (waited {time.time()-t0:.0f}s)")
    pg.reload(); pg.wait_for_selector("#updatebar:not([hidden])", timeout=180000)
    log(f"[update] 'Update ready' bar shown; page still on {pg.evaluate('PRECACHE.version')}")
    n0 = len(navs); pg.click("#updatebar")
    pg.wait_for_function(f"() => window.PRECACHE && PRECACHE.version === '{NEW}'", timeout=60000)
    pg.wait_for_timeout(1500)
    log(f"[update] tapped -> {len(navs) - n0} reload(s), now on {pg.evaluate('PRECACHE.version')}; caches: {pg.evaluate('caches.keys()')}")
    pg.wait_for_selector("text=Ready for offline", timeout=120000)
    P = pg.evaluate("JSON.parse(localStorage.getItem('ppr.progress.v1'))")
    G = P["game"]; R = G["rewards"]
    assert P["completed"] == old["completed"] and P["quiz"] == old["quiz"] and G["xp"] == 600 and G["active"] == game["active"] and G["badges"] == game["badges"], "progress lost!"
    assert [r["days"] for r in R["items"]] == [7, 30, 60, 100] and R["unlocked"] == {} and R["claimed"] == {}
    log(f"[migrate] progress/streak/XP/badges intact; rewards added: {[(r['days'], r['name']) for r in R['items']]}")
    # ---------------- OFFLINE ----------------
    ctx.set_offline(True); pg.reload(); pg.wait_for_selector(".rewardscard", timeout=30000)
    pg.wait_for_selector("text=Ready for offline", timeout=30000)
    log(f"[OFFLINE] reload OK (navigator.onLine={pg.evaluate('navigator.onLine')}); rewards card: " + pg.locator(".rewardscard").inner_text().replace("\n", " | "))
    assert "1 day to go" in pg.locator(".rewardscard").inner_text()
    log("[OFFLINE] streak card level line (secondary): " + pg.locator(".streakcard .level-line").inner_text().replace("\n", " | "))
    lessons = pg.evaluate("fetch('lessons.json').then(r=>r.json())")
    L = [l for u in lessons["units"] for l in u["lessons"] if l["id"] == "u3l1"][0]
    pg.goto(URL + "#/l/u3l1"); pg.wait_for_selector("text=Python ready", timeout=120000)
    pg.locator("button:has-text('Run')").first.click()
    pg.wait_for_function("() => [...document.querySelectorAll('pre.out')].some(e => e.textContent.trim().length > 0)", timeout=90000)
    log("[OFFLINE] pandas example output: " + pg.locator("pre.out").first.inner_text()[:80].replace("\n", " | "))
    for i in range(2):
        card = pg.locator(".card.exercise").nth(i)
        card.locator(".cm-content").click(); pg.keyboard.press("Control+A"); pg.keyboard.press("Delete")
        pg.keyboard.insert_text(L["exercises"][i]["solution"])
        card.locator("button:has-text('Check')").click()
        pg.wait_for_function(f"() => {{ const b = document.querySelectorAll('.card.exercise')[{i}].querySelector('.banner'); return b && b.textContent.includes('passed!'); }}", timeout=90000)
        log(f"[OFFLINE] u3l1 exercise {i+1}: " + card.locator(".banner").inner_text())
    pg.wait_for_selector(".rw-modal", timeout=8000)
    confetti = pg.locator("canvas.confetti").count()
    txt = pg.locator(".rw-modal h2").inner_text(); assert txt == MSG, txt
    log(f"[OFFLINE] 7th day -> unlock celebration: '{txt}' (confetti canvases: {confetti})")
    pg.wait_for_timeout(1200); pg.screenshot(path=f"{SHOTS}/rewards-unlock-live.png")
    pg.click(".rw-modal >> text=Later"); pg.wait_for_timeout(2500)
    pg.goto(URL + "#/"); pg.wait_for_selector(".rewardscard")
    log("[OFFLINE] home rewards card: " + pg.locator(".rewardscard").inner_text().replace("\n", " | "))
    pg.click("text=All rewards →"); pg.wait_for_selector(".rw-item")
    pg.locator(".rw-item").nth(1).locator("text=Edit").click()
    pg.fill("input[name=name]", "Hoka Speedgoat 6"); pg.fill("input[name=price]", "$155"); pg.click("form.rw-item >> text=Save")
    pg.wait_for_selector(".rw-item:not(form) >> text=Hoka Speedgoat 6")
    log("[OFFLINE] edit saved: " + pg.locator(".rw-item").nth(1).inner_text().replace("\n", " | ")[:90])
    pg.locator(".rw-item").nth(1).locator("text=Edit").click(); pg.click("form.rw-item >> text=Default"); pg.wait_for_selector(".rw-item:not(form) >> text=New pair of trail running shoes")
    log("[OFFLINE] 'Default' restored the 30-day reward name (price now: " + str(pg.evaluate("JSON.parse(localStorage.getItem('ppr.progress.v1')).game.rewards.items[1].price")) + ")")
    pg.evaluate("() => { const P = JSON.parse(localStorage.getItem('ppr.progress.v1')); P.game.rewards.items[1].price = null; localStorage.setItem('ppr.progress.v1', JSON.stringify(P)); }")
    pg.reload(); pg.wait_for_selector(".rw-item")
    pg.locator(".rw-item").nth(0).locator("text=Mark claimed").click()
    log("[OFFLINE] claimed: " + pg.locator(".rw-item").nth(0).inner_text().replace("\n", " | "))
    pg.reload(); pg.wait_for_selector(".rw-item")
    st = pg.evaluate("[...document.querySelectorAll('.rw-item')].map(e => e.className.split(' ').pop())"); log(f"[OFFLINE] rewards screen states after reload: {st}")
    assert st == ["claimed", "locked", "locked", "locked"]
    pg.wait_for_timeout(500); pg.screenshot(path=f"{SHOTS}/rewards-screen.png", full_page=True)
    pg.goto(URL + "#/"); pg.wait_for_selector(".rewardscard"); pg.wait_for_timeout(700)
    log("[OFFLINE] home rewards card: " + pg.locator(".rewardscard").inner_text().replace("\n", " | "))
    pg.locator(".rewardscard").screenshot(path=f"{SHOTS}/rewards-home.png")
    pg.screenshot(path=f"{SHOTS}/home-rewards-live.png")
    log("[OFFLINE] scrollWidth", pg.evaluate("document.documentElement.scrollWidth"))
    R = pg.evaluate("JSON.parse(localStorage.getItem('ppr.progress.v1')).game.rewards")
    log(f"[OFFLINE] stored rewards: unlocked={R['unlocked']} claimed={R['claimed']}")
    log("console errors:", [e for e in errs if "ERR_INTERNET_DISCONNECTED" not in e][:6])
    b.close()
log("LIVE REWARDS UPDATE + OFFLINE VERIFICATION PASSED")
