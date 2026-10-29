#!/usr/bin/env python3
"""Concurrency-safe append-only attempt ledger for the main-Pump swarm."""
import argparse
import datetime as dt
import fcntl
import hashlib
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "ATTEMPTS.jsonl"
LOCK = ROOT / ".attempts.lock"


def read_rows():
    if not LOG.exists():
        return []
    rows = []
    for number, line in enumerate(LOG.read_text().splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"corrupt ledger line {number}: {exc}")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--dedupe-key", required=True)
    record = sub.add_parser("record")
    record.add_argument("--lane", required=True)
    record.add_argument("--approach", required=True)
    record.add_argument("--target", required=True)
    record.add_argument("--dedupe-key", required=True)
    record.add_argument("--hypothesis", required=True)
    record.add_argument("--status", required=True, choices=["analyzed", "built", "compile-failed", "rejected", "partial", "normalized-match", "raw-match"])
    record.add_argument("--data", default="{}", help="JSON object with evidence paths, hashes, metrics, and notes")
    args = parser.parse_args()
    data = json.loads(args.data) if args.command == "record" else None
    if data is not None and not isinstance(data, dict):
        raise SystemExit("--data must be a JSON object")
    LOCK.touch(exist_ok=True)
    with LOCK.open("r+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        rows = read_rows()
        duplicates = [r for r in rows if r.get("dedupe_key") == args.dedupe_key]
        if args.command == "check":
            print(json.dumps({"dedupe_key": args.dedupe_key, "duplicate": bool(duplicates), "attempt_ids": [r.get("attempt_id") for r in duplicates]}))
            return
        if duplicates:
            raise SystemExit(f"duplicate dedupe key: {args.dedupe_key}; attempt already logged")
        row = {
            "schema": "main-pump-attempt-v1",
            "attempt_id": uuid.uuid4().hex,
            "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "lane": args.lane,
            "approach": args.approach,
            "target": args.target,
            "dedupe_key": args.dedupe_key,
            "hypothesis": args.hypothesis,
            "status": args.status,
            "data": data,
        }
        line = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        with LOG.open("a") as output:
            output.write(line)
            output.flush()
        row["ledger_sha256"] = hashlib.sha256(LOG.read_bytes()).hexdigest()
        print(json.dumps({"recorded": True, "attempt_id": row["attempt_id"], "attempts": len(rows) + 1, "ledger_sha256": row["ledger_sha256"]}))


if __name__ == "__main__":
    main()
