"""Live end-to-end: an EXISTING install (old build + pre-streak progress) receives the new build through the
service-worker update flow, progress migrates without loss, then everything is re-verified OFFLINE at iPhone viewport."""
import sys, json, time, datetime as dt, urllib.request
from playwright.sync_api import sync_playwright
URL, NEW, SHOTS = sys.argv[1], sys.argv[2], sys.argv[3]
def log(*a): print(*a, flush=True)
def live_sw_version():
    try: return urllib.request.urlopen(URL + f"sw.js?nocache={time.time()}", timeout=20).read().decode()
    except Exception as e: return ""
yday = (dt.date.today() - dt.timedelta(days=1)).isoformat()
old = {"version": 1, "completed": {"u1l1": yday}, "ex": {"u1l1:0": {"attempts": 1, "passed": True, "passedOn": yday}, "u1l1:1": {"attempts": 2, "passed": True, "passedOn": yday}},
       "quiz": {"u1l1:0": 1}, "last": "u1l2", "days": [yday], "created": yday}
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
    log("[installed] seeded pre-streak progress (u1l1 completed yesterday, 2 exercises passed)")
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
    assert P["completed"] == old["completed"] and P["ex"]["u1l1:1"]["passed"] and P["quiz"] == old["quiz"], "progress lost!"
    log(f"[migrate] progress intact; game created: active={sorted(P['game']['active'])}, xp={P['game']['xp']}, badges={sorted(P['game']['badges'])}")
    # ---------------- OFFLINE ----------------
    ctx.set_offline(True); pg.reload(); pg.wait_for_selector(".streakcard", timeout=30000)
    pg.wait_for_selector("text=Ready for offline", timeout=30000)
    log(f"[OFFLINE] reload OK (navigator.onLine={pg.evaluate('navigator.onLine')}); streak card: " + pg.locator(".sc-top").inner_text().replace("\n", " "))
    lessons = pg.evaluate("fetch('lessons.json').then(r=>r.json())")
    L = [l for u in lessons["units"] for l in u["lessons"] if l["id"] == "u3l1"][0]
    pg.goto(URL + "#/l/u3l1"); pg.wait_for_selector("text=Python ready", timeout=120000)
    pg.locator("button:has-text('Run')").first.click()
    pg.wait_for_function("() => [...document.querySelectorAll('pre.out')].some(e => e.textContent.trim().length > 0)", timeout=90000)
    log("[OFFLINE] pandas example output: " + pg.locator("pre.out").first.inner_text()[:120].replace("\n", " | "))
    for i in range(2):
        card = pg.locator(".card.exercise").nth(i)
        card.locator(".cm-content").click(); pg.keyboard.press("Control+A"); pg.keyboard.press("Delete")
        pg.keyboard.insert_text(L["exercises"][i]["solution"])
        card.locator("button:has-text('Check')").click()
        pg.wait_for_function(f"() => {{ const b = document.querySelectorAll('.card.exercise')[{i}].querySelector('.banner'); return b && b.textContent.includes('passed!'); }}", timeout=90000)
        log(f"[OFFLINE] u3l1 exercise {i+1}: " + card.locator(".banner").inner_text())
    pg.wait_for_selector("canvas.confetti", state="attached", timeout=5000)
    pg.wait_for_function("() => /Daily goal met/.test(document.querySelector('#toast').textContent)", timeout=10000)
    log("[OFFLINE] lesson auto-completed -> confetti + toast: " + pg.locator("#toast").inner_text())
    pg.wait_for_timeout(2500)
    pg.goto(URL + "#/"); pg.wait_for_selector(".streakcard"); pg.wait_for_timeout(700)
    log("[OFFLINE] home streak card: " + pg.locator(".streakcard").inner_text().replace("\n", " | ")[:260])
    pg.locator(".streakcard").screenshot(path=f"{SHOTS}/streak-card-live.png")
    pg.screenshot(path=f"{SHOTS}/home-streak-live.png")
    pg.goto(URL + "#/badges"); pg.wait_for_selector(".badge-tile"); pg.wait_for_timeout(700)
    log(f"[OFFLINE] badges screen: {pg.locator('.badge-tile.earned').count()} earned, {pg.locator('.badge-tile.locked').count()} locked; level: " + pg.locator(".levelcard b").first.inner_text())
    pg.screenshot(path=f"{SHOTS}/badges-screen-live.png")
    log("[OFFLINE] scrollWidth", pg.evaluate("document.documentElement.scrollWidth"))
    G = pg.evaluate("JSON.parse(localStorage.getItem('ppr.progress.v1')).game")
    log(f"[OFFLINE] stored game: streak days={sorted(G['active'])}, xp={G['xp']}, best={G['best']}")
    log("console errors:", [e for e in errs if "ERR_INTERNET_DISCONNECTED" not in e][:6])
    b.close()
log("LIVE UPDATE + OFFLINE VERIFICATION PASSED")
