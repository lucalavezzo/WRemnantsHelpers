"""Per-fine-bin model/theory-corr ratio in the qT tail, WITHOUT rebuilding the
heavy model (avoids the OOM on a memory-pressured node).

Model σ_gen(λ_central) on the theory-corr's fine qT edges, |Y|<2.5, was already
computed (sigma_gen_at_lambda run, log fine_compare_Ylt2p5.log) — pasted below.
Here we only project the theory correction onto the SAME fine edges (cheap) and
divide, to see whether the [44,100] agreement is really ~0.05% per fine bin (=> the
earlier −1.4% was just the single WIDE overflow bin's integration averaging).
"""

import numpy as np

from wremnants.postprocessing.scetlib_np.validation.agreement import (
    load_theory_corr_hist,
    theory_corr_projection,
)

CORRZ = (
    "/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections/"
    "scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4"
)

FINE = [
    0,
    0.5,
    1,
    1.5,
    2,
    2.5,
    3,
    3.5,
    4,
    4.5,
    5,
    5.5,
    6,
    6.5,
    7,
    7.5,
    8,
    8.5,
    9,
    9.5,
    10,
    10.5,
    11,
    11.5,
    12,
    12.5,
    13,
    13.5,
    14,
    14.5,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    42,
    44,
    46,
    48,
    50,
    52,
    54,
    56,
    58,
    60,
    65,
    70,
    80,
    90,
    100,
]

# model σ_gen(λ_c), |Y|<2.5, on FINE edges (from fine_compare_Ylt2p5.log)
MODEL = [
    3.5909,
    10.5888,
    16.509,
    22.1719,
    26.8459,
    30.4692,
    33.0583,
    34.6956,
    35.5088,
    35.6485,
    35.2697,
    34.517,
    33.5153,
    32.3655,
    31.1439,
    29.9044,
    28.6829,
    27.5007,
    26.3689,
    25.2921,
    24.2705,
    23.3021,
    22.3841,
    21.5132,
    20.6863,
    19.9007,
    19.1538,
    18.4435,
    17.7677,
    17.1244,
    32.4401,
    30.2137,
    28.1875,
    26.338,
    24.6432,
    23.0843,
    21.6466,
    20.3177,
    19.0871,
    17.944,
    16.8893,
    15.9349,
    15.0441,
    14.209,
    13.4311,
    12.7062,
    12.0291,
    11.3958,
    10.8027,
    10.2467,
    9.7247,
    9.2342,
    8.773,
    8.3387,
    7.9294,
    14.7224,
    13.344,
    12.1109,
    11.0043,
    10.0088,
    9.1114,
    8.3006,
    7.5673,
    6.906,
    6.3109,
    13.5436,
    10.9292,
    16.1593,
    10.9578,
    7.4406,
]


def main():
    edges = np.array(FINE, dtype=float)
    model = np.array(MODEL, dtype=float)
    assert model.size == edges.size - 1, (model.size, edges.size - 1)
    gen_axes = [("ptVGen", edges), ("absYVGen", np.array([0.0, 2.5]))]
    h = load_theory_corr_hist(CORRZ, proc="Z")
    corr = theory_corr_projection(h, gen_axes, "ptVGen", var="pdf0")
    corr = np.asarray(corr, dtype=float)
    ratio = np.where(corr > 0, model / corr, np.nan)

    ctr = 0.5 * (edges[:-1] + edges[1:])
    print(f"{'qT bin':>14}  {'model':>10}  {'corr':>10}  {'model/corr':>10}")
    for i in range(model.size):
        tag = "  <-- tail" if edges[i] >= 44 else ""
        print(
            f"[{edges[i]:5.1f},{edges[i+1]:6.1f}) {model[i]:10.4g}  {corr[i]:10.4g}  "
            f"{ratio[i]:10.5f}{tag}"
        )

    # summary over bulk (<44) and tail (>=44)
    for lab, m in [("qT<44", ctr < 44), ("qT>=44 (tail)", ctr >= 44)]:
        r = ratio[m]
        r = r[np.isfinite(r)]
        w = corr[m][np.isfinite(ratio[m])]
        print(
            f"\n  {lab:16s}: mean|model/corr-1| = {np.average(np.abs(r-1), weights=w)*100:.3f}%"
            f"   range [{r.min():.4f}, {r.max():.4f}]  ({r.size} bins)"
        )

    _plot(edges, model, corr, ratio)


def _plot(edges, model, corr, ratio):
    """Theorist-facing figure: dσ/dqT (model vs SCETlib+DYTurbo) + ratio panel,
    on the correction's own fine qT binning, |Y|<2.5, out to the grid ceiling 100."""
    import os

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from wremnants.postprocessing.scetlib_np import plot_output

    widths = np.diff(edges)
    dm, dc = model / widths, corr / widths  # differential dσ/dqT (variable bins)

    fig, (ax, axr) = plt.subplots(
        2,
        1,
        sharex=True,
        figsize=(7.2, 6.2),
        gridspec_kw={"height_ratios": [3, 1.3], "hspace": 0.07},
    )
    ax.stairs(dc, edges, color="black", lw=1.6, label="SCETlib+DYTurbo (pdf0)")
    ax.stairs(
        dm,
        edges,
        color="#e42536",
        lw=1.6,
        ls=(0, (4, 2)),
        label=r"ParamModel $\sigma_{\mathrm{gen}}$ (bt-grid integral)",
    )
    ax.set_yscale("log")
    ax.set_ylabel(r"$d\sigma_{\mathrm{gen}}/dq_T$  [a.u.]")
    ax.legend(loc="upper right", fontsize=10)
    ax.text(
        0.03,
        0.06,
        "Z, |y|<2.5, Q∈[60,120]\nλ_central (FranksVals)\ncorr's own fine qT binning",
        transform=ax.transAxes,
        fontsize=8.5,
        va="bottom",
        family="monospace",
        bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.9),
    )
    ax.axvline(44, color="0.6", lw=0.8, ls=":")
    ax.margins(x=0)

    axr.stairs(ratio, edges, color="#e42536", lw=1.5, baseline=None)
    axr.axhline(1.0, color="0.5", lw=0.8, ls="--")
    axr.axvline(44, color="0.6", lw=0.8, ls=":")
    axr.set_ylabel("model /\nSCETlib+DYTurbo")
    axr.set_xlabel(r"$q_T$ (ptVGen) [GeV]")
    axr.set_ylim(0.90, 1.02)
    axr.margins(x=0)
    axr.text(
        0.62,
        0.10,
        "tail deficit grows\ntoward grid ceiling (100)",
        transform=axr.transAxes,
        fontsize=8,
        color="#e42536",
    )

    outdir = os.path.expanduser("~/public_html/alphaS/260702_scetlib_np_validation")
    plot_output.save_plot(
        outdir, "fine_sigma_gen_vs_theorycorr_Ylt2p5", fig=fig, dpi=130
    )
    plt.close(fig)
    print(f"\n[plot] wrote {outdir}/fine_sigma_gen_vs_theorycorr_Ylt2p5.png(.pdf,.log)")


if __name__ == "__main__":
    main()
