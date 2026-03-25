import argparse
import os
from datetime import datetime
import re
import warnings
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.lines as mlines
from matplotlib.legend_handler import HandlerPatch
import mplhep as hep

import rabbit
import rabbit.io_tools
import wums.output_tools
from wremnants.utilities import theory_utils as theory_tools

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
PDF_TO_THEORY_CORR = {
    "ct18z": "scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO",
    "herapdf20": "scetlib_dyturbo_LatticeNP_HERAPDF20_N3p0LL_N2LO",
    "msht20": "scetlib_dyturbo_LatticeNP_MSHT20_N3p0LL_N2LO",
    "msht20an3lo": "scetlib_dyturbo_LatticeNP_MSHT20aN3LO_N3p0LL_N2LO",
    "nnpdf40": "scetlib_dyturbo_LatticeNP_NNPDF40_N3p0LL_N2LO",
    "pdf4lhc21": "scetlib_dyturbo_LatticeNP_PDF4LHC21_N3p0LL_N2LO",
    "nnpdf31": "scetlib_dyturbo_LatticeNP_NNPDF31_N3p0LL_N2LO",
    "ct18": "scetlib_dyturbo_LatticeNP_CT18_N3p0LL_N2LO",
}


def _split_dir_pattern(file_base: str) -> re.Pattern:
    escaped_base = re.escape(file_base)
    return re.compile(
        rf"^(?P<file_base>{escaped_base})(?P<separator>_)?(?:(?P<postfix>.+)_)?(?P<central>[a-z0-9]+)_pseudo(?P<pseudo>[a-z0-9]+)$"
    )


def get_pdf_map_name(pdf_key: str) -> str:
    info = theory_tools.pdfMap.get(pdf_key)
    if info:
        return info["name"]
    return f"pdf{pdf_key.upper()}"


def normalize_pdf(pdf):
    return pdf.lower()


def parse_split_dir_name(name, file_base):
    match = _split_dir_pattern(file_base).match(name)
    if not match:
        return None, None
    central = normalize_pdf(match.group("central"))
    pseudo = normalize_pdf(match.group("pseudo"))
    if central != pseudo:
        return None, None
    postfix = (match.group("postfix") or "").strip()
    if central in PDF_TO_THEORY_CORR and pseudo in PDF_TO_THEORY_CORR:
        return central, postfix
    return None, None


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
            "<input-dir>/<file-base>_<postfix_><central>_pseudo<central>/fitresults.hdf5."
            "configured via the script arguments"
            "(Default: None)"
        ),
    )
    parser.add_argument(
        "--file-base",
        default="ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_",
        dest="file_base",
        help=(
            "Directory prefix before <postfix_><central> in split-fit layout. "
            "(Default: %(default)s)"
        ),
    )
    parser.add_argument(
        "--fit-postfix",
        default="",
        help=(
            "Split layout only: require this postfix in "
            "'..._Zmumu_<postfix>_<central>_pseudo<central>'. "
            "Use empty string for no-postfix dirs."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(
            os.environ.get("MY_PLOT_DIR", "."),
            datetime.now().strftime("%y%m%d_alternate_pdfs"),
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
        default=(0.116, 0.1205),
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


def collect_split_fitfiles(input_dir, fit_postfix, file_base):
    fitfiles = {}
    for entry in sorted(os.listdir(input_dir)):
        full = os.path.join(input_dir, entry)
        if not os.path.isdir(full):
            continue
        central, postfix = parse_split_dir_name(entry, file_base)
        if not central:
            continue
        if postfix != fit_postfix:
            continue
        fitfile = os.path.join(full, "fitresults.hdf5")
        if not os.path.exists(fitfile):
            continue
        if central in fitfiles:
            warnings.warn(
                f"Multiple split-fit files found for central={central}; keeping first: {fitfiles[central]}"
            )
            continue
        fitfiles[central] = fitfile
    return fitfiles


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    results = []
    tot_uncerts = []
    pdf_uncerts = []
    used_central_pdfs = []

    split_fitfiles = {}
    split_fitfiles = collect_split_fitfiles(
        args.input_dir, args.fit_postfix, args.file_base
    )
    if not split_fitfiles:
        raise RuntimeError(
            "No split-fit outputs found for requested --fit-postfix in input dir."
        )
    print("Using input layout: split")

    for central_pdf in args.central_pdfs:
        if central_pdf not in PDF_TO_THEORY_CORR:
            raise ValueError(
                f"Unsupported central PDF '{central_pdf}'. Supported: "
                + ", ".join(sorted(PDF_TO_THEORY_CORR))
            )
        input_file = split_fitfiles.get(central_pdf)
        if not input_file:
            warnings.warn(
                f"Missing split Asimov fit for central={central_pdf}; skipping."
            )
            continue
        result_name = f"nominal_{PDF_TO_THEORY_CORR[central_pdf]}_Corr_vars"

        central_pdf_name = get_pdf_map_name(central_pdf)
        print(input_file)

        try:
            fitresult, _ = rabbit.io_tools.get_fitresult(
                input_file, result=result_name, meta=True
            )
        except Exception:
            fitresult, _ = rabbit.io_tools.get_fitresult(
                input_file, result="asimov", meta=True
            )
        parms = fitresult["parms"].get()

        alphas = parms["pdfAlphaS"].value
        alphas *= ALPHA_S_SCALING
        results.append(alphas)
        used_central_pdfs.append(central_pdf)

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

    if not results:
        raise RuntimeError(
            "No fit results loaded. Check --fit-postfix and --central-pdfs."
        )

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
        used_central_pdfs, results_array, tot_uncerts_array, pdf_uncerts_array
    ):
        label = XLABELS.get(central_pdf, central_pdf).replace("_", r"\_")
        latex_lines.append(
            f"{label} & {format_alphas_value(value, tot_uncert, pdf_uncert)} \\\\"
        )
    print("\nLaTeX table:\n" + "\n".join(latex_lines))

    # bar plot: bars encode uncertainty, horizontal line marks central value
    fig, ax = plt.subplots(figsize=(8, 7))
    bar_positions = np.arange(len(used_central_pdfs))
    bar_width = 1.0  # edges touch when x-limits are set to +/-0.5 from first/last bar
    for idx, central_pdf in enumerate(used_central_pdfs):
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
        label=f"PDG avg.: " + ALPHA_S_TEX + f"={ALPHA_S_PDG}",
        linestyle="--",
        linewidth=1,
    )
    ax.set_ylabel(ALPHA_S_TEX, loc="center")
    ax.set_xticks(bar_positions)
    ax.set_xticklabels(
        [XLABELS.get(p, p) for p in used_central_pdfs],
        rotation=45,
        ha="right",
    )
    ax.set_xlim(-0.5, len(used_central_pdfs) - 0.5)
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
            "Total uncert.",
            "PDF uncert.",
            pdg_line.get_label(),
        ],
        fontsize="x-small",
        loc="upper left",
        handler_map={pdf_handle: HandlerPatchWithLine()},
        ncols=2,
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
