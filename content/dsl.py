from textwrap import dedent
UNITS = []

def _d(s):
    return dedent(s).strip("\n") if s else s

def unit(uid, title, blurb):
    UNITS.append(dict(id=uid, title=title, blurb=blurb, lessons=[]))

def lesson(lid, title, use, body, examples=(), quiz=(), exercises=(), work=None, timed=None, minutes=12, talk=None, kind=None,
           learn=None, chunks=(), recap=None):
    UNITS[-1]["lessons"].append(dict(
        id=lid, title=title, use=use, body=_d(body), learn=learn, recap=recap, chunks=list(chunks),
        examples=[_d(e) if isinstance(e, str) else dict(title=e[0], code=_d(e[1])) for e in examples],
        quiz=list(quiz), exercises=list(exercises), work=_d(work) if work else None,
        timed=timed, minutes=minutes, talk=_d(talk) if talk else None, kind=kind))

def ex(title, prompt, starter, solution, tests, hints=(), wrong=None, setup="", difficulty=None):
    return dict(difficulty=difficulty, title=title, prompt=_d(prompt), starter=_d(starter), solution=_d(solution),
                tests=[dict(name=n, code=_d(c)) for n, c in tests], hints=list(hints),
                wrong=_d(wrong), setup=_d(setup))

def q(question, options, answer, why, code=None):
    return dict(q=question, options=options, answer=answer, why=why, code=_d(code) if code else None)

def checkpoint(uid, lid, title, use, body, quiz, exercises, minutes=15, timed=None):
    """Append a checkpoint lesson to an existing unit (by id)."""
    lesson(lid, title, use, body, quiz=quiz, exercises=exercises, minutes=minutes, timed=timed, kind="checkpoint")
    l = UNITS[-1]["lessons"].pop()
    for u in UNITS:
        if u["id"] == uid:
            u["lessons"].append(l)
            return
    raise KeyError(uid)

def chunk(text, code=None, error=False):
    """A small explanation step, optionally followed by a runnable example. error=True: the example is
    deliberately broken (validate.mjs checks that it DOES raise an error)."""
    return dict(text=_d(text), code=_d(code) if code else None, error=error)

def beginner(lid, title, learn, chunks, predict, exercises, recap, minutes=10):
    """Beginner lesson: 'What you'll learn', small chunks with runnable examples, a predict-the-output
    question, 2-4 exercises and a one-line recap."""
    k = sum(map(ord, lid)) % len(predict["options"])  # rotate options so the right answer isn't always first
    opts = predict["options"]; predict = dict(predict, options=opts[k:] + opts[:k], answer=(predict["answer"] - k) % len(opts))
    for e in exercises:  # line-by-line solution comments: mark lines that were given in the starter
        given = {ln.strip() for ln in e["starter"].split("\n") if ln.strip() and not ln.strip().startswith("#")}
        out, width = [], max(len(ln) for ln in e["solution"].split("\n"))
        for ln in e["solution"].split("\n"):
            if ln.strip() in given and "#" not in ln and len(ln) <= 60 and ln.strip() not in ("", "return net") and not ln.strip().startswith(("print(", "def ", "for ", "if ", "else", "net =")):
                ln = (ln.ljust(min(width, 40)) if len(ln) <= 40 else ln) + "   # given in the starter"
            out.append(ln)
        e["solution"] = "\n".join(out)
    lesson(lid, title, learn, "", quiz=[predict], exercises=exercises, minutes=minutes, learn=learn, chunks=chunks, recap=recap)
