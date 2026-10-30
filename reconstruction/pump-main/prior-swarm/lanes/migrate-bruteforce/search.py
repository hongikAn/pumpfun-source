#!/usr/bin/env python3
"""Bounded, source-deduped create_token_account_v2 composition search.

Only lanes/migrate-bruteforce is mutated, apart from the shared attempt ledger and
the harness's shared build-slot locks. Acceptance is exclusively tools/harness/score.py.
"""
from pathlib import Path
import argparse
import collections
import contextlib
import difflib
import gzip
import hashlib
import io
import json
import subprocess
import sys

LANE = Path(__file__).resolve().parent
SWARM = LANE.parents[1]
REPO = SWARM.parent.parent
HARNESS = SWARM / "tools/harness"
sys.path[:0] = [str(HARNESS), str(LANE / "tools")]
import fastbuild  # noqa: E402
import score  # noqa: E402
import win  # noqa: E402
import cfg_attribution as cfg  # noqa: E402

TARGET = 0x4C158
TARGET_NAME = "migrate_v2::create_token_account_v2"
ORIGINAL_BYTES = 8368
ORIGINAL_BLOCKS = 137
ORIGINAL_REDUCED = 112
BASE_COMMIT = "e38a8b97a18d33417e364487eb69f8ed74aff19e"
BASE_UNSTRIPPED = "0f50faa8c325104dc77898ed84866dec2ad1eec475b6abba72c475cf7bf9bab6"
BASE_STRIPPED = "d0377d7cef5b7378063f8bfabac5dc9c08d29eeaaaaa14022d36909688ff5e1b"
BASE_SOURCE = SWARM / "baseline/pump/src/migrate_v2.rs"
WORK_SOURCE = LANE / "source/src/migrate_v2.rs"
CANONICAL = SWARM / "baseline/canonical-unstripped.so"
STATE = LANE / "SEARCH-STATE.json"
SUMMARY = LANE / "SUMMARY.json"
LEDGER = SWARM / "log_attempt.py"
BASE_BYTES = BASE_SOURCE.read_bytes()
BASE_TEXT = BASE_BYTES.decode()
assert hashlib.sha256((CANONICAL).read_bytes()).hexdigest() == BASE_UNSTRIPPED
assert hashlib.sha256(BASE_BYTES).hexdigest() == "01b9cd6e1cc397f2238936e59a2837a2b0b63f2063ee52dbda56f52b30e58541"
assert (SWARM / "tools/base/original-windows.pkl").is_file(), "refuse to mutate shared scorer cache"

N = "cta_signed(a,&a.bonding_curve,account,wallet,mint,token_program,&[&[b\"pool-authority\",a.base_mint.key().as_ref(),&[bump]]])"
IX = "Instruction{program_id:anchor_spl::associated_token::ID,accounts:vec![AccountMeta::new(a.user.key(),true),AccountMeta::new(account.key(),false),AccountMeta::new_readonly(wallet.key(),false),AccountMeta::new_readonly(mint.key(),false),AccountMeta::new_readonly(a.system_program.key(),false),AccountMeta::new_readonly(token_program.key(),false)],data:anchor_lang::prelude::borsh::to_vec(&1u8).unwrap()}"
INFOS = "[a.user.to_account_info(),account.clone(),wallet.clone(),mint.to_account_info(),a.system_program.to_account_info(),token_program]"
INVOKE = "anchor_lang::solana_program::program::invoke(&" + IX + ",&" + INFOS + ")"
LOCAL_INVOKE = "anchor_lang::solana_program::program::invoke(&ix,&infos)"
SCOPED_PROGRAM = "{let ix=" + IX + ";let infos=" + INFOS + ";" + LOCAL_INVOKE + "}"
SCOPED_MAPPED = "{let ix=" + IX + ";let infos=" + INFOS + ";" + LOCAL_INVOKE + ".map_err(Into::into)}"

