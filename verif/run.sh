#!/usr/bin/env bash
# Build and run tb_forward_converter for n=4..10 with Verilator.
# Run inside a container from the repository root, e.g. (Git Bash on Windows):
#   MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W)":/work -w /work/verif \
#       --entrypoint bash verilator/verilator:v5.028 run.sh
set -u
cd "$(dirname "$0")"
RTL=../rtl/forward_converter.sv
NS=${NS:-"4 5 6 7 8 9 10"}
OUT=results.txt
verilator --version | tee "$OUT"
echo "RTL: $RTL  sha256: $(sha256sum "$RTL" | cut -d' ' -f1)" | tee -a "$OUT"
status=0
for n in $NS; do
    obj=build/obj_n$n
    rm -rf "$obj"
    verilator --binary --timing -Wno-fatal -Wno-WIDTH -GN=$n \
        --top-module tb_forward_converter -Mdir "$obj" -o sim \
        "$RTL" tb_forward_converter.sv > "build_n$n.log" 2>&1 \
        || { echo "N=$n BUILD FAILED (see build_n$n.log)" | tee -a "$OUT"; status=1; continue; }
    "$obj/sim" +VEC=vectors/vec_n$n.hex +NVEC=$(cat vectors/vec_n$n.count) | tee -a "$OUT"
    grep -q "RESULT N=$n .* PASS" "$OUT" || status=1
done
echo "OVERALL: $([ $status -eq 0 ] && echo PASS || echo FAIL)" | tee -a "$OUT"
exit $status
