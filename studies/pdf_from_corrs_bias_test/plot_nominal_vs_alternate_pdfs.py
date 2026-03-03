import argparse
import datetime
import os

import h5py
import mplhep as hep
from hist import Hist

from utilities import parsing
from wremnants import theory_tools
from wums import boostHistHelpers as hh
from wums import ioutils
from wums import output_tools
from wums import plot_tools

hep.style.use("CMS")

DEFAULT_ALT_PDFS = [
    "ct18z",
    "nnpdf31",
    "nnpdf40",
    "pdf4lhc21",
    "msht20",
    "herapdf20",
]

DEFAULT_PSEUDODATA_PDFS = {
    "ct18z": "scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO",
    "herapdf20": "scetlib_dyturbo_LatticeNP_HERAPDF20_N3p0LL_N2LO",
    "msht20": "scetlib_dyturbo_LatticeNP_MSHT20_N3p0LL_N2LO",
    "msht20an3lo": "scetlib_dyturbo_LatticeNP_MSHT20aN3LO_N3p0LL_N2LO",
    "nnpdf40": "scetlib_dyturbo_LatticeNP_NNPDF40_N3p0LL_N2LO",
    "pdf4lhc21": "scetlib_dyturbo_LatticeNP_PDF4LHC21_N3p0LL_N2LO",
    "nnpdf31": "scetlib_dyturbo_LatticeNP_NNPDF31_N3p0LL_N2LO",
}


def load_results_h5py(h5file):
    if "results" in h5file.keys():
        return ioutils.pickle_load_h5py(h5file["results"])
    return {k: ioutils.pickle_load_h5py(v) for k, v in h5file.items()}


def get_pdf_map_name(pdf_key):
    info = theory_tools.pdfMap.get(pdf_key)
    if info:
        return info["name"]
    return f"pdf{pdf_key.upper()}"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Plot nominal histogram vs central predictions from alternate PDFs "
            "from a histmaker HDF5 output."
        )
    )
    parser.add_argument("infile", type=str, help="Input histmaker HDF5 file.")
    parser.add_argument(
        "--proc",
        type=str,
        default="ZmumuPostVFP",
        help="Process key inside the HDF5 results dictionary.",
    )
    parser.add_argument(
        "--nominal-hist",
        type=str,
        default="nominal",
        help="Histogram name for the nominal prediction.",
    )
    parser.add_argument(
        "--alt-pdfs",
        nargs="+",
        default=DEFAULT_ALT_PDFS,
        help="Alternate PDF keys to resolve into histogram names.",
    )
    parser.add_argument(
        "--include-minnlo-pdfs",
        action="store_true",
        help=(
            "Also plot MINNLO PDF-weight histograms (nominal_pdf{PDFNAME}) "
            "for the same --alt-pdfs keys."
        ),
    )
    parser.add_argument(
        "--alt-hists",
        nargs="+",
        default=None,
        help="Explicit alternate histogram names. If passed, overrides --alt-pdfs.",
    )
    parser.add_argument(
        "--axes",
        nargs="+",
        default=[],
        help="Axes to keep before plotting. Remaining axes are unrolled.",
    )
    parser.add_argument(
        "--select",
        nargs="+",
        dest="selection",
        type=str,
        default=None,
        help=(
            "Apply selections before projection. Each entry is either "
            "'axis value' or 'axis low high'."
        ),
    )
    parser.add_argument(
        "--corr-vars",
        default="0",
        help=(
            "Selection to apply on the theory-correction 'vars' axis. "
            "Use an index (default: 0) or an explicit category label."
        ),
    )
    parser.add_argument(
        "--minnlo-pdfvar",
        default="0",
        help=(
            "Selection to apply on the MINNLO 'pdfVar' axis. "
            "Use an index (default: 0) or an explicit category label."
        ),
    )
    parser.add_argument(
        "--binwnorm",
        type=int,
        default=1,
        help="Bin-width normalization used in unrolling.",
    )
    parser.add_argument(
        "--rrange",
        default=None,
        type=float,
        nargs=2,
        help="Manual ratio range for the lower panel. If omitted, auto-range is used.",
    )
    parser.add_argument(
        "--autorrange",
        type=float,
        default=0.05,
        help=(
            "Padding fraction for automatic ratio-range selection "
            "(used when --rrange is not provided)."
        ),
    )
    parser.add_argument(
        "--oname",
        type=str,
        default="nominal_vs_alternate_pdfs",
        help="Output name stem.",
    )
    parser.add_argument(
        "--postfix",
        default="",
        help="Postfix to append to output filename.",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default=os.path.join(
            os.environ.get("MY_PLOT_DIR", "."),
            datetime.datetime.now().strftime("%y%m%d_pdf_from_corrs_bias_test"),
        ),
        help="Output directory.",
    )
    return parser.parse_args()


