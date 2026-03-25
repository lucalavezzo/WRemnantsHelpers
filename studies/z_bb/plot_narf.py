import argparse
import os
from datetime import datetime
import matplotlib.pyplot as plt
import mplhep as hep
import numpy as np

from wums import boostHistHelpers as hh
from wremnants.utilities.io_tools import input_tools
from wums import logging, output_tools, plot_tools  # isort: skip


def parse_args():
    parser = argparse.ArgumentParser(description="Plot z_bb comparison histograms.")
    parser.add_argument(
        "--massive-file",
        required=True,
        help="HDF5 file for massive-b sample (Zbb_MiNNLO).",
    )
    parser.add_argument(
        "--massless-file",
        required=True,
        help="HDF5 file for massless sample (Zmumu_13TeVGen).",
    )
    parser.add_argument(
        "--outdir",
        default=None,
        help="Output directory. Default: $MY_PLOT_DIR/<date>_z_bb/hadrons/<tag>",
    )
    parser.add_argument(
        "--tag",
        default=datetime.now().strftime("%H%M%S"),
        help="Tag to append in default output path.",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize swapped massive component to nominal bottom component.",
    )
    parser.add_argument(
        "--massive-scale",
        type=float,
        default=1.0,
        help="Additional multiplicative scale factor applied to swapped massive component.",
    )
    parser.add_argument(
        "--norm-mode",
        choices=["default", "sigma-difference"],
        default="default",
        help=(
            "Normalization mode for the inclusive correction. "
            "'default': use raw split yields (optionally --normalize selected component). "
            "'sigma-difference': enforce sigma(5FS_bveto)=sigma(5FS_total)-sigma(4FS_total) "
            "and sigma(4FS_addback)=sigma(4FS_total) using template shapes."
        ),
    )
    return parser.parse_args()


args = parse_args()
f_mass = args.massive_file
f_massless = args.massless_file
normalize = args.normalize
massive_scale = args.massive_scale
norm_mode = args.norm_mode

if norm_mode == "sigma-difference" and normalize:
    raise ValueError("--norm-mode sigma-difference is incompatible with --normalize")
if norm_mode == "sigma-difference" and massive_scale != 1.0:
    raise ValueError(
        "--norm-mode sigma-difference is incompatible with --massive-scale != 1"
    )

res_massive, meta, _ = input_tools.read_infile(f_mass)
res_massless, meta, _ = input_tools.read_infile(f_massless)

outdir = args.outdir or os.path.join(
    os.environ["MY_PLOT_DIR"], datetime.now().strftime("%y%m%d_z_bb/hadrons/"), args.tag
)
if not os.path.exists(outdir):
    os.makedirs(outdir)
    print(f"Output directory '{outdir}' created.")


def read_h(res, proc, h):
    # Dataset cross sections are stored in pb.
    h = hh.scaleHist(
        h, res[proc]["dataset"]["xsec"] / res[proc]["weight_sum"], createNew=True
    )
    return h


def resolve_hist_key(output_dict, var):
    if var in output_dict:
        return var
    alias_map = {
        "lhe_init_flavor": "presel_lhe_init_flavor",
        "z_mother_flavor": "presel_z_mother_flavor",
        "n_lhe_fin_bbbar": "postsel_n_lhe_fin_bbbar",
        "n_lhe_bbbar": "postsel_n_lhe_bbbar",
        "lhe_bbbar_fin_min_pt": "postsel_lhe_bbbar_fin_min_pt",
        "lhe_bbbar_fin_max_pt": "postsel_lhe_bbbar_fin_max_pt",
        "m_bb_lhe": "postsel_m_bb",
        "dR_bb_lhe": "postsel_dR_bb",
    }
    alias = alias_map.get(var)
    if alias and alias in output_dict:
        return alias
    return None


def maybe_select_bottom_bin(h, bottom_sel_bin=None):
    if bottom_sel_bin is None:
        return h, ""
    axis_names = [ax.name for ax in h.axes]
    if "bottom_sel" not in axis_names:
        return h, ""
    out = h[{"bottom_sel": bottom_sel_bin}]
    keep_axes = [ax.name for ax in out.axes if ax.name != "bottom_sel"]
    if keep_axes:
        out = out.project(*keep_axes)
    return out, f"_b{bottom_sel_bin}"


def project_to_axis(h, axis_name):
    axis_names = [ax.name for ax in h.axes]
    if axis_name not in axis_names:
        return h
    if h.ndim == 1 and axis_names[0] == axis_name:
        return h
    return h.project(axis_name)


def print_nB_table(h, label):
    centers = h.axes[0].centers
    vals = h.values()
    total = np.sum(vals)
    print(f"\n{label}: nBhad_pt5 weighted bin contents")
    for c, v in zip(centers, vals):
        frac = (v / total) if total != 0 else np.nan
        print(f"  nB={int(round(c))}: yield={v:.6e}, frac={frac:.6f}")


def print_lhe_init_flavor_table(h, label):
    vals = h.values()
    centers = h.axes[0].centers
    total = np.sum(vals)
    name_map = {
        0: "other/mixed",
        1: "ddbar",
        2: "uubar",
        3: "ssbar",
        4: "ccbar",
        5: "bbbar",
    }
    print(f"\n{label}: initial-state flavor fractions (LHE, preselection)")
    for code in range(0, 6):
        mask = np.isclose(np.round(centers).astype(int), code)
        y = float(np.sum(vals[mask])) if np.any(mask) else 0.0
        frac = (y / total) if total > 0 else np.nan
        print(f"  {name_map[code]}: yield={y:.6e}, frac={frac:.6f}")


def print_z_mother_flavor_table(h, label):
    vals = h.values()
    centers = h.axes[0].centers
    total = np.sum(vals)
    name_map = {
        0: "other/mixed/unclassified",
        1: "ddbar",
        2: "uubar",
        3: "ssbar",
        4: "ccbar",
        5: "bbbar",
    }
    print(
        f"\n{label}: Z/gamma*-ancestor quark flavor fractions (GenPart, preselection)"
    )
    for code in range(0, 6):
        mask = np.isclose(np.round(centers).astype(int), code)
        y = float(np.sum(vals[mask])) if np.any(mask) else 0.0
        frac = (y / total) if total > 0 else np.nan
        print(f"  {name_map[code]}: yield={y:.6e}, frac={frac:.6f}")


