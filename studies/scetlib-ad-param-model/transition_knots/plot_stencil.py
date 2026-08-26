#!/usr/bin/env python3
"""THE MECHANISM PICTURE: where the transition-induced muF shift sits relative
to the two muF members the model interpolates through. One figure per qT bin,
because BOTH the shift and the stencil depend on qT.

The autodiff model carries the beam convolutions' muF dependence as THREE
samples -- kappa_F = 1/f, 1, f -- and puts a quadratic through them. A
transition-point change moves muF per bT node by D_trans(bT); the model reads
its answer off that quadratic at D_trans.

The member positions are NOT +-ln f per node: Vary.muf scales muF by f AND
divides the scale floor by f (Scale_provider), so the members' own separation
collapses toward zero at large bT where that floor dominates -- while D_trans
GROWS with bT. Where a curve leaves the band the model is EXTRAPOLATING its
quadratic, and no knot spacing repairs that: a tighter band extrapolates
further, a wider one costs h^2 at small bT.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stencil_geometry import X1A, X2A, X3A, Q, muf  # noqa: E402

CASES = [(r"$x_2 = 0.35$  (template leg)", 0.2, 0.35, 1.0, "#e42536", "solid"),
         (r"$x_2 = 0.75$  (template leg)", 0.2, 0.75, 1.0, "#f89c20", "solid"),
         (r"$x_1,x_3 = 0.3,\,0.9$  (template)", 0.3, 0.6, 0.9, "#964a8b",
          "dashed"),
         (r"$x_2 = 0.55$  (near-anchor probe)", 0.2, 0.55, 1.0, "#5790fc",
          "dotted")]


def main(outdir):
    import matplotlib.pyplot as plt

    from wums import output_tools, plot_tools

    os.makedirs(outdir, exist_ok=True)
    bT = np.geomspace(0.05, 5.0, 400)
    for qt, lo, hi in ((19.0, 18, 20), (22.0, 20, 24), (26.0, 24, 28),
                       (30.5, 28, 33), (38.5, 33, 44)):
        x = qt / Q
        fig, ax = plot_tools.figure(
            bT, xlabel=r"$b_\mathrm{T}$ (GeV$^{-1}$)",
            ylabel=r"$\Delta\ln\mu_\mathrm{F}$  (per node)",
            xlim=[bT[0], bT[-1]], ylim=[-0.95, 0.95], grid=True,
            logx=True, automatic_scale=False, width_scale=1.15)
        a = np.array([muf(b, x, X1A, X2A, X3A, 0, 2.0) for b in bT])
        for f, col, lab in ((2.0, "0.75", r"member stencil, $f=2$"),
                            (np.sqrt(2.0), "0.45",
                             r"member stencil, $f=\sqrt{2}$")):
            up = np.array([np.log(muf(b, x, X1A, X2A, X3A, +1, f)
                                  / muf(b, x, X1A, X2A, X3A, 0, f))
                           for b in bT])
            dn = np.array([np.log(muf(b, x, X1A, X2A, X3A, -1, f)
                                  / muf(b, x, X1A, X2A, X3A, 0, f))
                           for b in bT])
            ax.fill_between(bT, dn, up, color=col, alpha=0.45, lw=0, label=lab,
                            zorder=0)
        for title, l1, l2, l3, col, ls in CASES:
            v = np.array([muf(b, x, l1, l2, l3, 0, 2.0) for b in bT])
            ax.plot(bT, np.log(v / a), color=col, lw=2.4, ls=ls, label=title)
        ax.axhline(0.0, color="k", lw=0.8)
        ax.set_title(rf"$q_\mathrm{{T}} \in [{lo},{hi}]$ GeV  "
                     rf"(centre {qt:g} GeV),  $Q = m_Z$", fontsize=19, pad=12)
        ax.legend(loc="lower left", fontsize=14, ncol=2, framealpha=0.92)
        name = f"stencil_qT_{lo}_{hi}"
        plot_tools.save_pdf_and_png(outdir, name, fig=fig)
        output_tools.write_index_and_log(
            outdir, name,
            analysis_meta_info={
                "what": "per-node ln(muF) displacement induced by a transition"
                        " point change, against the muF member stencil",
                "shaded bands": "the two muF members' OWN per-node positions. "
                                "They collapse at large bT because Vary.muf "
                                "compensates the muf_min floor.",
                "curve outside the band": "the model EXTRAPOLATES its 3-point "
                                          "quadratic there",
                "qT bin": f"[{lo}, {hi}] GeV, evaluated at the centre {qt} GeV",
                "source": "SCETlib scales_formulas.hpp / Scale_provider.cpp, "
                          "arithmetic only -- no calculation is run",
            }, args=None)
        plt.close(fig)
        print(f"wrote {outdir}/{name}.png")


if __name__ == "__main__":
    main(sys.argv[1])