NATIVE = {
    "q": "  " + N + "?;",
    "bind-map": "  let result:Result<()>=" + N + ".map_err(Into::into);result?;",
    "match": "  match " + N + "{Ok(())=>{},Err(error)=>return Err(error.into())};",
    "early": "  return " + N + ".map_err(Into::into);",
}
NONNATIVE = {
    "q": "  " + INVOKE + "?;",
    "bind-q": "  let result=" + INVOKE + ";result?;",
    "bind-map": "  let result:Result<()>=" + INVOKE + ".map_err(Into::into);result?;",
    "scoped-bind-q": "  let result=" + SCOPED_PROGRAM + ";result?;",
    "scoped-bind-map": "  let result:Result<()>=" + SCOPED_MAPPED + ";result?;",
    "match-map": "  match " + INVOKE + ".map_err(Into::into){Ok(())=>{},Err(error)=>return Err(error)};",
    "scoped-match-map": "  let result:Result<()>=" + SCOPED_MAPPED + ";match result{Ok(())=>{},Err(error)=>return Err(error)};",
}
CLONE = " let token_program=token_program.clone();"
OLD_BODY = CLONE + "\n if native{\n" + NATIVE["q"] + "\n }else{\n" + NONNATIVE["q"] + "\n }\n Ok(())"
assert OLD_BODY in BASE_TEXT


def body(native, nonnative):
    return CLONE + "\n if native{\n" + NATIVE[native] + "\n }else{\n" + NONNATIVE[nonnative] + "\n }\n Ok(())"


def unified(kind):
    native_expr = N + ".map_err(Into::into)"
    nonnative_expr = SCOPED_MAPPED
    if kind.endswith("-lines"):
        assert kind.endswith("question-lines")
        if kind.startswith("expr"):
            return CLONE + "\n let result:Result<()>=if native{\n  " + native_expr + "\n }else{\n  " + nonnative_expr + "\n };result?;\n Ok(())"
        return CLONE + "\n let result:Result<()>;if native{\n  result=" + native_expr + ";\n }else{\n  result=" + nonnative_expr + ";\n }result?;\n Ok(())"
    if kind.startswith("expr"):
        prefix = CLONE + "\n let result:Result<()>=if native{\n  " + native_expr + "\n }else{\n  " + nonnative_expr + "\n };\n "
    else:
        prefix = CLONE + "\n let result:Result<()>;\n if native{\n  result=" + native_expr + ";\n }else{\n  result=" + nonnative_expr + ";\n }\n "
    return prefix + ("result?;\n Ok(())" if kind.endswith("question") else "result")


def make_source(native=None, nonnative=None, unified_kind=None):
    new_body = unified(unified_kind) if unified_kind else body(native, nonnative)
    text = BASE_TEXT.replace(OLD_BODY, new_body, 1)
    assert text != BASE_TEXT and text.count("pub fn create_token_account_v2") == 1
    assert "let token_program=token_program.clone();" in text
    return text


