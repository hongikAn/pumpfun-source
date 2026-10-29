"""Eight unchanged source-owned claim_v2 cases, with captured-loader and signed-wire observations."""
from pathlib import Path
import sys,argparse,base64,gzip,hashlib,json,re
sys.dont_write_bytecode=True
R=Path('/mnt/c/Users/ahi20/Documents/ChatGPT/pumpfun-source');sys.path.insert(0,str(R/'scripts'))
import pump_captured_loader as loader
loader.install()
import pump_cashback_differential as fixture
f=fixture.f;Base=f.LiteSVM;SENDS=[]
class ObservedVM(Base):
 def add_program_from_file(self,pid,path):
  digest=hashlib.sha256(Path(path).read_bytes()).hexdigest();answer=super().add_program_from_file(pid,path);assert digest==hashlib.sha256(Path(path).read_bytes()).hexdigest()
  if not hasattr(self,'observed_loads'):self.observed_loads=[]
  self.observed_loads.append(dict(program=str(pid),sha256=digest));return answer
 def send_transaction(self,tx):
  before=[]
  for key in tx.message.account_keys:
   a=self.get_account(key);before.append(dict(key=str(key),owner=str(a.owner),lamports=a.lamports,data_bytes=len(a.data),data_sha256=hashlib.sha256(a.data).hexdigest(),executable=a.executable)if a else dict(key=str(key),missing=True))
  result=super().send_transaction(tx);failed=isinstance(result,f.FailedTransactionMetadata);meta=result.meta()if failed else result
  SENDS.append(dict(transaction_base64=base64.b64encode(bytes(tx)).decode(),signatures_verified=all(tx.verify_with_results()),before=before,metadata=json.loads(meta.to_json()),loads=list(loader.LOADS),program_loads=self.observed_loads));return result
f.LiteSVM=ObservedVM

def selected_cases():
 all_cases=fixture.cases();chosen=[]
 for mode in [{'v2':True},{'v2':True,'token_quote':True},{'v2':True,'token_quote':True,'token22':True}]:
  variants=[{} ,{'lamports':1628640}]if not mode.get('token_quote')else[{}, {'token_balance':0}]
  for variant in variants:
   expected=dict(mode,**variant);matches=[c for c in all_cases if{k:v for k,v in c.items()if k!='name'}==expected];assert len(matches)==1;chosen.append(matches[0])
 for token22 in [False,True]:
  expected={'v2':True,'token_quote':True,'mutations':{'associated_user_volume_accumulator':{'length':0}}}
  if token22:expected['token22']=True
  matches=[c for c in all_cases if{k:v for k,v in c.items()if k!='name'}==expected];assert len(matches)==1;chosen.append(matches[0])
 assert len(chosen)==8;return chosen

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();assert not a.output.exists();images={'original':R/'evidence/original/pump/deployed.so','parent':a.parent.resolve(),'candidate':a.candidate.resolve()};rows=[];units=re.compile(r'^Program [1-9A-HJ-NP-Za-km-z]+ consumed [0-9]+ of [0-9]+ compute units$')
 for case in selected_cases():
  runs={};obs={}
  for label,path in images.items():
   SENDS.clear();loader.LOADS.clear();runs[label]=fixture.run(case,path);assert len(SENDS)==1;obs[label]=SENDS[0]
  fields=['error','accounts','events','inner','return_data','transaction_base64'];diff=lambda label:[k for k in fields if runs[label][k]!=runs['original'][k]];logs=lambda label:[s for s in runs[label]['logs']if not units.fullmatch(s)]
  row=dict(case=case,runs=runs,observations=obs,differences={label:diff(label)for label in ['parent','candidate']},ordered_log_equal={label:logs(label)==logs('original')for label in ['parent','candidate']});rows.append(row);print(json.dumps(dict(case=case['name'],errors={k:v['error']for k,v in runs.items()},differences=row['differences'],ordered_log_equal=row['ordered_log_equal'],notices={k:sum('No cashback to claim'in x for x in v['logs'])for k,v in runs.items()})),flush=True)
 report=dict(scope=__doc__,images_sha256={k:hashlib.sha256(v.read_bytes()).hexdigest()for k,v in images.items()},producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),fixture_sha256=hashlib.sha256(Path(fixture.__file__).read_bytes()).hexdigest(),cases=rows);a.output.write_bytes(gzip.compress(json.dumps(report,separators=(',',':')).encode(),mtime=0));assert all(not d for r in rows for d in r['differences'].values());assert all(v for r in rows for v in r['ordered_log_equal'].values())
if __name__=='__main__':main()
