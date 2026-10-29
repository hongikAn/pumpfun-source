#!/usr/bin/env python3
"""Diagnostic reduced-CFG residuals for the main-Pump exact-quote target.

The official score remains the only acceptance rule. This report only maps
normalized instruction and actual-callee differences after the same forwarding
and straight-line reduction used by the recorded best-base analysis.
"""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
SWARM = ROOT.parents[1]
HARNESS = SWARM / "tools" / "harness"
sys.path.insert(0, str(HARNESS))
sys.path.insert(0, str(ROOT / "tools"))
import score  # noqa: E402
import cfg_attribution as cfg  # noqa: E402

TARGET = 0x13F630
SYMBOL = "buy_exact_quote_in_handler17h"


class Inventory(cfg.Inventory):
    def __init__(self, path, original=False):
        super().__init__(path, False)
        self.original = original
        if original:
            self.functions = {
                w["start"]: {"start": w["start"], "size": w["bytes"], "name": ""}
                for w in score.original_windows()
            }
        secs = score.sections(self.elf.b)
        text = secs[".text"]
        lo = text["offset"]
        hi = lo + text["size"]
        self.elf.normalized = (
            self.elf.b[:lo]
            + score.normalize(self.elf.b[lo:hi], text["addr"], secs)
            + self.elf.b[hi:]
        )


def compact_differences(rows):
    result = []
    for row in rows:
        spans = []
        for diff in row["differences"]:
            spans.append({
                "kind": diff["kind"],
                "original_offsets": [r["offset"] for r in diff["original_instructions"]],
                "candidate_offsets": [r["offset"] for r in diff["candidate_instructions"]],
                "original_values": [r["official_normalized_value"] for r in diff["original_instructions"]],
                "candidate_values": [r["official_normalized_value"] for r in diff["candidate_instructions"]],
            })
        result.append({
            "original": row["original_block"],
            "candidate": row["candidate_block"],
            "operations": [row["original_value_operation_count"], row["candidate_value_operation_count"]],
            "terminal_equal": row["terminal_original"] == row["terminal_candidate"],
            "terminal_original": row["terminal_original"],
            "terminal_candidate": row["terminal_candidate"],
            "difference_spans": spans,
        })
    return result


def diagnose(candidate_path):
    original = Inventory(score.BASE / "original.so", True)
    candidate = Inventory(candidate_path)
    candidate_address = next(
        address for address, function in candidate.functions.items()
        if SYMBOL in function["name"] and function["size"] > 10000
    )
    og = original.graph(TARGET, True)
    cg = candidate.graph(candidate_address, True)
    topology = cfg.bijection(og, cg, True)
    rows = cfg.mapped_differences(og, cg, topology["mapping"]) if topology["verified"] else []
    differences = compact_differences(rows)

    oc = [r for n in og["nodes"] for r in n["code"] if r["actual_direct_callee"]]
    cc = [r for n in cg["nodes"] for r in n["code"] if r["actual_direct_callee"]]
    oc.sort(key=lambda r: int(r["offset"], 0))
    cc.sort(key=lambda r: int(r["offset"], 0))
    key = lambda r: r["actual_direct_callee"]["identity_sha256"]
    matcher = difflib.SequenceMatcher(None, list(map(key, oc)), list(map(key, cc)), autojunk=False)
    aligned_callees = sum(block.size for block in matcher.get_matching_blocks())

    return {
        "schema": "exactquote-reordering-residuals-v1",
        "scope": "Diagnostic reduced-CFG comparison only; strict score.json determines acceptance.",
        "symbols_sha256": hashlib.sha256(Path(candidate_path).read_bytes()).hexdigest(),
        "original": {"start": hex(TARGET), "bytes": og["bytes"]},
        "candidate": {"start": hex(candidate_address), "bytes": cg["bytes"]},
        "machine_blocks": [og["machine_blocks"], cg["machine_blocks"]],
        "reduced_cfg_blocks": [og["canonical_reachable_blocks"], cg["canonical_reachable_blocks"]],
        "topology": {k: v for k, v in topology.items() if k not in ("mapping", "partial_mapping")},
        "differing_reduced_block_count": len(differences) if topology["verified"] else None,
        "differing_reduced_blocks": differences if topology["verified"] else None,
        "all_mapped_value_operation_counts_equal": all(
            row["operations"][0] == row["operations"][1] for row in differences
        ) if topology["verified"] else None,
        "forwarded_empty_block_counts": [
            len(og["forwarded_empty_blocks"]), len(cg["forwarded_empty_blocks"])
        ],
        "candidate_forwarded_empty_blocks": cg["forwarded_empty_blocks"],
        "actual_direct_call_counts": [len(oc), len(cc)],
        "actual_ordered_depth2_callees_equal": aligned_callees,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    report = diagnose(args.candidate.resolve())
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in (
        "differing_reduced_blocks", "candidate_forwarded_empty_blocks"
    )}))


if __name__ == "__main__":
    main()
