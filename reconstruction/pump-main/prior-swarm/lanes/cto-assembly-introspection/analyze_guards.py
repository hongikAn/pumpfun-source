#!/usr/bin/env python3
"""Demand-driven register/stack provenance for admin_cto::execute guard CFG.

This pass consumes the verified instruction streams emitted by
analyze_provenance.py. It resolves actual signed branch offsets, then walks
 backwards from a value use. Mov and direct stack spill/reload chains are
followed across joins; every possible terminal definition is retained.

The analysis is deliberately conservative about source roles: a stack slot is
program-point-specific, and calls crossed by a stack demand are listed for
manual alias review. No instruction-body-size or source-candidate claim is
made by this script.
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


def reg_number(reg: str) -> int:
    return int(reg[1:])


def relative_row(image: Image, address: int, **extra):
    row = image.by_addr[address]
    result = {"relative": hex(row.relative), "address": hex(address), "text": row.text}
    result.update(extra)
    return result


def window(image: Image, relative: int, before=12, after=16):
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


def context(image: Image, address: int, radius=8):
    index = image.index[address]
    start = block_start(image, address)
    lo = max(image.index[start], index - radius)
    hi = min(len(image.insns), index + 2)
    return [relative_row(image, image.insns[i].address) for i in range(lo, hi)]


def backward_demand(image: Image, query_relative: int, location: dict, role: str, limit=250000):
    """Return every terminal definition for location at input to query_relative.

    Locations are {"reg": N} or {"stack": signed_byte_offset, "width": N}.
    A work item (before, location) demands the value at input to before.
    """
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
                    enqueue(pred, {"reg": reg_number(mov.group(2))})
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
                enqueue(pred, {"reg": reg_number(source)})
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
        "cycle_revisits": cycles[:50],
        "cycle_revisit_count": len(cycles),
        "work_items": steps,
        "limit": "May-demand over actual decoded CFG. Calls crossed by stack demands are not assumed alias-free; register r0-r5 are call-clobbered and r6-r9 preserved under the eBPF ABI. A terminal set alone does not assign a typed source role.",
    }


def reaches(image: Image, start_relative: int, target_relative: int):
    start = image.row(start_relative).address
    target = image.row(target_relative).address
    queue = deque([start])
    seen = {start}
    while queue:
        addr = queue.popleft()
        if addr == target:
            return True
        for succ in image.successors[addr]:
            if succ not in seen:
                seen.add(succ)
                queue.append(succ)
    return False


IMAGES = {name: Image(name) for name in ("original", "natural_closure")}
original = IMAGES["original"]
natural = IMAGES["natural_closure"]

DEMANDS = [
    (original, 0x1C78, {"reg": 6}, "first old-nonzero normalization input"),
    (original, 0x1C80, {"reg": 6}, "first old-nonzero branch input"),
    (original, 0x18E0, {"reg": 1}, "branch immediately preceding only original old-zero memcmp"),
    (original, 0x18E0, {"stack": -0x8E0, "width": 8}, "direct stack input to pre-old-zero branch"),
    (original, 0x1D40, {"reg": 1}, "post-wallet original guard input"),
    (original, 0x1D38, {"stack": -0x8E0, "width": 8}, "direct stack input to post-wallet original guard"),
    (original, 0x2160, {"reg": 6}, "later original r6 guard; test whether old boolean survives"),
    (original, 0x5E40, {"reg": 6}, "late original r6 normalization; test whether old boolean survives"),
    (original, 0x5E88, {"reg": 6}, "late original r6 branch; test whether old boolean survives"),
    (natural, 0x1A28, {"reg": 1}, "natural shared guard between wallet and second old-zero memcmp"),
    (natural, 0x1A98, {"reg": 0}, "natural second old-zero result branch"),
]

SITES = [
    (original, 0x18E0), (original, 0x1940), (original, 0x1968),
    (original, 0x1C78), (original, 0x1C80), (original, 0x1D40),
    (original, 0x2020), (original, 0x3C68), (original, 0x5E40),
    (natural, 0x1848), (natural, 0x1870), (natural, 0x1A28),
    (natural, 0x1A78), (natural, 0x1A98), (natural, 0x1B48),
]

report = {
    "schema": "cto-execute-old-guard-dataflow-v1",
    "scope": "Actual decoded CFG demand traces for original old-nonzero and adjacent guards, with natural two-site comparison. No candidate claim and no body-size similarity metric.",
    "inputs": {name: {"path": str(image.path), "sha256": hashlib.sha256(image.path.read_bytes()).hexdigest(),
                      "instruction_count": len(image.insns)} for name, image in IMAGES.items()},
    "demands": [backward_demand(image, relative, location, role)
                for image, relative, location, role in DEMANDS],
    "sites": [{"image": image.name, "relative": hex(relative),
               "window": window(image, relative)} for image, relative in SITES],
    "reachability": {
        "original_old_zero_call_reachable_from_its_own_successor": reaches(original, 0x1948, 0x1940),
        "original_pre_old_branch_to_old_zero_call": reaches(original, 0x18E0, 0x1940),
        "original_old_zero_call_to_first_r6_branch": reaches(original, 0x1940, 0x1C80),
        "original_old_zero_call_to_post_wallet_guard": reaches(original, 0x1940, 0x1D40),
        "natural_first_old_zero_to_second_old_zero": reaches(natural, 0x1848, 0x1A78),
    },
    "method_limits": [
        "Demand traces are may analyses and retain every decoded predecessor; terminal source roles require typed corroboration.",
        "Stack slots are program-point-specific. Calls crossed by a stack demand are listed rather than assumed not to alias.",
        "A single static old-zero memcmp is not by itself proof of explicit source-level boolean caching; guard restructuring and path specialization remain alternatives.",
        "Natural closure is an unqualified comparison image, not a candidate accepted by this analysis.",
    ],
}

path = OUT / "old-guard-dataflow.json"
path.write_text(json.dumps(report, indent=2) + "\n")
with (OUT / "old-guard-dataflow.txt").open("w") as stream:
    stream.write("SCOPE: actual-CFG may-demand evidence; no candidate or body-size claim\n")
    for demand in report["demands"]:
        stream.write(f"\n===== {demand['image']} {demand['query_relative']} {demand['role']} =====\n")
        stream.write(f"query={demand['query_instruction']} location={demand['demanded_location_at_query_input']} terminals={demand['terminal_definition_count']} work={demand['work_items']}\n")
        for terminal in demand["terminal_definitions"]:
            stream.write(f"DEF {terminal['relative']} {terminal['kind']} loc={terminal['demanded_location_before_instruction']} :: {terminal['text']}\n")
        for call in demand["calls_crossed_by_stack_demand_for_alias_audit"]:
            stream.write(f"CROSSED_CALL {call['relative']} {call['text']}\n")
    stream.write("\n===== REACHABILITY =====\n")
    for name, value in report["reachability"].items():
        stream.write(f"{name}={value}\n")
    for site in report["sites"]:
        stream.write(f"\n===== SITE {site['image']} {site['relative']} =====\n")
        for row in site["window"]:
            stream.write(f"{row['relative']} {row['text']} succ={row['successors']} pred={row['predecessors']}\n")

print(json.dumps({
    "output": str(path),
    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "demands": [{"image": row["image"], "query": row["query_relative"],
                 "role": row["role"], "terminals": row["terminal_definition_count"],
                 "definitions": [{"relative": item["relative"], "kind": item["kind"], "text": item["text"]}
                                 for item in row["terminal_definitions"]]}
                for row in report["demands"]],
    "reachability": report["reachability"],
}, indent=2))