def plot_tagging_matrix(h_nominal, sample_label, rel_name_prefix):
    axis_names = [ax.name for ax in h_nominal.axes]
    if "bottom_sel" not in axis_names or "bottom_sel_pdt" not in axis_names:
        print(
            f"Skipping tagging-matrix for {sample_label}: missing 'bottom_sel' or 'bottom_sel_pdt' axis"
        )
        return

    h2 = h_nominal.project("bottom_sel", "bottom_sel_pdt")
    mat = h2.values()
    if mat.shape != (2, 2):
        print(
            f"Skipping tagging-matrix for {sample_label}: unexpected matrix shape {mat.shape}"
        )
        return

    total = float(np.sum(mat))
    frac = mat / total if total > 0 else np.full_like(mat, np.nan, dtype=float)

    agree = float(mat[0, 0] + mat[1, 1])
    disagree = float(mat[0, 1] + mat[1, 0])
    print(
        f"{sample_label}: tag agreement={agree:.6e}, disagreement={disagree:.6e}, "
        f"disagreement_frac={(disagree/total if total > 0 else np.nan):.6f}"
    )

    def _save(fig, rel_oname):
        oname = os.path.join(outdir, rel_oname)
        fig.savefig(oname + ".pdf", bbox_inches="tight")
        fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
        plt.close(fig)
        output_tools.write_index_and_log(outdir, rel_oname)

    fig, ax = plt.subplots(figsize=(6.0, 5.2))
    im = ax.imshow(mat, origin="lower", cmap="Blues")
    ax.set_xticks([0, 1], labels=["PDT=0", "PDT=1"])
    ax.set_yticks([0, 1], labels=["base=0", "base=1"])
    ax.set_xlabel("PDT-based tag (bottom_sel_pdt)")
    ax.set_ylabel("Analysis tag (bottom_sel)")
    ax.set_title(f"{sample_label}: event-yield matrix")
    plt.colorbar(im, ax=ax, label="Weighted yield [pb]")
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{mat[i, j]:.3e}\n({frac[i, j]:.2%})",
                ha="center",
                va="center",
                color="black",
                fontsize=10,
            )
    _save(fig, f"{rel_name_prefix}_event_yield_matrix")

    fig, ax = plt.subplots(figsize=(6.0, 5.2))
    im = ax.imshow(frac, origin="lower", cmap="viridis", vmin=0.0, vmax=1.0)
    ax.set_xticks([0, 1], labels=["PDT=0", "PDT=1"])
    ax.set_yticks([0, 1], labels=["base=0", "base=1"])
    ax.set_xlabel("PDT-based tag (bottom_sel_pdt)")
    ax.set_ylabel("Analysis tag (bottom_sel)")
    ax.set_title(f"{sample_label}: event-fraction matrix")
    plt.colorbar(im, ax=ax, label="Fraction of total")
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{frac[i, j]:.2%}",
                ha="center",
                va="center",
                color="white" if frac[i, j] > 0.5 else "black",
                fontsize=11,
            )
    _save(fig, f"{rel_name_prefix}_event_fraction_matrix")


def auto_rrange_from_ratio(
    ref_hist, var_hist, qlow=0.02, qhigh=0.98, x_range=None, min_ref_rel=1e-4
):
    ref = ref_hist.values()
    var = var_hist.values()
    mask = np.isfinite(ref) & np.isfinite(var) & (ref > 0)

    if x_range is not None and ref_hist.ndim == 1:
        x_lo, x_hi = x_range
        x_centers = ref_hist.axes[0].centers
        mask = mask & (x_centers >= x_lo) & (x_centers <= x_hi)

    # Suppress bins with tiny reference content that can blow up ratios.
    ref_max = float(np.max(ref[mask])) if np.any(mask) else 0.0
    if ref_max > 0:
        mask = mask & (ref >= min_ref_rel * ref_max)

    if not np.any(mask):
        return [[0.5, 1.5]]

    ratio = var[mask] / ref[mask]
    ratio = ratio[np.isfinite(ratio)]
    if ratio.size == 0:
        return [[0.5, 1.5]]

    lo = float(np.quantile(ratio, qlow))
    hi = float(np.quantile(ratio, qhigh))

    if not np.isfinite(lo) or not np.isfinite(hi):
        return [[0.5, 1.5]]

    if hi <= lo:
        lo = min(lo, 1.0) - 0.1
        hi = max(hi, 1.0) + 0.1
    else:
        pad = 0.2 * (hi - lo)
        lo -= pad
        hi += pad

    lo = min(lo, 1.0)
    hi = max(hi, 1.0)
    lo = max(0.0, lo)

    if hi - lo < 0.1:
        mid = 0.5 * (hi + lo)
        lo = max(0.0, mid - 0.1)
        hi = mid + 0.1

    return [[lo, hi]]


def scaled_to_integral(h, target, label):
    current = h.sum().value
    if current <= 0:
        raise ValueError(
            f"Cannot scale '{label}' to target integral: current integral is <= 0"
        )
    return hh.scaleHist(h, target / current, createNew=True)


h_massive_nominal = read_h(
    res_massive,
    "Zbb_MiNNLO",
    res_massive["Zbb_MiNNLO"]["output"]["nominal_gen"].get(),
)
h_massless_nominal = read_h(
    res_massless,
    "Zmumu_13TeVGen",
    res_massless["Zmumu_13TeVGen"]["output"]["nominal_gen"].get(),
)
sigma4_total = h_massive_nominal.project("ptVgen").sum().value
sigma5_total = h_massless_nominal.project("ptVgen").sum().value
sigma5_bveto_target = sigma5_total - sigma4_total
if norm_mode == "sigma-difference" and sigma5_bveto_target < 0:
    raise ValueError(
        f"sigma-difference target for 5FS_bveto is negative ({sigma5_bveto_target})"
    )


