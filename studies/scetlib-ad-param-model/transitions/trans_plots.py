#!/usr/bin/env python3
"""Figures for the transition-point round. Reads the attribution JSONs; runs
no calculation."""
import json
import os
import sys

import numpy as np

C_SHIP = "#e42536"
C_ANL = "#5790fc"
C_I1 = "#3f9950"
C_LF = "#964a8b"
C_CONV = "#f89c20"
C_NOMUF = "#7a21dd"

PTS = [("attr_x2_035.json", r"$x_2 = 0.35$  (template leg)"),
       ("attr_x2_075.json", r"$x_2 = 0.75$  (template leg)"),
       ("attr_x2_055.json", r"$x_2 = 0.55$  (near-anchor, what a FIT uses)"),
       ("attr_x1x3.json", r"$x_1,x_3 = 0.3,\,0.9$")]
USABLE = 1e-4


def _centres(d):
    b = np.asarray(d["bins"], float)
    return 0.5 * (b[:, 4] + b[:, 5]), b


def fig_cancellation(here, outdir):
    """The two halves of the muF cancellation, as multiples of the net."""
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    d = json.load(open(os.path.join(here, "attr_x2_035.json")))
    x, b = _centres(d)
    R = np.asarray(d["true_resp"], float)
    sh = np.asarray(d["arms"]["shipped"]["resp"], float)
    lf = (sh - np.asarray(d["arms"]["noLf"]["resp"], float)) / R
    cv = (sh - np.asarray(d["arms"]["noconv"]["resp"], float)) / R
    net = (sh - np.asarray(d["arms"]["nomuf"]["resp"], float)) / R
    fig, ax = plot_tools.figure(
        x, xlabel=r"$q_\mathrm{T}$ (GeV)",
        ylabel=r"contribution $/$ net true response",
        xlim=[17, 46], ylim=[-12.5, 12.5], grid=True, automatic_scale=False,
        width_scale=1.15)
    w = 1.7
    ax.bar(x - w, lf, width=1.7 * w, color=C_LF, alpha=0.85,
           label=r"analytic half: explicit $\ln(\mu_B/\mu_F)$ in the beam"
                 r" coefficients")
    ax.bar(x + w, cv, width=1.7 * w, color=C_CONV, alpha=0.85,
           label=r"numerical half: the PDF's evolution to $\mu_F$"
                 r" (frozen convolutions)")
    ax.plot(x, net, color="k", lw=2.6, marker="o", ms=7,
            label=r"NET $\mu_F$ sector (what survives)")
    ax.axhline(0.0, color="k", lw=0.8)
    ax.axhline(1.0, color="0.4", lw=1.0, ls=":")
    for xi, li in zip(x, lf):
        ax.text(xi, -12.0, f"{abs(li):.1f}$\\times$", ha="center", fontsize=11,
                color=C_LF)
    ax.legend(loc="upper center", fontsize=12, framealpha=0.95, ncol=1)
    ax.set_title(r"The $\mu_F$ RG cancellation at the $\sigma$ level, "
                 r"$x_2=0.35$, $|Y|<0.15$", fontsize=17, pad=12)
    plot_tools.save_pdf_and_png(outdir, "muf_cancellation", fig=fig)
    output_tools.write_index_and_log(
        outdir, "muf_cancellation",
        analysis_meta_info={
            "what": "the transition response of each half of the muF sector, "
                    "divided by the NET true response of the same bin. Halves "
                    "isolated with DrellYan.set_muf_ablate: bit 16 freezes the "
                    "explicit ln(muB/muF) at the anchor transition points, bit "
                    "1 drops the member interpolation of the convolutions",
            "why it matters": "the two halves are +-(5.8 .. 10.0) x the net and "
                              "cancel, so a 1% error in either is a 6-10% error "
                              "in the answer. The kernel does the first half "
                              "analytically and the second numerically, which "
                              "is why the second has to be made analytic too",
            "reading": "the halves are NOT additive -- their sum is not the net "
                       "-- because the beam function is nonlinear in both; the "
                       "NET curve is the 1|16 ablation, which IS exact",
            "regime": "FINITE variation, x2 = 0.35 (what the templates carry)",
            "source": "trans_attribute.py -> attr_x2_035.json",
        }, args=None)
    plt.close(fig)
    print("wrote muf_cancellation")


