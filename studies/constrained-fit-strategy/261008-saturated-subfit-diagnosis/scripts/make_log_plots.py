#!/usr/bin/env python3
"""Figures from the logs alone (cost_breakdown.json, step_classes.json). No cache, no fit.

  subfit_progress : q still to go, 2 (loss - final), vs minimiser wall time, SATB8 / SATB8SA / SATC2 (live, measured
                    against SATB8's final); horizontal lines at the q accuracies that matter for a p-value.
  subfit_dt       : dt per iteration of SATB8 and SATB8SA, coloured by step class, with the estimated HVPs of the
                    deep solves on a second axis.
Not histograms (iteration traces), so bare matplotlib, saved through save_plot.
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot  # noqa: E402

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cb = json.load(open(f"{T}/cost_breakdown.json"))
sc = json.load(open(f"{T}/step_classes.json"))
START = 376.6751
FINAL = cb["SATB8"]["final"]
META = dict(
    note="log parsing only; q = 2*(loss - SATB8 final 337.47616205812)",
    logs={
        k: v
        for k, v in [
            ("SATB8", "261007_lattice_term_native/SATB8.log"),
            ("SATB8SA", "261007_lattice_term_native/SATB8SA.log"),
            ("SATC2", "261008_c2_wall_test/SATC2.log"),
            ("SATP", "261008_saturated_subfit_diag/SATP.log"),
        ]
    },
)
COL = dict(SATB8="#1f77b4", SATB8SA="#d62728", SATC2="#2ca02c", SATP="#9467bd")
LAB = dict(
    SATB8="SATB8 (relu$^2$, warm start)",
    SATB8SA="SATB8SA (relu$^2$, --saturatedSeed all)",
    SATC2="SATC2 (C$^2$ wall, warm start)",
    SATP="SATP (relu$^2$, warm start, full spectral preconditioner)",
)
CC = dict(
    rejected="#7f7f7f",
    ladder="#ff7f0e",
    polish="#9467bd",
    big="#1f77b4",
    other="#bcbd22",
)


def progress():
    plt.rcdefaults()
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
    for k in ["SATB8", "SATB8SA", "SATC2", "SATP"]:
        rows = cb[k]["rows"]
        L = np.r_[START, [r["loss"] for r in rows]]
        el = np.r_[0, np.cumsum([r["dt"] for r in rows])] / 3600
        it = np.arange(len(L))
        q = np.maximum(2 * (L - FINAL), 1e-9)
        if (
            k == "SATB8SA"
        ):  # seeded: its iteration 0 starts from the seed (logged 341.79), not from the warm start
            q, el, it = q[1:], el[1:], it[1:]
        ax[0].semilogy(el, q, "-", color=COL[k], label=LAB[k], lw=1.4)
        ax[1].semilogy(it, q, "-", color=COL[k], label=LAB[k], lw=1.4)
    for a in ax:
        for y, s in [(0.1, "q to 0.1"), (0.01, "q to 0.01")]:
            a.axhline(y, color="k", ls=":", lw=0.8)
            a.text(
                a.get_xlim()[1] if False else 0.02,
                y * 1.15,
                s,
                transform=a.get_yaxis_transform(),
                fontsize=8,
            )
        a.set_ylabel("q still to go = 2 (loss $-$ final)")
        a.set_ylim(1e-9, 200)
        a.grid(alpha=0.3)
    ax[0].set_xlabel("sub-fit minimiser wall time [h]")
    ax[1].set_xlabel("iteration")
    ax[0].legend(fontsize=8, loc="lower left")
    ax[0].set_title("projected-ptll saturated sub-fit at LATB8: progress", fontsize=10)
    ax[1].set_title(
        "same, per iteration (q = 78.4 total; start = LATB8 minimum)", fontsize=10
    )
    fig.tight_layout()
    save_plot(T, "subfit_progress", fig=fig, meta_info=META)


def dts():
    plt.rcdefaults()
    fig, ax = plt.subplots(3, 1, figsize=(13, 10), sharex=False)
    for a, k in zip(ax, ["SATB8", "SATB8SA", "SATP"]):
        rows = cb[k]["rows"]
        dt = np.array([r["dt"] for r in rows])
        cls = sc[k]["cls"]
        x = np.arange(len(dt))
        a.bar(x, dt, color=[CC[c] for c in cls], width=0.9)
        a.set_yscale("log")
        a.set_ylim(1, 4000)
        a.set_ylabel("dt [s]")
        th, tf_ = cb[k]["t_h"], cb[k]["t_f"]
        sec = a.secondary_yaxis(
            "right",
            functions=(
                lambda d, th=th, tf_=tf_: np.maximum(d - tf_, 1e-3) / th,
                lambda h, th=th, tf_=tf_: h * th + tf_,
            ),
        )
        sec.set_yticks([1, 3, 10, 30, 100, 300])
        sec.set_yticklabels(["1", "3", "10", "30", "100", "300"])
        sec.set_ylabel(f"~HVPs in the solve (t_f={tf_:.0f} s, t_HVP={th:.1f} s)")
        a.set_title(
            f"{LAB[k]}: {len(dt)} iterations, {dt.sum()/3600:.2f} h, nhev={cb[k]['counters']['nhev']} "
            f"({100*cb[k]['time_in_hvp_frac']:.0f} % of the time in HVPs)",
            fontsize=10,
        )
        a.grid(alpha=0.3, axis="y")
        a.set_xlabel("iteration")
    handles = [plt.Rectangle((0, 0), 1, 1, color=v) for v in CC.values()]
    ax[0].legend(handles, list(CC), fontsize=8, ncol=5, loc="upper left")
    fig.tight_layout()
    save_plot(T, "subfit_dt", fig=fig, meta_info=META)


if __name__ == "__main__":
    progress()
    dts()
