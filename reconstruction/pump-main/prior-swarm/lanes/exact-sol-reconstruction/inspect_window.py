#!/usr/bin/env python3
"""Report aligned raw and normalized evidence for the exact-SOL target."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
HARNESS = LANE.parents[1] / "tools/harness"
sys.path.insert(0, str(HARNESS))
import score  # noqa: E402
import win  # noqa: E402

TARGET = 0x14F4E0
SYMBOL = "pump_recovered::pump_recovered::buy_exact_sol_in"


def direct_target(address, raw):
    op, regs, _off, imm = struct.unpack_from("<BBhi", raw, 0)
    if op == 0x85 and regs >> 4 == 1 and imm != -1:
        return address + 8 + imm * 8
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    original_window = next(w for w in score.original_windows() if w["start"] == TARGET)
    candidate = win.Cand(args.candidate)
    matches = [(s, n, name) for s, n, name in candidate.funcs if win.demangle(name) == SYMBOL]
    if len(matches) != 1:
        raise SystemExit(f"expected one exact target symbol, found {len(matches)}")
    start, size, name = matches[0]
    raw = candidate.fn(start, size)
    normalized = score.normalize(raw, start, candidate.secs)
    original_raw = original_window["raw"]
    original_normalized = original_window["norm"]
    aligned = len(raw) == len(original_raw)
    raw_differences = [i for i, (a, b) in enumerate(zip(original_raw, raw)) if a != b]
    normalized_differences = [i for i, (a, b) in enumerate(zip(original_normalized, normalized)) if a != b]
    original_insns = win.insns(original_raw, TARGET, win.ORIG_SECS)
    candidate_insns = win.insns(raw, start, candidate.secs)
    original_text = win.objdump_text(score.BASE / "original.so", TARGET, TARGET + len(original_raw))
    candidate_text = win.objdump_text(args.candidate, start, start + size)
    instructions = []
    if aligned and len(original_insns) == len(candidate_insns):
        for offset, (orig, cand) in enumerate(zip(original_insns, candidate_insns)):
            if orig[1] == cand[1] and orig[2] == cand[2]:
                continue
            orig_target = direct_target(orig[0], orig[1])
            cand_target = direct_target(cand[0], cand[1])
            row = {
                "offset": offset * 8,
                "slot": offset,
                "original_address": hex(orig[0]),
                "candidate_address": hex(cand[0]),
                "original_instruction": original_text.get(orig[0]),
                "candidate_instruction": candidate_text.get(cand[0]),
                "original_raw_hex": orig[1].hex(),
                "candidate_raw_hex": cand[1].hex(),
                "original_normalized_hex": orig[2].hex(),
                "candidate_normalized_hex": cand[2].hex(),
            }
            if orig_target is not None or cand_target is not None:
                row["original_direct_target"] = hex(orig_target) if orig_target is not None else None
                row["candidate_direct_target"] = hex(cand_target) if cand_target is not None else None
            instructions.append(row)
    result = {
        "schema": "exact-sol-window-evidence-v1",
        "original": {"start": hex(TARGET), "bytes": len(original_raw), "raw_sha256": hashlib.sha256(original_raw).hexdigest(), "normalized_sha256": hashlib.sha256(original_normalized).hexdigest()},
        "candidate": {"path": str(args.candidate.resolve()), "start": hex(start), "bytes": size, "symbol": win.demangle(name), "raw_sha256": hashlib.sha256(raw).hexdigest(), "normalized_sha256": hashlib.sha256(normalized).hexdigest()},
        "aligned_size": aligned,
        "raw_equal": raw == original_raw,
        "normalized_equal": normalized == original_normalized,
        "raw_different_bytes": len(raw_differences),
        "raw_different_slots": sorted({i // 8 for i in raw_differences}),
        "normalized_different_bytes": len(normalized_differences),
        "normalized_different_slots": sorted({i // 8 for i in normalized_differences}),
        "different_instructions": instructions,
    }
    text = json.dumps(result, indent=2) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text)
    print(text, end="")


if __name__ == "__main__":
    main()