# 2d
# for var in [
#     "n_lhe_init_bbbar_vs_n_lhe_fin_bbbar"
# ]:
#     h_massless = read_h(
#         res_massless,
#         f"Zmumu_13TeVGen",
#         res_massless[f"Zmumu_13TeVGen"]["output"][f"{var}"].get(),
#     )
#     fig = plt.figure()
#     ax = fig.add_subplot()
#     for bin in range(len(h_massless.axes[0].centers)):
#         hep.histplot(
#             h_massless[bin, :],
#             label=f"n_lhe_init_bbbar = {bin}",
#             ax=ax
#         )
#     ax.set_yscale("log")
#     ax.legend()
#     rel_oname = f"samples_comparison_{var}"
#     oname = os.path.join(outdir, rel_oname)
#     if not os.path.exists(outdir):
#         os.makedirs(outdir)
#         print(f"Output directory '{outdir}' created.")
#     fig.savefig(oname + ".pdf", bbox_inches="tight")
#     fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
#     plt.close(fig)
#     output_tools.write_index_and_log(outdir, rel_oname)

# massless only
# for var, xlabel in zip(
#     [
#         "lhe_fin_bbbar_pt",
#         "lhe_fin_bbbar_abseta",
#     ],
#     [
#         "Final b/bbar pt",
#         "Final b/bbar abseta"
#     ],
# ):
#     print("Plotting", var)

#     h_massless = read_h(
#         res_massless,
#         f"Zmumu_13TeVGen",
#         res_massless[f"Zmumu_13TeVGen"]["output"][f"{var}"].get(),
#     )

#     fig = plot_tools.makePlotWithRatioToRef(
#         [h_massless],
#         labels=["Nominal MiNNLO",],
#         ratio_legend=False,
#         nlegcols=1,
#         legtext_size=16,
#         binwnorm=1,
#         rrange=[[0.2, 1.5]],
#         xlabel=xlabel,
#     )
#     rel_oname = f"samples_comparison_{var}"
#     oname = os.path.join(outdir, rel_oname)
#     if not os.path.exists(outdir):
#         os.makedirs(outdir)
#         print(f"Output directory '{outdir}' created.")
#     fig.savefig(oname + ".pdf", bbox_inches="tight")
#     fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
#     plt.close(fig)
#     output_tools.write_index_and_log(outdir, rel_oname)


"""
plot_specs = [
    ("unknown_weight0", "Applied extra weight factor UnknownWeightAltSet1[0]", True, None),
    ("nBhad", "Number of B hadrons", True, None),
    ("nBhad_unity", "Number of B hadrons (unity weight)", True, None),
    ("nBhad_weight", "Number of B hadrons (base event weight)", True, None),
    ("nBhad_legacy", "Number of B hadrons (legacy ID)", True, None),
    ("nBhad_pt5", "Number of B hadrons", True, None),
    ("leadB_pt", "Leading B-hadron $p_T$ [GeV]", True, None),
    ("leadB_pt_legacy", "Leading B-hadron $p_T$ [GeV] (legacy ID)", True, None),
    ("subB_pt", "Subleading B-hadron $p_T$ [GeV]", True, None),
    ("subB_aeta", "Subleading B-hadron $|\\eta|$ (no $p_T$ cut)", False, None),
    ("leadB_pt5", "Leading B-hadron $p_T$ [GeV]", True, None),
    ("subB_pt5", "Subleading B-hadron $p_T$ [GeV]", True, None),
    ("softB_pt5", "Softest B-hadron $p_T$ [GeV]", True, None),
    ("leadB_pt5_b2", "Leading B-hadron $p_T$ [GeV]", True, None),
    ("subB_pt5_b2", "Subleading B-hadron $p_T$ [GeV]", True, None),
    ("m_bb_had", "$m_{bb}$ from B hadrons [GeV]", True, None),
    ("dR_bb_had", "$\\Delta R_{bb}$ from B hadrons", True, None),
    ("n_bjets", "Number of gen b-jets", True, None),
    ("n_bjets_recl", "Number of reclustered gen b-jets (GenPart+ghost-b)", True, None),
    ("lead_bjet_pt", "Leading gen b-jet pT", True, None),
    ("lead_bjet_pt_recl", "Leading reclustered gen b-jet pT", True, None),
    ("sublead_bjet_pt", "Subleading gen b-jet pT", True, None),
    ("sublead_bjet_pt_recl", "Subleading reclustered gen b-jet pT", True, None),
    ("lead_bjet_eta", "Leading gen b-jet eta", False, None),
    ("lead_bjet_eta_recl", "Leading reclustered gen b-jet eta", False, None),
    ("sublead_bjet_eta", "Subleading gen b-jet eta", False, None),
    ("sublead_bjet_eta_recl", "Subleading reclustered gen b-jet eta", False, None),
    ("m_bb_jet", "m_bb from gen b-jets", True, None),
    ("m_bb_jet_recl", "m_bb from reclustered gen b-jets", True, None),
    ("dR_bb_jet", "DeltaR_bb from gen b-jets", True, None),
    ("dR_bb_jet_recl", "DeltaR_bb from reclustered gen b-jets", True, None),
    ("n_bjets_parton", "Number of gen b-jets (parton flavour)", True, None),
    ("lead_bjet_pt_parton", "Leading gen b-jet $p_T$ [GeV] (parton flavour)", True, None),
    (
        "sublead_bjet_pt_parton",
        "Subleading gen b-jet $p_T$ [GeV] (parton flavour)",
        True,
        None,
    ),
    ("lead_bjet_eta_parton", "Leading gen b-jet $\\eta$ (parton flavour)", False, None),
    ("sublead_bjet_eta_parton", "Subleading gen b-jet $\\eta$ (parton flavour)", False, None),
    ("m_bb_jet_parton", "$m_{bb}$ from gen b-jets [GeV] (parton flavour)", True, None),
    ("dR_bb_jet_parton", "$\\Delta R_{bb}$ from gen b-jets (parton flavour)", True, None),
    ("n_lhe_init_bbbar", "LHE initial-state bb multiplicity", True, None),
    ("presel_n_lhe_init_bbbar", "LHE initial-state bb multiplicity (preselection)", True, None),
    ("presel_n_lhe_fin_bbbar", "LHE final-state bb multiplicity (preselection)", True, None),
    ("presel_n_lhe_bbbar", "LHE total bb multiplicity (preselection)", True, None),
    ("presel_lhe_init_flavor", "LHE initial-state flavor bin (preselection)", False, None),
    ("presel_z_mother_flavor", "GenPart Z/gamma* ancestor flavor bin (preselection)", False, None),
    ("presel_lhe_bbbar_fin_min_pt", "LHE final-state min b pT (preselection)", True, None),
    ("presel_lhe_bbbar_fin_max_pt", "LHE final-state max b pT (preselection)", True, None),
    ("presel_m_bb", "m_bb from LHE b quarks (preselection)", True, None),
    ("presel_dR_bb", "DeltaR_bb from LHE b quarks (preselection)", True, None),
    ("lhe_init_flavor", "LHE initial-state flavor bin (0=other,1=d,2=u,3=s,4=c,5=b)", False, None),
    ("z_mother_flavor", "GenPart Z/gamma* ancestor flavor bin (0=other,1=d,2=u,3=s,4=c,5=b)", False, None),
    ("n_lhe_fin_bbbar", "LHE final-state bb multiplicity", True, None),
    ("n_lhe_bbbar", "LHE total bb multiplicity", True, None),
    ("lhe_bbbar_fin_min_pt", "LHE final-state min b pT", True, None),
    ("lhe_bbbar_fin_max_pt", "LHE final-state max b pT", True, None),
    ("m_bb_lhe", "m_bb from LHE b quarks", True, None),
    ("dR_bb_lhe", "DeltaR_bb from LHE b quarks", True, None),
    ("presel_cms_appc_pass_z", "Appendix-C pass-Z flag (preselection)", False, None),
    (
        "presel_cms_appc_n_lep",
        "Appendix-C selected lepton multiplicity (preselection)",
        True,
        None,
    ),
    (
        "presel_cms_appc_n_bjets_clean",
        "Appendix-C clean b-jet multiplicity (preselection)",
        True,
        None,
    ),
    ("cms_appc_mll", "Appendix-C dressed SFOS $m_{\\ell\\ell}$ [GeV]", False, None),
    ("cms_appc_mll_b1", "Appendix-C dressed SFOS $m_{\\ell\\ell}$ [GeV] (Z + >=1 b-jet)", False, None),
    ("nominal_dressedLepPt1", "Leading dressed lepton $p_T$ [GeV]", True, 1),
    ("nominal_dressedLepPt2", "Subleading dressed lepton $p_T$ [GeV]", True, 1),
    ("nominal_dressedLepEta1", "Leading dressed lepton $\\eta$", False, 1),
    ("nominal_dressedLepEta2", "Subleading dressed lepton $\\eta$", False, 1),
]


# 1D hists
for var, xlabel, logy, bottom_sel_bin in plot_specs:
    print("Plotting", var)

    key_massive = resolve_hist_key(res_massive["Zbb_MiNNLO"]["output"], var)
    key_massless = resolve_hist_key(res_massless["Zmumu_13TeVGen"]["output"], var)
    if key_massive is None or key_massless is None:
        print(f"Skipping {var}: histogram not found in one of the inputs")
        continue

    h_massive = read_h(
        res_massive,
        f"Zbb_MiNNLO",
        res_massive[f"Zbb_MiNNLO"]["output"][key_massive].get(),
    )
    h_massless = read_h(
        res_massless,
        f"Zmumu_13TeVGen",
        res_massless[f"Zmumu_13TeVGen"]["output"][key_massless].get(),
    )
    h_massive, suffix_massive = maybe_select_bottom_bin(h_massive, bottom_sel_bin)
    h_massless, suffix_massless = maybe_select_bottom_bin(h_massless, bottom_sel_bin)
    suffix = suffix_massive or suffix_massless

    fig = plot_tools.makePlotWithRatioToRef(
        [h_massless, h_massive],
        labels=["Nominal MiNNLO", "Massive b's MiNNLO"],
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        logy=logy,
        rrange=auto_rrange_from_ratio(h_massless, h_massive),
        xlabel=xlabel,
    )
    rel_oname = f"samples_comparison_{var}{suffix}"
    oname = os.path.join(outdir, rel_oname)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
        print(f"Output directory '{outdir}' created.")
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)
"""

