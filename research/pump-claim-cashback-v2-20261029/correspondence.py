"""Finite source-owned cases, signed messages, setup bytes and retained receipt joins.
No producer, LiteSVM or compiler is imported or executed. This is consistency
verification of retained execution, not independent execution attestation.
"""
if not __debug__:
    raise SystemExit("Run without -O")
import base64,hashlib,json,re,struct
from pathlib import PurePosixPath
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.rent import Rent

def need(ok,message):
    if not ok:raise AssertionError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":")).encode()
PUMP="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
TOKEN="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN22="TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
ATA="ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
WSOL="So11111111111111111111111111111111111111112"
SYSTEM="11111111111111111111111111111111"
PROGRAMS=[(TOKEN,"spl_token"),(TOKEN22,"spl_token_2022"),(ATA,"associated_token")]

def definitions():
    result=[]
    for mode in [{'v2':True},{'v2':True,'token_quote':True},{'v2':True,'token_quote':True,'token22':True}]:
        variants=[{},{'lamports':1628640}]if not mode.get('token_quote')else[{},{'token_balance':0}]
        for variant in variants:result.append(dict(mode,**variant,name=f'mode{mode}-state{variant}'))
    for token22 in [False,True]:
        mode={'v2':True,'token_quote':True}
        if token22:mode['token22']=True
        mutation={'length':0}
        result.append(dict(mode,name=f'v2mut{mode}-associated_user_volume_accumulator-{mutation}',mutations={'associated_user_volume_accumulator':mutation}))
    return result

def key(value):return Pubkey.from_string(value)
def pda(seeds,program):return str(Pubkey.find_program_address(seeds,key(program))[0])
def addresses(case):
    user=str(Keypair.from_seed(bytes([229])*32).pubkey());payer=str(Keypair.from_seed(bytes([228])*32).pubkey())
    vol=pda([b'user_volume_accumulator',bytes(key(user))],PUMP)
    mint=str(Pubkey.from_bytes(bytes([71])*32))if case.get('token_quote')else WSOL
    tp=TOKEN22 if case.get('token22')else TOKEN
    ata=lambda owner:pda([bytes(key(owner)),bytes(key(tp)),bytes(key(mint))],ATA)
    return dict(user=user,payer=payer,user_volume_accumulator=vol,quote_mint=mint,quote_token_program=tp,system_program=SYSTEM,event_authority=pda([b'__event_authority'],PUMP),program=PUMP,associated_token_program=ATA,associated_user_volume_accumulator=ata(vol),associated_quote_user=ata(user))

def check_wire(result,observation,case,idl):
    a=addresses(case);declared=next(v for v in idl['instructions']if v['name']=='claim_cashback_v2')
    metas=[(a[v['name']],bool(v.get('signer')),bool(v.get('writable')))for v in declared['accounts']]
    wire=base64.b64decode(result['transaction_base64'],validate=True);tx=Transaction.from_bytes(wire);msg=tx.message
    need(bytes(tx)==wire and len(tx.signatures)==1 and all(tx.verify_with_results()),'verified canonical signed wire')
    need(result['signatures_verified']is True and observation['signatures_verified']is True and observation['transaction_base64']==result['transaction_base64'],'observer signed wire join')
    need(str(tx.signatures[0])==observation['metadata']['signature'],'metadata signature join')
    need(len(msg.instructions)==1 and str(msg.account_keys[0])==a['payer'],'fixture exact instruction count/payer')
    ix=msg.instructions[0]
    need(str(msg.account_keys[ix.program_id_index])==PUMP and bytes(ix.data)==bytes(declared['discriminator']),'fixture signed claim instruction')
    need([str(msg.account_keys[i])for i in ix.accounts]==[k for k,s,w in metas],'fixture signed account roles/order')
    effective={PUMP:(False,False),a['payer']:(True,True)}
    for k,s,w in metas:
        os,ow=effective.get(k,(False,False));effective[k]=(s or os,w or ow)
    keys=list(map(str,msg.account_keys));need(len(set(keys))==len(keys)and set(keys)==set(effective),'fixture signed key membership')
    h=msg.header
    for i,k in enumerate(keys):
        signer=i<h.num_required_signatures;writable=i<h.num_required_signatures-h.num_readonly_signed_accounts if signer else i<len(keys)-h.num_readonly_unsigned_accounts
        need((signer,writable)==effective[k],'fixture signed effective privileges')
    return a,keys

