#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List


@dataclass
class Context:
    output_root: Path
    uncerts_out: Path
    reco_results: Path
    z_reco_results: Path
    plot_narf: Path | None = None
    pdf_bias_plot: Path | None = None
    z_input_h5: Path | None = None
    z_reco_carrot: Path | None = None
    z_reco_fit: Path | None = None
    pdf_bias_input_dir: Path | None = None
    rabbit_base: Path | None = None
    wrem_base: Path | None = None
    my_an_dir: Path | None = None


@dataclass
class Section:
    key: str
    runner: Callable[[Context], None]
    description: str
    children: List[str] = field(default_factory=list)


SECTION_REQUIREMENTS: Dict[str, set[str]] = {
    "4": {"MY_WORK_DIR", "MY_OUT_DIR", "RABBIT_BASE", "WREM_BASE"},
    "5.1": {"MY_OUT_DIR", "RABBIT_BASE", "WREM_BASE"},
    "5.2": {"MY_OUT_DIR", "MY_AN_DIR"},
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run figure production for AN sections."
    )
    parser.add_argument(
        "--output",
        choices=["an", "www"],
        default="an",
        help="Destination for plots: analysis folder (an) or www-ready folder (www).",
    )
    parser.add_argument(
        "--sections",
        nargs="+",
        help="Sections to run (e.g. 4, 5, 5.1). Default runs 4 and 5.*.",
    )
    return parser.parse_args(argv)


def env_path(var: str) -> Path:
    value = os.environ.get(var)
    if not value:
        raise SystemExit(f"Environment variable {var} is required to run this script.")
    return Path(value)


def build_output_root(mode: str) -> Path:
    if mode == "an":
        return env_path("MY_AN_DIR")
    if mode == "www":
        return env_path("MY_PLOT_DIR") / f"{datetime.now():%y%m%d}_AN_Figures"
    raise SystemExit(f"Unknown output mode '{mode}'.")


def ensure_env_variables(names: Iterable[str]) -> Dict[str, Path]:
    return {name: env_path(name) for name in names}


def expand_sections(requested: List[str], registry: Dict[str, Section]) -> List[str]:
    seen = set()
    expanded: List[str] = []
    for item in requested:
        if item not in registry:
            prefixed = [name for name in registry if name.startswith(f"{item}.")]
            if prefixed:
                for name in sorted(prefixed):
                    if name not in seen:
                        expanded.append(name)
                        seen.add(name)
                continue
            known = ", ".join(sorted(registry))
            raise SystemExit(f"Unknown section '{item}'. Known sections: {known}")

        section = registry[item]
        targets = section.children or [item]
        for target in targets:
            if target not in registry:
                raise SystemExit(
                    f"Section '{item}' references unknown child '{target}'."
                )
            if target not in seen:
                expanded.append(target)
                seen.add(target)
    return expanded


def required_env_vars(sections: List[str], output_mode: str) -> set[str]:
    envs: set[str] = set()
    for sec in sections:
        envs.update(SECTION_REQUIREMENTS.get(sec, set()))
    if output_mode == "an":
        envs.add("MY_AN_DIR")
    elif output_mode == "www":
        envs.add("MY_PLOT_DIR")
    return envs


def run_command(command: List[str]) -> None:
    printable = " ".join(shlex.quote(part) for part in command)
    print(f"[cmd] {printable}")
    subprocess.run(command, check=True)


def require_paths(section_label: str, required: Dict[str, Path | None]) -> None:
    missing = [name for name, value in required.items() if value is None]
    if missing:
        joined = ", ".join(sorted(missing))
        raise SystemExit(
            f"Section {section_label} requires environment variables: {joined}"
        )


