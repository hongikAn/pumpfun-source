"""Recompute source/build identity, complete functions, calls, data and signed receipts.

Audits retained evidence; does not compile or execute the program again.
"""
from collections import Counter
import base64,difflib,gzip,hashlib,json,re,runpy,tarfile
from pathlib import Path
from solders.transaction import Transaction
if not __debug__: raise SystemExit('Verification requires Python without -O')
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def read(name):
    data=(HERE/name).read_bytes()
    return gzip.decompress(data) if name.endswith('.gz') else data
def record(name):return json.loads(read(name))
manifest=record('MANIFEST.json')
def verify_inventory(root, entries):
    paths = list(root.rglob('*'))
    assert not any(p.is_symlink() for p in paths), 'packet symlink'
    assert all(p.is_file() or p.is_dir() for p in paths), 'packet special file'
    assert set(entries) == {p.relative_to(root).as_posix() for p in paths
                            if p.is_file() and p != root / 'MANIFEST.json'}, 'packet inventory differs'
verify_inventory(HERE,manifest['files'])
for n,v in manifest['files'].items():assert sha((HERE/n).read_bytes())==v,n
for n,v in manifest['repository_inputs'].items():assert sha((ROOT/n).read_bytes())==v,n
assert all(manifest['repository_inputs'][n]==v for n,v in record('runtime/inputs.json').items())
materialize=runpy.run_path(str(HERE/'materialize.py'))
sources={k:materialize['source_files'](k) for k in ('baseline','candidate')}
before,after=sources.values()
source='programs/pump-amm/src/utils/transfer_fee.rs'
native='crates/native-transfer-fee/src/lib.rs'
assert set(before)==set(after) and len(before)==54
assert {n for n in before if before[n]!=after[n]}=={source,native}
needle=b'pub fn amount_before_fee(data: &TransferFeeData, amount: u64) -> Result<u64> {\n    match data {'
assert before[source].count(needle)==1
assert after[source]==before[source].replace(needle,needle.replace(b'match data',b'match *data')).replace(b'            .spl_fee()',b'')
assert after[source]==read('proposed/transfer_fee.rs') and after[native]==read('proposed/native_transfer_fee.rs')
method=read('controls/late-max/input.rs').split(b'#[no_mangle]\n')[1].replace(b'pub fn inverse_return(fee:&DecodedTransferFee, amount:u64)',b'pub fn calculate_pre_fee_amount(&self, amount:u64)').replace(b'fee.',b'self.').replace(b'maximum_self.',b'maximum_fee.')
assert after[native]==before[native].rstrip()[:-2]+b'\n    #[inline(never)]\n'+method+b'}\n'
patch=''.join(''.join(difflib.unified_diff(before[n].decode().splitlines(True),after[n].decode().splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in (source,native))
assert patch.encode()==read('source.patch')
with tarfile.open(ROOT/'research/amm-fee-value-call-recovery/sources/candidate.tar.gz','r:gz') as tf:
    parent={m.name:tf.extractfile(m).read() for m in tf.getmembers()}
assert parent==before
builds={};images={};results={}
for label in ('baseline','candidate','repeat'):
    launch=record('builds/'+label+'/launch.json');result=record('builds/'+label+'/result.json')
    src=sources['candidate' if label=='repeat' else label]
    assert launch['inputs']=={n:sha(b) for n,b in src.items()}
    assert result['returncode']==0 and result['source_unchanged'] and result['actual_root_invocations']==1
    assert result['dependencies_unchanged_except_native_fee' if label=='candidate' else 'dependencies_unchanged']
    log=read('builds/'+label+'/build.log.gz').decode()
    for crate in ('pump_amm_recovered','native_transfer_fee'):
        assert sum(l.strip().startswith('Running `') and '--crate-name '+crate+' ' in l for l in log.splitlines())==1
    cmd=launch['command'];assert cmd[cmd.index('--network')+1]=='none' and '--offline' in cmd and '--locked' in cmd
    assert not any('evidence/original' in part for part in cmd)
    images[label]={k:read('builds/'+label+'/'+k+'.so.gz') for k in ('symbols','candidate')}
    for k,b in images[label].items():assert sha(b)==result[k+'_sha256']
    builds[label]=launch;results[label]=result
external=lambda deps:{n:v for n,v in deps.items() if 'native_transfer_fee' not in n}
assert len(external(builds['baseline']['dependencies_before']))==393
for label in ('candidate','repeat'):
    assert builds[label]['tools']==builds['baseline']['tools']
    assert external(builds[label]['dependencies_before'])==external(builds['baseline']['dependencies_before'])
assert results['candidate']['dependencies_after']==builds['repeat']['dependencies_before']
assert len(results['candidate']['dependencies_after'])==396
assert all('native_transfer_fee' in n for n in results['candidate']['changed_native_dependency_artifacts'])
assert images['candidate']==images['repeat']
assert sha(images['baseline']['candidate'])=='f7c4850c6529bf40ffc490753b0a3470aed9b5d630023c8a7df5bd3992c6dee6'
assert sha(images['candidate']['candidate'])=='785e9078efb31e8ff472075bd079394fba33d564e67371bac7c51461c7686b34'
static=runpy.run_path(str(HERE/'analyze.py'));helper=runpy.run_path(str(HERE/'helper.py'))
w=static['w'];original=static['blobs']['original'];originals=w.windows(original)
assert len(originals)==785 and sha(original)=='6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7'
matched={}
for label in ('baseline','candidate'):
    fs=w.windows(images[label]['symbols'])
    matched[label]=[Counter(f[k] for f in originals)&Counter(f[k] for f in fs) for k in ('signature','raw_sha256')]
assert [sum(c.values()) for c in matched['baseline']]==[733,148]
assert [sum(c.values()) for c in matched['candidate']]==[735,159]
a,b=static['out']['original'],helper['out']['original']
assert (a['address'],a['bytes'])==(0x74b80,688) and (b['address'],b['bytes'])==(0xf2ed0,776)
assert matched['candidate'][0]-matched['baseline'][0]==Counter([a['signature'],b['signature']])
assert not matched['baseline'][0]-matched['candidate'][0] and not matched['baseline'][1]-matched['candidate'][1]
assert len(static['out']['direct_calls'])==5 and len(static['out']['typed_references'])==7
assert static['out']['direct_calls'][0]['original']['address']==b['address']
assert [len(v) for v in static['out']['incoming'].values()]==[4,4,4]
assert static['out']['source_records']==[dict(offset=544,filename=source,line=67,error=6023)]
assert len(helper['out']['direct_calls'])==2 and not helper['out']['data_refs'] and helper['out']['raw_gain_count']==11
for label,length,match in [('early-max-control',92,False),('late-max',97,True)]:
    report=record('controls/'+label+'/report.json');launch=record('controls/'+label+'/launch.json')
    assert report['original_instructions']==97 and report['candidate_instructions']==length and report['equal_after_call_mask']==match
    assert report['source_sha256']==launch['source_sha256']==sha(read('controls/'+label+'/input.rs')) and launch['returncode']==0
native_ir=record('compiler/native/result.json');root_ir=record('compiler/root/result.json')
assert native_ir['returncode']==root_ir['returncode']==0 and native_ir['normal_object_equal'] and not native_ir['normal_rlib_equal']
assert root_ir['normal_stripped_equal'] and root_ir['dependencies_unchanged'] and root_ir['candidate_sha256']==sha(images['candidate']['candidate'])
def ar_members(data):
    assert data[:8]==b'!<arch>\n';pos=8;out=[]
    while pos<len(data):
        h=data[pos:pos+60];assert len(h)==60 and h[58:]==b'`\n';size=int(h[48:58]);pos+=60;out.append(data[pos:pos+size]);pos+=size+(size%2)
    assert pos==len(data)
    return out
assert read('compiler/native/normal.o.gz')==read('compiler/native/diagnostic.o.gz')
for label in ('normal','diagnostic'):
    lib=read('compiler/native/'+label+'.rlib.gz');obj=read('compiler/native/'+label+'.o.gz')
    assert sha(lib)==native_ir[label+'_rlib_sha256'] and sha(obj)==native_ir['object_sha256'][label]
    assert ar_members(lib).count(obj)==1
assert native_ir['normal_rlib_sha256']==results['candidate']['dependencies_after']['sbpf-solana-solana/release/libnative_transfer_fee.rlib']
ll=read('compiler/native/function.ll').decode()
assert ll.index('%_27 = load i64')>ll.index('udiv i128') and 'ptr %self, i64 8' not in ll.split('bb5:')[0]
assert b'%fee = alloca [24 x i8]' in read('compiler/root/function.ll')
assert b'_4 = (((*_1) as Some).0: native_transfer_fee::DecodedTransferFee);' in read('compiler/root/function.mir')
assert b'maximum_self' in read('failed-generator/native_transfer_fee.rs') and b'could not compile' in read('failed-generator/build.log')
exec(compile(read('runtime_audit.inc'),str(HERE/'runtime_audit.inc'),'exec'))
report=record('runtime/focused/report.json.gz')
errors=[r for r in report['cases'] if r['classification']=='other-rejection-review-logs']
assert len(errors)==2
assert all(any('transfer_fee.rs:67' in line and '6023' in line for line in r['original']['logs']) for r in errors)
print('PASS:733 ->735/785 normalized,148 ->159raw, no losses; complete inverse776B and caller688B;2+5 actual callees,7 typed references;2266 cached+216 fresh triples.')
