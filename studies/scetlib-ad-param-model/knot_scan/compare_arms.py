#!/usr/bin/env python3
"""A/B table of two validate_variations runs that differ ONLY in the muF knots.

validate_variations prints one row per variation:
    <label> <max|dev|> <mean|dev|> [model range] [template range] <worst qT bin>
so both arms can be parsed from their logs and put side by side. The ratio
column is what decides the question: a 3-point quadratic's error at a fixed
displacement scales as ln(f)^2, so going 2 -> sqrt(2) must divide an
interpolation-limited residual by about 4. A residual that does not move is not
interpolation error.
"""
import re
import sys

ROW = re.compile(
    r"^(\S+)\s+([0-9.]+e[-+]\d+)\s+([0-9.]+e[-+]\d+)\s+"
    r"\[([-0-9.]+),([-0-9.]+)\]\s+\[([-0-9.]+),([-0-9.]+)\]\s+(\[[^\]]*\])\s*$"
)


def parse(path):
    out = {}
    for line in open(path):
        m = ROW.match(line.rstrip("\n"))
        if m:
            out[m.group(1)] = (float(m.group(2)), float(m.group(3)), m.group(8))
    return out


def main():
    a_path, b_path = sys.argv[1], sys.argv[2]
    a_lab, b_lab = sys.argv[3], sys.argv[4]
    A, B = parse(a_path), parse(b_path)
    keys = [k for k in A if k in B]
    if not keys:
        raise SystemExit("no rows parsed -- did either run fail?")

    groups = [
        ("TRANSITIONS (the question)", lambda k: k.startswith("transition_points")),
        ("muF (positive control: 0.5/2 are OFF the sqrt2 knots)",
         lambda k: k in ("mufdown", "mufup")),
        ("muF x kappa_R", lambda k: k.startswith("muf") and "kappaFO" in k),
        ("kappa_R", lambda k: k.startswith("kappaFO")),
        ("alphaS", lambda k: "as_0" in k or k.startswith("ALPHAS")),
        ("NP lambda (invariance control)",
         lambda k: k.startswith("lambda") or k.startswith("delta_lambda")),
        ("TNP (invariance control)",
         lambda k: k.startswith(("gamma_", "b_q", "h_qqV", "s-", "s0", "s1", "s"))),
    ]
    seen = set()
    hdr = (f"{'variation':<34}{a_lab+' max':>12}{b_lab+' max':>12}{'ratio':>8}"
           f"{a_lab+' mean':>12}{b_lab+' mean':>12}{'ratio':>8}   worst qT (A/B)")
    for title, sel in groups:
        rows = [k for k in keys if sel(k) and k not in seen]
        if not rows:
            continue
        seen.update(rows)
        print(f"\n### {title}")
        print(hdr)
        print("-" * len(hdr))
        for k in sorted(rows):
            am, ame, aq = A[k]
            bm, bme, bq = B[k]
            print(f"{k:<34}{am:>12.2e}{bm:>12.2e}{am/bm:>8.2f}"
                  f"{ame:>12.2e}{bme:>12.2e}{ame/bme:>8.2f}   {aq} / {bq}")
    rest = [k for k in keys if k not in seen]
    if rest:
        print(f"\n### other")
        print(hdr)
        for k in sorted(rest):
            am, ame, aq = A[k]
            bm, bme, bq = B[k]
            print(f"{k:<34}{am:>12.2e}{bm:>12.2e}{am/bm:>8.2f}"
                  f"{ame:>12.2e}{bme:>12.2e}{ame/bme:>8.2f}   {aq} / {bq}")
    only = sorted(set(A) ^ set(B))
    if only:
        print("\nrows in one arm only:", only)


if __name__ == "__main__":
    main()
