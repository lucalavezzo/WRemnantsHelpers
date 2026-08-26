#!/usr/bin/env python3
"""Figures for the safe-interpolant round. Reads the JSONs; runs no calculation.

  mech_pred_vs_meas   the quartic's node error, predicted from (A1-1) e1 D +
                      (A2-1) e2 D^2/2 against measured, mode 1 and mode 3.
                      THE mechanism figure.
  e1_truncation       e1, the analytic model's own LINEAR truncation error, vs
                      the node's muF, at mode 1 and mode 3. THE figure for why
                      no r'(0) = 0 form can work at mode 1.
  A1_geometry         A1 and A2 from the stencil geometry alone, per leg.
  form_node_errors    max and rms node error per candidate form per leg, mode 1
                      against mode 3. THE "nothing beats the quadratic" figure.
"""
import json
import math
import os
import sys

import numpy as np

C_M1 = "#e42536"
C_M3 = "#5790fc"
C_QUAD = "#3f9950"
C_LEG = {"x1x3": "#e42536", "x2_035": "#5790fc", "x2_055": "#f89c20",
         "x2_075": "#7a21dd"}
LEGLAB = {"x1x3": r"$x_1,x_3 = 0.3,\,0.9$", "x2_035": r"$x_2 = 0.35$",
          "x2_055": r"$x_2 = 0.55$", "x2_075": r"$x_2 = 0.75$"}


def _meta(what, how, caveat):
    return {"what": what, "how": how, "caveat": caveat}


def fig_pred_vs_meas(here, out):
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    rows = json.load(open(os.path.join(here, "mech.json")))
    fig, ax = plot_tools.figure(
        np.array([-0.6, 0.6]),
        xlabel=r"predicted  $(A_1\!-\!1)\,e_1 D + (A_2\!-\!1)\,e_2 D^2/2$",
        ylabel=r"measured quartic node error  $/\;R$",
        xlim=[-0.3, 0.6], ylim=[-0.3, 0.6], grid=True, automatic_scale=False)
    ax.plot([-1, 1], [-1, 1], color="k", lw=1, ls="--", zorder=1)
    for mode, col, mk, lab in (("m1", C_M1, "o", "mode 1 (P0, P1)"),
                               ("m3", C_M3, "s", r"mode 3 (+ P2, $\alpha_s^3$)")):
        sub = [r for r in rows if r["mode"] == mode]
        ax.scatter([r["pred"] / r["R"] for r in sub],
                   [r["meas_quart"] / r["R"] for r in sub],
                   s=26, marker=mk, facecolor="none", edgecolor=col,
                   linewidth=1.3, label=lab, zorder=3)
    sub = [r for r in rows if r["mode"] == "m1"]
    ax.scatter([0.0] * len(sub), [r["meas_quad"] / r["R"] for r in sub],
               s=14, marker="x", color=C_QUAD, linewidth=1.1, zorder=4,
               label="quadratic (predicted 0)")
    ax.legend(loc="upper left", fontsize=13, frameon=False)
    plot_tools.save_pdf_and_png(out, "mech_pred_vs_meas", fig=fig)
    output_tools.write_index_and_log(out, "mech_pred_vs_meas",
        analysis_meta_info={"safeint": _meta(
            "the quartic residual form's per-node error against the closed-form "
            "prediction (A1-1) e1 D + (A2-1) e2 D^2/2, where A1 and A2 are pure "
            "stencil geometry and e1, e2 are the analytic model's own truncation "
            "error fitted from r(t) on |t| <= 0.02",
            "mechanism_check.py: r measured with DrellYan.conv_probe, delta "
            "replicated term for term from muf_evo_coeffs; nodes at qT 19..30, "
            "bT 0.8..8, three legs, modes 1 and 3",
            "conv[c_delta] only, pid 2 side 0, x = 0.00756. Node-level errors do "
            "NOT map linearly to sigma: the previous round measured a 5x-50x "
            "under-prediction through the bT integral.")})
    plt.close(fig)


def fig_e1(here, out):
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    rows = json.load(open(os.path.join(here, "mech.json")))
    mu = np.array(sorted({r["mf0"] for r in rows}))
    fig, ax = plot_tools.figure(
        mu, xlabel=r"node $\mu_F$ (GeV)",
        ylabel=r"$e_1$ / (node response slope)",
        xlim=[1.2, 7.5], ylim=[-0.02, 0.17], grid=True, automatic_scale=False)
    for mode, col, mk, lab in (("m1", C_M1, "o", "mode 1 (P0, P1)"),
                               ("m3", C_M3, "s", r"mode 3 (+ P2, $\alpha_s^3$)")):
        sub = sorted([r for r in rows if r["mode"] == mode],
                     key=lambda r: r["mf0"])
        ax.plot([r["mf0"] for r in sub],
                [r["e1"] / (r["R"] / r["D"]) for r in sub],
                marker=mk, ms=4.5, lw=0, color=col, label=lab)
    ax.axvline(1.40, color="k", lw=1, ls=":")
    ax.text(1.44, 0.15, r"$\mu_F^{\rm min} = 1.40$", fontsize=12)
    ax.axhline(0.0, color="k", lw=0.8)
    ax.legend(loc="upper right", fontsize=13, frameon=False)
    plot_tools.save_pdf_and_png(out, "e1_truncation", fig=fig)
    output_tools.write_index_and_log(out, "e1_truncation",
        analysis_meta_info={"safeint": _meta(
            "e1 = r'(0), the analytic muF evolution's own LINEAR truncation "
            "error, as a fraction of the node's mean response slope R/D. The "
            "premise of every r'(0) = 0 form is that this vanishes; at mode 1 "
            "it reaches 13.8% at the muf_min floor, and mode 3 divides it by "
            "7-20x.",
            "mechanism_check.py, least-squares fit of r(t) = e1 t + e2 t^2/2 + "
            "C t^3 on |t| <= 0.02, both signs, per node",
            "one flavour/side; the muF axis is the node's own anchor muF, so the "
            "leftmost points are the large-bT nodes the profile has pinned at "
            "the floor.")})
    plt.close(fig)


