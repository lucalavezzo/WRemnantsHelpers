#!/usr/bin/env python3
"""2026-09-24 (Luca): one unambiguous comparison figure, gamma(b_T, mu = 2 GeV).

Curves (each with an explicit provenance legend entry):
  1. data: ASWZ per-ensemble points minus k1*a/b_T with k1 = 0.21365 = the value ASWZ used to build
     the continuum file (CS_ASWZ_2024_data-1.csv); raw diagonal errors; one marker per a.
  2. ASWZ published: Eq. (6)-(8) at a=0, B_NP = 2 GeV^-1, c0 = 0.032 (Eq. 9), band sigma(c0) = 0.012.
  3. our refit of ASWZ Eq. (6)-(8): (c0,k1) fit, full cov (cs_fit.py), dashed, lighter band.
  4. (optional) our SCETlib tanh_2 fit from ../260923-scetlib-kernel-fit (imported, not re-derived):
     n_f = 5, lambda_inf_nu = 2, lambda4_nu = 0, lambda2_nu +- stat+syst; free (l2,l4) fit dotted.
D_res: corrected numeric 4-loop RGE (cs_fit.py --dres numeric); the paper's closed form is checked.

Usage: python3 compare_figure.py [--no-scetlib]
"""
import argparse
import importlib.util
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from wums import plot_tools  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
SK = os.path.join(STUDY, "260923-scetlib-kernel-fit")
sys.path.insert(0, HERE)
import cs_fit as CSF  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


PO = _load(
    "plot_output",
    "/home/submit/lavezzo/alphaS/PR710/WRemnants/wremnants/postprocessing/scetlib_np/plot_output.py",
)

K1_FILE = 0.213649158150396  # = shift/(a/b_T) of the continuum file, identical at all 21 points
C0_PUB, SC0_PUB, BNP = 0.032, 0.012, 2.0


def _plot_py_style():
    """Data style constants of ../260923-scetlib-kernel-fit/plot.py (the postfit-comparison plots).

    plot.py itself can't be imported outside the container (it pulls wremnants -> tensorflow), so the
    literals are read from its source with ast: module-level ENS_COL / ENS_LAB / CMS6 and the first
    `dx = {...}` assignment. Nothing is copied by hand, so a change in plot.py propagates here.
    """
    import ast

    tree = ast.parse(open(os.path.join(SK, "plot.py")).read())
    out = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            n = node.targets[0].id
            if n in ("ENS_COL", "ENS_LAB", "CMS6", "dx") and n not in out:
                out[n] = ast.literal_eval(node.value)
    return out


