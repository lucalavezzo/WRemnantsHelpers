#!/usr/bin/env python3
"""The CS kernel under a lattice PRIOR, against the wall and the free fit.

The question is about a FUNCTION, not about two numbers: does the fit's
gamma_nu^NP(b_T) sit inside the band the lattice determination allows, and does
it stay damping (<= 0)? So the figure draws the lattice band itself -- the
conditional 2x2 read back out of the card's own external term, propagated
through the tanh with the full correlation -- and puts every arm's postfit
curve on it.

Formulas transcribed from the SCETlib source the fit LINKS
(scetlib-audit-b66f8de include/scetlib/qT/{Gamma_nu,NP_models}_formulas.hpp,
tanh_2 branches), not from AN-25-085 eq. (eq:npf); both are called with the raw
b_T, since b0_over_bmax_global = 0 makes b* the identity here.

NB the CONVENTION: this plots gamma_nu^NP = -lambda_inf_nu * tanh(A), which is
2x the gamma_zeta^NP that lattice papers draw (knowledge note section 13). The
lattice band here is drawn in OUR gamma_nu convention, i.e. the parameters are
used exactly as the fit uses them -- no factor is applied anywhere.

Bare matplotlib (analytic curves over continuous b_T, not histograms); the SAVE
goes through the wums helpers, which is the png/pdf/.log/index.php contract
scetlib_np's save_plot wraps (that package is not on this branch).

usage: plot_np_forms_lattice.py <outdir> <lattice_fitresult.hdf5>
"""
import sys

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD = f"{CEPH}/study_scratch/260910-anchor-verify/card_none.hdf5"
LATCARD = f"{CEPH}/study_scratch/260911-lattice/card_latticeCS.hdf5"
PLAIN = f"{CEPH}/260910_blinding_final/fitresults_DATABLIND.hdf5"
WALLED = f"{CEPH}/260910_wall_port/fitresults_DATAWALL5.hdf5"

from rabbit import inputdata, io_tools  # noqa: E402
from wums import output_tools, plot_tools  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402


def gamma_nu_np(bT, p):
    b2 = bT**2
    arg = (p["lambda2_nu"] + p["lambda4_nu"] * b2) * b2 / p["lambda_inf_nu"]
    return -p["lambda_inf_nu"] * np.tanh(arg)


def f_np(bT, Y, p):
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
    return {
        n: (
            float(wall.physical_from_theta(inp["specs"][n], theta[n]))
            if n in theta
            else float(inp["anchors"][n])
        )
        for n in inp["names"]
    }


def lattice_prior(inp):
    """(mu_phys, cov_phys) for (lambda2_nu, lambda4_nu), out of the card."""
    with h5py.File(LATCARD, "r") as f:
        tg = f["external_terms"]["lattice_cs"]
        names = [s.decode() if isinstance(s, bytes) else s for s in tg["params"][...]]
        g = np.asarray(tg["grad_values"][...])
        H = np.asarray(tg["hess_dense"][...]).reshape(len(names), len(names))
    C_t = np.linalg.inv(H)
    mu_t = -C_t @ g
    w = np.array([inp["specs"][n][1][1] for n in names])
    c0 = np.array([inp["specs"][n][1][0] for n in names])
    return names, c0 + w * mu_t, np.diag(w) @ C_t @ np.diag(w)


