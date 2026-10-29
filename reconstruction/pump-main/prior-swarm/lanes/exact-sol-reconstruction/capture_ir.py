#!/usr/bin/env python3
"""Build the current lane source with retained optimized LLVM IR evidence."""
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

OUT = LANE / "outputs/scalar-optionbool-ir"
WORK = LANE / "ir-build"
real_run = subprocess.run


def emit_ir(command, *args, **kwargs):
    if isinstance(command, list) and len(command) > 1 and str(command[0]).endswith("/cargo") and command[1] == "build":
        command = command[:]
        command[1] = "rustc"
        command += ["--lib", "--", "--emit=link,llvm-ir"]
    return real_run(command, *args, **kwargs)


def extract_definitions(text, needle):
    return [match.group(0) + "\n" for match in re.finditer(r"^define[^\n]*" + needle + r"[^\n]*\{\n.*?^\}", text, re.M | re.S)]


def main():
    subprocess.run = emit_ir
    try:
        result = fastbuild.build(LANE / "source", WORK, OUT, recipe="identity")
    finally:
        subprocess.run = real_run
    result["root_only_additional_flags"] = ["--emit=link,llvm-ir"]
    result["source_diff"] = "lanes/exact-sol-reconstruction/outputs/wrapper-scalar-optionbool/source.patch"
    if result["ok"]:
        module_path = WORK / "target-identity/sbpf-solana-solana/release/deps/pump_recovered.ll"
        text = module_path.read_text()
        target = extract_definitions(text, r"14pump_recovered14pump_recovered16buy_exact_sol_in17")
        formatting = extract_definitions(text, r"with_values")
        if len(target) != 1:
            raise RuntimeError(f"expected one target IR definition, found {len(target)}")
        (OUT / "target.ll").write_text(target[0])
        (OUT / "with-values.ll").write_text("\n".join(formatting))
        result["full_module_sha256"] = hashlib.sha256(module_path.read_bytes()).hexdigest()
        result["target_ir_sha256"] = hashlib.sha256(target[0].encode()).hexdigest()
        result["with_values_definition_count"] = len(formatting)
        result["with_values_definitions_in_module_order"] = [line.strip() for line in text.splitlines() if line.startswith("define") and "with_values" in line]
        result["target_with_values_call_lines"] = [line.strip() for line in target[0].splitlines() if "with_values" in line]
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
