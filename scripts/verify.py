"""Headless verification: iPhone 14 emulation, run example + exercise check, SW caching, offline reload."""
import sys, json, time, os
from playwright.sync_api import sync_playwright
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/"
SHOTS = sys.argv[2] if len(sys.argv) > 2 else None
LESSON = sys.argv[3] if len(sys.argv) > 3 else "u1l1"
def log(*a): print(*a, flush=True)
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
    pg.wait_for_selector("text=Ready for offline", timeout=180000)
    log(f"offline-ready badge after {time.time()-t0:.1f}s")
    info = pg.evaluate("""async () => { const all=[...PRECACHE.app,...PRECACHE.pyodide]; let miss=[]; for (const u of all) if(!(await caches.match(new URL(u,location.href).href))) miss.push(u); return {n: all.length, miss, keys: await caches.keys(), ctrl: !!navigator.serviceWorker.controller}; }""")
    log("cache check:", json.dumps(info))
    pg.wait_for_selector("text=Python ready", timeout=120000)
    sw = pg.evaluate("document.documentElement.scrollWidth")
    log("home scrollWidth", sw, "(viewport 390)")
    if SHOTS: pg.screenshot(path=f"{SHOTS}/01-home.png")
    # --- go offline and reload
    ctx.set_offline(True)
    pg.reload(wait_until="load")
    pg.wait_for_selector("text=Today", timeout=30000)
    log("reloaded OFFLINE: home rendered")
    pg.goto(URL + f"#/l/{LESSON}")
    pg.wait_for_selector("text=Python ready", timeout=120000)
    log("OFFLINE: Python ready")
    ex_card = pg.locator(".card", has=pg.locator("h3")).nth(0)
    pg.locator("button:has-text('Run')").first.click()
    pg.wait_for_function("() => [...document.querySelectorAll('pre.out')].some(e => e.textContent.trim().length > 0)", timeout=60000)
    log("example output:", pg.locator("pre.out").first.inner_text()[:200].replace("\n", " | "))
    # exercise: first check starter (should fail), then paste solution and check
    lessons = pg.evaluate(f"fetch('lessons.json').then(r=>r.json())")
    L = [l for u in lessons["units"] for l in u["lessons"] if l["id"] == LESSON][0]
    chk = pg.locator("button:has-text('Check')").first
    chk.click()
    pg.wait_for_selector(".banner", timeout=60000)
    log("starter check:", pg.locator(".banner").first.inner_text(), "|", pg.locator(".results li.fail .m").first.inner_text()[:120] if pg.locator(".results li.fail").count() else "")
    # replace code in first exercise editor via CodeMirror
    editors = pg.locator(".card:has(button:has-text('Check')) .cm-content")
    editors.first.click()
    pg.keyboard.press("Control+A"); pg.keyboard.press("Delete")
    pg.evaluate("(t) => navigator.clipboard ? 0 : 0", L["exercises"][0]["solution"])
    pg.keyboard.insert_text(L["exercises"][0]["solution"])
    if SHOTS: 
        pg.locator(".card:has(button:has-text('Check'))").first.scroll_into_view_if_needed()
    chk.click()
    pg.wait_for_function("() => document.querySelector('.banner') && document.querySelector('.banner').textContent.includes('passed!')", timeout=60000)
    log("solution check:", pg.locator(".banner").first.inner_text())
    lw = pg.evaluate("document.documentElement.scrollWidth")
    log("lesson scrollWidth", lw)
    if SHOTS:
        pg.locator(".banner").first.scroll_into_view_if_needed(); pg.evaluate("window.scrollBy(0, -380)")
        pg.screenshot(path=f"{SHOTS}/03-exercise-checked.png")
        pg.evaluate("window.scrollTo(0,0)"); pg.screenshot(path=f"{SHOTS}/02-lesson.png")
    log("console errors:", errs[:5])
    b.close()
