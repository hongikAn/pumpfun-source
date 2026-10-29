#!/usr/bin/env python3
"""Verify lane evidence, source scope, hashes, ledger rows, and official census."""
import fcntl
import hashlib
import json
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
SWARM = LANE.parents[1]
WORKSPACE = LANE.parents[3]
HARNESS = SWARM / "tools" / "harness"
sys.path.insert(0, str(HARNESS))
import score

OUT1 = LANE / "outputs" / "enum-config-validation"
OUT2 = LANE / "outputs" / "enum-config-validation-source-rows"
X27 = WORKSPACE / "research" / "goal-pump-create-recovery-20261028" / "trials" / "x27_current_roles"
BASELINE_SOURCE = SWARM / "baseline" / "pump"
EXPECTED_LOSSES = ["0x17cf0", "0x18678", "0x19cc0", "0x19ec8", "0x1a918", "0x1ac28"]
EXPECTED_CHANGED_ROWS = {145, 196, 197, 213, 221, 222, 226, 229, 262, 739, 772, 784, 786}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def fresh_summary(candidate):
    current = score.score(candidate)
    baseline = score.load_baseline(SWARM / "baseline" / "score.json")
    return {
        "candidate_sha256": sha256(candidate),
        "normalized": sum(v["normalized"] for v in current.values()),
        "raw": sum(v["raw"] for v in current.values()),
        "total": len(current),
        "matched_text_bytes": sum(v["bytes"] for v in current.values() if v["normalized"]),
        "gains": [hex(k) for k, v in sorted(current.items()) if v["normalized"] and not baseline.get(k, {}).get("normalized")],
        "losses": [hex(k) for k, v in sorted(current.items()) if not v["normalized"] and baseline.get(k, {}).get("normalized")],
        "raw_gains": [hex(k) for k, v in sorted(current.items()) if v["raw"] and not baseline.get(k, {}).get("raw")],
        "raw_losses": [hex(k) for k, v in sorted(current.items()) if not v["raw"] and baseline.get(k, {}).get("raw")],
    }


def source_differences(left, right):
    left_files = {p.relative_to(left) for p in left.rglob("*") if p.is_file()}
    right_files = {p.relative_to(right) for p in right.rglob("*") if p.is_file()}
    changed = sorted(left_files.symmetric_difference(right_files), key=str)
    for relative in sorted(left_files.intersection(right_files), key=str):
        if (left / relative).read_bytes() != (right / relative).read_bytes():
            changed.append(relative)
    return [p.as_posix() for p in changed]


