import argparse
import os
from datetime import datetime
import warnings

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import rabbit.io_tools
import wums.output_tools
from wremnants import theory_tools
import matplotlib
from scripts.common_plot_style import build_cms_color_cycle

hep.style.use("CMS")

ALPHA_S = 0.118
ALPHA_S_UNCERT_SCALE = 0.002

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

PDF_ORDER = [
    "ct18z",
    "herapdf20",
    "msht20",
    "msht20an3lo",
    "nnpdf31",
    "nnpdf40",
    "pdf4lhc21",
    "ct18",
]


def normalize_pdf(pdf):
    return pdf.lower()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot alpha_s bias results from split-fit output directories."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing fit output subdirectories.",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(
            os.environ.get("MY_PLOT_DIR", "."),
            datetime.now().strftime("%y%m%d_pdf_from_corrs_bias_test"),
        ),
        help="Output directory for plots. (Default: %(default)s)",
    )
    parser.add_argument(
        "--postfix",
        default="",
        help="Postfix for output file names.",
    )
    parser.add_argument(
        "--uncert",
        default="pdf-only-trad",
        choices=["total", "pdf-only-trad"],
        help="Uncertainty used for normalization. (Default: %(default)s)",
    )
    parser.add_argument(
        "--central-pdfs",
        nargs="+",
        default=PDF_ORDER,
        choices=sorted(PDF_TO_THEORY_CORR.keys()),
        help="Central PDFs to show on the y-axis (rows).",
    )
    parser.add_argument(
        "--pseudodata-pdfs",
        nargs="+",
        default=PDF_ORDER,
        choices=sorted(PDF_TO_THEORY_CORR.keys()),
        help="Pseudodata PDFs to show on the x-axis (columns).",
    )
    return parser.parse_args()


def parse_dir_name(name):
    if "_pseudo" not in name:
        return None, None
    left, pseudo = name.rsplit("_pseudo", 1)
    central = normalize_pdf(left.split("_")[-1])
    pseudo = normalize_pdf(pseudo)
    if central in PDF_TO_THEORY_CORR and pseudo in PDF_TO_THEORY_CORR:
        return central, pseudo
    return None, None