"""
derived_plot_specs = [
    ("dressed_MllPTll", "ewMll", "Dressed SFOS $m_{\\ell\\ell}$ [GeV] (from dressed_MllPTll)", False, 1),
    ("dressed_MllPTll", "ewPTll", "Dressed dilepton $p_T$ [GeV] (from dressed_MllPTll)", True, 1),
    ("dressed_YllMll", "ewAbsYll", "Dressed $|y_{\\ell\\ell}|$ (from dressed_YllMll)", False, 1),
]

for src_var, proj_axis, xlabel, logy, bottom_sel_bin in derived_plot_specs:
    print(f"Plotting {src_var} projected to {proj_axis}")
    key_massive = resolve_hist_key(res_massive["Zbb_MiNNLO"]["output"], src_var)
    key_massless = resolve_hist_key(res_massless["Zmumu_13TeVGen"]["output"], src_var)
    if key_massive is None or key_massless is None:
        print(f"Skipping {src_var}->{proj_axis}: source histogram not found in one of the inputs")
        continue

    h_massive = read_h(
        res_massive,
        "Zbb_MiNNLO",
        res_massive["Zbb_MiNNLO"]["output"][key_massive].get(),
    )
    h_massless = read_h(
        res_massless,
        "Zmumu_13TeVGen",
        res_massless["Zmumu_13TeVGen"]["output"][key_massless].get(),
    )
    h_massive, suffix_massive = maybe_select_bottom_bin(h_massive, bottom_sel_bin)
    h_massless, suffix_massless = maybe_select_bottom_bin(h_massless, bottom_sel_bin)
    h_massive = project_to_axis(h_massive, proj_axis)
    h_massless = project_to_axis(h_massless, proj_axis)
    suffix = suffix_massive or suffix_massless

    fig = plot_tools.makePlotWithRatioToRef(
        [h_massless, h_massive],
        labels=["Nominal MiNNLO", "Massive b's MiNNLO"],
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        logy=logy,
        rrange=auto_rrange_from_ratio(h_massless, h_massive),
        xlabel=xlabel,
    )
    rel_oname = f"samples_comparison_{src_var}_proj_{proj_axis}{suffix}"
    oname = os.path.join(outdir, rel_oname)
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)

# custom-bin cross-section checks requested for leading b-jet observables
key_leadpt_massive = resolve_hist_key(res_massive["Zbb_MiNNLO"]["output"], "lead_bjet_pt")
key_leadpt_massless = resolve_hist_key(res_massless["Zmumu_13TeVGen"]["output"], "lead_bjet_pt")
if key_leadpt_massive is not None and key_leadpt_massless is not None:
    h_leadpt_massive = read_h(
        res_massive,
        "Zbb_MiNNLO",
        res_massive["Zbb_MiNNLO"]["output"][key_leadpt_massive].get(),
    )
    h_leadpt_massless = read_h(
        res_massless,
        "Zmumu_13TeVGen",
        res_massless["Zmumu_13TeVGen"]["output"][key_leadpt_massless].get(),
    )
    h_leadpt_massive, suffix_massive = maybe_select_bottom_bin(h_leadpt_massive, None)
    h_leadpt_massless, suffix_massless = maybe_select_bottom_bin(h_leadpt_massless, None)
    suffix = suffix_massive or suffix_massless
    h_leadpt_massive = hh.rebinHist(
        h_leadpt_massive,
        h_leadpt_massive.axes[0].name,
        [30.0, 50.0, 75.0, 110.0, 150.0, 220.0, 300.0],
    )
    h_leadpt_massless = hh.rebinHist(
        h_leadpt_massless,
        h_leadpt_massless.axes[0].name,
        [30.0, 50.0, 75.0, 110.0, 150.0, 220.0, 300.0],
    )
    fig = plot_tools.makePlotWithRatioToRef(
        [h_leadpt_massless, h_leadpt_massive],
        labels=["Nominal MiNNLO", "Massive b's MiNNLO"],
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        logy=True,
        xlabel="Leading gen b-jet $p_T$ [GeV]",
        ylabel="Cross section / bin width [pb]",
        rrange=auto_rrange_from_ratio(h_leadpt_massless, h_leadpt_massive),
    )
    rel_oname = f"samples_comparison_lead_bjet_pt_custombins_30_50_75_110_150_220_300{suffix}"
    oname = os.path.join(outdir, rel_oname)
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)
else:
    print("Skipping custom lead_bjet_pt plot: histogram not found in one of the inputs")

key_leadeta_massive = resolve_hist_key(res_massive["Zbb_MiNNLO"]["output"], "lead_bjet_eta")
key_leadeta_massless = resolve_hist_key(res_massless["Zmumu_13TeVGen"]["output"], "lead_bjet_eta")
if key_leadeta_massive is not None and key_leadeta_massless is not None:
    h_leadeta_massive = read_h(
        res_massive,
        "Zbb_MiNNLO",
        res_massive["Zbb_MiNNLO"]["output"][key_leadeta_massive].get(),
    )
    h_leadeta_massless = read_h(
        res_massless,
        "Zmumu_13TeVGen",
        res_massless["Zmumu_13TeVGen"]["output"][key_leadeta_massless].get(),
    )
    h_leadeta_massive, suffix_massive = maybe_select_bottom_bin(h_leadeta_massive, None)
    h_leadeta_massless, suffix_massless = maybe_select_bottom_bin(h_leadeta_massless, None)
    suffix = suffix_massive or suffix_massless
    h_leadeta_massive = hh.makeAbsHist(h_leadeta_massive, h_leadeta_massive.axes[0].name, rename=False)
    h_leadeta_massless = hh.makeAbsHist(h_leadeta_massless, h_leadeta_massless.axes[0].name, rename=False)
    eta_max = float(h_leadeta_massive.axes[0].edges[-1])
    h_leadeta_massive = hh.rebinHist(
        h_leadeta_massive,
        h_leadeta_massive.axes[0].name,
        [0.0, 0.4, 0.8, 1.2, 1.6, 2.0, eta_max],
    )
    h_leadeta_massless = hh.rebinHist(
        h_leadeta_massless,
        h_leadeta_massless.axes[0].name,
        [0.0, 0.4, 0.8, 1.2, 1.6, 2.0, eta_max],
    )
    fig = plot_tools.makePlotWithRatioToRef(
        [h_leadeta_massless, h_leadeta_massive],
        labels=["Nominal MiNNLO", "Massive b's MiNNLO"],
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        logy=True,
        xlabel="Leading gen b-jet $|y|$",
        ylabel="Cross section / bin width [pb]",
        rrange=auto_rrange_from_ratio(h_leadeta_massless, h_leadeta_massive),
    )
    rel_oname = f"samples_comparison_lead_bjet_absy_custombins_0_0p4_0p8_1p2_1p6_2p0_inf{suffix}"
    oname = os.path.join(outdir, rel_oname)
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)
else:
    print("Skipping custom lead_bjet_absy plot: histogram not found in one of the inputs")



def plot_bhad_id_compare(var_pdt, var_legacy, xlabel, sample_key, sample_label, logy):
    if var_pdt not in sample_key["output"] or var_legacy not in sample_key["output"]:
        print(f"Skipping {sample_label} {var_pdt}/{var_legacy}: missing histogram")
        return

    h_pdt = read_h(
        {"tmp": sample_key},
        "tmp",
        sample_key["output"][var_pdt].get(),
    )
    h_legacy = read_h(
        {"tmp": sample_key},
        "tmp",
        sample_key["output"][var_legacy].get(),
    )

    fig = plot_tools.makePlotWithRatioToRef(
        [h_pdt, h_legacy],
        labels=["PDT helper", "Legacy helper"],
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        logy=logy,
        rrange=auto_rrange_from_ratio(h_pdt, h_legacy),
        xlabel=xlabel,
    )
    rel_oname = f"bhad_id_compare_{sample_label}_{var_pdt}"
    oname = os.path.join(outdir, rel_oname)
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)

    if var_pdt == "nBhad":
        vals_pdt = h_pdt.values()
        vals_legacy = h_legacy.values()
        ge1_pdt = np.sum(vals_pdt[h_pdt.axes[0].centers >= 1])
        ge1_legacy = np.sum(vals_legacy[h_legacy.axes[0].centers >= 1])
        print(
            f"{sample_label} nBhad>=1 yield: PDT={ge1_pdt:.6e}, Legacy={ge1_legacy:.6e}, "
            f"ratio(Leg/PDT)={(ge1_legacy/ge1_pdt if ge1_pdt else np.nan):.6f}"
        )

def plot_jet_collection_compare(var_nano, var_recl, xlabel, sample_key, sample_label, logy):
    if var_nano not in sample_key["output"] or var_recl not in sample_key["output"]:
        print(f"Skipping {sample_label} {var_nano}/{var_recl}: missing histogram")
        return

    h_nano = read_h({"tmp": sample_key}, "tmp", sample_key["output"][var_nano].get())
    h_recl = read_h({"tmp": sample_key}, "tmp", sample_key["output"][var_recl].get())
    fig = plot_tools.makePlotWithRatioToRef(
        [h_nano, h_recl],
        labels=["Nano GenJet b-tagged", "Reclustered GenPart+ghost-b"],
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        logy=logy,
        rrange=auto_rrange_from_ratio(h_nano, h_recl),
        xlabel=xlabel,
    )
    rel_oname = f"jet_collection_compare_{sample_label}_{var_nano}"
    oname = os.path.join(outdir, rel_oname)
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)


plot_bhad_id_compare(
    "leadB_pt",
    "leadB_pt_legacy",
    "Leading B-hadron $p_T$ [GeV] (events with >=1 B hadron)",
    res_massive["Zbb_MiNNLO"],
    "massive",
    True,
)
plot_bhad_id_compare(
    "leadB_pt",
    "leadB_pt_legacy",
    "Leading B-hadron $p_T$ [GeV] (events with >=1 B hadron)",
    res_massless["Zmumu_13TeVGen"],
    "massless",
    True,
)
plot_bhad_id_compare(
    "nBhad",
    "nBhad_legacy",
    "Number of B hadrons (all events)",
    res_massive["Zbb_MiNNLO"],
    "massive",
    True,
)
plot_bhad_id_compare(
    "nBhad",
    "nBhad_legacy",
    "Number of B hadrons (all events)",
    res_massless["Zmumu_13TeVGen"],
    "massless",
    True,
)

plot_jet_collection_compare(
    "n_bjets",
    "n_bjets_recl",
    "Number of b-jets",
    res_massive["Zbb_MiNNLO"],
    "massive",
    True,
)
plot_jet_collection_compare(
    "n_bjets",
    "n_bjets_recl",
    "Number of b-jets",
    res_massless["Zmumu_13TeVGen"],
    "massless",
    True,
)
plot_jet_collection_compare(
    "lead_bjet_pt",
    "lead_bjet_pt_recl",
    "Leading b-jet $p_T$ [GeV]",
    res_massive["Zbb_MiNNLO"],
    "massive",
    True,
)
plot_jet_collection_compare(
    "lead_bjet_pt",
    "lead_bjet_pt_recl",
    "Leading b-jet $p_T$ [GeV]",
    res_massless["Zmumu_13TeVGen"],
    "massless",
    True,
)
plot_jet_collection_compare(
    "sublead_bjet_pt",
    "sublead_bjet_pt_recl",
    "Subleading b-jet $p_T$ [GeV]",
    res_massive["Zbb_MiNNLO"],
    "massive",
    True,
)
plot_jet_collection_compare(
    "sublead_bjet_pt",
    "sublead_bjet_pt_recl",
    "Subleading b-jet $p_T$ [GeV]",
    res_massless["Zmumu_13TeVGen"],
    "massless",
    True,
)
plot_jet_collection_compare(
    "lead_bjet_eta",
    "lead_bjet_eta_recl",
    "Leading b-jet $\\eta$",
    res_massive["Zbb_MiNNLO"],
    "massive",
    True,
)
plot_jet_collection_compare(
    "lead_bjet_eta",
    "lead_bjet_eta_recl",
    "Leading b-jet $\\eta$",
    res_massless["Zmumu_13TeVGen"],
    "massless",
    False,
)
plot_jet_collection_compare(
    "sublead_bjet_eta",
    "sublead_bjet_eta_recl",
    "Subleading b-jet $\\eta$",
    res_massive["Zbb_MiNNLO"],
    "massive",
    False,
)
plot_jet_collection_compare(
    "sublead_bjet_eta",
    "sublead_bjet_eta_recl",
    "Subleading b-jet $\\eta$",
    res_massless["Zmumu_13TeVGen"],
    "massless",
    False,
)
plot_jet_collection_compare(
    "m_bb_jet",
    "m_bb_jet_recl",
    "$m_{bb}$ [GeV]",
    res_massive["Zbb_MiNNLO"],
    "massive",
    True,
)
plot_jet_collection_compare(
    "m_bb_jet",
    "m_bb_jet_recl",
    "$m_{bb}$ [GeV]",
    res_massless["Zmumu_13TeVGen"],
    "massless",
    True,
)
plot_jet_collection_compare(
    "dR_bb_jet",
    "dR_bb_jet_recl",
    "$\\Delta R_{bb}$",
    res_massive["Zbb_MiNNLO"],
    "massive",
    True,
)
plot_jet_collection_compare(
    "dR_bb_jet",
    "dR_bb_jet_recl",
    "$\\Delta R_{bb}$",
    res_massless["Zmumu_13TeVGen"],
    "massless",
    True,
)


if (
    "nBhad_pt5" in res_massive["Zbb_MiNNLO"]["output"]
    and "nBhad_pt5" in res_massless["Zmumu_13TeVGen"]["output"]
):
    h_nB_massive = read_h(
        res_massive,
        "Zbb_MiNNLO",
        res_massive["Zbb_MiNNLO"]["output"]["nBhad_pt5"].get(),
    )
    h_nB_massless = read_h(
        res_massless,
        "Zmumu_13TeVGen",
        res_massless["Zmumu_13TeVGen"]["output"]["nBhad_pt5"].get(),
    )

    def frac_nB_geq(h, nmin):
        centers = h.axes[0].centers
        vals = h.values()
        den = np.sum(vals)
        if den == 0:
            return np.nan
        return np.sum(vals[centers >= nmin]) / den

    print("B-hadron multiplicity fractions from nBhad_pt5:")
    print(
        "Nominal MiNNLO: f(nB>=1)={:.4f}, f(nB>=2)={:.4f}".format(
            frac_nB_geq(h_nB_massless, 1), frac_nB_geq(h_nB_massless, 2)
        )
    )
    print(
        "Massive b's MiNNLO: f(nB>=1)={:.4f}, f(nB>=2)={:.4f}".format(
            frac_nB_geq(h_nB_massive, 1), frac_nB_geq(h_nB_massive, 2)
        )
    )
    print_nB_table(h_nB_massless, "Nominal MiNNLO")
    print_nB_table(h_nB_massive, "Massive b's MiNNLO")

key_lhe_init_flav_massive = resolve_hist_key(
    res_massive["Zbb_MiNNLO"]["output"], "lhe_init_flavor"
)
key_lhe_init_flav_massless = resolve_hist_key(
    res_massless["Zmumu_13TeVGen"]["output"], "lhe_init_flavor"
)
if key_lhe_init_flav_massive is not None and key_lhe_init_flav_massless is not None:
    h_lhe_init_flav_massive = read_h(
        res_massive,
        "Zbb_MiNNLO",
        res_massive["Zbb_MiNNLO"]["output"][key_lhe_init_flav_massive].get(),
    )
    h_lhe_init_flav_massless = read_h(
        res_massless,
        "Zmumu_13TeVGen",
        res_massless["Zmumu_13TeVGen"]["output"][key_lhe_init_flav_massless].get(),
    )
    print_lhe_init_flavor_table(h_lhe_init_flav_massless, "Nominal MiNNLO")
    print_lhe_init_flavor_table(h_lhe_init_flav_massive, "Massive b's MiNNLO")

key_z_mother_flav_massive = resolve_hist_key(
    res_massive["Zbb_MiNNLO"]["output"], "z_mother_flavor"
)
key_z_mother_flav_massless = resolve_hist_key(
    res_massless["Zmumu_13TeVGen"]["output"], "z_mother_flavor"
)
if key_z_mother_flav_massive is not None and key_z_mother_flav_massless is not None:
    h_z_mother_flav_massive = read_h(
        res_massive,
        "Zbb_MiNNLO",
        res_massive["Zbb_MiNNLO"]["output"][key_z_mother_flav_massive].get(),
    )
    h_z_mother_flav_massless = read_h(
        res_massless,
        "Zmumu_13TeVGen",
        res_massless["Zmumu_13TeVGen"]["output"][key_z_mother_flav_massless].get(),
    )
    print_z_mother_flavor_table(h_z_mother_flav_massless, "Nominal MiNNLO")
    print_z_mother_flavor_table(h_z_mother_flav_massive, "Massive b's MiNNLO")


h_massive = h_massive_nominal
h_massless = h_massless_nominal

plot_tagging_matrix(h_massive_nominal, "Massive b's MiNNLO", "tagging_matrix_massive")
plot_tagging_matrix(h_massless_nominal, "Nominal MiNNLO", "tagging_matrix_massless")

print("Ratio of selected events (bottom_sel==1): ")
print(
    h_massless[{"bottom_sel": 1}].sum().value / h_massive[{"bottom_sel": 1}].sum().value
)
print("% of massive MiNNLO sample being selected for swap:")
print(h_massive[{"bottom_sel": 1}].sum().value / h_massive.sum().value)
print("% of massless MiNNLO sample being selected for swap:")
print(h_massless[{"bottom_sel": 1}].sum().value / h_massless.sum().value)

# comparison of selected bottom_sel events
for vars in [["ptVgen"], ["absYVgen"]]:

    nominal_bottom = h_massless[{"bottom_sel": 1}].project(*vars)
    massive = h_massive[{"bottom_sel": 1}].project(*vars)
    if norm_mode == "sigma-difference":
        massive_total = h_massive.project(*vars)
        massive = scaled_to_integral(
            massive,
            massive_total.sum().value,
            f"massive_selected_{'_'.join(vars)}",
        )
    if massive_scale != 1.0:
        massive = hh.scaleHist(massive, massive_scale, createNew=True)
    if normalize:
        massive = hh.scaleHist(
            massive, nominal_bottom.sum().value / massive.sum().value
        )

    fig = plot_tools.makePlotWithRatioToRef(
        [nominal_bottom, massive],
        labels=[
            "Nominal MiNNLO (selected)",
            (
                "Massive b's MiNNLO (selected, sigma-difference normalized)"
                if norm_mode == "sigma-difference"
                else (
                    f"Massive b's MiNNLO (selected, x{massive_scale:g}, normalized)"
                    if normalize
                    else f"Massive b's MiNNLO (selected, x{massive_scale:g})"
                )
            ),
        ],
        rrange=auto_rrange_from_ratio(
            nominal_bottom,
            massive,
            x_range=(0, 100) if vars[0] == "ptVgen" else None,
        ),
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        xlim=(0, 100) if vars[0] == "ptVgen" else None,
    )
    rel_oname = "bb_" + "_".join(vars)
    if norm_mode == "sigma-difference":
        rel_oname += "_sigma_difference"
    elif massive_scale != 1.0:
        rel_oname += f"_x{massive_scale:g}".replace(".", "p")
    if normalize:
        rel_oname += "_normalized"
    oname = os.path.join(outdir, rel_oname)
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)

# comparison of final distributions
"""
h_massive = h_massive_nominal
h_massless = h_massless_nominal

