import numpy as np
import mplhep as hep
import matplotlib.pyplot as plt
from rabbit import io_tools
import sys, os
import argparse
import yaml
import datetime
from wums import output_tools

hep.style.use(hep.style.CMS)

ALPHA_S = 0.118
ALPHA_S_SIGMA = 2.0


def load_config(config_path):
    """Load YAML configuration file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def get_default_markers():
    """Return list of default markers."""
    return ["o", "s", "^", "v", "D", "P", "X", "*", "h", "+"]


def get_default_colors():
    """Return list of default colors."""
    return [
        "blue",
        "red",
        "green",
        "orange",
        "purple",
        "brown",
        "pink",
        "gray",
        "olive",
        "cyan",
    ]


def assign_defaults(fit_results):
    """Assign default markers and colors to fit results that don't have them specified."""
    default_markers = get_default_markers()
    default_colors = get_default_colors()

    marker_idx = 0
    color_idx = 0

    for name, result in fit_results.items():
        if "marker" not in result:
            result["marker"] = default_markers[marker_idx % len(default_markers)]
            marker_idx += 1
        if "color" not in result:
            result["color"] = default_colors[color_idx % len(default_colors)]
            color_idx += 1
        if "label" not in result:
            result["label"] = name  # Use the key name as default label


def add_atlas_results(ax, show_atlas):
    """Add ATLAS results to the plot if requested."""
    if not show_atlas:
        return

    # ATLAS results - you may need to adjust these values based on actual ATLAS measurements
    atlas_results = {
        "N4LLa": {"value": 0.9, "label": "ATLAS (N4LLa+N3LO)"},
        "N3LL+N3LO": {"value": 1.1, "label": "ATLAS (N3LL+NNLO)"},
    }

    for result_name, data in atlas_results.items():
        ax.axhline(data["value"], linestyle="--", color="black", alpha=0.7)
        ax.text(
            0.02,
            data["value"] * 1.001,
            data["label"],
            fontsize=14,
            color="black",
            ha="left",
            va="bottom",
            rotation=0,
        )


def main(args):
    """Main function to load config and create plot."""
    # Load configuration
    config = load_config(args.config)

    # Extract settings from config
    plot_title = config.get("plot_title", "MC Statistics Study")

    # Get fit results and assign defaults
    fit_results = config.get("fit_results", {})
    assign_defaults(fit_results)

    # Calculate uncertainties for each fit result
    uncertainties = {}

    for name, result in fit_results.items():
        file_path = result["file"]
        alpha_s_sigma = result.get("alpha_s_sigma", ALPHA_S_SIGMA)

        print(f"Processing: {file_path}")

        try:
            fitresult, meta = io_tools.get_fitresult(file_path, None, meta=True)

            out = io_tools.read_impacts_poi(
                fitresult,
                "pdfAlphaS",
                False,
                pulls=True,
                asym=False,
                add_total=True,
            )
            pulls, pulls_prefit, constraints, constraints_prefit, impacts, labels = out

            idx = np.where(labels == "pdfAlphaS")
            total = impacts[idx]
            uncertainties[name] = total * alpha_s_sigma

        except Exception as e:
            print(f"Error processing {name}: {e}")
            continue

    # Create the plot
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_ylabel(r"Uncertainty in $\alpha_\mathrm{S}$ in $10^{-3}$")

    # Set up x-axis labels
    labels = [fit_results[name]["label"] for name in uncertainties.keys()]
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels([] * len(labels), rotation=45, ha="right")

    # Plot the uncertainties
    for i, name in enumerate(uncertainties.keys()):
        result = fit_results[name]
        uncertainty = uncertainties[name]

        ax.scatter(
            i,
            uncertainty,
            marker=result["marker"],
            color=result["color"],
            s=100,
            label=(
                result["label"]
                if "show_in_legend" not in result or result["show_in_legend"]
                else None
            ),
        )

    # Add ATLAS results if requested
    add_atlas_results(ax, args.showATLAS)

    # Add legend if any items should be shown
    legend_handles = ax.get_legend_handles_labels()[0]
    if legend_handles:
        ax.legend(loc=(1.01, 0))

    # Save the plot
    fig.tight_layout()
    output_dir = args.output_dir
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Generate output filename
    postfix = f"_{args.postfix}" if args.postfix else ""
    fig.savefig(
        os.path.join(output_dir, f"fitresults{postfix}.png"),
        dpi=300,
        bbox_inches="tight",
    )
    fig.savefig(
        os.path.join(output_dir, f"fitresults{postfix}.pdf"), bbox_inches="tight"
    )
    output_tools.write_index_and_log(args.output_dir, f"fitresults{postfix}", args=args)

    print(f"Plots saved to {output_dir}")

    plt.show()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot alpha_S uncertainties from fit results specified in YAML config"
    )
    parser.add_argument("config", help="Path to YAML configuration file")
    parser.add_argument(
        "--showATLAS", action="store_true", help="Show ATLAS results on the plot"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=f"{os.environ['MY_PLOT_DIR']}{datetime.date.today().strftime('%y%m%d')}_fitresults",
        help="Output directory for plots. (default: %(default)s)",
    )
    parser.add_argument("--postfix", default="", help="Postfix for output filenames")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
