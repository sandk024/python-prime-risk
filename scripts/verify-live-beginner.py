"""Live: an existing install (previous build, progress in the old Unit 1) gets the beginner-unit build via the
service-worker update flow; progress migrates; then the new lessons are verified OFFLINE at iPhone 14 size.
Usage: python3 scripts/verify-live-beginner.py URL NEWVERSION SHOTSDIR"""
import sys, time, datetime as dt, urllib.request
from playwright.sync_api import sync_playwright
URL, NEW, SHOTS = sys.argv[1], sys.argv[2], sys.argv[3]
def log(*a): print(*a, flush=True)
def live_sw():
    try: return urllib.request.urlopen(URL + f"sw.js?nocache={time.time()}", timeout=20).read().decode()
    except Exception: return ""
T = dt.date.today(); yday = (T - dt.timedelta(days=1)).isoformat()
old = {"version": 1, "completed": {"u1l1": yday}, "ex": {"u1l1:0": {"attempts": 2, "passed": True, "passedOn": yday}, "u1l1:1": {"attempts": 1, "passed": False}},
       "quiz": {"u1l1:0": 1}, "last": "u1l2", "days": [yday], "created": yday}
def code_in(pg, card, text):
    card.locator(".cm-content").click(); pg.keyboard.press("Control+A"); pg.keyboard.press("Delete"); pg.keyboard.insert_text(text)
def full_shot(pg, path):
    h = pg.evaluate("document.documentElement.scrollHeight")
    for y in range(0, h, 500): pg.evaluate(f"scrollTo(0,{y})"); pg.wait_for_timeout(60)
    pg.evaluate("scrollTo(0,0); const t = document.querySelector('#toast'); if (t) t.hidden = true; document.querySelectorAll('canvas.confetti').forEach(c => c.remove())"); pg.wait_for_timeout(300); pg.screenshot(path=path, full_page=True)
