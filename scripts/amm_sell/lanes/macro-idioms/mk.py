#!/usr/bin/env python3
"""mk.py BASE OUT 'LINE<TAB>NEWTEXT' ... : replace whole lines (1-based) keeping line count.
NEWTEXT may use {ind} for original indentation; 'LINE<TAB>R<TAB>old<TAB>new' does substring replace."""
import sys
base, out, *subs = sys.argv[1:]
L = open(base).read().split('\n')
for s in subs:
    n, t = s.split('\t', 1); n = int(n) - 1
    if t.startswith('R\t'):
        _, old, new = t.split('\t', 2)
        assert old in L[n], (n+1, old, L[n]); L[n] = L[n].replace(old, new, 1)
    else:
        ind = L[n][:len(L[n]) - len(L[n].lstrip())]
        L[n] = t.replace('{ind}', ind)
open(out, 'w').write('\n'.join(L))
