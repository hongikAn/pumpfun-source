#!/usr/bin/env python3
"""Capture target-filtered SelectionDAG, register-allocation, and scheduler evidence."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
SWARM = LANE.parents[1]
sys.path.insert(0, str(SWARM / "tools/harness"))
import fastbuild  # noqa: E402

OUT = LANE / "outputs/scalar-optionbool-backend"
WORK = LANE / "backend-build"
SYMBOL = "_ZN14pump_recovered14pump_recovered16buy_exact_sol_in17h49bc4356a9e68eb0E"
WITH_VALUES = "_ZN11anchor_lang5error5Error11with_values17h17a91ba7c0882e46E"
real_run = subprocess.run


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capture_passes(command, *args, **kwargs):
    if isinstance(command, list) and len(command) > 1 and str(command[0]).endswith("/cargo") and command[1] == "build":
        llvm_args = [
            "-filter-print-funcs=" + SYMBOL,
            "-print-after=finalize-isel",
            "-print-before=machine-scheduler",
            "-print-after=machine-scheduler",
            "-print-after=greedy",
            "-print-before=post-RA-sched",
            "-print-after=post-RA-sched",
            "-print-after=block-placement",
        ]
        extra = ["--emit=link,llvm-ir"] + [item for value in llvm_args for item in ("-C", "llvm-args=" + value)]
        command = command[:]
        command[1] = "rustc"
        command += ["--lib", "--"] + extra
    return real_run(command, *args, **kwargs)


def machine_blocks(text):
    headers = list(re.finditer(r"(?m)^bb\.\d+[^:\n]*:\n", text))
    blocks = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        body = text[header.start():end]
        body = body.split("\n# End machine code for function", 1)[0]
        if WITH_VALUES in body:
            blocks.append(body.rstrip() + "\n")
    return blocks


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run = capture_passes
    try:
        result = fastbuild.build(LANE / "source", WORK, OUT, recipe="identity")
    finally:
        subprocess.run = real_run
    result["root_only_additional_flags"] = [
        "--emit=link,llvm-ir",
        "-filter-print-funcs=" + SYMBOL,
        "-print-after=finalize-isel",
        "-print-before=machine-scheduler",
        "-print-after=machine-scheduler",
        "-print-after=greedy",
        "-print-before=post-RA-sched",
        "-print-after=post-RA-sched",
        "-print-after=block-placement",
    ]
    result["filter_symbol"] = SYMBOL
    result["pass_dumps"] = []
    blocks_by_dump = []
    if result.get("ok"):
        text = (OUT / "build.log").read_text(errors="replace")
        chunks = re.split(r"(?=\*\*\* IR Dump )", text)
        for index, chunk in enumerate(chunks):
            if not chunk.startswith("*** IR Dump "):
                continue
            heading = chunk.splitlines()[0]
            stage = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")[:120]
            dump_path = OUT / f"dump-{index:02d}-{stage}.txt"
            dump_path.write_text(chunk)
            result["pass_dumps"].append({
                "file": dump_path.name,
                "heading": heading,
                "bytes": dump_path.stat().st_size,
                "sha256": sha(dump_path),
            })
            blocks = machine_blocks(chunk)
            blocks_by_dump.append({"file": dump_path.name, "heading": heading, "with_values_blocks": blocks})
        (OUT / "with-values-machine-blocks.json").write_text(json.dumps(blocks_by_dump, indent=2) + "\n")
        module = WORK / "target-identity/sbpf-solana-solana/release/deps/pump_recovered.ll"
        if module.exists():
            result["full_module_sha256"] = sha(module)
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "pass_dumps"}, indent=2))
    print(json.dumps({"pass_dumps": result["pass_dumps"]}, indent=2))
    raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