with sync_playwright() as p:
    dev = dict(p.devices["iPhone 14"]); dev.pop("default_browser_type", None)
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome"); ctx = b.new_context(**dev, color_scheme="dark"); pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    navs = []; pg.on("framenavigated", lambda f: navs.append(f.url) if f == pg.main_frame else None)
    pg.goto(URL); pg.wait_for_selector("text=Ready for offline", timeout=240000)
    log(f"[installed] old build {pg.evaluate('PRECACHE.version')} ready for offline")
    pg.evaluate("(o) => localStorage.setItem('ppr.progress.v1', JSON.stringify(o))", old); pg.reload(); pg.wait_for_selector(".hero")
    log("[installed] seeded progress in the old Unit 1 (u1l1 completed yesterday); old Today's lesson: " + pg.locator(".hero h1").inner_text())
    t0 = time.time()
    while f'"version":"{NEW}"' not in live_sw():
        if time.time() - t0 > 900: raise SystemExit("new build never appeared on the live URL")
        time.sleep(15)
    log(f"[deploy] live sw.js now serves {NEW} (waited {time.time()-t0:.0f}s)")
    pg.reload(); pg.wait_for_selector("#updatebar:not([hidden])", timeout=180000)
    log(f"[update] 'Update ready' bar shown; page still on {pg.evaluate('PRECACHE.version')}")
    n0 = len(navs); pg.click("#updatebar")
    pg.wait_for_function(f"() => window.PRECACHE && PRECACHE.version === '{NEW}'", timeout=60000); pg.wait_for_timeout(1500)
    log(f"[update] tapped -> {len(navs) - n0} reload(s), now on {pg.evaluate('PRECACHE.version')}; caches: {pg.evaluate('caches.keys()')}")
    pg.wait_for_selector("text=Ready for offline", timeout=120000)
    pg.wait_for_selector(".hero")
    log("[update] home after update: Today's lesson = " + pg.locator(".hero h1").inner_text() + "; one-time notice: " + (pg.locator(".notice.intro").inner_text().replace("\n", " — ") if pg.locator(".notice.intro").count() else "none"))
    P = pg.evaluate("JSON.parse(localStorage.getItem('ppr.progress.v1'))")
    assert P["completed"] == old["completed"] and P["ex"]["u1l1:0"]["passed"] and P["quiz"] == old["quiz"], "progress lost!"
    log(f"[migrate] progress intact: completed={P['completed']}, streak days={sorted(P['game']['active'])}, rewards={len(P['game']['rewards']['items'])}")
    # ---------------- OFFLINE ----------------
    ctx.set_offline(True); pg.goto(URL + "#/"); pg.reload(); pg.wait_for_selector(".hero", timeout=30000)
    hero = pg.locator(".hero h1").inner_text()
    log(f"[OFFLINE] reload OK (navigator.onLine={pg.evaluate('navigator.onLine')}); Today's lesson: {hero}; intro notice: {pg.locator('.notice.intro').count()}")
    assert hero.startswith("1. What a program is")
    units = pg.evaluate("[...document.querySelectorAll('details.unit summary .t')].map(e => e.textContent)")
    log(f"[OFFLINE] units: {units[0]} | {units[1]} | {units[2]} … ({len(units)} total)")
    row = pg.locator("details.unit").nth(1).inner_text()
    pg.goto(URL + "#/l/u0l1"); pg.wait_for_selector(".chunk"); pg.wait_for_selector("text=Python ready", timeout=120000)
    pg.locator(".chunk").first.locator("button:has-text('Run')").click()
    pg.wait_for_function("() => document.querySelector('.chunk pre.out').textContent.includes('Hello!')", timeout=90000)
    log("[OFFLINE] lesson 1 step 1 output: " + pg.locator(".chunk pre.out").first.inner_text().strip().replace("\n", " / "))
    pg.locator(".card.quiz .btn.opt:has-text('one, three')").click()
    log("[OFFLINE] predict-the-output: " + pg.locator(".card.quiz .hint").inner_text()[:70])
    full_shot(pg, f"{SHOTS}/beginner-l1.png")
    ex = pg.locator(".card.exercise")
    code_in(pg, ex.nth(0), 'print("hello python")'); ex.nth(0).locator("button:has-text('Check')").click()
    pg.wait_for_selector(".card.exercise >> nth=0 >> .results li.fail", timeout=60000)
    log("[OFFLINE] wrong answer feedback: " + ex.nth(0).locator(".results li.fail .m").inner_text().replace("\n", " | "))
    for i, s in enumerate(['print("Hello, Python!")', 'print("Ready")\nprint("Set")\nprint("Go!")', 'print("Buy milk")\n# print("Buy a spaceship")\nprint("Buy bread")']):
        code_in(pg, ex.nth(i), s); ex.nth(i).locator("button:has-text('Check')").click()
        pg.wait_for_function(f"() => {{ const b = document.querySelectorAll('.card.exercise')[{i}].querySelector('.banner'); return b && b.textContent.includes('passed!'); }}", timeout=60000)
        log(f"[OFFLINE] lesson 1 exercise {i+1}: " + ex.nth(i).locator(".banner").inner_text())
    pg.wait_for_selector("text=✓ Lesson complete", timeout=5000)
    pg.wait_for_function("() => /Daily goal met|lesson complete/i.test(document.querySelector('#toast').textContent)", timeout=10000)
    log("[OFFLINE] lesson 1 complete; toast: " + pg.locator("#toast").inner_text())
    pg.wait_for_timeout(3000)
    pg.goto(URL + "#/"); pg.wait_for_selector(".hero")
    log("[OFFLINE] Today's lesson now: " + pg.locator(".hero h1").inner_text() + " | streak: " + pg.locator(".sc-num").inner_text().replace("\n", " "))
    pg.goto(URL + "#/l/u0l2"); pg.wait_for_selector(".chunk"); pg.wait_for_timeout(400)
    pg.locator(".chunk").first.locator("button:has-text('Run')").click()
    pg.wait_for_function("() => document.querySelector('.chunk pre.out').textContent.includes('Double quotes work')", timeout=60000)
    log("[OFFLINE] lesson 2 step 1 output: " + pg.locator(".chunk pre.out").first.inner_text().strip().replace("\n", " / "))
    full_shot(pg, f"{SHOTS}/beginner-l2.png")
    pg.goto(URL + "#/l/u0l5"); pg.wait_for_selector(".chunk.broken"); pg.locator(".chunk.broken").first.locator("button:has-text('Run')").click()
    pg.wait_for_selector(".chunk.broken pre.out.err", timeout=60000)
    log("[OFFLINE] lesson 5 broken-on-purpose example: " + pg.locator(".chunk.broken pre.out.err").first.inner_text().split("\n")[0])
    pg.goto(URL + "#/l/u1l1"); pg.wait_for_selector(".card.prose")
    log("[OFFLINE] old first lesson now 'Python on a Trading Desk': " + pg.locator("nav.crumbs").inner_text() + " | still completed: " + str(pg.locator("text=✓ Lesson complete").count() == 1))
    log("[OFFLINE] scrollWidth", pg.evaluate("document.documentElement.scrollWidth"))
    log("console errors:", [e for e in errs if "ERR_INTERNET_DISCONNECTED" not in e][:6])
    b.close()
log("LIVE BEGINNER UPDATE + OFFLINE VERIFICATION PASSED")