def main():
    outdir, latfit = sys.argv[1], sys.argv[2]
    inp = wall.resolve_wall_inputs(inputdata.FitInputData(CARD))
    lat_names, lat_mu, lat_cov = lattice_prior(inp)
    assert lat_names == ["lambda2_nu", "lambda4_nu"], lat_names

    tunes = [
        ("card anchor (FranksVals)", tune(inp, None), "k", "-"),
        ("free fit (plain)", tune(inp, PLAIN), "tab:red", "--"),
        (r"walled ($\tau=5$)", tune(inp, WALLED), "tab:green", "-."),
        ("lattice prior", tune(inp, latfit), "tab:blue", "-"),
    ]
    for label, p, _, _ in tunes:
        print(f"{label}: " + ", ".join(f"{k}={v:.6g}" for k, v in p.items()))
    print(f"lattice prior (physical): mu {lat_mu}  sigma {np.sqrt(np.diag(lat_cov))}")

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
    linf_nu = float(inp["anchors"]["lambda_inf_nu"])

    # lattice band: linear propagation of the conditional 2x2 through the tanh
    p_lat = {"lambda2_nu": lat_mu[0], "lambda4_nu": lat_mu[1], "lambda_inf_nu": linf_nu}
    g_lat = gamma_nu_np(bT, p_lat)
    A = (lat_mu[0] + lat_mu[1] * bT**2) * bT**2 / linf_nu
    sech2 = 1.0 / np.cosh(A) ** 2
    J = np.stack([-sech2 * bT**2, -sech2 * bT**4], axis=1)
    var = np.einsum("bi,ij,bj->b", J, lat_cov, J)
    sig = np.sqrt(np.maximum(var, 0.0))

    fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.2))
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
            (-0.35, 0.03),
            r"same, zoomed on the small-$b_T$ turn-on",
        ),
    ):
        ax.fill_between(
            bT,
            g_lat - sig,
            g_lat + sig,
            color="tab:blue",
            alpha=0.18,
            lw=0,
            label=r"lattice $\pm1\sigma$ (conditional 2$\times$2)",
        )
        ax.plot(bT, g_lat, color="tab:blue", lw=1.0, alpha=0.6, ls=":")
        for label, p, c, ls in tunes:
            ax.plot(bT, gamma_nu_np(bT, p), color=c, ls=ls, lw=1.8, label=label)
        ax.axhline(0.0, color="0.55", lw=0.9)
        ax.set_xlim(*xlim)
        if ylim is not None:
            ax.set_ylim(*ylim)
            ax.axhspan(0.0, ylim[1], color="tab:red", alpha=0.07, lw=0)
            ax.text(
                0.03,
                0.10,
                "anti-damping",
                transform=ax.transAxes,
                fontsize=7.5,
                color="tab:red",
                va="bottom",
            )
        ax.set_xlabel(r"$b_T$ [GeV$^{-1}$]")
        ax.set_ylabel(r"$\tilde\gamma_\nu^{\rm NP}(b_T)$")
        ax.set_title(ttl)
        ax.legend(loc="lower left")

    for ax, Y in ((axes[1][0], 0.0), (axes[1][1], inp["ymax"])):
        for label, p, c, ls in tunes:
            ax.plot(bT, f_np(bT, Y, p), color=c, ls=ls, lw=1.8, label=label)
        ax.axhline(1.0, color="0.55", lw=0.9)
        ax.set_xlabel(r"$b_T$ [GeV$^{-1}$]")
        ax.set_ylabel(r"$f^{\rm NP}(b_T, Y)$")
        ax.set_title(f"TMD b.c. at $|Y|={Y:g}$ (NO external constraint exists)")
        ax.set_yscale("log")
        ax.set_ylim(1e-3, 2.0)
        ax.legend(loc="lower left")

    fig.suptitle(
        "SCETlib NP form factors (tanh_2), blinded data fits: free vs walled vs "
        "lattice-prior",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    meta = {
        "card": CARD,
        "lattice_card": LATCARD,
        "plain_fitresult": PLAIN,
        "walled_fitresult": WALLED,
        "lattice_fitresult": latfit,
        "np_model": inp["np_model"],
        "np_model_nu": inp["np_model_nu"],
        "binding_absY": inp["ymax"],
        "lattice_prior_physical": {
            "params": lat_names,
            "mu": lat_mu.tolist(),
            "cov": lat_cov.tolist(),
        },
        "convention": "gamma_nu = 2 x gamma_zeta; lattice band drawn in gamma_nu",
        "formulas": (
            "scetlib-audit-b66f8de include/scetlib/qT/"
            "{Gamma_nu,NP_models}_formulas.hpp, tanh_2"
        ),
        "tunes": {label: p for label, p, _, _ in tunes},
    }
    plot_tools.save_pdf_and_png(outdir, "np_form_factors_lattice", fig=fig)
    output_tools.write_index_and_log(
        outdir, "np_form_factors_lattice", analysis_meta_info=meta, args=None
    )
    print(f"wrote {outdir}/np_form_factors_lattice.png / .pdf / .log")

    # --- the (lambda2_nu, lambda4_nu) plane: prior ellipse + the four tunes ---
    fig2, ax = plt.subplots(figsize=(5.6, 5.0))
    th = np.linspace(0, 2 * np.pi, 400)
    ev, evec = np.linalg.eigh(lat_cov)
    for k, nsig in enumerate((1, 2, 3)):
        pts = lat_mu[:, None] + nsig * (
            evec @ (np.sqrt(ev)[:, None] * np.stack([np.cos(th), np.sin(th)]))
        )
        ax.plot(
            pts[0],
            pts[1],
            color="tab:blue",
            lw=1.0,
            alpha=0.8 - 0.2 * k,
            label=f"lattice {nsig}$\\sigma$" if k == 0 else None,
        )
    ax.plot(*lat_mu, "P", color="tab:blue", ms=9, label="lattice prior mean")
    for label, p, c, _ in tunes:
        ax.plot(p["lambda2_nu"], p["lambda4_nu"], "o", color=c, ms=7, label=label)
    ax.axhline(0.0, color="0.7", lw=0.8)
    ax.axvline(0.0, color="0.7", lw=0.8)
    ax.set_xlabel(r"$\lambda_2^\nu$ [GeV$^2$]")
    ax.set_ylabel(r"$\lambda_4^\nu$ [GeV$^4$]")
    ax.set_title("CS-kernel parameters: lattice prior vs the fitted tunes")
    ax.legend(fontsize=7)
    fig2.tight_layout()
    plot_tools.save_pdf_and_png(outdir, "cs_lambda_plane", fig=fig2)
    output_tools.write_index_and_log(
        outdir, "cs_lambda_plane", analysis_meta_info=meta, args=None
    )
    print(f"wrote {outdir}/cs_lambda_plane.png / .pdf / .log")
    print("PLOT_LATTICE_DONE")


if __name__ == "__main__":
    main()
