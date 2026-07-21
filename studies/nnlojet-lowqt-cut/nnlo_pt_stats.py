#!/usr/bin/env python3
"""Per-bin qT statistics of the incrementally-merged NNLOJET ptz5 run.

Reads result/part/<part>/ptz__<ylo>__<yhi>.dat (incremental MergePart output,
central scale col 4/5), folds |y| < YMAX, sums parts into:
  - full NNLO spectrum (LO+V+R+VV+RV+RRa+RRb)
  - alpha_s^3 coefficient only (VV+RV+RRa+RRb)  <- what NNLOJET is needed for
Errors: quadrature across parts and y-slices (disjoint MC bins ~independent).

ERROR CONVENTIONS (settled 2026-07-18, see LOGBOOK):
- ptz5 run (hdf5 branch): incremental MergePart errors ARE trim+k-scan
  calibrated (verified via .merged.json cfg; this script asserts it).
- as118_v2 overlay: read from result/final ONLY (k-scan calibrated).
  NEVER compare against result/merge of the old fork: those are naive
  weighted errors, a median factor 4.3 (p10-p90: 3.6-6.2) too small.
- Folding is quadrature over disjoint y-slices; a folded median is therefore
  ~sqrt(N_slices) smaller than the per-(qT x y)-bin medians quoted in
  the 07-14 logbook Findings (7.9%) or make_unc_table output - different
  binning bases, do not compare across them.

Run with any py3 with numpy+matplotlib:
  python3 nnlo_pt_stats.py [--run DIR] [--old DIR] [--ymax 2.5]
"""

import glob
import os
import re
import sys

import numpy as np

import argparse
import json

_ap = argparse.ArgumentParser()
_ap.add_argument(
    "--run",
    default="/scratch/submit/cms/alphaS/"
    "CMS_Z_NNLO_condor_msht20an3lo_as118_ptz5_20260714",
)
_ap.add_argument(
    "--old",
    default="/scratch/submit/cms/alphaS/"
    "CMS_Z_NNLO_condor_msht20an3lo_as118_20260401_seedfix_clean_v2",
    help="reference run for the overlay; uses result/final ONLY",
)
_ap.add_argument("--ymax", type=float, default=2.5)
_ap.add_argument(
    "--out",
    default=os.path.expanduser("~/public_html/alphaS/260718_nnlojet_ptz5_perbin_stats"),
)
_ap.add_argument(
    "--min-ndat",
    type=int,
    default=0,
    help="exclude parts merged from fewer files (their per-bin "
    "errors are unreliable 1-file estimates). DEFAULT 0 = "
    "hide nothing (honest picture); quarantined runs must "
    "be explicitly requested and are always disclosed",
)
_ap.add_argument(
    "--absolute",
    action="store_true",
    help="also plot ABSOLUTE errors (fb) for the alpha_s^3 part "
    "(immune to zero-crossing artifacts)",
)
_ap.add_argument(
    "--orders",
    action="store_true",
    help="also plot LO and NLO-coefficient comparison, both runs",
)
_args = _ap.parse_args()
RUN, YMAX, OUT = _args.run, _args.ymax, _args.out
QT_MAX_SHOW = 100.0


def assert_calibrated(run):
    """Refuse to run on uncalibrated (old-fork naive) incremental merges."""
    sample = glob.glob(f"{run}/result/part/*/ptz__*.merged.json")
    if not sample:
        sys.exit(
            f"ABORT: no .merged.json under {run}/result/part - cannot "
            "verify the merge is trim+k-scan calibrated (old-fork naive "
            "merge?). Use result/final of a finalized run instead."
        )
    cfg = json.load(open(sample[0])).get("cfg", {})
    if "k_scan_nsteps" not in cfg or "trim_threshold" not in cfg:
        sys.exit(f"ABORT: merge cfg lacks trim/k-scan keys: {cfg}")


A3_PREFIX = {"VV", "RV", "RRa", "RRb"}
ALL_PREFIX = {"LO", "V", "R"} | A3_PREFIX


def yname_to_float(tok: str) -> float:
    return float(tok.replace("p", "."))