def create_context(output_mode: str, sections_to_run: List[str]) -> Context:
    env_names = required_env_vars(sections_to_run, output_mode)
    env = ensure_env_variables(env_names)

    output_root = build_output_root(output_mode)
    uncerts_out = output_root / "Figures" / "uncertainties"
    reco_results = output_root / "Figures" / "detector_extraction"
    z_reco_results = reco_results / "Z_fit"
    for path in (uncerts_out, reco_results, z_reco_results):
        path.mkdir(parents=True, exist_ok=True)

    out_dir = env.get("MY_OUT_DIR")
    work_dir = env.get("MY_WORK_DIR")
    rabbit_base = env.get("RABBIT_BASE")
    wrem_base = env.get("WREM_BASE")
    my_an_dir = env.get("MY_AN_DIR")

    plot_narf = (
        work_dir / "scripts" / "plot_narf_hists.py" if work_dir is not None else None
    )
    pdf_bias_plot = (
        work_dir / "studies" / "pdf_bias_test" / "plot_results.py"
        if work_dir is not None
        else None
    )
    z_input_h5 = (
        out_dir / "251114_histmaker_dilepton" / "mz_dilepton_correctMbcIHope.hdf5"
        if out_dir is not None
        else None
    )
    z_reco_carrot = (
        out_dir
        / "251114_histmaker_dilepton"
        / "ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_correctMbcIHope"
        / "ZMassDilepton.hdf5"
        if out_dir is not None
        else None
    )
    z_reco_fit = (
        out_dir
        / "251114_histmaker_dilepton"
        / "ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_correctMbcIHope"
        / "fitresults.hdf5"
        if out_dir is not None
        else None
    )
    pdf_bias_input_dir = (
        out_dir / "251120_histmaker_dilepton_pdfs" if out_dir is not None else None
    )

    return Context(
        output_root=output_root,
        uncerts_out=uncerts_out,
        reco_results=reco_results,
        z_reco_results=z_reco_results,
        plot_narf=plot_narf,
        pdf_bias_plot=pdf_bias_plot,
        z_input_h5=z_input_h5,
        z_reco_carrot=z_reco_carrot,
        z_reco_fit=z_reco_fit,
        pdf_bias_input_dir=pdf_bias_input_dir,
        rabbit_base=rabbit_base,
        wrem_base=wrem_base,
        my_an_dir=my_an_dir,
    )


def run_section_4(ctx: Context) -> None:
    require_paths(
        "4",
        {
            "MY_WORK_DIR": ctx.plot_narf,
            "MY_OUT_DIR": ctx.z_input_h5,
            "RABBIT_BASE": ctx.rabbit_base,
            "WREM_BASE": ctx.wrem_base,
        },
    )

    commands = [
        [
            "python",
            str(ctx.plot_narf),
            str(ctx.z_input_h5),
            "--filterProcs",
            "ZmumuPostVFP",
            "--hists",
            "nominal",
            "nominal_pdfCT18Z",
            "nominal_pdfCT18ZUncertByHelicity",
            "--selectByHist",
            "",
            "pdfVar 2",
            "pdfVar 2",
            "--labels",
            "nominal",
            "via MiNNLO",
            "via helicities",
            "--axes",
            "ptll",
            "yll",
            "--binwnorm",
            "1",
            "--rrange",
            "0.97",
            "1.01",
            "--noRatioErrorBars",
            "--postfix",
            "fullAngularDistribution",
            "--legLoc",
            "0.7",
            "0.3",
            "-o",
            str(ctx.uncerts_out),
        ],
        [
            "python",
            str(ctx.plot_narf),
            str(ctx.z_input_h5),
            "--filterProcs",
            "ZmumuPostVFP",
            "--hists",
            "nominal",
            "nominal_pdfCT18Z",
            "nominal_pdfCT18ZUncertByHelicity",
            "--selectByHist",
            "",
            "pdfVar 2",
            "pdfVar 2",
            "--labels",
            "nominal",
            "via MiNNLO",
            "via helicities",
            "--axes",
            "ptll",
            "yll",
            "--binwnorm",
            "1",
            "--rrange",
            "0.97",
            "1.01",
            "--noRatioErrorBars",
            "--select",
            "cosThetaStarll_quantile 0",
            "phiStarll_quantile 0",
            "--postfix",
            "singleAngularBin",
            "--legLoc",
            "0.7",
            "0.3",
            "-o",
            str(ctx.uncerts_out),
        ],
        [
            "python",
            str(ctx.pdf_bias_plot),
            "--input-dir",
            str(ctx.pdf_bias_input_dir),
        ],
        [
            "python",
            str(ctx.pdf_bias_plot),
            "--input-dir",
            str(ctx.pdf_bias_input_dir),
            "--file-base",
            "ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_pdfBiasTest_Zmumu_scale1p0_",
            "--postfix",
            "scale1p0",
        ],
        [
            "python",
            str(ctx.rabbit_base / "bin" / "rabbit_plot_hists.py"),
            str(ctx.z_reco_fit),
            "-m",
            "Project ch0 ptll",
            "--prefit",
            "--config",
            str(ctx.wrem_base / "utilities" / "styles" / "styles.py"),
            "--title",
            "CMS",
            "--titlePos",
            "0",
            "-o",
            f"{ctx.uncerts_out}/",
            "--processGrouping",
            "z_dilepton",
            "--rrange",
            "0.88",
            "1.12",
            "--varName",
            "pdfAlphaS",
            "--varLabel",
            "$\\alpha_\\mathrm{S}{\\pm}1\\sigma$",
            "--yscale",
            "1.25",
            "--noExtraText",
            "--subtitle",
            "Preliminary",
            "--lowerLegPos",
            "upper right",
            "--noData",
            "--postfix",
            "alphas",
        ],
        [
            "python",
            str(ctx.rabbit_base / "bin" / "rabbit_plot_hists.py"),
            str(ctx.z_reco_fit),
            "-m",
            "Project ch0 ptll",
            "--prefit",
            "--config",
            str(ctx.wrem_base / "utilities" / "styles" / "styles.py"),
            "--title",
            "CMS",
            "--titlePos",
            "0",
            "-o",
            f"{ctx.uncerts_out}/",
            "--processGrouping",
            "z_dilepton",
            "--rrange",
            "0.88",
            "1.12",
            "--varName",
            "pdf22CT18ZSymAvg",
            "pdf4CT18ZSymDiff",
            "pdf26CT18ZSymDiff",
            "--varLabel",
            "CT18Z 22 (Avg.)",
            "CT18Z 4 (Diff.)",
            "CT18Z 26 (Diff.)",
            "--yscale",
            "1.25",
            "--noExtraText",
            "--subtitle",
            "Preliminary",
            "--lowerLegPos",
            "upper right",
            "--noData",
            "--postfix",
            "pdfs",
            "--showVariations",
            "both",
        ],
    ]

    for command in commands:
        run_command(command)


