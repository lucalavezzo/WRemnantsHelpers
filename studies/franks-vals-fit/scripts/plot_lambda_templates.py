"""Plot lambda template variations from the FranksVals histmaker output.

For each NP variation pair (Up vs Down), draws the ratio template/nominal
projected to gen massVgen.  The visual asymmetry of Up/nominal vs
nominal/Down quantifies the template asymmetry that gets squashed by
default --symmetrizeTheoryUnc=quadratic.

Reads gen_massVgen_..._Corr from the histmaker hdf5 (no qT axis since
this projection marginalizes qT; the asymmetry visible here reflects
the asymmetry of the underlying template *per qT bin* convoluted with
the gen ptll spectrum).
"""

import argparse
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import mplhep as hep
import h5py
from wums import ioutils

hep.style.use("CMS")

INFILE_DEFAULT = "/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Theorymodels/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"

# Variation pairs to plot. Each tuple: (Up_label, Down_label, display_title,
# nominal_central_for_title, up_phys, down_phys)
PAIRS = [
    (
        "lambda21.0",
        "lambda20.0",
        r"TMD $\Lambda_2$ ($+0.6 / -0.4$ around 0.4)",
        0.40,
        1.00,
        0.00,
    ),
    (
        "lambda41.0",
        "lambda40.0",
        r"TMD $\Lambda_4$ ($+0.6 / -0.4$ around 0.4)",
        0.40,
        1.00,
        0.00,
    ),
    (
        "lambda2_nu0.25",
        "lambda2_nu0.05",
        r"CS $\gamma\,\lambda_2$ ($\pm 0.1$ around 0.15)",
        0.15,
        0.25,
        0.05,
    ),
    (
        "delta_lambda20.02",
        "delta_lambda2-0.02",
        r"TMD $\Delta\Lambda_2$ ($\pm 0.02$ around 0.0)",
        0.00,
        0.02,
        -0.02,
    ),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--infile", default=INFILE_DEFAULT, help="histmaker hdf5")
    ap.add_argument(
        "--hist",
        default="gen_massVgen_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_Corr",
        help="corr histogram name in the histmaker output",
    )
    ap.add_argument("--proc", default="Zmumu_2016PostVFP", help="process group")
    ap.add_argument("-o", "--output", required=True, help="output directory")
    args = ap.parse_args()

    os.makedirs(args.output, exist_ok=True)

    f = h5py.File(args.infile, "r")
    res = {k: ioutils.pickle_load_h5py(v) for k, v in f.items()}
    h = res[args.proc]["output"][args.hist].get()
    print(f"Loaded {args.hist}: axes = {[a.name for a in h.axes]}")

    vars_axis = h.axes["vars"]
    var_labels = list(vars_axis)
    nominal_label = "pdf0"
    if nominal_label not in var_labels:
        sys.exit(f"Could not find nominal '{nominal_label}' in vars axis")

    massVgen_ax = h.axes["massVgen"]
    centers = 0.5 * (
        np.asarray(massVgen_ax.edges)[:-1] + np.asarray(massVgen_ax.edges)[1:]
    )

    nom_vals = h[{"vars": nominal_label}].values()

    # Filter pairs that exist in this hist
    plot_pairs = []
    for up_lbl, dn_lbl, title, n_phys, u_phys, d_phys in PAIRS:
        if up_lbl in var_labels and dn_lbl in var_labels:
            plot_pairs.append((up_lbl, dn_lbl, title, n_phys, u_phys, d_phys))
        else:
            print(
                f"WARNING: missing labels for {title}: up={up_lbl!r}, down={dn_lbl!r}"
            )

    n = len(plot_pairs)
    if n == 0:
        sys.exit("No variation pairs found")
    fig, axes = plt.subplots(n, 1, figsize=(8, 3.0 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for ax, (up_lbl, dn_lbl, title, n_phys, u_phys, d_phys) in zip(axes, plot_pairs):
        up_ratio = np.divide(
            h[{"vars": up_lbl}].values(),
            nom_vals,
            out=np.zeros_like(nom_vals),
            where=nom_vals != 0,
        )
        dn_ratio = np.divide(
            h[{"vars": dn_lbl}].values(),
            nom_vals,
            out=np.zeros_like(nom_vals),
            where=nom_vals != 0,
        )
        # Convert to fractional deviation (template/nominal - 1) in %
        up_pct = (up_ratio - 1.0) * 100.0
        dn_pct = (dn_ratio - 1.0) * 100.0

        ax.plot(
            centers,
            up_pct,
            color="tab:red",
            lw=2,
            label=f"Up:   {up_lbl} (phys = {u_phys:+.2f})",
        )
        ax.plot(
            centers,
            dn_pct,
            color="tab:blue",
            lw=2,
            label=f"Down: {dn_lbl} (phys = {d_phys:+.2f})",
        )
        # Hypothetical symmetric "mirror" of Down to compare to Up.
        ax.plot(
            centers,
            -dn_pct,
            color="tab:blue",
            lw=1,
            ls="--",
            label=r"$-$Down  (symmetrize-around-nominal hypothesis)",
        )

        ax.axhline(0.0, color="k", lw=0.5)
        ax.set_ylabel("template/nominal $-1$ [\\%]")
        ax.set_title(f"{title}    nominal phys $= {n_phys:+.2f}$")
        ax.legend(fontsize=8, loc="best")
        ax.grid(alpha=0.3)

    axes[-1].set_xlabel(r"$m_{V,\mathrm{gen}}$ [GeV]")
    fig.suptitle(
        "FranksVals NP templates: up vs down asymmetry (gen $m_{V}$ projection)",
        y=1.0,
        fontsize=12,
    )
    fig.tight_layout()

    outpath_pdf = os.path.join(args.output, "lambda_templates_franksvals.pdf")
    outpath_png = os.path.join(args.output, "lambda_templates_franksvals.png")
    fig.savefig(outpath_pdf, bbox_inches="tight")
    fig.savefig(outpath_png, dpi=120, bbox_inches="tight")
    print(f"Wrote {outpath_pdf}")
    print(f"Wrote {outpath_png}")

    # Quantitative summary: integrated asymmetry per pair.
    # A_int = sum_i (Up_i - nom_i) / sum_i (nom_i - Down_i)
    # If A_int == 1, the integrated up/down magnitudes match (symmetric).
    # Print to stdout for inclusion in the runlog.
    print()
    print("Integrated asymmetry (mass-marginalized):")
    print(
        f"  {'pair':40s}  {'up_int [%]':>10s}  {'dn_int [%]':>10s}  {'|up|/|dn|':>8s}"
    )
    for up_lbl, dn_lbl, title, n_phys, u_phys, d_phys in plot_pairs:
        up_vals = h[{"vars": up_lbl}].values()
        dn_vals = h[{"vars": dn_lbl}].values()
        up_int = (np.sum(up_vals) - np.sum(nom_vals)) / np.sum(nom_vals) * 100
        dn_int = (np.sum(dn_vals) - np.sum(nom_vals)) / np.sum(nom_vals) * 100
        ratio = abs(up_int) / abs(dn_int) if dn_int != 0 else float("inf")
        print(f"  {title[:40]:40s}  {up_int:+10.4f}  {dn_int:+10.4f}  {ratio:8.3f}")


if __name__ == "__main__":
    main()
