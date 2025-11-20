#!/usr/bin/env python3

import argparse
import pathlib
import sys
from typing import Iterable, Tuple

import hist
from hist import tag
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np


REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
WREMNANTS_PATH = REPO_ROOT / "WRemnants"
if str(WREMNANTS_PATH) not in sys.path:
    sys.path.append(str(WREMNANTS_PATH))

from wremnants.theory_corrections import load_corr_hist  # noqa: E402
from wums import boostHistHelpers as hh  # noqa: E402


hep.style.use("CMS")
_SLICER = tag.Slicer()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two correction histograms through their ratio and residuals."
    )
    parser.add_argument("numerator", help="Path to numerator .pkl.lz4 file.")
    parser.add_argument("denominator", help="Path to denominator .pkl.lz4 file.")
    parser.add_argument(
        "--proc",
        default="Z",
        help="Process key to pick from the correction dictionaries (e.g. 'W' or 'Z').",
    )
    parser.add_argument(
        "--num-hist",
        required=True,
        help="Histogram name to extract from the numerator file.",
    )
    parser.add_argument(
        "--den-hist",
        required=True,
        help="Histogram name to extract from the denominator file.",
    )
    parser.add_argument(
        "--axes",
        nargs="+",
        default=["qT"],
        help="Axes to keep before plotting. Remaining axes are unrolled.",
    )
    parser.add_argument(
        "--select",
        nargs=2,
        action="append",
        metavar=("AXIS", "VALUE"),
        help="Select a single bin along an axis before projection. "
        "Use numeric bin indices for numerical axes or labels for categorical axes.",
    )
    parser.add_argument(
        "--num-label",
        default="numerator",
        help="Label used for the numerator histogram in the legend.",
    )
    parser.add_argument(
        "--den-label",
        default="denominator",
        help="Label used for the denominator histogram in the legend.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file stem. When set, figures are written as '<stem>_ratio.<fmt>' "
        "and '<stem>_residuals.<fmt>'.",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["png"],
        help="File formats to use when saving the figures (default: png).",
    )
    parser.add_argument(
        "--ratio-range",
        type=float,
        nargs=2,
        default=None,
        metavar=("YMIN", "YMAX"),
        help="Optional y-axis range for the ratio plot.",
    )
    parser.add_argument(
        "--residual-range",
        type=float,
        nargs=2,
        default=None,
        metavar=("XMIN", "XMAX"),
        help="Optional x-axis range for the residual distribution histogram.",
    )
    parser.add_argument(
        "--residual-bins",
        type=int,
        default=30,
        help="Number of bins for the residual distribution histogram (default: 30).",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional title for the ratio figure.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the plots even when '--output' is provided.",
    )
    return parser.parse_args()


def _apply_selection(h: hist.Hist, selections: Iterable[Tuple[str, str]]) -> hist.Hist:
    if not selections:
        return h
    for axis_name, raw_value in selections:
        if axis_name not in h.axes.name:
            raise KeyError(
                f"Axis '{axis_name}' not found in histogram axes {h.axes.name}"
            )
        axis = h.axes[axis_name]
        if isinstance(axis, hist.axis.StrCategory):
            value = raw_value
            if value not in axis:
                raise KeyError(f"Label '{value}' not available on axis '{axis_name}'")
            h = h[{axis_name: value}]
        else:
            try:
                value = int(raw_value)
            except ValueError as exc:
                raise ValueError(
                    f"Selection for axis '{axis_name}' requires an integer bin index."
                ) from exc
            h = h[{axis_name: _SLICER[value]}]
    return h


def _project_axes(h: hist.Hist, axes_to_keep: Iterable[str]) -> hist.Hist:
    if not axes_to_keep:
        return h
    missing = [ax for ax in axes_to_keep if ax not in h.axes.name]
    if missing:
        raise KeyError(
            f"Axes {missing} are not present in histogram axes {h.axes.name}"
        )
    return h.project(*axes_to_keep)


def _compute_ratio(numerator: hist.Hist, denominator: hist.Hist) -> hist.Hist:
    ratio = hh.divideHists(numerator, denominator, flow=False)
    return ratio


def _compute_residuals(ratio: hist.Hist) -> hist.Hist:
    values = ratio.values(flow=False)
    variances = ratio.variances(flow=False)
    sigmas = np.sqrt(variances)
    residual_vals = np.zeros_like(values)
    np.divide(values - 1.0, sigmas, out=residual_vals, where=sigmas > 0)
    print(values)
    print(variances)
    print(residual_vals)
    residual_hist = hist.Hist(*ratio.axes, storage=hist.storage.Double())
    residual_hist[...] = residual_vals
    return residual_hist