_S = _plot_py_style()
ENS_COL, ENS_LAB, DX = _S["ENS_COL"], _S["ENS_LAB"], _S["dx"]
COL_SCET = _S["CMS6"][0]  # "#5790fc", the lattice-fit blue of plot.py
COL_PUB, COL_REF = "black", "0.45"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--no-scetlib",
        action="store_true",
        help="theorist-email variant: data + ASWZ + our refit only",
    )
    args = ap.parse_args()
    plt.rcParams.update({"axes.labelsize": 22})

    ens, D = CSF.load()
    b, y, a, cov, s = D["b"], D["y"], D["a"], D["cov"], D["s"]
    # sanity: continuum file k1
    k1f = ((y - D["cont"][:, 1]) / (a / b)).mean()
    assert abs(k1f - K1_FILE) < 1e-9, k1f

    ref = CSF.fit(y, cov, b, a, ["c0", "k1"], BNP=BNP, mode="numeric")
    c0r, sc0r, k1r = ref["theta"]["c0"], ref["err"]["c0"], ref["theta"]["k1"]

    bb = np.linspace(0.03, 1.0, 195)
    off, cols = CSF.design(bb, np.zeros_like(bb), BNP, "numeric")
    offp, _ = CSF.design(bb, np.zeros_like(bb), BNP, "paper")
    g_pub = off + C0_PUB * cols["c0"]
    g_pub_closed = offp + C0_PUB * cols["c0"]
    dmax = np.max(np.abs(g_pub - g_pub_closed))
    print(
        f"published curve, numeric vs closed-form D_res: max |diff| = {dmax:.4f} (b_T in [0.03,1] fm)"
    )
    s_pub = np.abs(cols["c0"]) * SC0_PUB
    g_ref = off + c0r * cols["c0"]
    s_ref = (
        np.abs(cols["c0"]) * sc0r
    )  # a=0: k1 column vanishes, (c0,k1)-cov band == |dg/dc0| sigma(c0)
    print(
        f"our refit: c0={c0r:.4f}({sc0r:.4f}) k1={k1r:.4f} chi2={ref['chi2']:.2f}/{ref['ndf']}"
    )

    fig, ax = plot_tools.figure(
        bb,
        r"$b_T$ [fm]",
        r"$\gamma_q(b_T,\mu=2\,\mathrm{GeV})$",
        ylim=(-2.0, 1.0),
        xlim=(0.0, 1.0),
        automatic_scale=False,
        width_scale=1.3,
    )
    ax.fill_between(
        bb, g_pub - s_pub, g_pub + s_pub, color="0.55", alpha=0.30, lw=0, zorder=1
    )
    ax.plot(
        bb,
        g_pub,
        color=COL_PUB,
        lw=2.2,
        zorder=3,
        label=(
            r"ASWZ published: Eq. (6)-(8), $a$=0, $B_{NP}$=2 GeV$^{-1}$, "
            rf"$c_0$={C0_PUB}$\pm${SC0_PUB} (Eq. 9)"
        ),
    )
    ax.fill_between(
        bb, g_ref - s_ref, g_ref + s_ref, color="0.75", alpha=0.45, lw=0, zorder=2
    )
    ax.plot(
        bb,
        g_ref,
        color=COL_REF,
        lw=2.0,
        ls="--",
        zorder=4,
        label=(
            rf"our refit of ASWZ Eq. (6)-(8): $c_0$={c0r:.4f}$\pm${sc0r:.4f}, "
            rf"$k_1$={k1r:.3f} (full cov)"
        ),
    )
    meta = dict(
        published=f"c0={C0_PUB}+-{SC0_PUB} B_NP={BNP} D_res numeric (closed-form max diff {dmax:.4f})",
        refit=f"cs_fit (c0,k1) numeric: c0={c0r} sc0={sc0r} k1={k1r}",
        points=f"raw - {K1_FILE} a/b_T (continuum-file k1)",
        data="/work/submit/lavezzo/cs_kernel/CS_lattice_results.tar",
    )
    if not args.no_scetlib:
        KF = _load("kernel_fit", os.path.join(SK, "kernel_fit.py"))
        Z = json.load(open(os.path.join(SK, "fit_l4zero.json")))
        L = Z["lambda2_nu"]
        k1s = Z["fits"]["L4=0 | linf=2 | k1 [nominal]"]["x"]["k1"]
        free2 = json.load(open(os.path.join(SK, "fit_results.json")))[
            "tanh2 | linf=2 | k1"
        ]["x"]
        pert = KF.K.our_cs_kernel(bb, {"lambda_inf_nu": 0.0}, mu=2.0, scheme="fit")
        g_s = pert + KF.np_zeta(bb, 2.0, L["central"], 0.0)
        g_lo = pert + KF.np_zeta(bb, 2.0, L["central"] - L["tot"], 0.0)
        g_hi = pert + KF.np_zeta(bb, 2.0, L["central"] + L["tot"], 0.0)
        g_f = pert + KF.np_zeta(bb, 2.0, free2["l2"], free2["l4"])
        ax.fill_between(
            bb,
            np.minimum(g_lo, g_hi),
            np.maximum(g_lo, g_hi),
            color=COL_SCET,
            alpha=0.25,
            lw=0,
            zorder=2,
        )
        ax.plot(
            bb,
            g_s,
            color=COL_SCET,
            lw=2.2,
            zorder=4,
            label=(
                r"our SCETlib tanh$_2$ fit ($n_f$=5): $\lambda_\infty^\nu$=2, $\lambda_4^\nu$=0, "
                rf"$\lambda_2^\nu$={L['central']:.4f}$\pm${L['tot']:.3f} GeV$^2$ (own $k_1$={k1s:.3f})"
            ),
        )
        ax.plot(
            bb,
            g_f,
            color=COL_SCET,
            lw=1.2,
            ls=":",
            zorder=4,
            label=(
                rf"our SCETlib tanh$_2$, free $\lambda_2^\nu$={free2['l2']:.3f}, "
                rf"$\lambda_4^\nu$={free2['l4']:.4f}"
            ),
        )
        meta["scetlib"] = (
            f"l4zero nominal l2={L['central']} tot={L['tot']} k1={k1s}; free l2={free2['l2']} l4={free2['l4']}"
        )
    for e in range(3):
        m = D["ens"] == e
        ax.errorbar(
            b[m] + DX[e],
            y[m] - K1_FILE * a[m] / b[m],
            s[m],
            fmt="o",
            ms=6,
            color=ENS_COL[e],
            zorder=5,
            label=rf"ASWZ lattice {ENS_LAB[e]}, $-k_1 a/b_T$ with $k_1$=0.2136 (ASWZ continuum file)",
        )
    ax.axhline(0, color="0.8", lw=0.8, zorder=0)
    ax.legend(loc="lower left", fontsize=10, frameon=False)
    ax.text(
        0.0,
        1.01,
        r"$\overline{\mathrm{MS}}$, $\mu$ = 2 GeV; lattice errors = diagonal of per-ensemble cov.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=13,
    )
    name = "comparison_aswz_refit" + ("" if args.no_scetlib else "_scetlib")
    PO.save_plot(HERE, name, fig=fig, args=args, meta_info=meta)
    plt.close(fig)


if __name__ == "__main__":
    main()