def get_uncert(fitresult, central_pdf, uncert_type):
    if uncert_type == "total":
        return fitresult["parms"].get()["pdfAlphaS"].variance ** 0.5
    if uncert_type == "pdf-only-trad":
        info = theory_tools.pdfMap.get(central_pdf)
        if not info:
            raise RuntimeError(f"Missing pdfMap entry for {central_pdf}")
        impact_name = f"{info['name']}NoAlphaS"
        return fitresult["impacts_grouped"].get()[{"impacts": impact_name}].values()[0]
    raise ValueError(f"Unsupported uncertainty: {uncert_type}")


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    pairs = []
    for entry in sorted(os.listdir(args.input_dir)):
        full = os.path.join(args.input_dir, entry)
        if not os.path.isdir(full):
            continue
        central, pseudo = parse_dir_name(entry)
        if not central:
            continue
        fitfile = os.path.join(full, "fitresults.hdf5")
        if os.path.exists(fitfile):
            pairs.append((central, pseudo, fitfile))

    if not pairs:
        raise RuntimeError("No split-fit outputs found.")

    centrals = args.central_pdfs
    pseudos = args.pseudodata_pdfs

    values = np.full((len(centrals), len(pseudos)), np.nan)
    uncerts = np.full((len(centrals), len(pseudos)), np.nan)

    for central, pseudo, fitfile in pairs:
        result_name = f"nominal_{PDF_TO_THEORY_CORR[pseudo]}_Corr_vars"
        try:
            fitresult, _ = rabbit.io_tools.get_fitresult(
                fitfile, result=result_name, meta=True
            )
        except Exception as exc:
            warnings.warn(
                f"Skipping unreadable fit file or missing result '{result_name}' in "
                f"{fitfile}: {exc}"
            )
            continue
        val = fitresult["parms"].get()["pdfAlphaS"].value * ALPHA_S_UNCERT_SCALE
        unc = get_uncert(fitresult, central, args.uncert) * ALPHA_S_UNCERT_SCALE
        i = centrals.index(central)
        j = pseudos.index(pseudo)
        values[i, j] = val
        uncerts[i, j] = unc

    fig, ax = plt.subplots(figsize=(2 * (len(pseudos) + 2), 2 * max(1, len(centrals))))
    mask = np.ma.masked_invalid(np.abs(values))
    mesh = ax.imshow(mask, origin="lower", aspect="auto", cmap="viridis")
    cbar = fig.colorbar(mesh, ax=ax)
    cbar.set_label(r"$|\Delta\alpha_S|$")

    ax.set_xticks(np.arange(len(pseudos)))
    ax.set_xticklabels(pseudos, rotation=45)
    ax.set_yticks(np.arange(len(centrals)))
    ax.set_yticklabels(centrals)
    ax.set_xlabel("Pseudodata PDF")
    ax.set_ylabel("Central PDF")

    for i in range(len(centrals)):
        for j in range(len(pseudos)):
            if np.isnan(values[i, j]):
                continue
            ax.text(
                j,
                i,
                f"{values[i,j]:.5f}\n$\\pm${uncerts[i,j]:.5f}",
                ha="center",
                va="center",
                color="white",
                fontsize=12,
            )

    plt.tight_layout()
    name = "alphas_heatmap_split_fits"
    if args.postfix:
        name += f"_{args.postfix}"
    out = os.path.join(args.output_dir, name)
    fig.savefig(out + ".pdf", bbox_inches="tight")
    fig.savefig(out + ".png", bbox_inches="tight", dpi=120)
    wums.output_tools.write_index_and_log(args.output_dir, name)
    print(f"Saved {out}(.pdf)(.png)(.log)")

    # scatter plot
    colors = build_cms_color_cycle(len(pseudos))
    markers = ["o", "s", "^", "D", "v", "P", "X", "<", ">", "*"]
    fig, ax = plt.subplots(figsize=(14, max(5, 1.5 * len(centrals))))
    for yline in range(len(centrals) + 1):
        ax.axhline(y=yline, color="gray", linestyle="--", linewidth=0.5)
    for i, central in enumerate(centrals):
        y_center = i + 0.5
        row_unc = np.nanmedian(np.abs(uncerts[i, :]))
        if np.isfinite(row_unc):
            ax.fill_betweenx(
                [i, i + 1],
                ALPHA_S - row_unc,
                ALPHA_S + row_unc,
                color="gray",
                alpha=0.2,
                linewidth=0,
                zorder=0,
            )
        for j, pseudo in enumerate(pseudos):
            if np.isnan(values[i, j]) or np.isnan(uncerts[i, j]):
                continue
            x = ALPHA_S + values[i, j]
            y = i + (j + 1) * (1.0 / (len(pseudos) + 1))
            ax.plot(
                x,
                y,
                marker=markers[j % len(markers)],
                linestyle="",
                color=colors[j],
            )
        # Put the central-PDF name inside the row, centered between separators.
        ax.text(
            0.01,
            y_center,
            central,
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=14,
            bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none", "pad": 1.5},
        )
    ax.axvline(x=ALPHA_S, color="black", linestyle="--")
    ax.set_xlabel(r"$\alpha_S$", loc="center")
    ax.set_ylabel("Central PDF", loc="center")
    ax.set_ylim(0, len(centrals))
    ax.set_yticks([])
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.legend(
        handles=[
            matplotlib.lines.Line2D(
                [],
                [],
                color=colors[i],
                marker=markers[i % len(markers)],
                linestyle="",
                label=p,
            )
            for i, p in enumerate(pseudos)
        ],
        labels=pseudos,
        loc=(1.01, 0),
        title="Pseudodata PDF",
    )
    fig.tight_layout()
    name = "alphas_scatter_split_fits"
    if args.postfix:
        name += f"_{args.postfix}"
    out = os.path.join(args.output_dir, name)
    fig.savefig(out + ".pdf", bbox_inches="tight")
    fig.savefig(out + ".png", bbox_inches="tight", dpi=120)
    wums.output_tools.write_index_and_log(args.output_dir, name)
    print(f"Saved {out}(.pdf)(.png)(.log)")


if __name__ == "__main__":
    main()
