#!/usr/bin/env python3
"""CFG-sensitive stack-definition and cleanup evidence for admin_cto::execute.

The reaching-definition pass models direct stack stores only. It deliberately
reports multiple possible definitions at joins instead of guessing a source
origin. Callee writes are not assumed away: conclusions must be read with the
listed intervening calls and pointer arguments.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path
import hashlib
import json
import re
import struct

import analyze_memcmp as base

LANE = Path(__file__).resolve().parent
OUT = LANE / "evidence"
OUT.mkdir(exist_ok=True)

IMAGES = {image.name: image for image in (base.original, base.natural)}
ADDRS = {name: [a for a, _, _ in image.insns] for name, image in IMAGES.items()}
INDEX = {name: {a: i for i, a in enumerate(addrs)} for name, (image, addrs) in
         ((name, (IMAGES[name], addrs)) for name, addrs in ADDRS.items())}

QUERIES = [
    ("original", 0x1C8, 1, "sharing-key versus curve creator"),
    ("original", 0x340, 1, "curve quote-mint versus zero"),
    ("original", 0xCC8, 1, "selected target versus zero"),
    ("original", 0xD10, 2, "selected target versus derived key"),
    ("original", 0xD58, 2, "selected target versus account key"),
    ("original", 0x1940, 1, "later key versus zero"),
    ("original", 0x1DF0, 1, "collection quote account key versus native mint"),
    ("original", 0x1F30, 2, "holder vault account key versus derived destination"),
    ("original", 0x5BD8, 1, "shared-path quote account key versus native mint"),
    ("natural_closure", 0x5B8, 1, "first early selected-key zero comparison"),
    ("natural_closure", 0xAB0, 1, "second early selected-key zero comparison"),
    ("natural_closure", 0xD78, 2, "selected key versus derived key"),
    ("natural_closure", 0xE48, 2, "selected key versus account key"),
    ("natural_closure", 0x1848, 1, "first later old-key zero comparison"),
    ("natural_closure", 0x1A78, 1, "second later old-key zero comparison"),
]

STACK_REF = re.compile(r"\[r10\s*([+-])\s*(0x[0-9a-f]+|\d+)\]")
STORE_RE = re.compile(r"^(stxdw|stxw|stxb|stdw|stw|stb)\s+\[r10\s*([+-])\s*(0x[0-9a-f]+|\d+)\]\s*,\s*(\S+)")
WIDTH = {"stxdw": 8, "stdw": 8, "stxw": 4, "stw": 4, "stxb": 1, "stb": 1}


def signed(sign, value):
    n = int(value, 0)
    return n if sign == "+" else -n


def direct_store(text):
    match = STORE_RE.match(text)
    if not match:
        return None
    op, sign, raw_offset, source = match.groups()
    return signed(sign, raw_offset), WIDTH[op], source


def stack_refs(text):
    return [signed(sign, value) for sign, value in STACK_REF.findall(text)]


def instruction(image, addr):
    raw, norm, text = image.by_addr[addr]
    return raw, text


def successors(image, addr):
    raw, text = instruction(image, addr)
    op = raw[0]
    next_addr = addr + len(raw)
    if op == 0x95:  # exit
        return []
    if op == 0x05:  # ja: signed 16-bit instruction offset, unlike call imm
        target = addr + 8 + struct.unpack_from("<h", raw, 2)[0] * 8
        return [target] if target in image.by_addr else []
    if text.startswith("j") and op != 0x85:
        target = addr + 8 + struct.unpack_from("<h", raw, 2)[0] * 8
        result = [next_addr] if next_addr in image.by_addr else []
        if target in image.by_addr:
            result.append(target)
        return result
    return [next_addr] if next_addr in image.by_addr else []


def graph(image):
    preds = {addr: [] for addr, _, _ in image.insns}
    succs = {}
    for addr, _, _ in image.insns:
        succs[addr] = successors(image, addr)
        for target in succs[addr]:
            preds[target].append(addr)
    return succs, preds


GRAPHS = {name: graph(image) for name, image in IMAGES.items()}


def memcmp_argument(image, call_addr, register):
    """Resolve only a same-block rN = r10 + constant argument chain."""
    wanted = f"r{register}"
    reg_values = {"r10": 0}
    for addr, _, _ in image.insns:
        if addr == call_addr:
            return reg_values.get(wanted), reg_values
        text = image.text[addr]
        if text.startswith("j") or text == "exit":
            reg_values = {"r10": 0}
            continue
        mov = re.match(r"^mov64\s+(r\d+),\s*(r\d+)$", text)
        if mov:
            dst, src = mov.groups()
            reg_values[dst] = reg_values.get(src)
            continue
        add = re.match(r"^add64\s+(r\d+),\s*(-?0x[0-9a-f]+|-?\d+)$", text)
        if add:
            dst, raw_imm = add.groups()
            previous = reg_values.get(dst)
            reg_values[dst] = None if previous is None else previous + int(raw_imm, 0)
            continue
        # Any other register-writing instruction kills a simple pointer chain.
        first = re.match(r"^[a-z0-9]+\s+(r\d+)", text)
        if first and not text.startswith("st"):
            reg_values[first.group(1)] = None
    raise AssertionError("call not found")


def reaching_definitions(image, call_addr, offset):
    """May-reaching direct byte definitions immediately before call_addr."""
    succs, preds = GRAPHS[image.name]
    entry = tuple(frozenset(("entry",)) for _ in range(32))
    empty = tuple(frozenset() for _ in range(32))
    ins = {addr: empty for addr, _, _ in image.insns}
    outs = {addr: empty for addr, _, _ in image.insns}
    queue = deque([image.start])
    queued = {image.start}

    def join(predecessor_states):
        if not predecessor_states:
            return empty
        return tuple(frozenset().union(*(state[i] for state in predecessor_states)) for i in range(32))

    def transfer(state, addr):
        text = image.text[addr]
        store = direct_store(text)
        if store is None:
            return state
        store_offset, width, _ = store
        lo = max(offset, store_offset)
        hi = min(offset + 32, store_offset + width)
        if lo >= hi:
            return state
        mutable = list(state)
        label = f"store@{addr:#x}"
        for absolute in range(lo, hi):
            mutable[absolute - offset] = frozenset((label,))
        return tuple(mutable)

    while queue:
        addr = queue.popleft()
        queued.discard(addr)
        if addr == image.start:
            incoming = entry
        else:
            incoming = join([outs[p] for p in preds[addr]])
        outgoing = transfer(incoming, addr)
        changed_in = incoming != ins[addr]
        changed_out = outgoing != outs[addr]
        ins[addr] = incoming
        outs[addr] = outgoing
        if changed_out or changed_in:
            for target in succs[addr]:
                if target not in queued:
                    queue.append(target)
                    queued.add(target)
    return ins[call_addr], outs[call_addr]


def block_start(image, addr):
    for candidate in range(INDEX[image.name][addr], -1, -1):
        current = ADDRS[image.name][candidate]
        if candidate == 0:
            return current
        previous = ADDRS[image.name][candidate - 1]
        text = image.text[previous]
        if text == "exit" or (text.startswith("j") and not text.startswith("call")):
            return current
        if GRAPHS[image.name][1][current] != [previous]:
            return current
    return image.start


def store_context(image, addr, radius=7):
    index = INDEX[image.name][addr]
    start = block_start(image, addr)
    lo = max(INDEX[image.name][start], index - radius)
    hi = min(len(ADDRS[image.name]), index + 2)
    return [{"address": hex(ADDRS[image.name][i]),
             "relative": hex(ADDRS[image.name][i] - image.start),
             "text": image.text[ADDRS[image.name][i]]}
            for i in range(lo, hi)]


def path_calls(image, call_addr, store_addrs):
    """Calls in the query block and direct store blocks, for manual alias audit."""
    relevant_blocks = {block_start(image, call_addr)}
    for addr in store_addrs:
        relevant_blocks.add(block_start(image, addr))
    rows = []
    for start in sorted(relevant_blocks):
        index = INDEX[image.name][start]
        while index < len(ADDRS[image.name]):
            addr = ADDRS[image.name][index]
            text = image.text[addr]
            if text.startswith("call"):
                rows.append({"address": hex(addr), "relative": hex(addr - image.start),
                             "block": hex(start), "text": text})
            if addr != start and (text == "exit" or text.startswith("j")):
                break
            index += 1
            if index < len(ADDRS[image.name]) and block_start(image, ADDRS[image.name][index]) != start:
                break
    return rows


def query_report(name, call_offset, register, role):
    image = IMAGES[name]
    call_addr = image.start + call_offset
    offset, pointer_chain = memcmp_argument(image, call_addr, register)
    if offset is None:
        return {"image": name, "call_offset": hex(call_offset), "role": role,
                "argument": f"r{register}", "origin": "unresolved same-block pointer"}
    incoming, outgoing = reaching_definitions(image, call_addr, offset)
    assert incoming == outgoing  # memcmp is not a direct stack store
    groups = []
    start = 0
    while start < 32:
        defs = incoming[start]
        end = start + 1
        while end < 32 and incoming[end] == defs:
            end += 1
        groups.append({"bytes": [start, end], "definitions": sorted(defs)})
        start = end
    store_addrs = sorted({int(label.split("@")[1], 16) for defs in incoming for label in defs
                          if label.startswith("store@")})
    stores = []
    for addr in store_addrs:
        store = direct_store(image.text[addr])
        stores.append({"address": hex(addr), "relative": hex(addr - image.start),
                       "text": image.text[addr], "stack_offset": hex(store[0]),
                       "width": store[1], "source": store[2],
                       "same_block_context": store_context(image, addr)})
    return {
        "image": name,
        "execute_start": hex(image.start),
        "call_offset": hex(call_offset),
        "call_address": hex(call_addr),
        "role": role,
        "argument": f"r{register}",
        "stack_offset": hex(offset),
        "same_block_pointer_chain": {key: None if value is None else hex(value)
                                     for key, value in pointer_chain.items()},
        "may_reaching_direct_store_bytes": groups,
        "all_32_bytes_single_direct_definition": all(len(defs) == 1 and next(iter(defs)).startswith("store@")
                                                       for defs in incoming),
        "reaching_stores": stores,
        "calls_in_relevant_blocks_for_alias_audit": path_calls(image, call_addr, store_addrs),
        "interpretation_limit": "Direct-store RD is a may analysis. Multiple definitions or entry labels require guard-sensitive review; an opaque callee sret/pointer write is not converted into a typed source origin without separate call evidence.",
    }


def window(image, center, before=28, after=36):
    index = INDEX[image.name][center]
    lo = max(0, index - before)
    hi = min(len(ADDRS[image.name]), index + after + 1)
    return [{"address": hex(ADDRS[image.name][i]),
             "relative": hex(ADDRS[image.name][i] - image.start),
             "text": image.text[ADDRS[image.name][i]],
             "successors": [hex(x - image.start) for x in GRAPHS[image.name][0][ADDRS[image.name][i]]],
             "predecessors": [hex(x - image.start) for x in GRAPHS[image.name][1][ADDRS[image.name][i]]]}
            for i in range(lo, hi)]


def cleanup_report(image, relative):
    center = image.start + relative
    exits = []
    for addr, _, _ in image.insns:
        if image.text[addr] == "exit":
            exits.append({"address": hex(addr), "relative": hex(addr - image.start),
                          "context": window(image, addr, before=10, after=0)})
    joins = []
    for addr, _, _ in image.insns:
        predecessors = GRAPHS[image.name][1][addr]
        if len(predecessors) >= 3 and (addr == image.start or image.text[ADDRS[image.name][INDEX[image.name][addr] - 1]].startswith("j")):
            joins.append({"relative": hex(addr - image.start), "predecessor_count": len(predecessors),
                          "predecessors": [hex(x - image.start) for x in predecessors],
                          "first_instructions": window(image, addr, before=0, after=5)})
    joins.sort(key=lambda row: (-row["predecessor_count"], int(row["relative"], 16)))
    return {
        "image": image.name,
        "requested_relative": hex(relative),
        "requested_address": hex(center),
        "instruction_at_site": image.text[center],
        "window": window(image, center),
        "exit_sites": exits,
        "largest_instruction_joins": joins[:20],
        "limit": "Instruction predecessors are actual decoded branch/fallthrough edges. Cleanup source roles are not inferred solely from fan-in.",
    }


# Full disassembly is evidence, not a normalized-body claim.
for image in IMAGES.values():
    with (OUT / f"{image.name}-execute-disassembly.txt").open("w") as stream:
        for addr, _, _ in image.insns:
            stream.write(f"{addr:#x} {addr - image.start:#x} {image.text[addr]}\n")

report = {
    "schema": "cto-execute-stack-provenance-cleanup-v1",
    "scope": "CFG-sensitive may-reaching direct stack byte definitions at actual memcmp calls, plus decoded cleanup windows. No source-origin claim from a same-block slice alone.",
    "inputs": {name: {"path": str(image.path), "sha256": base.sha(image.path),
                      "execute_start": hex(image.start), "execute_bytes": image.size}
               for name, image in IMAGES.items()},
    "queries": [query_report(*query) for query in QUERIES],
    "cleanup": [cleanup_report(base.original, 0x5868),
                cleanup_report(base.natural, 0x3148)],
    "method_limits": [
        "The may-RD pass includes direct byte stores and entry unknowns, but does not synthesize typed origins for opaque callee writes.",
        "A single direct definition on all decoded paths is necessary but not sufficient for a typed source name; intervening calls are listed for pointer-alias review.",
        "Stack slots are program-point specific and may be reused for different keys later in the function.",
    ],
}
path = OUT / "stack-provenance-cleanup.json"
path.write_text(json.dumps(report, indent=2) + "\n")

with (OUT / "stack-provenance-cleanup.txt").open("w") as stream:
    for query in report["queries"]:
        stream.write(f"\n===== {query['image']} memcmp {query['call_offset']} {query['role']} =====\n")
        stream.write(f"argument={query['argument']} stack={query.get('stack_offset')} single={query.get('all_32_bytes_single_direct_definition')}\n")
        for group in query.get("may_reaching_direct_store_bytes", []):
            stream.write(f"bytes {group['bytes'][0]}..{group['bytes'][1]} defs={','.join(group['definitions'])}\n")
        for store in query.get("reaching_stores", []):
            stream.write(f"STORE {store['relative']}: {store['text']}\n")
            for row in store["same_block_context"]:
                stream.write(f"  {row['relative']} {row['text']}\n")
    for cleanup in report["cleanup"]:
        stream.write(f"\n===== cleanup {cleanup['image']} {cleanup['requested_relative']} =====\n")
        for row in cleanup["window"]:
            stream.write(f"{row['relative']} {row['text']} succ={row['successors']} pred={row['predecessors']}\n")
        stream.write(f"exits={[row['relative'] for row in cleanup['exit_sites']]}\n")

print(json.dumps({"output": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "queries": [{"image": q["image"], "call": q["call_offset"],
                               "stack": q.get("stack_offset"),
                               "single": q.get("all_32_bytes_single_direct_definition")}
                              for q in report["queries"]]}, indent=2))
