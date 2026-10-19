"""Reference model for the signed forward converter, moduli {2^n-1, 2^n, 2^n+1}.

Two independent models:
  golden(x, n)  : residues via Python's % (always non-negative for positive modulus)
  sliced(x, n)  : the paper's bit-slicing algorithm with the corrections of Tables I/II

Run directly to check, for each n:
  1. sliced == golden for every tested input (exhaustive for small n)
  2. S and T stay inside the ranges the correction tables assume
  3. residue triplets are unique on the balanced range [-M/2, M/2-1]
  4. every 3n-bit input outside that range aliases with exactly x + M or x - M
"""
import random
import sys


def moduli(n):
    return (1 << n) - 1, 1 << n, (1 << n) + 1


def dyn_range(n):
    m1, m0, p1 = moduli(n)
    return m1 * m0 * p1


def word_range(n):
    """Full 3n-bit two's complement range, inclusive."""
    return -(1 << (3 * n - 1)), (1 << (3 * n - 1)) - 1


def balanced_range(n):
    """Range over which the residue triplet is unique, inclusive."""
    M = dyn_range(n)
    return -(M // 2), M // 2 - 1


def golden(x, n):
    m1, m0, p1 = moduli(n)
    return x % m1, x % m0, x % p1  # (r_-1, r_0, r_1)


def slices(x, n):
    mask = (1 << n) - 1
    u = x & ((1 << (3 * n)) - 1)  # 3n-bit two's complement pattern
    n0 = u & mask
    n1 = (u >> n) & mask
    n2 = (u >> (2 * n)) & mask
    if n2 >> (n - 1):
        n2 -= 1 << n  # signed high segment
    return n2, n1, n0


def sliced(x, n, trace=None):
    m1, _, p1 = moduli(n)
    n2, n1, n0 = slices(x, n)

    r0 = n0

    S = n2 + n1 + n0  # Table I
    if S < 0:
        rm1 = S + m1
    elif S < m1:
        rm1 = S
    elif S < 2 * m1:
        rm1 = S - m1
    else:
        rm1 = S - 2 * m1

    T = n2 - n1 + n0  # Table II
    if T < -p1:
        rp1 = T + 2 * p1
    elif T < 0:
        rp1 = T + p1
    elif T < p1:
        rp1 = T
    else:
        rp1 = T - p1

    if trace is not None:
        trace.append((S, T))
    return rm1, r0, rp1


def inputs_for(n, exhaustive_max_n, n_random, rng):
    lo, hi = word_range(n)
    if n <= exhaustive_max_n:
        return range(lo, hi + 1), True
    xs = set(edge_values(n))
    xs.update(rng.randint(lo, hi) for _ in range(n_random))
    return sorted(xs), False


def edge_values(n):
    """Inputs at range ends and at every correction boundary of Tables I/II."""
    lo, hi = word_range(n)
    blo, bhi = balanced_range(n)
    m1, _, p1 = moduli(n)
    mask = (1 << n) - 1
    xs = {0, 1, -1, 2, -2, lo, lo + 1, hi, hi - 1,
          blo, blo - 1, blo + 1, bhi, bhi + 1, bhi - 1}

    def compose(n2, n1, n0):
        return (n2 << (2 * n)) + (n1 << n) + n0

    n2_vals = [-(1 << (n - 1)), -1, 0, 1, (1 << (n - 1)) - 1]
    seg_vals = [0, 1, mask - 1, mask]
    for n2 in n2_vals:
        for n1 in seg_vals:
            for n0 in seg_vals:
                xs.add(compose(n2, n1, n0))
    # Hit S and T exactly at, below and above each table boundary.
    s_targets = [-1, 0, m1 - 1, m1, 2 * m1 - 1, 2 * m1]
    t_targets = [-p1 - 1, -p1, -1, 0, p1 - 1, p1]
    for n2 in range(-(1 << (n - 1)), 1 << (n - 1)):
        for n1 in seg_vals + [mask // 2]:
            for s in s_targets:
                n0 = s - n2 - n1
                if 0 <= n0 <= mask:
                    xs.add(compose(n2, n1, n0))
            for t in t_targets:
                n0 = t - n2 + n1
                if 0 <= n0 <= mask:
                    xs.add(compose(n2, n1, n0))
    return sorted(x for x in xs if lo <= x <= hi)


def check(n, exhaustive_max_n=8, uniq_max_n=7, n_random=200_000, seed=2026):
    rng = random.Random(seed + n)
    m1, _, p1 = moduli(n)
    M = dyn_range(n)
    lo, hi = word_range(n)
    blo, bhi = balanced_range(n)
    xs, exhaustive = inputs_for(n, exhaustive_max_n, n_random, rng)

    mismatches, count = 0, 0
    s_min = t_min = 10**9
    s_max = t_max = -10**9
    for x in xs:
        tr = []
        if sliced(x, n, tr) != golden(x, n):
            mismatches += 1
            if mismatches <= 5:
                print(f"  MISMATCH n={n} x={x}: sliced={sliced(x, n)} golden={golden(x, n)}")
        S, T = tr[0]
        s_min, s_max = min(s_min, S), max(s_max, S)
        t_min, t_max = min(t_min, T), max(t_max, T)
        count += 1

    # Analytic bounds of S and T, and whether a single table correction suffices.
    s_lo_a, s_hi_a = -(1 << (n - 1)), (1 << (n - 1)) - 1 + 2 * ((1 << n) - 1)
    t_lo_a, t_hi_a = -(1 << (n - 1)) - ((1 << n) - 1), (1 << (n - 1)) - 1 + ((1 << n) - 1)
    bounds_ok = (s_lo_a >= -m1 and s_hi_a < 3 * m1 and t_lo_a >= -2 * p1 and t_hi_a < 2 * p1)
    if exhaustive:
        bounds_ok &= (s_min, s_max, t_min, t_max) == (s_lo_a, s_hi_a, t_lo_a, t_hi_a)

    # Uniqueness on the balanced range, and aliasing of the excluded extremes.
    uniq = None
    if n <= uniq_max_n:
        seen = {}
        dup = 0
        for x in range(blo, bhi + 1):
            key = golden(x, n)
            if key in seen:
                dup += 1
            seen[key] = x
        uniq = dup == 0 and len(seen) == M
    excluded = list(range(lo, blo)) + list(range(bhi + 1, hi + 1))
    alias_ok = len(excluded) == (1 << n)
    for x in excluded:
        partner = x + M if x < blo else x - M
        alias_ok &= blo <= partner <= bhi and golden(x, n) == golden(partner, n) \
            and sliced(x, n) == golden(partner, n)

    ok = mismatches == 0 and bounds_ok and alias_ok and uniq in (True, None)
    print(f"n={n:2d} {'exhaustive' if exhaustive else 'edge+random'} inputs={count:>9,} "
          f"mismatches={mismatches} S=[{s_min},{s_max}] T=[{t_min},{t_max}] "
          f"bounds={'ok' if bounds_ok else 'FAIL'} "
          f"unique={'ok' if uniq else ('n/a' if uniq is None else 'FAIL')} "
          f"excluded={len(excluded)} alias={'ok' if alias_ok else 'FAIL'} "
          f"-> {'PASS' if ok else 'FAIL'}")
    return ok


def worked_examples():
    """The two examples printed in the paper (n=4)."""
    assert sliced(-1234, 4) == golden(-1234, 4) == (11, 14, 7)
    assert sliced(1234, 4) == golden(1234, 4) == (4, 2, 10)
    print("worked examples (n=4, N=+-1234): ok")


if __name__ == "__main__":
    ns = [int(a) for a in sys.argv[1:]] or list(range(4, 11))
    worked_examples()
    results = [check(n) for n in ns]
    print("ALL PASS" if all(results) else "FAILURES PRESENT")
    sys.exit(0 if all(results) else 1)
