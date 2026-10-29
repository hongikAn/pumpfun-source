#!/usr/bin/env python3
"""Finite retained-evidence verifier. No compiler, producer, VM, or network execution.
Requires Python 3 and solders (qualified runtime version 0.27.1).
Consistency and signed-wire checks are not independent execution attestation.
"""
if not __debug__:
    raise SystemExit("Run without -O")
import argparse,difflib,gzip,hashlib,importlib.util,json,stat,sys,tarfile
from pathlib import Path,PurePosixPath
sys.dont_write_bytecode=True
ORIGINAL_SHA="7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"
SOURCE_PATH="programs/pump/src/token_incentives/claim_token_incentives.rs"
SOURCE_PATHS=(SOURCE_PATH,)
LABELS=("parent","candidate")
def require(ok,message):
    if not ok:raise AssertionError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":")).encode()
def read(path):
    raw=path.read_bytes();return gzip.decompress(raw)if path.suffix==".gz"else raw
def doc(path):return json.loads(read(path))
def relative(name):
    p=PurePosixPath(name)
    require(p.parts and not p.is_absolute()and ".."not in p.parts and "\\"not in name,"unsafe relative path")
    return p.as_posix()
def manifest(packet):
    require(not packet.is_symlink(),"packet root symlink")
    actual={}
    for p in packet.rglob("*"):
        mode=p.lstat().st_mode
        require(stat.S_ISDIR(mode)or stat.S_ISREG(mode),"non-regular packet entry")
        if p.is_file()and p.relative_to(packet).as_posix()!="MANIFEST.json":actual[p.relative_to(packet).as_posix()]=sha(p.read_bytes())
    saved=doc(packet/"MANIFEST.json")
    require(isinstance(saved,dict)and saved==actual,"MANIFEST hash/membership differs")
    for name in saved:relative(name)
    return len(actual)
def archive(path):
    files={}
    with tarfile.open(path,"r:gz")as tf:
        for member in tf:
            name=relative(member.name)
            if member.isdir():continue
            require(member.isfile()and name not in files,"archive nonregular/duplicate member")
            files[name]=tf.extractfile(member).read()
    return files

def sources(packet,repo):
    files={label:archive(packet/("source-"+label+".tar.gz"))for label in LABELS}
    maps={label:{k:sha(v)for k,v in rows.items()}for label,rows in files.items()}
    require(len(maps["parent"])==len(maps["candidate"])==66 and maps["parent"].keys()==maps["candidate"].keys(),"66-source membership")
    require(sha(canonical(maps["parent"]))=="a4c2686840a534a8cf15b66de7105e7a2a8453e144fbd8e5bd6d9e3ac85bf8ef","selected B13 parent source identity")
    for label in LABELS:require(maps[label]==doc(packet/("source-"+label+".json")),"source map/archive join")
    require([k for k in files["parent"]if files["parent"][k]!=files["candidate"][k]]==[SOURCE_PATH],"only reviewed claim source changed")
    a,b=[files[label][SOURCE_PATH].splitlines(keepends=True)for label in LABELS]
    require(len(a)==len(b)==350,"preserved physical source line counts")
    require([i+1 for i,(x,y)in enumerate(zip(a,b))if x!=y]==[311],"one reviewed physical source line")
    old=b"let amount=if native{a.user_volume_accumulator.to_account_info().lamports().saturating_sub(Rent::get()?.minimum_balance(a.user_volume_accumulator.to_account_info().data_len()))}else{let data=a.associated_user_volume_accumulator.try_borrow_data()?;if data.is_empty(){0}else{TokenAccount::try_deserialize(&mut &data[..])?.amount}};"
    new=b"let amount=if native{a.user_volume_accumulator.to_account_info().lamports().saturating_sub(Rent::get()?.minimum_balance(a.user_volume_accumulator.to_account_info().data_len()))}else if a.associated_user_volume_accumulator.data_is_empty(){0}else{let data=a.associated_user_volume_accumulator.try_borrow_data()?;TokenAccount::try_deserialize(&mut &data[..])?.amount};"
    require((a[310].strip(),b[310].strip())==(old,new),"exact pre-borrow empty account guard")
    patch="".join(difflib.unified_diff([x.decode()for x in a],[x.decode()for x in b],fromfile="a/"+SOURCE_PATH,tofile="b/"+SOURCE_PATH))
    require((packet/"source.patch").read_bytes()==patch.encode(),"exact source patch")
    return maps

