#!/usr/bin/env python3
"""Assemble survey/index.html from src/ and pin an explicit data-eid ("sN") on every
body element, so published editor edits can never shift onto the wrong element.

Run ONLY for structural changes, and never after Julian has published edits to the
td-survey store without checking them first (see feedback_approved_questionnaires).
"""
import pathlib, re
R = pathlib.Path(__file__).parent
CFG = '{ site:"td-survey", page:1, pwKey:"trtdad", api:"https://jv-dashboard-chi.vercel.app/api/content" }'
T = R.parent / "offer/src"
early = (T / "early.html").read_text().replace("__CFG__", CFG)
tail = (T / "tail.html").read_text().replace("__CFG__", CFG) \
    .replace('"editor.css?v=1"', '"/editor.css?v=27"').replace('"editor.js?v=1"', '"/editor.js?v=27"')
assert "/editor.js?v=27" in tail
body = (R / "src/body.html").read_text()
n = 0
def stamp(m):
    global n
    if m.group(1).lower() in {"script", "style", "br"} or "data-eid=" in m.group(0):
        return m.group(0)
    n += 1
    return '<%s data-eid="s%d"%s' % (m.group(1), n, m.group(2))
body = re.sub(r"<([a-zA-Z][a-zA-Z0-9]*)(\s|>|/)", stamp, body)
html = ((R / "src/head.html").read_text() + early + "\n</head>\n<body>\n" + body + "\n"
        + (R / "src/app.html").read_text() + tail + "\n</body>\n</html>\n")
(R / "index.html").write_text(html)
print("survey/index.html written, %d elements pinned" % n)