def fig_sector_accuracy(here, outdir):
    """The muF-sector transition response itself, model against truth."""
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    for f, lab in PTS:
        d = json.load(open(os.path.join(here, f)))
        x, _ = _centres(d)
        R = np.asarray(d["true_resp"], float)
        nm = np.asarray(d["arms"]["nomuf"]["resp"], float)
        ok = np.abs(R) >= USABLE
        tag = f.replace("attr_", "").replace(".json", "")
        sgn = np.sign(R[ok][-1]) or 1.0
        fig, ax = plot_tools.figure(
            x, xlabel=r"$q_\mathrm{T}$ (GeV)",
            ylabel=r"$\mu_F$-sector transition response  ($\times\,\sigma$)",
            xlim=[17, 46], grid=True, automatic_scale=False, width_scale=1.15)
        ax.plot(x[ok], sgn * (R - nm)[ok], color="k", lw=2.8, marker="o", ms=7,
                label=r"TRUE (runcard $-$ frozen-$\mu_F$ model)")
        for arm, col, name in (
                ("shipped", C_SHIP, "shipped: member interpolation"),
                ("anl1", C_ANL, "analytic DGLAP evolution, mode 1")):
            y = np.asarray(d["arms"][arm]["resp"], float) - nm
            ax.plot(x[ok], sgn * y[ok], color=col, lw=2.3, marker="s", ms=6,
                    label=name)
        ax.axhline(0.0, color="0.5", lw=0.8)
        ax.set_yscale("symlog", linthresh=1e-4)
        ax.axvspan(17, 24, color="0.9", zorder=0)
        ax.text(20.5, 0.0, "the route does\nNOT fix these", ha="center",
                va="bottom", fontsize=11, color="0.25")
        ax.legend(loc="upper left", fontsize=11, framealpha=0.95)
        ax.set_title(r"$\mu_F$-sector response, " + lab, fontsize=16, pad=12)
        plot_tools.save_pdf_and_png(outdir, f"sector_{tag}", fig=fig)
        output_tools.write_index_and_log(
            outdir, f"sector_{tag}",
            analysis_meta_info={
                "what": "the transition response carried by the muF sector "
                        "alone, as a fraction of sigma: arm minus the 1|16 "
                        "ablation, which freezes the whole muF sector at the "
                        "anchor transition points. TRUE = runcard minus the "
                        "same ablation, which assumes the response through "
                        "muB, muS and nuS (all analytic in the kernel) is exact",
                "why it matters": "at qT >= 24 the analytic evolution brings "
                                  "this onto the truth; at qT <= 24 the model's "
                                  "sector is near zero while the truth is not, "
                                  "and that is the whole residual",
                "sign": "multiplied by the sign of the highest-qT true response "
                        "so the curves read upward; symlog below 1e-4",
                "regime": lab,
                "source": f"trans_attribute.py -> {f}",
            }, args=None)
        plt.close(fig)
        print(f"wrote sector_{tag}")


def fig_dev(here, outdir):
    """dev as % of the true response, shipped vs mode 1, one panel per point."""
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    for f, lab in PTS:
        d = json.load(open(os.path.join(here, f)))
        x, b = _centres(d)
        R = np.asarray(d["true_resp"], float)
        ok = np.abs(R) >= USABLE
        tag = f.replace("attr_", "").replace(".json", "")
        fig, ax = plot_tools.figure(
            x, xlabel=r"$q_\mathrm{T}$ (GeV)",
            ylabel=r"(model $-$ runcard) $/$ true response  (percent)",
            xlim=[17, 46], ylim=[-60, 60], grid=True, automatic_scale=False,
            width_scale=1.15)
        for arm, col, name in (("shipped", C_SHIP, "shipped model"),
                               ("anl1", C_ANL, "analytic DGLAP, mode 1"),
                               ("nomuf", C_NOMUF,
                                r"$\mu_F$ sector frozen (reference point)")):
            if arm not in d["arms"]:
                continue
            y = 100.0 * np.asarray(d["arms"][arm]["dev"], float) / R
            ax.plot(x[ok], y[ok], color=col, lw=2.4, marker="o", ms=6,
                    label=name)
        ax.axhline(0.0, color="k", lw=1.2)
        ax.axhspan(-5, 5, color="0.87", zorder=0, label=r"$\pm5\%$")
        ax.legend(loc="lower right", fontsize=11, framealpha=0.95)
        ax.set_title(lab + r",  $|Y|<0.15$, runcard reference", fontsize=16,
                     pad=12)
        plot_tools.save_pdf_and_png(outdir, f"dev_{tag}", fig=fig)
        output_tools.write_index_and_log(
            outdir, f"dev_{tag}",
            analysis_meta_info={
                "what": "model/runcard - 1, divided by the bin's own true "
                        "response, for the shipped model and for the analytic "
                        "DGLAP evolution (mode 1). The third curve freezes the "
                        "whole muF sector, so the gap between it and zero is "
                        "the response the muF sector has to supply",
                "regime": lab,
                "reading": "bins below 1e-4 of sigma in true response are "
                           "dropped. Quote A/B DIFFERENCES: the absolute level "
                           "carries a 0.3-3.7 pp run-to-run scatter between two "
                           "independent adaptive integrations, while the "
                           "shipped -> mode 1 difference reproduces to 0.1 pp",
                "source": f"trans_attribute.py -> {f}",
            }, args=None)
        plt.close(fig)
        print(f"wrote dev_{tag}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    fig_cancellation(here, out)
    fig_sector_accuracy(here, out)
    fig_dev(here, out)


main()
