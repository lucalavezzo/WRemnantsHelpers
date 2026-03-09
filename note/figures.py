#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SUBTITLE = "Preliminary"
VALID_SECTIONS = {"4", "5", "6", "7"}
SECTIONS_HELP = """
Section(s) to run, specified as a comma-separated list, matching the numbering in the AN. Valid sections are:
4: Uncertainties
5: Detector-level extraction results
6: Unfolding results
7: Generator-level extraction results
"""


Task = dict[str, Any]


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def resolve_paths(output_mode: str) -> dict[str, str]:
    my_out_dir = require_env("MY_OUT_DIR")
    my_work_dir = require_env("MY_WORK_DIR")
    wrem_base = require_env("WREM_BASE")
    rabbit_base = require_env("RABBIT_BASE")

    if output_mode == "an":
        output_root = require_env("MY_AN_DIR")
    elif output_mode == "www":
        my_plot_dir = require_env("MY_PLOT_DIR")
        output_root = str(Path(my_plot_dir) / f"{datetime.now():%y%m%d}_AN_Figures")
    else:
        raise RuntimeError(f"Invalid --output '{output_mode}', expected 'an' or 'www'.")

    paths = {
        "my_out_dir": my_out_dir,
        "my_work_dir": my_work_dir,
        "wrem_base": wrem_base,
        "rabbit_base": rabbit_base,
        "plot_narf": str(Path(my_work_dir) / "scripts/plot_narf_hists.py"),
        "z_input_h5": str(
            Path(my_out_dir) / "260303_histmaker_dilepton_unfolding/mz_dilepton.hdf5"
        ),
        "z_reco_carrot": str(
            Path(my_out_dir)
            / "260303_histmaker_dilepton_unfolding/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton.hdf5"
        ),
        "z_reco_fit": str(
            Path(my_out_dir)
            / "260303_histmaker_dilepton_unfolding/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5"
        ),
        "w_reco_carrot": str(
            Path(my_out_dir)
            / "260304_WZRecoFit/Combination_ZMassDileptonWMass/Combination.hdf5"
        ),
        "wz_reco_fit": str(
            Path(my_out_dir)
            / "260304_WZRecoFit/Combination_ZMassDileptonWMass/fitresults.hdf5"
        ),
        "wz_unfolding_fit_composite": str(
            Path(my_out_dir)
            / "260304_WZSimultaneousUnfolding/Combination_ZMassDileptonWMass/fitresults_asimov.hdf5"
        ),
        "wz_unfolding_fit_mappings": str(
            Path(my_out_dir)
            / "260304_WZSimultaneousUnfolding/Combination_ZMassDileptonWMass/fitresults_mappings_asimov.hdf5"
        ),
        "wz_gen_fit": str(
            Path(my_out_dir)
            / "260304_WZSimultaneousUnfolding/Combination_ZMassDileptonWMass/Combination_WMassZMassDilepton_noQCDscalesZ_flipped/fitresults.hdf5"
        ),
        "z_gen_fit": str(
            Path(my_out_dir)
            / "260303_histmaker_dilepton_unfolding/ZMassDilepton_ptVGen_absYVGen_noQCDscales/fitresults.hdf5"
        ),
        "higher_orders_input_dir": str(Path(my_out_dir) / "260304_ho"),
        "alternate_pdfs_input_dir": str(
            Path(my_out_dir) / "260302_histmaker_dilepton_pdfFromCorrBiasTest"
        ),
        "pdf_from_corrs_bias_input_dir": str(
            Path(my_out_dir) / "260302_histmaker_dilepton_pdfFromCorrBiasTest"
        ),
        "styles": str(Path(wrem_base) / "wremnants/utilities/styles/styles.py"),
        "output_root": output_root,
    }

    # Add output-directory paths in a second step because they are derived from
    # output_root above. Keeping them separate makes it easy to see what is
    # environment/input configuration versus what is computed output layout.
    paths.update(
        {
            "uncerts_out": str(Path(output_root) / "Figures/uncertainties"),
            "reco_results": str(Path(output_root) / "Figures/detector_extraction"),
            "z_reco_results": str(
                Path(output_root) / "Figures/detector_extraction/Z_fit"
            ),
            "wz_reco_results": str(
                Path(output_root) / "Figures/detector_extraction/WZ_fit"
            ),
            "wz_reco_comparison": str(
                Path(output_root) / "Figures/detector_extraction/comparison"
            ),
            "z_unfolding_xsecs": str(
                Path(output_root) / "Figures/unfolding/helicity_xsecs"
            ),
            "w_unfolding_xsecs": str(
                Path(output_root) / "Figures/unfolding/w_unfolded_xsecs"
            ),
            "gen_results": str(Path(output_root) / "Figures/gen_extraction"),
            "wz_gen_results": str(Path(output_root) / "Figures/gen_extraction/WZ_fit"),
            "z_gen_results": str(Path(output_root) / "Figures/gen_extraction/Z_fit"),
        }
    )

    return paths


