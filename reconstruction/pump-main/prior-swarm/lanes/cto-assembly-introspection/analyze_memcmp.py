#!/usr/bin/env python3
"""Bind actual CTO memcmp calls to machine operands and ELF constants.

This is static evidence only. Register setup is reported verbatim; no linear
slice is treated as proof across a control-flow join or an opaque callee write.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys

LANE = Path(__file__).resolve().parent
SWARM = LANE.parents[1]
RECOVERY = SWARM.parent / "goal-pump-cto-recovery-20261029"
HARNESS = SWARM / "tools/harness"
sys.path.insert(0, str(HARNESS))
import score
import win

OUT = LANE / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
ORIGINAL_START = 0x22A10
ORIGINAL_SIZE = 27400


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Image:
    def __init__(self, name, path, original=False):
        self.name = name
        self.path = Path(path)
        self.original = original
        self.blob = self.path.read_bytes()
        self.secs = score.sections(self.blob)
        self.funcs = [] if original else score.candidate_functions(self.path)
        self.fmap = {start: (size, win.demangle(symbol)) for start, size, symbol in self.funcs}
        if original:
            self.start, self.size = ORIGINAL_START, ORIGINAL_SIZE
            self.memcmp_targets = set()
            self.memcmp_body = None
        else:
            matches = [f for f in self.funcs if win.demangle(f[2]) == "pump_recovered::admin_cto::execute"]
            assert len(matches) == 1, (name, matches)
            self.start, self.size, _ = matches[0]
            memcmp = [f for f in self.funcs if win.demangle(f[2]) == "memcmp"]
            assert len(memcmp) == 1, (name, memcmp)
            self.memcmp_targets = {memcmp[0][0]}
            self.memcmp_body = score.body(self.blob, self.secs, memcmp[0][0], memcmp[0][1])
            assert memcmp[0][1] == 64
        self.raw = score.body(self.blob, self.secs, self.start, self.size)
        self.insns = win.insns(self.raw, self.start, self.secs)
        self.text = win.objdump_text(self.path, self.start, self.start + self.size)
        assert len(self.insns) == len(self.text), (name, len(self.insns), len(self.text))
        self.by_addr = {addr: (raw, norm, self.text.get(addr, "")) for addr, raw, norm in self.insns}

    def bind_original_memcmp(self, canonical):
        target = next(iter(canonical.memcmp_targets))
        wanted = score.normalize(canonical.memcmp_body, target, canonical.secs)
        matches = [w for w in score.original_windows() if w["bytes"] == len(canonical.memcmp_body) and w["norm"] == wanted]
        assert len(matches) == 1, [(hex(w["start"]), w["bytes"]) for w in matches]
        self.memcmp_targets = {matches[0]["start"]}
        self.memcmp_body = matches[0]["raw"]
        self.memcmp_binding = {
            "virtual_address": hex(matches[0]["start"]),
            "normalized_sha256": hashlib.sha256(matches[0]["norm"]).hexdigest(),
            "method": "unique original 64-byte window normalized-equal to canonical memcmp",
        }

    def data_at(self, value, length=32):
        for name, sec in self.secs.items():
            if sec["addr"] <= value and value + length <= sec["addr"] + sec["size"]:
                offset = sec["offset"] + value - sec["addr"]
                data = self.blob[offset:offset + length]
                return {"section": name, "address": hex(value), "hex": data.hex(),
                        "all_zero": not any(data)}
        return {"address": hex(value), "unmapped": True}

    def calls(self):
        result = []
        for addr, raw, _ in self.insns:
            op, regs, off, imm = struct.unpack_from("<BBhi", raw, 0)
            if op != 0x85:
                continue
            target = addr + 8 + imm * 8
            if target in self.memcmp_targets:
                result.append((addr, target))
        return result


original = Image("original", score.BASE / "original.so", True)
canonical = Image("canonical", SWARM / "baseline/canonical-unstripped.so")
natural = Image("natural_closure", RECOVERY / "validation-closure-boundary-out/unstripped.so")
original.bind_original_memcmp(canonical)
assert [len(image.calls()) for image in (original, canonical, natural)] == [14, 15, 16]


def is_terminator(text):
    op = text.split(None, 1)[0] if text else ""
    return op == "ja" or op.startswith("j") or op == "exit"


def constant_from_raw(raw):
    if raw[0] != 0x18:
        return None
    return struct.unpack_from("<I", raw, 4)[0] | (struct.unpack_from("<I", raw, 12)[0] << 32)


def context(image, addr, target):
    addrs = [a for a, _, _ in image.insns]
    index = addrs.index(addr)
    block = index
    while block > 0 and not is_terminator(image.text[addrs[block - 1]]):
        block -= 1
    lo = max(0, min(block, index - 24))
    hi = min(len(addrs), index + 7)
    rows = []
    for pos in range(lo, hi):
        a = addrs[pos]
        raw, _, text = image.by_addr[a]
        row = {"address": hex(a), "relative": hex(a - image.start), "text": text,
               "relation": "call" if pos == index else ("before" if pos < index else "after"),
               "same_block_setup": block <= pos < index}
        value = constant_from_raw(raw)
        if value is not None:
            row["lddw"] = hex(value)
            row["data32"] = image.data_at(value)
        rows.append(row)
    return {
        "call_offset": hex(addr - image.start),
        "call_address": hex(addr),
        "actual_target": hex(target),
        "target_symbol": image.fmap.get(target, (None, "memcmp"))[1],
        "block_start": hex(addrs[block]),
        "same_block_prefix_truncated": lo < block,
        "instructions": rows,
    }


report = {
    "schema": "cto-assembly-memcmp-context-v1",
    "scope": "Static actual call targets, same-block machine operand setup and mapped 32-byte ELF constants. No runtime or source-origin claim is made solely from a linear context.",
    "inputs": {image.name: {"path": str(image.path), "sha256": sha(image.path),
                            "execute_start": hex(image.start), "execute_bytes": image.size,
                            "memcmp_targets": [hex(x) for x in sorted(image.memcmp_targets)],
                            "memcmp_body_sha256": hashlib.sha256(image.memcmp_body).hexdigest(),
                            "memcmp_calls": len(image.calls())}
               for image in (original, canonical, natural)},
    "original_memcmp_binding": original.memcmp_binding,
    "images": {image.name: [context(image, addr, target) for addr, target in image.calls()]
               for image in (original, canonical, natural)},
    "limits": [
        "Original memcmp is rebound in the virtual-address domain by its unique normalized 64-byte original window; prior file-offset labels are not used as virtual addresses.",
        "Mapped constants identify bytes, not unique Rust expressions; all-zero Pubkey and System Program ID are byte-identical.",
        "A same-block setup slice does not trace callee sret writes or prove pointee values. Cross-block sources require separate CFG-sensitive analysis.",
    ],
}
(OUT / "memcmp-contexts.json").write_text(json.dumps(report, indent=2) + "\n")
with (OUT / "memcmp-contexts.txt").open("w") as stream:
    for image in (original, canonical, natural):
        stream.write(f"\n===== {image.name} execute={image.start:#x} calls={len(image.calls())} =====\n")
        for call in report["images"][image.name]:
            stream.write(f"\n--- memcmp {call['call_offset']} target={call['actual_target']} block={call['block_start']} ---\n")
            for row in call["instructions"]:
                extra = ""
                if "data32" in row:
                    extra = " ; data32=" + json.dumps(row["data32"], sort_keys=True)
                stream.write(f"{row['address']} {row['text']}{extra}\n")
print(json.dumps({"output": str(OUT / "memcmp-contexts.json"),
                  "counts": {name: len(rows) for name, rows in report["images"].items()},
                  "sha256": sha(OUT / "memcmp-contexts.json")}, indent=2))
