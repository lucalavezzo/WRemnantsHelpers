#!/usr/bin/env python3
"""Draw the two NP form factors at the anchor, the unwalled tune, the walled tune.

The point of the wall is a statement about FUNCTIONS, not about parameters, so
this is the figure that shows whether it did its job: gamma_nu^NP(bT) must stay
<= 0 and f^NP(bT, Y) must decay, at every rapidity the fit evaluates.

The formulas are transcribed from the SCETlib source the fit links --
scetlib-audit-b66f8de/include/scetlib/qT/{Gamma_nu,NP_models}_formulas.hpp,
tanh_2 branches -- NOT from AN-25-085 Eq. (eq:npf), whose L2^3 term carries one
power of lambda_inf where the source carries three (lambda_inf = 1 here, so it
does not matter numerically, but the wall's condition is written in the source's
convention). Both are called with the RAW bT: Gamma_nu.cpp passes b* only to the
perturbative logarithm, and this cache has b0_over_bmax_global = 0.

Bare matplotlib rather than wums.plot_tools on purpose -- these are analytic
curves over a continuous bT, not histograms, which is what plot_tools' entry
points take. The SAVE still goes through the wums helpers
(save_pdf_and_png + write_index_and_log), which is what scetlib_np's save_plot
wraps, so the png/pdf/.log/index.php gallery contract is unchanged. That package
is not checked out on this branch, hence the direct call.

usage: plot_np_forms.py <outdir> <walled_fitresult.hdf5>
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

CARD = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
    "study_scratch/260910-anchor-verify/card_none.hdf5"
)
UNWALLED = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
    "260910_blinding_final/fitresults_DATABLIND.hdf5"
)

from rabbit import inputdata, io_tools  # noqa: E402
from wums import output_tools, plot_tools  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402


def gamma_nu_np(bT, p):
    """SCETlib gamma_nu_np_model, tanh_2 branch. Damping means <= 0."""
    b2 = bT**2
    arg = (p["lambda2_nu"] + p["lambda4_nu"] * b2) * b2 / p["lambda_inf_nu"]
    return -p["lambda_inf_nu"] * np.tanh(arg)


def f_np(bT, Y, p):
    """SCETlib np_effective, tanh_2 branch. Damping means decaying, <= 1."""
    linf = p["lambda_inf"]
    l2Y = p["lambda2"] + p["delta_lambda2"] * Y**2
    arg = (l2Y + p["lambda4"] * bT**2) * bT / linf
    arg = arg + (l2Y * bT / linf) ** 3 / 3.0
    return np.exp(-2.0 * linf * bT * np.tanh(arg))


def tune(inp, fitresult):
    if fitresult is None:
        return {n: float(inp["anchors"][n]) for n in inp["names"]}
    h = io_tools.get_fitresult(fitresult)["parms"].get()
    names = [str(n) for n in h.axes[0]]
    vals = h.values()
    theta = {n: float(vals[i]) for i, n in enumerate(names)}
    out = {}
    for n in inp["names"]:
        out[n] = (
            float(wall.physical_from_theta(inp["specs"][n], theta[n]))
            if n in theta
            else float(inp["anchors"][n])
        )
    return out


def main():
    outdir, walled = sys.argv[1], sys.argv[2]
    inp = wall.resolve_wall_inputs(inputdata.FitInputData(CARD))
    tunes = [
        ("anchor (lattice tune)", tune(inp, None), "k", "-"),
        ("unwalled data fit", tune(inp, UNWALLED), "tab:red", "--"),
        (r"walled data fit ($\tau=5$)", tune(inp, walled), "tab:blue", "-"),
    ]
    for label, p, _, _ in tunes:
        print(f"{label}: " + ", ".join(f"{k}={v:.6g}" for k, v in p.items()))

    # wums pulls in the mplhep CMS style, whose default font sizes are set for
    # a single big panel; these are multi-panel diagnostics, so bring them down
    # or the axis titles overlap into unreadability.
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 9,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 7.5,
        }
    )

    bT = np.linspace(1e-4, 3.0, 2000)
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.2))

    # --- CS kernel, full range and zoomed on the small-bT turn-on. The zoom is
    # the panel that matters: the anti-damping excursion is O(0.02) against a
    # -2 asymptote, so on the full-range axis it is invisible.
    for ax, xlim, ylim, ttl in (
        (
            axes[0][0],
            (0.0, 3.0),
            None,
            r"CS kernel $\tilde\gamma_\nu^{\rm NP}$: damping requires $\leq 0$",
        ),
        (
            axes[0][1],
            (0.0, 1.5),
            (-0.06, 0.03),
            r"same, zoomed on the small-$b_T$ turn-on",
        ),
    ):
        for label, p, c, ls in tunes:
            ax.plot(bT, gamma_nu_np(bT, p), color=c, ls=ls, lw=1.8, label=label)
        ax.axhline(0.0, color="0.55", lw=0.9)
        ax.set_xlim(*xlim)
        if ylim is not None:
            ax.set_ylim(*ylim)
            ax.axhspan(0.0, ylim[1], color="tab:red", alpha=0.07, lw=0)
            ax.text(
                0.03,
                0.93,
                "anti-damping\n($\\tilde\\gamma_\\nu^{\\rm NP} > 0$)",
                transform=ax.transAxes,
                fontsize=7.5,
                color="tab:red",
                va="top",
            )
        ax.set_xlabel(r"$b_T$ [GeV$^{-1}$]")
        ax.set_ylabel(r"$\tilde\gamma_\nu^{\rm NP}(b_T)$")
        ax.set_title(ttl)
        ax.legend(loc="lower left")

    # --- TMD boundary condition at the two rapidities the wall evaluates.
    for ax, Y in ((axes[1][0], 0.0), (axes[1][1], inp["ymax"])):
        for label, p, c, ls in tunes:
            ax.plot(bT, f_np(bT, Y, p), color=c, ls=ls, lw=1.8, label=label)
        ax.axhline(1.0, color="0.55", lw=0.9)
        ax.set_xlabel(r"$b_T$ [GeV$^{-1}$]")
        ax.set_ylabel(r"$f^{\rm NP}(b_T, Y)$")
        ax.set_title(f"TMD b.c. at $|Y|={Y:g}$: damping requires monotone decay")
        ax.set_yscale("log")
        ax.set_ylim(1e-3, 2.0)
        ax.legend(loc="lower left")

    fig.suptitle(
        "SCETlib nonperturbative form factors (tanh_2) at the physical "
        "$\\lambda$; blinded data fit, 2026-09-10",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    meta = {
        "card": CARD,
        "unwalled_fitresult": UNWALLED,
        "walled_fitresult": walled,
        "np_model": inp["np_model"],
        "np_model_nu": inp["np_model_nu"],
        "binding_absY": inp["ymax"],
        "formulas": (
            "transcribed from scetlib-audit-b66f8de "
            "include/scetlib/qT/{Gamma_nu,NP_models}_formulas.hpp, tanh_2"
        ),
        "tunes": {label: p for label, p, _, _ in tunes},
    }
    # scetlib_np.plot_output.save_plot's two calls, inlined (that package is not
    # checked out on scetlib-ad-param-model).
    plot_tools.save_pdf_and_png(outdir, "np_form_factors", fig=fig)
    output_tools.write_index_and_log(
        outdir, "np_form_factors", analysis_meta_info=meta, args=None
    )
    print(f"wrote {outdir}/np_form_factors.png / .pdf / .log")

    # --- The two TMD damping coefficients vs rapidity. The wall is imposed only
    # at |Y| = 0 and |Y| = ymax; this shows that covers the whole range, since
    # L2 is monotonic in Y^2 and so is the cubic.
    Ys = np.linspace(0.0, inp["ymax"], 400)
    fig2, axes2 = plt.subplots(1, 2, figsize=(9.2, 3.9))
    for label, p, c, ls in tunes:
        l2Y = p["lambda2"] + p["delta_lambda2"] * Ys**2
        cubic = 3.0 * p["lambda_inf"] ** 2 * p["lambda4"] + l2Y**3
        axes2[0].plot(Ys, l2Y, color=c, ls=ls, lw=1.8, label=label)
        axes2[1].plot(Ys, cubic, color=c, ls=ls, lw=1.8, label=label)
    for ax, ttl in (
        (axes2[0], r"$L_2(Y)=\lambda_2+\delta\lambda_2 Y^2 \geq 0$"),
        (axes2[1], r"$3\lambda_\infty^2\lambda_4 + L_2(Y)^3 \geq 0$"),
    ):
        ax.axhline(0.0, color="0.55", lw=0.9)
        ax.axhline(wall.NP_DAMPING_MARGIN, color="0.55", lw=0.9, ls=":")
        ax.set_xlabel("$|Y|$")
        ax.set_title(ttl)
        ax.legend()
    axes2[1].set_ylim(-0.03, 0.12)
    # Never let a curve leave the panel silently: the anchor's cubic is 1.264,
    # a hundred times the window the two fitted tunes need, so say so on the
    # figure rather than letting it read as a missing curve.
    lo, hi = axes2[1].get_ylim()
    off = [
        f"{label}: {3.0 * p['lambda_inf'] ** 2 * p['lambda4'] + p['lambda2'] ** 3:+.3g}"
        for label, p, _, _ in tunes
        if not (lo < 3.0 * p["lambda_inf"] ** 2 * p["lambda4"] + p["lambda2"] ** 3 < hi)
    ]
    if off:
        axes2[1].text(
            0.03,
            0.55,
            "off scale at $|Y|=0$:\n" + "\n".join(off),
            transform=axes2[1].transAxes,
            fontsize=7,
            color="0.3",
            va="top",
        )
    fig2.suptitle(
        "TMD damping coefficients vs rapidity (dotted: the wall's 5e-3 margin)",
        fontsize=10,
    )
    fig2.tight_layout(rect=(0, 0, 1, 0.93))
    plot_tools.save_pdf_and_png(outdir, "tmd_damping_vs_Y", fig=fig2)
    output_tools.write_index_and_log(
        outdir, "tmd_damping_vs_Y", analysis_meta_info=meta, args=None
    )
    print(f"wrote {outdir}/tmd_damping_vs_Y.png / .pdf / .log")
    print("PLOT_NP_FORMS_DONE")


if __name__ == "__main__":
    main()
