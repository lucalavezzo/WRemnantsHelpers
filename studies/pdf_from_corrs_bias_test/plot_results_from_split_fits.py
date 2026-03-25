import argparse
import os
from datetime import datetime
import re
import warnings

import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
import matplotlib
import rabbit.io_tools
import wums.output_tools
from wremnants.utilities import theory_utils
from scripts.common_plot_style import build_cms_color_cycle
from matplotlib.patches import Patch

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

DIR_NAME_RE = re.compile(
    r"^ZMassDilepton_.*_pdfBiasTest_Zmumu(?:_(?P<postfix>.+))?_(?P<central>[a-z0-9]+)_pseudo(?P<pseudo>[a-z0-9]+)$"
)


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
    parser.add_argument(
        "--dir-name-regex",
        default="",
        help=(
            "Only use fit-output subdirectories whose name matches this regex. "
            "Useful to select one run variant/postfix."
        ),
    )
    parser.add_argument(
        "--fit-postfix",
        default="",
        help=(
            "Select only directories with this postfix in "
            "'..._Zmumu_<postfix>_<pdf>_pseudo<pdf>'. "
            "Use empty string to select no-postfix directories."
        ),
    )
    return parser.parse_args()


def parse_dir_name(name):
    match = DIR_NAME_RE.match(name)
    if not match:
        return None, None, None
    central = normalize_pdf(match.group("central"))
    pseudo = normalize_pdf(match.group("pseudo"))
    postfix = (match.group("postfix") or "").strip()
    if central in PDF_TO_THEORY_CORR and pseudo in PDF_TO_THEORY_CORR:
        return central, pseudo, postfix
    return None, None, None


def collect_split_fitfiles(input_dir, fit_postfix, dir_name_regex):
    fitfiles_by_pair = {}
    regex = re.compile(dir_name_regex) if dir_name_regex else None
    for entry in sorted(os.listdir(input_dir)):
        full = os.path.join(input_dir, entry)
        if not os.path.isdir(full):
            continue
        if regex and not regex.search(entry):
            continue
        central, pseudo, postfix = parse_dir_name(entry)
        if not central:
            continue
        if postfix != fit_postfix:
            continue
        fitfile = os.path.join(full, "fitresults.hdf5")
        if not os.path.exists(fitfile):
            continue
        key = (central, pseudo)
        if key in fitfiles_by_pair:
            raise RuntimeError(
                "Duplicate split-fit outputs for "
                f"central={central}, pseudo={pseudo}: "
                f"{fitfiles_by_pair[key]} and {fitfile}"
            )
        fitfiles_by_pair[key] = fitfile
    return fitfiles_by_pair


def get_uncert(fitresult, central_pdf, uncert_type):
    if uncert_type == "total":
        return fitresult["parms"].get()["pdfAlphaS"].variance ** 0.5
    if uncert_type == "pdf-only-trad":
        info = theory_utils.pdfMap.get(central_pdf)
        if not info:
            raise RuntimeError(f"Missing pdfMap entry for {central_pdf}")
        impact_name = f"{info['name']}NoAlphaS"
        return fitresult["impacts_grouped"].get()[{"impacts": impact_name}].values()[0]
    raise ValueError(f"Unsupported uncertainty: {uncert_type}")


