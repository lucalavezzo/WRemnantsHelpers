#!/usr/bin/env python3

import argparse
import datetime
import os
import warnings

import h5py
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np
from hist import Hist

from utilities import parsing
from wums import boostHistHelpers as hh
from wums import ioutils
from wums import output_tools
from wums import plot_tools

hep.style.use("CMS")
warnings.filterwarnings(
    "ignore",
    message="invalid value encountered in sqrt",
    category=RuntimeWarning,
    module="mplhep\\._utils",
)


def load_results_h5py(h5file):
    if "results" in h5file.keys():
        return ioutils.pickle_load_h5py(h5file["results"])
    return {k: ioutils.pickle_load_h5py(v) for k, v in h5file.items()}


def load_hist(entry):
    if isinstance(entry, Hist):
        return entry
    return entry.get()


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
    if axis_name not in h.axes.name:
        return h
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


def find_existing_hist(output_hists, candidates):
    for candidate in candidates:
        if candidate in output_hists:
            return candidate
    return None


def build_corr_hist_candidates(theory_corr):
    token = theory_corr
    if token.startswith("nominal_"):
        token = token[len("nominal_") :]
    if token.endswith("_CorrByHelicity"):
        token = token[: -len("_CorrByHelicity")]
    if token.endswith("_Corr"):
        token = token[: -len("_Corr")]

    tokens = [token]
    if token.endswith("_pdfvar"):
        tokens.append(token + "s")

    corr_candidates = []
    corr_by_helicity_candidates = []
    for tok in tokens:
        corr_candidates.append(f"nominal_{tok}_Corr")
        corr_by_helicity_candidates.append(f"nominal_{tok}_CorrByHelicity")
        corr_by_helicity_candidates.append(f"nominal_{tok}_pdfvars_CorrByHelicity")

    corr_candidates = list(dict.fromkeys(corr_candidates))
    corr_by_helicity_candidates = list(dict.fromkeys(corr_by_helicity_candidates))
    return corr_candidates, corr_by_helicity_candidates


