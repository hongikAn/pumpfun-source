from pathlib import Path
import os,sys,json,gzip,re,hashlib,importlib,copy,base64
R=Path('/mnt/c/Users/ahi20/Documents/ChatGPT/pumpfun-source');D=Path('/home/ahi200/pumpfun-work/20261028-amm-inverse-arithmetic');B=Path('/home/ahi200/pumpfun-work/20261028-amm-fee-wrapper');family=sys.argv[1];O=D/('fee-runtime-'+family);O.mkdir(exist_ok=False);os.chdir(R);sys.path.insert(0,str(R/'scripts'));os.environ['PUMP_AMM_FRESH_VM']='0'
module,entry={'buy':('pump_amm_legacy_buy_differential','legacy_buy'),'sell':('pump_amm_legacy_sell_differential','legacy'),'sweep':('pump_amm_sweep_differential','sweep'),'liquidity':('pump_amm_liquidity_differential','run')}[family];h=importlib.import_module(module)
from solders.litesvm import LiteSVM
from solders.transaction_metadata import FailedTransactionMetadata
actual_send=LiteSVM.send_transaction;sent=None
# Preserve full signed transaction and account state even for the older sweep API.
def send(self,tx):
 global sent
 def snapshot():
  out={}
  for key in sorted(tx.message.account_keys,key=str):
   a=self.get_account(key)
   if not a or not a.executable:out[str(key)]=None if not a else {'data_hex':bytes(a.data).hex(),'lamports':a.lamports,'owner':str(a.owner)}
  return out
 before=snapshot();raw=bytes(tx);result=actual_send(self,tx);meta=result.meta() if isinstance(result,FailedTransactionMetadata) else result
 sent={'transaction_base64':base64.b64encode(raw).decode(),'observed_before':before,'observed_after':snapshot(),'observed_return_data':json.loads(meta.to_json()).get('return_data')};return result
LiteSVM.send_transaction=send
base=B/'value-match/candidate.so';candidate=D/'native-corrected/candidate.so';actual=getattr(h,entry);original=None;rows=[]
norm=lambda logs:[x for x in logs if not re.fullmatch(r'Program \S+ consumed \d+ of \d+ compute units',x)]
file=gzip.open(O/'triples.jsonl.gz','wt')
def run(*args,**kw):
 global original
 def invoke(params):
  result=actual(*args,**params);result.update(sent);return result
 if kw.get('candidate') is None:
  original=invoke(kw);return original
 baseline=invoke(dict(kw,candidate=base));result=invoke(kw)
 diffs={label:[k for k in original if k!='logs' and original[k]!=v[k]] for label,v in [('baseline',baseline),('candidate',result)]};same={label:norm(original['logs'])==norm(v['logs']) for label,v in [('baseline',baseline),('candidate',result)]};i=len(rows);rows.append({'index':i,'diffs':diffs,'log_equal':same});file.write(json.dumps({'index':i,'results':{'original':original,'baseline':baseline,'candidate':result}},separators=(',',':'))+'\n')
 if len(rows)%100==0:print(family,'completed',len(rows),'case triples',flush=True)
 return result
setattr(h,entry,run);sys.argv=[module+'.py','--candidate',str(candidate),'--output',str(O/'suite.json')]
try:h.main()
except SystemExit as e:code=e.code
else:code=0
file.close();report=json.loads((O/'suite.json').read_text());(O/'case-labels.json').write_text(json.dumps([{k:v for k,v in row.items() if k not in ['original','candidate']} for row in report['cases']],indent=2)+'\n');summary={'family':family,'case_count':len(rows),'returncode':code,'fresh_vm':False,'functional_mismatches':{k:[r['index'] for r in rows if r['diffs'][k]] for k in ['baseline','candidate']},'noncompute_log_mismatches':{k:sum(not r['log_equal'][k] for r in rows) for k in ['baseline','candidate']},'log_gains':[r['index'] for r in rows if not r['log_equal']['baseline'] and r['log_equal']['candidate']],'log_losses':[r['index'] for r in rows if r['log_equal']['baseline'] and not r['log_equal']['candidate']],'artifact_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in [('original',R/'evidence/original/pump_amm/deployed.so'),('baseline',base),('candidate',candidate)]},'controller_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(O/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