def read_dat(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            v = line.split()
            if len(v) >= 5:
                rows.append((float(v[0]), float(v[2]), float(v[3]), float(v[4])))
    a = np.array(rows)  # lower, upper, value, err
    return a


OLD = _args.old


def read_old_order(order):
    """Fold |y|<YMAX for an order-level file set of the as118_v2 finalize
    (result/final/<order>.ptz__<ylo>__<yhi>.dat). Returns (edges, val, err)."""
    val = err2 = edges = None
    for f in glob.glob(f"{OLD}/result/final/{order}.ptz__*.dat"):
        m = re.match(
            rf"{order}\.ptz__(-?[\dp]+)__(-?[\dp]+)\.dat$", os.path.basename(f)
        )
        if not m:
            continue
        ylo, yhi = (yname_to_float(t) for t in m.groups())
        if ylo < -YMAX - 1e-9 or yhi > YMAX + 1e-9:
            continue
        a = read_dat(f)
        if edges is None:
            edges = np.append(a[:, 0], a[-1, 1])
            val, err2 = np.zeros(len(a)), np.zeros(len(a))
        val += a[:, 2]
        err2 += a[:, 3] ** 2
    return edges, val, np.sqrt(err2)


def main():
    assert_calibrated(RUN)
    parts = sorted(os.listdir(f"{RUN}/result/part"))
    # ghost-part quarantine: parts merged from < min_ndat files carry
    # meaningless per-bin errors (single-file "scatter"); they are numerically
    # tiny channels dokan never fed. Excluded from ALL curves; disclosed here.
    ghosts = []
    for part in list(parts):
        js = glob.glob(f"{RUN}/result/part/{part}/ptz__*.merged.json")
        nd = json.load(open(js[0]))["ndat"] if js else 0
        if nd < _args.min_ndat:
            ghosts.append((part, nd))
            parts.remove(part)
    if ghosts:
        print(
            f"quarantined {len(ghosts)} ghost parts (ndat<{_args.min_ndat}):",
            " ".join(f"{p}({n})" for p, n in ghosts),
        )
    edges = None
    acc = {}  # prefix -> [val, err2]
    nslices = 0
    for part in parts:
        prefix = part.split("_")[0]
        if prefix not in ALL_PREFIX:
            continue
        for f in glob.glob(f"{RUN}/result/part/{part}/ptz__*.dat"):
            m = re.match(r"ptz__(-?[\dp]+)__(-?[\dp]+)\.dat$", os.path.basename(f))
            if not m:
                continue
            ylo, yhi = (yname_to_float(t) for t in m.groups())
            if ylo < -YMAX - 1e-9 or yhi > YMAX + 1e-9:
                continue
            a = read_dat(f)
            if edges is None:
                edges = np.append(a[:, 0], a[-1, 1])
            if prefix not in acc:
                acc[prefix] = [np.zeros(len(a)), np.zeros(len(a))]
            acc[prefix][0] += a[:, 2]
            acc[prefix][1] += a[:, 3] ** 2
            nslices += 1
    print(f"folded {nslices} (part x y-slice) histograms, |y|<{YMAX}")

    def combine(prefixes):
        v = sum(acc[p][0] for p in prefixes if p in acc)
        e = np.sqrt(sum(acc[p][1] for p in prefixes if p in acc))
        return v, e

    full_v, full_e = combine(ALL_PREFIX)
    a3_v, a3_e = combine(A3_PREFIX)

    ctr = 0.5 * (edges[:-1] + edges[1:])
    sel = (edges[:-1] >= 5.0 - 1e-9) & (edges[1:] <= QT_MAX_SHOW + 1e-9)

    def stats(v, e, s):
        rel = np.abs(e[s] / np.where(v[s] != 0, v[s], np.nan)) * 100
        return np.nanmedian(rel), np.nanmax(rel), rel

    med_f, max_f, rel_f = stats(full_v, full_e, sel)
    med_a, max_a, rel_a = stats(a3_v, a3_e, sel)
    print(f"1-GeV bins, qT 5-{QT_MAX_SHOW:.0f}, |y|<{YMAX}:")
    print(f"  full NNLO : median rel err {med_f:.2f}%  worst {max_f:.1f}%")
    print(f"  a3-only   : median rel err {med_a:.2f}%  worst {max_a:.1f}%")

    # 2-GeV rebin for comparison with the as118_v2 audit table (median 3.7%)
    def rebin2(v, e2):
        n = (len(v) // 2) * 2
        return v[:n].reshape(-1, 2).sum(1), np.sqrt(e2[:n].reshape(-1, 2).sum(1))

    fv2, fe2 = rebin2(full_v, full_e**2)
    edges2 = edges[:-1:2]
    sel2 = (edges2 >= 5.0 - 1e-9) & (edges2 + 2.0 <= QT_MAX_SHOW + 1e-9)
    rel2 = np.abs(fe2[sel2] / np.where(fv2[sel2] != 0, fv2[sel2], np.nan)) * 100
    print(f"  full NNLO, 2-GeV bins: median {np.nanmedian(rel2):.2f}%")

    os.makedirs(OUT, exist_ok=True)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(8, 8),
        sharex=True,
        gridspec_kw={"height_ratios": [2, 1.4], "hspace": 0.06},
    )
    ax1.stairs(full_v, edges, label="full NNLO (LO+..+RR)", color="k", lw=1.4)
    ax1.stairs(
        a3_v, edges, label=r"$\alpha_s^3$ coefficient only", color="crimson", lw=1.2
    )
    ax1.axhline(0, color="gray", lw=0.6)
    ax1.set_xlim(0, QT_MAX_SHOW)
    ax1.set_ylabel(r"$d\sigma/dq_T$ per 1 GeV bin, $|y|<2.5$  [fb]")
    ax1.legend(frameon=False)
    import time as _t

    ax1.set_title(
        "NNLOJET ptz5 run — incremental-merge state " + _t.strftime("%Y-%m-%d %H:%M")
    )
    ax2.stairs(
        np.abs(full_e / np.where(full_v != 0, full_v, np.nan)) * 100,
        edges,
        color="k",
        lw=1.4,
        label="full NNLO (this run)",
    )
    ax2.stairs(
        np.abs(a3_e / np.where(a3_v != 0, a3_v, np.nan)) * 100,
        edges,
        color="crimson",
        lw=1.2,
        label=r"$\alpha_s^3$ only (this run)",
    )
    # as118_v2 finalize overlay (1 GeV cut, full campaign, 1.05M CPU-h)
    for order, color, lbl in (
        ("nnlo", "royalblue", "full NNLO (as118_v2 final)"),
        ("nnlo_only", "darkorange", r"$\alpha_s^3$ only (as118_v2 final)"),
    ):
        oe, ov, oer = read_old_order(order)
        if oe is None:
            continue
        n = min(len(ov), len(edges) - 1)
        rel_o = np.abs(oer[:n] / np.where(ov[:n] != 0, ov[:n], np.nan)) * 100
        ax2.stairs(rel_o, oe[: n + 1], color=color, lw=1.0, ls="--", label=lbl)
        osel = (oe[:n] >= 5.0 - 1e-9) & (oe[1 : n + 1] <= QT_MAX_SHOW + 1e-9)
        print(
            f"  as118_v2 {order:9s}: median rel err "
            f"{np.nanmedian(rel_o[osel]):.2f}% (qT 5-{QT_MAX_SHOW:.0f})"
        )
    ax2.axhline(1.0, color="green", ls="--", lw=0.8, label="1% target")
    ax2.axvspan(0, 5, color="gray", alpha=0.15, lw=0)
    ax2.set_yscale("log")
    ax2.set_ylabel("rel. stat. err per bin [%]")
    ax2.set_xlabel(r"$q_T^Z$ [GeV]")
    ax2.legend(frameon=False, fontsize=9)
    for ext in ("png", "pdf"):
        fig.savefig(f"{OUT}/nnlo_pt_perbin_stats.{ext}", dpi=160, bbox_inches="tight")
    print(f"saved {OUT}/nnlo_pt_perbin_stats.png/.pdf")

    if _args.absolute:
        oe, ov, oer = read_old_order("nnlo_only")
        n = min(len(a3_v), (len(oe) - 1) if oe is not None else len(a3_v))
        figA, (b1, b2) = plt.subplots(
            2,
            1,
            figsize=(8, 7),
            sharex=True,
            gridspec_kw={"height_ratios": [1.4, 1.4], "hspace": 0.06},
        )
        b1.stairs(
            a3_v,
            edges,
            color="crimson",
            lw=1.3,
            label=r"$\alpha_s^3$ coeff (ptz5, incremental)",
        )
        if oe is not None:
            b1.stairs(
                ov[:n],
                oe[: n + 1],
                color="darkorange",
                ls="--",
                lw=1.1,
                label=r"$\alpha_s^3$ coeff (as118_v2 final)",
            )
        b1.axhline(0, color="gray", lw=0.6)
        b1.set_ylabel(r"$d\sigma/dq_T$ per 1 GeV, $|y|<2.5$ [fb]")
        b1.legend(frameon=False, fontsize=9)
        b1.set_title(r"$\alpha_s^3$ coefficient — value and absolute error")
        b2.stairs(a3_e, edges, color="crimson", lw=1.3, label="ptz5 (this run)")
        if oe is not None:
            b2.stairs(
                oer[:n],
                oe[: n + 1],
                color="darkorange",
                ls="--",
                lw=1.1,
                label="as118_v2 final",
            )
        b2.set_yscale("log")
        b2.set_ylabel("abs. stat. err per bin [fb]")
        b2.set_xlabel(r"$q_T^Z$ [GeV]")
        b2.set_xlim(0, QT_MAX_SHOW)
        b2.axvspan(0, 5, color="gray", alpha=0.15, lw=0)
        b2.legend(frameon=False, fontsize=9)
        for ext in ("png", "pdf"):
            figA.savefig(f"{OUT}/a3_absolute_err.{ext}", dpi=160, bbox_inches="tight")
        sel_a = (edges[:-1] >= 5.0) & (edges[1:] <= QT_MAX_SHOW)
        if oe is not None:
            osel = (oe[:n] >= 5.0) & (oe[1 : n + 1] <= QT_MAX_SHOW)
            print(
                f"a3 ABSOLUTE err median (fb): ptz5 "
                f"{np.median(a3_e[sel_a]):.1f} vs as118_v2 "
                f"{np.median(oer[:n][osel]):.1f} "
                f"(ratio {np.median(a3_e[sel_a]) / np.median(oer[:n][osel]):.2f})"
            )
        print(f"saved {OUT}/a3_absolute_err.png/.pdf")

    if _args.orders:
        new_orders = {
            "LO": (["LO"], "black", "solid"),
            "NLO coeff (V+R)": (["V", "R"], "crimson", "solid"),
        }
        old_orders = {
            "LO": ("lo", "gray", "dashed"),
            "NLO coeff (V+R)": ("nlo_only", "darkorange", "dashed"),
        }
        figO, (c1, c2) = plt.subplots(
            2,
            1,
            figsize=(8, 7),
            sharex=True,
            gridspec_kw={"height_ratios": [1.4, 1.4], "hspace": 0.06},
        )
        for lbl, (pfx, col, ls) in new_orders.items():
            v, e = combine(set(pfx))
            c1.stairs(np.abs(v), edges, color=col, ls=ls, lw=1.3, label=f"{lbl} (ptz5)")
            c2.stairs(
                np.abs(e / np.where(v != 0, v, np.nan)) * 100,
                edges,
                color=col,
                ls=ls,
                lw=1.3,
                label=f"{lbl} (ptz5)",
            )
            s = (edges[:-1] >= 5.0) & (edges[1:] <= QT_MAX_SHOW)
            print(
                f"orders: {lbl:16s} ptz5     median rel err "
                f"{np.nanmedian(np.abs(e[s]/v[s]))*100:.2f}%"
            )
        for lbl, (order, col, ls) in old_orders.items():
            oe, ov, oer = read_old_order(order)
            if oe is None:
                continue
            n = len(ov)
            c1.stairs(
                np.abs(ov),
                oe[: n + 1],
                color=col,
                ls=ls,
                lw=1.1,
                label=f"{lbl} (as118_v2)",
            )
            c2.stairs(
                np.abs(oer / np.where(ov != 0, ov, np.nan)) * 100,
                oe[: n + 1],
                color=col,
                ls=ls,
                lw=1.1,
                label=f"{lbl} (as118_v2)",
            )
            s = (oe[:n] >= 5.0) & (oe[1 : n + 1] <= QT_MAX_SHOW)
            print(
                f"orders: {lbl:16s} as118_v2 median rel err "
                f"{np.nanmedian(np.abs(oer[s]/ov[s]))*100:.2f}%"
            )
        c1.set_yscale("log")
        c1.set_ylabel(r"$|d\sigma/dq_T|$ per 1 GeV, $|y|<2.5$ [fb]")
        c1.legend(frameon=False, fontsize=9, ncol=2)
        c1.set_title("LO and NLO-coefficient pieces — ptz5 vs as118_v2 (final)")
        c2.set_yscale("log")
        c2.set_ylabel("rel. stat. err per bin [%]")
        c2.set_xlabel(r"$q_T^Z$ [GeV]")
        c2.set_xlim(0, QT_MAX_SHOW)
        c2.axvspan(0, 5, color="gray", alpha=0.15, lw=0)
        c2.legend(frameon=False, fontsize=9, ncol=2)
        for ext in ("png", "pdf"):
            figO.savefig(f"{OUT}/lo_nlo_compare.{ext}", dpi=160, bbox_inches="tight")
        print(f"saved {OUT}/lo_nlo_compare.png/.pdf")

    with open(f"{OUT}/nnlo_pt_perbin_stats_table.md", "w") as fh:
        fh.write(
            "| qT [GeV] | full NNLO [fb] | rel err % | a3-only [fb] | rel err % |\n"
        )
        fh.write("|---|---|---|---|---|\n")
        for i in range(len(ctr)):
            if edges[i] >= QT_MAX_SHOW:
                break
            rf = abs(full_e[i] / full_v[i]) * 100 if full_v[i] else float("nan")
            ra = abs(a3_e[i] / a3_v[i]) * 100 if a3_v[i] else float("nan")
            fh.write(
                f"| {edges[i]:.0f}-{edges[i+1]:.0f} | {full_v[i]:.4g} | "
                f"{rf:.2f} | {a3_v[i]:.4g} | {ra:.2f} |\n"
            )
    print(f"saved {OUT}/nnlo_pt_perbin_stats_table.md")


if __name__ == "__main__":
    sys.exit(main())
