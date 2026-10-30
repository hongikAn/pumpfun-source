#!/usr/bin/env python3
"""Record diagnostic target metrics without changing official acceptance rules."""
import argparse
import difflib
import hashlib
import json
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
HARNESS = LANE.parents[1] / "tools" / "harness"
sys.path.insert(0, str(HARNESS))
import score
import win

TARGET = 0x1E7C0
TARGET_NAME = "pump_recovered::create_v2::execute"
X27_UNSTRIPPED = Path("research/goal-pump-create-recovery-20261028/trials/x27_current_roles/unstripped.so")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    unstripped = output / "unstripped.so"
    stripped = output / "candidate.so"
    census = json.loads((output / "score.json").read_text())
    summary = census["summary"]
    candidate = win.Cand(unstripped)
    functions = [f for f in candidate.funcs if win.demangle(f[2]) == TARGET_NAME]
    if len(functions) != 1:
        raise SystemExit(f"expected one {TARGET_NAME}, found {len(functions)}")
    start, size, symbol = functions[0]
    window = next(w for w in score.original_windows() if w["start"] == TARGET)
    original_tokens = [x[2] for x in win.insns(window["raw"], window["start"], win.ORIG_SECS)]
    candidate_tokens = [x[2] for x in win.insns(candidate.fn(start, size), start, candidate.secs)]
    target_window = census["windows"][str(TARGET)]
    losses = []
    for address in summary["losses"] + summary["raw_losses"]:
        key = str(int(address, 16))
        losses.append({
            "original": address,
            "candidate": target_window if key == str(TARGET) else census["windows"][key],
        })
    result = {
        "target": {
            "original": hex(TARGET),
            "name": TARGET_NAME,
            "candidate": hex(start),
            "symbol": symbol,
            "original_bytes": window["bytes"],
            "candidate_bytes": size,
            "instruction_equal": original_tokens == candidate_tokens,
            "instruction_similarity": difflib.SequenceMatcher(None, original_tokens, candidate_tokens, autojunk=False).ratio(),
            "normalized": target_window["normalized"],
            "raw": target_window["raw"],
            "diagnostic_only": True,
        },
        "census": summary,
        "baseline_preserved": not summary["losses"] and not summary["raw_losses"],
        "loss_details": losses,
        "hashes": {
            "create_v2": sha256(LANE / "source" / "src" / "create_v2.rs"),
            "pump_quote": sha256(LANE / "source" / "src" / "pump_quote.rs"),
            "unstripped": sha256(unstripped),
            "candidate": sha256(stripped),
        },
        "equivalent_to_x27_unstripped": sha256(unstripped) == sha256(X27_UNSTRIPPED),
    }
    (output / "target.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
