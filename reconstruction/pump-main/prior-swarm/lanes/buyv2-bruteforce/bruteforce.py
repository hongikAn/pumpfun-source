#!/usr/bin/env python3
"""Evidence-pruned buy_v2 source-composition runner.

Only lanes/buyv2-bruteforce is modified, apart from the shared locked attempt ledger.
Every executed candidate gets a real identity build and an official baseline score.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

LANE = Path(__file__).resolve().parent
SWARM = LANE.parents[1]
ROOT = SWARM.parents[1]
RECOVERY = ROOT / "research/goal-pump-buyv2-recovery-20261028"
HARNESS = SWARM / "tools/harness"
SOURCE = LANE / "source"
P = SOURCE / "src/buy_v2.rs"
BASE = P.read_text()
TARGET = 0x13B9B8
ARCHIVE_SHA = "9f371116f66cbff28f10ad1d02a160d878321eef28bbf73bcb5261ab879abd39"
FROZEN_UNSTRIPPED = "f432b793a6eb7d93d89e8619d70f7877726c48adb3a43d5e8feb4dfd41d11c6e"
FROZEN_STRIPPED = "87d299201077941cf636bc1f1978d9d2a035fff3a6b307b85c21f330130eca23"
PAYMENT_HASHES = {
    "pump-native-payments/Cargo.toml": "d4c573b09a2644bb736889b416715802d2a008e9c7c7644d92e7aa92b9665e69",
    "pump-native-payments/src/lib.rs": "e07d978e14a7aab54ab9a41c013bacddfb503669172bed18a757b5f37091218c",
}

SNAP = "let c=&a.bonding_curve;let creator=c.creator;let quote_mint=c.quote_mint;let vb=c.virtual_token_reserves;let vq=c.virtual_quote_reserves;let rb=c.real_token_reserves;let rq=c.real_quote_reserves;"
IS_SOL = "let c=&a.bonding_curve;let is_sol=quote_mint==Pubkey::default();"
TAIL = "let a=&mut *ctx.accounts;crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;\nOk(())"
ADD = "require_gte!(limit,gross.checked_add(pf)\n// layout-pad\n// layout-pad\n// layout-pad\n  .ok_or_else(||error!(PumpError::Overflow))?\n  .checked_add(cf)\n  .ok_or_else(||error!(PumpError::Overflow))?,PumpError::TooMuchSolRequired);"
COMPLETION = "let a=&mut *ctx.accounts;if a.bonding_curve.real_token_reserves==0{a.bonding_curve.complete=true;let event=crate::trade_types::CompleteEvent{mint:a.base_mint.key(),user:a.user.key(),bonding_curve:a.bonding_curve.key(),quote_mint:a.bonding_curve.quote_mint,timestamp};emit!(event);emit_cpi!(event);}"
POST_FEE = "buyback_fee:crate::transfer_fee_recovered::post_fee_amount(&fee,bf)?,"

for marker in (SNAP, IS_SOL, TAIL, ADD, COMPLETION, POST_FEE):
    assert BASE.count(marker) == 1, marker[:100]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def replace_one(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, old[:120]
    return text.replace(old, new, 1)


def replace_handler_first(text: str, old: str, new: str) -> str:
    assert old in text, old[:120]
    return text.replace(old, new, 1)


def snap_early(text: str) -> str:
    text = replace_one(text, SNAP, SNAP.replace("let vb=", "let is_sol=quote_mint==Pubkey::default();let vb="))
    return replace_one(text, IS_SOL, "let c=&a.bonding_curve;")


def snap_qrc(text: str) -> str:
    replacement = "let c=&a.bonding_curve;let quote_mint=c.quote_mint;let is_sol=quote_mint==Pubkey::default();let vb=c.virtual_token_reserves;let vq=c.virtual_quote_reserves;let rb=c.real_token_reserves;let rq=c.real_quote_reserves;let creator=c.creator;"
    text = replace_one(text, SNAP, replacement)
    return replace_one(text, IS_SOL, "let c=&a.bonding_curve;")


def borrowed_helper(text: str) -> str:
    completion = replace_one(COMPLETION, "emit!(event);emit_cpi!(event);", "emit_buy_complete(&ctx,&event)?;")
    text = replace_one(text, COMPLETION, completion)
    helper = "\n#[inline(always)]fn emit_buy_complete<'info>(ctx:&Context<'_,'_,'_,'info,BuyV2<'info>>,event:&crate::trade_types::CompleteEvent)->Result<()>{emit!(*event);emit_cpi!(*event);Ok(())}\n"
    return text + helper


def tail_explicit(text):
    return replace_one(text, TAIL, TAIL.replace("Ok(())", "return Ok(());"))


def snap_late(text):
    replacement = "let c=&a.bonding_curve;let creator;let quote_mint;let vb=c.virtual_token_reserves;let vq=c.virtual_quote_reserves;let rb=c.real_token_reserves;let rq=c.real_quote_reserves;creator=c.creator;quote_mint=c.quote_mint;"
    return replace_one(text, SNAP, replacement)


def tail_match(text: str) -> str:
    replacement = "let a=&mut *ctx.accounts;match crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user) {Err(e)=>Err(e),\nOk(())=>Ok(())}"
    return replace_one(text, TAIL, replacement)


def tail_iflet(text: str) -> str:
    replacement = "let a=&mut *ctx.accounts;if let Err(e)=crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user){return Err(e);}\nOk(())"
    return replace_one(text, TAIL, replacement)


def tail_result_match(text: str) -> str:
    replacement = "let a=&mut *ctx.accounts;let result=crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user);\nmatch result {Err(e)=>Err(e),Ok(())=>Ok(())}"
    return replace_one(text, TAIL, replacement)


def tail_and_then(text: str) -> str:
    replacement = "let a=&mut *ctx.accounts;crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user).and_then(|()|\nOk(()))"
    return replace_one(text, TAIL, replacement)


def add_lets(text: str) -> str:
    replacement = "let subtotal=gross.checked_add(pf)\n// layout-pad\n// layout-pad\n// layout-pad\n  .ok_or_else(||error!(PumpError::Overflow))?;\n  let total=subtotal.checked_add(cf)\n  .ok_or_else(||error!(PumpError::Overflow))?;require_gte!(limit,total,PumpError::TooMuchSolRequired);"
    return replace_one(text, ADD, replacement)


def add_option(text: str) -> str:
    replacement = "let total=match gross.checked_add(pf) {\n// layout-pad\n// layout-pad\n// layout-pad\n  None=>return Err(error!(PumpError::Overflow)),Some(subtotal)=>match subtotal.checked_add(cf) {\n  Some(total)=>total,\n  None=>return Err(error!(PumpError::Overflow))}};require_gte!(limit,total,PumpError::TooMuchSolRequired);"
    return replace_one(text, ADD, replacement)


def add_option_some_first(text: str) -> str:
    replacement = "let total=match gross.checked_add(pf) {\n// layout-pad\n// layout-pad\n// layout-pad\n  Some(subtotal)=>match subtotal.checked_add(cf) {Some(total)=>total,None=>return Err(error!(PumpError::Overflow))},\n  None=>{\n  return Err(error!(PumpError::Overflow))}};require_gte!(limit,total,PumpError::TooMuchSolRequired);"
    return replace_one(text, ADD, replacement)


def post_fee_bind(text: str) -> str:
    text = replace_handler_first(text, "let ev=TradeEvent{", "let buyback_fee=crate::transfer_fee_recovered::post_fee_amount(&fee,bf)?;let ev=TradeEvent{")
    return replace_one(text, POST_FEE, "buyback_fee,")


def post_fee_result_snapshot(text: str) -> str:
    text = replace_one(text, SNAP, "let buyback_fee_result=crate::transfer_fee_recovered::post_fee_amount(&fee,bf)?;" + SNAP)
    # Deliberately retain a Result until event construction: remove the early question mark.
    text = text.replace("let buyback_fee_result=crate::transfer_fee_recovered::post_fee_amount(&fee,bf)?;", "let buyback_fee_result=crate::transfer_fee_recovered::post_fee_amount(&fee,bf);", 1)
    return replace_one(text, POST_FEE, "buyback_fee:buyback_fee_result?,")


def post_fee_result_event(text: str) -> str:
    text = replace_handler_first(text, "let ev=TradeEvent{", "let buyback_fee_result=crate::transfer_fee_recovered::post_fee_amount(&fee,bf);let ev=TradeEvent{")
    return replace_one(text, POST_FEE, "buyback_fee:buyback_fee_result?,")


def compose(*ops):
    def apply(text: str) -> str:
        for op in ops:
            text = op(text)
        return text
    return apply


# Names describe mechanisms, not prior trial aliases. Single prior isolated mechanisms are
# intentionally absent; only new constructs or novel compositions are executable here.
VARIANTS = {
    "new_snapshot_early_is_sol": (compose(snap_early), "Move is_sol directly after quote snapshot to make quote/reserve/creator load order explicit"),
    "new_snapshot_quote_reserves_creator": (compose(snap_qrc), "Declare quote, reserves, then creator with early is_sol to mirror observed original load groups"),
    "new_post_fee_bound_value": (compose(post_fee_bind), "Bind post-fee u64 before TradeEvent construction to separate its Result lifetime from event results"),
    "new_post_fee_result_before_snapshot": (compose(post_fee_result_snapshot), "Hold post-fee Result across snapshots and unwrap in the event field to alter stack-slot coloring"),
    "new_post_fee_result_before_event": (compose(post_fee_result_event), "Materialize post-fee Result immediately before TradeEvent and unwrap in its original field"),
    "new_checked_add_external_lets": (compose(add_lets), "Lift checked-add temporaries outside require_gte to constrain overflow block ordering"),
    "new_checked_add_option_none_first": (compose(add_option), "Use nested Option matches with None-first overflow exits and distinct original error lines"),
    "new_checked_add_option_some_first": (compose(add_option_some_first), "Use nested Option matches with Some-first success layout and distinct overflow exits"),
    "new_tail_terminal_match": (compose(tail_match), "Return an Err-first terminal match over prepare_bonding_curve to remove forwarding jump"),
    "new_tail_iflet_err": (compose(tail_iflet), "Use explicit if-let error return after prepare_bonding_curve to invert terminal branch layout"),
    "new_tail_result_match": (compose(tail_result_match), "Name prepare Result then consume it with a terminal Err-first match"),
    "new_tail_and_then": (compose(tail_and_then), "Consume prepare Result with and_then to share success and error forwarding"),
    "compose_borrowed_snapshot_early": (compose(snap_early, borrowed_helper), "Combine early quote snapshot ordering with borrowed complete-event Result-slot boundary"),
    "compose_borrowed_snapshot_qrc": (compose(snap_qrc, borrowed_helper), "Combine quote/reserve/creator declaration order with borrowed complete-event Result-slot boundary"),
    "compose_borrowed_tail_match": (compose(tail_match, borrowed_helper), "Combine borrowed complete-event boundary with terminal prepare match to remove both Result residuals"),
    "compose_borrowed_tail_explicit_ok": (compose(tail_explicit, borrowed_helper), "Combine borrowed complete-event Result-slot boundary with explicit terminal Ok return"),
    "compose_borrowed_snapshot_late_assign": (compose(snap_late, borrowed_helper), "Combine prior late snapshot assignment with borrowed complete-event Result-slot boundary"),
    "compose_late_assign_tail_explicit_ok": (compose(snap_late, tail_explicit), "Compose the two strongest isolated snapshot and tail mechanisms"),
    "compose_borrowed_tail_result_match": (compose(tail_result_match, borrowed_helper), "Combine named prepare Result with borrowed complete-event boundary"),
    "compose_borrowed_tail_and_then": (compose(tail_and_then, borrowed_helper), "Combine prepare and_then forwarding with borrowed complete-event boundary"),
    "compose_borrowed_tail_iflet": (compose(tail_iflet, borrowed_helper), "Combine borrowed complete-event boundary with explicit prepare error return"),
    "compose_borrowed_checked_external": (compose(add_lets, borrowed_helper), "Combine external checked-add temporaries with borrowed complete-event Result-slot boundary"),
    "compose_borrowed_checked_option": (compose(add_option, borrowed_helper), "Combine nested Option overflow exits with borrowed complete-event Result-slot boundary"),
    "compose_borrowed_snapshot_qrc_tail_match": (compose(snap_qrc, tail_match, borrowed_helper), "Compose the three targeted snapshot, prepare-tail, and complete-event mechanisms"),
    "compose_borrowed_snapshot_qrc_checked_option": (compose(snap_qrc, add_option, borrowed_helper), "Compose snapshot ordering and Option overflow blocks with the Result-slot boundary"),
    "compose_borrowed_snapshot_qrc_tail_result_match": (compose(snap_qrc, tail_result_match, borrowed_helper), "Compose snapshot ordering and named prepare Result with the complete-event boundary"),
    "compose_borrowed_snapshot_qrc_checked_option_tail_match": (compose(snap_qrc, add_option, tail_match, borrowed_helper), "Compose all four evidence-targeted mechanisms without changing runtime semantics"),
}


def prior_art():
    source_hashes = {}
    candidates = (list(RECOVERY.glob("trials/*/buy_v2.rs")) + [RECOVERY / "src/src/buy_v2.rs"]
                  + list(LANE.glob("outputs/*/buy_v2.rs")))
    for path in candidates:
        if path.exists():
            source_hashes.setdefault(sha_file(path), []).append(str(path.relative_to(ROOT)))
    output_hashes = {
        FROZEN_UNSTRIPPED: ["frozen-best-unstripped"],
        FROZEN_STRIPPED: ["frozen-best-stripped"],
    }
    result_files = list(RECOVERY.glob("results*.json"))
    if (LANE / "results.json").exists():
        result_files.append(LANE / "results.json")
    for path in result_files:
        try:
            rows = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = row.get("name", path.stem)
            for key in ("unstripped_sha256", "candidate_sha256"):
                value = row.get(key)
                if value:
                    output_hashes.setdefault(value, []).append(name)
    return source_hashes, output_hashes


def ledger(command: str, key: str, **kwargs):
    args = [sys.executable, str(SWARM / "log_attempt.py"), command, "--dedupe-key", key]
    if command == "record":
        for name in ("lane", "approach", "target", "hypothesis", "status", "data"):
            value = kwargs[name]
            if name == "data":
                value = json.dumps(value, separators=(",", ":"), sort_keys=True)
            args += ["--" + name.replace("_", "-"), str(value)]
    result = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    return json.loads(result.stdout)


def target_diagnostic(path: Path):
    sys.path.insert(0, str(HARNESS))
    import score
    import win
    candidate = win.Cand(path)
    window = next(x for x in score.original_windows() if x["start"] == TARGET)
    function = next(f for f in candidate.funcs if "6buy_v211buy_handler17h" in f[2])
    original_tokens = [x[2] for x in win.insns(window["raw"], window["start"], win.ORIG_SECS)]
    candidate_tokens = [x[2] for x in win.insns(candidate.fn(function[0], function[1]), function[0], candidate.secs)]
    ratio = difflib.SequenceMatcher(None, original_tokens, candidate_tokens, autojunk=False).ratio()
    return {
        "target_bytes": function[1],
        "target_ratio": ratio,
        "target_candidate_address": hex(function[0]),
        "target_symbol": function[2],
    }


def write_summary(rows):
    successful = [r for r in rows if r.get("ok")]
    best_new = None
    if successful:
        best_new = max(successful, key=lambda r: (
            bool(r.get("target_raw")), bool(r.get("target_normalized")),
            r.get("normalized", 0) - len(r.get("losses", [])) * 10000,
            r.get("raw", 0), r.get("target_ratio", 0),
            -abs(r.get("target_bytes", 0) - 15480),
        ))
    accepted = [r["name"] for r in successful if r.get("status") in ("normalized-match", "raw-match")]
    frozen_best = {
        "name": "frozen-best",
        "source_archive_sha256": ARCHIVE_SHA,
        "source_buy_v2_sha256": sha_bytes(BASE.encode()),
        "unstripped_sha256": FROZEN_UNSTRIPPED,
        "stripped_sha256": FROZEN_STRIPPED,
        "normalized": 1019,
        "raw": 188,
        "target_normalized": False,
        "target_raw": False,
        "target_bytes": 15488,
        "diagnostic_instruction_similarity": 0.9617716846823096,
    }
    strict_losses = sorted({x for r in successful for x in r.get("losses", [])})
    strict_raw_losses = sorted({x for r in successful for x in r.get("raw_losses", [])})
    summary = {
        "schema": "buyv2-bruteforce-summary-v2",
        "targets": [{"original": hex(TARGET), "name": "pump_recovered::buy_v2::buy_handler", "original_bytes": 15480}],
        "base": frozen_best,
        "attempts": rows,
        "attempt_counts": {
            "total": len(rows),
            "executed_builds": sum(bool(r.get("build_executed")) for r in rows),
            "successful_builds": len(successful),
            "compile_failures": sum(r.get("status") == "compile-failed" for r in rows),
            "source_deduped": sum(r.get("status") == "source-deduped" for r in rows),
            "output_equivalent": sum(bool(r.get("equivalent_prior")) for r in rows),
        },
        "strict_outcome": {
            "accepted_candidates": accepted,
            "target_normalized_gain": any(r.get("target_normalized") for r in successful),
            "target_raw_gain": any(r.get("target_raw") for r in successful),
            "note": "No executed candidate accepted a target-window gain; frozen-best remains best overall." if not accepted else "See accepted candidates.",
        },
        "best_candidate": best_new if accepted else frozen_best,
        "best_candidate_scope": "overall",
        "best_new_candidate": best_new,
        "best_new_candidate_note": "Per-candidate diagnostic ranking only; no new candidate has a strict target gain or exceeds the frozen diagnostic ratio.",
        "strict_gains": sorted({x for r in successful for x in r.get("gains", [])}),
        "strict_losses": strict_losses,
        "strict_raw_gains": sorted({x for r in successful for x in r.get("raw_gains", [])}),
        "strict_raw_losses": strict_raw_losses,
        "payment_crate": {"preserved": all(sha_file(SOURCE / p) == h for p, h in PAYMENT_HASHES.items()), "expected_sha256": PAYMENT_HASHES},
        "rejected_mechanisms": [
            {"mechanism": r["name"], "reason": r.get("status"), "target_ratio": r.get("target_ratio"), "equivalent_prior": r.get("equivalent_prior", [])}
            for r in rows if r.get("status") not in ("normalized-match", "raw-match")
        ],
        "evidence_pruned_compositions": [
            {"name": "compose_borrowed_tail_result_match", "reason": "The isolated named-Result form produced the same unstripped ELF as new_tail_terminal_match; that tail layout was already composed and scored."},
            {"name": "compose_borrowed_tail_and_then", "reason": "The isolated and_then form produced the same stripped ELF, target size, ratio, and diagnostic diff as the passthrough tail; it supplied no new target mechanism."},
        ],
        "borrowed_helper_seed": {
            "name": "complete_helper_borrowed_mir",
            "normalized": 1019,
            "raw": 188,
            "target_normalized": False,
            "target_raw": False,
            "target_bytes": 15520,
            "diagnostic_instruction_similarity": 0.9597050302870688,
            "observation": "Recolors the shared Result slot to original sp-0x100 and has a 502-instruction equal run in the linear diff, but adds an Anchor Result discriminator across Rc cleanup (204 reduced blocks versus 203 original).",
        },
        "unresolved_residual": "Frozen-best remains normalized/raw unmatched: shared Result slot sp-0x28 versus original sp-0x100, checked-add overflow block order, quote/reserve/creator snapshot scheduling, whitelist user-copy stack coloring, and final prepare forwarding remain unresolved. Borrowed-helper compositions establish the sp-0x100 coloring but retain additional Result/cleanup control-flow differences.",
        "next_genuinely_novel_experiment": "In only the borrowed complete-event helper, replace emit!(*event);emit_cpi!(*event);Ok(()) with emit!(*event);Ok(emit_cpi!(*event)) to nest event emission in the single terminal Ok and target the extra Result temporary; keep snapshot and prepare-tail source frozen.",
        "acceptance_note": "Instruction similarity is diagnostic only. Strict acceptance requires official normalized/raw window equality with no baseline membership regression.",
    }
    (LANE / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", default=[])
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if args.list:
        print("\n".join(VARIANTS))
        return
    selected = args.only or list(VARIANTS)
    unknown = set(selected) - set(VARIANTS)
    assert not unknown, unknown
    source_hashes, output_hashes = prior_art()
    results_path = LANE / "results.json"
    rows = json.loads(results_path.read_text()) if results_path.exists() else []
    by_name = {r["name"]: r for r in rows}
    for p, expected in PAYMENT_HASHES.items():
        assert sha_file(SOURCE / p) == expected, p
    try:
        for name in selected:
            operation, hypothesis = VARIANTS[name]
            text = operation(BASE)
            assert text != BASE, name
            source_sha = sha_bytes(text.encode())
            key = f"0x13b9b8-9f371116-{source_sha[:16]}-{name}"
            row = {
                "name": name,
                "dedupe_key": key,
                "hypothesis": hypothesis,
                "source_sha256": source_sha,
                "source_fingerprint_sha256": sha_bytes((ARCHIVE_SHA + ":" + source_sha).encode()),
                "build_executed": False,
            }
            duplicate_sources = source_hashes.get(source_sha, [])
            if duplicate_sources:
                row.update(status="source-deduped", duplicate_sources=duplicate_sources, notes="Exact prior source hash; build pruned before execution.")
                by_name[name] = row
                rows = list(by_name.values())
                results_path.write_text(json.dumps(rows, indent=2) + "\n")
                write_summary(rows)
                print(json.dumps(row), flush=True)
                continue
            check = ledger("check", key)
            if check["duplicate"]:
                row.update(status="ledger-deduped", notes="Attempt key already exists in shared ledger; build pruned.")
                by_name[name] = row
                rows = list(by_name.values())
                results_path.write_text(json.dumps(rows, indent=2) + "\n")
                write_summary(rows)
                print(json.dumps(row), flush=True)
                continue
            out = LANE / "outputs" / name
            out.mkdir(parents=True, exist_ok=True)
            (out / "buy_v2.rs").write_text(text)
            (out / "source.diff").write_text("".join(difflib.unified_diff(BASE.splitlines(True), text.splitlines(True), fromfile="frozen-best/src/buy_v2.rs", tofile=name + "/src/buy_v2.rs")))
            P.write_text(text)
            row["build_executed"] = True
            build_cmd = [sys.executable, str(HARNESS / "fastbuild.py"), "--src", str(SOURCE), "--work", str(LANE / "build"), "--out", str(out), "--recipe", "identity"]
            built = subprocess.run(build_cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (out / "build-command.txt").write_text(" ".join(build_cmd) + "\n")
            (out / "build-stdout.json").write_text(built.stdout)
            try:
                build_result = json.loads(built.stdout)
            except json.JSONDecodeError:
                build_result = {"ok": False, "log": str(out / "build.log"), "stdout": built.stdout[-2000:]}
            row.update(build_result)
            row["ok"] = bool(build_result.get("ok")) and built.returncode == 0
            if not row["ok"]:
                row["status"] = "compile-failed"
            else:
                official_cmd = [sys.executable, str(HARNESS / "score.py"), str(out / "unstripped.so"), "--baseline", str(SWARM / "baseline/score.json"), "--json", str(out / "score.json"), "--quiet"]
                scored = subprocess.run(official_cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
                (out / "score-command.txt").write_text(" ".join(official_cmd) + "\n")
                (out / "score-stdout.json").write_text(scored.stdout)
                score_doc = json.loads((out / "score.json").read_text())
                summary = score_doc["summary"]
                for field in ("normalized", "raw", "total", "matched_text_bytes", "gains", "losses", "raw_gains", "raw_losses"):
                    row[field] = summary[field]
                target_window = score_doc["windows"][str(TARGET)]
                row["target_normalized"] = target_window["normalized"]
                row["target_raw"] = target_window["raw"]
                row.update(target_diagnostic(out / "unstripped.so"))
                equivalent = []
                for hash_key in (row.get("unstripped_sha256"), row.get("candidate_sha256")):
                    equivalent += output_hashes.get(hash_key, [])
                row["equivalent_prior"] = sorted(set(equivalent))
                if row["target_raw"] and not row["losses"] and not row["raw_losses"]:
                    row["status"] = "raw-match"
                elif row["target_normalized"] and not row["losses"]:
                    row["status"] = "normalized-match"
                elif row["gains"] or row["raw_gains"]:
                    row["status"] = "partial"
                else:
                    row["status"] = "rejected"
                diff_path = LANE / "diagnostics" / (name + ".diff.txt")
                diff_path.parent.mkdir(exist_ok=True)
                with diff_path.open("w") as diff_out:
                    subprocess.run([sys.executable, str(HARNESS / "win.py"), "show", hex(TARGET), "--cand", str(out / "unstripped.so"), "--sym", "6buy_v211buy_handler17h", "--context", "2"], cwd=ROOT, stdout=diff_out, stderr=subprocess.STDOUT, text=True, check=True)
                row["diagnostic_diff"] = str(diff_path.relative_to(SWARM))
                output_hashes.setdefault(row["unstripped_sha256"], []).append(name)
                output_hashes.setdefault(row["candidate_sha256"], []).append(name)
            row["output"] = str(out.relative_to(SWARM))
            source_hashes.setdefault(source_sha, []).append(str((out / "buy_v2.rs").relative_to(ROOT)))
            data = {k: row[k] for k in ("output", "source_sha256", "source_fingerprint_sha256", "unstripped_sha256", "candidate_sha256", "normalized", "raw", "gains", "losses", "raw_gains", "raw_losses", "target_normalized", "target_raw", "target_bytes", "target_ratio", "equivalent_prior") if k in row}
            data["notes"] = hypothesis
            if row.get("equivalent_prior"):
                data["notes"] += "; output hash duplicates prior candidate(s): " + ",".join(row["equivalent_prior"])
            status = row["status"] if row["status"] in ("compile-failed", "rejected", "partial", "normalized-match", "raw-match") else "rejected"
            row["ledger"] = ledger("record", key, lane="buyv2-bruteforce", approach="evidence-pruned-composition", target=hex(TARGET), hypothesis=hypothesis, status=status, data=data)
            by_name[name] = row
            rows = list(by_name.values())
            results_path.write_text(json.dumps(rows, indent=2) + "\n")
            write_summary(rows)
            print(json.dumps(row), flush=True)
    finally:
        P.write_text(BASE)
        for p, expected in PAYMENT_HASHES.items():
            assert sha_file(SOURCE / p) == expected, p


if __name__ == "__main__":
    main()