def rabbit(paths: dict[str, str], script_name: str) -> str:
    return str(Path(paths["rabbit_base"]) / "bin" / script_name)


def py(script: str, *args: str) -> list[str]:
    return [sys.executable, script, *args]


def task(
    task_id: str, section: str, command: list[str], *, inputs: list[str] | None = None
) -> Task:
    return {
        "id": task_id,
        "section": section,
        "cmd": command,
        "inputs": inputs or [],
    }


def build_tasks(paths: dict[str, str]) -> list[Task]:
    t: list[Task] = []  # task train choo-choo

    # Section 4: uncertainties
    t.append(
        task(
            "sec4_alphas_smoothing_full_angular",
            "4",
            py(
                paths["plot_narf"],
                paths["z_input_h5"],
                "--filterProcs",
                "Zmumu_2016PostVFP",
                "--hists",
                "nominal",
                "nominal_scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO_pdfas_Corr",
                "nominal_scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO_pdfas_CorrByHelicity",
                "--selectByHist",
                "",
                "vars 1",
                "vars 1",
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
                "0.96",
                "1.01",
                "--noRatioErrorBars",
                "--postfix",
                "fullAngularDistribution",
                "--legLoc",
                "0.7",
                "0.3",
                "-o",
                paths["uncerts_out"],
            ),
        )
    )
    t.append(
        task(
            "sec4_alphas_smoothing_single_angular_bin",
            "4",
            py(
                paths["plot_narf"],
                paths["z_input_h5"],
                "--filterProcs",
                "Zmumu_2016PostVFP",
                "--hists",
                "nominal",
                "nominal_scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO_pdfas_Corr",
                "nominal_scetlib_dyturbo_LatticeNP_CT18Z_N3p0LL_N2LO_pdfas_CorrByHelicity",
                "--selectByHist",
                "",
                "vars 1",
                "vars 1",
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
                "0.96",
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
                paths["uncerts_out"],
            ),
        )
    )
    t.append(
        task(
            "sec4_pdf_smoothing_full_angular",
            "4",
            py(
                paths["plot_narf"],
                paths["z_input_h5"],
                "--filterProcs",
                "Zmumu_2016PostVFP",
                "--hists",
                "nominal",
                "nominal_pdfCT18Z",
                "nominal_pdfCT18ZByHelicity",
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
                "0.96",
                "1.01",
                "--noRatioErrorBars",
                "--postfix",
                "fullAngularDistribution",
                "--legLoc",
                "0.7",
                "0.3",
                "-o",
                paths["uncerts_out"],
            ),
            inputs=[paths["z_input_h5"]],
        )
    )
    t.append(
        task(
            "sec4_pdf_smoothing_single_angular_bin",
            "4",
            py(
                paths["plot_narf"],
                paths["z_input_h5"],
                "--filterProcs",
                "Zmumu_2016PostVFP",
                "--hists",
                "nominal",
                "nominal_pdfCT18Z",
                "nominal_pdfCT18ZByHelicity",
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
                "0.96",
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
                paths["uncerts_out"],
            ),
            inputs=[paths["z_input_h5"]],
        )
    )
    t.append(
        task(
            "sec4_pdf_bias_default",
            "4",
            py(
                str(
                    Path(paths["my_work_dir"])
                    / "studies/pdf_from_corrs_bias_test/plot_results_from_split_fits.py"
                ),
                "--input-dir",
                paths["pdf_from_corrs_bias_input_dir"],
                "--output-dir",
                paths["uncerts_out"],
            ),
        )
    )
    t.append(
        task(
            "sec4_pdf_bias_scale1p0",
            "4",
            py(
                str(
                    Path(paths["my_work_dir"])
                    / "studies/pdf_from_corrs_bias_test/plot_results_from_split_fits.py"
                ),
                "--input-dir",
                paths["pdf_from_corrs_bias_input_dir"],
                "--fit-postfix",
                "scalePdf1p0",
                "--output-dir",
                paths["uncerts_out"],
                "--postfix",
                "scale1p0",
            ),
        )
    )
    for obs in ["ptll", "yll", "cosThetaStarll_quantile", "phiStarll_quantile"]:
        t.append(
            task(
                f"sec4_rabbit_alphas_{obs}",
                "4",
                [
                    rabbit(paths, "rabbit_plot_hists.py"),
                    paths["z_reco_fit"],
                    "-m",
                    f"Project ch0 {obs}",
                    "--prefit",
                    "--config",
                    paths["styles"],
                    "--title",
                    "CMS",
                    "--titlePos",
                    "0",
                    "-o",
                    f"{paths['uncerts_out']}/",
                    "--processGrouping",
                    "z_dilepton",
                    "--rrange",
                    "0.88",
                    "1.12",
                    "--varName",
                    "pdfAlphaS",
                    "--varLabel",
                    r"$\alpha_\mathrm{S}{\pm}1\sigma$",
                    "--yscale",
                    "1.25",
                    "--noExtraText",
                    "--subtitle",
                    SUBTITLE,
                    "--lowerLegPos",
                    "upper right",
                    "--noData",
                    "--postfix",
                    "alphas",
                ],
            )
        )
    t.append(
        task(
            "sec4_rabbit_pdfs_ptll",
            "4",
            [
                rabbit(paths, "rabbit_plot_hists.py"),
                paths["z_reco_fit"],
                "-m",
                "Project ch0 ptll",
                "--prefit",
                "--config",
                paths["styles"],
                "--title",
                "CMS",
                "--titlePos",
                "0",
                "-o",
                f"{paths['uncerts_out']}/",
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
                SUBTITLE,
                "--lowerLegPos",
                "upper right",
                "--noData",
                "--postfix",
                "pdfs",
                "--showVariations",
                "both",
            ],
        )
    )
    t.append(
        task(
            "sec4_bquark_mass_pt",
            "4",
            py(
                "scripts/plot_corr_hists.py",
                str(
                    Path(paths["wrem_base"])
                    / "wremnants-data/data/TheoryCorrections/MiNNLO_Zbb_CorrZ.pkl.lz4"
                ),
                "--corr",
                "Z",
                "--corrName",
                "MiNNLO_Zbb",
                "--axis",
                "ptVgen",
                "--varAxis",
                "vars",
                "--vars",
                "mb_up",
                "--xlim",
                "0",
                "200",
                "--binwnorm",
                "1",
                "-o",
                f"{paths['uncerts_out']}/",
            ),
        )
    )
    t.append(
        task(
            "sec4_bquark_mass_absy",
            "4",
            py(
                "scripts/plot_corr_hists.py",
                str(
                    Path(paths["wrem_base"])
                    / "wremnants-data/data/TheoryCorrections/MiNNLO_Zbb_CorrZ.pkl.lz4"
                ),
                "--corr",
                "Z",
                "--corrName",
                "MiNNLO_Zbb",
                "--axis",
                "absYVgen",
                "--varAxis",
                "vars",
                "--vars",
                "mb_up",
                "--binwnorm",
                "1",
                "-o",
                f"{paths['uncerts_out']}/",
            ),
        )
    )

    # Section 5: detector-level extraction
    t.append(
        task(
            "sec5_input_z_ptll_yll",
            "5",
            [
                rabbit(paths, "rabbit_plot_inputdata.py"),
                paths["z_reco_carrot"],
                "--hists",
                "ptll-yll",
                "--config",
                paths["styles"],
                "--title",
                "CMS",
                "--titlePos",
                "0",
                "-o",
                f"{paths['reco_results']}/",
                "--processGrouping",
                "z_dilepton",
                "--noData",
            ],
        )
    )
    for h in ["phiStarll_quantile", "cosThetaStarll_quantile"]:
        t.append(
            task(
                f"sec5_input_z_{h}",
                "5",
                [
                    rabbit(paths, "rabbit_plot_inputdata.py"),
                    paths["z_reco_carrot"],
                    "-o",
                    f"{paths['reco_results']}/",
                    "--hists",
                    h,
                    "--config",
                    paths["styles"],
                    "--title",
                    "CMS",
                    "--titlePos",
                    "0",
                    "--ylim",
                    "0",
                    "1300000",
                    "--processGrouping",
                    "z_dilepton",
                    "--noData",
                ],
            )
        )
    t.append(
        task(
            "sec5_input_w_pt_eta",
            "5",
            [
                rabbit(paths, "rabbit_plot_inputdata.py"),
                paths["w_reco_carrot"],
                "--hists",
                "pt-eta",
                "--channels",
                "ch1",
                "--config",
                paths["styles"],
                "--title",
                "CMS",
                "--titlePos",
                "0",
                "-o",
                f"{paths['reco_results']}/",
                "--processGrouping",
                "w_mass",
                "--selectionAxes",
                "charge",
                "--postfix",
                "single_muon",
                "--noData",
                "--invertAxes",
            ],
        )
    )
    t.append(
        task(
            "sec5_z_impacts",
            "5",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["z_reco_fit"],
                "--poi",
                "pdfAlphaS",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "2.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "-o",
                paths["z_reco_results"],
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
                SUBTITLE,
            ],
        )
    )
    t.append(
        task(
            "sec5_z_impacts_global",
            "5",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["z_reco_fit"],
                "--poi",
                "pdfAlphaS",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "2.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "-o",
                paths["z_reco_results"],
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
                SUBTITLE,
                "--globalImpacts",
            ],
        )
    )
    t.append(
        task(
            "sec5_higher_orders",
            "5",
            py(
                "studies/higher_orders/plot_results.py",
                "--input-dir",
                paths["higher_orders_input_dir"],
                "--output-dir",
                paths["z_reco_results"],
            ),
        )
    )
    t.append(
        task(
            "sec5_alternate_pdfs",
            "5",
            py(
                "studies/alternate_pdfs/plot_results.py",
                "--input-dir",
                paths["alternate_pdfs_input_dir"],
                "--fit-postfix",
                "pdfBiasTest_Zmumu",
                "--output-dir",
                paths["z_reco_results"],
            ),
        )
    )
    t.append(
        task(
            "sec5_alternate_pdfs_scale1p0",
            "5",
            py(
                "studies/alternate_pdfs/plot_results.py",
                "--input-dir",
                paths["alternate_pdfs_input_dir"],
                "--fit-postfix",
                "pdfBiasTest_Zmumu_scalePdf1p0",
                "--postfix",
                "scale1p0",
                "--output-dir",
                paths["z_reco_results"],
            ),
        )
    )
    t.append(
        task(
            "sec5_wz_impacts_alphas",
            "5",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["wz_reco_fit"],
                "--poi",
                "pdfAlphaS",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "2.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>α</i><sub>S</sub> in 10<sup>-3</sup>",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["wz_reco_results"],
            ],
        )
    )
    t.append(
        task(
            "sec5_wz_impacts_mw",
            "5",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["wz_reco_fit"],
                "--poi",
                "massShiftW100MeV",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "100.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>m</i><sub>W</sub> in MeV",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["wz_reco_results"],
            ],
        )
    )
    t.append(
        task(
            "sec5_wz_impacts_alphas_global",
            "5",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["wz_reco_fit"],
                "--poi",
                "pdfAlphaS",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "2.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>α</i><sub>S</sub> in 10<sup>-3</sup>",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["wz_reco_results"],
                "--globalImpacts",
            ],
        )
    )
    t.append(
        task(
            "sec5_wz_impacts_mw_global",
            "5",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["wz_reco_fit"],
                "--poi",
                "massShiftW100MeV",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "100.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>m</i><sub>W</sub> in MeV",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["wz_reco_results"],
                "--globalImpacts",
            ],
        )
    )
    t.append(
        task(
            "sec5_compare_z_vs_wz_global",
            "5",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["z_reco_fit"],
                "--poi",
                "pdfAlphaS",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "2.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>α</i><sub>S</sub> in 10<sup>-3</sup>",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["wz_reco_comparison"],
                "-r",
                paths["wz_reco_fit"],
                "--refName",
                "W+Z",
                "--name",
                "Z only",
                "--globalImpacts",
            ],
        )
    )
    t.append(
        task(
            "sec5_compare_z_vs_wz",
            "5",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["z_reco_fit"],
                "--poi",
                "pdfAlphaS",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "2.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>α</i><sub>S</sub> in 10<sup>-3</sup>",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["wz_reco_comparison"],
                "-r",
                paths["wz_reco_fit"],
                "--refName",
                "W+Z",
                "--name",
                "Z only",
            ],
        )
    )

    # Section 6: unfolding
    t.append(
        task(
            "sec6_z_xsec_project",
            "6",
            [
                rabbit(paths, "rabbit_plot_hists.py"),
                paths["wz_unfolding_fit_mappings"],
                "-o",
                paths["z_unfolding_xsecs"],
                "-m",
                "Project",
                "--selectionAxes",
                "helicitySig",
                "--channels",
                "ch0_masked",
                "--unfoldedXsec",
                "--extraTextLoc",
                "0.35",
                "0.9",
                "--legCols",
                "1",
                "--yscale",
                "1.2",
                "--title",
                "CMS",
                "--titlePos",
                "0",
                "--subtitle",
                SUBTITLE,
                "--rrange",
                "0.8",
                "1.2",
                "--config",
                paths["styles"],
            ],
        )
    )
    t.append(
        task(
            "sec6_z_xsec_uncertainties",
            "6",
            [
                rabbit(paths, "rabbit_plot_hists_uncertainties.py"),
                paths["wz_unfolding_fit_mappings"],
                "-o",
                paths["z_unfolding_xsecs"],
                "-m",
                "Project",
                "--selectionAxes",
                "helicitySig",
                "--channels",
                "ch0_masked",
                "--absolute",
                "--extraTextLoc",
                "0.05",
                "0.95",
                "--legCols",
                "2",
                "--yscale",
                "1.5",
                "--title",
                "CMS",
                "--titlePos",
                "0",
                "--subtitle",
                SUBTITLE,
                "--grouping",
                "unfolding",
                "--config",
                paths["styles"],
            ],
        )
    )
    t.append(
        task(
            "sec6_z_xsec_cov",
            "6",
            [
                rabbit(paths, "rabbit_plot_hists_cov.py"),
                paths["wz_unfolding_fit_mappings"],
                "-o",
                paths["z_unfolding_xsecs"],
                "-m",
                "Project",
                "--selectionAxes",
                "helicitySig",
                "--correlation",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "--titlePos",
                "0",
                "--config",
                paths["styles"],
            ],
        )
    )
    t.append(
        task(
            "sec6_w_xsec_select",
            "6",
            [
                rabbit(paths, "rabbit_plot_hists.py"),
                paths["wz_unfolding_fit_mappings"],
                "-o",
                paths["w_unfolding_xsecs"],
                "-m",
                "Select",
                "--selectionAxes",
                "qGen",
                "--channels",
                "ch1_masked",
                "--unfoldedXsec",
                "--extraTextLoc",
                "0.35",
                "0.9",
                "--legCols",
                "1",
                "--yscale",
                "1.2",
                "--title",
                "CMS",
                "--titlePos",
                "0",
                "--subtitle",
                SUBTITLE,
                "--rrange",
                "0.8",
                "1.2",
                "--invertAxes",
                "--customFigureWidth",
                "2.5",
                "--config",
                paths["styles"],
                "-p combined",
            ],
        )
    )
    t.append(
        task(
            "sec6_w_xsec_select_uncertainties",
            "6",
            [
                rabbit(paths, "rabbit_plot_hists_uncertainties.py"),
                paths["wz_unfolding_fit_mappings"],
                "-o",
                paths["w_unfolding_xsecs"],
                "-m",
                "Select",
                "--selectionAxes",
                "qGen",
                "--channels",
                "ch1_masked",
                "--extraTextLoc",
                "0.05",
                "0.95",
                "--legCols",
                "2",
                "--yscale",
                "1.5",
                "--title",
                "CMS",
                "--titlePos",
                "0",
                "--subtitle",
                SUBTITLE,
                "--grouping",
                "unfolding",
                "--invertAxes",
                "--customFigureWidth",
                "2.5",
                "--config",
                paths["styles"],
            ],
        )
    )
    t.append(
        task(
            "sec6_w_xsec_project",
            "6",
            [
                rabbit(paths, "rabbit_plot_hists.py"),
                paths["wz_unfolding_fit_mappings"],
                "-o",
                paths["w_unfolding_xsecs"],
                "-m",
                "Project",
                "--selectionAxes",
                "qGen",
                "--channels",
                "ch1_masked",
                "--unfoldedXsec",
                "--extraTextLoc",
                "0.35",
                "0.9",
                "--legCols",
                "1",
                "--yscale",
                "1.2",
                "--title",
                "CMS",
                "--titlePos",
                "0",
                "--subtitle",
                SUBTITLE,
                "--rrange",
                "0.8",
                "1.2",
                "--invertAxes",
                "--config",
                paths["styles"],
            ],
        )
    )
    t.append(
        task(
            "sec6_w_xsec_project_uncertainties",
            "6",
            [
                rabbit(paths, "rabbit_plot_hists_uncertainties.py"),
                paths["wz_unfolding_fit_mappings"],
                "-o",
                paths["w_unfolding_xsecs"],
                "-m",
                "Project",
                "--selectionAxes",
                "qGen",
                "--channels",
                "ch1_masked",
                "--extraTextLoc",
                "0.05",
                "0.95",
                "--legCols",
                "2",
                "--yscale",
                "1.5",
                "--title",
                "CMS",
                "--titlePos",
                "0",
                "--subtitle",
                SUBTITLE,
                "--grouping",
                "unfolding",
                "--invertAxes",
                "--config",
                paths["styles"],
            ],
        )
    )
    t.append(
        task(
            "sec6_w_xsec_cov",
            "6",
            [
                rabbit(paths, "rabbit_plot_hists_cov.py"),
                paths["wz_unfolding_fit_mappings"],
                "-o",
                paths["w_unfolding_xsecs"],
                "-m",
                "Project",
                "--selectionAxes",
                "qGen",
                "--correlation",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "--titlePos",
                "0",
                "--config",
                paths["styles"],
            ],
        )
    )

    # Section 7: gen-level extraction
    t.append(
        task(
            "sec7_wz_setup_mw",
            "7",
            [
                rabbit(paths, "rabbit_plot_hists.py"),
                paths["wz_gen_fit"],
                "-o",
                paths["wz_gen_results"],
                "--prefit",
                "--channels",
                "ch0",
                "--selectionAxes",
                "qGen",
                "--invertAxes",
                "-m",
                "BaseMapping",
                "--varName",
                "massShiftW100MeV",
                "--varLabel",
                r"$\Delta m_{W}{\pm}100\mathrm{MeV}$",
                "--extraTextLoc",
                "0.04",
                "0.9",
                "--legCols",
                "1",
                "--yscale",
                "1.2",
                "--title",
                "CMS",
                "--titlePos",
                "0",
                "--chisq",
                "none",
                "--subtitle",
                SUBTITLE,
                "--rrange",
                "0.95",
                "1.05",
                "--config",
                paths["styles"],
                "--customFigureWidth",
                "2.5",
                "--subplotSizes",
                "1",
                "1",
                "--lowerLegPos",
                "upper right",
            ],
        )
    )
    t.append(
        task(
            "sec7_wz_setup_alphas",
            "7",
            [
                rabbit(paths, "rabbit_plot_hists.py"),
                paths["wz_gen_fit"],
                "-o",
                paths["wz_gen_results"],
                "--prefit",
                "--channels",
                "ch1",
                "-m",
                "BaseMapping",
                "--varName",
                "pdfAlphaS",
                "--varLabel",
                r"$\alpha_\mathrm{S}{\pm}1\sigma$",
                "--extraTextLoc",
                "0.04",
                "0.9",
                "--legCols",
                "1",
                "--yscale",
                "1.2",
                "--title",
                "CMS",
                "--titlePos",
                "0",
                "--chisq",
                "none",
                "--subtitle",
                SUBTITLE,
                "--rrange",
                "0.85",
                "1.15",
                "--config",
                paths["styles"],
                "--customFigureWidth",
                "2.5",
                "--subplotSizes",
                "1",
                "1",
                "--lowerLegPos",
                "upper right",
            ],
        )
    )
    t.append(
        task(
            "sec7_z_impacts",
            "7",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["z_gen_fit"],
                "--poi",
                "pdfAlphaS",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "2.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>α</i><sub>S</sub> in 10<sup>-3</sup>",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["z_gen_results"],
            ],
        )
    )
    t.append(
        task(
            "sec7_z_impacts_global",
            "7",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["z_gen_fit"],
                "--poi",
                "pdfAlphaS",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "2.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>α</i><sub>S</sub> in 10<sup>-3</sup>",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["z_gen_results"],
                "--globalImpacts",
            ],
        )
    )
    t.append(
        task(
            "sec7_wz_impacts_alphas",
            "7",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["wz_gen_fit"],
                "--poi",
                "pdfAlphaS",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "2.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>α</i><sub>S</sub> in 10<sup>-3</sup>",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["wz_gen_results"],
            ],
        )
    )
    t.append(
        task(
            "sec7_wz_impacts_mw",
            "7",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["wz_gen_fit"],
                "--poi",
                "massShiftW100MeV",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "100.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>m</i><sub>W</sub> in MeV",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["wz_gen_results"],
            ],
        )
    )
    t.append(
        task(
            "sec7_wz_impacts_alphas_global",
            "7",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["wz_gen_fit"],
                "--poi",
                "pdfAlphaS",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "2.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>α</i><sub>S</sub> in 10<sup>-3</sup>",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["wz_gen_results"],
                "--globalImpacts",
            ],
        )
    )
    t.append(
        task(
            "sec7_wz_impacts_mw_global",
            "7",
            [
                rabbit(paths, "rabbit_plot_pulls_and_impacts.py"),
                paths["wz_gen_fit"],
                "--poi",
                "massShiftW100MeV",
                "--config",
                paths["styles"],
                "--scaleImpacts",
                "100.0",
                "--showNumbers",
                "--oneSidedImpacts",
                "--grouping",
                "min",
                "--otherExtensions",
                "pdf",
                "png",
                "-n",
                "50",
                "--impactTitle",
                "<i>m</i><sub>W</sub> in MeV",
                "--title",
                "CMS",
                "--subtitle",
                SUBTITLE,
                "-o",
                paths["wz_gen_results"],
                "--globalImpacts",
            ],
        )
    )

    return t


