#!/usr/bin/env python3
"""Figures for the analytic d(conv)/d(ln muF) round.

Reads the JSON written by the gate scripts; runs no calculation.
"""
import json
import os
import sys

import numpy as np

C_SHIP = "#e42536"     # shipped model
C_ANL = "#5790fc"      # analytic alone
C_CORR = "#3f9950"     # analytic + interpolated residual
C_T3 = "#964a8b"
C_GREY = "#7a21dd"


def fig1(d, outdir):
    """The analytic derivative against a converged central difference."""
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    a = d["partA"]
    mu = np.array([r["muf"] for r in a])
    fd = np.array([r["fd"] for r in a])
    fig, ax = plot_tools.figure(
        mu, xlabel=r"$\mu_\mathrm{F}$ (GeV)",
        ylabel=r"analytic $/$ finite difference $-\,1$",
        xlim=[1.8, 100.0], ylim=[-0.6, 0.06], grid=True, logx=True,
        automatic_scale=False, width_scale=1.15)
    for key, lab, col, ls in (
            ("p0", r"$2g\,P_0$ only  (LO splitting)", C_SHIP, "solid"),
            ("p0p1", r"$+\,2g^2 P_1$  (NLO)", "#f89c20", "solid"),
            ("p0p1p2", r"$+\,2g^3 P_2$  (NNLO) $\;\to$ what the route needs",
             C_CORR, "solid")):
        y = np.array([r[key] for r in a]) / fd - 1.0
        ax.plot(mu, y, color=col, lw=2.6, marker="o", ms=5, ls=ls, label=lab)
    ax.axhline(0.0, color="k", lw=0.8)
    ax.axhspan(-0.003, 0.003, color="0.85", zorder=0,
               label=r"$\pm0.3\%$: what a 3\% net response needs")
    ax.legend(loc="lower right", fontsize=13, framealpha=0.95)
    ax.set_title(r"$\mathrm{d}\,\mathrm{conv}[\delta]/\mathrm{d}\ln\mu_\mathrm{F}$"
                 r" against LHAPDF's own evolution", fontsize=18, pad=12)
    plot_tools.save_pdf_and_png(outdir, "derivative_truncation", fig=fig)
    output_tools.write_index_and_log(
        outdir, "derivative_truncation",
        analysis_meta_info={
            "what": "the analytic DGLAP derivative of the beam convolution, "
                    "truncated at P0 / P0+P1 / P0+P1+P2, divided by a converged "
                    "central difference of DrellYan.conv_probe and minus one",
            "why it matters": "the muF RG cancellation makes the NET transition "
                              "response ~9x smaller than the convolution half, "
                              "so this has to be right to ~0.3% for the answer "
                              "to be right to 3%",
            "reading": "the NNLO splitting kernel P2 is what takes the route "
                       "from 1-8% to 1e-4..5e-3. P2 is not FILLED at the "
                       "production fixed_order = nnlo, but its grids exist",
            "x, beam": f"x = {d['x']:.5f}, pid = {d['pid']}, side = {d['side']}",
            "source": "dconv_gate2.py",
        }, args=None)
    plt.close(fig)
    print("wrote derivative_truncation")


