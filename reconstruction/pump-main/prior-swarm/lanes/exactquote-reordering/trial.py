#!/usr/bin/env python3
"""Build, strictly score, diagnose, and ledger one isolated exact-quote variant."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SWARM = ROOT.parents[1]
HARNESS = SWARM / "tools" / "harness"
sys.path.insert(0, str(HARNESS))
import fastbuild  # noqa: E402
import score  # noqa: E402
import win  # noqa: E402
from diagnose import diagnose, TARGET, SYMBOL  # noqa: E402

BASE_BUY_V2 = ROOT / "source" / "src" / "buy_v2.rs"
BASE_RATIO = 0.9874239350912779
BASE_BYTES = 20200
BASE_RESIDUALS = 7


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return str(Path(path).resolve().relative_to(SWARM))


def ledger(command, key, **kwargs):
    argv = [sys.executable, str(SWARM / "log_attempt.py"), command, "--dedupe-key", key]
    if command == "record":
        for name in ("lane", "approach", "target", "hypothesis", "status"):
            argv.extend((f"--{name.replace('_', '-')}", kwargs[name]))
        argv.extend(("--data", json.dumps(kwargs["data"], separators=(",", ":"))))
    result = subprocess.run(argv, cwd=SWARM.parents[1], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--hypothesis", required=True)
    parser.add_argument("--approach", default="evaluation-lifetime-reordering")
    args = parser.parse_args()
    name = args.name
    if not name.replace("-", "").replace("_", "").isalnum():
        raise SystemExit("variant name must contain only letters, digits, '_' and '-'")
    source = args.source.resolve()
    buy_v2 = source / "src" / "buy_v2.rs"
    key = f"0x13f630-e808e568-{name}"
    check = ledger("check", key)
    if check["duplicate"]:
        raise SystemExit(json.dumps(check))
    out = ROOT / "outputs" / name
    out.mkdir(parents=True, exist_ok=False)
    source_hash = sha(buy_v2)
    patch = "".join(difflib.unified_diff(
        BASE_BUY_V2.read_text().splitlines(True), buy_v2.read_text().splitlines(True),
        fromfile="base/src/buy_v2.rs", tofile=f"{name}/src/buy_v2.rs"
    ))
    (out / "source.patch").write_text(patch)
    build = fastbuild.build(source, ROOT / "build", out, quiet=True, recipe="identity")
    metrics = {"name": name, "dedupe_key": key, "hypothesis": args.hypothesis,
               "source": rel(source), "buy_v2_sha256": source_hash, **build}
    if not build["ok"]:
        metrics["status"] = "compile-failed"
        (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
        ledger("record", key, lane="exactquote-reordering", approach=args.approach,
               target=hex(TARGET), hypothesis=args.hypothesis, status="compile-failed",
               data={"output": rel(out), "source": rel(source), "buy_v2_sha256": source_hash,
                     "source_diff": rel(out / "source.patch"), "build_log": rel(out / "build.log")})
        print(json.dumps(metrics))
        return

    score_cmd = [sys.executable, str(HARNESS / "score.py"), str(out / "unstripped.so"),
                 "--baseline", str(SWARM / "baseline" / "score.json"),
                 "--json", str(out / "score.json"), "--quiet"]
    scored = subprocess.run(score_cmd, check=True, capture_output=True, text=True)
    census = json.loads(scored.stdout)
    score_doc = json.loads((out / "score.json").read_text())
    target = score_doc["windows"][str(TARGET)]

    candidate = win.Cand(out / "unstripped.so")
    window = next(w for w in score.original_windows() if w["start"] == TARGET)
    function = next(f for f in candidate.funcs if SYMBOL in f[2] and f[1] > 10000)
    candidate_tokens = [x[2] for x in win.insns(candidate.fn(function[0], function[1]), function[0], candidate.secs)]
    original_tokens = [x[2] for x in win.insns(window["raw"], window["start"], win.ORIG_SECS)]
    ratio = difflib.SequenceMatcher(None, original_tokens, candidate_tokens, autojunk=False).ratio()
    diff_cmd = [sys.executable, str(HARNESS / "win.py"), "show", hex(TARGET),
                "--cand", str(out / "unstripped.so"), "--full"]
    diff = subprocess.run(diff_cmd, check=True, capture_output=True, text=True)
    (out / "diff.txt").write_text(diff.stdout)
    residuals = diagnose(out / "unstripped.so")
    (out / "residuals.json").write_text(json.dumps(residuals, indent=2) + "\n")

    no_membership_loss = not census["losses"] and not census["raw_losses"]
    if target["raw"] and no_membership_loss:
        status = "raw-match"
    elif target["normalized"] and no_membership_loss:
        status = "normalized-match"
    elif (not build["runtime_valid"]) or not no_membership_loss:
        status = "rejected"
    elif ratio > BASE_RATIO or (
        residuals["differing_reduced_block_count"] is not None
        and residuals["differing_reduced_block_count"] < BASE_RESIDUALS
    ):
        status = "partial"
    else:
        status = "rejected"
    residual_blocks = residuals["differing_reduced_blocks"]
    metrics.update(
        status=status, census=census, target=target, target_address=hex(function[0]),
        target_bytes=function[1], target_ratio=ratio, target_ratio_delta=ratio - BASE_RATIO,
        target_bytes_delta=function[1] - BASE_BYTES,
        topology_verified=residuals["topology"]["verified"],
        differing_reduced_block_count=residuals["differing_reduced_block_count"],
        differing_reduced_blocks=None if residual_blocks is None else [
            {"original": r["original"], "candidate": r["candidate"]} for r in residual_blocks
        ],
        machine_blocks=residuals["machine_blocks"], reduced_cfg_blocks=residuals["reduced_cfg_blocks"],
        forwarded_empty_block_counts=residuals["forwarded_empty_block_counts"],
        actual_ordered_depth2_callees_equal=residuals["actual_ordered_depth2_callees_equal"],
    )
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    data = {
        "output": rel(out), "source": rel(source), "buy_v2_sha256": source_hash,
        "source_diff": rel(out / "source.patch"),
        "unstripped_sha256": build["unstripped_sha256"], "candidate_sha256": build["candidate_sha256"],
        "normalized": census["normalized"], "raw": census["raw"], "total": census["total"],
        "gains": census["gains"], "losses": census["losses"],
        "raw_gains": census["raw_gains"], "raw_losses": census["raw_losses"],
        "runtime_valid": build["runtime_valid"], "stack_warnings": build["stack_warnings"],
        "target_normalized": target["normalized"], "target_raw": target["raw"],
        "target_bytes": function[1], "target_ratio": ratio, "target_ratio_delta": ratio - BASE_RATIO,
        "differing_reduced_blocks": metrics["differing_reduced_blocks"],
        "differing_reduced_block_count": residuals["differing_reduced_block_count"],
        "machine_blocks": residuals["machine_blocks"], "reduced_cfg_blocks": residuals["reduced_cfg_blocks"],
        "forwarded_empty_blocks": residuals["forwarded_empty_block_counts"],
        "actual_ordered_depth2_callees_equal": residuals["actual_ordered_depth2_callees_equal"],
        "residual_report": rel(out / "residuals.json"), "diff": rel(out / "diff.txt"),
        "notes": "Diagnostic similarity and reduced-CFG residuals are not acceptance; full census is authoritative.",
    }
    ledger("record", key, lane="exactquote-reordering", approach=args.approach,
           target=hex(TARGET), hypothesis=args.hypothesis, status=status, data=data)
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
