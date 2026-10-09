#!/usr/bin/env python3
"""Figures for the Phase-0 diagnosis. Reads logs_parsed.json and surrogate/*.json; no cache, no fit.

zigzag_mechanism : (a) surrogate trust-krylov at tau=8 from the CENS03 seed: trust radius and face value per
                   iteration; (b) the same period-2 gain signature in the REAL CENS03 and CMR1A logs;
tau_scan         : surrogate iterations to converge vs wall stiffness tau, 5 starts, with the real fits at tau=8;
tc_traces        : the real trust-constr fits (barrier mu, optimality, loss above NOMSTIFF, dt).
"""
import glob
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot  # noqa: E402

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUR = f"{TASK}/surrogate"
D = json.load(open(f"{TASK}/logs_parsed.json"))
NOM = 376.6146329237086  # NOMSTIFF walled NLL (NLL is not blinded)
NOM_NOPEN = (
    376.6146254794  # NOMSTIFF without its 7.44e-6 wall penalty (trust-constr objective)
)
META = dict(
    note="no cache load; surrogate = data-only Hessian at TCA + KKT gradient + exact NPDampingWall conditions"
)


def rc():
    plt.rcdefaults()
    plt.rcParams.update({"font.size": 10})


def zigzag():
    rc()
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    h = [x for x in json.load(open(f"{SUR}/tk_pert002_tau8.json"))["hist"] if "f" in x][
        :400
    ]
    k = np.arange(len(h))
    a0 = ax[0]
    a0.semilogy(k, [x["r"] for x in h], color="C0", lw=1, label="trust radius used")
    a0.set_xlabel("iteration")
    a0.set_ylabel("trust radius (theta units)", color="C0")
    a1 = a0.twinx()
    a1.plot(
        k, [x["face"] for x in h], ".", ms=2, color="C3", label="face value L2(|Y|=2.5)"
    )
    a1.axhline(0, color="k", lw=0.5)
    a1.set_ylim(-5e-6, 5e-6)
    a1.set_ylabel("face value  L2(|Y|=2.5)  [GeV$^2$]", color="C3")
    a0.set_title(
        "(a) surrogate, trust-krylov + wall tau=8, start = CENS03 seed\n"
        "radius frozen at 3.8e-6 while the iterate zig-zags across the face",
        fontsize=9,
    )
    for name, sl, c in (
        ("CENS03", slice(80, 129), "C2"),
        ("CMR1A", slice(40, 105), "C1"),
    ):
        loss = np.array([r["loss"] for r in D[name]["rows"]])
        g = -np.diff(loss)
        kk = np.arange(len(g))[sl]
        gg = g[sl]
        m = gg > 0
        ax[1].semilogy(
            kk[m], gg[m], "o-", ms=3, lw=0.7, color=c, label=f"{name} (real fit)"
        )
    ax[1].set_xlabel("iteration")
    ax[1].set_ylabel("loss decrease per iteration")
    ax[1].set_title(
        "(b) real logs: every step accepted, gains alternate\n"
        "(the same period-2 limit cycle), constant rate",
        fontsize=9,
    )
    ax[1].legend(fontsize=8)
    gs = [x for x in json.load(open(f"{SUR}/tk_pert002_tau8.json"))["hist"] if "f" in x]
    gsur = -np.diff([x["f"] for x in gs])[80:129]
    ax[2].semilogy(
        np.arange(80, 80 + len(gsur))[gsur > 0],
        gsur[gsur > 0],
        "o-",
        ms=3,
        lw=0.7,
        color="C0",
        label="surrogate (CENS03 seed, tau=8)",
    )
    ax[2].set_xlabel("iteration")
    ax[2].set_ylabel("loss decrease per iteration")
    ax[2].set_title("(c) surrogate: same signature", fontsize=9)
    ax[2].legend(fontsize=8)
    fig.tight_layout()
    save_plot(TASK, "zigzag_mechanism", fig=fig, meta_info=META)


def tau_scan():
    rc()
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for st, c in zip(
        ("CENS03R", "pert002", "pert000", "cold000", "C1A"),
        ("C0", "C1", "C2", "C3", "C4"),
    ):
        taus, its, fail = [], [], []
        for f in sorted(glob.glob(f"{SUR}/tk_{st}_tau*.json")):
            s = json.load(open(f))["summary"]
            taus.append(s["tau"])
            t = s["to_1e-06"]
            its.append(t["nf"] if t else s["n_f"])
            fail.append(t is None)
        o = np.argsort(taus)
        taus, its, fail = np.array(taus)[o], np.array(its)[o], np.array(fail)[o]
        ax.semilogy(taus, its, "o-", color=c, label=f"start {st}")
        ax.semilogy(taus[fail], its[fail], "x", color="k", ms=10)
    real = dict(CENS01=95, CENS09=90, CENS03="not conv. (390+)")
    ax.scatter(
        [8, 8],
        [95, 90],
        marker="*",
        s=120,
        color="k",
        zorder=5,
        label="real fits at tau=8 (CENS01, CENS09)",
    )
    ax.annotate(
        "real CENS03: not converged\nafter 390 iterations",
        (8, 390),
        (8.3, 1500),
        fontsize=8,
        arrowprops=dict(arrowstyle="->"),
    )
    ax.set_xlabel(r"wall stiffness $\tau$  (penalty $e^{2\tau}\,\mathrm{relu}^2$)")
    ax.set_ylabel("loss+grad evaluations to $f-f^*<10^{-6}$")
    ax.set_title(
        "Surrogate: trust-krylov + relu$^2$ wall vs stiffness\n(x = not converged in 20000)",
        fontsize=9,
    )
    ax.legend(fontsize=7)
    fig.tight_layout()
    save_plot(TASK, "tau_scan", fig=fig, meta_info=dict(META, real=real))


def tc_traces():
    rc()
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    for name, c in (("TCA", "C0"), ("TCB1", "C1"), ("TCB2", "C2")):
        rows = D[name]["rows"]
        k = np.arange(len(rows))
        ax[0].semilogy(
            k,
            [max(r["loss"] - NOM_NOPEN, 1e-7) for r in rows],
            color=c,
            lw=1,
            label=name,
        )
        ax[1].semilogy(
            k,
            [r.get("mu", np.nan) for r in rows],
            color=c,
            lw=1,
            label=f"{name} barrier $\\mu$",
        )
        ax[1].semilogy(
            k,
            [r.get("opt", np.nan) for r in rows],
            color=c,
            lw=1,
            ls=":",
            label=f"{name} optimality",
        )
        ax[2].plot(k, [r["dt"] for r in rows], ".", ms=2, color=c, label=name)
    ax[0].set_ylabel("loss - NOMSTIFF (penalty-free)")
    ax[0].set_title(
        "(a) trust-constr loss above the minimum\n(TCA = warm start AT the minimum)",
        fontsize=9,
    )
    ax[1].axhline(0.1, color="k", lw=0.5)
    ax[1].set_title(
        "(b) barrier parameter (solid) and optimality (dotted)\nstage 1 ends when optimality < 0.1",
        fontsize=9,
    )
    ax[2].set_ylabel("seconds per iteration")
    ax[2].set_ylim(0, 600)
    ax[2].set_title("(c) cost per iteration (t_f ~ 27 s + n_CG x ~13 s)", fontsize=9)
    for a in ax:
        a.set_xlabel("iteration")
        a.legend(fontsize=7)
    fig.tight_layout()
    save_plot(TASK, "tc_traces", fig=fig, meta_info=META)


if __name__ == "__main__":
    zigzag()
    tau_scan()
    tc_traces()
