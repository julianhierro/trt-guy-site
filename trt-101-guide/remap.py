"""
Re-freeze element ids.

The editor auto-tags every element e1,e2,e3... in document order and stores the
page's content against those ids. Wrapping the guide in <section> elements shifted
the numbering, so already-published edits started landing on the wrong elements.

This stamps explicit data-eid attributes that reproduce the ORIGINAL numbering, and
gives the containers added later ids outside that number space. Once written, the
ids are frozen: the auto-tagger only assigns ids to elements that don't have one,
so future structural changes can never scramble stored content again.
"""
import json, re, sys
from bs4 import BeautifulSoup, Tag

SKIP = {"script","style","noscript","template","br","link","meta","head"}

def tagged_elements(soup):
    """Mirror editor.js's tagger: document order over body's descendants."""
    body = soup.body
    out = []
    for el in body.find_all(True):
        if el.name in SKIP:
            continue
        skip = False
        for p in [el] + list(el.parents):
            if not isinstance(p, Tag): continue
            if p.has_attr("data-noedit"): skip = True; break
            cls = p.get("class") or []
            if "jv-toolbar" in cls or "jv-launcher" in cls: skip = True; break
        if skip:
            continue
        out.append(el)
    return out

def is_added(el):
    cls = el.get("class") or []
    return (el.name == "section" and "sec" in cls) or ("cover-mid" in cls)

def norm(s):
    s = re.sub(r'\sdata-eid="[^"]*"', '', s or '')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

soup = BeautifulSoup(open('guide.html', encoding='utf-8').read(), 'html.parser')
tags = tagged_elements(soup)
old  = [e for e in tags if not is_added(e)]

print(f'tagged in new doc : {len(tags)}')
print(f'old-equivalent    : {len(old)}')

# provisional old-numbering
eid = {id(e): f'e{i+1}' for i, e in enumerate(old)}

store = json.load(open('/tmp/store.json'))['edits']
by_eid = {x['eid']: x for x in store}
print(f'stored edits      : {len(store)}')

match = miss = diff = 0
diffs = []
rev = {v: k for k, v in eid.items()}
byid = {id(e): e for e in old}
for x in store:
    key = rev.get(x['eid'])
    if key is None:
        miss += 1; continue
    el = byid[key]
    if norm(el.decode_contents()) == norm(x['html']):
        match += 1
    else:
        diff += 1
        diffs.append((x['eid'], el.name, norm(el.decode_contents())[:70], norm(x['html'])[:70]))

print(f'\nmapping check -> identical: {match}   differing: {diff}   unmapped: {miss}')
print(f'confidence: {match/max(1,len(store))*100:.1f}% of stored entries land on an element with the exact same content\n')
print('entries whose stored text differs from the file (i.e. YOUR edits):')
for d in diffs[:30]:
    print(f'  {d[0]:>6} <{d[1]}>')
    print(f'        file : {d[2]}')
    print(f'        store: {d[3]}')
