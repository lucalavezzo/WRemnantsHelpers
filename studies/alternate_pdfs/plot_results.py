import argparse
import os
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.lines as mlines
from matplotlib.legend_handler import HandlerPatch
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
            os.environ["MY_PLOT_DIR"], datetime.now().strftime("%y%m%d_alternate_pdfs")
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
        "--impact-type",
        default="traditional",
        choices=["traditional", "global"],
        help="Type of impact to show, traditional or global. (Default: %(default)s)",
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


class HandlerPatchWithLine(HandlerPatch):
    """Legend handler drawing a line across a patch."""

    def create_artists(
        self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans
    ):
        patch = super().create_artists(
            legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans
        )[0]
        line = mlines.Line2D(
            [xdescent, xdescent + width],
            [ydescent + height / 2.0, ydescent + height / 2.0],
            linestyle=getattr(orig_handle, "_legend_line_style", "--"),
            color=getattr(orig_handle, "_legend_line_color", "black"),
            linewidth=getattr(orig_handle, "_legend_line_width", 2),
            transform=trans,
        )
        return [patch, line]


def draw_bar_edges(
    ax, rect, *, horizontal_style="--", vertical_style="-", **line_kwargs
):
    """Draw bar edges with separate linestyles for horizontal and vertical sides."""
    x_left = rect.get_x()
    x_right = x_left + rect.get_width()
    y_bottom = rect.get_y()
    y_top = y_bottom + rect.get_height()
    ax.hlines(
        [y_bottom, y_top],
        x_left,
        x_right,
        linestyles=horizontal_style,
        linewidth=2,
        **line_kwargs,
    )
    ax.vlines(
        [x_left, x_right],
        y_bottom,
        y_top,
        linestyles=vertical_style,
        linewidth=1,
        **line_kwargs,
    )


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    results = []
    tot_uncerts = []
    pdf_uncerts = []
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

        alphas_tot_uncert = parms["pdfAlphaS"].variance ** 0.5
        if args.impact_type == "global":
            alphas_pdf_uncert = (
                fitresult["global_impacts_grouped"]
                .get()[{"impacts": f"{central_pdf_name}NoAlphaS"}]
                .values()[0]
            )
        elif args.impact_type == "traditional":
            alphas_pdf_uncert = (
                fitresult["impacts_grouped"]
                .get()[{"impacts": f"{central_pdf_name}NoAlphaS"}]
                .values()[0]
            )

        alphas_tot_uncert *= ALPHA_S_SCALING
        alphas_pdf_uncert *= ALPHA_S_SCALING
        tot_uncerts.append(alphas_tot_uncert)
        pdf_uncerts.append(alphas_pdf_uncert)

    results_array = np.array(results)
    tot_uncerts_array = np.array(tot_uncerts)
    pdf_uncerts_array = np.array(pdf_uncerts)

    def format_alphas_value(value, tot_uncert, pdf_uncert):
        """Return latex-safe alpha_s value with symmetric or asymmetric tot_uncertainty."""
        central_value = ALPHA_S + float(np.squeeze(value))
        tot_uncert_array = np.atleast_1d(tot_uncert).astype(float).flatten()
        pdf_uncert_array = np.atleast_1d(pdf_uncert).astype(float).flatten()
        if tot_uncert_array.size == 1:
            return f"${central_value:.5f} \\pm {abs(tot_uncert_array[0]):.5f} ({abs(pdf_uncert_array[0]):.5f})$"
        lower, upper = tot_uncert_array[0], tot_uncert_array[1]
        return f"${central_value:.5f}^{{+{abs(upper):.5f}}}_{{-{abs(lower):.5f}}}$"

    latex_lines = []
    for central_pdf, value, tot_uncert, pdf_uncert in zip(
        args.central_pdfs, results_array, tot_uncerts_array, pdf_uncerts_array
    ):
        latex_lines.append(
            f"{XLABELS[central_pdf].replace('_', '\\_')} & {format_alphas_value(value, tot_uncert, pdf_uncert)} \\\\"
        )
    print("\nLaTeX table:\n" + "\n".join(latex_lines))

    # bar plot: bars encode uncertainty, horizontal line marks central value
    fig, ax = plt.subplots(figsize=(12, 7))
    bar_positions = np.arange(len(args.central_pdfs))
    bar_width = 1.0  # edges touch when x-limits are set to +/-0.5 from first/last bar
    for idx, central_pdf in enumerate(args.central_pdfs):
        central = float(np.squeeze(results_array[idx] + ALPHA_S))
        tot_uncert_array = np.atleast_1d(tot_uncerts_array[idx]).astype(float).flatten()
        if tot_uncert_array.size == 1:
            lower = upper = abs(tot_uncert_array[0])
        else:
            lower, upper = abs(tot_uncert_array[0]), abs(tot_uncert_array[1])
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
        pdf_uncert_array = np.atleast_1d(pdf_uncerts_array[idx]).astype(float).flatten()
        if pdf_uncert_array.size == 1:
            lower = upper = abs(pdf_uncert_array[0])
        else:
            lower, upper = abs(pdf_uncert_array[0]), abs(pdf_uncert_array[1])
        bottom = central - lower
        height = lower + upper
        pdf_bar = ax.bar(
            bar_positions[idx],
            height,
            width=bar_width,
            bottom=bottom,
            color="darkgray",
            edgecolor="none",
            linewidth=0,
            alpha=0.7,
        )[0]
        draw_bar_edges(
            ax,
            pdf_bar,
            color="black",
            horizontal_style="--",
            vertical_style="-",
            zorder=3,
        )
        ax.plot(
            [
                bar_positions[idx] - bar_width / 2,
                bar_positions[idx] + bar_width / 2,
            ],
            [central, central],
            color="black",
            linewidth=2,
        )
    pdg_line = ax.axhline(
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
    total_handle = matplotlib.patches.Patch(
        facecolor="gray",
        edgecolor="black",
        alpha=0.35,
        label="Total uncertainty",
    )
    pdf_handle = matplotlib.patches.Patch(
        facecolor="darkgray",
        edgecolor="black",
        alpha=0.7,
        label="PDF uncertainty",
    )
    pdf_handle._legend_line_style = "--"
    pdf_handle._legend_line_color = "black"
    pdf_handle._legend_line_width = 2
    ax.legend(
        handles=[total_handle, pdf_handle, pdg_line],
        labels=[
            "Total uncertainty",
            "PDF uncertainty",
            pdg_line.get_label(),
        ],
        fontsize="x-small",
        loc="lower left",
        bbox_to_anchor=(1.01, 0),
        handler_map={pdf_handle: HandlerPatchWithLine()},
    )
    fname = "alt_pdfs_alphas_results"
    fname += f"_{args.impact_type}Impacts"
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
