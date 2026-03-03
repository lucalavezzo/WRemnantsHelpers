import argparse
import datetime
import os
import re

import h5py
import matplotlib.pyplot as plt
import mplhep as hep
from hist import Hist

from utilities import parsing
from wremnants import theory_tools
from wums import boostHistHelpers as hh
from wums import ioutils
from wums import output_tools
from wums import plot_tools
from scripts.common_plot_style import build_cms_color_cycle

hep.style.use("CMS")

PDF_TO_THEORY_CORR = {
    "ct18z": "scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO",
    "herapdf20": "scetlib_dyturbo_LatticeNP_HERAPDF20_N3p0LL_N2LO",
    "msht20": "scetlib_dyturbo_LatticeNP_MSHT20_N3p0LL_N2LO",
    "msht20an3lo": "scetlib_dyturbo_LatticeNP_MSHT20aN3LO_N3p0LL_N2LO",
    "nnpdf40": "scetlib_dyturbo_LatticeNP_NNPDF40_N3p0LL_N2LO",
    "pdf4lhc21": "scetlib_dyturbo_LatticeNP_PDF4LHC21_N3p0LL_N2LO",
    "nnpdf31": "scetlib_dyturbo_LatticeNP_NNPDF31_N3p0LL_N2LO",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Plot nominal vs PDF/theoryCorr templates from a directory of "
            "histmaker outputs produced per PDF/theoryCorr pair."
        )
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing mz_dilepton_*.hdf5 files.",
    )
    parser.add_argument(
        "--proc",
        default="Zmumu_2016PostVFP",
        help="Process key inside each HDF5 file.",
    )
    parser.add_argument(
        "--pdfs",
        nargs="+",
        default=list(PDF_TO_THEORY_CORR.keys()),
        choices=list(PDF_TO_THEORY_CORR.keys()),
        help="PDFs to include from the directory. (Default: %(default)s)",
    )
    parser.add_argument(
        "--reference-pdf",
        default=None,
        choices=list(PDF_TO_THEORY_CORR.keys()),
        help="PDF whose nominal histogram is used as reference. Default: first available from --pdfs.",
    )
    parser.add_argument(
        "--nominal-hist",
        default="nominal",
        help="Nominal histogram name.",
    )
    parser.add_argument(
        "--include-minnlo-pdfs",
        action="store_true",
        help="Also include nominal_pdf{PDFNAME} curves from each file.",
    )
    parser.add_argument(
        "--corr-legend-template",
        default="{pdf} (corr: {hist})",
        help=(
            "Legend label template for corr curves. "
            "Available fields: {pdf}, {corr}, {hist}."
        ),
    )
    parser.add_argument(
        "--minnlo-legend-template",
        default="{pdf} (minnlo: {hist})",
        help=(
            "Legend label template for MINNLO curves. "
            "Available fields: {pdf}, {pdf_token}, {hist}."
        ),
    )
    parser.add_argument(
        "--axes",
        nargs="+",
        default=[],
        help="Axes to keep before plotting; remaining axes are unrolled.",
    )
    parser.add_argument(
        "--select",
        nargs="+",
        dest="selection",
        type=str,
        default=None,
        help="Selections before projection: 'axis value' or 'axis low high'.",
    )
    parser.add_argument(
        "--corr-vars",
        default="0",
        help="Selection on 'vars' axis for corr hists (default: 0).",
    )
    parser.add_argument(
        "--minnlo-pdfvar",
        default="0",
        help="Selection on 'pdfVar' axis for MINNLO hists (default: 0).",
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
        help="Manual ratio range. If omitted, auto-range is used.",
    )
    parser.add_argument(
        "--autorrange",
        type=float,
        default=0.05,
        help="Padding fraction used when ratio auto-range is active.",
    )
    parser.add_argument(
        "--oname",
        default="nominal_vs_alternate_pdfs_from_dir",
        help="Output name stem.",
    )
    parser.add_argument("--postfix", default="", help="Optional output postfix.")
    parser.add_argument(
        "--outdir",
        default=os.path.join(
            os.environ.get("MY_PLOT_DIR", "."),
            datetime.datetime.now().strftime("%y%m%d_pdf_from_corrs_bias_test"),
        ),
        help="Output directory.",
    )
    return parser.parse_args()


def load_results_h5py(h5file):
    if "results" in h5file.keys():
        return ioutils.pickle_load_h5py(h5file["results"])
    return {k: ioutils.pickle_load_h5py(v) for k, v in h5file.items()}


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


def apply_category_axis_selection(h, axis_name, selector):
    axis = h.axes[axis_name]
    try:
        idx = int(selector)
        selected = axis[idx]
    except (ValueError, TypeError, IndexError):
        selected = selector
    return h[{axis_name: selected}]


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


def infer_pdf_key_from_filename(path):
    stem = os.path.basename(path).replace(".hdf5", "")
    for pdf in sorted(PDF_TO_THEORY_CORR.keys(), key=len, reverse=True):
        if stem == f"mz_dilepton_{pdf}" or stem.endswith(f"_{pdf}"):
            return pdf
    match = re.match(r"^mz_dilepton_(.+)$", stem)
    if match:
        pdf = match.group(1).lower()
        if pdf in PDF_TO_THEORY_CORR:
            return pdf
    return None


