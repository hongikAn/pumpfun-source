"""Resealed finite negative controls; no compiler, producer or VM execution."""
if not __debug__:
    raise SystemExit("Run without -O")
import argparse,base64,copy,gzip,hashlib,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.dont_write_bytecode=True
SOURCE="programs/pump/src/token_incentives/claim_token_incentives.rs"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(path):
    raw=path.read_bytes();return json.loads(gzip.decompress(raw)if path.suffix=='.gz'else raw)
def save(path,value):
    raw=(json.dumps(value,indent=2)+'\n').encode();path.write_bytes(gzip.compress(raw,mtime=0)if path.suffix=='.gz'else raw)
def seal(packet):save(packet/'MANIFEST.json',{p.relative_to(packet).as_posix():sha(p.read_bytes())for p in packet.rglob('*')if p.is_file()and p.relative_to(packet).as_posix()!='MANIFEST.json'})
def repin(packet):
    path=packet/'runtime/observed/execution.json';value=load(path)
    for name in value['output_files']:
        raw=(path.parent/name).read_bytes();value['output_files'][name]=dict(sha256=sha(raw),bytes=len(raw))
    save(path,value);seal(packet)
def run(packet,repo=None):return subprocess.run([sys.executable,'-I','-B',str(packet/'verify.py'),'--repo-root',str(ROOT if repo is None else repo)],capture_output=True,text=True)
def report(packet,mutate):
    p=packet/'runtime/observed/eight.json.gz';v=load(p);mutate(v);save(p,v)
def duplicate(packet):report(packet,lambda v:v['cases'].__setitem__(1,copy.deepcopy(v['cases'][0])))
def signed_wrong_roles(packet):
    def change(v):
        for label in ['original','parent','candidate']:
            old,new=v['cases'][2],v['cases'][0];wire=old['runs'][label]['transaction_base64'];new['runs'][label]['transaction_base64']=new['observations'][label]['transaction_base64']=wire;new['observations'][label]['metadata']['signature']=old['observations'][label]['metadata']['signature']
    report(packet,change)
def invalid_signature(packet):
    def change(v):
        for label in ['original','parent','candidate']:
            row=v['cases'][0];wire=bytearray(base64.b64decode(row['runs'][label]['transaction_base64']));wire[1]^=1;row['runs'][label]['transaction_base64']=row['observations'][label]['transaction_base64']=base64.b64encode(wire).decode()
    report(packet,change)
def prestate(packet):
    def change(v):
        for label in ['original','parent','candidate']:v['cases'][0]['observations'][label]['before'][0]['lamports']+=1
    report(packet,change)
def empty_data(packet):
    def change(v):
        for label in ['original','parent','candidate']:
            rows=v['cases'][6]['observations'][label]['before'];row=next(r for r in rows if r.get('data_bytes')==0 and r.get('owner')not in ['11111111111111111111111111111111',None]);row['data_bytes']=1;row['data_sha256']=sha(b'\0')
    report(packet,change)
def loader(packet):
    def change(v):
        for label in ['original','parent','candidate']:v['cases'][0]['observations'][label]['loads'][0]['zero_allocation_tail']=False
    report(packet,change)
def loaded_program(packet):report(packet,lambda v:v['cases'][0]['observations']['candidate']['program_loads'][0].__setitem__('sha256','0'*64))
def metadata(packet):report(packet,lambda v:v['cases'][0]['observations']['candidate']['metadata']['logs'].append('invented raw log'))
def poststate(packet):
    def change(v):
        account=next(row for row in v['cases'][0]['runs']['candidate']['accounts'].values()if row is not None and not row['executable']);account['lamports']+=1
    report(packet,change)
def build_command(packet):
    p=packet/'build/candidate/launch.json';v=load(p);v['command'].append('--unreviewed');save(p,v)
def build_tools(packet):
    p=packet/'build/candidate/launch.json';v=load(p);v['tools']['rustc']='0'*64;save(p,v)
def receipt(packet,mutate):
    p=packet/'runtime/observed/execution.json';v=load(p);mutate(v);save(p,v)
def runtime_command(packet):receipt(packet,lambda v:v['command'].append('--unreviewed'))
def missing_output(packet):receipt(packet,lambda v:v['output_files'].pop('stderr.log'))
def stream(packet):
    p=packet/'runtime/observed/stdout.log';p.write_bytes(p.read_bytes()+b'changed stream\n')
