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
DEFAULT_CENTRAL_PDFS = [
    "ct18",
    "ct18z",
    "nnpdf31",
    "nnpdf40",
    "pdf4lhc21",
    "msht20",
    "herapdf20",
]
DEFAULT_PSEUDODATA_PDFS = [
    "ct18",
    "ct18z",
    "nnpdf31",
    "nnpdf40",
    "pdf4lhc21",
    "msht20",
    "herapdf20",
]


def get_pdf_map_name(pdf_key: str) -> str:
    info = theory_tools.pdfMap.get(pdf_key)
    if info:
        return info["name"]
    return f"pdf{pdf_key.upper()}"


def get_pdf_display_name(pdf_key: str) -> str:
    info = theory_tools.pdfMap.get(pdf_key)
    if info:
        return info["name"].strip("pdf")
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
        default="pdf-only",
        choices=["total", "pdf-only", "pdf-only-trad", "contour"],
        help="Type of uncertainty from the central PDF set to normalize by. (Default: %(default)s)",
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

    args.central_pdfs = list(args.central_pdfs)
    args.pseudodata_pdfs = list(args.pseudodata_pdfs)

    return args


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    asym_uncert = True if args.uncert in ["contour"] else False

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

            alphas = parms["pdfAlphaS"].value
            alphas *= 0.0015
            this_central_results.append(alphas)

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
    for ipdf in range(len(args.central_pdfs)):
        for jpdf in range(len(args.pseudodata_pdfs)):
            if args.central_pdfs[ipdf] == args.pseudodata_pdfs[jpdf]:
                uncert = uncerts_array[ipdf, jpdf]
                if asym_uncert:
                    print(
                        f"{args.central_pdfs[ipdf]}\t\t"
                        f"+{uncert[1]:.5f}/-{uncert[0]:.5f}"
                    )
                else:
                    print(f"{args.central_pdfs[ipdf]}\t\t{uncert:.5f}")

    fig, ax = plt.subplots(
        figsize=(
            2 * (len(args.pseudodata_pdfs) + 2),
            2 * len(args.central_pdfs),
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

    y_positions = np.arange(len(args.central_pdfs))
    x_positions = np.arange(len(args.pseudodata_pdfs))

    ax.set_yticks(y_positions)
    ax.set_yticklabels(
        [get_pdf_display_name(pdf) for pdf in args.central_pdfs],
        rotation=45,
        ha="right",
    )
    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        [get_pdf_display_name(pdf) for pdf in args.pseudodata_pdfs], rotation=45
    )
    ax.set_ylabel("Central PDF", loc="center")
    ax.set_xlabel("Pseudodata PDF", loc="center")

    for x_idx, _ in enumerate(args.pseudodata_pdfs):
        for y_idx, _ in enumerate(args.central_pdfs):
            value = results_array[y_idx, x_idx]
            uncert = uncerts_array[y_idx, x_idx]
            if asym_uncert:
                uncert_up = uncert[1] if uncert[1] > 0 else uncert[0]
                uncert_down = uncert[0] if uncert[0] > 0 else uncert[1]
                color = (
                    "white" if (value < uncert_up and value > uncert_down) else "red"
                )
                ax.text(
                    x_positions[x_idx],
                    y_positions[y_idx],
                    f"{value:.5f}\n$^{{+{uncert_up:.5f}}}_{{-{uncert_down:.5f}}}$",
                    ha="center",
                    va="center",
                    color=color,
                    fontsize=14,
                )
            else:
                value = np.abs(value)
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

    ax.set_ylim(-0.5, len(args.central_pdfs) - 0.5)
    ax.set_xlim(-0.5, len(args.pseudodata_pdfs) - 0.5)

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
    colors = cmap(np.linspace(0, 1, len(args.pseudodata_pdfs)))
    height = 1.5 * len(args.central_pdfs)
    fig, ax = plt.subplots(
        figsize=(
            15,
            height,
        )
    )
    for central_pdf_idx, central_pdf in enumerate(args.central_pdfs):
        for pseudodata_pdf_idx, pseudodata_pdf in enumerate(args.pseudodata_pdfs):
            x = results_array[central_pdf_idx, pseudodata_pdf_idx] + ALPHA_S
            y = central_pdf_idx + pseudodata_pdf_idx * (
                1 / (len(args.pseudodata_pdfs) + 3)
            )
            xerr = uncerts_array[central_pdf_idx, pseudodata_pdf_idx]
            ax.errorbar(
                x,
                y,
                xerr=abs(xerr[..., np.newaxis]),
                fmt="o",
                color=colors[pseudodata_pdf_idx],
            )
    ax.axvline(x=ALPHA_S, color="black", linestyle="--")
    ax.set_xlabel(r"$\alpha_S$", loc="center")
    ax.set_ylabel("Central PDF", loc="center")
    ax.set_yticks(np.arange(len(args.central_pdfs)))
    ax.set_yticklabels([get_pdf_display_name(pdf) for pdf in args.central_pdfs])
    ax.legend(
        handles=[
            matplotlib.lines.Line2D(
                [],
                [],
                color=colors[i],
                marker="o",
                linestyle="",
                label=get_pdf_display_name(pdf),
            )
            for i, pdf in enumerate(args.pseudodata_pdfs)
        ],
        labels=[get_pdf_display_name(pdf) for pdf in args.pseudodata_pdfs],
        loc=(1.01, 0),
        title="Pseudodata PDF",
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
