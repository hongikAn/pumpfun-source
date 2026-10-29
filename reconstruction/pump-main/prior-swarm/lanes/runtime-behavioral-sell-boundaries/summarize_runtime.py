#!/usr/bin/env python3
"""Compact offline runtime receipts into ordered, source-relevant JSONL evidence."""
import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path


def load(path):
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def case_name(case, index):
    value = case.get("case", case.get("name", index))
    if isinstance(value, dict):
        return value.get("name", value.get("id", index)), value.get("kind")
    return value, case.get("kind")


def outcome(case, side):
    value = case.get(side)
    if isinstance(value, dict) and any(k in value for k in ("error", "logs", "inner", "return_data")):
        return value
    result = case.get("result")
    if isinstance(result, dict):
        value = result.get(side, result)
        if isinstance(value, dict):
            return value
    return case if any(k in case for k in ("error", "logs", "inner", "return_data")) else {}


def relevant_log(line):
    return (
        "Program invoke:" in line
        or "Instruction:" in line
        or "Program data:" in line
        or "Program log:" in line
        or " failed:" in line
        or "failed:" in line
        or "Program return:" in line
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--side", default="original", choices=["original", "candidate"])
    parser.add_argument("--case", dest="case_re")
    args = parser.parse_args()
    matcher = re.compile(args.case_re) if args.case_re else None
    rows = []
    for path in args.inputs:
        document, decompressed_sha256 = load(path)
        cases = document.get("cases", []) if isinstance(document, dict) else document
        if not isinstance(cases, list):
            raise SystemExit(f"{path}: no case list")
        for index, case in enumerate(cases):
            if not isinstance(case, dict):
                continue
            name, kind = case_name(case, index)
            if matcher and not matcher.search(str(name)):
                continue
            observed = outcome(case, args.side)
            logs = observed.get("logs") or []
            rows.append({
                "source": str(path),
                "source_decompressed_sha256": decompressed_sha256,
                "case_index": index,
                "case": name,
                "kind": kind,
                "match": case.get("match"),
                "different_fields": case.get("different_fields"),
                "error": observed.get("error"),
                "ordered_program_messages": [line for line in logs if isinstance(line, str) and relevant_log(line)],
                "inner_cpi_sequence": observed.get("inner"),
                "return_data": observed.get("return_data"),
                "events": observed.get("events"),
            })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"output": str(args.output), "cases": len(rows), "inputs": len(args.inputs)}))


if __name__ == "__main__":
    main()