# Priority is evidence-led: preserve conversion-before-drop first, then vary cleanup
# and outer Result live ranges. Exact prior controls are not generated.
SPECS = [
    ("m-scoped-bind-map", "q", "scoped-bind-map", None),
    ("early-m-scoped-bind-map", "early", "scoped-bind-map", None),
    ("m-bind-map", "q", "bind-map", None),
    ("early-m-bind-map", "early", "bind-map", None),
    ("m-scoped-bind-q", "q", "scoped-bind-q", None),
    ("early-m-scoped-bind-q", "early", "scoped-bind-q", None),
    ("m-scoped-match-map", "q", "scoped-match-map", None),
    ("early-m-scoped-match-map", "early", "scoped-match-map", None),
    ("m-bind-q", "q", "bind-q", None),
    ("early-m-bind-q", "early", "bind-q", None),
    ("m-match-map", "q", "match-map", None),
    ("early-m-match-map", "early", "match-map", None),
    ("n-bind-map", "bind-map", "q", None),
    ("n-match", "match", "q", None),
    ("n-bind-map__m-scoped-bind-q", "bind-map", "scoped-bind-q", None),
    ("n-bind-map__m-scoped-bind-map", "bind-map", "scoped-bind-map", None),
    ("n-bind-map__m-scoped-match-map", "bind-map", "scoped-match-map", None),
    ("n-match__m-scoped-bind-q", "match", "scoped-bind-q", None),
    ("n-match__m-scoped-bind-map", "match", "scoped-bind-map", None),
    ("n-match__m-scoped-match-map", "match", "scoped-match-map", None),
    ("unified-expr-question", None, None, "expr-question"),
    ("unified-expr-tail", None, None, "expr-tail"),
    ("unified-assign-question", None, None, "assign-question"),
    ("unified-assign-tail", None, None, "assign-tail"),
    ("unified-expr-question-lines", None, None, "expr-question-lines"),
    ("unified-assign-question-lines", None, None, "assign-question-lines"),
]
assert len(SPECS) == 26 and len({s[0] for s in SPECS}) == 26
GENERATED_SOURCE_HASHES = {s[0]: hashlib.sha256(make_source(s[1], s[2], s[3]).encode()).hexdigest() for s in SPECS}
assert len(set(GENERATED_SOURCE_HASHES.values())) == len(SPECS), "duplicate generated source"
assert not set(GENERATED_SOURCE_HASHES.values()) & {
    "58a34c7c0f22954c5144fa8a240675050f5dd7e32e2676ebdf686b6d5e860baa",
    "93d5bddc0a6bac40caae2f83b3a7f994eab7de1301f3dc43793361d764a7d2c5",
    "b5b6ec56cc598708199d6c80b2f27f9fc2994acef23ad879ba180243b468e099",
    "7d373629b4a9b5b10f3d038bb6b6b127a3dfc16fae9a5373322be94414db5160",
}, "exact prior four-control source repeat"
SEARCH_SPACE = {
    "schema": "migrate-bruteforce-search-v2",
    "initial_cap": 24,
    "evidence_followup_cap": 2,
    "cap": 26,
    "candidate_count": len(SPECS),
    "selection_basis": [
        "original has 137 machine blocks and 112 reduced nodes versus baseline 138/113",
        "baseline non-native success/error cleanup joins an output-pointer reload",
        "preserve two ProgramError conversions and both six-account cleanups",
        "prior native-early control is used only in new compositions, never repeated alone",
        "two unified forms verified the 112-node topology but shifted later Anchor error line constants; exactly two line-preserving followups are justified",
    ],
    "native_axes": {
        "q": "baseline question-mark propagation; no standalone rebuild",
        "bind-map": "named Anchor Result after map_err, then question-mark propagation",
        "match": "explicit Ok/Err propagation without a whole-branch early return",
        "early": "prior native early-return component only composed with novel non-native forms",
    },
    "nonnative_axes": {
        "bind-q": "bound ProgramResult propagated after temporary cleanup",
        "bind-map": "map error before temporary cleanup, bind Anchor Result, then propagate",
        "scoped-bind-q": "CPI locals scoped before ProgramResult propagation",
        "scoped-bind-map": "CPI locals scoped after conversion but before outer propagation",
        "match-map": "explicit match propagation of mapped CPI Result",
        "scoped-match-map": "scoped mapped CPI Result followed by explicit match propagation",
    },
    "unified_axes": ["if-expression versus assignment", "outer question-mark versus tail Result", "original physical source-line preservation for the two verified-topology forms"],
    "forbidden_repeats_excluded": [
        "explicit field-by-field first AccountInfo clone",
        "unscoped both-branch direct tail Results",
        "named non-native Instruction/AccountInfo locals with direct question-mark",
        "native early return with unchanged baseline non-native branch",
        "H3 wrapper/helper, argument reorder, visibility, and older H3 Result controls",
    ],
    "deduplication": "26 distinct full migrate_v2.rs SHA-256 values verified before followup builds; unstripped SHA-256 after build; equivalent outputs grouped in SUMMARY.json",
}


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def rel(path):
    return str(Path(path).resolve().relative_to(SWARM))


def ledger_check(key):
    run = subprocess.run([sys.executable, str(LEDGER), "check", "--dedupe-key", key], check=True, text=True, stdout=subprocess.PIPE)
    return json.loads(run.stdout)


def ledger_record(key, hypothesis, status, data):
    run = subprocess.run([
        sys.executable, str(LEDGER), "record", "--lane", "migrate-bruteforce",
        "--approach", "bounded-result-cpi-liveness-composition", "--target", hex(TARGET),
        "--dedupe-key", key, "--hypothesis", hypothesis, "--status", status,
        "--data", json.dumps(data, sort_keys=True, separators=(",", ":")),
    ], check=True, text=True, stdout=subprocess.PIPE)
    return json.loads(run.stdout)