def account(raw,lamports,owner,executable=False):return dict(raw=bytes(raw),lamports=lamports,owner=owner,executable=executable)
def source_prestate(case,repo,program,capture):
    a=addresses(case);tp=a['quote_token_program'];user=a['user'];vol=a['user_volume_accumulator'];mint=a['quote_mint']
    state={a['payer']:account(b'',10**11,SYSTEM),user:account(b'',10**8,SYSTEM)}
    raw=bytearray(hashlib.sha256(b'account:UserVolumeAccumulator').digest()[:8]+bytes(key(user))+bytes(66))
    for offset,value in [(74,1000),(82,200),(90,3000),(98,400)]:struct.pack_into('<Q',raw,offset,value)
    state[vol]=account(raw,case.get('lamports',10000000),PUMP)
    raw=bytearray(82);struct.pack_into('<Q',raw,36,10**12);raw[44]=6;raw[45]=1;state[mint]=account(raw,10**9,tp)
    for name,owner,amount in [('associated_user_volume_accumulator',vol,case.get('token_balance',5000)),('associated_quote_user',user,100)]:
        raw=bytearray(165);raw[:32]=bytes(key(mint));raw[32:64]=bytes(key(owner));struct.pack_into('<Q',raw,64,amount);raw[108]=1
        if name in case.get('mutations',{}):
            need(case['mutations']=={'associated_user_volume_accumulator':{'length':0}},'only selected empty-account mutation');raw=bytearray()
        state[a[name]]=account(raw,10**8,tp)
    state[PUMP]=account(program,Rent.default().minimum_balance(36),capture['owner'],True)
    # Fixed built-in runtime identity, explicit retained-cohort assumption.
    state[SYSTEM]=account(b'system_program',1,'NativeLoader1111111111111111111111111111111',True)
    for pid,name in PROGRAMS:
        raw=(repo/'evidence/dependencies'/name/'deployed.so').read_bytes()
        state[pid]=account(raw,Rent.default().minimum_balance(len(raw)),'BPFLoader2111111111111111111111111111111111',True)
    state[a['event_authority']]=None
    return state

def prestate(result,observation,case,repo,keys,program,capture):
    state=source_prestate(case,repo,program,capture)
    need([r['key']for r in observation['before']]==keys,'observer exact signed key order')
    for row in observation['before']:
        k=row['key'];need(k in state,'known fixture account');expected=state[k]
        if expected is None:need(row==dict(key=k,missing=True),'source missing prestate')
        else:
            raw=expected['raw'];need(row==dict(key=k,owner=expected['owner'],lamports=expected['lamports'],data_bytes=len(raw),data_sha256=sha(raw),executable=expected['executable']),'source-owned complete prestate')
    need(set(result['accounts'])==set(keys)-{PUMP},'post-state signed key membership')
    for k,row in result['accounts'].items():
        if row is None:continue
        need(set(row)=={'lamports','owner','data','executable'}and isinstance(row['lamports'],int)and row['lamports']>=0 and isinstance(row['executable'],bool),'post-state record shape')
        if row['executable']:need(row['data']is None,'fixture executable post-state projection')
        else:base64.b64decode(row['data'],validate=True)

METER=re.compile(r'^Program [1-9A-HJ-NP-Za-km-z]+ consumed [0-9]+ of [0-9]+ compute units$')
def logs(result):return [s for s in result['logs']if not METER.fullmatch(s)]

