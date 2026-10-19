"""Write golden test vectors for tb_forward_converter.sv.

One file per n: vectors/vec_n<N>.hex, one $readmemh word per line, packed as
    {x[3n-1:0], r_m1[n-1:0], r_0[n-1:0], r_1[n:0]}   (6n+1 bits)
Exhaustive over the full 3n-bit word for n <= EXHAUSTIVE_MAX_N; otherwise the
edge set from ref_model.edge_values plus N_RANDOM seeded random inputs.
vectors/vec_n<N>.count holds the number of vectors.
"""
import os
import random
import sys

from ref_model import edge_values, golden, word_range

EXHAUSTIVE_MAX_N = 7
N_RANDOM = 1_000_000
SEED = 2026


def pack(x, n):
    rm1, r0, rp1 = golden(x, n)
    u = x & ((1 << (3 * n)) - 1)
    return (((u << n | rm1) << n | r0) << (n + 1)) | rp1


def main(ns):
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "vectors")
    os.makedirs(out, exist_ok=True)
    for n in ns:
        lo, hi = word_range(n)
        if n <= EXHAUSTIVE_MAX_N:
            xs, kind = range(lo, hi + 1), "exhaustive"
        else:
            rng = random.Random(SEED + n)
            xs = edge_values(n) + [rng.randint(lo, hi) for _ in range(N_RANDOM)]
            kind = "edge+random"
        digits = (6 * n + 1 + 3) // 4
        cnt = 0
        with open(os.path.join(out, f"vec_n{n}.hex"), "w", newline="\n") as f:
            for x in xs:
                f.write(f"{pack(x, n):0{digits}x}\n")
                cnt += 1
        with open(os.path.join(out, f"vec_n{n}.count"), "w", newline="\n") as f:
            f.write(f"{cnt}\n")
        print(f"n={n:2d} {kind:11s} vectors={cnt:,}")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(range(4, 11)))