for vars in [["ptVgen"], ["absYVgen"]]:

    nominal = h_massless.project(*vars)
    nominal_nobottom = h_massless[{"bottom_sel": 0}].project(*vars)
    massive = h_massive[{"bottom_sel": 1}].project(*vars)
    if norm_mode == "sigma-difference":
        massive_total = h_massive.project(*vars)
        target_massive = massive_total.sum().value
        target_nobottom = nominal.sum().value - target_massive
        if target_nobottom < 0:
            raise ValueError(
                f"sigma-difference target for 5FS_bveto is negative ({target_nobottom}) for vars={vars}"
            )
        nominal_nobottom = scaled_to_integral(
            nominal_nobottom,
            target_nobottom,
            f"nominal_nobottom_{'_'.join(vars)}",
        )
        massive = scaled_to_integral(
            massive,
            target_massive,
            f"massive_selected_{'_'.join(vars)}",
        )
        print(
            f"[sigma-difference:{'_'.join(vars)}] target_massive={target_massive:.6e}, "
            f"target_5FS_bveto={target_nobottom:.6e}, total_5FS={nominal.sum().value:.6e}"
        )
    else:
        if massive_scale != 1.0:
            massive = hh.scaleHist(massive, massive_scale, createNew=True)
        if normalize:
            nominal_bottom = h_massless[{"bottom_sel": 1}].project(*vars)
            massive = hh.scaleHist(
                massive, nominal_bottom.sum().value / massive.sum().value
            )
    corrected = hh.addHists(nominal_nobottom, massive)

    fig = plot_tools.makePlotWithRatioToRef(
        [nominal, nominal_nobottom, corrected],
        labels=[
            "Nominal MiNNLO (inclusive)",
            "Nominal MiNNLO (b's subtracted)",
            (
                "Corrected MiNNLO (inclusive, sigma-difference normalization)"
                if norm_mode == "sigma-difference"
                else (
                    f"Corrected MiNNLO (inclusive, x{massive_scale:g}, normalized swap)"
                    if normalize
                    else f"Corrected MiNNLO (inclusive, x{massive_scale:g})"
                )
            ),
        ],
        rrange=auto_rrange_from_ratio(
            nominal,
            corrected,
            x_range=(0, 100) if vars[0] == "ptVgen" else None,
        ),
        ratio_legend=False,
        nlegcols=1,
        legtext_size=16,
        binwnorm=1,
        xlim=(0, 100) if vars[0] == "ptVgen" else None,
    )
    rel_oname = "inclusive_" + "_".join(vars)
    if norm_mode == "sigma-difference":
        rel_oname += "_sigma_difference"
    elif massive_scale != 1.0:
        rel_oname += f"_x{massive_scale:g}".replace(".", "p")
    if normalize:
        rel_oname += "_normalized"
    oname = os.path.join(outdir, rel_oname)
    fig.savefig(oname + ".pdf", bbox_inches="tight")
    fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    output_tools.write_index_and_log(outdir, rel_oname)

