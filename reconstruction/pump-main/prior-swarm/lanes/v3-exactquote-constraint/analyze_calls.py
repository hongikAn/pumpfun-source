#!/usr/bin/env python3
"""Resolve direct SBPF calls in the exact-quote original and canonical candidate.

This is read-only evidence generation. It does not alter the scorer or binaries.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SWARM = ROOT / "research/goal-pump-main-swarm-20261029"
LANE = SWARM / "lanes/v3-exactquote-constraint"
sys.path.insert(0, str(SWARM / "tools/harness"))
import score  # noqa: E402
import win  # noqa: E402


def parse_asm(path: Path):
    rows = []
    pattern = re.compile(r"^\s*(?:0x)?([0-9a-f]+):?\s+(.*)$")
    for line in path.read_text().splitlines():
        match = pattern.match(line)
        if match:
            rows.append((int(match.group(1), 16), match.group(2).strip()))
    return rows


def calls(rows):
    result = []
    for address, text in rows:
        match = re.match(r"call\s+(-?0x[0-9a-f]+|-?\d+)", text)
        if not match:
            continue
        immediate = int(match.group(1), 0)
        result.append({
            "call_site": hex(address),
            "immediate": immediate,
            "target": hex(address + 8 + immediate * 8),
        })
    return result


def original_names():
    baseline = json.loads((SWARM / "baseline/score.json").read_text())
    targets = json.loads((SWARM / "TARGETS.json").read_text())["targets"]
    names = {}
    for target in targets:
        names[int(target["original"], 0)] = target["name"]
    for start, window in baseline["windows"].items():
        address = int(start)
        symbols = window.get("symbols", [])
        if symbols and address not in names:
            names[address] = " | ".join(sorted({win.demangle(s) for s in symbols}))
    return names


def candidate_names():
    path = SWARM / "baseline/canonical-unstripped.so"
    return {
        address: win.demangle(name)
        for address, size, name in score.candidate_functions(path)
        if size
    }


def annotate(items, names):
    for item in items:
        target = int(item["target"], 0)
        item["target_name"] = names.get(target)
        item["target_is_known_function_start"] = target in names
    return items


def main():
    original = annotate(calls(parse_asm(LANE / "evidence/original-buy-exact-quote.asm")), original_names())
    candidate = annotate(calls(parse_asm(LANE / "evidence/baseline-buy-exact-quote.asm")), candidate_names())
    output = {
        "schema": "v3-exactquote-call-evidence-v1",
        "target": "0x1489f8",
        "method": "Direct call target = call site + 8 + signed immediate * 8; exact function-start symbol lookup only.",
        "limits": [
            "No names are inferred for non-function-start targets or unknown original windows.",
            "Call identity alone does not establish source expression shape or runtime equivalence.",
        ],
        "original": {
            "window": {"start": "0x1489f8", "bytes": 7856},
            "call_count": len(original),
            "calls": original,
        },
        "canonical_candidate": {
            "window": {"start": "0xa0ef8", "bytes": 7800},
            "call_count": len(candidate),
            "calls": candidate,
        },
    }
    destination = LANE / "evidence/call-targets.json"
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({
        "output": str(destination.relative_to(ROOT)),
        "original_calls": len(original),
        "original_named": sum(c["target_name"] is not None for c in original),
        "candidate_calls": len(candidate),
        "candidate_named": sum(c["target_name"] is not None for c in candidate),
    }, indent=2))


if __name__ == "__main__":
    main()
