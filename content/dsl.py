from textwrap import dedent
UNITS = []

def _d(s):
    return dedent(s).strip("\n") if s else s

def unit(uid, title, blurb):
    UNITS.append(dict(id=uid, title=title, blurb=blurb, lessons=[]))

def lesson(lid, title, use, body, examples=(), quiz=(), exercises=(), work=None, timed=None, minutes=12, talk=None, kind=None):
    UNITS[-1]["lessons"].append(dict(
        id=lid, title=title, use=use, body=_d(body),
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
