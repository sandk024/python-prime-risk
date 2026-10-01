"""Browser check of the 'Python from Zero' unit at iPhone 14 size.
Usage: python3 scripts/verify-beginner.py URL [SHOTSDIR] [--offline-after-load]"""
import sys, json, datetime as dt
from playwright.sync_api import sync_playwright
URL = sys.argv[1]; SHOTS = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
OFFLINE = "--offline-after-load" in sys.argv
ok = 0
def check(c, m):
    global ok
    if not c: raise SystemExit("FAIL: " + m)
    ok += 1; print("ok  ", m, flush=True)
yday = (dt.date.today() - dt.timedelta(days=1)).isoformat()
old = {"version": 1, "completed": {"u1l1": yday, "u1l2": yday}, "ex": {"u1l1:0": {"attempts": 1, "passed": True, "passedOn": yday}}, "quiz": {}, "last": "u1l3", "days": [yday], "created": yday}
def code_in(pg, card, text):
    card.locator(".cm-content").click(); pg.keyboard.press("Control+A"); pg.keyboard.press("Delete"); pg.keyboard.insert_text(text)
def full_shot(pg, path):
    h = pg.evaluate("document.documentElement.scrollHeight")
    for y in range(0, h, 500): pg.evaluate(f"scrollTo(0,{y})"); pg.wait_for_timeout(60)   # let every editor measure itself
    pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(300); pg.screenshot(path=path, full_page=True)
with sync_playwright() as p:
    dev = dict(p.devices["iPhone 14"]); dev.pop("default_browser_type", None)
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome"); c = b.new_context(**dev, color_scheme="dark"); pg = c.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_selector(".hero"); pg.wait_for_selector("text=Ready for offline", timeout=240000)
    pg.evaluate("(o) => localStorage.setItem('ppr.progress.v1', JSON.stringify(o))", old)
    if OFFLINE: c.set_offline(True)
    pg.reload(); pg.wait_for_selector(".hero")
    hero = pg.locator(".hero").inner_text()
    check("1. What a program is" in hero and "Python from Zero" in hero, "existing user: Today's lesson is the new first lesson (" + hero.split("\n")[1] + ")")
    check(pg.locator(".notice.intro").count() == 1, "one-time notice explains the new first unit")
    P = pg.evaluate("JSON.parse(localStorage.getItem('ppr.progress.v1'))")
    check(P["completed"] == old["completed"] and P["ex"]["u1l1:0"]["passed"] and P["game"]["active"].get(yday), "old progress kept (u1l1/u1l2 completed, exercise passed, streak day)")
    pg.reload(); pg.wait_for_selector(".hero"); check(pg.locator(".notice.intro").count() == 0, "notice shown only once")
    units = pg.evaluate("[...document.querySelectorAll('details.unit summary .t')].slice(0,3).map(e => e.textContent)")
    check(units[0] == "Unit 1 · Python from Zero" and units[1] == "Unit 2 · Python on a Trading Desk", f"curriculum order: {units[:2]}")
    # lesson 1
    pg.goto(URL + "#/l/u0l1"); pg.wait_for_selector(".chunk"); pg.wait_for_selector("text=Python ready", timeout=120000)
    check("What you'll learn" in pg.locator(".card.use.learn").inner_text() and pg.locator(".chunk").count() == 4, "lesson 1: 'What you'll learn' + 4 small steps")
    pg.locator(".chunk").first.locator("button:has-text('Run')").click()
    pg.wait_for_function("() => document.querySelector('.chunk pre.out').textContent.includes('Hello!')", timeout=60000)
    check(True, "step 1 example runs: " + pg.locator(".chunk pre.out").first.inner_text().replace("\n", " / "))
    check(pg.locator(".sec-title:has-text('Predict the output')").count() == 1 and pg.locator(".card.recap").count() == 1, "predict-the-output question and recap present")
    pg.locator(".card.quiz .btn.opt:has-text('one, three')").click()
    check("Correct" in pg.locator(".card.quiz .hint").inner_text(), "predict question answers with an explanation")
    if SHOTS: full_shot(pg, f"{SHOTS}/beginner-l1.png")   # fresh lesson: step 1 run, predict answered, exercises untouched
    ex = pg.locator(".card.exercise")
    code_in(pg, ex.nth(0), 'print("hello python")'); ex.nth(0).locator("button:has-text('Check')").click()
    pg.wait_for_selector(".card.exercise >> nth=0 >> .results li.fail", timeout=60000)
    fb = ex.nth(0).locator(".results").inner_text()
    check("Expected the output to be exactly: Hello, Python!" in fb and "Yours was: hello python" in fb, "beginner feedback: expected vs got (" + fb.split("\n")[1][:60] + "…)")
    sols = ['print("Hello, Python!")', 'print("Ready")\nprint("Set")\nprint("Go!")', 'print("Buy milk")\n# print("Buy a spaceship")\nprint("Buy bread")']
    for i, s in enumerate(sols):
        code_in(pg, ex.nth(i), s); ex.nth(i).locator("button:has-text('Check')").click()
        pg.wait_for_function(f"() => {{ const b = document.querySelectorAll('.card.exercise')[{i}].querySelector('.banner'); return b && b.textContent.includes('passed!'); }}", timeout=60000)
    check(pg.locator("text=✓ Lesson complete").count() == 1, "all 3 exercises passed → lesson 1 complete")
    pg.goto(URL + "#/"); pg.wait_for_selector(".hero")
    check("2. print() and text in quotes" in pg.locator(".hero").inner_text(), "Today's lesson moves on to lesson 2")
    pg.goto(URL + "#/l/u0l2"); pg.wait_for_selector(".chunk"); pg.wait_for_timeout(400)
    pg.locator(".chunk").first.locator("button:has-text('Run')").click(); pg.wait_for_function("() => document.querySelector('.chunk pre.out').textContent.includes('Double quotes work')", timeout=60000)
    if SHOTS: full_shot(pg, f"{SHOTS}/beginner-l2.png")
    check(True, "lesson 2 renders and runs")
    # error lesson: broken-on-purpose example shows a readable error
    pg.goto(URL + "#/l/u0l5"); pg.wait_for_selector(".chunk.broken")
    pg.locator(".chunk.broken").first.locator("button:has-text('Run')").click()
    pg.wait_for_selector(".chunk.broken pre.out.err", timeout=60000)
    err = pg.locator(".chunk.broken pre.out.err").first.inner_text()
    check("Line 2: NameError: name 'totl' is not defined" in err, "lesson 5 broken example shows: " + err.split("\n")[0])
    # rerun-based check gives specific feedback
    pg.goto(URL + "#/l/u0l9"); pg.wait_for_selector(".card.exercise")
    e0 = pg.locator(".card.exercise").nth(0)
    code_in(pg, e0, 'temp = 31\nif temp >= 25:\n    advice = "Bring water"\nelse:\n    advice = "Enjoy the run"')
    e0.locator("button:has-text('Check')").click(); pg.wait_for_selector(".card.exercise >> nth=0 >> .results li.fail", timeout=60000)
    check("25 is not ABOVE 25" in e0.locator(".results").inner_text(), "if/else exercise tries other values and explains the boundary")
    check(pg.evaluate("document.documentElement.scrollWidth") <= 390, "no horizontal overflow at 390px")
    check(not errs, f"no page errors {errs}")
    b.close()
print(f"\nBEGINNER BROWSER TESTS: {ok} passed")
