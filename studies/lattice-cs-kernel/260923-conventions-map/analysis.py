"""Numbers + figure for the conventions-map task.

    python analysis.py            (inside the WRemnants singularity, venv active)

Writes analysis_numbers.txt and the figure cs_kernel_ours_vs_lattice.{png,pdf} (+ .log).
"""

import argparse
import importlib.util
import os
import sys

import matplotlib

matplotlib.use("Agg")
from wums import (
    plot_tools,
)  # noqa: E402  (import at top: styles the process, see knowledge/60_plotting_style)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.optimize import brentq  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import our_cs_kernel as K  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "plot_output",
    "/home/submit/lavezzo/alphaS/PR710/WRemnants/wremnants/postprocessing/scetlib_np/plot_output.py",
)
plot_output = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(plot_output)

LATTICE_CSV = "/work/submit/lavezzo/cs_kernel/CS_ASWZ_2024_data-1.csv"
BT = np.array([0.1, 0.15, 0.2, 0.3, 0.45, 0.6, 0.75, 0.9])
PERT = dict(lambda_inf_nu=0.0, lambda2_nu=0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alphas-mz", type=float, default=0.118)
    args = ap.parse_args()
    amz = args.alphas_mz
    lam = K.AN_CRIDGE_TUNE
    out = []
    p = out.append

    # ---------------------------------------------------------------- alpha_s
    c5, c4 = K.Coupling(amz, "fit"), K.Coupling(amz, "lattice")
    p(
        f"alpha_s(mZ)^(5) = {amz}   [4-loop running, m_b(m_b) = {K.MB_MSBAR} GeV, 3-loop decoupling]"
    )
    for mu in (1.0, 1.25, 2.0, 4.18):
        p(
            f"  mu = {mu:5.2f} GeV   alpha_s^(5) = {c5(mu):.4f}   alpha_s^(4) = {c4(mu):.4f}"
        )
    a_target = 0.293
    amz_293 = brentq(lambda a: K.Coupling(a, "lattice")(2.0) - a_target, 0.110, 0.125)
    p(
        f"alpha_s^(4)(2 GeV) = 0.293 (lattice input)  <=>  alpha_s^(5)(mZ) = {amz_293:.4f}"
    )
    for mb in (4.0, 4.78):
        p(
            f"  (threshold at {mb} GeV instead: alpha_s^(4)(2) = {K.Coupling(amz, 'lattice', mb=mb)(2.0):.4f})"
        )
    p("")

    # ---------------------------------------------------------------- kernel table
    pf = K.our_cs_kernel(BT, PERT, amz, scheme="fit", parts=True)
    pl = K.our_cs_kernel(BT, PERT, amz, scheme="lattice", parts=True)
    npk = K.our_cs_kernel(BT, lam, amz, scheme="fit", parts=True)["np"]
    d = 1e-3
    dpf = (
        K.our_cs_kernel(BT, PERT, amz + d, scheme="fit")
        - K.our_cs_kernel(BT, PERT, amz - d, scheme="fit")
    ) / (2 * d)
    dpl = (
        K.our_cs_kernel(BT, PERT, amz + d, scheme="lattice")
        - K.our_cs_kernel(BT, PERT, amz - d, scheme="lattice")
    ) / (2 * d)
    dtn = K.our_cs_kernel(BT, PERT, amz, scheme="fit", tnp_nu=1.0) - pf["pert"]
    dtc = K.our_cs_kernel(BT, PERT, amz, scheme="fit", tnp_cusp=1.0) - pf["pert"]
    n4 = K.our_cs_kernel(BT, PERT, amz, scheme="lattice", order="n4ll") - pl["pert"]
    nnll = K.our_cs_kernel(BT, PERT, amz, scheme="lattice", order="nnll") - pl["pert"]
    # the nf5 -> nf4 difference is mu dependent: evaluate it at mu = 1 GeV too
    d51 = K.our_cs_kernel(BT, PERT, amz, mu=1.0, scheme="fit") - K.our_cs_kernel(
        BT, PERT, amz, mu=1.0, scheme="lattice"
    )
    p(
        "gamma_zeta [lattice normalisation] at mu = 2 GeV, N3LL (N3+0LL, TNPs = 0), AN/Cridge NP tune"
    )
    p(
        " bT[fm]  mu0[GeV] as5(mu0)  pert(nf5,fit) pert(nf4,latt) nf5-nf4 |(nf5-nf4)@mu=1  NP(AN)   full(fit) full(latt) "
        "dpert/das(mZ)[fit,latt]  d/dth_gnu d/dth_cusp  N4LL-N3LL NNLL-N3LL"
    )
    for i, b in enumerate(BT):
        p(
            f" {b:5.2f}  {pf['mu0'][i]:7.3f}  {pf['alphas_mu0'][i]:.4f}   {pf['pert'][i]: .4f}      {pl['pert'][i]: .4f}"
            f"     {pf['pert'][i]-pl['pert'][i]: .4f}   {d51[i]: .4f}        {npk[i]: .4f}  {pf['pert'][i]+npk[i]: .4f}"
            f"   {pl['pert'][i]+npk[i]: .4f}     {dpf[i]: .2f}  {dpl[i]: .2f}           {dtn[i]: .4f}  {dtc[i]: .4f}"
            f"   {n4[i]: .4f}   {nnll[i]: .4f}"
        )
    p("")
    for sig in (0.001, 0.0015):
        p(
            f"delta(alpha_s(mZ)) = {sig}: shift of pert kernel over bT in [0.2, 0.9] fm = "
            f"{np.min(np.abs(dpl[BT >= 0.2]))*sig:.4f} .. {np.max(np.abs(dpl[BT >= 0.2]))*sig:.4f} (lattice scheme)"
        )
    p("")

    # ---------------------------------------------------------------- vs lattice continuum csv (no refit)
    lat = np.genfromtxt(LATTICE_CSV, delimiter=",", skip_header=1)
    bl, gl, el = lat[:, 0], lat[:, 1], lat[:, 2]
    full_l = K.our_cs_kernel(bl, lam, amz, scheme="lattice")
    full_f = K.our_cs_kernel(bl, lam, amz, scheme="fit")
    pert_l = K.our_cs_kernel(bl, PERT, amz, scheme="lattice")
    m = bl >= 0.2
    for tag, th in (
        ("full, lattice scheme (nf=4)", full_l),
        ("full, fit scheme (nf=5)", full_f),
        ("pert only, nf=4", pert_l),
    ):
        chi = ((gl - th) / el) ** 2
        p(
            f"AN tune vs continuum csv, DIAGONAL chi2 [{tag}]: all 21 pts {chi.sum():.1f};  bT>=0.2 fm ({m.sum()} pts) "
            f"{chi[m].sum():.1f}   (csv has NO correlations; points share the k1 shift -> chi2 is indicative only)"
        )
    txt = "\n".join(out)
    print(txt)
    with open(os.path.join(HERE, "analysis_numbers.txt"), "w") as f:
        f.write(txt + "\n")

    # ---------------------------------------------------------------- figure
    bb = np.linspace(0.03, 1.0, 120)
    fig, ax = plot_tools.figure(
        None,
        r"$b_T$ [fm]",
        r"$\gamma_\zeta(b_T, \mu = 2\,\mathrm{GeV})$",
        xlim=(0, 1.0),
        ylim=(-1.6, 0.6),
        automatic_scale=False,
        width_scale=1.25,
    )
    ens = [
        (0, 6, "a = 0.15 fm", "o"),
        (6, 13, "a = 0.12 fm", "s"),
        (13, 21, "a = 0.09 fm", "^"),
    ]
    for lo, hi, lab, mk in ens:
        ax.errorbar(
            bl[lo:hi],
            gl[lo:hi],
            el[lo:hi],
            ls="none",
            marker=mk,
            color="black",
            mfc="white" if mk != "o" else "black",
            label=f"ASWZ 2024, {lab} (a/b$_T$-corrected)",
        )
    ax.plot(
        bb,
        K.our_cs_kernel(bb, lam, amz, scheme="lattice"),
        color="tab:red",
        lw=2,
        label=r"ours, AN tune, $n_f=4$ (lattice scheme)",
    )
    ax.plot(
        bb,
        K.our_cs_kernel(bb, lam, amz, scheme="fit"),
        color="tab:red",
        lw=2,
        ls="--",
        label=r"ours, AN tune, $n_f=5$ (as in the fit)",
    )
    ax.plot(
        bb,
        K.our_cs_kernel(bb, PERT, amz, scheme="lattice"),
        color="tab:blue",
        lw=1.5,
        label=r"ours, perturbative only, $n_f=4$",
    )
    ax.plot(
        bb,
        K.our_cs_kernel(bb, PERT, amz, scheme="fit"),
        color="tab:blue",
        lw=1.5,
        ls="--",
        label=r"ours, perturbative only, $n_f=5$",
    )
    ax.axhline(0, color="grey", lw=0.5)
    ax.text(
        0.02,
        0.03,
        r"N$^3$LL, $\alpha_s(m_Z)=0.118$, $\mu_0$ floor 1 GeV, sextic $b^*$ ($b_0/b_{max}$=1 GeV)"
        "\n"
        "AN tune = Cridge et al. fit to 2023 lattice (unverified, not robust)\n"
        "lattice csv: raw per-point errors, no correlations",
        transform=ax.transAxes,
        fontsize=13,
        va="bottom",
    )
    ax.legend(loc="upper right", fontsize=12)
    plot_tools.add_cms_decor(ax, "Preliminary", data=False, no_energy=True, loc=0)
    plot_output.save_plot(
        outdir=HERE,
        basename="cs_kernel_ours_vs_lattice",
        fig=fig,
        args=args,
        meta_info={
            "lattice_csv": LATTICE_CSV,
            "tune": str(lam),
            "module": "our_cs_kernel.py",
        },
    )


if __name__ == "__main__":
    main()
