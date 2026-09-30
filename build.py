import json, sys, importlib, hashlib, os, re
sys.path.insert(0, "content")
import markdown
from dsl import UNITS
MODS = ["u1", "u2", "u3", "u4", "u5", "u6", "u7", "u8", "u9a", "u9b", "u9c", "u9d", "u9e", "cp1", "cp2", "cp3", "final"]
for m in MODS:
    if os.path.exists(f"content/{m}.py"):
        importlib.import_module(m)
def _fix_lists(s):
    # Python-Markdown needs a blank line before a list; authors often omit it. Skip fenced code.
    out, fence, prev = [], False, ""
    for line in s.split("\n"):
        if line.strip().startswith("```"):
            fence = not fence
        is_item = bool(re.match(r"^\s{0,3}([-*]|\d+\.)\s+", line))
        prev_item = bool(re.match(r"^\s*([-*]|\d+\.)\s+", prev))
        if not fence and is_item and prev.strip() and not prev_item and not prev.strip().startswith("```"):
            out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)
md = lambda s: markdown.markdown(_fix_lists(s), extensions=["fenced_code", "tables"]) if s else None
out = []
for u in UNITS:
    uu = dict(u, lessons=[])
    for l in u["lessons"]:
        l = dict(l)
        l["body_html"] = md(l["body"]); del l["body"]
        l["work_html"] = md(l["work"]); del l["work"]
        l["talk_html"] = md(l["talk"]); del l["talk"]
        l["exercises"] = [dict(e, prompt_html=md(e["prompt"])) for e in l["exercises"]]
        for i, e in enumerate(l["exercises"]):
            del e["prompt"]
            if not e.get("difficulty"):
                e["difficulty"] = min(3, 1 + i) if len(l["exercises"]) > 2 else min(3, 1 + i + (1 if l.get("kind") or l.get("timed") else 0))
        l["quiz"] = [dict(x, q_html=md(x["q"])) for x in l["quiz"]]
        uu["lessons"].append(l)
    out.append(uu)
data = json.dumps({"units": out}, ensure_ascii=False)
open("public/lessons.json", "w").write(data)
n = sum(len(u["lessons"]) for u in out)
ne = sum(len(l["exercises"]) for u in out for l in u["lessons"])
print(f"units={len(out)} lessons={n} exercises={ne} bytes={len(data)}")
