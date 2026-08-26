#!/usr/bin/env python3
"""How big is the rule's bin-level constant c_val in the PRODUCTION cache, and
how much transition response can it be hiding?

node_cval interpolates the per-member constants on the GLOBAL kappa_F label,
tf = log(kappa_F)/var_muf_lnstep, with no transition-induced shift -- so
d(c_val)/d(x1,x2,x3) is identically ZERO. c_val is the one part of the rule with
no bT node, so it is the one place a "global coordinate cannot follow a per-node
shift" error genuinely survives.

Reported per bin:
  c_val / sigma_bin                     the share of the bin the dead constant is
  max_leg |c_leg - c_0| / sigma_bin     how far it moves over a FULL muF member
                                        step. The transition-induced coordinate
                                        is a FRACTION of a step, so this is a
                                        generous UPPER BOUND on the response
                                        node_cval fails to produce.
Compare that bound with the measured shortfall against the runcard route
(~1e-4 .. 1e-3 of sigma in qT 20-44).
"""
import argparse
import json
import os
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--conf", required=True)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

    core = ScetlibADXsec(args.conf, args.cache, threads=args.threads)
    sing, _ = core._sigma.sub_pieces()
    rep = sing.rule_cvals()
    sig, _ = core.values_and_jacobian(core.anchor)
    sig = np.asarray(sig, float).reshape(-1)
    keys = np.asarray([r["key"] for r in rep], float)
    # rules and bins are in the same order (the cache stores one rule per bin)
    order = {tuple(np.round(k, 9)): i for i, k in enumerate(keys)}
    rows = []
    print(f"{'|Y| bin':>14}{'qT bin':>12}{'sigma':>13}{'c_val/sigma':>13}"
          f"{'max|dc|/sigma':>15}{'sites':>7}")
    for i, b in enumerate(core.bins):
        j = order.get(tuple(np.round(b, 9)))
        if j is None:
            continue
        d = rep[j]
        c0 = d["c_val"]
        vc = np.asarray(d["var_c_val"], float)
        im = np.asarray(d["var_is_muf"], int)
        dmax = float(np.abs(vc[im != 0] - c0).max()) if (im != 0).any() else 0.0
        rows.append(dict(key=list(map(float, b)), sigma=float(sig[i]),
                         c_val=float(c0), dmax=dmax,
                         n_sites=int(d["n_sites"])))
        if b[4] >= 16.0 and b[2] < 0.31:
            print(f"[{b[2]:g},{b[3]:g}]".rjust(14)
                  + f"[{b[4]:g},{b[5]:g}]".rjust(12)
                  + f"{sig[i]:>13.4e}{c0/sig[i]:>13.3e}"
                  + f"{dmax/abs(sig[i]):>15.3e}{d['n_sites']:>7d}")
    json.dump(rows, open(args.out, "w"), indent=1)
    a = np.array([abs(r["c_val"] / r["sigma"]) for r in rows])
    m = np.array([r["dmax"] / abs(r["sigma"]) for r in rows])
    print(f"\nover all {len(rows)} bins: |c_val|/sigma median {np.median(a):.2e}"
          f" max {a.max():.2e};  max|dc|/sigma median {np.median(m):.2e}"
          f" max {m.max():.2e}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
