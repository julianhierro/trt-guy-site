#!/usr/bin/env python3
"""Assemble index.html from src/ and stamp a stable data-eid on every body element.

The inline editor (editor.js) keys every published edit by data-eid, so the ids
have to live in the file, not be generated at load time. Run this only when the
page STRUCTURE changes in src/. Copy changes happen in the browser editor
(?edit=1) and get baked back with bake-edits.py; never re-run build.py after
that without re-baking, or the ids and the published edits can drift apart.

    python3 build.py
"""
import pathlib, re

ROOT = pathlib.Path(__file__).parent
SITE = "trtguy-offer"
CFG = '{ site:"%s", page:1, pwKey:"trtdad", api:"https://jv-dashboard-chi.vercel.app/api/content" }' % SITE

head = (ROOT / "src/head.html").read_text()
content = (ROOT / "src/content.html").read_text()
early = (ROOT / "src/early.html").read_text().replace("__CFG__", CFG)
tail = (ROOT / "src/tail.html").read_text().replace("__CFG__", CFG)

SKIP = {"script", "style", "noscript", "template", "br", "link", "meta"}
n = 0


def stamp(m):
    global n
    tag = m.group(1).lower()
    if tag in SKIP or "data-eid=" in m.group(0):
        return m.group(0)
    n += 1
    return "<%s data-eid=\"e%d\"%s" % (m.group(1), n, m.group(2))


content = re.sub(r"<([a-zA-Z][a-zA-Z0-9]*)(\s|>|/)", stamp, content)

html = head + early + "\n</head>\n<body>\n" + content + "\n" + tail + "\n</body>\n</html>\n"
(ROOT / "index.html").write_text(html)
print("index.html written, %d elements tagged" % n)
