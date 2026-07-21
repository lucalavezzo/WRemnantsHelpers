"""Isolate the high-qT resum reconstruction error: is it OUR bT-Simpson, or the
stored bT node-set/range?  (Fixed-API port of prod/scetlib_run/hankel_quadrature_check.py,
which calls the old gamma_nu_NP_tf/F_eff_tf signature.)

For a fixed (Q,Y) cell, per qT:
  ours = qT * Σ wS · [bT J0(qT bT)] · W(bT)        (our 2000-node log-grid Simpson)
  hi   = qT * ∫ [bT J0(qT bT)] · spline(W)(bT) dbT  (fine LINEAR grid, resolves J0)
  pm   = point-mode SCETlib σ(Q,Y,qT)               (the direct reference)
with W(bT) = I_pert · exp(C_nu·γ_ν^NP(b_bar)) · F_eff(Y,b_bar).

  ours != hi                -> OUR Simpson is biased (fix = better integration; maybe NO regen)
  ours == hi != pm          -> the stored 2000-node bT grid range/density is insufficient (bT regen)
"""

import argparse
import pickle
import numpy as np

BTGRID = "/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/"
POINTMODE = (
    "/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_CT18Z_N3p0LL_franksvals_pointmode/"
    "inclusive_Z_COM13_CT18Z_N3p0LL_franksvals_pointmode_pdf0_bins_000_558360_var_000_pointspec.pkl"
)
EFF = {
    "np_model": "tanh_2",
    "lambda_inf": 1.0,
    "lambda2": 0.4,
    "lambda4": 0.4,
    "lambda6": 0.0,
    "delta_lambda2": 0.0,
}
GNU = {
    "np_model_nu": "tanh_2",
    "lambda2_nu": 0.15,
    "lambda4_nu": 0.0,
    "lambda_inf_nu": 2.0,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--btgrid", default=BTGRID)
    ap.add_argument("--pointmode", default=POINTMODE)
    ap.add_argument("--Q", type=float, default=91.0)
    ap.add_argument("--Y", type=float, default=0.0)
    ap.add_argument("--nfine", type=int, default=400000)
    args = ap.parse_args()

    from scipy.interpolate import CubicSpline
    from scipy.integrate import simpson as _simpson
    from scipy.special import j0
    from wremnants.postprocessing.scetlib_np import btgrid_cache
    from wremnants.postprocessing.scetlib_np import btgrid_tf as fz_tf

    print(f"[load] {args.btgrid}", flush=True)
    grid = btgrid_cache.load(args.btgrid)
    for k in ("I_pert", "C_nu"):
        np.nan_to_num(grid[k], copy=False, nan=0.0, posinf=0.0, neginf=0.0)
    bT = np.asarray(grid["bT"], np.float64)
    b_bar = np.asarray(grid["b_bar"], np.float64)
    Ipert = np.asarray(grid["I_pert"][0], np.float64)
    Cnu = np.asarray(grid["C_nu"][0], np.float64)
    bins = grid["bins"]
    wS = fz_tf.simpson_weights(bT)
    print(
        f"  bT: {bT.size} nodes [{bT.min():.1e},{bT.max():.1f}]  Nbins={len(bins)}",
        flush=True,
    )

    # CURRENT API: params dict minus the form key, form passed separately.
    gnu = {k: v for k, v in GNU.items() if k != "np_model_nu"}
    eff = {k: v for k, v in EFF.items() if k != "np_model"}
    gNP = fz_tf.gamma_nu_NP_tf(b_bar, gnu, np_model_nu=GNU["np_model_nu"]).numpy()
    Feff = fz_tf.F_eff_tf(args.Y, b_bar, eff, np_model=EFF["np_model"]).numpy()

    sel = [
        (i, b[2])
        for i, b in enumerate(bins)
        if abs(b[0] - args.Q) < 1e-6 and abs(b[1] - args.Y) < 1e-6
    ]
    sel.sort(key=lambda t: t[1])
    print(f"  (Q={args.Q}, Y={args.Y}): {len(sel)} qT bins", flush=True)

    sp = pickle.load(open(args.pointmode, "rb"))["spectra"][0]

    def pm_at(qT):
        for k in sp:
            if (
                abs(k[0] - args.Q) < 1e-6
                and abs(k[1] - args.Y) < 1e-6
                and abs(k[2] - qT) < 1e-6
            ):
                return sp[k]
        return np.nan

    bT_fine = np.linspace(bT.min(), bT.max(), args.nfine)
    print(
        f"{'qT':>7} {'ours':>12} {'hi':>12} {'pm':>12} {'ours/pm':>9} {'hi/pm':>9} {'ours/hi':>9}"
    )
    for ibin, qT in sel:
        if qT < 55:  # focus on the tail
            continue
        W = Ipert[ibin] * np.exp(Cnu[ibin] * gNP) * Feff
        s_ours = qT * np.sum(wS * (bT * j0(qT * bT)) * W)
        W_fine = CubicSpline(bT, W)(bT_fine)
        s_hi = qT * _simpson(bT_fine * j0(qT * bT_fine) * W_fine, x=bT_fine)
        pm = pm_at(qT)
        r_op = s_ours / pm if pm else np.nan
        r_hp = s_hi / pm if pm else np.nan
        r_oh = s_ours / s_hi if s_hi else np.nan
        print(
            f"{qT:7.1f} {s_ours:12.5g} {s_hi:12.5g} {pm:12.5g} {r_op:9.4f} {r_hp:9.4f} {r_oh:9.4f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
