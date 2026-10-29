#!/usr/bin/env python3
"""Recover basic-block and call ownership evidence for buy_exact_quote."""
from __future__ import annotations

import json
import re
from pathlib import Path

from analyze_calls import LANE, ROOT, calls, candidate_names, original_names, parse_asm


JUMP = re.compile(r"^(j[a-z]+)\s+.*?([+-]0x[0-9a-f]+|[+-]\d+)(?:\s+<.*)?$")


def make_cfg(path, names):
    rows = parse_asm(path)
    by_address = dict(rows)
    addresses = [address for address, _ in rows]
    next_address = {address: addresses[i + 1] if i + 1 < len(addresses) else None for i, address in enumerate(addresses)}
    decoded = {}
    leaders = {addresses[0]}
    for address, text in rows:
        match = JUMP.match(text)
        if match:
            op = match.group(1)
            offset = int(match.group(2), 0)
            target = address + 8 + offset * 8
            fallthrough = next_address[address] if op != "ja" else None
            decoded[address] = {"op": op, "target": target, "fallthrough": fallthrough}
            leaders.add(target)
            if fallthrough is not None:
                leaders.add(fallthrough)
        elif text == "exit":
            decoded[address] = {"op": "exit", "target": None, "fallthrough": None}
    ordered_leaders = sorted(leaders)
    blocks = []
    for index, start in enumerate(ordered_leaders):
        if start not in by_address:
            continue
        end_limit = ordered_leaders[index + 1] if index + 1 < len(ordered_leaders) else None
        instructions = [(address, text) for address, text in rows if address >= start and (end_limit is None or address < end_limit)]
        if not instructions:
            continue
        end = instructions[-1][0]
        block_calls = []
        for item in calls(instructions):
            item["target_name"] = names.get(int(item["target"], 0))
            block_calls.append(item)
        terminator = decoded.get(end, {"op": "fallthrough", "target": None, "fallthrough": next_address[end]})
        blocks.append({
            "start": hex(start),
            "last_instruction": hex(end),
            "instruction_count": len(instructions),
            "calls": block_calls,
            "terminator": {
                "op": terminator["op"],
                "target": hex(terminator["target"]) if terminator["target"] is not None else None,
                "fallthrough": hex(terminator["fallthrough"]) if terminator["fallthrough"] is not None else None,
            },
            "instructions": [{"address": hex(address), "text": text} for address, text in instructions],
        })
    return blocks


def compact(blocks):
    return [{
        "start": block["start"],
        "last_instruction": block["last_instruction"],
        "call_sites": [{"site": c["call_site"], "target": c["target"], "name": c["target_name"]} for c in block["calls"]],
        "terminator": block["terminator"],
    } for block in blocks]


def main():
    original = make_cfg(LANE / "evidence/original-buy-exact-quote.asm", original_names())
    candidate = make_cfg(LANE / "evidence/baseline-buy-exact-quote.asm", candidate_names())
    (LANE / "evidence/original-cfg.json").write_text(json.dumps({"schema": "sbpf-cfg-v1", "blocks": original}, indent=2) + "\n")
    (LANE / "evidence/candidate-cfg.json").write_text(json.dumps({"schema": "sbpf-cfg-v1", "blocks": candidate}, indent=2) + "\n")
    summary = {
        "schema": "v3-exactquote-cfg-summary-v1",
        "target": "0x1489f8",
        "method": "Direct branches only; leaders are function entry, direct branch targets, and conditional fallthroughs.",
        "limits": ["No indirect branches occur in these windows.", "Physical block order is not execution order."],
        "original": {"block_count": len(original), "blocks": compact(original)},
        "canonical_candidate": {"block_count": len(candidate), "blocks": compact(candidate)},
    }
    destination = LANE / "evidence/cfg-summary.json"
    destination.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({
        "output": str(destination.relative_to(ROOT)),
        "original_blocks": len(original),
        "candidate_blocks": len(candidate),
        "original_business_call_blocks": sum(bool(b["calls"]) for b in original),
        "candidate_business_call_blocks": sum(bool(b["calls"]) for b in candidate),
    }, indent=2))


if __name__ == "__main__":
    main()