def run_section_5_impacts(ctx: Context) -> None:
    require_paths(
        "5.1",
        {
            "MY_OUT_DIR": ctx.z_reco_fit,
            "RABBIT_BASE": ctx.rabbit_base,
            "WREM_BASE": ctx.wrem_base,
        },
    )
    impacts_script = ctx.rabbit_base / "bin" / "rabbit_plot_pulls_and_impacts.py"
    commands = [
        [
            "python",
            str(impacts_script),
            str(ctx.z_reco_fit),
            "--poi",
            "pdfAlphaS",
            "--config",
            str(ctx.wrem_base / "utilities" / "styles" / "styles.py"),
            "--scaleImpacts",
            "2.0",
            "--showNumbers",
            "--oneSidedImpacts",
            "--grouping",
            "max",
            "-o",
            str(ctx.z_reco_results),
            "--otherExtensions",
            "pdf",
            "png",
            "-n",
            "50",
            "--poi",
            "pdfAlphaS",
            "--impactTitle",
            "<i>α</i><sub>S</sub> in 10<sup>-3</sup>",
            "--title",
            "CMS",
            "--subtitle",
            "Preliminary",
        ],
        [
            "python",
            str(impacts_script),
            str(ctx.z_reco_fit),
            "--poi",
            "pdfAlphaS",
            "--config",
            str(ctx.wrem_base / "utilities" / "styles" / "styles.py"),
            "--scaleImpacts",
            "2.0",
            "--showNumbers",
            "--oneSidedImpacts",
            "--grouping",
            "max",
            "-o",
            str(ctx.z_reco_results),
            "--otherExtensions",
            "pdf",
            "png",
            "-n",
            "50",
            "--poi",
            "pdfAlphaS",
            "--impactTitle",
            "<i>α</i><sub>S</sub> in 10<sup>-3</sup>",
            "--title",
            "CMS",
            "--subtitle",
            "Preliminary",
            "--globalImpacts",
        ],
    ]

    for command in commands:
        run_command(command)


def run_section_5_higher_orders(ctx: Context) -> None:
    require_paths(
        "5.2",
        {
            "MY_OUT_DIR": ctx.z_reco_fit,
            "MY_AN_DIR": ctx.my_an_dir,
        },
    )
    input_dir = ctx.z_reco_fit.parent.parent.parent / "251124_histmaker_dilepton_ho"
    output_dir = ctx.my_an_dir / "Figures" / "detector_extraction" / "Z_fit"
    run_command(
        [
            "python",
            "studies/higher_orders/plot_results.py",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ]
    )


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    default_sections = ["4", "5"]
    registry: Dict[str, Section] = {}

    registry["4"] = Section(
        key="4",
        runner=run_section_4,
        description="Systematics",
    )
    registry["5"] = Section(
        key="5",
        runner=lambda ctx: None,
        description="Detector-level extraction (all subsections)",
        children=["5.1", "5.2"],
    )
    registry["5.1"] = Section(
        key="5.1",
        runner=run_section_5_impacts,
        description="Detector-level extraction: pulls and impacts",
    )
    registry["5.2"] = Section(
        key="5.2",
        runner=run_section_5_higher_orders,
        description="Detector-level extraction: higher orders study",
    )

    requested = args.sections or default_sections
    sections_to_run = expand_sections(requested, registry)
    context = create_context(args.output, sections_to_run)

    print(f"Output root directory: {context.output_root}")
    for section_key in sections_to_run:
        section = registry[section_key]
        print(f"Running section {section_key}: {section.description}")
        section.runner(context)


if __name__ == "__main__":
    main()
