#!/usr/bin/env python3
"""Summary figures for studies/constrained-fit-strategy (SUMMARY.tex). Cheap: log parsing + analytic curves only.

  crawl_fix      : loss - NOMSTIFF (376.6146329237086) vs minimiser wall time and vs iteration for
                   CENS03R (relu^2, the original crawl, ENDING at its snapshot: plotted at t <= 0),
                   and C2A (C^2) / R2A (relu^2), both restarted FROM that snapshot (t >= 0), side by side.
                   Logs: 261008-c2-wall-test/logs/{C2A,R2A}.log, CENS03R.log path from 261008-c2-wall-test/scripts/analyze.py.
  wall_penalty   : the per-condition penalty P(x) and its curvature P''(x) for relu^2 and the C^2 ramp
                   (formula of WRemnants 2f1c3df4, np_damping_wall.py; x = violation in the condition's units, d = ramp width).

Run in the WRemnants container (needs wums):  python3 summary_figs/make_summary_figs.py
"""
import os
import re

import wums.plot_tools as plot_tools  # noqa: F401  (import first: it sets the global style)
from wums import output_tools

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NOM = 376.6146329237086  # NOMSTIFF reduced NLL, 261008-c2-wall-test/ref.json
LOGS = {
    "CENS03R": f"{CEPH}/261001_census_nominal/CENS03R.log",
    "R2A": f"{STUDY}/261008-c2-wall-test/logs/R2A.log",
    "C2A": f"{STUDY}/261008-c2-wall-test/logs/C2A.log",
}
PAT = re.compile(
    r"Iteration (\d+): loss ([0-9.eE+-]+)\s+\[dt=([0-9.]+)s elapsed=([0-9.]+)s"
)
COL = {"CENS03R": "#9c9ca1", "R2A": "#5790fc", "C2A": "#e42536"}
LAB = {
    "CENS03R": r"CENS03R: relu$^2$, the original crawl",
    "R2A": r"R2A: relu$^2$ from the snapshot",
    "C2A": r"C2A: C$^2$ ramp from the snapshot",
}


def save_plot(outdir, basename, fig, meta):
    os.makedirs(outdir, exist_ok=True)
    plot_tools.save_pdf_and_png(outdir, basename, fig=fig)
    output_tools.write_index_and_log(
        outdir, basename, analysis_meta_info=meta, args=None
    )


def parse(path):
    it, loss, el = [], [], []
    with open(path, errors="replace") as f:
        for line in f:
            m = PAT.search(line)
            if m:
                it.append(int(m.group(1)))
                loss.append(float(m.group(2)))
                el.append(float(m.group(4)))
    return np.array(it), np.array(loss), np.array(el)


def crawl_fix():
    fig, ax = plt.subplots(
        1, 2, figsize=(24, 8.5), gridspec_kw=dict(width_ratios=[1.15, 1])
    )
    for k in ["CENS03R", "R2A", "C2A"]:
        it, loss, el = parse(LOGS[k])
        y = loss - NOM
        if (
            k == "CENS03R"
        ):  # its history leads TO the snapshot: shift so that it ends at t = 0, iteration 0
            t = (el - el[-1]) / 3600.0
            n = it - it[-1]
        else:
            t = el / 3600.0
            n = it
        ax[0].plot(t, y, "-o", ms=4, lw=2.2, color=COL[k], label=LAB[k])
        ax[1].plot(n, y, "-o", ms=4, lw=2.2, color=COL[k], label=LAB[k])
    for a in ax:
        a.set_yscale("symlog", linthresh=1e-6, linscale=0.6)
        a.axhline(0, color="k", lw=0.8)
        a.axhline(1e-6, color="k", lw=0.6, ls=":")
        a.axvline(0, color="#964a8b", lw=1.0, ls="--")
        a.set_ylim(-1e-4, 3e3)
        a.set_yticks([-1e-5, 0, 1e-6, 1e-4, 1e-2, 1, 1e2])
        a.set_yticklabels(
            [
                r"$-10^{-5}$",
                "0",
                r"$10^{-6}$",
                r"$10^{-4}$",
                r"$10^{-2}$",
                "1",
                r"$10^{2}$",
            ]
        )
        a.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        a.set_ylabel(r"loss $-$ NOMSTIFF loss")
        a.grid(alpha=0.3)
    ax[0].set_xlabel("minimiser wall time since the snapshot [h]")
    ax[1].set_xlabel("iteration since the snapshot")
    ax[0].text(
        -0.08,
        0.80,
        "CENS03R snapshot\n(+430 NLL)",
        transform=ax[0].get_xaxis_transform(),
        fontsize=19,
        color="#964a8b",
        ha="right",
    )
    ax[0].text(ax[0].get_xlim()[0] + 0.1, 1.6e-6, r"NOMSTIFF + $10^{-6}$", fontsize=18)
    ax[0].text(
        -4.3, -3.0e-5, r"C$^2$ ends $1.9\times10^{-5}$ below NOMSTIFF", fontsize=18
    )
    ax[0].legend(fontsize=17, loc="center left", frameon=True)
    fig.tight_layout()
    save_plot(
        HERE,
        "crawl_fix",
        fig,
        dict(
            note="log parsing only; y = loss - NOMSTIFF 376.6146329237086 (symlog, linthresh 1e-6)",
            logs=LOGS,
            nomstiff=f"{CEPH}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
        ),
    )


def wall_penalty():
    d = 1.0
    x = np.linspace(-0.6, 2.6, 801)
    xp = np.clip(x, 0, None)
    P_r2 = xp**2
    P_c2 = (
        np.clip(x, 0, d) ** 3 / (3 * d)
        + np.maximum(x - d, 0) ** 2
        + d * np.maximum(x - d, 0)
    )
    # second derivatives
    Pp_r2 = np.where(x > 0, 2.0, 0.0)
    Pp_c2 = np.where(x <= 0, 0.0, np.where(x < d, 2 * x / d, 2.0))
    fig, ax = plt.subplots(1, 2, figsize=(20, 7))
    ax[0].plot(x, P_r2, color="#5790fc", lw=3, label=r"relu$^2$")
    ax[0].plot(x, P_c2, color="#e42536", lw=3, ls="--", label=r"C$^2$ ramp")
    ax[0].set_ylabel(r"penalty $P(x)$ [$d^2$]")
    ax[0].set_ylim(-0.2, 5.5)
    ax[1].plot(x, Pp_r2, color="#5790fc", lw=3, label=r"relu$^2$ (jump at the face)")
    ax[1].plot(x, Pp_c2, color="#e42536", lw=3, ls="--", label=r"C$^2$ (linear ramp)")
    ax[1].set_ylabel(r"curvature $P''(x)$")
    ax[1].set_ylim(-0.2, 3.0)
    for a in ax:
        a.axvline(0, color="k", lw=0.7)
        a.axvline(d, color="k", lw=0.6, ls=":")
        a.set_xlabel(r"violation $x$  [units of the ramp width $d$]")
        a.legend(fontsize=17, loc="upper left", frameon=True, framealpha=1)
        a.grid(alpha=0.3)
    ax[0].text(-0.58, 0.35, "physical\n(slack)", fontsize=17)
    ax[1].text(1.05, 0.25, r"$x=d$", fontsize=18)
    fig.tight_layout()
    save_plot(
        HERE,
        "wall_penalty",
        fig,
        dict(
            note="analytic; wall NLL term = k * P(x) per condition, k = exp(2 tau); WRemnants 2f1c3df4 np_damping_wall.py"
        ),
    )


if __name__ == "__main__":
    crawl_fix()
    wall_penalty()
