from pathlib import Path
import subprocess,json,datetime
R=Path('/mnt/c/Users/ahi20/Documents/ChatGPT/pumpfun-source');P=Path('/mnt/c/Users/ahi20/Documents/ChatGPT/pumpfun-contribution-review/amm-inverse-arithmetic-20261028');D=Path('/home/ahi200/pumpfun-work/20261028-amm-inverse-arithmetic');commands=[]
for family in ['liquidity','buy','sell']:
 cmd=['/home/ahi200/pumpfun-work/20261027-fidelity/runtime-venv/bin/python',str(R/'repro/pump_amm/owner6048-v144/runtime/observe_suite.py'),str(D/('fee-'+family+'-observed.json.gz')),str(P/'inverse_runtime.py'),family];commands.append(cmd);(D/'fee-runtime-commands.json').write_text(json.dumps(commands,indent=2)+'\n');r=subprocess.run(cmd,cwd=R);r.check_returncode()