# # ratio 2d plot
# vars = ["ptVgen", "absYVgen"]
# nominal = h_massless.project(*vars)
# nominal_nobottom = h_massless[{"bottom_sel": 0}].project(*vars)
# massive = h_massive[{"bottom_sel": 1}].project(*vars)
# corrected = hh.addHists(nominal_nobottom, massive)
# h2_ratio = hh.divideHists(corrected, nominal)
# fig = hep.hist2dplot(h2_ratio)
# rel_oname = "inclusive_2d_" + "_".join(vars)
# oname = os.path.join(outdir, rel_oname)
# plt.xlim(0, 100)
# plt.savefig(oname + ".pdf", bbox_inches="tight")
# plt.savefig(oname + ".png", bbox_inches="tight", dpi=300)
# output_tools.write_index_and_log(outdir, rel_oname)
# plt.close()
# for var in vars:
#     h_ratio = hh.divideHists(corrected.project(var), nominal.project(var))
#     hep.histplot(h_ratio)
#     plt.axhline(1, color="black", alpha=0.5, linestyle="--")
#     plt.xlim(0, 100) if var == "ptVgen" else None
#     plt.ylim(0.9, 1.1)
#     rel_oname = "inclusive_ratio_" + var
#     oname = os.path.join(outdir, rel_oname)
#     plt.savefig(oname + ".pdf", bbox_inches="tight")
#     plt.savefig(oname + ".png", bbox_inches="tight", dpi=300)
#     plt.close()
#     output_tools.write_index_and_log(outdir, rel_oname)

