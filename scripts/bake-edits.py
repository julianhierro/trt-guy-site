#!/usr/bin/env python3
"""Bake a page's PUBLISHED editor edits back into its HTML file.

Why this exists: the inline editor stores Julian's published copy in the
jv-dashboard content store and re-applies it in the browser on every load. If the
file on disk still holds the ORIGINAL copy, a first-time visitor paints the old
text and then watches it get swapped — the flash Julian has reported repeatedly.
Baking makes the file itself the current copy, and stamps window.JV_BAKED_AT so
the runtime can see it is current and skip the re-apply entirely.

Run it after Julian publishes an edit:

    python3 scripts/bake-edits.py fertility-guide/thanks/index.html td-fertility-thanks

Then commit and deploy. Re-running is safe: with nothing new published it is a
no-op apart from refreshing the stamp.
"""
import io, json, re, sys, urllib.request

API = 'https://jv-dashboard-chi.vercel.app/api/content'


def locate(s, eid):
    """Return (elem_start, inner_start, inner_end, elem_end) for data-eid=eid."""
    m = re.search(r'<(\w+)[^>]*\sdata-eid="%s"[^>]*>' % re.escape(eid), s)
    if not m:
        raise KeyError(eid)
    tag, depth, i = m.group(1), 1, m.end()
    pat = re.compile(r'</?%s\b[^>]*>' % tag, re.I)
    while depth:
        mm = pat.search(s, i)
        if not mm:
            raise ValueError('unbalanced markup around ' + eid)
        t = mm.group(0)
        if t.startswith('</'):
            depth -= 1
        elif not t.endswith('/>'):
            depth += 1
        i = mm.end()
        if depth == 0:
            return m.start(), m.end(), mm.start(), mm.end()


def bake(path, site, page=1):
    s = io.open(path, encoding='utf-8').read()
    with urllib.request.urlopen('%s?site=%s&page=%d' % (API, site, page)) as r:
        data = json.load(r)
    edits, stamp = data.get('edits'), data.get('updatedAt')
    if not edits:
        print('%s: nothing published for %s' % (path, site))
        return
    patched = removed = 0

    for e in edits:                                   # 1. innerHTML patches
        if e.get('reorder') or e.get('removed') or 'html' not in e:
            continue
        try:
            _, i0, i1, _ = locate(s, e['eid'])
        except KeyError:
            print('  ! %s not in the file (already removed?)' % e['eid'])
            continue
        if s[i0:i1] != e['html']:
            s = s[:i0] + e['html'] + s[i1:]
            patched += 1

    for e in edits:                                   # 2. removals
        if not e.get('removed'):
            continue
        try:
            a, _, _, b = locate(s, e['eid'])
        except KeyError:
            continue
        while b < len(s) and s[b] == '\n':
            b += 1
        s = s[:a] + s[b:]
        removed += 1

    for e in edits:                                   # 3. reorders
        if not e.get('reorder'):
            continue
        a, i0, i1, b = locate(s, e['eid'])
        inner = s[i0:i1]
        blocks = {}
        for eid in e['order']:
            try:
                x0, _, _, x1 = locate(inner, eid)
            except KeyError:
                continue
            blocks[eid] = inner[x0:x1]
        if len(blocks) != len(e['order']):
            print('  ! could not reorder %s cleanly, left as is' % e['eid'])
            continue
        rest = inner
        for chunk in blocks.values():
            rest = rest.replace(chunk, '', 1)
        s = s[:i0] + '\n' + '\n'.join(blocks[x] for x in e['order']) + '\n' + rest.strip('\n') + s[i1:]

    tag = '<script>window.JV_BAKED_AT='                # 4. stamp
    if tag in s:
        s = re.sub(r'<script>window\.JV_BAKED_AT="[^"]*";</script>',
                   '<script>window.JV_BAKED_AT="%s";</script>' % stamp, s)
    else:
        anchor = '<script>window.JV_EDITOR_EARLY='
        if anchor not in s:
            anchor = '<script>window.JV_EDITOR='
        s = s.replace(anchor, '<script>window.JV_BAKED_AT="%s";</script>\n%s' % (stamp, anchor), 1)

    io.open(path, 'w', encoding='utf-8').write(s)
    print('%s: %d patched, %d removed, stamped %s' % (path, patched, removed, stamp))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    bake(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1)
