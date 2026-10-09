#!/usr/bin/env python3
"""Cost model for a Q-split, no-PDF-eigenvector SCETlib AD cache.

Calibrated ONLY on the timing probes in ../logs (time_t_*.txt, /usr/bin/time -v of
a whole 4-bin build: node set + rules + alphaS pair, --pdf-eig 0, P = 24, pin
ca15aec, base_1e3.conf).  Each probe is 4 cells = 2 |Y| rows x 2 qT rows.

Model: core-minutes per (Q window, |Y| row, qT row) cell
    c = C_Q[window] * g(Y) * h(qT)
with C_Q the measured low-qT (0-2 GeV) FORWARD (|Y| 1.5-2.5) cell cost per Q
window, and g, h shape factors measured in the PEAK window only (86-96) and
assumed to factorise.  UPPER bound: every cell priced at C_Q (the most expensive
cell class, which is what the probes measured directly).

Wall time = sum(c) / effective cores.  Effective cores: the probes averaged
36-54 busy of 64; the 260914/260921 production builds ran 185-364 busy of 384.
We use 250 (low) .. 330 (high) of a 384-core cap.
"""
import glob
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(HERE, "logs")


def coremin(tag):
    s = open(os.path.join(LOGS, f"time_{tag}.txt")).read()
    u = float(re.search(r"User time \(seconds\): ([0-9.]+)", s).group(1))
    y = float(re.search(r"System time \(seconds\): ([0-9.]+)", s).group(1))
    return (u + y) / 60.0


PER = 4.0  # cells per probe
C_Q = {
    (60, 76): coremin("t_q60_76") / PER,
    (76, 86): coremin("t_q76_86") / PER,
    (86, 96): coremin("t_q86_96") / PER,
    (96, 106): coremin("t_q96_106") / PER,
    (106, 120): coremin("t_q106_120") / PER,
}
C_FULL = coremin("t_q60_120") / PER  # the single [60,120] window, same cells

# shape factors in the peak window, relative to the low-qT forward cell
peak = C_Q[(86, 96)]
lo_c = coremin("t_q86_96_loqt_c") / PER  # qT 0-2, |Y| 0-1
mid_c = coremin("t_q86_96_midqt_c") / PER  # qT 6-10, |Y| 0-1
mid_f = coremin("t_q86_96_midqt_f") / PER  # qT 6-10, |Y| 1.5-2.5
hi_c = coremin("t_q86_96_hiqt") / PER  # qT 25-40, |Y| 0-1

# forward/central ratio, measured at low and mid qT; at high qT assume the mid one
yratio_lo = peak / lo_c
yratio_mid = mid_f / mid_c
# central-Y qT profile (log-interpolated between measured qT centres)
qt_pts = np.array([1.0, 8.0, 32.5])
cen_pts = np.log(np.array([lo_c, mid_c, hi_c]))
ratio_pts = np.array([yratio_lo, yratio_mid, yratio_mid])


def cell_cost(qlo, qhi, ylo, yhi, tlo, thi):
    qc = 0.5 * (tlo + thi)
    cen = np.exp(np.interp(qc, qt_pts, cen_pts))  # peak-window, |Y|~0.5
    r = np.interp(qc, qt_pts, ratio_pts)
    yc = 0.5 * (ylo + yhi)
    # linear in |Y| between the central (0.5) and forward (2.0) probe centres
    g = 1.0 + (r - 1.0) * np.clip((yc - 0.5) / 1.5, 0.0, 1.2)
    cpeak = cen * g
    return (
        cpeak * C_Q[(qlo, qhi)] / peak if (qlo, qhi) in C_Q else cpeak * C_FULL / peak
    )


def grid_cost(q_edges, y_edges, t_edges):
    tot = up = 0.0
    n = 0
    for q in zip(q_edges[:-1], q_edges[1:]):
        for y in zip(y_edges[:-1], y_edges[1:]):
            for t in zip(t_edges[:-1], t_edges[1:]):
                n += 1
                if q not in C_Q:
                    raise SystemExit(f"Q window {q} was not probed; no cost for it")
                tot += cell_cost(*q, *y, *t)
                up += C_Q[q]
    return n, tot, up


GRIDS = {
    "A 5Q x 5Y x 15qT (recommended)": (
        [60, 76, 86, 96, 106, 120],
        [0, 0.5, 1.0, 1.5, 2.0, 2.5],
        [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 17, 20, 25, 30, 40],
    ),
    "B 5Q x 3Y x 10qT (minimal)": (
        [60, 76, 86, 96, 106, 120],
        [0, 0.8, 1.6, 2.5],
        [0, 2, 4, 6, 8, 10, 13, 16, 20, 30, 40],
    ),
    "C 5Q x 6Y x 20qT (rich)": (
        [60, 76, 86, 96, 106, 120],
        [0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.5],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 23, 26, 30, 35, 40],
    ),
    "ref 1Q [60,120] x 5Y x 15qT": (
        [60, 120],
        [0, 0.5, 1.0, 1.5, 2.0, 2.5],
        [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 17, 20, 25, 30, 40],
    ),
}

if __name__ == "__main__":
    print("per-cell core-min, low-qT forward cells, by Q window:")
    for k, v in C_Q.items():
        print(f"   Q {k}: {v:7.1f}")
    print(
        f"   sum of 5 windows: {sum(C_Q.values()):7.1f}   single [60,120]: {C_FULL:7.1f}"
    )
    print(
        f"peak-window shape: lo_c {lo_c:.1f} lo_f {peak:.1f} mid_c {mid_c:.1f} "
        f"mid_f {mid_f:.1f} hi_c {hi_c:.1f}  (core-min/cell)"
    )
    print()
    print(
        f"{'grid':34s} {'bins':>5s} {'model core-h':>12s} {'upper core-h':>12s} "
        f"{'wall model':>11s} {'wall upper':>11s}"
    )
    for name, (q, y, t) in GRIDS.items():
        if name.startswith("ref"):
            # single window: use the measured full-window cost directly
            n = (len(y) - 1) * (len(t) - 1)
            tot = sum(
                cell_cost(60, 120, *yy, *tt)
                for yy in zip(y[:-1], y[1:])
                for tt in zip(t[:-1], t[1:])
            )
            up = n * C_FULL
        else:
            n, tot, up = grid_cost(q, y, t)
        w_model = tot / 330.0 / 60.0, tot / 250.0 / 60.0
        w_up = up / 330.0 / 60.0, up / 250.0 / 60.0
        print(
            f"{name:34s} {n:5d} {tot / 60:12.0f} {up / 60:12.0f} "
            f"{w_model[0]:4.1f}-{w_model[1]:4.1f} h {w_up[0]:4.1f}-{w_up[1]:4.1f} h"
        )
