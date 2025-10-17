import argparse
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

import rabbit
import rabbit.io_tools
import wums.output_tools
from wremnants import theory_tools

DEFAULT_CENTRAL_PDFS = [
    "ct18",
    "ct18z",
    "nnpdf31",
    "nnpdf40",
    "pdf4lhc21",
    "msht20",
    "msht20an3lo",
]
DEFAULT_PSEUDODATA_PDFS = [
    "ct18",
    "ct18z",
    "nnpdf31",
    "nnpdf40",
    "pdf4lhc21",
    "msht20",
    "msht20an3lo",
    "nnpdf30",
]


def get_pdf_map_name(pdf_key: str) -> str:
    info = theory_tools.pdfMap.get(pdf_key)
    if info:
        return info["name"]
    return f"pdf{pdf_key.upper()}"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create alpha_s pull heatmaps for the PDF bias test."
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
        default="ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_pdfBiasTest_Zmumu_",
        dest="file_base",
        help="Label for the PDF bias test configuration (reported in log output). (Default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(
            os.environ["MY_PLOT_DIR"], datetime.now().strftime("%y%m%d_pdf_bias_test")
        ),
        help=(f"Directory where plots are written. (Default: %(default)s)"),
    )
    parser.add_argument(
        "--central-pdfs",
        nargs="+",
        default=DEFAULT_CENTRAL_PDFS,
        metavar="PDF",
        help="Central PDFs to include on the y-axis of the heatmap. (Default: %(default)s)",
    )
    parser.add_argument(
        "--pseudodata-pdfs",
        nargs="+",
        default=DEFAULT_PSEUDODATA_PDFS,
        metavar="PDF",
        help="Pseudodata PDFs to include on the x-axis of the heatmap. (Default: %(default)s)",
    )
    parser.add_argument(
        "--uncert",
        default="central-pdf",
        choices=["total", "central-pdf"],
        help="Type of uncertainty to use for comparison. (Default: %(default)s)",
    )

    args = parser.parse_args()

    args.input_dir = os.path.abspath(args.input_dir)
    args.output_dir = os.path.abspath(args.output_dir)

    args.central_pdfs = list(args.central_pdfs)
    args.pseudodata_pdfs = list(args.pseudodata_pdfs)

    return args


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    results = []
    uncerts = []
    for central_pdf in args.central_pdfs:
        central_pdf_name = get_pdf_map_name(central_pdf)
        this_central_results = []
        this_central_uncerts = []
        input_file = os.path.join(
            args.input_dir, args.file_base + central_pdf, "fitresults.hdf5"
        )
        print(input_file)

        for pseudodata_pdf in args.pseudodata_pdfs:
            result = (
                f"nominal_{get_pdf_map_name(pseudodata_pdf)}UncertByHelicity_pdfVar"
            )
            fitresult, _ = rabbit.io_tools.get_fitresult(
                input_file, result=result, meta=True
            )
            parms = fitresult["parms"].get()
            alphas = abs(parms["pdfAlphaS"].value)
            alphas_uncert = parms["pdfAlphaS"].variance ** 0.5
            pdf_uncert = (
                fitresult["global_impacts_grouped"]
                .get()[{"impacts": f"{central_pdf_name}NoAlphaS"}]
                .values()[0]
            )
            alphas *= 0.0015
            alphas_uncert *= 0.0015
            pdf_uncert *= 0.0015
            this_central_results.append(alphas)
            if args.uncert == "total":
                this_central_uncerts.append(alphas_uncert)
            elif args.uncert == "central-pdf":
                this_central_uncerts.append(pdf_uncert)

        results.append(this_central_results)
        uncerts.append(this_central_uncerts)

    results_array = np.array(results)
    uncerts_array = np.array(uncerts)
    data_to_plot = results_array

    fig, ax = plt.subplots(
        figsize=(
            1.1 * (len(args.pseudodata_pdfs) + 2),
            1.1 * len(args.central_pdfs),
        )
    )
    mesh = ax.imshow(
        data_to_plot,
        origin="lower",
        aspect="auto",
        cmap="viridis",
    )
    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_label(r"$|\Delta\alpha_S$/$\sigma_{\mathrm{central\;PDF}}|$")

    y_positions = np.arange(len(args.central_pdfs))
    x_positions = np.arange(len(args.pseudodata_pdfs))

    ax.set_yticks(y_positions)
    ax.set_yticklabels(
        [get_pdf_map_name(pdf) for pdf in args.central_pdfs], rotation=45, ha="right"
    )
    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        [get_pdf_map_name(pdf) for pdf in args.pseudodata_pdfs], rotation=45
    )
    ax.set_ylabel("Central PDF")
    ax.set_xlabel("Pseudodata PDF")
    ax.set_title(r"PDF bias test")

    for x_idx, _ in enumerate(args.pseudodata_pdfs):
        for y_idx, _ in enumerate(args.central_pdfs):
            value = results_array[y_idx, x_idx]
            uncert = uncerts_array[y_idx, x_idx]
            color = "white" if value < uncert else "red"
            ax.text(
                x_positions[x_idx],
                y_positions[y_idx],
                f"{value:.5f}\n$\\pm${uncert:.5f}",
                ha="center",
                va="center",
                color=color,
                fontsize=9,
            )

    ax.set_ylim(-0.5, len(args.central_pdfs) - 0.5)
    ax.set_xlim(-0.5, len(args.pseudodata_pdfs) - 0.5)

    plt.tight_layout()
    fname = "alphas_heatmap"
    output_path = os.path.join(
        args.output_dir,
        fname,
    )
    fig.savefig(output_path + ".pdf")
    fig.savefig(output_path + ".png", dpi=100)
    wums.output_tools.write_index_and_log(
        args.output_dir,
        fname,
    )
    print(f"Saved 2D alpha_s histogram to {output_path}(.pdf)(.png)(.log)")


if __name__ == "__main__":
    main()
