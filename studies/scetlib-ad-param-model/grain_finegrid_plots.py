#!/usr/bin/env python3
r"""The measured fine-grid points, on top of the coarsening ladder.

Takes the CSVs written by ``grain_vs_grid.py`` (coarsenings of the production
card, model included) and by ``grain_finegrid.py`` (one or two dedicated
histmaker runs whose gen grid is FINER than the card's) and draws them on one
axis, so the extrapolation and the measurement can be read against each other.

Bare matplotlib on purpose: these are scaling curves of derived quantities, not
histograms. ``wums.output_tools.write_index_and_log`` still writes the
provenance beside each figure.
"""

import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

BLUE, RED, PURPLE, GREEN, ORANGE = "#5790fc", "#e42536", "#964a8b", "#2ca02c", "#f89c20"


def load(path):
    rows = list(csv.DictReader(open(path)))
    for r in rows:
        for k in r:
            if k not in ("direction", "qgrid", "ygrid"):
                try:
                    r[k] = float(r[k])
                except ValueError:
                    pass
    return rows


def save(fig, outdir, name, meta):
    os.makedirs(outdir, exist_ok=True)
    fig.savefig(os.path.join(outdir, name + ".png"), dpi=150, bbox_inches="tight")
    fig.savefig(os.path.join(outdir, name + ".pdf"), bbox_inches="tight")
    plt.close(fig)
    try:
        from wums import output_tools
        output_tools.write_index_and_log(outdir, name, analysis_meta_info=meta,
                                         args=None)
    except Exception as exc:
        print(f"   [warn] write_index_and_log: {exc}")


def series_from_fine(rows, ygrid="card"):
    """{n_gen_qT_bins: (median, worst)} at a fixed |Y| grid."""
    out = {}
    for q in sorted({r["qgrid"] for r in rows}):
        s = [r for r in rows if r["qgrid"] == q and r["ygrid"] == ygrid]
        if not s:
            continue
        v = np.array([r["grain_wmean"] for r in s])
        out[int(s[0]["nT"])] = (float(np.median(v)), float(v.max()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--card-csv", required=True, help="grain_vs_grid.py scan")
    ap.add_argument("--fine-csv", action="append", default=[],
                    metavar="LABEL=PATH", help="grain_finegrid.py output(s)")
    ap.add_argument("-o", "--out-dir", required=True)
    ap.add_argument("--meta", default="")
    args = ap.parse_args()

    card = load(args.card_csv)
    fines = {}
    for spec in args.fine_csv:
        lab, path = spec.split("=", 1)
        fines[lab] = load(path)

    meta = {"card scan": os.path.abspath(args.card_csv),
            "fine scans": {k: os.path.abspath(v.split("=")[-1])
                           for k, v in zip(fines, args.fine_csv)},
            "note": args.meta}

    fig, ax = plt.subplots(figsize=(7.6, 5.2))

    # the card-based coarsening ladder (model in the loop, |Y| at the card's 10)
    ks = sorted({r["k"] for r in card})
    nb, med, wst = [], [], []
    for k in ks:
        s = [r for r in card if r["k"] == k and r["m"] == 1]
        v = np.array([r["grain_wmean"] for r in s])
        nb.append(int(s[0]["nT"])); med.append(np.median(v)); wst.append(v.max())
    ax.plot(nb, med, "-o", color=RED, lw=1.8, ms=6,
            label="production card, coarsened: median")
    ax.plot(nb, wst, "--s", color=RED, lw=1.4, ms=5, alpha=0.55,
            label="production card, coarsened: worst")

    styles = {"reco-grid": (GREEN, "*", 17), "corr-grid": (PURPLE, "P", 13)}
    for lab, rows in fines.items():
        s = series_from_fine(rows)
        c, mk, ms = styles.get(lab, (ORANGE, "D", 10))
        xs = sorted(s)
        ax.plot(xs, [s[x][0] for x in xs], ":", color=c, lw=1.2, alpha=0.7)
        ax.plot(xs, [s[x][0] for x in xs], mk, color=c, ms=ms,
                label=f"{lab} run, MEASURED: median", zorder=5)
        ax.plot(xs, [s[x][1] for x in xs], mk, color=c, ms=ms * 0.62,
                markerfacecolor="none", label=f"{lab} run, MEASURED: worst",
                zorder=5)

    ax.set_xscale("log"); ax.set_yscale("log")
    allx = sorted(set(nb) | {x for r in fines.values()
                             for x in series_from_fine(r)})
    ax.set_xticks(allx); ax.set_xticklabels([str(x) for x in allx], fontsize=8)
    ax.set_xticks([], minor=True)
    ax.axvline(21, color="k", lw=0.8, ls="-.", alpha=0.6)
    ax.text(21, ax.get_ylim()[1], " shipped", fontsize=8, va="top")
    ax.set_xlabel("gen $q_T$ bins (resolved region plus one tail bin)")
    ax.set_ylabel(r"GRAIN: yield-weighted mean $|r_B/r_\mathrm{ref}-1|$")
    ax.grid(alpha=0.3, which="major")
    ax.legend(fontsize=8, loc="lower left")
    ax.set_title("Granularity term against gen $q_T$ resolution:\n"
                 "coarsening ladder (line) and the dedicated finer histmakers "
                 "(markers)", fontsize=10)
    save(fig, args.out_dir, "grain_measured_vs_grid", meta)
    print(f"figures -> {args.out_dir}")


if __name__ == "__main__":
    main()
