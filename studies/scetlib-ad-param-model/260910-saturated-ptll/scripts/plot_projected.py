#!/usr/bin/env python3
"""The ptll projection this task tests: data vs the two postfit tunes, and the
per-bin contribution to the projected saturated statistic.

Figure 1 goes through wums.plot_tools.makePlotWithRatioToRef (the house rule).
Figure 2 is bare matplotlib because what it shows -- a per-bin contribution to
a chi2, against its flat ndf=1 expectation -- is not a ratio of histograms and
wums has no entry point for it.
"""
import sys

import hist
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, "/work/submit/lavezzo/alphaS/rabbit-blinding")
from rabbit import io_tools  # noqa: E402
from wums import output_tools, plot_tools  # noqa: E402

OUTDIR = sys.argv[1]
ARMS = [
    ("unwalled", sys.argv[2], "#1f77b4"),
    (r"walled $\tau=5$", sys.argv[3], "#d62728"),
]

data = None
preds, qbins, meta_arms = [], [], {}
for label, fr, _c in ARMS:
    res, meta = io_tools.get_fitresult(fr, meta=True)
    ch = res["mappings"]["BaseMapping"]["channels"]["ch0"]
    hN = ch["hist_postfit_inclusive"].get()
    hD = ch["hist_nobs"].get()
    edges = np.asarray(hN.axes["ptll"].edges)
    ax = hist.axis.Variable(edges, name="ptll")
    Nj = hN.values().sum(axis=1)
    Dj = hD.values().sum(axis=1)
    if data is None:
        data = hist.Hist(ax, storage=hist.storage.Weight())
        data.view(flow=False).value = Dj
        data.view(flow=False).variance = Dj
        Dref = Dj
    else:
        assert np.allclose(Dj, Dref)
    h = hist.Hist(ax, storage=hist.storage.Weight())
    h.view(flow=False).value = Nj
    h.view(flow=False).variance = 0.0
    preds.append(h)
    q = 2.0 * (Nj - Dj + Dj * np.log(Dj / Nj))
    qbins.append(q)
    meta_arms[label] = dict(fitresult=fr, q=float(q.sum()), ndf=int(len(Nj)))

labels = [r"data", *[l for l, _, _ in ARMS]]
colors = ["black", *[c for _, _, c in ARMS]]
meta = {
    "what": "ptll projection of the 39x20 (ptll,yll) fit; postfit_inclusive vs nobs",
    "statistic": "q_fixed = 2 sum_j [N_j - D_j + D_j ln(D_j/N_j)], ndf = 39; "
    "the projected saturated statistic with the model parameters HELD at the "
    "main postfit, i.e. a LOWER bound on rabbit's "
    "--computeSaturatedProjectionTests value",
    "arms": meta_arms,
    "blinding": "alpha_s blinded additively; no central value appears here",
}

fig = plot_tools.makePlotWithRatioToRef(
    [data, *preds],
    labels=labels,
    colors=colors,
    xlabel=r"$p_{T}^{\ell\ell}$ (GeV)",
    ylabel="Events / GeV",
    binwnorm=1.0,
    rlabel=["postfit / data"],
    rrange=[[0.99, 1.011]],
    dataIdx=0,
    ratio_to_data=True,
    yerr=True,
    nlegcols=1,
    cms_label="Preliminary",
    logoPos=0,
    grid=True,
)
plot_tools.save_pdf_and_png(OUTDIR, "ptll_projection", fig=fig)
output_tools.write_index_and_log(
    OUTDIR, "ptll_projection", analysis_meta_info=meta, args=None
)

centers = 0.5 * (
    np.asarray(data.axes["ptll"].edges[:-1]) + np.asarray(data.axes["ptll"].edges[1:])
)
edges = np.asarray(data.axes["ptll"].edges)
# The wums CMS style is global once plot_tools is imported and its font sizes
# are sized for a single big panel; this two-panel diagnostic needs the plain
# style to stay legible.
with plt.style.context("default"):
    fig2, axs = plt.subplots(
        2, 1, figsize=(8, 6.4), sharex=True, gridspec_kw=dict(height_ratios=[1.4, 1])
    )
    for (label, _fr, c), q in zip(ARMS, qbins):
        axs[0].stairs(
            q,
            edges,
            color=c,
            lw=1.8,
            baseline=None,
            label=f"{label}:  q = {q.sum():.2f} / 39",
        )
        axs[1].stairs(np.cumsum(q), edges, color=c, lw=1.8, baseline=None, label=label)
    axs[0].axhline(
        1.0, color="0.45", ls=":", lw=1.2, label="ndf = 1 per bin (the expectation)"
    )
    axs[0].set_ylabel("per-bin contribution to $q$", fontsize=11)
    axs[0].legend(fontsize=10, loc="upper right")
    axs[1].stairs(
        np.arange(1, len(q) + 1),
        edges,
        color="0.45",
        ls=":",
        lw=1.2,
        baseline=None,
        label="cumulative ndf",
    )
    axs[1].set_ylabel("cumulative $q$", fontsize=11)
    axs[1].set_xlabel(r"$p_{T}^{\ell\ell}$ (GeV)", fontsize=11)
    axs[1].legend(fontsize=10, loc="lower right")
    for a in axs:
        a.tick_params(labelsize=10)
        a.grid(alpha=0.25, ls=":")
    axs[0].set_title(
        "projected saturated statistic on $p_T^{\\ell\\ell}$, "
        "model parameters held at the main postfit",
        fontsize=11,
    )
    fig2.tight_layout()
plot_tools.save_pdf_and_png(OUTDIR, "ptll_projected_q_breakdown", fig=fig2)
output_tools.write_index_and_log(
    OUTDIR, "ptll_projected_q_breakdown", analysis_meta_info=meta, args=None
)
print("wrote ptll_projection and ptll_projected_q_breakdown to", OUTDIR)