# outpath = "."
# generator = "MiNNLO_Zbb"
# import numpy as np

# h2_ratio_out_vals = h2_ratio.project("absYVgen", "ptVgen").values()[
#     np.newaxis, :, :, np.newaxis
# ]  # (Q, Y, pt, vars)
# output_dict = {
#     f"{generator}_minnlo_ratio": h2_ratio,
#     f"{generator}_hist": corrected,
#     "minnlo_ref_hist": nominal,
# }
# outfile = f"{outpath}/{generator}_CorrZ.pkl.lz4"
# output_tools.write_lz4_pkl_output(outfile, "Z", output_dict, outdir, [], {})

# # angular coefficients
# h_massive = read_h(
#     res_massive,
#     f"Zbb_MiNNLO",
#     res_massive[f"Zbb_MiNNLO"]["output"]["nominal_gen_helicity_xsecs_scale"].get(),
# )
# h_massless = read_h(
#     res_massless,
#     f"ZmumuPostVFP",
#     res_massless[f"ZmumuPostVFP"]["output"]["nominal_gen_helicity_xsecs_scale"].get(),
# )
# for vars in [["ptVgen"], ["absYVgen"]]:

#     h_massive_sigmaUL = h_massive[{"helicity": -1j, "bottom_sel": 1}].project(*vars)
#     h_nominal_sigmaUL = h_massless[{"helicity": -1j}].project(*vars)
#     h_nominal_nobottom_sigmaUL = h_massless[{"helicity": -1j, "bottom_sel": 0}].project(*vars)
#     h_corrected_sigmaUL = hh.addHists(h_nominal_nobottom_sigmaUL, h_massive_sigmaUL)

