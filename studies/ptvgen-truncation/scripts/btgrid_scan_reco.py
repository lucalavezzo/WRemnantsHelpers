"""Reconstruct WITH NP from the generate .npz grids (varying n_bT, bT_max) and
compare to point-mode SCETlib at high qT. The generate NP-off self-test is useless
here (b0_over_bmax=0 -> NP provides ALL large-bT damping -> bare Hankel diverges),
so we apply the franksvals NP and Hankel-integrate, then compare to point-mode.

Answers: does a denser / wider bT grid converge the high-qT resum reconstruction
to SCETlib?  ours = log-Simpson (as the model does); hi = spline->fine-linear.
"""

import glob, pickle, re
import numpy as np

SCAN = (
    "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ptvgen-truncation/btgrid_scan"
)
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
QT_SHOW = [70, 80, 85, 90, 95, 100]


def main():
    from scipy.interpolate import CubicSpline
    from scipy.integrate import simpson as _simpson
    from scipy.special import j0
    from wremnants.postprocessing.scetlib_np import btgrid_tf as fz_tf

    sp = pickle.load(open(POINTMODE, "rb"))["spectra"][0]

    def pm_at(qT):
        for k in sp:
            if abs(k[0] - Q) < 1e-6 and abs(k[1] - Y) < 1e-6 and abs(k[2] - qT) < 1e-6:
                return sp[k]
        return np.nan

    gnu = {k: v for k, v in GNU.items() if k != "np_model_nu"}
    eff = {k: v for k, v in EFF.items() if k != "np_model"}

    files = sorted(glob.glob(f"{SCAN}/g_*.npz"))
    print(f"grids: {[f.split('/')[-1] for f in files]}\n")
    print(f"{'grid':>14} {'qT':>5} {'ours/pm':>9} {'hi/pm':>9} {'ours/hi':>9}")
    for f in files:
        d = np.load(f)
        bT = d["bT"].astype(float)
        b_bar = d["b_bar"].astype(float)
        qT = d["qT"].astype(float)
        Ip = d["I_pert"].astype(float)
        Cn = d["C_nu"].astype(float)
        tag = re.search(r"g_(\d+)_(\d+)", f).group(0)
        gNP = fz_tf.gamma_nu_NP_tf(b_bar, gnu, np_model_nu=GNU["np_model_nu"]).numpy()
        Feff = fz_tf.F_eff_tf(Y, b_bar, eff, np_model=EFF["np_model"]).numpy()
        wS = fz_tf.simpson_weights(bT)
        bT_fine = np.linspace(bT.min(), bT.max(), 400000)
        for j, q in enumerate(qT):
            if round(q) not in QT_SHOW:
                continue
            W = Ip[j] * np.exp(Cn[j] * gNP) * Feff
            s_ours = q * np.sum(wS * (bT * j0(q * bT)) * W)
            W_fine = CubicSpline(bT, W)(bT_fine)
            s_hi = q * _simpson(bT_fine * j0(q * bT_fine) * W_fine, x=bT_fine)
            pm = pm_at(q)
            print(
                f"{tag:>14} {q:5.0f} {s_ours/pm:9.4f} {s_hi/pm:9.4f} {s_ours/s_hi:9.4f}"
            )
        print()


if __name__ == "__main__":
    main()
