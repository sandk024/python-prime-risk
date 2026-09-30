# Shared runner: used by the in-browser worker AND the Node test harness.
import sys, io, json, traceback, re

def _fmt_exc(e, src_name="<your code>"):
    tb = traceback.extract_tb(e.__traceback__)
    frames = [f for f in tb if f.filename == src_name]
    line = frames[-1].lineno if frames else None
    msg = f"{type(e).__name__}: {e}"
    if line:
        msg = f"Line {line}: " + msg
    tips = {
        "NameError": "Tip: check spelling, and make sure the variable/function is defined above where you use it.",
        "IndentationError": "Tip: Python uses indentation (4 spaces) to group code. Use the ⇥ key on the toolbar.",
        "SyntaxError": "Tip: look for a missing colon ':', bracket or quote on or just before that line.",
        "TypeError": "Tip: you may be mixing types (e.g. str + int) or calling a function with the wrong arguments.",
        "KeyError": "Tip: that key isn't in the dict / column isn't in the DataFrame. Print the keys/columns to check.",
        "ZeroDivisionError": "Tip: guard against dividing by zero.",
    }
    t = tips.get(type(e).__name__)
    return msg + ("\n" + t if t else "")

def run(code, tests_json="null", setup=""):
    tests = json.loads(tests_json) if tests_json else None
    ns = {"__name__": "__main__"}
    out = io.StringIO()
    old = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = out
    error = None
    if "pandas" in code or "pandas" in setup:
        try:
            import pandas as _pd
            _pd.set_option("display.width", 72)
            _pd.set_option("display.max_columns", 10)
            _pd.set_option("display.max_rows", 40)
        except Exception:
            pass
    try:
        if setup:
            exec(compile(setup, "<setup>", "exec"), ns)
        exec(compile(code, "<your code>", "exec"), ns)
    except SyntaxError as e:
        error = f"Line {e.lineno}: SyntaxError: {e.msg}\nTip: look for a missing colon ':', bracket or quote on or just before that line."
    except BaseException as e:
        error = _fmt_exc(e)
    finally:
        sys.stdout, sys.stderr = old
    stdout = out.getvalue()
    results = []
    if tests is not None:
        ns["_stdout"] = stdout
        ns["_source"] = code
        ns["_close"] = lambda a, b, tol=1e-6: abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))
        for t in tests:
            if error:
                results.append({"name": t["name"], "ok": False, "msg": "Your code raised an error before tests could run."})
                continue
            buf = io.StringIO()
            sys.stdout = sys.stderr = buf
            try:
                exec(compile(t["code"], "<test>", "exec"), ns)
                results.append({"name": t["name"], "ok": True, "msg": ""})
            except AssertionError as e:
                results.append({"name": t["name"], "ok": False, "msg": str(e) or "Result didn't match what was expected."})
            except NameError as e:
                m = re.search(r"name '(\w+)'", str(e))
                nm = m.group(1) if m else "?"
                results.append({"name": t["name"], "ok": False, "msg": f"Couldn't find `{nm}` — did you define it with exactly that name?"})
            except BaseException as e:
                results.append({"name": t["name"], "ok": False, "msg": f"{type(e).__name__} while testing: {e}"})
            finally:
                sys.stdout, sys.stderr = old
    if len(stdout) > 20000:
        stdout = stdout[:20000] + "\n… (output truncated)"
    return json.dumps({"stdout": stdout, "error": error, "results": results})
