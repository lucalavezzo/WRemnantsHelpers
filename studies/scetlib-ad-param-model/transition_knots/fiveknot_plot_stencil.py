#!/usr/bin/env python3
"""WHY FIVE KNOTS DOES NOT FIX THE TEMPLATE VARIATION -- the mechanism picture.

Same construction as plot_stencil.py, with the extra knots drawn. For each qT
bin it shows the per-node displacement

    D(bT) = ln[ muF(live transition points) / muF(anchor) ]

against the muF member positions the model interpolates through:

    outer pair   kappa_F = 1/2, 2          (both stencils)
    narrow inner kappa_F = 1/sqrt2, sqrt2  (the five-knot proposal)
    wide extra   kappa_F = 1/4, 4          (the alternative geometry)

The member positions are NOT +-ln f per node: Vary.muf scales muF by f AND
divides the muf_min floor by f, so their own separation collapses at large bT.
A curve INSIDE the inner knots is a place where extra interior knots help; a
curve OUTSIDE the outer pair is a place where the model is EXTRAPOLATING, and
a quartic extrapolates worse than a quadratic. Read the qT dependence: at the
template's own variation size the curve leaves the outer band over qT ~ 26-44,
which is exactly where the five-knot arm degrades.

Arithmetic from SCETlib's own scale formulas only. No calculation is run.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fiveknot_stencil_geometry import X1A, X2A, X3A, Q, muf  # noqa: E402

CASES = [(r"$x_2 = 0.35$  (template leg)", 0.2, 0.35, 1.0, "#e42536", "solid"),
         (r"$x_2 = 0.75$  (template leg)", 0.2, 0.75, 1.0, "#f89c20", "solid"),
         (r"$x_1,x_3 = 0.3,\,0.9$  (template)", 0.3, 0.6, 0.9, "#964a8b",
          "dashed"),
         (r"$x_2 = 0.55$  (near-anchor, what a FIT uses)", 0.2, 0.55, 1.0,
          "#5790fc", "dotted")]


def main(outdir):
    import matplotlib.pyplot as plt

    from wums import output_tools, plot_tools

    os.makedirs(outdir, exist_ok=True)
    bT = np.geomspace(0.05, 5.0, 400)
    for qt, lo, hi in ((19.0, 18, 20), (22.0, 20, 24), (26.0, 24, 28),
                       (30.5, 28, 33), (38.5, 33, 44), (60.0, 44, 100)):
        x = qt / Q
        fig, ax = plot_tools.figure(
            bT, xlabel=r"$b_\mathrm{T}$ (GeV$^{-1}$)",
            ylabel=r"$\Delta\ln\mu_\mathrm{F}$  (per node)",
            xlim=[bT[0], bT[-1]], ylim=[-1.5, 1.5], grid=True,
            logx=True, automatic_scale=False, width_scale=1.15)
        a = np.array([muf(b, x, X1A, X2A, X3A, 1.0) for b in bT])

        def pos(ratio):
            return np.array([np.log(muf(b, x, X1A, X2A, X3A, ratio)
                                    / muf(b, x, X1A, X2A, X3A, 1.0))
                             for b in bT])

        up4, dn4 = pos(4.0), pos(0.25)
        up2, dn2 = pos(2.0), pos(0.5)
        upS, dnS = pos(2.0 ** 0.5), pos(2.0 ** -0.5)
        ax.fill_between(bT, dn4, up4, color="0.88", lw=0, zorder=0,
                        label=r"WIDE extra knots  $\kappa_F=1/4,\,4$")
        ax.fill_between(bT, dn2, up2, color="0.70", lw=0, zorder=0,
                        label=r"outer knots  $\kappa_F=1/2,\,2$  (both stencils)")
        ax.fill_between(bT, dnS, upS, color="0.50", lw=0, zorder=0,
                        label=r"NARROW inner knots  $\kappa_F=1/\sqrt{2},\,\sqrt{2}$")
        for title, l1, l2, l3, col, ls in CASES:
            v = np.array([muf(b, x, l1, l2, l3, 1.0) for b in bT])
            ax.plot(bT, np.log(v / a), color=col, lw=2.4, ls=ls, label=title)
        ax.axhline(0.0, color="k", lw=0.8)
        ax.set_title(rf"$q_\mathrm{{T}} \in [{lo},{hi}]$ GeV  "
                     rf"(centre {qt:g} GeV),  $Q = m_Z$", fontsize=19, pad=12)
        ax.legend(loc="lower left", fontsize=12, ncol=2, framealpha=0.92)
        name = f"stencil5_qT_{lo}_{hi}"
        plot_tools.save_pdf_and_png(outdir, name, fig=fig)
        output_tools.write_index_and_log(
            outdir, name,
            analysis_meta_info={
                "what": "per-node ln(muF) displacement induced by a transition-"
                        "point change, against the muF member knots",
                "shaded bands": "the members' OWN per-node positions; they "
                                "collapse at large bT because Vary.muf "
                                "compensates the muf_min floor",
                "curve inside the darkest band": "extra INTERIOR knots can help",
                "curve outside the mid band": "the model EXTRAPOLATES; a "
                                              "quartic extrapolates worse than "
                                              "a quadratic",
                "qT bin": f"[{lo}, {hi}] GeV, evaluated at the centre {qt} GeV",
                "source": "SCETlib scales_formulas.hpp / Scale_provider.cpp, "
                          "arithmetic only -- no calculation is run",
            }, args=None)
        plt.close(fig)
        print(f"wrote {outdir}/{name}.png")


if __name__ == "__main__":
    main(sys.argv[1])
