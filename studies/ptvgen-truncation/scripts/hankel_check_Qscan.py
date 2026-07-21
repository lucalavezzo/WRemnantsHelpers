"""UNDERSTAND the high-qT resum-reconstruction deficit: does its onset track qT≈Q
(the profile transition_points=[0.2,0.6,1.0] turning resummation off at qT/Q→1)?

Loads the btgrid ONCE, then for Q in {60,91,120} (Y=0) prints ours/hi/pm vs qT.
  ours = our 2000-node log Simpson bT-Hankel (the model)
  hi   = spline(cached W) -> 400k linear grid, integrate (converged high-accuracy)
  pm   = point-mode SCETlib (its own internal bT integral)
Prediction if it's the resummation turn-off: deficit onset scales with Q, i.e. sets in
around qT/Q ~ 0.9-1.0. At Q=120 (transition at qT=120 > qT_max=100) there should be
little/no deficit; at Q=60 it should start ~qT 55-60.
"""

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
QS = [60.0, 91.0, 120.0]
Y = 0.0


def main():
    from scipy.interpolate import CubicSpline
    from scipy.integrate import simpson as _simpson
    from scipy.special import j0
    from wremnants.postprocessing.scetlib_np import btgrid_cache
    from wremnants.postprocessing.scetlib_np import btgrid_tf as fz_tf

    grid = btgrid_cache.load(BTGRID)
    for k in ("I_pert", "C_nu"):
        np.nan_to_num(grid[k], copy=False, nan=0.0, posinf=0.0, neginf=0.0)
    bT = np.asarray(grid["bT"], np.float64)
    b_bar = np.asarray(grid["b_bar"], np.float64)
    Ipert = np.asarray(grid["I_pert"][0], np.float64)
    Cnu = np.asarray(grid["C_nu"][0], np.float64)
    bins = grid["bins"]
    wS = fz_tf.simpson_weights(bT)
    bT_fine = np.linspace(bT.min(), bT.max(), 400000)
    sp = pickle.load(open(POINTMODE, "rb"))["spectra"][0]

    gnu = {k: v for k, v in GNU.items() if k != "np_model_nu"}
    eff = {k: v for k, v in EFF.items() if k != "np_model"}
    gNP = fz_tf.gamma_nu_NP_tf(b_bar, gnu, np_model_nu=GNU["np_model_nu"]).numpy()

    def pm_at(Q, qT):
        for k in sp:
            if abs(k[0] - Q) < 1e-6 and abs(k[1] - Y) < 1e-6 and abs(k[2] - qT) < 1e-6:
                return sp[k]
        return np.nan

    for Q in QS:
        Feff = fz_tf.F_eff_tf(Y, b_bar, eff, np_model=EFF["np_model"]).numpy()
        sel = sorted(
            [
                (i, b[2])
                for i, b in enumerate(bins)
                if abs(b[0] - Q) < 1e-6 and abs(b[1] - Y) < 1e-6
            ],
            key=lambda t: t[1],
        )
        print(f"\n===== Q={Q} (transition qT≈Q={Q:.0f}); {len(sel)} qT bins =====")
        print(f"{'qT':>6} {'qT/Q':>6} {'ours/pm':>9} {'hi/pm':>9} {'ours/hi':>9}")
        for ibin, qT in sel:
            if qT < 0.55 * Q:
                continue
            W = Ipert[ibin] * np.exp(Cnu[ibin] * gNP) * Feff
            s_ours = qT * np.sum(wS * (bT * j0(qT * bT)) * W)
            s_hi = qT * _simpson(
                bT_fine * j0(qT * bT_fine) * CubicSpline(bT, W)(bT_fine), x=bT_fine
            )
            pm = pm_at(Q, qT)
            print(
                f"{qT:6.1f} {qT/Q:6.3f} {s_ours/pm:9.4f} {s_hi/pm:9.4f} {s_ours/s_hi:9.4f}"
            )


if __name__ == "__main__":
    main()