def fig2(d5, outdir):
    """Model error at the REAL nodes, per direction."""
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    rows = d5["partC"]
    qts = sorted({r["qt"] for r in rows})
    groups = {}
    for r in rows:
        groups.setdefault((r["qt"], round(r["D"], 6) > 0), []).append(r)
    # one figure per (qT) of the x2 = 0.35 leg, plus the two extra cases
    seen = []
    for r in rows:
        key = r["qt"]
        if key not in seen:
            seen.append(key)
    for qt in seen:
        sub = [r for r in rows if r["qt"] == qt]
        # rows come in blocks per case; split on a bT decrease
        blocks, cur = [], []
        for r in sub:
            if cur and r["bT"] < cur[-1]["bT"]:
                blocks.append(cur)
                cur = []
            cur.append(r)
        blocks.append(cur)
        for ib, blk in enumerate(blocks):
            bT = np.array([r["bT"] for r in blk])
            resp = np.array([r["true_resp"] for r in blk])
            fig, ax = plot_tools.figure(
                bT, xlabel=r"$b_\mathrm{T}$ (GeV$^{-1}$)",
                ylabel=r"model error  /  true response  (\%)",
                xlim=[bT[0], bT[-1]], ylim=[-1.7, 1.7], grid=True, logx=True,
                automatic_scale=False, width_scale=1.15)
            for key, lab, col in (
                    ("knot3real", "shipped: 3 frozen $\\mu_F$ samples", C_SHIP),
                    ("anlcorr_SC", "analytic evolution + interpolated residual",
                     C_CORR)):
                y = 100.0 * np.array([r[key] for r in blk]) / resp
                ax.plot(bT, y, color=col, lw=2.6, marker="o", ms=5, label=lab)
            ax.axhline(0.0, color="k", lw=0.8)
            ax.set_title(rf"$q_\mathrm{{T}} = {qt:g}$ GeV,  "
                         rf"$\mu_\mathrm{{F}}^{{\rm anchor}}$ "
                         rf"{blk[0]['muf_a']:.1f}$\to${blk[-1]['muf_a']:.1f} GeV",
                         fontsize=18, pad=12)
            ax.legend(loc="upper left", fontsize=13, framealpha=0.95)
            name = f"node_error_qT{qt:g}_case{ib}"
            plot_tools.save_pdf_and_png(outdir, name, fig=fig)
            output_tools.write_index_and_log(
                outdir, name,
                analysis_meta_info={
                    "what": "error on conv[c_delta] as a fraction of that "
                            "node's true muF response, per bT node",
                    "geometry": "muF anchor, the live displacement D and the "
                                "two member positions all from SCETlib's own "
                                "scale formulas, floor compensation included",
                    "alphaS": "the kernel's own fixed-nf=5 4-loop solution",
                    "source": "dconv_gate5.py part C",
                }, args=None)
            plt.close(fig)
    print("wrote node_error_*")


def fig3(d7, outdir):
    """Tier summary across flavour, beam and rapidity."""
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    keys = ["T0", "T1", "T2", "T3"]
    labs = ["shipped", "analytic, no new kinds", "+ $P_2$ only",
            "full $\\alpha_s^3$ (4 new kinds)"]
    cols = [C_SHIP, C_ANL, "#f89c20", C_T3]
    vals = {k: np.array([r[k] for r in d7]) for k in keys}
    x = np.arange(len(keys))
    fig, ax = plot_tools.figure(
        x, xlabel="", ylabel=r"error / true response  (\%)",
        xlim=[-0.6, 3.6], ylim=[0.02, 200.0], grid=True, logy=True,
        automatic_scale=False, width_scale=1.15)
    for i, k in enumerate(keys):
        v = vals[k]
        ax.plot([i] * len(v), v, ".", color=cols[i], ms=6, alpha=0.35)
        for q, mk, lw in ((50, "_", 4), (90, "_", 2.5), (100, "_", 1.6)):
            ax.plot([i - 0.28, i + 0.28], [np.percentile(v, q)] * 2,
                    color=cols[i], lw=lw)
    ax.set_xticks(x)
    ax.set_xticklabels(labs, fontsize=12)
    ax.set_title("95 diagnosable (qT, direction, $|Y|$, flavour, beam) cells;\n"
                 "bars = median, 90th percentile, worst", fontsize=16, pad=12)
    plot_tools.save_pdf_and_png(outdir, "tier_summary", fig=fig)
    output_tools.write_index_and_log(
        outdir, "tier_summary",
        analysis_meta_info={
            "what": "worst |error| over the bT ladder, as a % of the node's own "
                    "true conv[delta] response, for every tier of the analytic "
                    "evolution, over 95 cells",
            "diagnosable": "a node counts only if its own muF response exceeds "
                           "1e-3 of its convolution -- the conv-level analogue "
                           "of the sigma-level 'do not diagnose below 1e-4' rule",
            "reading": "the INTERMEDIATE tier is worse than either end: the "
                       "terms T1 omits are low-order polynomials in D that the "
                       "residual interpolation already absorbs, and adding back "
                       "only the linear one changes the residual's shape",
            "source": "dconv_gate7.py",
        }, args=None)
    plt.close(fig)
    print("wrote tier_summary")


def main():
    d = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    fig1(json.load(open(os.path.join(d, "gate2_pid2.json"))), out)
    fig2(json.load(open(os.path.join(d, "gate5.json"))), out)
    fig3(json.load(open(os.path.join(d, "gate7.json"))), out)


main()
