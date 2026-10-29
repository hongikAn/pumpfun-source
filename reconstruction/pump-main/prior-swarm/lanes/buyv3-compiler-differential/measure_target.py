#!/usr/bin/env python3
"""Measure buy_v3 with the exact analyze_probes.py instruction-alignment metric."""
import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
SWARM = LANE.parent.parent
sys.path.insert(0, str(SWARM / "tools/harness"))
import score  # noqa: E402
import win  # noqa: E402

TARGET = 0x147BA0
SYMBOL = r"trade::buy$"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path, required=True)
    args = parser.parse_args()

    original = {w["start"]: w for w in score.original_windows()}[TARGET]
    candidate = win.Cand(args.candidate)
    functions = [
        (address, size, name)
        for address, size, name in candidate.funcs
        if re.search(SYMBOL, win.demangle(name))
    ]
    if len(functions) != 1:
        raise SystemExit(f"expected exactly one trade::buy function, found {len(functions)}")
    address, size, name = functions[0]
    original_rows = list(win.insns(original["raw"], TARGET, win.ORIG_SECS))
    candidate_rows = list(win.insns(candidate.fn(address, size), address, candidate.secs))
    original_text = [row[2] for row in original_rows]
    candidate_text = [row[2] for row in candidate_rows]
    matcher = difflib.SequenceMatcher(None, original_text, candidate_text, autojunk=False)
    opcodes = matcher.get_opcodes()
    aligned_difference_slots = sum(
        max(i2 - i1, j2 - j1)
        for tag, i1, i2, j1, j2 in opcodes
        if tag != "equal"
    )
    differences = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            continue
        differences.append({
            "tag": tag,
            "original_indexes": [i1, i2],
            "candidate_indexes": [j1, j2],
            "aligned_difference_slots": max(i2 - i1, j2 - j1),
            "original_addresses": [hex(row[0]) for row in original_rows[i1:i2]],
            "candidate_addresses": [hex(row[0]) for row in candidate_rows[j1:j2]],
            "original_normalized_hex": [value.hex() for value in original_text[i1:i2]],
            "candidate_normalized_hex": [value.hex() for value in candidate_text[j1:j2]],
        })
    result = {
        "metric_source": "research/goal-pump-recovery-20261028/analyze_probes.py lines 26-28",
        "target": hex(TARGET),
        "candidate": str(args.candidate),
        "candidate_sha256": hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        "candidate_start": hex(address),
        "candidate_symbol": win.demangle(name),
        "original_bytes": original["bytes"],
        "candidate_bytes": size,
        "original_instruction_slots": len(original_text),
        "candidate_instruction_slots": len(candidate_text),
        "normalized_instruction_similarity": matcher.ratio(),
        "aligned_instruction_difference_slots": aligned_difference_slots,
        "differences": differences,
    }
    args.json_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "differences"}, indent=2))


if __name__ == "__main__":
    main()
