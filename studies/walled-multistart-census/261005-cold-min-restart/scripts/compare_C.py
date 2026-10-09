#!/usr/bin/env python3
"""CMR1B (stiff-wall minimum seeded at C, new cache) vs the soft-wall C (CCWALLCOLDR, old cache) vs XWSTIFF.

(1) Distances in the CMR1B's OWN postfit sigma (not XWSTIFF's: XWSTIFF's lambda4 is wall-pinned, so its walled sigma
    is meaningless and inflates every distance by ~400x). Also in C's own sigma. Blinded: alphaS only as differences.
(2) The CS kernel gamma_nu^NP(b) = -lambda_inf_nu * tanh(P(b^2)/lambda_inf_nu), P(u) = l2nu*u + l4nu*u^2 (tanh_2; formula
    from np_damping_wall.py's docstring = SCETlib Gamma_nu, the same form 260930-np-forms validated against btgrid_tf).
    b_bar = b_T here (b0_over_bmax_global = 0). Reports where gamma_nu turns positive and its size at selected b.
usage (container): compare_C.py [--plot]
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from analyze_restart import load_fit, physical  # noqa: E402
from wremnants.postprocessing.scetlib_ad import np_damping_wall as W  # noqa: E402
from wremnants.postprocessing.scetlib_ad import response as R  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
FITS = {
    "CMR1B": f"{A}/261005_cold_min_restart/fitresults_CMR1B.hdf5",
    "C (CCWALLCOLDR)": f"{A}/260917_cc_fits_wall/fitresults_CCWALLCOLDR.hdf5",
    "XWSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
}
BS = [0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 12.6]


def gnu(b, l2nu, l4nu, linf=2.0):
    u = b * b
    return -linf * np.tanh((l2nu * u + l4nu * u * u) / linf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot", action="store_true")
    args = ap.parse_args()
    F = {k: load_fit(p) for k, p in FITS.items()}
    names = F["CMR1B"]["names"]
    for k, f in F.items():
        assert f["names"] == names, k
    cfg = R.corr_config_from_meta(F["CMR1B"]["meta"])["config"]
    npm, npmn = W.forms_from_corr_config(cfg)
    lam_names = tuple(dict.fromkeys(W._TMD_LAMBDAS[npm] + W._CS_LAMBDAS[npmn]))
    ia = names.index("alphaS")
    out = {"pairs": {}, "lambdas": {}, "gamma_nu": {}}
    for k, f in F.items():
        out["lambdas"][k] = {
            n: float(v) for n, v in physical(f, cfg, lam_names)[0].items()
        }
    for a, b, sref in [
        ("C (CCWALLCOLDR)", "CMR1B", "CMR1B"),
        ("C (CCWALLCOLDR)", "CMR1B", "C (CCWALLCOLDR)"),
        ("XWSTIFF", "CMR1B", "CMR1B"),
    ]:
        d = (F[b]["x"] - F[a]["x"]) / F[sref]["sig"]
        o = np.argsort(-np.abs(d))
        key = f"{b} - {a} [sigma_{sref}]"
        out["pairs"][key] = dict(
            dalphaS=float(d[ia]),
            norm=float(np.linalg.norm(d)),
            top10=[(names[i], float(d[i])) for i in o[:10]],
            n_gt_1sig=int(np.sum(np.abs(d) > 1)),
        )
        print(
            f"{key}: dalphaS {d[ia]:+.4f}  ||d|| {np.linalg.norm(d):.3f}  n(|d|>1) {np.sum(np.abs(d) > 1)}"
        )
        print("    top10:", ", ".join(f"{names[i]} {d[i]:+.3g}" for i in o[:10]))
    print(
        "sigma_alphaS ratios: CMR1B/XW %.4f  C/XW %.4f  CMR1B/C %.4f"
        % (
            F["CMR1B"]["sig"][ia] / F["XWSTIFF"]["sig"][ia],
            F["C (CCWALLCOLDR)"]["sig"][ia] / F["XWSTIFF"]["sig"][ia],
            F["CMR1B"]["sig"][ia] / F["C (CCWALLCOLDR)"]["sig"][ia],
        )
    )
    out["sig_alphaS_ratio"] = {
        "CMR1B/XWSTIFF": float(F["CMR1B"]["sig"][ia] / F["XWSTIFF"]["sig"][ia]),
        "C/XWSTIFF": float(F["C (CCWALLCOLDR)"]["sig"][ia] / F["XWSTIFF"]["sig"][ia]),
        "CMR1B/C": float(F["CMR1B"]["sig"][ia] / F["C (CCWALLCOLDR)"]["sig"][ia]),
    }
    for k in F:
        l = out["lambdas"][k]
        l2, l4 = l["lambda2_nu"], l["lambda4_nu"]
        cross = (
            float(np.sqrt(-l2 / l4))
            if (l4 < 0 and l2 > 0)
            else (0.0 if l4 < 0 else None)
        )
        vals = {str(b): float(gnu(b, l2, l4, l["lambda_inf_nu"])) for b in BS}
        out["gamma_nu"][k] = dict(crossing_b=cross, values=vals)
        print(
            f"{k:16s} l2nu {l2:+.3e} l4nu {l4:+.3e}  gamma_nu>0 for b > {cross}  ",
            " ".join(f"b={b}:{v:+.3g}" for b, v in vals.items()),
        )
    json.dump(out, open(f"{TASK}/compare_C.json", "w"), indent=1)
    if args.plot:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import wums.plot_tools  # noqa: F401 (house style)
        from plot_output import save_plot

        b = np.linspace(0.01, 13, 600)
        fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
        for k, st in zip(F, ("-", "--", ":")):
            l = out["lambdas"][k]
            g = gnu(b, l["lambda2_nu"], l["lambda4_nu"], l["lambda_inf_nu"])
            for ax in axs:
                ax.plot(
                    b,
                    g,
                    st,
                    lw=2,
                    label=f"{k}: λ2_ν={l['lambda2_nu']:.2g}, λ4_ν={l['lambda4_nu']:.2g}",
                )
        axs[0].set_ylim(-2.1, 2.1)
        axs[1].set_xlim(0, 6)
        axs[1].set_ylim(-0.02, 0.06)
        for ax in axs:
            ax.axhline(0, color="k", lw=0.8)
            ax.axvline(12.6, color="gray", ls=":", lw=1)
            ax.set_xlabel(r"$b_T$ [GeV$^{-1}$]", fontsize=13)
            ax.tick_params(labelsize=11)
            ax.set_ylabel(r"$\gamma_\nu^{NP}(b_T)$", fontsize=13)
            ax.grid(alpha=0.3)
        axs[0].legend(fontsize=7, loc="lower left")
        axs[1].set_title("zoom: small b (γ_ν > 0 = CS anti-damping)", fontsize=9)
        fig.suptitle(
            "CS kernel at CMR1B, soft-wall C and XWSTIFF (tanh_2, λ∞_ν = 2; dotted: cache b_T reach ≈ 12.6)",
            fontsize=9,
        )
        fig.tight_layout()
        save_plot(
            outdir=TASK,
            basename="gamma_nu_CMR1B_C_XW",
            fig=fig,
            args=args,
            meta_info={
                "formula": "-linf_nu*tanh((l2nu b^2 + l4nu b^4)/linf_nu), np_damping_wall.py docstring"
            },
        )


if __name__ == "__main__":
    main()
