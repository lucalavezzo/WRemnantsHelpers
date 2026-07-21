#!/usr/bin/env python3
"""Bin-by-bin pull test: ptz5 (incremental, calibrated) vs as118_v2 (final).

pull_i = (new_i - old_i) / sqrt(err_new_i^2 + err_old_i^2), per 1-GeV qT bin,
|y|<2.5 fold, central scale, qT in [QT_LO, QT_HI]. Two spectra: full NNLO and
alpha_s^3-coefficient-only. Statistically independent campaigns => pulls ~
N(0,1) if both central values and error estimates are honest.

Caveat printed per run: parts with ndat<4 in the new run carry soft error
estimates; the --solid variant drops them from the NEW side only as a
robustness check (values then slightly incomplete: disclosed, not hidden).
"""

import argparse
import glob
import json
import os
import re
import sys

import numpy as np

AP = argparse.ArgumentParser()
AP.add_argument(
    "--run",
    default="/scratch/submit/cms/alphaS/"
    "CMS_Z_NNLO_condor_msht20an3lo_as118_ptz5_20260714",
)
AP.add_argument(
    "--old",
    default="/scratch/submit/cms/alphaS/"
    "CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2",
)
AP.add_argument("--ymax", type=float, default=2.5)
AP.add_argument("--qt", nargs=2, type=float, default=[5.0, 100.0])
AP.add_argument(
    "--solid",
    action="store_true",
    help="drop ndat<4 parts from the NEW side (robustness check)",
)
AP.add_argument(
    "--out",
    default=os.path.expanduser("~/public_html/alphaS/260718_nnlojet_ptz5_perbin_stats"),
)
A = AP.parse_args()

A3 = ("VV", "RV", "RRa", "RRb")
ALL = ("LO", "V", "R") + A3


def read_dat(path):
    rows = [l.split() for l in open(path) if not l.startswith("#")]
    return np.array(
        [
            [float(v[0]), float(v[2]), float(v[3]), float(v[4])]
            for v in rows
            if len(v) >= 5
        ]
    )


def fold(pattern):
    val = err2 = edges = None
    for f in glob.glob(pattern):
        m = re.search(r"ptz__(-?[\dp]+)__(-?[\dp]+)\.dat$", os.path.basename(f))
        if not m:
            continue
        ylo, yhi = (float(t.replace("p", ".")) for t in m.groups())
        if ylo < -A.ymax - 1e-9 or yhi > A.ymax + 1e-9:
            continue
        a = read_dat(f)
        if edges is None:
            edges = np.append(a[:, 0], a[-1, 1])
            val, err2 = np.zeros(len(a)), np.zeros(len(a))
        val += a[:, 2]
        err2 += a[:, 3] ** 2
    return edges, val, np.sqrt(err2)


def fold_new(prefixes):
    val = err2 = edges = None
    dropped = []
    for part in sorted(os.listdir(f"{A.run}/result/part")):
        if not any(
            part.startswith(p) and part[len(p)] == "_"
            for p in prefixes
            if len(part) > len(p)
        ):
            continue
        if A.solid:
            js = glob.glob(f"{A.run}/result/part/{part}/ptz__*.merged.json")
            if js and json.load(open(js[0]))["ndat"] < 4:
                dropped.append(part)
                continue
        e, v, er = fold(f"{A.run}/result/part/{part}/ptz__*.dat")
        if e is None:
            continue
        if edges is None:
            edges, val, err2 = e, np.zeros(len(v)), np.zeros(len(v))
        val += v
        err2 += er**2
    return edges, val, np.sqrt(err2), dropped


def pulls(order_old, prefixes, label):
    oe, ov, oer = fold(f"{A.old}/result/final/{order_old}.ptz__*.dat")
    ne, nv, ner, dropped = fold_new(prefixes)
    n = min(len(ov), len(nv))
    sel = (ne[:n] >= A.qt[0] - 1e-9) & (ne[1 : n + 1] <= A.qt[1] + 1e-9)
    comb = np.sqrt(ner[:n] ** 2 + oer[:n] ** 2)
    p = (nv[:n] - ov[:n]) / np.where(comb > 0, comb, np.nan)
    p = p[sel]
    print(
        f"{label}: n_bins={p.size}  mean={np.nanmean(p):+.2f}  "
        f"rms={np.nanstd(p):.2f}  |pull|>3: {int(np.nansum(np.abs(p) > 3))}"
        + (f"  [dropped {len(dropped)} soft parts]" if dropped else "")
    )
    return ne[: n + 1], p, sel


def main():
    tag = "SOLID-PARTS-ONLY" if A.solid else "ALL PARTS (nothing hidden)"
    print(f"pull test, {tag}, qT {A.qt[0]:.0f}-{A.qt[1]:.0f}, |y|<{A.ymax}")
    e1, p_full, s1 = pulls("nnlo", ALL, "full NNLO")
    e2, p_a3, s2 = pulls("nnlo_only", A3, "a3-only  ")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(11, 4), gridspec_kw={"width_ratios": [2, 1]}
    )
    ctr = 0.5 * (e1[:-1] + e1[1:])[s1]
    ax1.plot(ctr, p_full, "k.", ms=4, label="full NNLO")
    ctr2 = 0.5 * (e2[:-1] + e2[1:])[s2]
    ax1.plot(ctr2, p_a3, ".", color="crimson", ms=4, label=r"$\alpha_s^3$ only")
    for y in (-3, 3):
        ax1.axhline(y, color="gray", ls=":", lw=0.7)
    ax1.axhline(0, color="gray", lw=0.7)
    ax1.set_xlabel(r"$q_T^Z$ [GeV]")
    ax1.set_ylabel("pull (new-old)/err")
    ax1.legend(frameon=False)
    ax1.set_title(f"ptz5 vs as118_v2 — {tag}")
    bins = np.linspace(-5, 5, 26)
    ax2.hist(
        p_full[~np.isnan(p_full)],
        bins=bins,
        histtype="step",
        color="k",
        label="full NNLO",
    )
    ax2.hist(
        p_a3[~np.isnan(p_a3)],
        bins=bins,
        histtype="step",
        color="crimson",
        label=r"$\alpha_s^3$",
    )
    x = np.linspace(-5, 5, 200)
    ax2.plot(
        x,
        np.exp(-(x**2) / 2)
        / np.sqrt(2 * np.pi)
        * p_full[~np.isnan(p_full)].size
        * (bins[1] - bins[0]),
        color="royalblue",
        lw=1,
        label="N(0,1)",
    )
    ax2.set_xlabel("pull")
    ax2.legend(frameon=False, fontsize=8)
    suffix = "_solid" if A.solid else ""
    for ext in ("png", "pdf"):
        fig.savefig(f"{A.out}/pull_test{suffix}.{ext}", dpi=160, bbox_inches="tight")
    print(f"saved {A.out}/pull_test{suffix}.png/.pdf")


if __name__ == "__main__":
    sys.exit(main())
