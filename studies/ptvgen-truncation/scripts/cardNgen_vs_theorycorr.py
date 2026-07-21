"""3-way: card N_gen vs bt-grid model σ_gen vs the OFFICIAL theory correction (SCETlib+DYTurbo).

Motivation: validate_agreement --reference card (new small-bt6k grid) shows model σ_gen ==
card N_gen to 1.000 in the RESOLVED ptVGen bins [0,44), but 0.83 in the single overflow bin
[44,100-label]. The model reaches only qT=100 (bt-grid ceiling); the card's N_gen overflow is
filled from the histmaker AXIS overflow -> qT in (44, inf) (response_matrix._append_axis_overflow).
Hypothesis (Luca): the histmaker gen is MiNNLO reweighted to SCETlib+DYTurbo, but the correction
only covers qT<=100, so the overflow bin keeps the raw-MiNNLO qT>100 tail that neither the model
NOR the theory correction predicts.

This script compares the card N_gen DIRECTLY to the theory correction (no model / no bt-grid),
projected onto the SAME gen bins. Expectation: ~1.0 in the resolved bins (both are SCETlib+DYTurbo
there, by construction of the correction), and an EXCESS of N_gen over the correction in the
overflow bin == the uncovered qT>100 MiNNLO tail. That shows the discrepancy is in the CARD's
overflow domain, not in our reconstruction.

Run: wremnants container (latest) + venv + setup.sh.
"""

import numpy as np

CARD = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260623_Zhistmaker/"
    "ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_realdata/ZMassDilepton.hdf5"
)
CORRZ = (
    "/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections/"
    "scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4"
)
BTGRID = "/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_smallbt6k/"
WEBDIR = (
    "/home/submit/lavezzo/public_html/alphaS/260703_new_btgrid/cardNgen_vs_theorycorr"
)


