#!/usr/bin/env python3
"""ABSOLUTE-sigma summary of the residual-form arms, per direction.

dev = arm/runcard - 1 in units of sigma, aggregated over the bins whose TRUE
response exceeds `--usable` of sigma -- the reference's own node-ladder target,
below which its response is not resolved. Same statistic as the previous round's
section 2, so the two tables are comparable.

QUOTE DIFFERENCES BETWEEN ARMS OF ONE RUN, NOT LEVELS. Two independent runs of
the same mode-0 measurement differ by 0.3-3.7 percentage points bin by bin (and
by 35 pp at qT [24,28] on the x1,x3 leg between this round and the last), while
the arm-vs-arm difference within one run shares the reference, the node set, the
rules and the members and is exact.
"""
import argparse
import json
import os

import numpy as np

PTS = [("safe_x2_035.json", "x2 = 0.35   FINITE (template)"),
       ("safe_x2_075.json", "x2 = 0.75   FINITE (template)"),
       ("safe_x2_055.json", "x2 = 0.55   NEAR-ANCHOR (a FIT)"),
       ("safe_x1x3.json",   "x1,x3 = 0.3,0.9   FINITE (template)")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--usable", type=float, default=1e-4)
    args = ap.parse_args()
    for f, lab in PTS:
        p = os.path.join(args.dir, f)
        if not os.path.exists(p):
            print(f"\n{lab}: {f} MISSING")
            continue
        d = json.load(open(p))
        R = np.asarray(d["true_resp"], float)
        keep = np.abs(R) > args.usable
        b = np.asarray(d["bins"], float)
        arms = list(d["arms"])
        print(f"\n{'=' * 96}\n{lab}   |Y| [{b[0,2]:g}, {b[0,3]:g}]   "
              f"bins used: "
              f"{', '.join(f'[{b[k,4]:g},{b[k,5]:g}]' for k in range(len(R)) if keep[k])}")
        print(f"{'=' * 96}")
        print(f"{'arm':>12}{'max|dev|':>12}{'vs anl1':>9}{'mean|dev|':>12}"
              f"{'vs anl1':>9}{'worst bin':>12}   per-bin dev/|R| (%)")
        ref = None
        for a in arms:
            dev = np.asarray(d["arms"][a]["dev"], float)[keep]
            mx, mn = np.max(np.abs(dev)), np.mean(np.abs(dev))
            if a == "anl1":
                ref = (mx, mn)
        for a in arms:
            dev = np.asarray(d["arms"][a]["dev"], float)
            dk = dev[keep]
            mx, mn = np.max(np.abs(dk)), np.mean(np.abs(dk))
            wb = np.argmax(np.abs(dk))
            wl = [k for k in range(len(R)) if keep[k]][wb]
            frac = "  ".join(f"{100 * dev[k] / R[k]:+6.1f}"
                             for k in range(len(R)) if keep[k])
            print(f"{a:>12}{mx:>12.3e}{mx / ref[0]:>9.2f}{mn:>12.3e}"
                  f"{mn / ref[1]:>9.2f}"
                  f"{f'[{b[wl,4]:g},{b[wl,5]:g}]':>12}   {frac}")
        print("  'vs anl1' < 1 is better than the shipped candidate "
              "(mode 1 + the quadratic).")


if __name__ == "__main__":
    main()
