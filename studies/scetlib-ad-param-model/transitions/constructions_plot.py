#!/usr/bin/env python3
"""Six constructions of the convolutions' muF dependence, at the sigma level."""
import json
import os
import sys

import numpy as np

ARMS = [("shipped",  "#e42536", "-",  "o", "shipped: 3-point quadratic"),
        ("anl1",     "#5790fc", "-",  "s", "+ analytic DGLAP, mode 1"),
        ("anl3",     "#7a21dd", "--", "^", "+ analytic DGLAP, mode 3"),
        ("anl3only", "#964a8b", ":",  "v", "PURE analytic, mode 3 (no residual)"),
        ("anl1herm", "#f89c20", "-.", "D", "quartic residual, mode 1"),
        ("anl3herm", "#3f9950", "-",  "*", "quartic residual, mode 3")]
PTS = [("herm_x2_035.json", r"$x_2 = 0.35$  (FINITE, the template leg)"),
       ("herm_x2_055.json", r"$x_2 = 0.55$  (NEAR-ANCHOR, what a FIT uses)")]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    for f, lab in PTS:
        path = os.path.join(here, f)
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        b = np.asarray(d["bins"], float)
        x = 0.5 * (b[:, 4] + b[:, 5])
        R = np.asarray(d["true_resp"], float)
        ok = np.abs(R) >= 1e-4
        tag = f.replace("herm_", "").replace(".json", "")
        fig, ax = plot_tools.figure(
            x, xlabel=r"$q_\mathrm{T}$ (GeV)",
            ylabel=r"(model $-$ runcard) $/$ true response  (percent)",
            xlim=[18, 72], ylim=[-55, 55], grid=True, automatic_scale=False,
            width_scale=1.25)
        for arm, col, ls, mk, name in ARMS:
            if arm not in d["arms"]:
                continue
            y = 100.0 * np.asarray(d["arms"][arm]["dev"], float) / R
            ax.plot(x[ok], y[ok], color=col, ls=ls, lw=2.3, marker=mk, ms=7,
                    label=name)
        ax.axhline(0.0, color="k", lw=1.3)
        ax.axhspan(-5, 5, color="0.88", zorder=0, label=r"$\pm5$ percent")
        ax.legend(loc="lower right", fontsize=10, framealpha=0.95, ncol=1)
        ax.set_title(lab + r",  $|Y|<0.15$, runcard reference", fontsize=15,
                     pad=12)
        plot_tools.save_pdf_and_png(out, f"constructions_{tag}", fig=fig)
        output_tools.write_index_and_log(
            out, f"constructions_{tag}",
            analysis_meta_info={
                "what": "model/runcard - 1 divided by the bin's own true "
                        "response, for six constructions of the beam "
                        "convolutions' muF dependence. All six run in ONE "
                        "process off ONE rule build against ONE runcard "
                        "reference, so the differences are the construction and "
                        "nothing else",
                "the constructions": "shipped = a quadratic through the three "
                    "frozen muF samples; + analytic DGLAP = the same plus the "
                    "integrated DGLAP evolution as a correction that vanishes at "
                    "the members (mode 1 = the fo_lvl=2 kinds, mode 3 = the full "
                    "alphas^3 set); PURE = the analytic evolution alone, member "
                    "interpolation dropped; quartic residual = the same "
                    "correction but with the residual interpolated under "
                    "r'(0) = r''(0) = 0, which the quadratic discards",
                "why it matters": "no single construction wins everywhere. The "
                    "residual quadratic owns qT >= 28 and the quartic and pure "
                    "ones own qT [20,24], where they reach 0.0-2.0% against "
                    "-31.9% shipped. So the low-qT residual is the construction, "
                    "not a limit of the route -- and mode 3, a no-op in the "
                    "residual construction, is essential in the other two",
                "regime": lab,
                "reading": "bins below 1e-4 of sigma in true response are "
                           "dropped. Quote A/B differences, not levels: the "
                           "absolute level carries a 0.3-3.7 pp run-to-run "
                           "scatter",
                "source": f"trans_attribute.py -> {f}",
            }, args=None)
        plt.close(fig)
        print(f"wrote constructions_{tag}")


main()
