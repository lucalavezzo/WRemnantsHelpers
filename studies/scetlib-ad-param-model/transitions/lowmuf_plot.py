#!/usr/bin/env python3
"""How well fixed-order DGLAP tracks the beam grid's OWN muF evolution, down to
the muf_min floor. Reads gate2_lowmuf.json; runs no calculation."""
import json
import os
import sys

import numpy as np

C_P0 = "#e42536"
C_P1 = "#f89c20"
C_P2 = "#3f9950"
C_TERM = "#5790fc"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    d = json.load(open(os.path.join(here, "gate2_lowmuf.json")))
    a = d["partA"]
    mu = np.array([r["muf"] for r in a])
    fd = np.array([r["fd"] for r in a])
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    fig, ax = plot_tools.figure(
        mu, xlabel=r"$\mu_\mathrm{F}$ (GeV)",
        ylabel=r"analytic $/$ grid's own $\mathrm{d}/\mathrm{d}\ln\mu_F - 1$",
        xlim=[1.3, 100.0], ylim=[-0.60, 0.05], grid=True, logx=True,
        automatic_scale=False, width_scale=1.15)
    for key, lab, col in (
            ("p0", r"$2gP_0$ only (LO splitting)", C_P0),
            ("p0p1", r"$+\,2g^2P_1$ (NLO)", C_P1),
            ("p0p1p2", r"$+\,2g^3P_2$ (NNLO) -- what the route uses", C_P2)):
        ax.plot(mu, np.array([r[key] for r in a]) / fd - 1.0, color=col, lw=2.6,
                marker="o", ms=5, label=lab)
    ax.plot(mu, -np.abs(np.array([r["p0p1p2"] for r in a])
                        - np.array([r["p0p1"] for r in a])) / fd,
            color=C_TERM, lw=2.0, ls="--", marker="s", ms=4,
            label=r"$-|$the $P_2$ term itself$|\,/$ the derivative")
    ax.axhline(0.0, color="k", lw=0.9)
    ax.axhspan(-0.003, 0.003, color="0.86", zorder=0,
               label=r"$\pm0.3\%$: what a 3 percent net response needs")
    ax.axvline(1.40, color="0.3", lw=1.6, ls=":")
    ax.text(1.44, -0.56, r"$\mu_F^{\min}=1.40$ GeV" "\n" r"(the profile's floor)",
            fontsize=11, color="0.2")
    ax.legend(loc="lower right", fontsize=11, framealpha=0.95)
    ax.set_title(r"Fixed-order DGLAP against the beam grid's own $\mu_F$"
                 r" evolution, down to the floor", fontsize=16, pad=12)
    plot_tools.save_pdf_and_png(out, "dglap_to_the_floor", fig=fig)
    output_tools.write_index_and_log(
        out, "dglap_to_the_floor",
        analysis_meta_info={
            "what": "the analytic derivative 2gP0 + 2g^2P1 + 2g^3P2 of "
                    "conv[delta], divided by a converged central difference of "
                    "DrellYan.conv_probe -- the SAME interpolant SCETlib itself "
                    "uses -- and minus one, extended from the previous round's "
                    "lowest point (2 GeV) down to the muf_min floor of 1.40 GeV",
            "why it matters": "the profile pins muF at that floor at large bT, "
                              "which is exactly where the transition response of "
                              "the qT 18-24 bins comes from. The NNLO-truncated "
                              "series is 0.5% off at 1.9 GeV and 1.0-2.9% off at "
                              "1.4-1.5 GeV, and the P2 term is 8-12% of the "
                              "whole derivative there -- i.e. the splitting "
                              "series is NOT converged at alphaS = 0.36",
            "reading": "above muF ~ 8 GeV the truncation is 1e-4, which is why "
                       "the route closes qT >= 24. Adding MORE splitting orders "
                       "is not the fix: mode 3 measured flat at the sigma level",
            "source": "gate2_lowmuf.py (dconv_gate2.py with the muF list "
                      "extended downward)",
        }, args=None)
    plt.close(fig)
    print("wrote dglap_to_the_floor")


main()
