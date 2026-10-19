"""Collect per-N metrics from flow/runs/RUN_N_<N> into results/metrics.csv and
compare them against Table III of the paper. Run from the repository root after
flow/sweep_n.py."""
import csv
import json
import os
import re

RUNS = "flow/runs"
OUT = "results/metrics.csv"
IO_DELAY = 4.0  # IO_DELAY_CONSTRAINT 20% of 20 ns (checked in resolved.json below)
PAPER = {4: (7287.51, 298, 6.52, 0.115), 5: (9181.51, 396, 5.16, 0.158),
         6: (10447.80, 456, 4.61, 0.197), 7: (11980.10, 537, 4.47, 0.260),
         8: (13939.00, 631, 3.71, 0.300), 9: (15295.20, 709, 3.46, 0.319),
         10: (16127.00, 752, 2.28, 0.363)}


def arrival(rpt):
    return float(re.search(r"([0-9.]+)\s+data arrival time", open(rpt).read()).group(1))


def total_power_mw(rpt):
    m = re.search(r"^Total\s+\S+\s+\S+\s+\S+\s+(\S+)", open(rpt).read(), re.M)
    return float(m.group(1)) * 1e3


rows = []
for n in range(4, 11):
    R = f"{RUNS}/RUN_N_{n}"
    cfg = json.load(open(f"{R}/resolved.json"))
    assert cfg["CLOCK_PERIOD"] == 20 and cfg["IO_DELAY_CONSTRAINT"] == 20, n
    m = json.load(open(f"{R}/final/metrics.json"))
    sta = f"{R}/" + [d for d in os.listdir(R) if "stapostpnr" in d][0]
    ws = {k.split(":")[1]: v for k, v in m.items() if k.startswith("timing__setup__ws__corner:")}
    pw = {c: total_power_mw(f"{sta}/{c}/power.rpt") for c in os.listdir(sta)
          if os.path.isfile(f"{sta}/{c}/power.rpt")}
    r = dict(
        N=n,
        die_area_um2=m["design__die__area"],
        cell_area_um2=round(m["design__instance__area"], 2),
        cells=m["design__instance__count"],
        setup_ws_worst_ns=round(m["timing__setup__ws"], 2),
        ws_worst_corner=min(ws, key=ws.get),
        delay_nom_tt_ns=round(arrival(f"{sta}/nom_tt_025C_1v80/max.rpt") - IO_DELAY, 2),
        delay_worst_ns=round(arrival(f"{sta}/{min(ws, key=ws.get)}/max.rpt") - IO_DELAY, 2),
        power_max_mW=round(m["power__total"] * 1e3, 3),
        power_max_corner=max(pw, key=pw.get),
        power_nom_tt_mW=round(pw["nom_tt_025C_1v80"], 3),
    )
    p = PAPER[n]
    r["matches_table3"] = (abs(r["die_area_um2"] - p[0]) < 0.01 and r["cells"] == p[1]
                           and abs(r["setup_ws_worst_ns"] - p[2]) < 0.006
                           and abs(r["power_max_mW"] - p[3]) < 0.0006)
    rows.append(r)
    print(r)

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print("ALL MATCH TABLE III" if all(r["matches_table3"] for r in rows) else "SOME ROWS DIFFER FROM TABLE III")
