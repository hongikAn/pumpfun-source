#!/usr/bin/env python3
"""blocks.py FN.ll [FROM_LABEL] : one line per IR block: label, callees (short), line consts, terminator."""
import re,sys
src=open(sys.argv[1]).read().split('\n')
start=sys.argv[2] if len(sys.argv)>2 else None
cur=None; info=[]
def short(n):
    n=n.strip('"@')
    m=re.findall(r'\d+([A-Za-z_][A-Za-z0-9_]*?)17h[0-9a-f]{16}E', n)
    if m: return m[-1][:28]
    return n[:28]
out=[]
for l in src:
    m=re.match(r'^([A-Za-z0-9_."$-]+):', l)
    if m or l.startswith('}'):
        if cur: out.append((cur,info))
        cur=m.group(1) if m else None; info=[]; continue
    if cur is None and l.startswith('define'): cur='start'; continue
    if cur is None: continue
    for c in re.findall(r'call [^@]*(@"?[^"( ]+"?)\(', l): info.append(short(c))
    for c in re.findall(r'invoke [^@]*(@"?[^"( ]+"?)\(', l): info.append(short(c))
    for c in re.findall(r'i32 (3[7-9]\d|4\d\d|50\d)\b', l): info.append('L'+c)
    s=l.strip()
    if s.startswith(('br ','switch','ret','unreachable')):
        info.append('| '+re.sub(r'"_ZN[^"]*?(\\d+[a-z_]+)17h[0-9a-f]+E([.a-z0-9]*)"', r'\\1\\2', re.sub(r'label %','',s))[:110])
go = start is None
for lab,i in out:
    if lab==start: go=True
    if go: print(short(lab) if lab.startswith('"') else lab, ':', ' '.join(i)[:170])
