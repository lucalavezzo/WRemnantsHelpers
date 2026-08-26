#!/usr/bin/env python3
"""The kappa_R A/B, reduced to what validate_variations should report.

Reads the route JSONs written by ../ab_scale_route.py (kept here because they are
the evidence for scetlib-cms MR !3) and prints, per qT bin, the response ratio
var/cen for each route and its deviation from the CorrZ template -- the SAME
metric validate_variations uses, so this is a PRE-REGISTERED prediction for the
kappa_R panel of the cache validation, not a post-hoc rationalisation.

Routes, all at kappa_R down (`kappaFO0.5-kappaf2.`), Q [60,120], |Y| [0,0.15]:
  A  runcard, autodiff OFF   -- SCETlib's own production path, the reference
  B  live parameter, BEFORE  -- the floor-compensation bug
  C  A with the floors doubled by hand -- the hypothesis test
  D  live parameter, FIXED
No SCETlib and no cache needed; runs anywhere python does.

The point of the table: D == A to ~1e-6 everywhere, so our differentiable kappa_R
now IS the production route. What survives against CorrZ is present in A too --
with autodiff off entirely -- so it is a difference between this runcard and the
one CorrZ was made with (the nonsingular qT cutoff, 0.1 vs 1.0), and it decays
with qT the way that effect does. It is NOT attributable to the AD path.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROUTES = [
    ("A runcard/ADoff", "kap_A_runcard.json"),
    ("B param/BEFORE", "kap_B_param_fo.json"),
    ("C param+floors2x", "kap_C_floorfix.json"),
    ("D param/FIXED", "kap_D_fixed.json"),
    ("CorrZ", "kap_corr.json"),
]


def main():
    R, bins = {}, None
    for tag, fname in ROUTES:
        with open(os.path.join(HERE, fname)) as fh:
            d = json.load(fh)
        # every route must be on the same bins or the columns are not comparable
        if bins is not None and d["bins"] != bins:
            raise SystemExit(f"{fname}: bins differ from the earlier routes")
        bins = d["bins"]
        R[tag] = [v / c for v, c in zip(d["var"], d["cen"])]

    qt = [f"[{int(b[4])},{int(b[5])}]" for b in bins]
    ref = R["CorrZ"]
    names = [t for t, _ in ROUTES]

    print("kappa_R down (kappaFO0.5-kappaf2.), Q [60,120] |Y| [0,0.15]\n")
    print("response ratio var/cen")
    print(f"{'qT':>9}" + "".join(f"{n.split()[0]:>12}" for n in names))
    for i, q in enumerate(qt):
        print(f"{q:>9}" + "".join(f"{R[n][i]:>12.6f}" for n in names))

    print("\ndev = route / CorrZ - 1   (what validate_variations plots)")
    print(f"{'qT':>9}" + "".join(f"{n.split()[0]:>12}" for n in names[:-1]))
    for i, q in enumerate(qt):
        print(f"{q:>9}" + "".join(f"{R[n][i] / ref[i] - 1:>12.2e}" for n in names[:-1]))

    print("\nmax |dev| vs CorrZ (all bins / excluding the first qT bin)")
    for n in names[:-1]:
        dev = [abs(R[n][i] / ref[i] - 1) for i in range(len(qt))]
        a = max(range(len(qt)), key=lambda i: dev[i])
        b = max(range(1, len(qt)), key=lambda i: dev[i])
        print(f"  {n:<20} {dev[a]:.2e} at {qt[a]:<8} / {dev[b]:.2e} at {qt[b]}")

    print("\ndev of the FIXED route against the runcard route (our own residual)")
    for i, q in enumerate(qt):
        print(f"{q:>9}  {R['D param/FIXED'][i] / R['A runcard/ADoff'][i] - 1:>10.2e}")


if __name__ == "__main__":
    main()