def fig_form_errors(here, out):
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    NAMES = ["quad", "cubic", "quart", "bq0.3", "bq1", "bc0.3", "bc1",
             "clip1", "clip2", "oneside"]
    d1 = {}
    for f in ("rf_x1x3.json", "rf_x2.json"):
        j = json.load(open(os.path.join(here, f)))
        for r in j["rows"]:
            d1.setdefault(r["leg"], []).append(r)
    d3 = {}
    for r in json.load(open(os.path.join(here, "rf_m3.json")))["rows"]:
        d3.setdefault(r["leg"], []).append(r)
    legs = ["x1x3", "x2_035", "x2_055"]
    xs = np.arange(len(NAMES), dtype=float)
    fig, ax = plot_tools.figure(
        xs, xlabel="", ylabel=r"max $|$node error$|\;/\;R$",
        xlim=[-0.6, len(NAMES) - 0.4], ylim=[0.0, 0.58], grid=True,
        automatic_scale=False, width_scale=1.5)
    w = 0.28
    for i, leg in enumerate(legs):
        for j, (mode, dd, hatch, alpha) in enumerate(
                (("mode 1", d1, "", 0.95), ("mode 3", d3, "////", 0.0))):
            v = [max(abs(r[f"err_{n}"]) for r in dd[leg]) for n in NAMES]
            ax.bar(xs + (i - 1) * w + (j - 0.5) * 0.5 * w, v, width=0.5 * w,
                   color=C_LEG[leg], alpha=(alpha if j == 0 else 1.0),
                   hatch=hatch, fill=(j == 0),
                   edgecolor=C_LEG[leg], lw=0.9,
                   label=f"{LEGLAB[leg]}, {mode}", zorder=2)
    ax.set_xticks(xs)
    ax.set_xticklabels(NAMES, rotation=35, ha="right", fontsize=12)
    ax.legend(loc="upper left", fontsize=10, frameon=False, ncol=2)
    plot_tools.save_pdf_and_png(out, "form_node_errors", fig=fig)
    output_tools.write_index_and_log(out, "form_node_errors",
        analysis_meta_info={"safeint": _meta(
            "max over (qT, bT) of each candidate residual form's node error as "
            "a fraction of the node's own true response. The quadratic (the "
            "shipped form) is the smallest on EVERY leg at mode 1; at mode 3 "
            "every form collapses into the same band.",
            "residual_forms.py, r measured with conv_probe, delta replicated "
            "from muf_evo_coeffs; qT 19..70, bT 0.1..8",
            "a max over nodes is a single-node statistic, and node-level error "
            "does not map linearly to sigma (5x-50x under-prediction through "
            "the bT integral).")})
    plt.close(fig)


def fig_A1(here, out):
    import matplotlib.pyplot as plt
    from wums import output_tools, plot_tools
    sys.path.insert(0, here)
    from form_conditioning import LEGS_DEF, amps, geom  # noqa
    bTs = np.geomspace(0.05, 8.0, 60)
    fig, ax = plot_tools.figure(
        bTs, xlabel=r"$b_\mathrm{T}$ (GeV$^{-1}$)",
        ylabel=r"$A_1$ (quartic's amplification of $e_1$)",
        xlim=[0.05, 8.0], ylim=[0.0, 9.0], grid=True, automatic_scale=False)
    ax.set_xscale("log")
    for leg, (x1L, x2L, x3L) in LEGS_DEF.items():
        for qt, ls in ((22.0, "-"), (26.0, "--")):
            v = []
            for bT in bTs:
                d, a, b, _ = geom(qt, bT, x1L, x2L, x3L, 2.0)
                v.append(abs(amps(d, a, b)[1]))
            ax.plot(bTs, v, ls=ls, color=C_LEG[leg], lw=1.6,
                    label=f"{LEGLAB[leg]}, $q_T$ = {qt:g}")
    ax.axhline(1.0, color="k", lw=0.9, ls=":")
    ax.legend(loc="upper left", fontsize=10, frameon=False, ncol=2)
    plot_tools.save_pdf_and_png(out, "A1_geometry", fig=fig)
    output_tools.write_index_and_log(out, "A1_geometry",
        analysis_meta_info={"safeint": _meta(
            "A1 = D^2/(b-a) [(b-D)/a^2 + (D-a)/b^2], the factor by which the "
            "quartic residual form renders the linear part of r. It is PURE "
            "stencil geometry -- no SCETlib, no PDF -- and it reaches 8 on the "
            "x1,x3 leg at the large-bT nodes where Vary.muf's floor "
            "compensation has collapsed the member stencil.",
            "form_conditioning.py: SCETlib's own mu_star / f_run / g_run at "
            "muf_min = 1.40, collins_soper4 form, slope profile, f = 2",
            "the quadratic form has A1 = 1 identically, which is why it does "
            "not amplify e1 at all.")})
    plt.close(fig)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    fig_pred_vs_meas(here, out)
    fig_e1(here, out)
    fig_form_errors(here, out)
    fig_A1(here, out)
    print(f"wrote figures to {out}")


if __name__ == "__main__":
    main()
