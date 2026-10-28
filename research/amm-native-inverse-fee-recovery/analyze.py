from pathlib import Path
from functools import lru_cache
import importlib.util,json,struct,hashlib,gzip
T=Path(__file__).resolve().parent;R=T.parents[1]
s=importlib.util.spec_from_file_location('w',R/'research/fees-composed-frontier188/window_map.py');w=importlib.util.module_from_spec(s);s.loader.exec_module(w);w.m.elf_layout=lru_cache(maxsize=8)(w.m.elf_layout);w.m.relocations=lru_cache(maxsize=8)(w.m.relocations)
blobs={'original':(R/'evidence/original/pump_amm/deployed.so').read_bytes(),'baseline':gzip.decompress((T/'builds/baseline/symbols.so.gz').read_bytes()),'candidate':gzip.decompress((T/'builds/candidate/symbols.so.gz').read_bytes())};maps={k:{f['address']:f for f in w.windows(b)} for k,b in blobs.items()};a=maps['original'][0x74b80];b=next(f for f in maps['candidate'].values() if f['signature']==a['signature']);out={'inputs':{k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()},'original':a,'candidate':b,'direct_calls':[],'typed_references':[],'source_records':[],'incoming':{}}
rows={k:w.m.instructions(blobs[k],f['address'],f['bytes']) for k,f in [('original',a),('candidate',b)]};rel={k:dict(w.m.relocations(v)) for k,v in blobs.items()}
def ptr(k,addr):
 assert rel[k].get(addr,0)&0xffffffff==8
 raw=int.from_bytes(w.m.at_address(blobs[k],addr,8),'little');assert raw&0xffffffff==0;return raw>>32
method_roots=[]
for x,y in zip(rows['original'],rows['candidate']):
 o=x['offset'];assert o==y['offset']
 if 'call_target' in x:
  aa=maps['original'][x['call_target']];bb=maps['candidate'][y['call_target']];assert aa['signature']==bb['signature'];out['direct_calls'].append({'offset':o,'original':aa,'candidate':bb})
 if 'lddw_value' not in x:continue
 aa,bb=x['lddw_value'],y['lddw_value'];assert rel['original'].get(a['address']+o,0)&0xffffffff==rel['candidate'].get(b['address']+o,0)&0xffffffff==8;row={'offset':o,'original':aa,'candidate':bb}
 if o in (192,336):
  value=w.m.at_address(blobs['original'],aa,4);assert value==w.m.at_address(blobs['candidate'],bb,4)==struct.pack('<I',23);row.update(kind='Overflow discriminant',bytes=4,value=23)
 elif o in (240,408):
  size=48 if o==240 else 32;layout=w.m.at_address(blobs['original'],aa+8,16);assert layout==w.m.at_address(blobs['candidate'],bb+8,16);assert struct.unpack('<QQ',layout)==((24,8) if o==240 else (0,1));methods=[]
  for slot in ([0,24,32,40] if size==48 else [0,24]):
   oa,ca=ptr('original',aa+slot),ptr('candidate',bb+slot);of,cf=maps['original'][oa],maps['candidate'][ca];assert of['signature']==cf['signature'];methods.append({'slot':slot,'original':of,'candidate':cf});method_roots.append((oa,ca))
  row.update(kind='vtable',bytes=size,layout=list(struct.unpack('<QQ',layout)),methods=methods)
 elif o==424:
  tail=w.m.at_address(blobs['original'],aa+8,16);assert tail==w.m.at_address(blobs['candidate'],bb+8,16);length,line,column=struct.unpack('<QII',tail);oa,ca=ptr('original',aa),ptr('candidate',bb);value=w.m.at_address(blobs['original'],oa,length);assert value==w.m.at_address(blobs['candidate'],ca,length);row.update(kind='panic Location',bytes=24,filename=value.decode(),line=line,column=column)
 else:
  assert o in (384,544);size=55 if o==384 else 43;value=w.m.at_address(blobs['original'],aa,size);assert value==w.m.at_address(blobs['candidate'],bb,size);row.update(kind='panic message' if o==384 else 'Source filename',bytes=size,value=value.decode())
 out['typed_references'].append(row)
assert [r['offset'] for r in out['typed_references']]==[192,240,336,384,408,424,544]
for k in ('original','candidate'):
 rs={r['offset']:r for r in rows[k]}
 for off,op,dst,src,disp,imm in [(560,0x7b,10,1,-264,0),(568,0x62,10,0,-120,6023),(576,0x72,10,0,-192,2),(584,0x62,10,0,-248,67),(592,0x7a,10,0,-256,43),(600,0x7a,10,0,-272,0)]:
  r=rs[off];assert (r['opcode'],r['destination'],r['source'],r['displacement'],r['immediate'])==(op,dst,src,disp,imm)
out['source_records']=[{'offset':544,'filename':'programs/pump-amm/src/utils/transfer_fee.rs','line':67,'error':6023}]
for k in blobs:
 fn=a if k=='original' else next(f for f in maps[k].values() if f['name'] and '12transfer_fee17amount_before_fee17h' in f['name']);edges=[]
 for f in maps[k].values():
  for row in w.m.instructions(blobs[k],f['address'],f['bytes']):
   if row.get('call_target')==fn['address']:edges.append({'caller':f,'offset':row['offset'],'target':fn['address']})
 out['incoming'][k]=edges
assert out==json.loads((T/'caller-static.json').read_text());print('PASS',len(out['direct_calls']),'actual directcalls;',len(out['typed_references']),'typedreferents;',len(method_roots),'vtablemethods;Source67/6023');print('incoming',{k:len(v) for k,v in out['incoming'].items()})
