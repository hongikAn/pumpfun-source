import sys,re,difflib
def load(p):
    res=[]
    for l in open(p):
        l=l.rstrip('\n')
        if ':' in l.split('\t')[0]: l=l.split(':',1)[1]
        parts=l.strip().split('\t')
        b=parts[0].split()
        txt=re.sub(r'\s*<.*>','',parts[1]) if len(parts)>1 else ''
        if not b: continue
        if b[0]=='18': k=' '.join(b[:2])+' LDDW'; txt=txt.split(',')[0]
        elif b[0]=='85': k=' '.join(b[:2])+' CALL'; txt='call'
        else: k=' '.join(b[:8])
        res.append((k,txt))
    return res
a=load(sys.argv[1]); b=load(sys.argv[2])
ka=[x[0] for x in a]; kb=[x[0] for x in b]
sm=difflib.SequenceMatcher(None,ka,kb,autojunk=False)
nd=0;out=[]
pa=[0];pb=[0]
for x in a[:-1]: pa.append(pa[-1]+(16 if x[0].endswith('LDDW') else 8))
for x in b[:-1]: pb.append(pb[-1]+(16 if x[0].endswith('LDDW') else 8))
for op,i1,i2,j1,j2 in sm.get_opcodes():
    if op=='equal': continue
    nd+=max(i2-i1,j2-j1)
    out.append('@@ orig 0x%x cand 0x%x'%(pa[i1] if i1<len(pa) else 0, pb[j1] if j1<len(pb) else 0))
    for i in range(i1,i2): out.append('- '+a[i][1])
    for j in range(j1,j2): out.append('+ '+b[j][1])
print(len(a),len(b),'dist',nd)
if len(sys.argv)>3: print('\n'.join(out[:int(sys.argv[3])]))