def main():
    summary = load(LANE / "SUMMARY.json")
    target1 = load(OUT1 / "target.json")
    target2 = load(OUT2 / "target.json")
    score1 = load(OUT1 / "score.json")["summary"]
    score2 = load(OUT2 / "score.json")["summary"]
    baseline_score = load(SWARM / "baseline" / "score.json")["windows"]
    final_source = LANE / "source" / "src" / "create_v2.rs"
    final_quote = LANE / "source" / "src" / "pump_quote.rs"
    x27_source = X27 / "create_v2.rs"
    original_lines = x27_source.read_text().splitlines()
    final_lines = final_source.read_text().splitlines()
    changed_rows = {i for i, (a, b) in enumerate(zip(original_lines, final_lines), 1) if a != b}
    baseline_quote_lines = (BASELINE_SOURCE / "src" / "pump_quote.rs").read_text().splitlines()
    final_quote_lines = final_quote.read_text().splitlines()
    quote_rows = {i for i, (a, b) in enumerate(zip(baseline_quote_lines, final_quote_lines), 1) if a != b}
    with (SWARM / ".attempts.lock").open("r") as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        ledger_rows = [json.loads(line) for line in (SWARM / "ATTEMPTS.jsonl").read_text().splitlines() if line.strip()]
        fcntl.flock(lock, fcntl.LOCK_UN)
    ledger_by_id = {row["attempt_id"]: row for row in ledger_rows}
    expected_ids = {"06d0209f3f24422cbd6b160fa6dca50a", "67d0513ddb55467fa8114e52a0409df8"}
    ledger_ok = expected_ids.issubset(ledger_by_id)
    for attempt in summary["attempts"]:
        row = ledger_by_id.get(attempt["attempt_id"])
        ledger_ok = ledger_ok and row is not None and row["dedupe_key"] == attempt["dedupe_key"]
        if row:
            ledger_ok = ledger_ok and row["data"]["normalized"] == attempt["official_census"]["normalized"]
            ledger_ok = ledger_ok and row["data"]["raw"] == attempt["official_census"]["raw"]
            ledger_ok = ledger_ok and row["data"]["create_v2_sha256"] == attempt["source_sha256"]["create_v2"]
            ledger_ok = ledger_ok and row["data"]["unstripped_sha256"] == attempt["elf_sha256"]["unstripped"]
    checks = {
        "summary_and_target_json_valid": True,
        "target_scope_exact": [t["original"] for t in summary["targets"]] == ["0x1e7c0"] and summary["targets"][0]["name"] == "pump_recovered::create_v2::execute",
        "original_elf_hash": sha256(SWARM / "tools" / "base" / "original.so") == "7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d",
        "pinned_create_input_unchanged": sha256(BASELINE_SOURCE / "src" / "create_v2.rs") == "afd072350a1febfb4c7e0b327a40f73556b3407d53bd609edf4b01f9ac1c198e",
        "pinned_quote_input_unchanged": sha256(BASELINE_SOURCE / "src" / "pump_quote.rs") == "68e893a86a76bf391a296b0b76f89355971503f67edb1e762401660b01f3646a",
        "canonical_unstripped_hash": sha256(SWARM / "baseline" / "canonical-unstripped.so") == "0f50faa8c325104dc77898ed84866dec2ad1eec475b6abba72c475cf7bf9bab6",
        "baseline_score_counts": sum(v["normalized"] for v in baseline_score.values()) == 1019 and sum(v["raw"] for v in baseline_score.values()) == 188 and len(baseline_score) == 1035,
        "final_source_scope_exact": source_differences(BASELINE_SOURCE, LANE / "source") == ["src/create_v2.rs", "src/pump_quote.rs"],
        "quote_visibility_only": quote_rows == {78} and len(baseline_quote_lines) == len(final_quote_lines) and final_quote_lines[77].startswith("pub(crate) fn global_quote("),
        "x27_source_hash": sha256(x27_source) == "736ef43b46f92f1198ede4d13858453723c7fcc21ef47feeee0006dd8660c841",
        "x27_unstripped_hash": sha256(X27 / "unstripped.so") == "8038e1c90e532e20b0ad7837a862850b0fda55b9f456f02279fb2103a6b57096",
        "first_archived_source_hashes": sha256(OUT1 / "create_v2.rs") == target1["hashes"]["create_v2"] and sha256(OUT1 / "pump_quote.rs") == target1["hashes"]["pump_quote"],
        "final_archived_source_exact": final_source.read_bytes() == (OUT2 / "create_v2.rs").read_bytes() and final_quote.read_bytes() == (OUT2 / "pump_quote.rs").read_bytes(),
        "first_elf_hashes": sha256(OUT1 / "unstripped.so") == target1["hashes"]["unstripped"] and sha256(OUT1 / "candidate.so") == target1["hashes"]["candidate"],
        "final_elf_hashes": sha256(OUT2 / "unstripped.so") == target2["hashes"]["unstripped"] and sha256(OUT2 / "candidate.so") == target2["hashes"]["candidate"],
        "saved_score_hashes": score1["candidate_sha256"] == sha256(OUT1 / "unstripped.so") and score2["candidate_sha256"] == sha256(OUT2 / "unstripped.so"),
        "first_official_census": score1["normalized"] == 1013 and score1["raw"] == 188 and score1["losses"] == EXPECTED_LOSSES and score1["raw_losses"] == [],
        "final_official_census": score2["normalized"] == 1019 and score2["raw"] == 188 and score2["total"] == 1035 and not score2["gains"] and not score2["losses"] and not score2["raw_gains"] and not score2["raw_losses"],
        "fresh_official_rescore": fresh_summary(OUT2 / "unstripped.so") == score2,
        "target_still_unaccepted": not target2["target"]["normalized"] and not target2["target"]["raw"] and not target2["target"]["instruction_equal"],
        "target_metrics_exact": target2["target"]["original_bytes"] == 15576 and target2["target"]["candidate_bytes"] == 15528 and target2["target"]["instruction_similarity"] == 0.46174568965517243,
        "source_rows_preserved_exactly": len(original_lines) == 816 and len(final_lines) == 816 and changed_rows == EXPECTED_CHANGED_ROWS,
        "attempt_ledger_complete_and_consistent": ledger_ok,
        "summary_best_candidate_consistent": summary["best_candidate"]["unstripped_sha256"] == sha256(OUT2 / "unstripped.so") and summary["best_candidate"]["candidate_sha256"] == sha256(OUT2 / "candidate.so"),
        "source_diffs_present": all((out / name).stat().st_size > 0 for out in (OUT1, OUT2) for name in ("source-vs-baseline.patch", "create-v2-vs-x27.patch")),
        "hash_records_present": all((out / "hashes.txt").stat().st_size > 0 for out in (OUT1, OUT2)),
    }
    result = {
        "ok": all(checks.values()),
        "checks": checks,
        "final_official_census": score2,
        "final_target": target2["target"],
        "final_source_sha256": {
            "create_v2": sha256(final_source),
            "pump_quote": sha256(final_quote),
        },
        "summary_sha256": sha256(LANE / "SUMMARY.json"),
        "ledger_attempt_ids": sorted(expected_ids),
    }
    (LANE / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