def source_map(packet):
    p=packet/'source-parent.json';v=load(p);v['programs/pump/src/buy.rs']='0'*64;save(p,v)
def census_helper(packet):
    p=packet/'tools/pump_compare_function_bytes.py';p.write_bytes(p.read_bytes()+b'\n# unreviewed helper\n')
CONTROLS=[('duplicate case',duplicate,'exact source-owned eight definitions'),('valid signed wrong roles',signed_wrong_roles,'fixture signed account roles/order'),('invalid signature',invalid_signature,'verified canonical signed wire'),('coherent wrong prestate',prestate,'source-owned complete prestate'),('empty account data drift',empty_data,'source-owned complete prestate'),('allocation tail drift',loader,'captured loader actual image/allocation/zero-tail join'),('loaded program drift',loaded_program,'all actual loaded program hashes'),('raw metadata drift',metadata,'raw metadata/result join'),('post-state drift',poststate,'actual structured parity: accounts'),('literal Cargo command',build_command,'reviewed literal Cargo command'),('tool fingerprints',build_tools,'qualified v1.44 tool hashes'),('runtime command',runtime_command,'exact runtime command'),('missing output',missing_output,'exact runtime output membership'),('resealed stdout',stream,'actual runtime stdout projection'),('source map drift',source_map,'source map/archive join'),('normalizer drift',census_helper,'qualified census/normalizer helper')]

class EvidenceTests(unittest.TestCase):
    def test_optimized_guards(self):
        for name in ['verify.py','correspondence.py','test_verify.py','audit_refs.py']:
            with self.subTest(entrypoint=name):
                result=subprocess.run([sys.executable,'-I','-B','-O',str(HERE/name),'--repo-root','/nonexistent'],capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0);self.assertIn('Run without -O',result.stdout+result.stderr);self.assertNotIn('Traceback',result.stderr)
    def test_resealed_correspondence_controls(self):
        for name,mutate,reason in CONTROLS:
            with self.subTest(control=name),tempfile.TemporaryDirectory()as tmp:
                packet=Path(tmp)/'packet';shutil.copytree(HERE,packet);mutate(packet);repin(packet);result=run(packet)
                self.assertNotEqual(result.returncode,0);self.assertIn(reason,result.stderr)
    def test_wrong_output_hash(self):
        with tempfile.TemporaryDirectory()as tmp:
            packet=Path(tmp)/'packet';shutil.copytree(HERE,packet);receipt(packet,lambda v:v['output_files']['stdout.log'].__setitem__('sha256','0'*64));seal(packet);result=run(packet)
            self.assertNotEqual(result.returncode,0);self.assertIn('actual runtime output receipt join',result.stderr)
    def test_historical_inventory_pin(self):
        with tempfile.TemporaryDirectory()as tmp:
            packet=Path(tmp)/'packet';shutil.copytree(HERE,packet);p=packet/'tools/functions.tsv.gz';p.write_bytes(gzip.compress(gzip.decompress(p.read_bytes())+bytes([10]),mtime=0));seal(packet);result=run(packet)
            self.assertNotEqual(result.returncode,0);self.assertIn('qualified historical function-window inventory',result.stderr)
    def test_repository_source_binding(self):
        with tempfile.TemporaryDirectory()as tmp:
            repo=Path(tmp);p=repo/SOURCE;p.parent.mkdir(parents=True);p.write_bytes(b'wrong maintained source');result=run(HERE,repo)
            self.assertNotEqual(result.returncode,0);self.assertIn('maintained repository sources equal compiled candidate',result.stderr)
    def test_repository_fixture_binding(self):
        with tempfile.TemporaryDirectory()as tmp:
            repo=Path(tmp);(repo/'evidence').symlink_to(ROOT/'evidence',target_is_directory=True);p=repo/SOURCE;p.parent.mkdir(parents=True);p.write_bytes((ROOT/SOURCE).read_bytes());p=repo/'scripts/pump_cashback_differential.py';p.parent.mkdir(parents=True);p.write_bytes((ROOT/p.relative_to(repo)).read_bytes()+b'\n');result=run(HERE,repo)
            self.assertNotEqual(result.returncode,0);self.assertIn('repository fixture agrees',result.stderr)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repo-root',type=Path,default=ROOT);args,remaining=parser.parse_known_args();ROOT=args.repo_root.resolve();unittest.main(argv=[sys.argv[0],*remaining])