def log_search_space():
    keys = ["migrate-bruteforce:0x4c158:e38a8b97a:search-space-v1"]
    if not ledger_check(keys[0])["duplicate"]:
        ledger_record(keys[0], "Evidence-bounded 24-source composition search excluding all exact prior controls", "analyzed", {
            "search_space": SEARCH_SPACE,
            "baseline_source_sha256": sha_bytes(BASE_BYTES),
            "baseline_unstripped_sha256": BASE_UNSTRIPPED,
            "baseline_stripped_sha256": BASE_STRIPPED,
        })
    followup = "migrate-bruteforce:0x4c158:e38a8b97a:line-preserving-followup-v2"
    if not ledger_check(followup)["duplicate"]:
        ledger_record(followup, "Cap two followups to restore source-line constants after unified forms verified target topology", "analyzed", {
            "initial_cap": 24,
            "followup_cap": 2,
            "total_cap": 26,
            "direct_observation": "unified-expr-question and unified-assign-question verified 112-node topology; unified-expr-question changed init_pump_amm_boost_v2 immediates 0x292->0x293 and 0x2eb->0x2ec",
            "search_space": SEARCH_SPACE,
        })
    keys.append(followup)
    return keys


class Inventory(cfg.Inventory):
    def __init__(self, path, original=False):
        super().__init__(path, False)
        self.original = original
        if original:
            self.functions = {w["start"]: {"start": w["start"], "size": w["bytes"], "name": ""} for w in score.original_windows()}
        secs = score.sections(self.elf.b)
        text = secs[".text"]
        lo, hi = text["offset"], text["offset"] + text["size"]
        self.elf.normalized = self.elf.b[:lo] + score.normalize(self.elf.b[lo:hi], text["addr"], secs) + self.elf.b[hi:]