def _prepare_for_plotting(h: hist.Hist) -> hist.Hist:
    if h.ndim == 1:
        return h
    return hh.unrolledHist(h)


def _plot_ratio(ratio: hist.Hist, args: argparse.Namespace) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    hep.histplot(
        ratio,
        ax=ax,
        histtype="step",
        yerr=True,
        label=f"{args.num_label}/{args.den_label}",
    )
    ax.axhline(1.0, color="black", linestyle="--", linewidth=1)
    ax.set_ylabel("Ratio")
    if args.ratio_range:
        ax.set_ylim(*args.ratio_range)
    x_axis = ratio.axes[0]
    ax.set_xlabel(x_axis.label or x_axis.name or "Bin")
    ax.legend()
    if args.title:
        ax.set_title(args.title)
    fig.tight_layout()
    return fig


def _plot_residual_hist(residual: hist.Hist, args: argparse.Namespace) -> plt.Figure:
    residual_values = residual.values(flow=False).ravel()
    finite_values = residual_values[np.isfinite(residual_values)]

    if finite_values.size:
        if args.residual_range:
            xmin, xmax = args.residual_range
        else:
            data_min = float(finite_values.min())
            data_max = float(finite_values.max())
            span = data_max - data_min
            padding = 0.1 * span if span > 0 else 1.0
            xmin = data_min - padding
            xmax = data_max + padding
    else:
        if args.residual_range:
            xmin, xmax = args.residual_range
        else:
            xmin, xmax = -5.0, 5.0

    residual_axis = hist.axis.Regular(
        args.residual_bins,
        xmin,
        xmax,
        name="residuals",
        label="(R - 1) / σ_R",
        underflow=False,
        overflow=False,
    )
    residual_dist = hist.Hist(residual_axis, storage=hist.storage.Weight())
    if finite_values.size:
        residual_dist.fill(residuals=finite_values)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    hep.histplot(
        residual_dist,
        ax=ax,
        histtype="step",
        yerr=True,
        color="tab:red",
        label="Residuals",
    )
    ax.axvline(0.0, color="black", linestyle="--", linewidth=1)
    ax.set_xlabel(residual_dist.axes[0].label)
    ax.set_ylabel("Entries")
    ax.set_xlim(xmin, xmax)
    ax.legend()
    fig.tight_layout()
    return fig


def main() -> None:
    args = _parse_args()

    numerator = load_corr_hist(args.numerator, args.proc, args.num_hist)
    denominator = load_corr_hist(args.denominator, args.proc, args.den_hist)

    numerator = _apply_selection(numerator, args.select)
    denominator = _apply_selection(denominator, args.select)

    numerator = _project_axes(numerator, args.axes)
    denominator = _project_axes(denominator, args.axes)

    ratio_hist = _compute_ratio(numerator, denominator)
    residual_hist = _compute_residuals(ratio_hist)

    ratio_plot = _prepare_for_plotting(ratio_hist)
    residual_plot = _prepare_for_plotting(residual_hist)

    fig_ratio = _plot_ratio(ratio_plot, args)
    fig_residual = _plot_residual_hist(residual_plot, args)

    residual_vals = residual_plot.values(flow=False)
    finite_mask = np.isfinite(residual_vals)
    if finite_mask.any():
        print(
            f"Residuals: mean={np.mean(residual_vals[finite_mask]):.3f}, "
            f"std={np.std(residual_vals[finite_mask]):.3f}, "
            f"max|z|={np.max(np.abs(residual_vals[finite_mask])):.3f}"
        )
    else:
        print("Residuals contain no finite entries.")

    if args.output:
        output_stem = pathlib.Path(args.output)
        output_parent = output_stem.parent
        output_parent.mkdir(parents=True, exist_ok=True)
        base_name = output_stem.stem if output_stem.suffix else output_stem.name
        ratio_stem = output_parent / f"{base_name}_ratio"
        residual_stem = output_parent / f"{base_name}_residuals"

        for fmt in args.formats:
            fig_ratio.savefig(
                ratio_stem.with_suffix(f".{fmt}"), dpi=300, bbox_inches="tight"
            )
            fig_residual.savefig(
                residual_stem.with_suffix(f".{fmt}"), dpi=300, bbox_inches="tight"
            )

    if args.show or not args.output:
        plt.show()
    else:
        plt.close(fig_ratio)
        plt.close(fig_residual)


if __name__ == "__main__":
    main()