def outputs_and_inputs(packet,repo,read,doc):
    raw=(packet/'runtime/input-map.json').read_bytes();need(sha(raw)=='1c7c3262387227ca4ce87cc261359eaf1271521943de89836406ce1a7b432588','reviewed complete runtime input map');mapping=json.loads(raw)
    folder=packet/'runtime/observed';e=doc(folder/'execution.json')
    need(e['returncode']==0,'successful actual runtime receipt')
    need(sha(canonical(e['command']))=='f93468970fd7c2ed63e5fb2c32f9f143c367eb0ed112e5ccc4994387ba303bd2','exact runtime command')
    need(len(mapping)==len(e['inputs'])==29 and {r['actual_path']for r in mapping}==set(e['inputs'])==set(e['inputs_unchanged'])and all(v is True for v in e['inputs_unchanged'].values()),'exact runtime input membership/preservation')
    checked=host=0
    for row in mapping:
        expected={k:row[k]for k in ['sha256','bytes']};need(e['inputs'][row['actual_path']]==expected,'runtime source input receipt')
        if row['kind']=='host-runtime':host+=1;continue
        path=PurePosixPath(row['path']);need(not path.is_absolute()and '..'not in path.parts,'safe mapped input');need(row['kind']in['packet','repo'],'known input kind');root=packet if row['kind']=='packet'else repo
        data=read(root/row['path']);need(dict(sha256=sha(data),bytes=len(data))==expected,'actual runtime input bytes');checked+=1
    outputs={'eight.json.gz','stdout.log','stderr.log'}
    need(set(e['output_files'])==outputs and {p.name for p in folder.iterdir()if p.is_file()}==outputs|{'execution.json'},'exact runtime output membership')
    for name in outputs:
        raw=(folder/name).read_bytes();need(e['output_files'][name]==dict(sha256=sha(raw),bytes=len(raw)),'actual runtime output receipt join')
    need(checked==27 and host==2,'finite receipt totals')
    return dict(input_records=29,packet_or_repository_byte_joins=checked,pinned_host_fingerprints=host,output_files=3,execution_receipts=1)

