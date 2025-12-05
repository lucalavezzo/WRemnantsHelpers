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
DEFAULT_CENTRAL_PDFS = [
    "ct18",
    "ct18z",
    "nnpdf31",
    "nnpdf40",
    "pdf4lhc21",
    "msht20",
    "herapdf20",
]
XLABELS = {
    "ct18": "CT18",
    "ct18z": "CT18Z",
    "nnpdf31": "NNPDF3.1",
    "nnpdf40": "NNPDF4.0",
    "pdf4lhc21": "PDF4LHC21",
    "msht20": "MSHT20",
    "herapdf20": "HERAPDF20",
}


def get_pdf_map_name(pdf_key: str) -> str:
    info = theory_tools.pdfMap.get(pdf_key)
    if info:
        return info["name"]
    return f"pdf{pdf_key.upper()}"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot extracted alpha_s values for each PDF ."
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        required=True,
        dest="input_dir",
        help=(
            f"Directory containing the directories of fit results, with the format"
            "<input-dir>/<file-base>_<central-pdf>/fitresult.hdf5."
            "configured via the script arguments"
            "(Default: None)"
        ),
    )
    parser.add_argument(
        "--file-base",
        default="ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_Zmumu_",
        dest="file_base",
        help="Label for the configuration (reported in log output). (Default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(
            os.environ["MY_PLOT_DIR"], datetime.now().strftime("%y%m%d_higher_orders")
        ),
        help=(f"Directory where plots are written. (Default: %(default)s)"),
    )
    parser.add_argument(
        "--central-pdfs",
        nargs="+",
        default=DEFAULT_CENTRAL_PDFS,
        help="Central pdfs to include on the y-axis of the heatmap. (Default: %(default)s)",
    )
    parser.add_argument(
        "--uncert",
        default="pdf-only-trad",
        choices=["total", "pdf-only", "pdf-only-trad", "contour"],
        help="Type of uncertainty from the central PDF set to normalize by. (Default: %(default)s)",
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
    args.central_pdfs = list(args.central_pdfs)

    return args


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    results = []
    uncerts = []
    for central_pdf in args.central_pdfs:
        input_file = os.path.join(
            args.input_dir, args.file_base + central_pdf, "fitresults.hdf5"
        )
        central_pdf_name = get_pdf_map_name(central_pdf)
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
        elif args.uncert == "pdf-only":
            alphas_uncert = (
                fitresult["global_impacts_grouped"]
                .get()[{"impacts": f"{central_pdf_name}NoAlphaS"}]
                .values()[0]
            )
        elif args.uncert == "pdf-only-trad":
            alphas_uncert = (
                fitresult["impacts_grouped"]
                .get()[{"impacts": f"{central_pdf_name}NoAlphaS"}]
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
    for central_pdf, value, uncert in zip(
        args.central_pdfs, results_array, uncerts_array
    ):
        latex_lines.append(
            f"{LABELS[central_pdf].replace('_', '\\_')} & {format_alphas_value(value, uncert)} \\\\"
        )
    print("\nLaTeX table:\n" + "\n".join(latex_lines))

    # bar plot: bars encode uncertainty, horizontal line marks central value
    fig, ax = plt.subplots(figsize=(16, 6))
    bar_positions = np.arange(len(args.central_pdfs))
    bar_width = 1.0  # edges touch when x-limits are set to +/-0.5 from first/last bar
    colors = plt.cm.tab20(np.linspace(0, 1, len(args.central_pdfs)))
    for idx, (central_pdf, color) in enumerate(zip(args.central_pdfs, colors)):
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
            color=color,
            edgecolor="black",
            alpha=0.35,
        )
        ax.plot(
            [
                bar_positions[idx] - bar_width / 2,
                bar_positions[idx] + bar_width / 2,
            ],
            [central, central],
            color=color,
            linewidth=2,
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
        [XLABELS.get(p, p) for p in args.central_pdfs],
        rotation=45,
        ha="right",
    )
    ax.set_xlim(-0.5, len(args.central_pdfs) - 0.5)
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
