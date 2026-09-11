#!/usr/bin/env python3
"""Full read of the walled fit against the unwalled one: lambdas, conditions,
convergence, and the pieces of the loss.

usage: analyse_walled.py <walled_fitresult.hdf5> [tau]
"""
import sys

import numpy as np
from scipy import stats

CARD = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
    "study_scratch/260910-anchor-verify/card_none.hdf5"
)
UNWALLED = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
    "260910_blinding_final/fitresults_DATABLIND.hdf5"
)
REF = dict(
    loss=405.5608736721634,
    edm=1.3863650682068962e-3,
    nit=221,
    sat_ndof=733,
    sat_2dnll=811.1217473443268,
    lin_ndof=780,
    lin_chi2=809.0,
    minimize_s=2645.4,
)
WAL = dict(
    loss=411.9912132618329,
    edm=9.632386862470065e-7,
    nit=138,
    sat_ndof=733,
    sat_2dnll=823.9824265236658,
    lin_ndof=780,
    lin_chi2=818.0,
    minimize_s=1509.2,
)

from rabbit import inputdata, io_tools  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402

NPNAMES = ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]


def read(path):
    res = io_tools.get_fitresult(path)
    h = res["parms"].get()
    names = [str(n) for n in h.axes[0]]
    return (names, h.values(), np.sqrt(h.variances()), res)


