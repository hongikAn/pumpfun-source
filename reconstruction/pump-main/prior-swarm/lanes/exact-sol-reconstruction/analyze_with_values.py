#!/usr/bin/env python3
"""Compare every aligned with_values call in the exact-SOL target window."""
import json
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
SWARM = LANE.parents[1]
sys.path.insert(0, str(SWARM / "tools/harness"))
import score  # noqa: E402
import win  # noqa: E402

TARGET = 0x14F4E0
SYMBOL = "pump_recovered::pump_recovered::buy_exact_sol_in"
WITH_VALUES_TARGETS = {0x340, 0x11B0}


def direct_target(address, raw):
    import struct
    op, regs, _off, imm = struct.unpack_from("<BBhi", raw, 0)
    if op == 0x85 and regs >> 4 == 1 and imm != -1:
        return address + 8 + imm * 8
    return None


def main():
    candidate_path = LANE / "outputs/wrapper-scalar-optionbool/unstripped.so"
    original_window = next(w for w in score.original_windows() if w["start"] == TARGET)
    candidate = win.Cand(candidate_path)
    start, size, _name = next(
        (s, n, name) for s, n, name in candidate.funcs if win.demangle(name) == SYMBOL
    )
    original = win.insns(original_window["raw"], TARGET, win.ORIG_SECS)
    emitted = win.insns(candidate.fn(start, size), start, candidate.secs)
    original_text = win.objdump_text(score.BASE / "original.so", TARGET, TARGET + len(original_window["raw"]))
    candidate_text = win.objdump_text(candidate_path, start, start + size)
    assert len(original) == len(emitted)

    calls = []
    for index, (orig, cand) in enumerate(zip(original, emitted)):
        orig_target = direct_target(orig[0], orig[1])
        cand_target = direct_target(cand[0], cand[1])
        if orig_target not in WITH_VALUES_TARGETS and cand_target not in WITH_VALUES_TARGETS:
            continue
        following = []
        for o, c in zip(original[index + 1:index + 7], emitted[index + 1:index + 7]):
            following.append({
                "byte_offset": o[0] - TARGET,
                "original_address": hex(o[0]),
                "candidate_address": hex(c[0]),
                "original_instruction": original_text.get(o[0]),
                "candidate_instruction": candidate_text.get(c[0]),
                "normalized_equal": o[2] == c[2],
                "raw_equal": o[1] == c[1],
            })
        calls.append({
            "byte_offset": orig[0] - TARGET,
            "original_address": hex(orig[0]),
            "candidate_address": hex(cand[0]),
            "original_target": hex(orig_target) if orig_target is not None else None,
            "candidate_target": hex(cand_target) if cand_target is not None else None,
            "following": following,
        })

    result = {
        "schema": "exact-sol-with-values-calls-v1",
        "candidate": str(candidate_path.resolve()),
        "candidate_start": hex(start),
        "original_start": hex(TARGET),
        "call_count": len(calls),
        "calls": calls,
        "note": "The direct targets 0x340 and 0x11b0 are the candidate u64,u64 and one-value i32 with_values specializations respectively. Offsets here are true byte offsets, including both slots of lddw instructions.",
    }
    output = LANE / "analysis/with-values-calls.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
