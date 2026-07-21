"""Is my high-accuracy Hankel actually CONVERGED for the 486x-cancelling high-qT
integrand, or is 400k linear points not enough (=> more points WOULD help)?

For Q=91, qT in {90,95,100}: reconstruct the real-b Hankel of the cached W(bT)
with increasing fine-linear-grid N, plus scipy adaptive quad, and print result/pm.
 - plateaus (N-independent) != pm  => converged; genuine real-b-Hankel vs SCETlib gap.
 - drifts toward pm with N          => my integration under-resolved; more points help.
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
Q, Y = 91.0, 0.0
QT = [90.0, 95.0, 100.0]
NS = [200_000, 400_000, 800_000, 1_600_000, 3_200_000, 6_400_000]


def main():
    from scipy.interpolate import CubicSpline
    from scipy.integrate import simpson as _simpson, quad
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
    gnu = {k: v for k, v in GNU.items() if k != "np_model_nu"}
    eff = {k: v for k, v in EFF.items() if k != "np_model"}
    gNP = fz_tf.gamma_nu_NP_tf(b_bar, gnu, np_model_nu=GNU["np_model_nu"]).numpy()
    Feff = fz_tf.F_eff_tf(Y, b_bar, eff, np_model=EFF["np_model"]).numpy()
    sp = pickle.load(open(POINTMODE, "rb"))["spectra"][0]

    def pm_at(qT):
        for k in sp:
            if abs(k[0] - Q) < 1e-6 and abs(k[1] - Y) < 1e-6 and abs(k[2] - qT) < 1e-6:
                return sp[k]
        return np.nan

    for qT in QT:
        ibin = min(
            range(len(bins)),
            key=lambda i: abs(bins[i][0] - Q)
            + abs(bins[i][1] - Y)
            + abs(bins[i][2] - qT),
        )
        W = Ipert[ibin] * np.exp(Cnu[ibin] * gNP) * Feff
        spl = CubicSpline(bT, W)
        pm = pm_at(qT)
        print(f"\n=== Q={Q} qT={qT}  point-mode={pm:.6g} ===")
        for N in NS:
            bf = np.linspace(bT.min(), bT.max(), N)
            s = qT * _simpson(bf * j0(qT * bf) * spl(bf), x=bf)
            print(f"  N={N:>9,}  result={s:12.6g}  result/pm={s/pm:8.4f}")
        # adaptive quad as an independent cross-check (limit high for oscillation)
        val, err = quad(
            lambda b: b * j0(qT * b) * float(spl(b)),
            bT.min(),
            bT.max(),
            limit=20000,
            epsabs=1e-12,
            epsrel=1e-10,
        )
        s = qT * val
        print(
            f"  scipy.quad result={s:12.6g}  result/pm={s/pm:8.4f}  (err~{qT*err:.2g})"
        )


if __name__ == "__main__":
    main()