def diagnostics(image, out):
    original_window = next(w for w in score.original_windows() if w["start"] == TARGET)
    cand = win.Cand(image)
    func = next(f for f in cand.funcs if "create_token_account_v2" in win.demangle(f[2]))
    start, size = func[0], func[1]
    raw = cand.fn(start, size)
    original_tokens = [x[2] for x in win.insns(original_window["raw"], TARGET, win.ORIG_SECS)]
    candidate_tokens = [x[2] for x in win.insns(raw, start, cand.secs)]
    matcher = difflib.SequenceMatcher(None, original_tokens, candidate_tokens, autojunk=False)
    prefix = 0
    for left, right in zip(original_tokens, candidate_tokens):
        if left != right:
            break
        prefix += 1
    original = Inventory(score.BASE / "original.so", True)
    candidate = Inventory(image)
    original_graph = original.graph(TARGET, True)
    candidate_graph = candidate.graph(start, True)
    topology = cfg.bijection(original_graph, candidate_graph, True)
    mapping = topology.get("mapping", topology.get("partial_mapping", {}))
    original_callees = [original.describe_callee(r["target"], 2) for r in original.function(TARGET)["calls"]]
    candidate_callees = [candidate.describe_callee(r["target"], 2) for r in candidate.function(start)["calls"]]
    report = {
        "original": original_graph,
        "candidate": candidate_graph,
        "topology": topology,
        "physical_order_callees": {"original": original_callees, "candidate": candidate_callees},
    }
    out.with_suffix(".json.gz").write_bytes(gzip.compress(json.dumps(report, indent=2).encode(), mtime=0))
    summary = {
        "original_bytes": ORIGINAL_BYTES,
        "candidate_bytes": size,
        "candidate_start": hex(start),
        "machine_blocks": [original_graph["machine_blocks"], candidate_graph["machine_blocks"]],
        "reduced_blocks": [original_graph["canonical_reachable_blocks"], candidate_graph["canonical_reachable_blocks"]],
        "topology": {k: v for k, v in topology.items() if k not in ("mapping", "partial_mapping")},
        "callee_calls": [len(original_callees), len(candidate_callees)],
        "physical_order_callees_depth2_equal": [r["identity_sha256"] for r in original_callees] == [r["identity_sha256"] for r in candidate_callees],
        "diagnostic_similarity": matcher.ratio(),
        "normalized_instruction_prefix": prefix,
        "target_raw_sha256": sha_bytes(raw),
        "target_normalized_sha256": sha_bytes(score.normalize(raw, start, cand.secs)),
    }
    out.with_suffix(".json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def official_score(image, destination):
    current = score.score(image)
    baseline = score.load_baseline(SWARM / "baseline/score.json")
    normalized = sum(v["normalized"] for v in current.values())
    raw = sum(v["raw"] for v in current.values())
    summary = {
        "candidate_sha256": sha_file(image),
        "normalized": normalized,
        "raw": raw,
        "total": len(current),
        "matched_text_bytes": sum(v["bytes"] for v in current.values() if v["normalized"]),
        "gains": [hex(k) for k in sorted(current) if current[k]["normalized"] and not baseline.get(k, {}).get("normalized")],
        "losses": [hex(k) for k in sorted(current) if not current[k]["normalized"] and baseline.get(k, {}).get("normalized")],
        "raw_gains": [hex(k) for k in sorted(current) if current[k]["raw"] and not baseline.get(k, {}).get("raw")],
        "raw_losses": [hex(k) for k in sorted(current) if not current[k]["raw"] and baseline.get(k, {}).get("raw")],
    }
    destination.write_text(json.dumps({"summary": summary, "windows": {str(k): v for k, v in current.items()}}, indent=1))
    return summary, current[TARGET]


def save_state(rows):
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(json.dumps({"search_space": SEARCH_SPACE, "results": rows}, indent=2) + "\n")
    temporary.replace(STATE)


def prior_output_owners():
    owners = {BASE_UNSTRIPPED: ["canonical-baseline", "explicit-token-program-clone"]}
    recovery = REPO / "research/goal-pump-migrate-token-recovery-20261029/probes"
    for result in recovery.glob("*/RESULT.json"):
        data = json.loads(result.read_text())
        if data.get("unstripped_sha256"):
            owners.setdefault(data["unstripped_sha256"], []).append(data["name"])
    old = REPO / "research/goal-pump-create-recovery-20261028"
    for name in ("results-cta.json", "results-cta2.json"):
        for data in json.loads((old / name).read_text()):
            if data.get("unstripped_sha256"):
                owners.setdefault(data["unstripped_sha256"], []).append(data["name"])
    return owners


def run_candidate(spec, native, nonnative, unified_kind, owners):
    source = make_source(native, nonnative, unified_kind)
    source_bytes = source.encode()
    source_hash = sha_bytes(source_bytes)
    key = "migrate-bruteforce:0x4c158:e38a8b97a:" + spec + ":" + source_hash[:16]
    out = LANE / "outputs" / spec
    result_path = out / "RESULT.json"
    check = ledger_check(key)
    if check["duplicate"]:
        if result_path.exists():
            return json.loads(result_path.read_text())
        return {"name": spec, "dedupe_key": key, "status": "duplicate-skipped", "source_sha256": source_hash, "notes": "ledger key exists but local result is absent"}
    out.mkdir(parents=True, exist_ok=True)
    (out / "migrate_v2.rs").write_bytes(source_bytes)
    diff = "".join(difflib.unified_diff(BASE_TEXT.splitlines(True), source.splitlines(True), fromfile="baseline/migrate_v2.rs", tofile=spec + "/migrate_v2.rs"))
    (out / "source.diff").write_text(diff)
    hypothesis = {
        "native": native,
        "nonnative": nonnative,
        "unified": unified_kind,
        "purpose": "change Result/cleanup/output-pointer live ranges while preserving CPI and public semantics",
    }
    result = {
        "name": spec,
        "dedupe_key": key,
        "hypothesis": hypothesis,
        "source_sha256": source_hash,
        "source_diff": rel(out / "source.diff"),
        "output": rel(out),
        "new_runtime_executions": 0,
    }
    WORK_SOURCE.write_bytes(source_bytes)
    try:
        build = fastbuild.build(LANE / "source", LANE / "build", out, quiet=True, recipe="identity")
    finally:
        WORK_SOURCE.write_bytes(BASE_BYTES)
    result.update(build)
    if not build.get("ok"):
        result["status"] = "compile-failed"
        (out / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
        ledger_record(key, json.dumps(hypothesis, sort_keys=True), "compile-failed", result)
        return result
    result["output_duplicate_of"] = owners.get(build["unstripped_sha256"], []).copy()
    owners.setdefault(build["unstripped_sha256"], []).append(spec)
    score_summary, target = official_score(out / "unstripped.so", out / "score.json")
    result.update(score_summary)
    result["target_official"] = target
    graph = diagnostics(out / "unstripped.so", out / "graph")
    result.update(graph)
    result["baseline_memberships_retained"] = not score_summary["losses"] and not score_summary["raw_losses"]
    result["strict_window_gain"] = bool(score_summary["gains"]) and result["baseline_memberships_retained"]
    if score_summary["losses"] or score_summary["raw_losses"] or not build.get("runtime_valid"):
        status = "rejected"
    elif target["raw"]:
        status = "raw-match"
    elif target["normalized"]:
        status = "normalized-match"
    elif graph["diagnostic_similarity"] > 0.563 or score_summary["gains"]:
        status = "partial"
    else:
        status = "built"
    result["status"] = status
    result["notes"] = "exact equivalent output" if result["output_duplicate_of"] else "distinct output; official target remains unmatched" if not target["normalized"] else "official target match"
    (out / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    ledger_record(key, json.dumps(hypothesis, sort_keys=True), status, result)
    return result


def diagnostic_baseline():
    destination = LANE / "baseline-diagnostics"
    summary = diagnostics(CANONICAL, destination)
    score_summary, target = official_score(CANONICAL, LANE / "baseline-score.json")
    (LANE / "BASELINE.json").write_text(json.dumps({
        "source_sha256": sha_bytes(BASE_BYTES),
        "unstripped_sha256": BASE_UNSTRIPPED,
        "stripped_sha256": BASE_STRIPPED,
        "score": score_summary,
        "target_official": target,
        "diagnostics": summary,
    }, indent=2) + "\n")


def finalize(rows, analysis_key):
    completed = [r for r in rows if r.get("ok")]
    assert len({r["source_sha256"] for r in rows}) == len(SPECS)
    audit = []
    for row in rows:
        assert ledger_check(row["dedupe_key"])["duplicate"], "unlogged attempt: " + row["dedupe_key"]
        if not row.get("ok"):
            continue
        out = SWARM / row["output"]
        assert sha_file(out / "migrate_v2.rs") == row["source_sha256"]
        assert sha_file(out / "unstripped.so") == row["unstripped_sha256"]
        stripped = sha_file(out / "candidate.so")
        scorer_input = json.loads((out / "score.json").read_text())["summary"]["candidate_sha256"]
        assert scorer_input == row["unstripped_sha256"]
        row["scorer_input_sha256"] = scorer_input
        row["candidate_sha256"] = stripped
        row["stripped_sha256"] = stripped
        row["output_duplicate_of"] = list(dict.fromkeys(x for x in row.get("output_duplicate_of", []) if x != row["name"]))
        (out / "RESULT.json").write_text(json.dumps(row, indent=2) + "\n")
        audit.append({"name": row["name"], "dedupe_key": row["dedupe_key"], "source_sha256": row["source_sha256"], "unstripped_sha256": row["unstripped_sha256"], "stripped_sha256": stripped, "scorer_input_sha256": scorer_input})
    save_state(rows)
    audit_key = "migrate-bruteforce:0x4c158:e38a8b97a:hash-audit-v1"
    if not ledger_check(audit_key)["duplicate"]:
        ledger_record(audit_key, "Authenticate all 26 source/output hashes and bind actual stripped ELFs", "analyzed", {
            "hash_audit": audit,
            "note": "score.json candidate_sha256 is the scorer's unstripped input hash. Per-trial RESULT files and this audit now bind candidate_sha256/stripped_sha256 to candidate.so; no binary or score was changed.",
        })
    analysis_keys = list(analysis_key) + [audit_key]
    eligible = [r for r in completed if r.get("baseline_memberships_retained") and r.get("runtime_valid")]
    def rank(r):
        return (
            bool(r["target_official"]["raw"]),
            bool(r["target_official"]["normalized"]),
            len(r.get("gains", [])),
            bool(r["topology"].get("verified")),
            r["physical_order_callees_depth2_equal"],
            -abs(r["reduced_blocks"][1] - ORIGINAL_REDUCED),
            -abs(r["machine_blocks"][1] - ORIGINAL_BLOCKS),
            -abs(r["candidate_bytes"] - ORIGINAL_BYTES),
            r["diagnostic_similarity"],
        )
    best = max(eligible, key=rank) if eligible else None
    groups = {}
    for row in rows:
        if row.get("target_official", {}).get("normalized"):
            continue
        group_key = row.get("unstripped_sha256", "compile-failed:" + row["name"])
        group = groups.setdefault(group_key, {"unstripped_sha256": row.get("unstripped_sha256"), "candidates": []})
        group["candidates"].append(row["name"])
    rejected = []
    for group in groups.values():
        members = [r for r in rows if r["name"] in group["candidates"]]
        if any(r.get("status") == "compile-failed" for r in members):
            observation = "compile failed"
        elif len(members) > 1:
            observation = "multiple distinct source forms produced this identical output; official target remains unmatched"
        elif members[0].get("output_duplicate_of"):
            observation = "exact prior-equivalent output; official target remains unmatched"
        else:
            observation = "distinct output but official target remains unmatched"
        group.update({
            "observation": observation,
            "best_diagnostic_similarity": max((r.get("diagnostic_similarity", 0) for r in members), default=0),
            "target_byte_sizes": sorted({r.get("candidate_bytes") for r in members if r.get("candidate_bytes") is not None}),
            "topology_verified": any(r.get("topology", {}).get("verified") for r in members),
            "baseline_memberships_retained": all(r.get("baseline_memberships_retained", False) for r in members),
            "normalized_losses": sorted({x for r in members for x in r.get("losses", [])}),
        })
        rejected.append(group)
    summary = {
        "schema": "main-pump-swarm-lane-summary-v1",
        "lane": "migrate-bruteforce",
        "targets": [{"original": hex(TARGET), "name": "pump_recovered::" + TARGET_NAME, "original_bytes": ORIGINAL_BYTES}],
        "search_space": SEARCH_SPACE,
        "analysis_keys": analysis_keys,
        "attempted_keys": [r["dedupe_key"] for r in rows],
        "attempts": [{k: r.get(k) for k in ("name", "dedupe_key", "status", "source_sha256", "unstripped_sha256", "stripped_sha256", "scorer_input_sha256", "normalized", "raw", "gains", "losses", "raw_gains", "raw_losses", "candidate_bytes", "diagnostic_similarity", "topology", "baseline_memberships_retained", "output_duplicate_of", "output")} for r in rows],
        "counts": {
            "generated": len(SPECS),
            "attempted": len(rows),
            "built": sum(bool(r.get("ok")) for r in rows),
            "compile_failed": sum(r.get("status") == "compile-failed" for r in rows),
            "distinct_sources": len({r["source_sha256"] for r in rows}),
            "distinct_outputs": len({r.get("unstripped_sha256") for r in completed}),
            "baseline_membership_preserving": len(eligible),
            "membership_rejected": len(rows) - len(eligible),
            "strict_window_gains": sum(bool(r.get("strict_window_gain")) for r in rows),
        },
        "hash_convention": "source_sha256=migrate_v2.rs; unstripped_sha256=unstripped.so; stripped_sha256=candidate.so; scorer_input_sha256=score.json summary candidate_sha256 (unstripped.so)",
        "best_candidate": None,
        "strict_gains": sorted({x for r in rows for x in r.get("gains", []) + r.get("raw_gains", [])}),
        "strict_losses": sorted({x for r in rows for x in r.get("losses", []) + r.get("raw_losses", [])}),
        "best_candidate_strict_gains": [],
        "best_candidate_strict_losses": [],
        "rejected_mechanisms": rejected,
        "unresolved_residuals": [],
        "next_genuinely_novel_experiment": {
            "name": "line-preserving-unified-native-programresult-binding",
            "composition": "Starting from unified-expr-question-lines, wrap only the native branch in a scope that binds cta_signed's ProgramResult before map_err(Into::into); retain the scoped non-native mapped Result, outer result?, original physical line count, and final Ok(()).",
            "why_untried": "No attempted key combines the verified unified-Result topology with a native ProgramResult binding. The native bind-map control is the strongest non-topology diagnostic, so this composition targets entry/register live ranges without changing CPI roles or revisiting a forbidden standalone control.",
        },
        "acceptance": "Only the unchanged official local scorer establishes normalized/raw membership; topology and diagnostic similarity are not acceptance.",
        "new_runtime_executions": 0,
    }
    if best:
        summary["best_candidate"] = {
            "name": best["name"],
            "dedupe_key": best["dedupe_key"],
            "output": best["output"],
            "source_sha256": best["source_sha256"],
            "unstripped_sha256": best["unstripped_sha256"],
            "stripped_sha256": best["stripped_sha256"],
            "target_raw_sha256": best["target_raw_sha256"],
            "target_normalized_sha256": best["target_normalized_sha256"],
            "normalized": best["normalized"],
            "raw": best["raw"],
            "target_official": best["target_official"],
            "candidate_bytes": best["candidate_bytes"],
            "diagnostic_similarity": best["diagnostic_similarity"],
            "machine_blocks": best["machine_blocks"],
            "reduced_blocks": best["reduced_blocks"],
            "topology": best["topology"],
            "physical_order_callees_depth2_equal": best["physical_order_callees_depth2_equal"],
            "diagnostic_only": not best["target_official"]["normalized"],
            "selection": "highest official target status, strict gains, verified topology, callee order, graph/byte proximity, then diagnostic similarity among candidates retaining every baseline normalized/raw membership",
        }
        summary["best_candidate_strict_gains"] = best["gains"] + best["raw_gains"]
        summary["best_candidate_strict_losses"] = best["losses"] + best["raw_losses"]
        if not best["target_official"]["normalized"]:
            summary["unresolved_residuals"] = [{
                "target": hex(TARGET),
                "original_bytes": ORIGINAL_BYTES,
                "best_candidate_bytes": best["candidate_bytes"],
                "official_normalized": False,
                "official_raw": False,
                "topology_verified": best["topology"].get("verified"),
                "ordered_callees_equal": best["physical_order_callees_depth2_equal"],
                "note": "Topology is verified, but normalized instruction values/register/stack scheduling remain unequal. No strict window gain is claimed.",
            }]
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=len(SPECS))
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    analysis_key = log_search_space()
    if not (LANE / "BASELINE.json").exists():
        diagnostic_baseline()
    rows = []
    if STATE.exists():
        rows = json.loads(STATE.read_text())["results"]
    by_name = {r["name"]: r for r in rows}
    owners = prior_output_owners()
    for row in rows:
        if row.get("unstripped_sha256"):
            owners.setdefault(row["unstripped_sha256"], []).append(row["name"])
    selected = SPECS[args.start:args.start + args.limit]
    for spec, native, nonnative, unified_kind in selected:
        if spec in by_name and by_name[spec].get("status") != "duplicate-skipped":
            print(json.dumps({"skipped_completed": spec}), flush=True)
            continue
        row = run_candidate(spec, native, nonnative, unified_kind, owners)
        by_name[spec] = row
        rows = [by_name[s[0]] for s in SPECS if s[0] in by_name]
        save_state(rows)
        print(json.dumps({k: row.get(k) for k in ("name", "status", "normalized", "raw", "gains", "losses", "candidate_bytes", "diagnostic_similarity", "machine_blocks", "reduced_blocks", "physical_order_callees_depth2_equal", "unstripped_sha256", "output_duplicate_of")}), flush=True)
    rows = [by_name[s[0]] for s in SPECS if s[0] in by_name]
    if args.finalize:
        assert len(rows) == len(SPECS), f"refusing final summary with {len(rows)}/{len(SPECS)} attempts"
        result = finalize(rows, analysis_key)
        print(json.dumps({"summary": rel(SUMMARY), "best": result["best_candidate"], "counts": result["counts"]}, indent=2), flush=True)
    assert WORK_SOURCE.read_bytes() == BASE_BYTES


if __name__ == "__main__":
    main()
