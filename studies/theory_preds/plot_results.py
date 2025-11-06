import argparse
import os
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import mplhep as hep

import rabbit
import rabbit.io_tools
import wums.output_tools
from wremnants import theory_tools

hep.style.use("CMS")

ALPHA_S = 0.118
DEFAULT_CENTRAL_PREDS = [
    "scetlib_dyturboCT18Z_pdfasCorr",
    "scetlib_dyturboMSHT20_pdfasCorr",
    "scetlib_dyturboN3p1LL_pdfasCorr",
    "scetlib_dyturboN4p0LL_pdfasCorr",
    "scetlib_nnlojetN3p1LLN3LO_pdfasCorr",
    "scetlib_nnlojetN4p0LLN3LO_pdfasCorr",
]
DEFAULT_PSEUDODATA_PREDS = [
    "scetlib_dyturboCT18Z_pdfasCorr",
    "scetlib_dyturboMSHT20_pdfasCorr",
    "scetlib_dyturboN3p1LL_pdfasCorr",
    "scetlib_dyturboN4p0LL_pdfasCorr",
    "scetlib_nnlojetN3p1LLN3LO_pdfasCorr",
    "scetlib_nnlojetN4p0LLN3LO_pdfasCorr",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create alpha_s pull heatmaps for the pred bias test."
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        required=True,
        dest="input_dir",
        help=(
            f"Directory containing the directories of fit results, with the format"
            "<input-dir>/<file-base>_<central-pred>/fitresult.hdf5."
            "configured via the script arguments"
            "(Default: None)"
        ),
    )
    parser.add_argument(
        "--file-base",
        default="ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_predBiasTest_Zmumu_",
        dest="file_base",
        help="Label for the pred bias test configuration (reported in log output). (Default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(
            os.environ["MY_PLOT_DIR"], datetime.now().strftime("%y%m%d_pred_bias_test")
        ),
        help=(f"Directory where plots are written. (Default: %(default)s)"),
    )
    parser.add_argument(
        "--central-preds",
        nargs="+",
        default=DEFAULT_CENTRAL_PREDS,
        help="Central preds to include on the y-axis of the heatmap. (Default: %(default)s)",
    )
    parser.add_argument(
        "--pseudodata-preds",
        nargs="+",
        default=DEFAULT_PSEUDODATA_PREDS,
        help="Pseudodata preds to include on the x-axis of the heatmap. (Default: %(default)s)",
    )
    parser.add_argument(
        "--uncert",
        default="total",
        choices=["total", "contour", "pTModeling"],
        help="Type of uncertainty from the central pred set to normalize by. (Default: %(default)s)",
    )
    parser.add_argument(
        "--xlim",
        nargs=2,
        type=float,
        default=None,
        help="Set x-axis limits for the scatter plot. (Default: automatic)",
    )
    parser.add_argument(
        "--postfix",
        default="",
        help="Postfix to add to output filenames. (Default: none)",
    )

    args = parser.parse_args()

    args.input_dir = os.path.abspath(args.input_dir)
    args.output_dir = os.path.abspath(args.output_dir)

    args.central_preds = list(args.central_preds)
    args.pseudodata_preds = list(args.pseudodata_preds)

    return args


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    asym_uncerts = True if args.uncert == "contour" else False

    results = []
    uncerts = []
    for central_pred in args.central_preds:
        this_central_results = []
        this_central_uncerts = []
        input_file = os.path.join(
            args.input_dir, args.file_base + central_pred, "fitresults.hdf5"
        )
        print(input_file)

        for pseudodata_pred in args.pseudodata_preds:
            result = f"nominal_{pseudodata_pred}ByHelicity_vars"
            fitresult, _ = rabbit.io_tools.get_fitresult(
                input_file, result=result, meta=True
            )
            parms = fitresult["parms"].get()

            alphas = parms["pdfAlphaS"].value
            alphas *= 0.0015
            this_central_results.append(alphas)

            if args.uncert == "total":
                alphas_uncert = parms["pdfAlphaS"].variance ** 0.5
            elif args.uncert == "pTModeling":
                alphas_uncert = (
                    fitresult["impacts_grouped"]
                    .get()[{"impacts": f"pTModeling"}]
                    .values()[0]
                )
            elif args.uncert == "contour":
                alphas_uncert = (
                    fitresult["contour_scan"]
                    .get()[{"parms": "pdfAlphaS"}]
                    .values()[0][0]
                )
            alphas_uncert *= 0.0015
            this_central_uncerts.append(alphas_uncert)

        results.append(this_central_results)
        uncerts.append(this_central_uncerts)

    results_array = np.array(results)
    uncerts_array = np.array(uncerts)
    data_to_plot = results_array

    print(f"{args.uncert} uncertainties on pdfAlphaS for Asimov fits:")
    for ipdf in range(len(args.central_preds)):
        for jpdf in range(len(args.pseudodata_preds)):
            if args.central_preds[ipdf] == args.pseudodata_preds[jpdf]:
                uncert = uncerts_array[ipdf, jpdf]
                if asym_uncerts:
                    print(
                        f"{args.central_preds[ipdf]}\t\t"
                        f"+{uncert[1]:.5f}/-{uncert[0]:.5f}"
                    )
                else:
                    print(f"{args.central_preds[ipdf]}\t\t{uncert:.5f}")

    fig, ax = plt.subplots(
        figsize=(
            2 * (len(args.pseudodata_preds) + 2),
            2 * len(args.central_preds),
        )
    )
    mesh = ax.imshow(
        np.abs(data_to_plot),
        origin="lower",
        aspect="auto",
        cmap="viridis",
    )
    cbar = fig.colorbar(mesh, ax=ax)
    if args.uncert == "total":
        cbar.set_label(r"$|\Delta\alpha_S$/$\sigma_{\mathrm{total}}|$")
    elif args.uncert == "pdf-only":
        cbar.set_label(r"$|\Delta\alpha_S$/$\sigma_{\mathrm{central\;PDF\;global}}|$")
    elif args.uncert == "pdf-only-trad":
        cbar.set_label(r"$|\Delta\alpha_S$/$\sigma_{\mathrm{central\;PDF}}|$")

    y_positions = np.arange(len(args.central_preds))
    x_positions = np.arange(len(args.pseudodata_preds))

    ax.set_yticks(y_positions)
    ax.set_yticklabels(
        [pred.replace("_pdfasCorr", "") for pred in args.central_preds],
        rotation=45,
        ha="right",
    )
    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        [pred.replace("_pdfasCorr", "") for pred in args.pseudodata_preds], rotation=45
    )
    ax.set_ylabel("Central pred.", loc="center")
    ax.set_xlabel("Pseudodata pred.", loc="center")

    for x_idx, _ in enumerate(args.pseudodata_preds):
        for y_idx, _ in enumerate(args.central_preds):
            value = np.abs(results_array[y_idx, x_idx])
            uncert = uncerts_array[y_idx, x_idx]
            if asym_uncerts:
                color = "white" if value < uncert[1] else "red"
                ax.text(
                    x_positions[x_idx],
                    y_positions[y_idx],
                    f"{value:.5f}\n$^{{+{uncert[1]:.5f}}}_{{-{uncert[0]:.5f}}}$",
                    ha="center",
                    va="center",
                    color=color,
                    fontsize=14,
                )
            else:
                color = "white" if value < uncert else "red"
                ax.text(
                    x_positions[x_idx],
                    y_positions[y_idx],
                    f"{value:.5f}\n$\\pm${uncert:.5f}",
                    ha="center",
                    va="center",
                    color=color,
                    fontsize=14,
                )

    ax.set_ylim(-0.5, len(args.central_preds) - 0.5)
    ax.set_xlim(-0.5, len(args.pseudodata_preds) - 0.5)

    plt.tight_layout()
    fname = "alphas_heatmap"
    fname += f"_{args.uncert}Uncert"
    if args.postfix:
        fname += f"_{args.postfix}"
    output_path = os.path.join(
        args.output_dir,
        fname,
    )
    fig.savefig(output_path + ".pdf", bbox_inches="tight")
    fig.savefig(output_path + ".png", bbox_inches="tight", dpi=100)
    wums.output_tools.write_index_and_log(
        args.output_dir,
        fname,
    )
    print(f"Saved 2D alpha_s histogram to {output_path}(.pdf)(.png)(.log)")

    # scatter plot
    cmap = plt.get_cmap("tab10")
    colors = cmap(np.linspace(0, 1, len(args.pseudodata_preds)))
    height = 1.5 * len(args.central_preds)
    fig, ax = plt.subplots(
        figsize=(
            15,
            height,
        )
    )
    for central_pred_idx, central_pred in enumerate(args.central_preds):
        for pseudodata_pred_idx, pseudodata_pred in enumerate(args.pseudodata_preds):
            x = results_array[central_pred_idx, pseudodata_pred_idx] + ALPHA_S
            y = central_pred_idx + pseudodata_pred_idx * (
                1 / (len(args.pseudodata_preds) + 3)
            )
            xerr = uncerts_array[central_pred_idx, pseudodata_pred_idx]
            ax.errorbar(
                x,
                y,
                xerr=abs(xerr[..., np.newaxis]),
                fmt="o",
                color=colors[pseudodata_pred_idx],
            )
    ax.axvline(x=ALPHA_S, color="black", linestyle="--")
    ax.set_xlabel(r"$\alpha_S$", loc="center")
    ax.set_ylabel("Central pred", loc="center")
    ax.set_yticks(np.arange(len(args.central_preds)))
    ax.set_yticklabels([pred.replace("_pdfasCorr", "") for pred in args.central_preds])
    ax.legend(
        handles=[
            matplotlib.lines.Line2D(
                [],
                [],
                color=colors[i],
                marker="o",
                linestyle="",
                label=pred.replace("_pdfasCorr", ""),
            )
            for i, pred in enumerate(args.pseudodata_preds)
        ],
        labels=[pred.replace("_pdfasCorr", "") for pred in args.pseudodata_preds],
        loc=(1.01, 0),
        title="Pseudodata pred.",
    )
    if args.xlim:
        ax.set_xlim(args.xlim)
    fname = "alphas_scatter"
    fname += f"_{args.uncert}Uncert"
    if args.postfix:
        fname += f"_{args.postfix}"
    output_path = os.path.join(
        args.output_dir,
        fname,
    )
    fig.tight_layout()
    fig.savefig(output_path + ".pdf", bbox_inches="tight")
    fig.savefig(output_path + ".png", bbox_inches="tight", dpi=100)
    wums.output_tools.write_index_and_log(
        args.output_dir,
        fname,
    )
    print(f"Saved alpha_s scatter plot to {output_path}(.pdf)(.png)(.log)")


if __name__ == "__main__":
    main()