def apply_selection(h, selections):
    if not selections:
        return h
    for sel in selections:
        tokens = sel.split()
        if len(tokens) == 3:
            axis_name, low, high = tokens
            low = parsing.str_to_complex_or_int(low)
            high = parsing.str_to_complex_or_int(high)
            h = h[{axis_name: slice(low, high)}]
        elif len(tokens) == 2:
            axis_name, value = tokens
            try:
                value = parsing.str_to_complex_or_int(value)
            except argparse.ArgumentTypeError:
                pass
            h = h[{axis_name: value}]
        else:
            raise ValueError(
                f"Invalid selection '{sel}'. Use 'axis value' or 'axis low high'."
            )
    return h


def prepare_hist(h, axes, selections, binwnorm):
    h = apply_selection(h, selections)
    if axes:
        missing_axes = [ax for ax in axes if ax not in h.axes.name]
        if missing_axes:
            raise ValueError(
                f"Axes {missing_axes} not found in histogram axes {h.axes.name}"
            )
        h = h.project(*axes)
    if h.ndim > 1:
        h = hh.unrolledHist(h, binwnorm=binwnorm)
    return h


def apply_category_axis_selection(h, axis_name, selector):
    if axis_name not in h.axes.name:
        return h
    axis = h.axes[axis_name]
    selected = None
    try:
        idx = int(selector)
        selected = axis[idx]
    except (ValueError, TypeError, IndexError):
        selected = selector
    return h[{axis_name: selected}]


def resolve_alt_hist_name(pdf_key, output_hists):
    candidates = []
    if pdf_key in DEFAULT_PSEUDODATA_PDFS:
        corr = DEFAULT_PSEUDODATA_PDFS[pdf_key]
        candidates.append(f"nominal_{corr}_pdfvars_CorrByHelicity")
        candidates.append(f"nominal_{corr}_Corr")

    map_name = get_pdf_map_name(pdf_key)
    candidates.append(f"nominal_{map_name}_pdfvars_CorrByHelicity")
    candidates.append(f"nominal_{map_name}_Corr")
    candidates.append(f"nominal_pdf{pdf_key.upper()}_Corr")

    for candidate in candidates:
        if candidate in output_hists:
            return candidate
    return None


def resolve_minnlo_hist_name(pdf_key, output_hists):
    map_name = get_pdf_map_name(pdf_key)
    pdf_token = map_name[3:] if map_name.startswith("pdf") else map_name
    candidates = [
        f"nominal_pdf{pdf_token}ByHelicity",
        f"nominal_pdf{pdf_token}",
        f"nominal_{map_name}",
        f"nominal_pdf{pdf_key.upper()}ByHelicity",
        f"nominal_pdf{pdf_key.upper()}",
    ]
    for candidate in candidates:
        if candidate in output_hists:
            return candidate
    return None


