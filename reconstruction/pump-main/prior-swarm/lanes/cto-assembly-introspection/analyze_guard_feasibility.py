#!/usr/bin/env python3
"""Path-condition feasibility query for original admin_cto old-zero CFG.

This pass tests whether the fee-tag nonzero fallthrough is necessary to reach
0x1508. It consumes the logged v1 demand result and preserves call-alias limits.
No source candidate, runtime observation, or body-size similarity is involved.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import re

LANE = Path(__file__).resolve().parent
OUT = LANE / "evidence"
PRIOR = OUT / "guard-path-origins.json"
EXPECTED_PRIOR_SHA256 = "6fe05d328381b25189680c05f34990f23dcd0afd1009ee01c0a5002a00a248e7"
LINE = re.compile(r"^(0x[0-9a-f]+) (0x[0-9a-f]+) (.*)$")


@dataclass(frozen=True)
class Insn:
    address: int
    relative: int
    text: str


class Image:
    def __init__(self, path: Path):
        self.path = path
        rows = []
        for raw in path.read_text().splitlines():
            match = LINE.match(raw)
            if not match:
                raise ValueError(f"bad disassembly row: {raw!r}")
            address, relative, text = match.groups()
            rows.append(Insn(int(address, 16), int(relative, 16), text))
        self.insns = rows
        self.by_addr = {row.address: row for row in rows}
        self.by_relative = {row.relative: row for row in rows}
        self.index = {row.address: i for i, row in enumerate(rows)}
        self.start = rows[0].address
        self.successors = {}
        self.predecessors = {row.address: [] for row in rows}
        for row in rows:
            targets = self._successors(row)
            self.successors[row.address] = targets
            for target in targets:
                self.predecessors[target].append(row.address)

    def _successors(self, row: Insn):
        i = self.index[row.address]
        next_addr = self.insns[i + 1].address if i + 1 < len(self.insns) else None
        text = row.text
        if text == "exit":
            return []
        if text.startswith("ja "):
            match = re.match(r"^ja\s+([+-](?:0x[0-9a-f]+|\d+))", text)
            if not match:
                raise ValueError(f"bad ja: {text}")
            target = row.address + 8 + int(match.group(1), 0) * 8
            return [target] if target in self.by_addr else []
        if text.startswith("j"):
            match = re.search(r",\s*([+-](?:0x[0-9a-f]+|\d+))(?:\s|$)", text)
            if not match:
                raise ValueError(f"bad conditional jump: {text}")
            target = row.address + 8 + int(match.group(1), 0) * 8
            result = [next_addr] if next_addr in self.by_addr else []
            if target in self.by_addr:
                result.append(target)
            return result
        return [next_addr] if next_addr in self.by_addr else []

    def row(self, relative):
        return self.by_relative[relative]


def row(image, address):
    insn = image.by_addr[address]
    return {
        "relative": hex(insn.relative),
        "address": hex(address),
        "text": insn.text,
        "successors": [hex(image.by_addr[x].relative) for x in image.successors[address]],
        "predecessors": [hex(image.by_addr[x].relative) for x in image.predecessors[address]],
    }


def reachable(image, start_relative, target_relative, forbidden_relative=()):
    start = image.row(start_relative).address
    target = image.row(target_relative).address
    forbidden = {image.row(x).address for x in forbidden_relative}
    if start in forbidden or target in forbidden:
        return False
    queue = deque([start])
    seen = {start}
    while queue:
        addr = queue.popleft()
        if addr == target:
            return True
        for succ in image.successors[addr]:
            if succ not in forbidden and succ not in seen:
                seen.add(succ)
                queue.append(succ)
    return False


def shortest_path(image, start_relative, target_relative, forbidden_relative=()):
    start = image.row(start_relative).address
    target = image.row(target_relative).address
    forbidden = {image.row(x).address for x in forbidden_relative}
    if start in forbidden or target in forbidden:
        return None
    queue = deque([start])
    parent = {start: None}
    while queue:
        addr = queue.popleft()
        if addr == target:
            path = []
            while addr is not None:
                path.append(addr)
                addr = parent[addr]
            return list(reversed(path))
        for succ in image.successors[addr]:
            if succ not in forbidden and succ not in parent:
                parent[succ] = addr
                queue.append(succ)
    return None


def path_record(image, start, target, forbidden=()):
    path = shortest_path(image, start, target, forbidden)
    result = {
        "start": hex(start), "target": hex(target),
        "forbidden": [hex(x) for x in forbidden],
        "reachable": path is not None,
    }
    if path is not None:
        result["instruction_count"] = len(path)
        result["branches"] = [row(image, addr) for addr in path if image.by_addr[addr].text.startswith("j")]
    return result


def window(image, relative, before=5, after=6):
    center = image.row(relative).address
    index = image.index[center]
    return [row(image, image.insns[i].address) for i in range(max(0, index - before), min(len(image.insns), index + after + 1))]


image = Image(OUT / "original-execute-disassembly.txt")
prior_bytes = PRIOR.read_bytes()
prior_sha = hashlib.sha256(prior_bytes).hexdigest()
if prior_sha != EXPECTED_PRIOR_SHA256:
    raise RuntimeError(f"logged v1 evidence hash mismatch: {prior_sha}")
prior = json.loads(prior_bytes)
prior_demands = {}
for demand in prior["demands"]:
    if demand["image"] == "original" and demand["query_relative"] in ("0x1508", "0x1500"):
        prior_demands[demand["query_relative"]] = demand
if set(prior_demands) != {"0x1508", "0x1500"}:
    raise RuntimeError("missing logged v1 entry-origin demands")

slot_rows = [row(image, insn.address) for insn in image.insns if "r10 - 0x928" in insn.text]
address_escape_rows = [
    row(image, insn.address) for insn in image.insns
    if re.search(r"^add64\s+r\d+,\s*-0x928$", insn.text)
    or re.search(r"^mov64\s+r\d+,\s*r10$", insn.text)
    and image.index[insn.address] + 1 < len(image.insns)
    and image.insns[image.index[insn.address] + 1].text.endswith(" -0x928")
]

checks = {
    "entry_to_1508": path_record(image, 0x0, 0x1508),
    "entry_to_1508_avoiding_af8_nonzero_fallthrough_b00": path_record(image, 0x0, 0x1508, [0xB00]),
    "entry_to_1508_avoiding_af8_branch_entirely": path_record(image, 0x0, 0x1508, [0xAF8]),
    "af8_zero_target_10e8_to_1508_avoiding_b00": path_record(image, 0x10E8, 0x1508, [0xB00]),
    "af8_nonzero_fallthrough_b00_to_1508": path_record(image, 0xB00, 0x1508),
    "1508_zero_edge_to_old_zero": path_record(image, 0x1508, 0x1940, [0x1510]),
    "18e8_holder_zero_edge_to_old_zero": path_record(image, 0x18E8, 0x1940, [0x18F0]),
}

nonzero_necessary = not checks["entry_to_1508_avoiding_af8_nonzero_fallthrough_b00"]["reachable"]
unique_entry_r4 = all(
    demand["terminal_definition_count"] == 1
    and demand["terminal_definitions"][0]["kind"] == "entry"
    and demand["terminal_definitions"][0]["demanded_location_before_instruction"] == {"reg": 4}
    for demand in prior_demands.values()
)

report = {
    "schema": "cto-execute-guard-path-feasibility-v2",
    "scope": "Necessary decoded-CFG path conditions for the alternate 0x1508 old-zero predecessor, consuming logged v1 entry-r4 provenance. No candidate or body-size claim.",
    "inputs": {
        "original_disassembly": {
            "path": str(image.path),
            "sha256": hashlib.sha256(image.path.read_bytes()).hexdigest(),
        },
        "logged_v1_guard_path_origins": {
            "path": str(PRIOR),
            "sha256": prior_sha,
            "attempt_dedupe_key": "0x22a10-e38a8b97a-assembly-guard-path-origins-v1",
        },
    },
    "instructions": {
        "af8_window": window(image, 0xAF8),
        "1508_window": window(image, 0x1508),
        "18e8_window": window(image, 0x18E8),
        "18f8_window": window(image, 0x18F8),
    },
    "checks": checks,
    "slot_0x928_all_static_references": slot_rows,
    "direct_slot_address_escape_sites": address_escape_rows,
    "prior_entry_origin_demands": prior_demands,
    "derived_static_conditions": {
        "af8_nonzero_fallthrough_b00_is_necessary_on_every_decoded_entry_path_to_1508": nonzero_necessary,
        "logged_v1_direct_demand_at_1508_has_unique_entry_r4_terminal": unique_entry_r4,
        "no_direct_r10_minus_0x928_address_escape_instruction_found": not address_escape_rows,
        "static_path_condition_supports_zero_edge_infeasibility_subject_to_call_alias_audit": (
            nonzero_necessary and unique_entry_r4 and not address_escape_rows
        ),
    },
    "required_alias_caveat": {
        "calls_crossed_by_v1_demands": {
            key: demand["calls_crossed_by_stack_demand_for_alias_audit"] for key, demand in prior_demands.items()
        },
        "statement": "The necessary nonzero edge and unique direct entry definition do not alone prove runtime infeasibility if a callee can alias the caller slot. Crossed calls are retained for audit; no universal non-holder claim is licensed until that caveat is resolved or explicitly retained.",
    },
    "method_limits": [
        "Decoded-CFG necessity is a static path property, not a runtime record.",
        "A shortest path is a witness only and establishes neither value feasibility nor source-level roles.",
        "The v1 typed fee-tag correspondence is candidate-side corroboration, not original source recovery.",
        "No universal holder-value claim is made by this script; call-alias audit results must accompany any such conclusion.",
        "No body-size or near-match metric is computed.",
    ],
}

path = OUT / "guard-path-feasibility.json"
path.write_text(json.dumps(report, indent=2) + "\n")
with (OUT / "guard-path-feasibility.txt").open("w") as stream:
    stream.write("SCOPE: static path-condition feasibility; call-alias caveat retained; no candidate or body-size claim\n")
    for name, value in report["derived_static_conditions"].items():
        stream.write(f"{name}={value}\n")
    stream.write("\n===== CHECKS =====\n")
    for name, check in checks.items():
        stream.write(f"{name}: reachable={check['reachable']} instructions={check.get('instruction_count')}\n")
        for branch in check.get("branches", []):
            stream.write(f"  {branch['relative']} {branch['text']} succ={branch['successors']}\n")
    stream.write("\n===== SLOT REFERENCES =====\n")
    for item in slot_rows:
        stream.write(f"{item['relative']} {item['text']}\n")
    stream.write("\n===== CROSSED CALLS REQUIRING ALIAS AUDIT =====\n")
    for key, calls in report["required_alias_caveat"]["calls_crossed_by_v1_demands"].items():
        stream.write(f"{key}: {len(calls)} calls\n")
        for call in calls:
            stream.write(f"  {call['relative']} {call['text']}\n")

print(json.dumps({
    "output": str(path),
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "derived_static_conditions": report["derived_static_conditions"],
    "checks": {name: {"reachable": check["reachable"], "instruction_count": check.get("instruction_count")} for name, check in checks.items()},
    "crossed_call_counts": {key: len(calls) for key, calls in report["required_alias_caveat"]["calls_crossed_by_v1_demands"].items()},
}, indent=2))
