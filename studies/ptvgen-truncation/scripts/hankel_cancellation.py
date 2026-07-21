"""Is the high-qT resum Hankel a delicate large-cancellation residual?
If so, the tiny result is acutely sensitive to any integrand difference (cached
real-b integrand vs SCETlib's internal treatment) -> explains why ours/hi both
miss point-mode there and why no amount of integration points fixes it.

At Q=91, Y=0, for several qT: integrand g(bT)=bT*J0(qT*bT)*W(bT) on a fine grid;
report result = qT*∫g, peak partial-sum |C|_max, and cancellation = |C|_max/|result|.
"""

import numpy as np

BTGRID = "/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/"
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
QT = [20.0, 60.0, 90.0, 100.0]


def main():
    from scipy.interpolate import CubicSpline
    from scipy.integrate import cumulative_trapezoid
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
    bfine = np.linspace(bT.min(), bT.max(), 400000)

    print(f"Q={Q} Y={Y}")
    print(
        f"{'qT':>6} {'result':>12} {'|C|_max':>12} {'cancel=|C|max/|res|':>20} {'bT* (peak |g|)':>14}"
    )
    for qT in QT:
        ibin = min(
            range(len(bins)),
            key=lambda i: (
                abs(bins[i][0] - Q) + abs(bins[i][1] - Y) + abs(bins[i][2] - qT)
            ),
        )
        W = Ipert[ibin] * np.exp(Cnu[ibin] * gNP) * Feff
        Wf = CubicSpline(bT, W)(bfine)
        g = bfine * j0(qT * bfine) * Wf
        C = qT * cumulative_trapezoid(g, bfine, initial=0.0)  # running integral
        result = C[-1]
        Cmax = np.max(np.abs(C))
        cancel = Cmax / abs(result) if result != 0 else np.inf
        bstar = bfine[np.argmax(np.abs(g))]
        print(f"{qT:6.1f} {result:12.5g} {Cmax:12.5g} {cancel:20.1f} {bstar:14.3f}")
    print(
        "\ncancel >> 1  => result is a tiny residual of a large oscillatory cancellation"
    )
    print(
        "            => acutely sensitive to any integrand difference; not fixable by more points"
    )


if __name__ == "__main__":
    main()
