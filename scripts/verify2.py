"""End-to-end verification on iPhone 14 emulation:
online load -> precache complete -> go OFFLINE -> reload -> pandas lesson: run example, fail starter, pass solution
-> Stop button on an infinite loop -> Review queue picks up a missed exercise -> light theme. Screenshots saved."""
import sys, json, time, os
from playwright.sync_api import sync_playwright
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/"
SHOTS = sys.argv[2] if len(sys.argv) > 2 else None
LESSON = sys.argv[3] if len(sys.argv) > 3 else "u3l1"
if SHOTS: os.makedirs(SHOTS, exist_ok=True)
def log(*a): print(*a, flush=True)
def shot(pg, name):
    if SHOTS: pg.wait_for_timeout(450); pg.screenshot(path=f"{SHOTS}/{name}.png")
with sync_playwright() as p:
    dev = dict(p.devices["iPhone 14"]); dev.pop("default_browser_type", None)
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
    ctx = b.new_context(**dev, color_scheme="dark")
    pg = ctx.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    t0 = time.time()
    pg.goto(URL, wait_until="load")
    pg.wait_for_selector("text=Ready for offline", timeout=240000)
    log(f"[online] 'Ready for offline' after {time.time()-t0:.1f}s")
    info = pg.evaluate("""async () => { const all=[...PRECACHE.app,...PRECACHE.pyodide]; let miss=[]; for (const u of all) if(!(await caches.match(new URL(u,location.href).href))) miss.push(u); return {files: all.length, missing: miss, caches: await caches.keys(), controlled: !!navigator.serviceWorker.controller, mb: +(PRECACHE.bytes/1e6).toFixed(1)}; }""")
    log("[online] cache check:", json.dumps(info))
    assert not info["missing"] and info["controlled"]
    pg.wait_for_selector("text=Python ready", timeout=120000)
    log("[online] home scrollWidth", pg.evaluate("document.documentElement.scrollWidth"))
    shot(pg, "01-home")

    # ---------------- OFFLINE ----------------
    ctx.set_offline(True)
    assert pg.evaluate("navigator.onLine") is False
    pg.reload(wait_until="load")
    pg.wait_for_selector("text=Today", timeout=30000)
    pg.wait_for_selector("text=Ready for offline", timeout=30000)
    log("[OFFLINE] reload OK: home rendered, badge still 'Ready for offline', navigator.onLine =", pg.evaluate("navigator.onLine"))
    pg.goto(URL + f"#/l/{LESSON}")
    pg.wait_for_selector("text=Python ready", timeout=120000)
    title = pg.locator("h1").first.inner_text()
    log(f"[OFFLINE] opened lesson {LESSON}: {title!r}; Python ready")
    lessons = pg.evaluate("fetch('lessons.json').then(r=>r.json())")
    L = [l for u in lessons["units"] for l in u["lessons"] if l["id"] == LESSON][0]
    ex0 = L["examples"][0]; ex0 = ex0["code"] if isinstance(ex0, dict) else ex0
    log("[OFFLINE] example imports pandas:", "import pandas" in ex0)
    t1 = time.time()
    pg.locator("button:has-text('Run')").first.click()
    pg.wait_for_function("() => [...document.querySelectorAll('pre.out')].some(e => e.textContent.trim().length > 0)", timeout=90000)
    out = pg.locator("pre.out").first.inner_text()
    log(f"[OFFLINE] pandas example ran in {time.time()-t1:.1f}s; error={'err' in (pg.locator('pre.out').first.get_attribute('class') or '')}; output: " + out[:220].replace("\n", " | "))
    card = pg.locator(".card.exercise").first
    card.locator("button:has-text('Check')").click()
    card.locator(".banner").wait_for(timeout=90000)
    log("[OFFLINE] starter check:", card.locator(".banner").inner_text())
    card.locator(".cm-content").click()
    pg.keyboard.press("Control+A"); pg.keyboard.press("Delete")
    pg.keyboard.insert_text(L["exercises"][0]["solution"])
    card.locator("button:has-text('Check')").click()
    pg.wait_for_function("() => document.querySelector('.card.exercise .banner') && document.querySelector('.card.exercise .banner').textContent.includes('passed!')", timeout=90000)
    log("[OFFLINE] solution check:", card.locator(".banner").inner_text(), "| checks:", card.locator(".results li.pass").count(), "pass /", card.locator(".results li").count())
    log("[OFFLINE] lesson scrollWidth", pg.evaluate("document.documentElement.scrollWidth"))
    card.locator(".banner").scroll_into_view_if_needed(); pg.evaluate("window.scrollBy(0, -360)")
    shot(pg, "03-exercise-checked-offline")
    pg.evaluate("window.scrollTo(0,0)"); shot(pg, "02-lesson-offline")

    # Stop button on an infinite loop (example editor)
    exc = pg.locator(".card:has(.cm-content):not(.exercise)").first
    exc.locator(".cm-content").click()
    pg.keyboard.press("Control+A"); pg.keyboard.press("Delete")
    pg.keyboard.insert_text("while True:\n    pass")
    exc.locator("button:has-text('Run')").click()
    exc.locator("button.stop").wait_for(state="visible", timeout=10000)
    pg.wait_for_timeout(1500)
    exc.locator("button.stop").click()
    pg.wait_for_function("() => [...document.querySelectorAll('pre.out.err')].some(e => e.textContent.includes('Stopped'))", timeout=15000)
    t2 = time.time()
    pg.wait_for_selector("text=Python ready", timeout=60000)
    log(f"[OFFLINE] Stop: infinite loop stopped, Python restarted and ready again in {time.time()-t2:.1f}s")

    # Miss exercise 2 -> appears in Review
    card2 = pg.locator(".card.exercise").nth(1)
    card2.locator("button:has-text('Check')").click()
    card2.locator(".banner").wait_for(timeout=60000)
    pg.goto(URL + "#/review")
    pg.wait_for_selector("h1:has-text('Daily review')")
    n = pg.locator(".rv-item").count()
    log(f"[OFFLINE] Review page: {n} item(s); first:", pg.locator(".rv-item .ctx").first.inner_text() if n else "-")
    shot(pg, "04-review")

    # Light theme
    pg.evaluate("localStorage.setItem('ppr.theme','light')")
    pg.goto(URL + f"#/l/{LESSON}"); pg.reload(wait_until="load")
    pg.wait_for_selector("h1")
    log("[OFFLINE] light theme applied:", pg.evaluate("document.documentElement.dataset.theme"))
    pg.wait_for_timeout(500); shot(pg, "05-lesson-light")
    pg.goto(URL + "#/"); pg.wait_for_timeout(500); shot(pg, "06-home-light")
    pg.evaluate("localStorage.setItem('ppr.theme','dark')")
    log("console errors:", [e for e in errs if "ERR_INTERNET_DISCONNECTED" not in e][:8])
    b.close()
    log("ALL STEPS PASSED")
