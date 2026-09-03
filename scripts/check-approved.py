#!/usr/bin/env python3
"""Lock on Julian's approved pages.

Once Julian approves a page — certainly once he sends it to a client — I may not
change it at all without him asking for that specific change. This locks the whole
file, not just its questions: any edit to a guarded page fails until it is
re-approved, and re-approving demands a written note saying what he asked for, so
the approval is visible in git history.

  python3 scripts/check-approved.py                       # verify (pre-commit hook)
  python3 scripts/check-approved.py --approve <page> "what Julian asked for"
"""
import datetime, hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARDED = {
    'onboarding': 'onboarding/index.html',
    'ped-health': 'ped-health/index.html',
    'waitlist': 'waitlist/index.html',
    'coaching-application': 'coaching-application/index.html',
    'onboarding-thanks': 'onboarding/thanks/index.html',
}

def read(path): return open(os.path.join(ROOT, path), encoding='utf-8').read()
def sha(path): return hashlib.sha256(read(path).encode()).hexdigest()

def questions(path):
    s = read(path); out = []
    for m in re.finditer(r'data-q="([^"]+)"', s):
        seg = s[m.end(): m.end() + 1200]
        lm = re.search(r'<label[^>]*>(.*?)</label>', seg, re.S)
        lab = re.sub(r'<[^>]+>', '', lm.group(1)) if lm else ''
        out.append([m.group(1), ' '.join(lab.split()).replace('*', '').strip()])
    if not out:
        m = re.search(r"ids\s*=\s*\[([^\]]*)\]", s)
        if m: out = [[x.strip().strip("'\""), ''] for x in m.group(1).split(',') if x.strip()]
    return out

def lock_path(n): return os.path.join(ROOT, 'approved', n + '.json')

def approve(name, note):
    if name not in GUARDED: sys.exit('unknown page: ' + name)
    if not note or len(note.strip()) < 8:
        sys.exit('Refusing: --approve needs a note saying what Julian asked for.\n'
                 '  python3 scripts/check-approved.py --approve %s "he asked to ..."' % name)
    path = GUARDED[name]
    json.dump({'page': path, 'sha256': sha(path),
               'approved_at': datetime.datetime.now().isoformat(timespec='seconds'),
               'approved_for': note.strip(),
               'questions': questions(path)},
              open(lock_path(name), 'w'), indent=1, ensure_ascii=False)
    print('APPROVED  %s\n  for: %s\n  %d questions locked' % (name, note.strip(), len(questions(path))))

def verify():
    bad = False
    for name, path in GUARDED.items():
        lp = lock_path(name)
        if not os.path.exists(lp) or not os.path.exists(os.path.join(ROOT, path)): continue
        lock = json.load(open(lp))
        if lock.get('sha256') == sha(path): continue
        bad = True
        want = {k: v for k, v in lock['questions']}
        have = {k: v for k, v in questions(path)}
        gone = [k for k in want if k not in have]
        changed = [k for k in want if k in have and want[k] and have[k] and want[k] != have[k]]
        added = [k for k in have if k not in want]
        print('\n  BLOCKED: %s changed since Julian approved it' % path)
        print('  last approved %s for: %s' % (lock.get('approved_at', '?'), lock.get('approved_for', '?')))
        for k in gone:    print('    REMOVED  %-20s %s' % (k, want[k][:60]))
        for k in changed: print('    REWORDED %-20s\n       was: %s\n       now: %s' % (k, want[k][:70], have[k][:70]))
        for k in added:   print('    ADDED    %-20s %s' % (k, have[k][:60]))
        if not (gone or changed or added): print('    (no question changes — copy, layout or script edits)')
    if bad:
        print("\n  Do NOT re-approve to make this pass. Re-approve only when Julian asked for")
        print("  this exact change, and say so in the note:")
        print('      python3 scripts/check-approved.py --approve <page> "he asked to ..."\n')
        return 1
    print('approved pages: unchanged')
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--approve':
        approve(sys.argv[2], ' '.join(sys.argv[3:]))
    else:
        sys.exit(verify())