#     for i in range(0, 8):
#         coeff = f"A{i}"

#         h_massive_hel = h_massive[{"helicity": i, "bottom_sel": 1}].project(*vars)
#         h_nominal_hel = h_massless[{"helicity": i}].project(*vars)
#         h_nominal_nobottom_hel = h_massless[{"helicity": i, "bottom_sel": 0}].project(*vars)
#         h_corrected_hel = hh.addHists(h_nominal_nobottom_hel, h_massive_hel)

#         h_nominal_ai = hh.divideHists(h_nominal_hel, h_nominal_sigmaUL, createNew=True)
#         h_corrected_ai = hh.divideHists(h_corrected_hel, h_corrected_sigmaUL, createNew=True)
#         h_nominal_nobottom_ai = hh.divideHists(
#             h_nominal_nobottom_hel, h_nominal_nobottom_sigmaUL, createNew=True
#         )

#         fig = plot_tools.makePlotWithRatioToRef(
#             [h_nominal_ai, h_nominal_nobottom_ai, h_corrected_ai],
#             labels=[
#                 f"Nominal MiNNLO (inclusive)",
#                 f"Nominal MiNNLO (0b)",
#                 f"Corrected MiNNLO (inclusive)",
#             ],
#             rrange=[[0.95, 1.05]],
#             ratio_legend=False,
#             nlegcols=1,
#             legtext_size=16,
#             #binwnorm=1,
#             xlim=(0, 100) if vars[0] == "ptVgen" else None,
#             ylabel=f"{coeff}",
#         )
#         rel_oname = f"{coeff}_" + "_".join(vars)
#         oname = os.path.join(outdir, rel_oname)
#         fig.savefig(oname + ".pdf", bbox_inches="tight")
#         fig.savefig(oname + ".png", bbox_inches="tight", dpi=300)
#         plt.close(fig)
#         output_tools.write_index_and_log(outdir, rel_oname)