def find_input_files(input_dir):
    files = []
    for fname in os.listdir(input_dir):
        if fname.startswith("mz_dilepton_") and fname.endswith(".hdf5"):
            files.append(os.path.join(input_dir, fname))
    return sorted(files)


def get_hist_from_file(path, proc, hist_name):
    with h5py.File(path, "r") as h5file:
        results = load_results_h5py(h5file)
        if proc not in results:
            raise KeyError(
                f"Process '{proc}' not in {path}; keys={list(results.keys())}"
            )
        output = results[proc].get("output", {})
        if hist_name not in output:
            return None
        entry = output[hist_name]
        return entry if isinstance(entry, Hist) else entry.get()


def resolve_corr_hist_name(pdf):
    corr = PDF_TO_THEORY_CORR[pdf]
    return [
        f"nominal_{corr}_pdfvars_CorrByHelicity",
        f"nominal_{corr}_Corr",
    ]


def resolve_minnlo_hist_name(pdf):
    info = theory_tools.pdfMap.get(pdf)
    if not info:
        return [f"nominal_pdf{pdf.upper()}ByHelicity", f"nominal_pdf{pdf.upper()}"]
    map_name = info["name"]
    token = map_name[3:] if map_name.startswith("pdf") else map_name
    return [
        f"nominal_pdf{token}ByHelicity",
        f"nominal_pdf{token}",
    ]


def get_pdf_token(pdf):
    info = theory_tools.pdfMap.get(pdf)
    if not info:
        return pdf.upper()
    map_name = info["name"]
    return map_name[3:] if map_name.startswith("pdf") else map_name


def first_existing_hist(path, proc, names):
    for n in names:
        h = get_hist_from_file(path, proc, n)
        if h is not None:
            return n, h
    return None, None


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    file_map = {}
    for path in find_input_files(args.input_dir):
        pdf = infer_pdf_key_from_filename(path)
        if pdf is not None:
            file_map[pdf] = path

    selected_pdfs = [p for p in args.pdfs if p in file_map]
    missing = [p for p in args.pdfs if p not in file_map]
    if missing:
        print(f"Missing files for PDFs (skipped): {missing}")
    if not selected_pdfs:
        raise RuntimeError(f"No matching input files found in {args.input_dir}")

    ref_pdf = args.reference_pdf if args.reference_pdf else selected_pdfs[0]
    if ref_pdf not in file_map:
        raise RuntimeError(f"Reference PDF '{ref_pdf}' has no matching file.")

    ref_nominal = get_hist_from_file(file_map[ref_pdf], args.proc, args.nominal_hist)
    if ref_nominal is None:
        raise RuntimeError(
            f"Nominal hist '{args.nominal_hist}' not found in {file_map[ref_pdf]}"
        )
    ref_nominal = prepare_hist(ref_nominal, args.axes, args.selection, args.binwnorm)

    hists = [ref_nominal]
    labels = [f"nominal (ref: {ref_pdf}, hist: {args.nominal_hist})"]
    linestyles = ["solid"]

    for pdf in selected_pdfs:
        path = file_map[pdf]
        corr_hist_names = resolve_corr_hist_name(pdf)
        corr_hist_name, corr_hist = first_existing_hist(
            path, args.proc, corr_hist_names
        )
        if corr_hist is None:
            print(f"Missing corr hist among {corr_hist_names} in {path}, skipping.")
        else:
            corr_hist = apply_category_axis_selection(corr_hist, "vars", args.corr_vars)
            corr_hist = prepare_hist(
                corr_hist, args.axes, args.selection, args.binwnorm
            )
            hists.append(corr_hist)
            labels.append(
                args.corr_legend_template.format(
                    pdf=pdf,
                    corr=PDF_TO_THEORY_CORR[pdf],
                    hist=corr_hist_name,
                )
            )
            linestyles.append("solid")

        if args.include_minnlo_pdfs:
            minnlo_hist_names = resolve_minnlo_hist_name(pdf)
            minnlo_hist_name, minnlo_hist = first_existing_hist(
                path, args.proc, minnlo_hist_names
            )
            if minnlo_hist is None:
                print(
                    f"Missing MINNLO hist among {minnlo_hist_names} in {path}, skipping."
                )
            else:
                minnlo_hist = apply_category_axis_selection(
                    minnlo_hist, "pdfVar", args.minnlo_pdfvar
                )
                minnlo_hist = prepare_hist(
                    minnlo_hist, args.axes, args.selection, args.binwnorm
                )
                hists.append(minnlo_hist)
                labels.append(
                    args.minnlo_legend_template.format(
                        pdf=pdf,
                        pdf_token=get_pdf_token(pdf),
                        hist=minnlo_hist_name,
                    )
                )
                linestyles.append("dashed")

    if len(hists) <= 1:
        raise RuntimeError("No comparison histograms were found.")

    xlabel = "Unrolled bin" if len(args.axes) != 1 else args.axes[0]
    use_auto_rrange = args.rrange is None
    rrange = args.rrange if args.rrange is not None else (0.98, 1.02)

    fig = plot_tools.makePlotWithRatioToRef(
        hists,
        labels,
        colors=build_cms_color_cycle(len(hists)),
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
