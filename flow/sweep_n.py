"""Run the OpenLane 2 flow for N = 4..10 (the sweep reported in the paper).

Uses config.json in this folder as the base and overrides only N.
Usage (from this folder):
    python sweep_n.py              # all N in 4..10
    python sweep_n.py 4 8          # selected N
    python sweep_n.py --dockerized # extra args are passed to openlane
Results land in runs/RUN_N_<N>/ (see final/metrics.json for area, power, timing).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ns = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(range(4, 11))
extra = [a for a in sys.argv[1:] if not a.isdigit()]

with open(os.path.join(HERE, "config.json")) as f:
    base = json.load(f)

failed = []
for n in ns:
    print(f"\n--- Starting run for N = {n} ---")
    config = dict(base, SYNTH_PARAMETERS=[f"N={n}"])
    # Temp config sits next to config.json so dir:: paths resolve the same way.
    temp_config = os.path.join(HERE, f"config_N{n}.json")
    with open(temp_config, "w") as f:
        json.dump(config, f, indent=4)
    try:
        subprocess.run(["openlane", *extra, temp_config, "--run-tag", f"RUN_N_{n}"],
                       check=True, cwd=HERE)
    except subprocess.CalledProcessError as e:
        print(f"Error during run N={n}: {e}")
        failed.append(n)
    finally:
        os.remove(temp_config)

sys.exit(1 if failed else 0)