def print_text_table(centrals, pseudos, values, uncerts, central_uncerts, uncert_type):
    print(
        f"\n{uncert_type} uncertainties on pdfAlphaS from diagonal "
        "(central==pseudo) entries:"
    )
    for central in centrals:
        unc = central_uncerts.get(central, np.nan)
        if np.isfinite(unc):
            print(f"{central:<15} {unc:>10.5f}")

    print("\n|Delta alpha_S| +/- sigma matrix:")
    cell_w = 18
    first_col = "central / pseudo"
    header = f"{first_col:<{cell_w}}" + "".join(f"{p:>{cell_w}}" for p in pseudos)
    print(header)
    for i, central in enumerate(centrals):
        row = f"{central:<{cell_w}}"
        for j in range(len(pseudos)):
            val = values[i, j]
            unc = uncerts[i, j]
            if np.isnan(val) or np.isnan(unc):
                cell = "--"
            else:
                cell = f"{abs(val):.5f} +/- {abs(unc):.5f}"
            row += f"{cell:>{cell_w}}"
        print(row)


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    fitfiles_by_pair = collect_split_fitfiles(
        args.input_dir, args.fit_postfix, args.dir_name_regex
    )
    if not fitfiles_by_pair:
        raise RuntimeError("No split-fit outputs found.")

    centrals = args.central_pdfs
    pseudos = args.pseudodata_pdfs
    central_to_idx = {pdf: i for i, pdf in enumerate(centrals)}
    pseudo_to_idx = {pdf: j for j, pdf in enumerate(pseudos)}
    central_with_data = {
        central
        for central, pseudo in fitfiles_by_pair
        if central in central_to_idx and pseudo in pseudo_to_idx
    }
    missing_diagonal = sorted(
        central
        for central in central_with_data
        if (central, central) not in fitfiles_by_pair
    )
    if missing_diagonal:
        raise RuntimeError(
            "Missing required split-fit diagonal files "
            "(expected central==pseudo): " + ", ".join(missing_diagonal)
        )

    values = np.full((len(centrals), len(pseudos)), np.nan)
    uncerts = np.full((len(centrals), len(pseudos)), np.nan)
    uncerts_pdf = np.full((len(centrals), len(pseudos)), np.nan)
    uncerts_total = np.full((len(centrals), len(pseudos)), np.nan)

    for (central, pseudo), fitfile in fitfiles_by_pair.items():
        if central not in central_to_idx or pseudo not in pseudo_to_idx:
            continue
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
        unc_pdf = get_uncert(fitresult, central, "pdf-only-trad") * ALPHA_S_UNCERT_SCALE
        unc_total = get_uncert(fitresult, central, "total") * ALPHA_S_UNCERT_SCALE
        unc = unc_total if args.uncert == "total" else unc_pdf
        i = central_to_idx[central]
        j = pseudo_to_idx[pseudo]
        values[i, j] = val
        uncerts[i, j] = unc
        uncerts_pdf[i, j] = unc_pdf
        uncerts_total[i, j] = unc_total

    diagonal_uncerts = {}
    diagonal_uncerts_pdf = {}
    diagonal_uncerts_total = {}
    for central in centrals:
        diagonal_uncerts[central] = np.nan
        diagonal_uncerts_pdf[central] = np.nan
        diagonal_uncerts_total[central] = np.nan
        i = central_to_idx[central]
        j = pseudo_to_idx.get(central)
        if j is None:
            continue
        diagonal_uncerts[central] = uncerts[i, j]
        diagonal_uncerts_pdf[central] = uncerts_pdf[i, j]
        diagonal_uncerts_total[central] = uncerts_total[i, j]
        if central in central_with_data and not np.isfinite(diagonal_uncerts[central]):
            warnings.warn(
                f"Missing diagonal uncertainty entry for central={central} "
                "(expected pair central==pseudo)."
            )

    print_text_table(centrals, pseudos, values, uncerts, diagonal_uncerts, args.uncert)

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
        row_unc_pdf = diagonal_uncerts_pdf.get(central, np.nan)
        row_unc_total = diagonal_uncerts_total.get(central, np.nan)
        if np.isfinite(row_unc_total):
            ax.fill_betweenx(
                [i, i + 1],
                ALPHA_S - row_unc_total,
                ALPHA_S + row_unc_total,
                color="gray",
                alpha=0.15,
                linewidth=0,
                zorder=0,
            )
        if np.isfinite(row_unc_pdf):
            ax.fill_betweenx(
                [i, i + 1],
                ALPHA_S - row_unc_pdf,
                ALPHA_S + row_unc_pdf,
                color="gray",
                alpha=0.35,
                linewidth=0,
                zorder=1,
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
    # Keep x-range symmetric around the reference alpha_s value.
    finite = np.isfinite(values)
    if np.any(finite):
        max_delta = np.nanmax(
            np.abs(values[finite]) + np.nan_to_num(np.abs(uncerts[finite]), nan=0.0)
        )
        half_range = max(1.1 * max_delta, 1e-4)
        ax.set_xlim(ALPHA_S - half_range, ALPHA_S + half_range)
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
        ]
        + [
            Patch(facecolor="gray", alpha=0.35, edgecolor="none", label="PDF impact"),
            Patch(
                facecolor="gray", alpha=0.15, edgecolor="none", label="Total uncert."
            ),
        ],
        loc=(1.01, 0),
        title="Legend",
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