def builds(packet,inputs):
    commands={"parent":"0b071b9760df92fce2ca3e03cbdb3752b2dfae5090ff02ed82977143c0281fd2","candidate":"b798d56df89d826a3bb63d36d8228301105e317d9e77f09df837d47326a01b70"}
    tools={"rustc":"c8807b7ebede8578ac5a257ea333780f9d89bd356064fd8184af7e996cb71a97","cargo":"d28444578306fe5a4f40524331411340123004e9e6556322fcabdbe351fe265d","objcopy":"f078d5b1f9df4190e67938a13e81e1dda1057e16228ff1a6f2f5d5540c9e6aaf"}
    image_pins={'parent': {'symbols': 'b79428215bac7c4cb487681ea3a5cdad84197fcaa04142a0e68f4a4706008898', 'candidate': 'a1a9223a33274b687d263a7ed263dbbd29429abe9532a61c3959b4d5b6e6bd2e'}, 'candidate': {'symbols': 'de53785cbf8a02ff962eebd6c365db7a85b7755d5c09d1d531c650f6ca4f2975', 'candidate': '10252ecd3dd7054efb12ef905ad40d972a477be85bcb320d46052371a80a302d'}}
    images={}
    for label in LABELS:
        folder=packet/"build"/label;launch=doc(folder/"launch.json");result=doc(folder/"result.json")
        require(launch["inputs"]==inputs[label],"build source hash join")
        require(result["returncode"]==0 and result["inputs_unchanged"]is True and result["actual_root_compilations"]==1,"successful actual build record")
        require(sha(canonical(launch["command"]))==commands[label],"reviewed literal Cargo command")
        require(launch["tools"]==tools,"qualified v1.44 tool hashes")
        require(launch["controller_sha256"]==sha((packet/"controllers/local_build.py").read_bytes())=="771d9295ee6e8997546b2f0cde677213f23d9d31528a6df33293b9a284911eea","actual build controller")
        log=read(folder/"build.log.gz").decode()
        require(sum(x.strip().startswith("Running ")and "--crate-name pump_recovered "in x for x in log.splitlines())==1,"one actual root compilation")
        images[label]={kind:read(folder/(kind+".so.gz"))for kind in ["symbols","candidate"]}
        for kind,raw in images[label].items():require(sha(raw)==result[kind+"_sha256"]==image_pins[label][kind],"build ELF hash join")
    return images