def main():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from rabbit.inputdata import FitInputData
    from wremnants.postprocessing.scetlib_np.param_model import (
        _R_info_from_auxiliary,
        SCETlibNPParamModel,
    )
    from wremnants.postprocessing.scetlib_np.validation.agreement import (
        load_theory_corr_hist,
        theory_corr_projection,
    )
    from wremnants.postprocessing.scetlib_np import plot_output

    print("Loading FitInputData (1 GB card) …", flush=True)
    indata = FitInputData(CARD)
    R = _R_info_from_auxiliary(indata)
    gen_axes = R["gen_axes"]
    names = [n for n, _ in gen_axes]
    shapes = [len(e) - 1 for _, e in gen_axes]
    edges = dict(gen_axes)
    N = np.asarray(R["N_gen"], float).reshape(shapes)
    ptv_ax = names.index("ptVGen")
    ptv_edges = edges["ptVGen"]
    print(f"gen axes: {[(n, len(e)-1) for n, e in gen_axes]}")
    print(f"ptVGen edges: {ptv_edges}")

    # card N_gen projected onto ptVGen (sum over the other gen axes)
    other = tuple(i for i in range(N.ndim) if i != ptv_ax)
    Ngen = N.sum(axis=other)

    # bt-grid model σ_gen(λ_c) on the SAME gen grid (new small-bt6k grid)
    print("Constructing SCETlibNPParamModel (bt integral, new grid) …", flush=True)
    model = SCETlibNPParamModel(indata, btgrid_dir=BTGRID, check_agreement=False)
    mg = np.asarray(model.sigma_gen_central, float).reshape(model.gen_shape)
    m_names = [n for n, _ in model._gen_axes_meta]
    m_ptv = m_names.index("ptVGen")
    model_ptv = mg.sum(axis=tuple(i for i in range(mg.ndim) if i != m_ptv))

    # theory correction (SCETlib+DYTurbo absolute) on the SAME gen bins
    h = load_theory_corr_hist(CORRZ, proc="Z")
    corr = np.asarray(theory_corr_projection(h, gen_axes, "ptVGen", var="pdf0"), float)

    # normalize corr + model to the card N_gen total on the RESOLVED bins (exclude
    # the trailing overflow) so the comparison is shape, not (yields vs pb) norm.
    nres = Ngen.size - 1  # last bin = overflow [44,100-label]
    corr_n = corr * (Ngen[:nres].sum() / corr[:nres].sum())
    model_n = model_ptv * (Ngen[:nres].sum() / model_ptv[:nres].sum())
    r_ngen = np.where(corr_n > 0, Ngen / corr_n, np.nan)
    r_model = np.where(corr_n > 0, model_n / corr_n, np.nan)

    widths = np.diff(ptv_edges)
    print(
        "\n  ptVGen bin        N_gen       model(bt)    corr(SD)     N_gen/corr  model/corr"
    )
    for i in range(Ngen.size):
        lo, hi = ptv_edges[i], ptv_edges[i + 1]
        tag = "  <- OVERFLOW (qT in (44,inf))" if i == Ngen.size - 1 else ""
        print(
            f"  [{lo:5.1f},{hi:6.1f})  {Ngen[i]:11.5g} {model_n[i]:11.5g} {corr_n[i]:11.5g}  "
            f"{r_ngen[i]:9.4f}  {r_model[i]:9.4f}{tag}"
        )

    # ---- plot ----
    fig, (ax, axr) = plt.subplots(
        2,
        1,
        figsize=(8.2, 6.6),
        sharex=True,
        gridspec_kw=dict(height_ratios=[3, 1], hspace=0.07),
    )
    ax.stairs(
        Ngen / widths,
        ptv_edges,
        color="k",
        lw=1.9,
        label=r"card $N_{gen}$ (MiNNLO$\to$SCETlib+DYTurbo, overflow qT$>$44)",
    )
    ax.stairs(
        model_n / widths,
        ptv_edges,
        color="C3",
        lw=1.5,
        label=r"bt-grid model $\sigma_{gen}(\lambda_c)$ (new small-$b_T$ grid)",
    )
    ax.stairs(
        corr_n / widths,
        ptv_edges,
        color="C0",
        lw=1.5,
        ls=(0, (4, 2)),
        label=r"theory corr SCETlib+DYTurbo",
    )
    ax.set_yscale("log")
    ax.set_ylabel(r"$\sigma$ / bin width  (norm. on resolved qT$<$44)")
    ax.set_title(
        r"$\sigma_{gen}$: card $N_{gen}$ vs bt-grid model vs theory corr — ptVGen (Z, incl. $|y|$)"
    )
    ax.legend(fontsize=8.5)
    ax.grid(alpha=0.3)

    axr.axhline(1.0, color="C0", lw=1, ls="--")
    axr.stairs(r_ngen, ptv_edges, color="k", lw=1.7, label=r"$N_{gen}$/corr")
    axr.stairs(r_model, ptv_edges, color="C3", lw=1.4, label=r"model/corr")
    axr.axvspan(ptv_edges[-2], ptv_edges[-1], color="0.85", zorder=0)
    axr.annotate(
        "overflow qT$>$44 (incl. qT$>$100):\nmodel & corr stop at 100,\ncard keeps the MiNNLO tail",
        xy=(0.5 * (ptv_edges[-2] + ptv_edges[-1]), r_ngen[-1]),
        xytext=(46, 1.27),
        fontsize=7.5,
        ha="left",
        arrowprops=dict(arrowstyle="->", color="0.4"),
    )
    axr.set_ylabel("ratio / corr")
    axr.set_xlabel(r"$p_T^{V,\,gen}$ [GeV]")
    axr.set_ylim(0.9, 1.42)
    axr.legend(fontsize=8, loc="upper left", ncol=2)
    axr.grid(alpha=0.3)

    fig.tight_layout()
    plot_output.save_plot(
        WEBDIR,
        "cardNgen_vs_theorycorr",
        fig=fig,
        meta_info={
            "study": "ptvgen-truncation",
            "point": "resolved qT<44: card N_gen == model == theory corr (all SCETlib+DYTurbo). "
            "overflow [44,100-label]=qT in (44,inf): model & corr stop at 100 and AGREE; "
            "card N_gen sits ~20% above because it keeps the qT>100 MiNNLO tail.",
            "card": CARD,
            "corr": CORRZ,
            "btgrid": BTGRID,
            "overflow_Ngen_over_corr": float(r_ngen[-1]),
            "overflow_model_over_corr": float(r_model[-1]),
        },
    )
    print(f"\nsaved -> {WEBDIR}/cardNgen_vs_theorycorr.png")


if __name__ == "__main__":
    main()
