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
ALPHA_S_PDG = 0.118
ALPHA_S_SCALING = 0.002
ALPHA_S_TEX = r"$\alpha_{\mathrm{S}}$"
DEFAULT_CENTRAL_PREDS = [
    "scetlib_dyturbo",
    # "scetlib_dyturboMSHT20",
    "scetlib_dyturboN3p1LL",
    "scetlib_dyturboN4p0LL",
    "scetlib_nnlojetN3p1LLN3LO",
    "scetlib_nnlojetN4p0LLN3LO",
]
LABELS = {
    "scetlib_dyturbo": "SCETlib N$^{3+0}$LL + DYTurbo NNLO",
    "scetlib_dyturboMSHT20": "SCETlib N$^{3+0}$LL + DYTurbo NNLO, MSHT20",
    "scetlib_dyturboN3p1LL": "SCETlib N$^{3+1}$LL + DYTurbo NNLO",
    "scetlib_dyturboN4p0LL": "SCETlib N$^{4+0}$LL + DYTurbo NNLO",
    "scetlib_nnlojetN3p1LLN3LO": "SCETlib N$^{3+1}$LL + NNLOjet N$^3$LO",
    "scetlib_nnlojetN4p0LLN3LO": "SCETlib N$^{4+0}$LL + NNLOjet N$^3$LO",
}
XLABELS = {
    "scetlib_dyturbo": "N$^{3+0}$LL + NNLO",
    "scetlib_dyturboMSHT20": "N$^{3+0}$LL + NNLO, MSHT20",
    "scetlib_dyturboN3p1LL": "N$^{3+1}$LL + NNLO",
    "scetlib_dyturboN4p0LL": "N$^{4+0}$LL + NNLO",
    "scetlib_nnlojetN3p1LLN3LO": "N$^{3+1}$LL + N$^3$LO",
    "scetlib_nnlojetN4p0LLN3LO": "N$^{4+0}$LL + N$^3$LO",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot extracted alpha_s values for each prediction ."
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
        default="ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_Zmumu_",
        dest="file_base",
        help="Label for the pred bias test configuration (reported in log output). (Default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(
            os.environ["MY_PLOT_DIR"], datetime.now().strftime("%y%m%d_higher_orders")
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
        "--uncert",
        default="total",
        choices=["total", "contour", "pTModeling"],
        help="Type of uncertainty from the central pred set to normalize by. (Default: %(default)s)",
    )
    parser.add_argument(
        "--ylim",
        nargs=2,
        type=float,
        default=(0.116, 0.120),
        help="Set y-axis limits for the scatter plot. (Default: %(default)s)",
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

    return args


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    results = []
    uncerts = []
    for central_pred in args.central_preds:
        input_file = os.path.join(
            args.input_dir, args.file_base + central_pred, "fitresults.hdf5"
        )
        print(input_file)

        result = f"asimov"
        fitresult, _ = rabbit.io_tools.get_fitresult(
            input_file, result=result, meta=True
        )
        parms = fitresult["parms"].get()

        alphas = parms["pdfAlphaS"].value
        alphas *= ALPHA_S_SCALING
        results.append(alphas)

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
                fitresult["contour_scan"].get()[{"parms": "pdfAlphaS"}].values()[0][0]
            )
        alphas_uncert *= ALPHA_S_SCALING
        uncerts.append(alphas_uncert)

    results_array = np.array(results)
    uncerts_array = np.array(uncerts)

    def format_alphas_value(value, uncert):
        """Return latex-safe alpha_s value with symmetric or asymmetric uncertainty."""
        central_value = ALPHA_S + float(np.squeeze(value))
        uncert_array = np.atleast_1d(uncert).astype(float).flatten()
        if uncert_array.size == 1:
            return f"${central_value:.5f} \\pm {abs(uncert_array[0]):.5f}$"
        lower, upper = uncert_array[0], uncert_array[1]
        return f"${central_value:.5f}^{{+{abs(upper):.5f}}}_{{-{abs(lower):.5f}}}$"

    latex_lines = []
    for central_pred, value, uncert in zip(
        args.central_preds, results_array, uncerts_array
    ):
        latex_lines.append(
            f"{LABELS[central_pred].replace('_', '\\_')} & {format_alphas_value(value, uncert)} \\\\"
        )
    print("\nLaTeX table:\n" + "\n".join(latex_lines))

    # bar plot: bars encode uncertainty, horizontal line marks central value
    fig, ax = plt.subplots(figsize=(8, 7))
    bar_positions = np.arange(len(args.central_preds))
    bar_width = 1.0  # edges touch when x-limits are set to +/-0.5 from first/last bar
    for idx, central_pred in enumerate(args.central_preds):
        central = float(np.squeeze(results_array[idx] + ALPHA_S))
        uncert_array = np.atleast_1d(uncerts_array[idx]).astype(float).flatten()
        if uncert_array.size == 1:
            lower = upper = abs(uncert_array[0])
        else:
            lower, upper = abs(uncert_array[0]), abs(uncert_array[1])
        bottom = central - lower
        height = lower + upper
        ax.bar(
            bar_positions[idx],
            height,
            width=bar_width,
            bottom=bottom,
            color="gray",
            edgecolor="black",
            alpha=0.35,
        )
        ax.plot(
            [
                bar_positions[idx] - bar_width / 2,
                bar_positions[idx] + bar_width / 2,
            ],
            [central, central],
            color="black",
            linewidth=2,
            # label=LABELS[central_pred],
        )
    ax.axhline(
        y=ALPHA_S_PDG,
        color="black",
        label=f"PDG average: " + ALPHA_S_TEX + f"={ALPHA_S_PDG}",
        linestyle="--",
        linewidth=1,
    )
    ax.set_ylabel(ALPHA_S_TEX, loc="center")
    ax.set_xticks(bar_positions)
    ax.set_xticklabels(
        [XLABELS.get(p, p) for p in args.central_preds],
        rotation=45,
        ha="right",
    )
    ax.set_xlim(-0.5, len(args.central_preds) - 0.5)
    if args.ylim:
        ax.set_ylim(args.ylim)
    ax.legend(
        fontsize="small",
        loc="upper center",
    )
    fname = "ho_alphas_results"
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
    print(f"Saved alpha_s bar plot to {output_path}(.pdf)(.png)(.log)")


if __name__ == "__main__":
    main()