def verify(packet,repo,images,read,doc):
    receipts=outputs_and_inputs(packet,repo,read,doc)
    script_pins={'pump_cashback_differential.py':'05d99973eab0e31e1fdb6a0062424f38bfb27d44aa2561b14e073193ab8534db','pump_trade_fixture.py':'9ee647c928070734fe700929b87d4016f76ec244c873e6f484318b5212aea1e1','pump_captured_loader.py':'8d51ba5feab9e74f67fb80f5827222308d45a36022151bc77ad076c401f65067'}
    for name,digest in script_pins.items():
        raw=(packet/'runtime/inputs'/name).read_bytes();need(sha(raw)==digest,'exact executed fixture/loader bytes')
        if name!='pump_captured_loader.py':need(raw==(repo/'scripts'/name).read_bytes(),'repository fixture agrees')
    need(sha((packet/'runtime/focused_runtime.py').read_bytes())=='2cb23139819d2f48c6ce60912637f1dc9425b1158faf822611809b85ebd911a7','exact eight-case observer')
    original=(repo/'evidence/original/pump/deployed.so').read_bytes();raw={'original':original,'parent':images['parent']['candidate'],'candidate':images['candidate']['candidate']};hashes={k:sha(v)for k,v in raw.items()}
    capture=doc(repo/'evidence/original/pump/capture.json');program=(repo/'evidence/original/pump/program-account.bin').read_bytes();pd=(repo/'evidence/original/pump/programdata-account.bin').read_bytes();header=pd[:45]
    need(sha(original)=='7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'and pd[45:]==original and sha(pd)==capture['programdata_sha256']and sha(original)==capture['payload_sha256']and len(original)==capture['payload_bytes'],'captured allocation/payload join')
    need(len(program)==36 and program[4:]==bytes(key(capture['programdata'])),'captured Program account')
    load_receipts={}
    for label,value in raw.items():
        need(len(value)<=len(original),'ELF allocation bound');allocated=header+value+bytes(len(original)-len(value))
        load_receipts[label]=dict(elf_sha256=sha(value),elf_bytes=len(value),program_owner=capture['owner'],program_bytes=len(program),program_sha256=sha(program),programdata_bytes=len(allocated),programdata_sha256=sha(allocated),header_sha256=sha(header),elf_prefix_unchanged=True,zero_allocation_tail=True,slot=struct.unpack_from('<Q',header,4)[0]+1)
    dependencies={pid:sha((repo/'evidence/dependencies'/name/'deployed.so').read_bytes())for pid,name in PROGRAMS}
    report=doc(packet/'runtime/observed/eight.json.gz');need(report['images_sha256']==hashes,'report actual image identities')
    need(report['producer_sha256']==sha((packet/'runtime/focused_runtime.py').read_bytes())and report['fixture_sha256']==script_pins['pump_cashback_differential.py'],'actual producer/fixture script')
    need([row['case']for row in report['cases']]==definitions(),'exact source-owned eight definitions')
    idl=doc(repo/'evidence/upstream/pump.json');signed=loads=paid=empty=0;outcomes=[]
    for i,row in enumerate(report['cases']):
        runs=row['runs'];observations=row['observations'];case=row['case'];need(set(runs)==set(observations)==set(raw),'three actual role membership')
        for label,result in runs.items():
            observation=observations[label];a,keys=check_wire(result,observation,case,idl);signed+=1;prestate(result,observation,case,repo,keys,program,capture)
            meta=observation['metadata'];need(meta['logs']==result['logs']and meta['inner_instructions']==result['inner']and meta.get('return_data')==result['return_data'],'raw metadata/result join')
            need(result['events']==[s[14:]for s in result['logs']if s.startswith('Program data: ')],'event ordered log projection')
            need(result['error']is None and len(result['events'])==(1 if i in [0,2,4]else 0)and sum('No cashback to claim'in s for s in result['logs'])==(0 if i in [0,2,4]else 1),'declared paid/zero-exit outcome')
            need(len(observation['loads'])==1,'one captured Pump load');receipt=dict(observation['loads'][0]);need(isinstance(receipt.pop('input_path'),str),'loader input label');need(receipt==load_receipts[label],'captured loader actual image/allocation/zero-tail join');loads+=1
            expected_loads=[dict(program=PUMP,sha256=hashes[label])]+[dict(program=pid,sha256=dependencies[pid])for pid,_ in PROGRAMS]
            need(observation['program_loads']==expected_loads,'all actual loaded program hashes')
            if label!='original':
                for field in ['error','accounts','events','inner','return_data','transaction_base64']:need(result[field]==runs['original'][field],'actual structured parity: '+field)
                need(logs(result)==logs(runs['original']),'actual ordered non-compute log parity')
        need(row['differences']=={'parent':[],'candidate':[]}and row['ordered_log_equal']=={'parent':True,'candidate':True},'retained parity summaries')
        paid+=i in [0,2,4];empty+=i in [6,7];outcomes.append(dict(case=case['name'],error=None,paid=i in[0,2,4]))
    expected_stdout=[dict(case=row['case']['name'],errors={k:v['error']for k,v in row['runs'].items()},differences=row['differences'],ordered_log_equal=row['ordered_log_equal'],notices={k:sum('No cashback to claim'in line for line in v['logs'])for k,v in row['runs'].items()})for row in report['cases']]
    try:actual_stdout=[json.loads(line)for line in (packet/'runtime/observed/stdout.log').read_text().splitlines()]
    except(ValueError,UnicodeError):raise AssertionError('actual runtime stdout projection')
    need(actual_stdout==expected_stdout and (packet/'runtime/observed/stderr.log').read_bytes()==b'','actual runtime stdout projection')
    need(signed==loads==24 and paid==3 and empty==2,'eight triples/24 signatures/three paid/two empty-account exits')
    return dict(case_triples=8,executions=24,verified_signatures=signed,captured_loader_records=loads,original_successes=8,paid_cases=paid,zero_exit_cases=5,empty_token_account_cases=empty,structured_or_ordered_log_mismatches=0,receipts=receipts,outcomes=outcomes,limitations=['Retained reports are not independent execution attestation.','Runtime builtin System program and default rent are fixed cohort assumptions; no LiteSVM replay.','No independent post-state snapshot; complete post-state is compared across the three reports.','Executed loader is pinned historical R bytes, not the newer maintained caching implementation.','No errors, borrow conflicts, overflow, transfer-fee or broad-case runtime coverage.'])
