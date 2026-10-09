#!/usr/bin/env python3
"""Loss histories of the T2 stiff-wall refits vs their references (main fit only), via save_plot.

Not a histogram plot (a minimiser trace), so plain matplotlib axes; saved through the local save_plot copy.
Top: loss - (final loss of that run) on a log axis (+1e-9 floor so the last point shows); rejected steps
(loss unchanged) marked with x. Bottom: wall time per iteration (s) -- long iterations = many Hessian-vector
products inside the trust-krylov subproblem.
NOTE the new and reference losses are DIFFERENT objectives (tau 8 / margin 0 vs tau 5 / margin 5e-3), so the
curves are each relative to their own final value; absolute levels are in the logbook table.
"""

import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import loghist  # noqa: E402
from plot_output import save_plot  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NEW = f"{A}/260930_stiff_wall_fits"
RUNS = {
    "NOM": [
        ("NOMSTIFF (m=0, tau=8)", f"{NEW}/NOMSTIFF.log"),
        (
            "ref LATL4ZY35WALLWARM (m=5e-3, tau=5)",
            f"{A}/260928_lattice_y35_fits/LATL4ZY35WALLWARM.log",
        ),
    ],
    "XW": [
        ("XWSTIFF (m=0, tau=8)", f"{NEW}/XWSTIFF.log"),
        (
            "ref Y35ZWALLWARM (m=5e-3, tau=5)",
            f"{A}/260924_y35_bin0xzero_fits/Y35ZWALLWARM.log",
        ),
    ],
    "XL4Z": [
        ("XL4ZSTIFF (m=0, tau=8)", f"{NEW}/XL4ZSTIFF.log"),
        (
            "ref Y35ZWALLL4Z (m=5e-3, tau=5, SIGTERMed)",
            f"{A}/260929_l4zero_fits/Y35ZWALLL4Z.log",
        ),
        ("ref Y35ZWALLL4ZR (resume)", f"{A}/260929_l4zero_fits/Y35ZWALLL4ZR.log"),
    ],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.dirname(HERE))
    ap.add_argument("--fits", nargs="*", default=list(RUNS))
    args = ap.parse_args()
    from wums import (
        plot_tools,
    )  # noqa: F401  (its import sets a global mplhep style; neutralise it below)

    for fit in args.fits:
        plt.rcdefaults()
        fig, (ax, ax2) = plt.subplots(
            2, 1, figsize=(8, 7), sharex=True, gridspec_kw=dict(height_ratios=[2, 1])
        )
        meta = {}
        for k, (lab, path) in enumerate(RUNS[fit]):
            if not os.path.exists(path):
                continue
            r = loghist.parse(path)
            if r["n_iter"] == 0:
                continue
            L = r["loss"]
            it = np.arange(len(L))
            gap = L - L.min() + 1e-9
            c = f"C{k}"
            ax.semilogy(
                it,
                gap,
                "-o",
                ms=3,
                color=c,
                label=f"{lab}: {len(L)} it, final {L[-1]:.8f}",
            )
            rej = np.r_[False, np.diff(L) == 0]
            ax.semilogy(it[rej], gap[rej], "x", color="k", ms=7)
            ax2.plot(it, r["dt"], "-o", ms=3, color=c)
            meta[lab] = dict(
                log=path,
                n_iter=r["n_iter"],
                result=r["result"],
                n_rejected=r.get("n_rejected"),
            )
        ax.set_ylabel("loss - min(loss of that run)")
        ax.set_title(f"{fit}: main-fit loss history (x = rejected step)", fontsize=10)
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)
        ax2.set_ylabel("dt per iteration [s]")
        ax2.set_xlabel("iteration")
        ax2.grid(alpha=0.3)
        fig.tight_layout()
        save_plot(
            outdir=args.outdir,
            basename=f"loss_history_{fit}",
            fig=fig,
            args=args,
            meta_info=meta,
        )
        plt.close(fig)


if __name__ == "__main__":
    main()
