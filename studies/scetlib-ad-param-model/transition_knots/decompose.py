#!/usr/bin/env python3
"""OURS vs THEIRS, per qT bin, at |Y| in [0, 0.15].

ours   = model / runcard  - 1   (interp JSONs; identical physics on both sides,
                                 so this is our interpolation error alone)
total  = model / template - 1   (perbin JSON, from the production cache)
theirs = (1+total)/(1+ours) - 1 (what is left: a different nonsingular and
                                 possibly a different matching in the template)

Also prints the two model instances against each other -- the live 5-bin rules
at target_precision_rel 1e-4 vs the 210-bin production cache at 1e-3 -- because
`ours` and `total` are measured on different ones and the difference is a
systematic on the split.
"""
import json
import sys

import numpy as np

B = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/nak/"
LAB = {"035": "transition_points0.2_0.35_1.0",
       "075": "transition_points0.2_0.75_1.0"}
QT = [(18, 20), (20, 24), (24, 28), (28, 33), (33, 44)]


def main():
    pb = json.load(open(B + "perbin_after.json"))
    Te = pb["qT_edges"]
    idx = {(Te[k], Te[k + 1]): k for k in range(len(Te) - 1)}
    for tag, knot in (("035", "k2"), ("035", "ksqrt2"), ("075", "k2"),
                      ("075", "ksqrt2")):
        try:
            d = json.load(open(f"{B}fix_x2_{tag}_{knot}.json"))
        except FileNotFoundError:
            print(f"\n[{tag} {knot}] not available")
            continue
        L = LAB[tag]
        rec = pb["dirs"][L]["iy0"]
        pc = np.asarray(d["par_cen"], float)
        rm_live = np.asarray(d["par_var"], float) / pc
        rr_run = np.asarray(d["run_var"], float) / pc
        print(f"\n=== {L}, muF knots f={d['knot']:.4g}, |Y| [0, 0.15]")
        print(f"{'qT bin':>12}{'true (runcard)':>16}{'model(live)':>13}"
              f"{'model(cache)':>14}{'ours':>11}{'total':>11}{'theirs':>11}"
              f"{'ours/true':>11}")
        for k, (lo, hi) in enumerate(QT):
            j = idx[(float(lo), float(hi))]
            tr = rr_run[k] - 1.0
            mo = rm_live[k] - 1.0
            mc = rec["R_model"][j] - 1.0
            ours = rm_live[k] / rr_run[k] - 1.0
            total = rec["total"][j]
            theirs = (1 + total) / (1 + ours) - 1.0
            print(f"[{lo},{hi}]".rjust(12)
                  + f"{tr:>16.3e}{mo:>13.3e}{mc:>14.3e}"
                  + f"{ours:>11.3e}{total:>11.3e}{theirs:>11.3e}"
                  + f"{100*ours/tr:>10.1f}%")


if __name__ == "__main__":
    main()
