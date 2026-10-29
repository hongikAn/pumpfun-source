#!/usr/bin/env python3
"""Focused CFG/path provenance for original admin_cto::execute guards.

This is an analysis-only pass. It does not propose a source candidate and never
uses function body size as a similarity measure. Typed LLVM is retained only as
candidate-side corroboration; machine argument roles are not inferred from the
LLVM signature alone.
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
LINE = re.compile(r"^(0x[0-9a-f]+) (0x[0-9a-f]+) (.*)$")
STACK = r"\[r10\s*([+-])\s*(0x[0-9a-f]+|\d+)\]"
LOAD_RE = re.compile(r"^ldxdw\s+(r\d+),\s*" + STACK + r"$")
STORE_RE = re.compile(r"^(stxdw|stdw|stxw|stw|stxb|stb)\s+" + STACK + r"\s*,\s*(\S+)$")
MOV_REG_RE = re.compile(r"^mov64\s+(r\d+),\s*(r\d+)$")
AND_ONE_RE = re.compile(r"^and64\s+(r\d+),\s*0x1$")
REG_DEST_RE = re.compile(r"^[a-z0-9]+\s+(r\d+)(?:,|$)")
WIDTH = {"stxdw": 8, "stdw": 8, "stxw": 4, "stw": 4, "stxb": 1, "stb": 1}


@dataclass(frozen=True)
class Insn:
    address: int
    relative: int
    text: str


class Image:
    def __init__(self, name: str):
        self.name = name
        self.path = OUT / f"{name}-execute-disassembly.txt"
        rows = []
        for raw in self.path.read_text().splitlines():
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

    def _successors(self, row: Insn) -> list[int]:
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

    def row(self, relative: int) -> Insn:
        return self.by_relative[relative]


def signed(sign: str, raw: str) -> int:
    value = int(raw, 0)
    return value if sign == "+" else -value


def direct_store(text: str):
    match = STORE_RE.match(text)
    if not match:
        return None
    op, sign, raw_offset, source = match.groups()
    return signed(sign, raw_offset), WIDTH[op], source


def reg_destination(text: str):
    if text.startswith(("st", "j", "call", "exit")):
        return None
    match = REG_DEST_RE.match(text)
    return match.group(1) if match else None


def relative_row(image: Image, address: int, **extra):
    row = image.by_addr[address]
    result = {"relative": hex(row.relative), "address": hex(address), "text": row.text}
    result.update(extra)
    return result


def window(image: Image, relative: int, before=10, after=12):
    center = image.row(relative).address
    index = image.index[center]
    rows = []
    for i in range(max(0, index - before), min(len(image.insns), index + after + 1)):
        row = image.insns[i]
        rows.append(relative_row(
            image, row.address,
            successors=[hex(image.by_addr[x].relative) for x in image.successors[row.address]],
            predecessors=[hex(image.by_addr[x].relative) for x in image.predecessors[row.address]],
        ))
    return rows


def block_start(image: Image, address: int) -> int:
    index = image.index[address]
    while index > 0:
        current = image.insns[index].address
        previous = image.insns[index - 1].address
        text = image.by_addr[previous].text
        if text == "exit" or text.startswith("j"):
            break
        if image.predecessors[current] != [previous]:
            break
        index -= 1
    return image.insns[index].address


def context(image: Image, address: int, radius=5):
    index = image.index[address]
    start = block_start(image, address)
    lo = max(image.index[start], index - radius)
    hi = min(len(image.insns), index + 2)
    return [relative_row(image, image.insns[i].address) for i in range(lo, hi)]


def backward_demand(image: Image, query_relative: int, location: dict, role: str, limit=250000):
    """May-demand trace at input to query_relative; retain every terminal."""
    query = image.row(query_relative).address
    initial = dict(location)
    work = deque([(query, initial)])
    queued = {(query, json.dumps(initial, sort_keys=True))}
    visited = set()
    terminals = {}
    crossed_calls = {}
    cycles = []
    steps = 0

    def key(addr, loc):
        return addr, json.dumps(loc, sort_keys=True)

    def enqueue(addr, loc):
        nonlocal steps
        item_key = key(addr, loc)
        if item_key in visited:
            cycles.append({"before": hex(image.by_addr[addr].relative), "location": loc})
            return
        if item_key not in queued:
            queued.add(item_key)
            work.append((addr, dict(loc)))

    def terminal(addr, loc, kind):
        row = image.by_addr[addr]
        terminals[(addr, json.dumps(loc, sort_keys=True), kind)] = {
            "relative": hex(row.relative), "address": hex(addr), "text": row.text,
            "kind": kind, "demanded_location_before_instruction": loc,
            "same_block_context": context(image, addr),
        }

    while work:
        before, loc = work.popleft()
        item_key = key(before, loc)
        queued.discard(item_key)
        if item_key in visited:
            continue
        visited.add(item_key)
        steps += 1
        if steps > limit:
            raise RuntimeError(f"demand limit exceeded for {image.name} {query_relative:#x} {loc}")
        if before == image.start:
            terminals[(before, json.dumps(loc, sort_keys=True), "entry")] = {
                "relative": hex(image.by_addr[before].relative), "address": hex(before),
                "text": image.by_addr[before].text, "kind": "entry",
                "demanded_location_before_instruction": loc, "same_block_context": [],
            }
            continue
        predecessors = image.predecessors[before]
        if not predecessors:
            terminals[(before, json.dumps(loc, sort_keys=True), "no-decoded-predecessor")] = {
                "relative": hex(image.by_addr[before].relative), "address": hex(before),
                "text": image.by_addr[before].text, "kind": "no-decoded-predecessor",
                "demanded_location_before_instruction": loc, "same_block_context": context(image, before),
            }
            continue
        for pred in predecessors:
            text = image.by_addr[pred].text
            if "reg" in loc:
                wanted = f"r{loc['reg']}"
                if text.startswith("call") and loc["reg"] <= 5:
                    terminal(pred, loc, "call-clobber")
                    continue
                dest = reg_destination(text)
                if dest != wanted:
                    enqueue(pred, loc)
                    continue
                mov = MOV_REG_RE.match(text)
                if mov and mov.group(1) == wanted:
                    enqueue(pred, {"reg": int(mov.group(2)[1:])})
                    continue
                load = LOAD_RE.match(text)
                if load and load.group(1) == wanted:
                    enqueue(pred, {"stack": signed(load.group(2), load.group(3)), "width": 8})
                    continue
                and_one = AND_ONE_RE.match(text)
                if and_one and and_one.group(1) == wanted:
                    enqueue(pred, loc)
                    continue
                terminal(pred, loc, "register-definition")
                continue

            wanted_offset = loc["stack"]
            wanted_width = loc.get("width", 8)
            if text.startswith("call"):
                crossed_calls[pred] = relative_row(image, pred)
            store = direct_store(text)
            if store is None:
                enqueue(pred, loc)
                continue
            offset, width, source = store
            overlap_lo = max(wanted_offset, offset)
            overlap_hi = min(wanted_offset + wanted_width, offset + width)
            if overlap_lo >= overlap_hi:
                enqueue(pred, loc)
                continue
            if offset == wanted_offset and width == wanted_width and re.fullmatch(r"r\d+", source):
                enqueue(pred, {"reg": int(source[1:])})
            else:
                terminal(pred, loc, "full-or-partial-stack-store")

    rows = sorted(terminals.values(), key=lambda row: (int(row["relative"], 16), row["kind"]))
    return {
        "image": image.name,
        "role": role,
        "query_relative": hex(query_relative),
        "query_instruction": image.row(query_relative).text,
        "demanded_location_at_query_input": initial,
        "terminal_definition_count": len(rows),
        "terminal_definitions": rows,
        "calls_crossed_by_stack_demand_for_alias_audit": sorted(
            crossed_calls.values(), key=lambda row: int(row["relative"], 16)),
        "cycle_revisit_count": len(cycles),
        "work_items": steps,
        "limit": "May-demand over decoded CFG; no path feasibility or source-role assignment is implied.",
    }


def shortest_path(image: Image, start_relative: int, target_relative: int, forbidden_relative=None):
    start = image.row(start_relative).address
    target = image.row(target_relative).address
    forbidden = {image.row(x).address for x in (forbidden_relative or [])}
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


def path_record(image: Image, start: int, target: int, forbidden=None, milestones=()):
    path = shortest_path(image, start, target, forbidden)
    if path is None:
        return {"reachable": False, "start": hex(start), "target": hex(target), "forbidden": [hex(x) for x in (forbidden or [])]}
    milestone_addrs = {image.row(x).address for x in milestones}
    rows = []
    for addr in path:
        row = image.by_addr[addr]
        if addr in milestone_addrs or row.text.startswith(("j", "exit")):
            rows.append(relative_row(image, addr))
    return {
        "reachable": True,
        "start": hex(start),
        "target": hex(target),
        "forbidden": [hex(x) for x in (forbidden or [])],
        "instruction_count": len(path),
        "branch_and_milestone_path": rows,
        "limit": "One shortest decoded-CFG path, not proof of dynamic feasibility or of the source-level value on that path.",
    }


def typed_excerpts(path: Path, line_numbers):
    lines = path.read_text().splitlines()
    return [{"line": number, "text": lines[number - 1]} for number in line_numbers]


IMAGES = {name: Image(name) for name in ("original", "natural_closure")}
original = IMAGES["original"]
natural = IMAGES["natural_closure"]
typed_path = OUT / "typed-current-cto.ll"

DEMANDS = [
    (original, 0x1508, {"reg": 1}, "alternate old-zero predecessor value; identify entry-origin slot"),
    (original, 0x1500, {"stack": -0x928, "width": 8}, "direct stack input at alternate predecessor"),
    (original, 0x1120, {"reg": 1}, "first shared-flag branch input"),
    (original, 0x1820, {"reg": 1}, "second shared-flag branch input"),
    (original, 0x1840, {"reg": 8}, "shared-path alternate predecessor condition"),
    (original, 0x1990, {"reg": 3}, "post-wallet boolean before its stack spill"),
    (original, 0x1D40, {"reg": 1}, "post-wallet boolean branch input"),
    (natural, 0xAF8, {"reg": 1}, "natural early fee-option discriminant branch"),
    (natural, 0x3670, {"reg": 4}, "natural late fee-option discriminant use"),
]

SITES = [
    (original, 0xAF8), (original, 0x1120), (original, 0x1508),
    (original, 0x1820), (original, 0x1840), (original, 0x18F8),
    (original, 0x1990), (original, 0x1D40),
    (natural, 0xAF8), (natural, 0x3670),
]

PATHS = [
    (original, 0x1120, 0x1198, [], (0x1120, 0x1198)),
    (original, 0x1120, 0x18C0, [], (0x1120, 0x18B0, 0x18C0)),
    (original, 0x1820, 0x18C0, [], (0x1820, 0x18B0, 0x18C0)),
    (original, 0x1820, 0x1898, [], (0x1820, 0x1840, 0x1850, 0x1898)),
    (original, 0x1820, 0x1198, [], (0x1820, 0x1840, 0x1848, 0x1138, 0x1198)),
    (original, 0x1508, 0x1940, [], (0x1508, 0x18F8, 0x1940)),
    (original, 0x648, 0x1508, [0x18E8], (0x640, 0x648, 0xAF8, 0x1508)),
    (original, 0x900, 0x1508, [0x18E8], (0x640, 0x900, 0xAF8, 0x1508)),
]

report = {
    "schema": "cto-execute-guard-path-origins-v1",
    "scope": "Actual decoded-CFG path and may-demand evidence for the alternate old-zero predecessor and shared-flag joins. Typed LLVM is candidate-side corroboration only; no candidate or body-size claim.",
    "inputs": {
        **{name: {"path": str(image.path), "sha256": hashlib.sha256(image.path.read_bytes()).hexdigest(),
                  "instruction_count": len(image.insns)} for name, image in IMAGES.items()},
        "typed_current_cto": {"path": str(typed_path), "sha256": hashlib.sha256(typed_path.read_bytes()).hexdigest()},
    },
    "demands": [backward_demand(image, relative, location, role) for image, relative, location, role in DEMANDS],
    "sites": [{"image": image.name, "relative": hex(relative), "window": window(image, relative)} for image, relative in SITES],
    "paths": [path_record(image, start, target, forbidden, milestones) for image, start, target, forbidden, milestones in PATHS],
    "typed_candidate_corroboration": {
        "warning": "These lines describe the typed candidate, not original source. Machine roles require the independent entry/use-site observations above.",
        "fee_option_and_shared_lines": typed_excerpts(typed_path, [1, 592, 594, 743, 744, 802, 834, 835, 842, 848, 851, 915, 928, 931, 934, 2755, 3291, 3403, 3404]),
    },
    "method_limits": [
        "Decoded-CFG reachability is not dynamic reachability and shortest paths are witnesses only.",
        "May-demand traces retain all decoded definitions and do not assume stack slots are never aliased across calls.",
        "Candidate typed LLVM names Option fee and shared roles, but does not by itself establish original source or original machine-register mapping.",
        "An alternate predecessor that bypasses the holder-byte test invalidates a universal non-holder claim; it does not prove that both holder values are dynamically feasible.",
        "No instruction-count, body-size, or near-match metric is computed.",
    ],
}

path = OUT / "guard-path-origins.json"
path.write_text(json.dumps(report, indent=2) + "\n")
with (OUT / "guard-path-origins.txt").open("w") as stream:
    stream.write("SCOPE: decoded-CFG path/may-demand evidence; typed candidate corroboration only; no candidate or body-size claim\n")
    for demand in report["demands"]:
        stream.write(f"\n===== {demand['image']} {demand['query_relative']} {demand['role']} =====\n")
        stream.write(f"query={demand['query_instruction']} location={demand['demanded_location_at_query_input']} terminals={demand['terminal_definition_count']}\n")
        for terminal in demand["terminal_definitions"]:
            stream.write(f"DEF {terminal['relative']} {terminal['kind']} loc={terminal['demanded_location_before_instruction']} :: {terminal['text']}\n")
    stream.write("\n===== PATHS =====\n")
    for item in report["paths"]:
        stream.write(json.dumps(item, separators=(",", ":")) + "\n")
    for site in report["sites"]:
        stream.write(f"\n===== SITE {site['image']} {site['relative']} =====\n")
        for row in site["window"]:
            stream.write(f"{row['relative']} {row['text']} succ={row['successors']} pred={row['predecessors']}\n")
    stream.write("\n===== TYPED CANDIDATE CORROBORATION; NOT ORIGINAL SOURCE =====\n")
    for row in report["typed_candidate_corroboration"]["fee_option_and_shared_lines"]:
        stream.write(f"LINE {row['line']}: {row['text']}\n")

print(json.dumps({
    "output": str(path),
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "demands": [{"image": row["image"], "query": row["query_relative"],
                 "terminals": [{"relative": item["relative"], "kind": item["kind"], "text": item["text"],
                                "location": item["demanded_location_before_instruction"]}
                               for item in row["terminal_definitions"]]}
                for row in report["demands"]],
    "paths": [{"start": row["start"], "target": row["target"], "reachable": row["reachable"],
               "instruction_count": row.get("instruction_count")} for row in report["paths"]],
}, indent=2))