def ensure_output_dirs(paths: dict[str, str]) -> None:
    for key in [
        "uncerts_out",
        "reco_results",
        "z_reco_results",
        "wz_reco_results",
        "wz_reco_comparison",
        "z_unfolding_xsecs",
        "w_unfolding_xsecs",
        "gen_results",
        "wz_gen_results",
        "z_gen_results",
    ]:
        Path(paths[key]).mkdir(parents=True, exist_ok=True)


def missing_inputs(task_def: Task) -> list[str]:
    missing: list[str] = []
    for candidate in task_def.get("inputs", []):
        if not Path(candidate).exists():
            missing.append(candidate)
    return missing


def list_tasks(tasks: list[Task]) -> None:
    for x in tasks:
        print(f"[{x['section']}] {x['id']}")


def select_tasks(
    tasks: list[Task], *, run_all: bool, sections: set[str], only: set[str]
) -> list[Task]:
    if run_all:
        return tasks

    selected: list[Task] = []
    for x in tasks:
        if x["section"] in sections or x["id"] in only:
            selected.append(x)
    return selected


def run_task(task_def: Task, *, dry_run: bool, skip_missing: bool) -> bool:
    missing = missing_inputs(task_def)
    if missing:
        print(f"[skip] {task_def['id']} missing inputs: {', '.join(missing)}")
        return skip_missing

    cmd = task_def["cmd"]
    print(f"[run ] {task_def['id']}")
    print("       " + shlex.join(cmd))
    if dry_run:
        return True

    subprocess.run(cmd, check=True)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate AN note figures with explicit task selection."
    )
    parser.add_argument("--output", choices=["an", "www"], default="an")
    parser.add_argument(
        "--sections",
        nargs="+",
        choices=sorted(VALID_SECTIONS),
        default=[],
        help=SECTIONS_HELP,
    )
    parser.add_argument(
        "--only", nargs="+", help="Run only the specified tasks", default=[]
    )
    parser.add_argument("--all", action="store_true", help="Run all tasks")
    parser.add_argument(
        "--list", action="store_true", help="List selected tasks and exit"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print commands without executing"
    )
    parser.add_argument(
        "--skip-missing-inputs",
        action="store_true",
        help="Skip tasks with missing declared input files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.all and not args.sections and not args.only:
        print("Nothing selected. Use --all, --sections, or --only.", file=sys.stderr)
        return 2

    paths = resolve_paths(args.output)
    ensure_output_dirs(paths)
    tasks = build_tasks(paths)

    only_unknown = sorted(set(args.only) - {x["id"] for x in tasks})
    if only_unknown:
        print(f"Unknown task id(s): {', '.join(only_unknown)}", file=sys.stderr)
        return 2

    selected = select_tasks(
        tasks,
        run_all=args.all,
        sections=set(args.sections),
        only=set(args.only),
    )

    if not selected:
        print("No tasks matched selection.", file=sys.stderr)
        return 2

    print(f"Output root directory: {paths['output_root']}")
    print(f"Selected tasks: {len(selected)}")

    if args.list:
        list_tasks(selected)
        return 0

    failures = 0
    for x in selected:
        try:
            ok = run_task(
                x,
                dry_run=args.dry_run,
                skip_missing=args.skip_missing_inputs,
            )
            if not ok:
                failures += 1
        except subprocess.CalledProcessError as err:
            failures += 1
            print(
                f"[fail] {x['id']} exited with code {err.returncode}", file=sys.stderr
            )
            break

    if failures:
        return 1

    print("All selected tasks completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
