#!/usr/bin/env python3
"""Guard approved questionnaires.

A questionnaire that has been sent to a client is APPROVED. Its questions may not be
removed or reworded without Julian saying so explicitly. This compares each guarded
page against its lock file and fails loudly on any drift.

  python3 scripts/check-approved.py          # verify (used by the pre-commit hook)
  python3 scripts/check-approved.py --approve <page>   # re-lock, ONLY on Julian's say-so
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARDED = {
    'onboarding': 'onboarding/index.html',
    'ped-health': 'ped-health/index.html',
    'waitlist': 'waitlist/index.html',
    'coaching-application': 'coaching-application/index.html',
}

def questions(path):
    """(key, label) for every question, in page order."""
    s = open(os.path.join(ROOT, path), encoding='utf-8').read()
    out = []
    for m in re.finditer(r'data-q="([^"]+)"', s):
        key = m.group(1)
        seg = s[m.end(): m.end() + 1200]
        lm = re.search(r'<label[^>]*>(.*?)</label>', seg, re.S)
        lab = re.sub(r'<[^>]+>', '', lm.group(1)) if lm else ''
        out.append([key, ' '.join(lab.split()).replace('*', '').strip()])
    # the standalone application/waitlist list required ids in JS instead
    if not out:
        m = re.search(r"ids\s*=\s*\[([^\]]*)\]", s)
        if m:
            out = [[x.strip().strip("'\""), ''] for x in m.group(1).split(',') if x.strip()]
    return out

def lock_path(name): return os.path.join(ROOT, 'approved', name + '.json')

def approve(name):
    path = GUARDED[name]
    json.dump({'page': path, 'questions': questions(path)},
              open(lock_path(name), 'w'), indent=1, ensure_ascii=False)
    print('APPROVED  %s  (%d questions locked)' % (name, len(questions(path))))

def verify():
    bad = False
    for name, path in GUARDED.items():
        lp = lock_path(name)
        if not os.path.exists(lp) or not os.path.exists(os.path.join(ROOT, path)):
            continue
        want = {k: v for k, v in json.load(open(lp))['questions']}
        have = {k: v for k, v in questions(path)}
        gone = [k for k in want if k not in have]
        changed = [k for k in want if k in have and want[k] and have[k] and want[k] != have[k]]
        if gone or changed:
            bad = True
            print('\n  BLOCKED: %s has drifted from what was approved' % path)
            for k in gone:    print('    REMOVED  %-18s %s' % (k, want[k][:70]))
            for k in changed:
                print('    REWORDED %s\n       was: %s\n       now: %s' % (k, want[k][:80], have[k][:80]))
    if bad:
        print("\n  These questions were approved and sent to clients. Do not change them without")
        print("  Julian saying so. If he HAS approved it, re-lock with:")
        print("      python3 scripts/check-approved.py --approve <name>\n")
        return 1
    print('approved questionnaires: unchanged')
    return 0

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--approve':
        approve(sys.argv[2])
    else:
        sys.exit(verify())
