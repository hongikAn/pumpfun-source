"""Replay the recorded offline native SBPF build with explicit local mounts.

Requires the captured Linux v1.44 SDK/image and already populated Cargo inputs.
No downloads or installation are performed. Run in Linux/WSL with Docker.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
for arg in ('source', 'sdk', 'cargo-home', 'target-dir', 'output'):
    p.add_argument('--' + arg, type=Path, required=True)
a = p.parse_args()
launch = json.loads((HERE / 'builds/candidate/launch.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert {p.relative_to(a.source).as_posix(): sha(p) for p in a.source.rglob('*') if p.is_file()} == launch['inputs']
for name, relative in [('rustc', 'rust/bin/rustc'), ('cargo', 'rust/bin/cargo'), ('objcopy', 'llvm/bin/llvm-objcopy')]:
    assert sha(a.sdk / relative) == launch['tools'][name], name
cmd = list(launch['command'])
mounts = [i + 1 for i, x in enumerate(cmd) if x == '-v']
assert len(mounts) == 4
for i, directory in zip(mounts, (a.source, a.sdk, a.cargo_home, a.target_dir)):
    _, destination, mode = cmd[i].split(':')
    cmd[i] = str(directory.resolve()) + ':' + destination + ':' + mode
a.output.mkdir(parents=True, exist_ok=False)
os.utime(a.source / 'programs/pump-amm/src/lib.rs', None)
os.utime(a.source / 'crates/native-transfer-fee/src/lib.rs', None)
(a.output / 'command.json').write_text(json.dumps(cmd, indent=2) + '\n')
with (a.output / 'build.log').open('wb') as log:
    result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
result.check_returncode()
log = (a.output / 'build.log').read_text()
assert sum(line.strip().startswith('Running `') and '--crate-name pump_amm_recovered ' in line for line in log.splitlines()) == 1
assert sum(line.strip().startswith('Running `') and '--crate-name native_transfer_fee ' in line for line in log.splitlines()) == 1
shutil.copyfile(a.target_dir / 'sbpf-solana-solana/release/pump_amm_recovered.so', a.output / 'symbols.so')
subprocess.run([str(a.sdk / 'llvm/bin/llvm-objcopy'), '--strip-all', str(a.output / 'symbols.so'), str(a.output / 'candidate.so')], check=True)
hashes = {kind + '_sha256': sha(a.output / (kind + '.so')) for kind in ('symbols', 'candidate')}
(a.output / 'hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
expected = json.loads((HERE / 'builds/candidate/result.json').read_text())
assert all(expected[k] == v for k, v in hashes.items()), hashes
print(json.dumps(hashes))
