# Signed Bit-Slicing Forward Converter for RNS {2^n−1, 2^n, 2^n+1}

Source code, physical-design flow and verification for the paper

> K. O. Boateng, B. E. Krapah and J. O. Sarfoh, "A Bit-Slicing Forward Converter for Signed Integers in the Residue Number System with Moduli Set {2^n−1, 2^n, 2^n+1}," Kwame Nkrumah University of Science and Technology (KNUST), 2026.

The converter maps a signed 3n-bit two's complement integer N to its residues
(r₋₁, r₀, r₁) = (|N|₂ⁿ₋₁, |N|₂ⁿ, |N|₂ⁿ₊₁) with no separate sign-extension or offset stage.

## How it works

N is split into three n-bit segments, N = 2²ⁿN₂ + 2ⁿN₁ + N₀, where N₀ and N₁ are unsigned and N₂ (the top segment) is read as **signed**.

| Channel | Computation | Correction |
|---|---|---|
| 2ⁿ | r₀ = N₀ | none (wiring) |
| 2ⁿ−1 | S = N₂ + N₁ + N₀ | add 2ⁿ−1, none, subtract 2ⁿ−1, or subtract 2(2ⁿ−1), chosen by the range of S |
| 2ⁿ+1 | T = N₂ − N₁ + N₀ | add 2(2ⁿ+1), add 2ⁿ+1, none, or subtract 2ⁿ+1, chosen by the range of T |

**Unique range.** The dynamic range is M = 2³ⁿ − 2ⁿ. The circuit returns the correct residues for every 3n-bit input, but the residue triplet is unique only on [−M/2, M/2−1]. The 2ⁿ extreme words outside that range (2ⁿ⁻¹ at each end) share a triplet with N ± M.

The partition and folding identities are the standard ones (Vinnakota & Rao, 1994; Krstić et al., 2016), which were given for unsigned inputs. What this design adds is the signed treatment of N₂.

## Repository layout

```
rtl/forward_converter.sv   parameterised SystemVerilog (parameter N = n)
flow/config.json           OpenLane 2 configuration used for the paper
flow/sweep_n.py            runs the flow for N = 4..10
verif/ref_model.py         Python reference model and property checks
verif/gen_vectors.py       writes golden test vectors
verif/tb_forward_converter.sv  self-checking testbench
verif/run.sh               Verilator regression for N = 4..10
```

## Implementation results

OpenLane 2, SkyWater sky130A, `SYNTH_STRATEGY = DELAY 0`, 20 ns (50 MHz) virtual-clock constraint (the design is purely combinational).

| N | Input bits | Area (µm²) | Cells | Setup slack (ns) | Power (mW) |
|---|---|---|---|---|---|
| 4 | 12 | 7287.51 | 298 | 6.52 | 0.115 |
| 5 | 15 | 9181.51 | 396 | 5.16 | 0.158 |
| 6 | 18 | 10447.80 | 456 | 4.61 | 0.197 |
| 7 | 21 | 11980.10 | 537 | 4.47 | 0.260 |
| 8 | 24 | 13939.00 | 631 | 3.71 | 0.300 |
| 9 | 27 | 15295.20 | 709 | 3.46 | 0.319 |
| 10 | 30 | 16127.00 | 752 | 2.28 | 0.363 |

## Reproducing

**Physical design** (needs [OpenLane 2](https://github.com/efabless/openlane2)):
```bash
cd flow
python sweep_n.py            # add --dockerized to run OpenLane inside its container
```
Metrics for each N are written to `flow/runs/RUN_N_<N>/final/metrics.json`.

**Functional verification** (needs Python 3 and Docker):
```bash
python verif/ref_model.py     # algorithm vs. Python %, range and uniqueness checks
python verif/gen_vectors.py   # writes verif/vectors/
docker run --rm -v "$PWD":/work -w /work/verif --entrypoint bash verilator/verilator:v5.028 run.sh
```
Coverage:
- RTL: exhaustive over every 3n-bit input for N = 4..8. For N = 9 and 10, a directed edge set plus 10⁶ seeded random inputs.
- Edge set: both ends of the word, ±M/2, and every correction boundary of S and T.
- Reference model: exhaustive for N ≤ 8; uniqueness on [−M/2, M/2−1] checked exhaustively for N ≤ 7; aliasing of all 2ⁿ excluded extremes checked for every N.

## Citation

See `CITATION.cff`. Until the paper is published, cite this repository.

## License

Copyright 2026 Kwame Osei Boateng, Bless Elikem Krapah, Jesse Osei Sarfoh (KNUST).
Licensed under the Apache License, Version 2.0. See `LICENSE`.