def load_hist(entry):
    if isinstance(entry, Hist):
        return entry
    return entry.get()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    with h5py.File(args.infile, "r") as h5file:
        results = load_results_h5py(h5file)

        if args.proc not in results:
            raise KeyError(
                f"Process '{args.proc}' not found. Available: {list(results.keys())}"
            )
        proc_data = results[args.proc]
        if not isinstance(proc_data, dict) or "output" not in proc_data:
            raise KeyError(f"Process '{args.proc}' has no 'output' dictionary.")

        output_hists = proc_data["output"]
        if args.nominal_hist not in output_hists:
            raise KeyError(
                f"Nominal hist '{args.nominal_hist}' not found. "
                f"Available: {list(output_hists.keys())}"
            )

        nominal = load_hist(output_hists[args.nominal_hist])
        nominal = prepare_hist(nominal, args.axes, args.selection, args.binwnorm)

        hists = [nominal]
        labels = ["nominal (ref.)"]
        linestyles = ["solid"]

        if args.alt_hists:
            corr_hist_names = [h for h in args.alt_hists if h in output_hists]
            missing = [h for h in args.alt_hists if h not in output_hists]
            if missing:
                print(f"Skipping missing histograms from --alt-hists: {missing}")
            minnlo_hist_names = []
        else:
            corr_hist_names = []
            minnlo_hist_names = []
            for pdf_key in args.alt_pdfs:
                corr_hist_name = resolve_alt_hist_name(pdf_key, output_hists)
                if corr_hist_name is None:
                    print(
                        f"No correction histogram found for PDF key '{pdf_key}', skipping corr."
                    )
                else:
                    corr_hist_names.append(corr_hist_name)

                if args.include_minnlo_pdfs:
                    minnlo_hist_name = resolve_minnlo_hist_name(pdf_key, output_hists)
                    if minnlo_hist_name is None:
                        print(
                            f"No MINNLO histogram found for PDF key '{pdf_key}', skipping MINNLO."
                        )
                    else:
                        minnlo_hist_names.append(minnlo_hist_name)

        if not corr_hist_names and not minnlo_hist_names:
            raise RuntimeError(
                "No alternate histograms were found to plot (corr or MINNLO)."
            )

        for hist_name in corr_hist_names:
            h = load_hist(output_hists[hist_name])
            h = apply_category_axis_selection(h, "vars", args.corr_vars)
            h = prepare_hist(h, args.axes, args.selection, args.binwnorm)
            hists.append(h)
            label = (
                hist_name.replace("nominal_", "")
                .replace("_Corr", "")
                .replace("scetlib_dyturbo_LatticeNP_", "")
            )
            label += " (corr)"
            labels.append(label)
            linestyles.append("solid")

        for hist_name in minnlo_hist_names:
            h = load_hist(output_hists[hist_name])
            h = apply_category_axis_selection(h, "pdfVar", args.minnlo_pdfvar)
            h = prepare_hist(h, args.axes, args.selection, args.binwnorm)
            hists.append(h)
            label = hist_name.replace("nominal_pdf", "").replace("nominal_", "")
            label += " (minnlo)"
            labels.append(label)
            linestyles.append("dashed")

    xlabel = "Unrolled bin"
    if len(args.axes) == 1:
        xlabel = args.axes[0]

    use_auto_rrange = args.rrange is None
    rrange = args.rrange if args.rrange is not None else (0.98, 1.02)

    fig = plot_tools.makePlotWithRatioToRef(
        hists,
        labels,
        linestyles=linestyles,
        xlabel=xlabel,
        ylabel="Events",
        rrange=[rrange],
        autorrange=args.autorrange if use_auto_rrange else None,
        ratio_legend=False,
    )
    handles, legend_labels = fig.axes[0].get_legend_handles_labels()
    fig.axes[0].legend(handles, legend_labels, loc=(1.01, 0), fontsize="small")

    outname = args.oname
    if args.postfix:
        outname += f"_{args.postfix}"
    plot_tools.save_pdf_and_png(args.outdir, outname, fig)
    output_tools.write_index_and_log(args.outdir, outname, args=args)
    print(f"Saved {os.path.join(args.outdir, outname)}(.pdf)(.png)(.log)")


if __name__ == "__main__":
    main()