def binary(packet,repo,images):
    pins={'census.py': '804b88102b69c7bf41f7a3f751454bf9d4d1c89cc36fb7e7f52bdc89f28b9d5c', 'pump_compare_function_bytes.py': '43fa359dce1e398f820df445d534e0912ac5f181f1ea15e13a5267b53105b075', 'pump_quote_control_function_match.py': '28ad656012f8fbcd41ed1726e9345ee76f6249992bf28c91c4b9202479d3e94e'}
    for name,digest in pins.items():require(sha((packet/"tools"/name).read_bytes())==digest,"qualified census/normalizer helper")
    # Recompute whole-window membership using the retained census implementation.
    import tempfile
    inventory=read(packet/"tools/functions.tsv.gz")
    require(sha(inventory)=="fb2c0a47514567d65eb45c1e268dacd5291e4659bb7dceb575a767dc20bcaff8","qualified historical function-window inventory")
    sys.path.insert(0,str(packet/"tools"));import census
    original=(repo/"evidence/original/pump/deployed.so").read_bytes()
    require(sha(original)==ORIGINAL_SHA,"original ELF identity")
    os_=census.sections(original);on,_=census.normalize(census.body(original,os_,0x77940,8832),0x77940,os_)
    counts={"total":1035,"normalized":1019,"raw":183,"unmatched":16,"matched_text_bytes":1611088}
    memberships=[];report={}
    with tempfile.TemporaryDirectory(prefix="pump-cashback-verify-")as tmp:
        # Current main removed this historical inventory. Keep the qualified
        # denominator explicit without changing the retained census helper.
        census_root=Path(tmp)/"census-root"
        for relative_path,raw in [("evidence/original/pump/deployed.so",original),("repro/reconstruction-status-2026-10-26/functions.tsv",inventory)]:
            target=census_root/relative_path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        census.ROOT=census_root
        for label,size,expected in [("parent",8464,1583),("candidate",8448,1582)]:
            blob=images[label]["symbols"];path=Path(tmp)/(label+".so");path.write_bytes(blob);sections=census.sections(blob)
            matches=[f for f in census.functions(blob)if f[2]=="_ZN14pump_recovered16token_incentives22claim_token_incentives8cashback8claim_v217h3c04a783ac0454a6E"]
            require(len(matches)==1 and matches[0][1]==size,"unique target size")
            addr,_,_=matches[0];norm,_=census.normalize(census.body(blob,sections,addr,size),addr,sections)
            slots=lambda b:[b[i:i+8]for i in range(0,len(b),8)]
            aligned=sum(max(j-i,l-k)for op,i,j,k,l in difflib.SequenceMatcher(None,slots(on),slots(norm),autojunk=False).get_opcodes()if op!="equal")
            require(aligned==expected and norm!=on,"partial alignment diagnostic")
            full=census.census(path);require(full==doc(packet/"build"/label/"census.json.gz")and full["counts"]==counts,"recomputed full census")
            membership={w["start"]:(bool(w["normalized_matches"]),w["raw_match"])for w in full["windows"]};require(membership[0x77940]==(False,False),"target remains unmatched");memberships.append(membership)
            stripped=images[label]["candidate"];ss=census.sections(stripped)
            for name in [".text",".rodata",".data.rel.ro"]:
                a,b=sections[name],ss[name];require(a["addr"]==b["addr"]and blob[a["offset"]:a["offset"]+a["size"]]==stripped[b["offset"]:b["offset"]+b["size"]],"strip section identity")
            report[label]={"bytes":size,"aligned_differing_8byte_slots":aligned}
    require(memberships[0]==memberships[1],"no whole-window gain or loss")
    return dict(original_bytes=8832,counts=counts,whole_target_equal=False,**report)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--repo-root",type=Path,required=True);args=parser.parse_args()
    packet=Path(__file__).resolve().parent;repo=args.repo_root.resolve();files=manifest(packet)
    candidate_sources=archive(packet/"source-candidate.tar.gz")
    require(all((repo/name).read_bytes()==candidate_sources[name]for name in SOURCE_PATHS),"maintained repository sources equal compiled candidate")
    inputs=sources(packet,repo);images=builds(packet,inputs)
    spec=importlib.util.spec_from_file_location("multihop_correspondence",packet/"correspondence.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    runtime=module.verify(packet,repo,images,read,doc)
    binary_report=binary(packet,repo,images)
    print(json.dumps(dict(verified=True,scope="Retained consistency and signatures, not execution attestation; no compiler or VM replay.",manifest_files=files,source_files=66,changed_source_lines={SOURCE_PATH:[311]},build_records=2,new_normal_compilations=1,reused_selected_parent_compilations=1,repeat_build_claim=False,binary=binary_report,runtime=runtime),indent=2))
if __name__=="__main__":main()
