exec(__import__('pathlib').Path(__file__).with_name('analyze.py').read_text().split("a=maps['original']")[0])
from collections import Counter
a=maps['original'][0xf2ed0];b=next(f for f in maps['candidate'].values() if f['signature']==a['signature']);assert a['bytes']==b['bytes']==776
out={'original':a,'candidate':b,'direct_calls':[],'data_refs':[],'raw_gained_original_windows':[]};aa=w.m.instructions(blobs['original'],a['address'],a['bytes']);bb=w.m.instructions(blobs['candidate'],b['address'],b['bytes'])
for x,y in zip(aa,bb):
 assert x['offset']==y['offset']
 if 'call_target' in x:
  of=maps['original'][x['call_target']];cf=maps['candidate'][y['call_target']];assert of['signature']==cf['signature'];assert of['raw_sha256']==cf['raw_sha256'];out['direct_calls'].append({'offset':x['offset'],'original':of,'candidate':cf})
 if 'lddw_value' in x:out['data_refs'].append(x)
assert len(out['direct_calls'])==2 and not out['data_refs']
co={k:Counter(f['raw_sha256'] for f in fs.values()) for k,fs in maps.items()};gains=(co['candidate']&co['original'])-(co['baseline']&co['original'])
out['raw_gained_original_windows']=[f for f in maps['original'].values() if f['raw_sha256'] in gains];out['raw_gain_count']=sum(gains.values());assert out['raw_gain_count']==11
assert out==json.loads((T/'helper-static.json').read_text());print('helper PASS',[(x['original']['bytes'],x['candidate']['name']) for x in out['direct_calls']]);print('raw gains',[(hex(f['address']),f['bytes']) for f in out['raw_gained_original_windows']])
