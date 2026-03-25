#!/usr/bin/env python3

import argparse
import datetime
import os
import pickle

import lz4.frame
import matplotlib.pyplot as plt
import mplhep as hep
from wums import output_tools
from wums import plot_tools

hep.style.use("CMS")


def _resolve_axis(axis_name, available_axes):
    if axis_name not in available_axes:
        raise ValueError(
            f"Axis '{axis_name}' not found. Available axes: {available_axes}"
        )
    return axis_name


def _pick_corr_hist(corr_payload, corr_name=None):
    available_hists = [
        key for key, value in corr_payload.items() if hasattr(value, "axes")
    ]
    if corr_name:
        preferred = [f"{corr_name}_hist"]
        for key in preferred:
            if key in corr_payload and hasattr(corr_payload[key], "axes"):
                return key
        raise ValueError(
            f"Could not find corr histogram for corr '{corr_name}'. "
            f"Tried {preferred}. Available histograms: {available_hists}"
        )

    candidates = [
        key
        for key in available_hists
        if key != "minnlo_ref_hist"
        and not key.endswith("_ratio")
        and not key.endswith("_minnlo_ratio")
    ]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        raise ValueError(
            "Multiple corr-like histograms found. Use --corrName or --hist to disambiguate. "
            f"Candidates: {candidates}"
        )
    raise ValueError(
        "No corr-like histogram found in payload. "
        f"Available histograms: {available_hists}"
    )


def _default_vars(var_labels):
    preferred = ["as0118", "as0116", "as0120"]
    if all(v in var_labels for v in preferred):
        return preferred
    return var_labels[: min(3, len(var_labels))]


def _project_hist(h, axis_name, var_axis=None, var_value=None):
    for ax in list(h.axes.name):
        if ax == axis_name or ax == var_axis:
            continue
        h = h[{ax: sum}]
    if var_axis and var_axis in h.axes.name:
        h = h[{var_axis: var_value}]
    return h


