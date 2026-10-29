#!/usr/bin/env python3
"""Build one source tree while capturing only trade::buy pass dumps."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
SWARM = LANE.parent.parent
sys.path.insert(0, str(SWARM / "tools/harness"))
import fastbuild  # noqa: E402

SYMBOL = "_ZN14pump_recovered5trade3buy17h040b74ddebd76776E"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mir-dir", type=Path, required=True)
    parser.add_argument("--reuse", action="store_true", help="only rebuild manifests from existing artifacts")
    args = parser.parse_args()
    args.mir_dir.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=True)
    real_run = subprocess.run
    llvm_args = [
        "-filter-print-funcs=" + SYMBOL,
        "-print-before=codegenprepare",
        "-print-after=codegenprepare",
        "-print-after=finalize-isel",
        "-print-before=machine-sink",
        "-print-after=machine-sink",
        "-print-after=block-placement",
    ]
    extra = [
        "--emit=link,llvm-ir",
        "-Zdump-mir=trade::buy",
        "-Zdump-mir-dir=" + str(args.mir_dir.resolve()),
        "-Zdump-mir-exclude-pass-number",
    ] + [item for value in llvm_args for item in ("-C", "llvm-args=" + value)]

    if args.reuse:
        required = [args.out / "unstripped.so", args.out / "candidate.so", args.out / "build.log"]
        if not all(path.exists() for path in required):
            raise SystemExit("cannot reuse incomplete capture output")
        result = {
            "ok": True,
            "recipe": "identity",
            "reuse_existing_build": True,
            "unstripped_sha256": sha(args.out / "unstripped.so"),
            "candidate_sha256": sha(args.out / "candidate.so"),
        }
    else:
        def run(cmd, *run_args, **kwargs):
            if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith("/cargo") and cmd[1] == "build":
                cmd = cmd[:]
                cmd[1] = "rustc"
                cmd += ["--lib", "--"] + extra
            return real_run(cmd, *run_args, **kwargs)

        subprocess.run = run
        try:
            result = fastbuild.build(args.src, args.work, args.out, recipe="identity")
        finally:
            subprocess.run = real_run
    result["source"] = str(args.src)
    result["root_only_additional_flags"] = extra
    result["pass_dumps"] = []
    log_path = args.out / "build.log"
    if log_path.exists():
        text = log_path.read_text(errors="replace")
        chunks = re.split(r"(?=\*\*\* IR Dump )", text)
        for index, chunk in enumerate(chunks):
            if not chunk.startswith("*** IR Dump "):
                continue
            heading = chunk.splitlines()[0]
            stage = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")[:120]
            dump_path = args.out / f"dump-{index:02d}-{stage}.txt"
            dump_path.write_text(chunk)
            result["pass_dumps"].append({
                "file": dump_path.name,
                "heading": heading,
                "bytes": dump_path.stat().st_size,
                "sha256": sha(dump_path),
            })
    module = args.work / "target-identity/sbpf-solana-solana/release/deps/pump_recovered.ll"
    if module.exists():
        text = module.read_text()
        match = re.search(r"^define[^\n]*" + re.escape(SYMBOL) + r"[^\n]*\n.*?^\}", text, re.M | re.S)
        if not match:
            raise SystemExit("trade::buy definition not found in final LLVM module")
        final_path = args.out / "trade-buy-final.ll"
        final_path.write_text(match.group(0) + "\n")
        result["final_llvm_ir"] = {"file": final_path.name, "sha256": sha(final_path)}
        result["full_module_sha256"] = sha(module)
    mir_files = sorted(p for p in args.mir_dir.resolve().rglob("*") if p.is_file())
    result["mir_files"] = [{"path": str(p.relative_to(LANE)), "sha256": sha(p)} for p in mir_files]
    (args.out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
