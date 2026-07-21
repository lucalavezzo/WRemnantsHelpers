"""Pinpoint the tail-gap integrand bug: cache I_pert / C_nu vs SCETlib truth (bT = cache nodes).

Inputs:
  - hankel_integrator_test.npz : SCETlib W_full/W_pert/C_nu on cache bT nodes at qT=90,100
    (b_bar == bs == bT confirmed there, so NP argument is not the issue).
  - btgrid cache via btgrid_cache.load : our stored I_pert, C_nu, b_bar, bT.

Checks at (Q=91,Y=0), qT in {90,100}:
  1. I_pert_cache  vs  W_pert_scetlib     (NP-off perturbative integrand)  -> ratio vs bT
  2. C_nu_cache    vs  C_nu_scetlib                                        -> ratio vs bT
  3. W_ours = I_pert*exp(C_nu*gnu(b_bar))*Feff(b_bar)  vs  W_full_scetlib  -> ratio vs bT
  4. Hankel W_ours and W_full_scetlib with the SAME finite method -> reproduces 0.444 vs 0.977 split

Run: wremnants container (latest) + venv + setup.sh.
"""

import numpy as np

SCET = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ptvgen-truncation/hankel_integrator_test.npz"
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


def band(x, sel):
    xs = x[sel]
    return float(np.nanmin(xs)), float(np.nanmedian(xs)), float(np.nanmax(xs))


def main():
    from scipy.interpolate import CubicSpline
    from scipy.integrate import simpson
    from scipy.special import j0
    from wremnants.postprocessing.scetlib_np import btgrid_cache
    from wremnants.postprocessing.scetlib_np import btgrid_tf as fz_tf

    s = np.load(SCET)
    cbT = s["cbT"]
    bs = s["bs_cache"]

    grid = btgrid_cache.load(BTGRID)
    for k in ("I_pert", "C_nu"):
        np.nan_to_num(grid[k], copy=False, nan=0.0, posinf=0.0, neginf=0.0)
    bT = np.asarray(grid["bT"], np.float64)
    b_bar = np.asarray(grid["b_bar"], np.float64)
    Ipert = np.asarray(grid["I_pert"][0], np.float64)
    Cnu = np.asarray(grid["C_nu"][0], np.float64)
    bins = grid["bins"]

    assert np.max(np.abs(bT - cbT)) < 1e-9, "cache bT grid mismatch vs dumped cbT"

    # NP factors (production fz_tf forms) at b_bar
    gnu = {k: v for k, v in GNU.items() if k != "np_model_nu"}
    eff = {k: v for k, v in EFF.items() if k != "np_model"}
    gNP = fz_tf.gamma_nu_NP_tf(b_bar, gnu, np_model_nu=GNU["np_model_nu"]).numpy()
    Feff = fz_tf.F_eff_tf(Y, b_bar, eff, np_model=EFF["np_model"]).numpy()

    for qt in [90.0, 100.0]:
        ibin = min(
            range(len(bins)),
            key=lambda i: abs(bins[i][0] - Q)
            + abs(bins[i][1] - Y)
            + abs(bins[i][2] - qt),
        )
        Ip = Ipert[ibin]
        Cn = Cnu[ibin]
        Wfull_scet = s[f"Wfull_scet_cache_{qt:.0f}"]
        Wpert_scet = s[f"Wpert_scet_cache_{qt:.0f}"]
        Cnu_scet = s[f"Cnu_scet_cache_{qt:.0f}"]

        # windows: perturbative core (small bT) and the NP-damped region
        core = (bT > 0.02) & (bT < 1.5)  # perturbative peak, well away from Landau
        damp = (bT > 0.02) & (bT < 8.0)  # where the full integrand has support

        print(f"\n================ qT={qt}  (bin {bins[ibin]}) ================")

        # 1. I_pert vs W_pert  (perturbative core only; large bT is undamped Landau, meaningless)
        with np.errstate(divide="ignore", invalid="ignore"):
            r_ip = Wpert_scet / Ip
        print(
            f"  [1] W_pert_scet / I_pert_cache  core(0.02,1.5) min/med/max = {band(r_ip, core)}"
        )

        # 2. C_nu vs C_nu_scet
        with np.errstate(divide="ignore", invalid="ignore"):
            r_cn = Cnu_scet / Cn
        print(
            f"  [2] C_nu_scet / C_nu_cache      core(0.02,1.5) min/med/max = {band(r_cn, core)}"
        )
        print(
            f"      C_nu_scet - C_nu_cache       damp(0.02,8) max|diff|    = {np.nanmax(np.abs((Cnu_scet-Cn)[damp])):.3e}"
        )

        # 3. full reconstructed integrand vs SCETlib full
        W_ours = Ip * np.exp(Cn * gNP) * Feff
        with np.errstate(divide="ignore", invalid="ignore"):
            r_w = W_ours / Wfull_scet
        print(
            f"  [3] W_ours / W_full_scet        damp(0.02,8) min/med/max  = {band(r_w, damp)}"
        )

        # 4. Hankel both on cbT with identical fine method
        def hankel(W):
            spl = CubicSpline(bT, W)
            bf = np.linspace(bT.min(), bT.max(), 2_000_000)
            return qt * simpson(bf * j0(qt * bf) * spl(bf), x=bf)

        h_ours = hankel(W_ours)
        h_scet = hankel(Wfull_scet)
        sval = float(s[f"sval_{qt:.0f}"])
        print(f"  [4] Hankel(W_ours)     = {h_ours:.7g}  /sval = {h_ours/sval:.4f}")
        print(f"      Hankel(W_full_scet) = {h_scet:.7g}  /sval = {h_scet/sval:.4f}")
        print(f"      Hankel(W_ours)/Hankel(W_full_scet) = {h_ours/h_scet:.4f}")


if __name__ == "__main__":
    main()