def main():
    walled = sys.argv[1]
    tau = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
    inp = wall.resolve_wall_inputs(inputdata.FitInputData(CARD))

    un, uv, ue, _ = read(UNWALLED)
    wn, wv, we, wres = read(walled)
    ut = {n: float(uv[i]) for i, n in enumerate(un)}
    us = {n: float(ue[i]) for i, n in enumerate(un)}
    wt = {n: float(wv[i]) for i, n in enumerate(wn)}
    ws = {n: float(we[i]) for i, n in enumerate(wn)}

    def phys(theta):
        return {
            n: (
                float(wall.physical_from_theta(inp["specs"][n], theta[n]))
                if n in theta
                else float(inp["anchors"][n])
            )
            for n in inp["names"]
        }

    up, wp = phys(ut), phys(wt)
    anchor = {n: float(inp["anchors"][n]) for n in inp["names"]}

    print("=" * 96)
    print("PHYSICAL NP LAMBDAS   anchor | unwalled DATABLIND | walled tau=5")
    print("=" * 96)
    print(
        f"{'lambda':15s} {'anchor':>10s} | {'unwalled':>11s} {'sig(th)':>10s} "
        f"| {'walled':>11s} {'sig(th)':>10s} | {'theta shift':>11s}"
    )
    print("-" * 96)
    for n in inp["names"]:
        if n in wt:
            print(
                f"{n:15s} {anchor[n]:10.5f} | {up[n]:11.6f} {us[n]:10.6f} "
                f"| {wp[n]:11.6f} {ws[n]:10.6f} | {wt[n] - ut[n]:+11.4f}"
            )
        else:
            print(
                f"{n:15s} {anchor[n]:10.5f} | {up[n]:11.6f} {'(held)':>10s} "
                f"| {wp[n]:11.6f} {'(held)':>10s} |"
            )

    for tag, values in (("UNWALLED", up), ("WALLED", wp)):
        conds = wall.damping_conditions(
            inp["np_model"], inp["np_model_nu"], inp["ymax"]
        )
        tot = 0.0
        nbad = []
        print()
        print(f"--- damping conditions, {tag} tune ---")
        for c in conds:
            v = float(c.value(values, wall.numpy_relu2))
            p = float(c.penalty(values, wall.numpy_relu2))
            tot += p
            if v < 0.0:
                nbad.append((c.label, v))
            print(
                f"  {'PHYS ' if v >= 0 else 'UNPHY'} {c.label:62s} "
                f"coeff {v:+13.6g} pen {p:.5g}"
            )
        print(
            f"  UNPHYSICAL: {len(nbad)}/{len(conds)}"
            + (
                ""
                if not nbad
                else "  -> " + "; ".join(f"{l} = {v:+.4g}" for l, v in nbad)
            )
        )
        print(
            f"  bare penalty {tot:.6g}   x exp(2*{tau:g}) = "
            f"{tot * np.exp(2 * tau):.6g} in NLL"
        )
        if tag == "WALLED":
            pen_w = tot * np.exp(2 * tau)

    # ---- the CS kernel's sign structure, which is what "physical" means here
    print()
    print("--- where does the CS kernel anti-damp?  P(u) = l2nu*u + l4nu*u^2 ---")
    for tag, p in (("unwalled", up), ("walled", wp)):
        l2, l4 = p["lambda2_nu"], p["lambda4_nu"]
        root = -l2 / l4 if l4 != 0 else np.inf  # P = 0 at u = -l2/l4
        if root > 0:
            b = np.sqrt(root)
            side = "b_T <" if l2 < 0 else "b_T >"
            print(
                f"  {tag:9s} l2nu={l2:+.6g} l4nu={l4:+.6g}  -> anti-damping "
                f"for {side} {b:.3g} GeV^-1"
            )
        else:
            print(f"  {tag:9s} l2nu={l2:+.6g} l4nu={l4:+.6g}  -> P >= 0 " "everywhere")

    # ---- convergence and the loss decomposition
    print()
    print("=" * 96)
    print("CONVERGENCE AND LOSS")
    print("=" * 96)
    d_tot = WAL["loss"] - REF["loss"]
    d_pure = d_tot - pen_w
    print(
        f"  loss (fun)          unwalled {REF['loss']:.6f}   walled "
        f"{WAL['loss']:.6f}   delta {d_tot:+.4f}"
    )
    print(f"  wall penalty in the walled loss                     " f"{pen_w:.4f}")
    print(
        f"  Delta(pure NLL) = walled - penalty - unwalled        "
        f"{d_pure:+.4f}   -> Delta(chi2) = {2 * d_pure:+.3f}"
    )
    print(
        f"  EDM                 unwalled {REF['edm']:.4e}   walled "
        f"{WAL['edm']:.4e}   ({REF['edm'] / WAL['edm']:.0f}x better)"
    )
    print(
        f"  iterations / minimize(s)  unwalled {REF['nit']} / "
        f"{REF['minimize_s']:.0f}   walled {WAL['nit']} / "
        f"{WAL['minimize_s']:.0f}"
    )
    for tag, d in (("unwalled", REF), ("walled", WAL)):
        p = stats.chi2.sf(d["sat_2dnll"], d["sat_ndof"]) * 100
        print(
            f"  saturated {tag:9s} 2dNLL {d['sat_2dnll']:.2f}/"
            f"{d['sat_ndof']}  p = {p:.2f}%"
        )
    # The saturated reference NLL is ~0 (2dNLL == 2*fun to the printed digits),
    # so the wall penalty enters the saturated chi2 twice over; take it out.
    sat_corr = WAL["sat_2dnll"] - 2 * pen_w
    print(
        f"  saturated walled, penalty removed: {sat_corr:.2f}/"
        f"{WAL['sat_ndof']}  p = "
        f"{stats.chi2.sf(sat_corr, WAL['sat_ndof']) * 100:.2f}%"
    )
    for tag, d in (("unwalled", REF), ("walled", WAL)):
        p = stats.chi2.sf(d["lin_chi2"], d["lin_ndof"]) * 100
        print(
            f"  linear    {tag:9s} chi2 {d['lin_chi2']:.0f}/{d['lin_ndof']}"
            f"  p = {p:.2f}%"
        )

    # ---- the card nuisances: still impeccable?
    print()
    print("--- card nuisances (the 3673 that were impeccable unwalled) ---")
    MODEL = (
        "alphaS",
        "lambda",
        "delta_lambda",
        "b0_over_bmax",
        "resumTNP_",
        "resumScale",
        "resumTransition",
        "pdfEig",
    )
    for tag, names, vals in (("unwalled", un, uv), ("walled", wn, wv)):
        card = np.array([v for n, v in zip(names, vals) if not n.startswith(MODEL)])
        cn = [n for n in names if not n.startswith(MODEL)]
        i = int(np.argmax(np.abs(card)))
        print(
            f"  {tag:9s} n={len(card)}  max|pull| {np.abs(card[i]):.3f} "
            f"({cn[i]})   >2sigma: {int((np.abs(card) > 2).sum())}   "
            f">3sigma: {int((np.abs(card) > 3).sum())}"
        )

    # ---- sigma(alphaS): SAFE to print (additive blinding), central is not.
    print()
    print("--- sigma(alpha_s)  [central value is BLINDED and not printed] ---")
    for tag, s in (("unwalled", us), ("walled", ws)):
        print(
            f"  {tag:9s} sigma(theta_alphaS) = {s['alphaS']:.6f}  -> "
            f"sigma(alpha_s) = {s['alphaS'] * 0.002:.6f}"
        )
    print("ANALYSE_WALLED_DONE")


if __name__ == "__main__":
    main()