def main():
    parser = argparse.ArgumentParser(
        description="Plot histograms from .pkl.lz4 corr files."
    )
    parser.add_argument("infile", type=str, help="Input .pkl.lz4 correction file.")
    parser.add_argument(
        "--corr",
        type=str,
        default="Z",
        help="Top-level correction key to load (default: Z).",
    )
    parser.add_argument(
        "--hist",
        type=str,
        default=None,
        help="Corr histogram key inside the selected correction payload.",
    )
    parser.add_argument(
        "--ref-hist",
        type=str,
        default="minnlo_ref_hist",
        help="Reference histogram key inside the selected correction payload.",
    )
    parser.add_argument(
        "--corrName",
        type=str,
        default=None,
        help="Base correction name used to select corr histogram '<corrName>_hist'.",
    )
    parser.add_argument(
        "--axis",
        type=str,
        default="qT",
        help="Axis to plot (must match a histogram axis name exactly).",
    )
    parser.add_argument(
        "--varAxis",
        type=str,
        default="vars",
        help="Category axis that stores variations (default: vars).",
    )
    parser.add_argument(
        "--vars",
        nargs="+",
        type=str,
        default=None,
        help="Variation labels to plot. If omitted, picks nominal/down/up when available.",
    )
    parser.add_argument(
        "--xlim",
        type=float,
        nargs=2,
        default=None,
        help="x-axis limits.",
    )
    parser.add_argument(
        "--xlabel",
        type=str,
        default=None,
        help="x-axis label override.",
    )
    parser.add_argument(
        "--ylabel",
        type=str,
        default="Events",
        help="y-axis label.",
    )
    parser.add_argument(
        "--binwnorm",
        type=float,
        default=1.0,
        help="Bin-width normalization factor passed to wums plotting (default: 1).",
    )
    parser.add_argument(
        "--logy",
        action="store_true",
        help="Use logarithmic y-axis.",
    )
    parser.add_argument(
        "--autorrange",
        action="store_true",
        help="Auto-set ratio-panel y-range from plotted ratios.",
    )
    parser.add_argument(
        "--rrange",
        type=float,
        nargs=2,
        default=(0.95, 1.05),
        help="Default y-range for ratio panel when --autorrange is not used.",
    )
    parser.add_argument(
        "--outname",
        type=str,
        default=None,
        help="Output basename (without extension).",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        default=os.path.join(
            os.environ.get("MY_PLOT_DIR", "."),
            datetime.datetime.now().strftime("%y%m%d") + "_plot_corr/",
        ),
        help="Output directory.",
    )
    args = parser.parse_args()

    with lz4.frame.open(args.infile, "rb") as f:
        data = pickle.load(f)

    if args.corr not in data:
        raise KeyError(
            f"Correction '{args.corr}' not found in file. Available top-level keys: {list(data.keys())}"
        )

    payload = data[args.corr]
    corr_hist_name = args.hist if args.hist else _pick_corr_hist(payload, args.corrName)
    ref_hist_name = args.ref_hist

    if corr_hist_name not in payload:
        raise KeyError(
            f"Corr histogram '{corr_hist_name}' not found under '{args.corr}'. "
            f"Available keys: {list(payload.keys())}"
        )
    if ref_hist_name not in payload:
        raise KeyError(
            f"Reference histogram '{ref_hist_name}' not found under '{args.corr}'. "
            f"Available keys: {list(payload.keys())}"
        )

    h_corr = payload[corr_hist_name]
    h_ref = payload[ref_hist_name]
    axis_name = _resolve_axis(args.axis, h_corr.axes.name)
    if axis_name not in h_ref.axes.name:
        raise ValueError(
            f"Axis '{axis_name}' not found in reference histogram. "
            f"Reference axes: {h_ref.axes.name}"
        )

    has_var_axis = args.varAxis in h_corr.axes.name and args.varAxis in h_ref.axes.name
    if args.varAxis in h_corr.axes.name and args.varAxis not in h_ref.axes.name:
        raise ValueError(
            f"Variation axis '{args.varAxis}' exists in corr histogram but not in reference. "
            f"Reference axes: {h_ref.axes.name}"
        )
    if args.varAxis in h_ref.axes.name and args.varAxis not in h_corr.axes.name:
        raise ValueError(
            f"Variation axis '{args.varAxis}' exists in reference histogram but not in corr. "
            f"Corr axes: {h_corr.axes.name}"
        )

    if has_var_axis:
        corr_vars = list(h_corr.axes[args.varAxis])
        ref_vars = set(h_ref.axes[args.varAxis])
        available_vars = [v for v in corr_vars if v in ref_vars]
        if not available_vars:
            raise ValueError(
                f"No common variation labels on axis '{args.varAxis}' between corr and ref."
            )
        if args.vars:
            str_to_label = {str(v): v for v in available_vars}
            vars_to_plot = [
                v if v in available_vars else str_to_label.get(v, v) for v in args.vars
            ]
        else:
            vars_to_plot = _default_vars(available_vars)
        missing_vars = [v for v in vars_to_plot if v not in available_vars]
        if missing_vars:
            raise ValueError(
                f"Requested vars not found: {missing_vars}. Available vars: {available_vars}"
            )
    else:
        vars_to_plot = [None]

    for var in vars_to_plot:
        h_corr_var = _project_hist(
            h_corr, axis_name, args.varAxis if has_var_axis else None, var
        )
        h_ref_var = _project_hist(
            h_ref, axis_name, args.varAxis if has_var_axis else None, var
        )
        var_label = str(var) if var is not None else "all"
        use_auto_rrange = args.autorrange
        rrange = None if use_auto_rrange else [args.rrange]
        fig = plot_tools.makePlotWithRatioToRef(
            [h_ref_var, h_corr_var],
            [f"{ref_hist_name} [{var_label}]", f"{corr_hist_name} [{var_label}]"],
            xlabel=args.xlabel if args.xlabel else axis_name,
            ylabel=args.ylabel,
            rlabel=["Corr/Ref"],
            rrange=rrange,
            autorrange=use_auto_rrange,
            ratio_legend=False,
            yerr=False,
            binwnorm=args.binwnorm,
            base_size=10,
        )

        ax_main = fig.axes[0]
        ax_ratio = fig.axes[-1]
        if args.logy:
            ax_main.set_yscale("log")
        if args.xlim:
            ax_main.set_xlim(args.xlim)
            ax_ratio.set_xlim(args.xlim)
        ax_main.legend(loc="best", fontsize="small")
        plot_tools.add_cms_decor(ax_main, "Preliminary", lumi=16.8, loc=0)

        if not os.path.exists(args.outdir):
            os.makedirs(args.outdir)

        if args.outname:
            outbase = f"{args.outname}_{var_label}"
        else:
            outbase = f"{args.corr}_{corr_hist_name}_vs_{ref_hist_name}_{axis_name}_{var_label}"
        outpath = os.path.join(args.outdir, outbase)

        fig.savefig(outpath + ".png", dpi=300, bbox_inches="tight")
        fig.savefig(outpath + ".pdf", bbox_inches="tight")
        plt.close(fig)
        output_tools.write_index_and_log(args.outdir, outbase, args=args)
        print(f"Saved {outpath}.png/.pdf")


if __name__ == "__main__":
    main()