def build_selection_text(args):
    select_text = ", ".join(args.selection) if args.selection else "none"
    return f"Selections: {select_text}\ncorr-vars: {args.corr_vars}"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Validate helicity smoothing by plotting the distribution of per-bin "
            "residuals: nominal_<theory_corr>_Corr - "
            "nominal_<theory_corr>_CorrByHelicity."
        )
    )
    parser.add_argument("infile", help="Input histmaker HDF5 file.")
    parser.add_argument(
        "--proc",
        default="ZmumuPostVFP",
        help="Process key inside the HDF5 results dictionary.",
    )
    parser.add_argument(
        "--theory-corr",
        required=True,
        help=(
            "Theory correction token used in histogram names, i.e. "
            "'nominal_<theory_corr>_Corr'."
        ),
    )
    parser.add_argument(
        "--axes",
        nargs="+",
        default=[],
        help="Axes to keep before residual computation. Remaining axes are unrolled.",
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
        help="Selection on 'vars' axis for correction histograms.",
    )
    parser.add_argument(
        "--binwnorm",
        type=int,
        default=1,
        help="Bin-width normalization for unrolled histograms.",
    )
    parser.add_argument(
        "--residual-bins",
        type=int,
        default=60,
        help="Number of bins for the residual-value distribution.",
    )
    parser.add_argument(
        "--residual-range",
        type=float,
        nargs=2,
        default=None,
        help="Optional x-range for residual-value distribution.",
    )
    parser.add_argument(
        "--oname",
        default=None,
        help="Output name stem. Default: validate_helicity_smoothing_<theory_corr>.",
    )
    parser.add_argument("--postfix", default="", help="Optional output postfix.")
    parser.add_argument(
        "--outdir",
        default=os.path.join(
            os.environ.get("MY_PLOT_DIR", "."),
            datetime.datetime.now().strftime("%y%m%d_validate_helicity_smoothing"),
        ),
        help="Output directory.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    corr_candidates, corr_by_helicity_candidates = build_corr_hist_candidates(
        args.theory_corr
    )

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
        if "nominal" not in output_hists:
            raise KeyError("Histogram 'nominal' not found in process output.")
        corr_name = find_existing_hist(output_hists, corr_candidates)
        if corr_name is None:
            raise KeyError(
                f"Could not find Corr histogram. Tried: {corr_candidates}. "
                f"Available histograms: {list(output_hists.keys())}"
            )

        corr_by_helicity_name = find_existing_hist(
            output_hists, corr_by_helicity_candidates
        )
        if corr_by_helicity_name is None:
            raise KeyError(
                "Could not find CorrByHelicity histogram. Tried: "
                f"{corr_by_helicity_candidates}"
            )

        h_nominal_raw = load_hist(output_hists["nominal"])
        h_corr_raw = load_hist(output_hists[corr_name])
        h_corr_by_helicity_raw = load_hist(output_hists[corr_by_helicity_name])

    h_corr = apply_category_axis_selection(h_corr_raw, "vars", args.corr_vars)
    h_corr_by_helicity = apply_category_axis_selection(
        h_corr_by_helicity_raw, "vars", args.corr_vars
    )

    h_corr = prepare_hist(h_corr, args.axes, args.selection, args.binwnorm)
    h_corr_by_helicity = prepare_hist(
        h_corr_by_helicity, args.axes, args.selection, args.binwnorm
    )

    if h_corr.axes.name != h_corr_by_helicity.axes.name:
        raise ValueError(
            "Histogram axes do not match after selections/projection: "
            f"{h_corr.axes.name} vs {h_corr_by_helicity.axes.name}"
        )

    residual_vals = (
        h_corr.values(flow=False).ravel()
        - h_corr_by_helicity.values(flow=False).ravel()
    )
    finite_vals = residual_vals[np.isfinite(residual_vals)]
    if finite_vals.size == 0:
        raise RuntimeError("Residual histogram has no finite values to plot.")

    if args.residual_range is not None:
        xmin, xmax = args.residual_range
    else:
        xmin = float(np.min(finite_vals))
        xmax = float(np.max(finite_vals))
        span = xmax - xmin
        pad = 0.05 * span if span > 0 else max(1e-6, abs(xmax) * 0.05 + 1e-6)
        xmin -= pad
        xmax += pad

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.hist(
        finite_vals,
        bins=args.residual_bins,
        range=(xmin, xmax),
        histtype="step",
        color="black",
        linewidth=1.8,
        label="Residuals",
    )
    ax.axvline(0.0, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("Residual value: Corr - CorrByHelicity")
    ax.set_ylabel("Entries")
    ax.set_title(
        corr_name.replace("nominal_", "").replace("_Corr", ""), fontsize="x-small"
    )
    ax.text(
        0.98,
        0.98,
        build_selection_text(args),
        transform=ax.transAxes,
        va="top",
        ha="right",
        fontsize="x-small",
        bbox=dict(
            boxstyle="round,pad=0.2", facecolor="white", alpha=0.7, edgecolor="none"
        ),
    )
    fig.tight_layout()

    outname = (
        args.oname
        if args.oname
        else f"validate_helicity_smoothing_{args.theory_corr.replace('/', '_')}"
    )
    if args.postfix:
        outname += f"_{args.postfix}"

    fig.savefig(os.path.join(args.outdir, f"{outname}.pdf"), bbox_inches="tight")
    fig.savefig(
        os.path.join(args.outdir, f"{outname}.png"), dpi=300, bbox_inches="tight"
    )
    plt.close(fig)

    h_nominal_unrolled = prepare_hist(
        apply_category_axis_selection(h_nominal_raw, "vars", args.corr_vars),
        args.axes,
        args.selection,
        args.binwnorm,
    )
    h_corr_unrolled = prepare_hist(
        apply_category_axis_selection(h_corr_raw, "vars", args.corr_vars),
        args.axes,
        args.selection,
        args.binwnorm,
    )
    h_corr_by_helicity_unrolled = prepare_hist(
        apply_category_axis_selection(h_corr_by_helicity_raw, "vars", args.corr_vars),
        args.axes,
        args.selection,
        args.binwnorm,
    )

    fig_unrolled = plot_tools.makePlotWithRatioToRef(
        [h_nominal_unrolled, h_corr_unrolled, h_corr_by_helicity_unrolled],
        ["nominal", "Corr", "CorrByHelicity"],
        colors=["black", "tab:blue", "tab:orange"],
        linestyles=["solid", "solid", "dashed"],
        xlabel="Unrolled bin",
        ylabel="Events",
        rlabel=["x/nominal"],
        autorrange=True,
        ratio_legend=False,
        yerr=False,
        binwnorm=args.binwnorm if len(args.axes) == 1 else None,
    )
    for axis in fig_unrolled.axes:
        axis.xaxis.set_major_locator(mticker.MaxNLocator(nbins=12))
    if fig_unrolled.axes:
        ax_main_unrolled = fig_unrolled.axes[0]
        ax_main_unrolled.legend(loc="upper left", fontsize="small")
        ax_main_unrolled.text(
            0.98,
            0.98,
            build_selection_text(args),
            transform=ax_main_unrolled.transAxes,
            va="top",
            ha="right",
            fontsize="x-small",
            bbox=dict(
                boxstyle="round,pad=0.2",
                facecolor="white",
                alpha=0.7,
                edgecolor="none",
            ),
        )
        ax_main_unrolled.set_title(
            corr_name.replace("nominal_", "").replace("_Corr", ""),
            fontsize="x-small",
        )

    unrolled_name = f"{outname}_unrolled_{'_'.join(args.axes) if args.axes else 'all'}"
    fig_unrolled.savefig(
        os.path.join(args.outdir, f"{unrolled_name}.pdf"), bbox_inches="tight"
    )
    fig_unrolled.savefig(
        os.path.join(args.outdir, f"{unrolled_name}.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig_unrolled)

    output_tools.write_index_and_log(args.outdir, outname, args=args)

    print(f"Corr histogram:          {corr_name}")
    print(f"CorrByHelicity histogram: {corr_by_helicity_name}")
    print(
        "Residual summary: "
        f"mean={np.mean(finite_vals):.6e}, "
        f"std={np.std(finite_vals):.6e}, "
        f"max_abs={np.max(np.abs(finite_vals)):.6e}, "
        f"n={finite_vals.size}"
    )
    print(f"Saved {os.path.join(args.outdir, outname)}(.pdf)(.png)(.log)")
    print(f"Saved {os.path.join(args.outdir, unrolled_name)}(.pdf)(.png)")


if __name__ == "__main__":
    main()
