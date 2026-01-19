import os
import json
import subprocess

n_values = range(4, 11)

for n in n_values:
    print(f"\n--- Starting Run for N = {n} ---")
    
    config = {
        "DESIGN_NAME": "forward_converter",
        "VERILOG_FILES": ["dir::src/forward_converter.sv"],
        "SYNTH_PARAMETERS": [f"N={n}"],
        "CLOCK_PERIOD": 20.0,             # Relaxed for N=10 critical paths
        "SYNTH_STRATEGY": "DELAY 0",
        "FP_SIZING": "relative",          # Area now grows with design size
        "FP_CORE_UTIL": 40,               # Target 40% cell utilization
        "PL_TARGET_DENSITY_PCT": 55,      # Higher density to avoid GPL-0302
        "RUN_POST_CTS_RESIZER_TIMING": True,
        "RUN_STP": True,
        "RUN_IRDROP_REPORT": True
    }
    
    temp_config = f"config_N{n}.json"
    with open(temp_config, "w") as f:
        json.dump(config, f, indent=4)
    
    try:
        subprocess.run([
            "openlane", 
            temp_config, 
            "--run-tag", f"RUN_N_{n}"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during run N={n}: {e}")
    finally:
        if os.path.exists(temp_config):
            os.remove(temp_config)
