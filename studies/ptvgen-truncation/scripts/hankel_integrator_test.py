"""Isolate the tail gap: INTEGRATOR (DE vs finite-range Hankel) vs INTEGRAND (our cache vs SCETlib).

np_factorization_clincher.py PROVED our NP factorization == SCETlib's internal NP to ~1e-12
point-by-point in bT. So the tail gap (recon 0.00207 vs point-mode 0.00466 at qT=100, ratio
0.444) is NOT the NP. It is one of:
  (I)  our cached I_pert (btgrid) differs from SCETlib's true perturbative integrand, or
  (II) the Hankel numerics: our finite-range simpson/quad != SCETlib's DE oscillatory
       integrator on the ~486x deep-tail cancellation.

Three numbers at each qT (full NP on, singular/resummed piece = card default 'sing'):
  sval        = sigma(Q,Y,qT).val                      SCETlib DE integral   (= point-mode ref)
  myH_scetlib = qT*int bT J0(qT bT) W_full(bT) dbT      MY Hankel of SCETLIB's own integrand
  myH_ours    = same Hankel of OUR reconstructed integrand (I_pert_cache * exp(C_nu*gnu)*F_eff)

Logic:
  myH_scetlib ~ sval, myH_ours < sval  ->  INTEGRAND: our cached I_pert is wrong.
  myH_scetlib ~ myH_ours < sval        ->  INTEGRATOR: finite-range Hankel can't match DE
                                            (deep-tail cancellation / truncation); integrand fine.

Also: point-by-point W_pert(SCETlib) vs cached I_pert on the cache's own 2000-node bT grid.

Run: v15 container (scetlib_core), source /opt/env.sh, hist stub on PYTHONPATH, bind /cvmfs.
"""

import sys
import numpy as np

CARD = "/scratch/submit/cms/wmass/scetlib_np/pointmode_bT_converge/pm_default.ini"
FAC = "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/prod/scetlib_run"
BUILD = "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/build/lib"
CACHE = "/scratch/submit/cms/wmass/scetlib_np/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/combined_btgrid.factorized.npz"
OUT = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ptvgen-truncation/hankel_integrator_test.npz"

Q, Y = 91.0, 0.0
QTS = [60.0, 90.0, 100.0]

FEFF = dict(
    lambda_inf=1.0,
    lambda2=0.4,
    delta_lambda2=0.0,
    lambda4=0.4,
    lambda6=0.016,
    np_model="tanh_2",
)
GNU = dict(
    lambda_inf_nu=2.0,
    lambda2_nu=0.15,
    lambda4_nu=0.0,
    lambda6_nu=0.0007,
    b0_bmax_nu=1.0,
    np_model_nu="tanh_2",
)


def feff_analytic(Y, bT, p):
    l2Y = p["lambda2"] + p["delta_lambda2"] * Y**2
    arg = (l2Y + p["lambda4"] * bT**2) * bT
    li = p["lambda_inf"]
    if li == 0.0:
        return np.ones_like(bT)
    arg = arg / li + (1.0 / 3.0) * (l2Y * bT / li) ** 3
    return np.exp(-2.0 * li * bT * np.tanh(arg))


def gammanu_analytic(bT, p):
    li = p["lambda_inf_nu"]
    if li == 0.0:
        return np.zeros_like(bT)
    bT2 = bT**2
    arg = (p["lambda2_nu"] + p["lambda4_nu"] * bT2) * bT2 / li
    return -li * np.tanh(arg)


def set_full_np(qT_mod, sigma):
    m = qT_mod.NPModelEffective()
    m.lambda_inf = FEFF["lambda_inf"]
    m.lambda2 = FEFF["lambda2"]
    m.delta_lambda2 = FEFF["delta_lambda2"]
    m.lambda4 = FEFF["lambda4"]
    m.lambda6 = FEFF["lambda6"]
    m.np_model = qT_mod.NPModelEffectiveModel.__members__[FEFF["np_model"]]
    sigma.set_effective_model(m)
    g = qT_mod.NPModelGammaNu()
    g.lambda_inf_nu = GNU["lambda_inf_nu"]
    g.lambda2_nu = GNU["lambda2_nu"]
    g.lambda4_nu = GNU["lambda4_nu"]
    if hasattr(g, "lambda6_nu"):
        g.lambda6_nu = GNU["lambda6_nu"]
    g.b0_bmax_nu = GNU["b0_bmax_nu"]
    g.np_model_nu = qT_mod.NPModelGammaNuModel.__members__[GNU["np_model_nu"]]
    sigma.set_gamma_nu_model_params(g)


def set_np_off(qT_mod, sigma):
    sigma.set_effective_model(qT_mod.NPModelEffective())  # default -> F_eff==1
    g = qT_mod.NPModelGammaNu()
    g.lambda_inf_nu = 0.0
    sigma.set_gamma_nu_model_params(g)


def my_hankel(qt, bT_nodes, W_nodes):
    """qT * int_0^inf bT J0(qT bT) W(bT) dbT via dense-simpson + scipy.quad(spline)."""
    from scipy.special import j0
    from scipy.integrate import simpson, quad
    from scipy.interpolate import CubicSpline

    spl = CubicSpline(bT_nodes, W_nodes, extrapolate=False)
    bmax = bT_nodes.max()
    # dense simpson
    xf = np.linspace(bT_nodes.min(), bmax, 4_000_000)
    Wf = spl(xf)
    Wf[np.isnan(Wf)] = 0.0
    simp = qt * simpson(xf * j0(qt * xf) * Wf, x=xf)

    # scipy.quad adaptive (independent method)
    def integrand(b):
        w = spl(b)
        return 0.0 if np.isnan(w) else b * j0(qt * b) * w

    q, qerr = quad(integrand, bT_nodes.min(), bmax, limit=400)
    return simp, qt * q, qt * qerr


def main():
    sys.path.insert(0, FAC)
    sys.path.insert(0, BUILD)
    from scetlib_run import config as scetlib_config
    import scetlib_qT as qT_mod

    conf = scetlib_config.read_config(CARD)
    _o, _a, _d, _s, sigma = scetlib_config.configure_calculation(conf)
    set_full_np(qT_mod, sigma)

    # ---- fine bT grid for the Hankel; W_full damped by F_eff ~ exp(-2 bT), safe to ~40 ----
    bT = np.logspace(-4, np.log10(40.0), 6000)

    # ---- load our cached grid: I_pert, C_nu, bT nodes at (Q,Y) ----
    cache = np.load(CACHE)
    cQ, cY, cqt = cache["Q_unique"], cache["Y_unique"], cache["qT_unique"]
    cbT = cache["bT"]
    cbbar = cache["b_bar"]
    iQ = int(np.argmin(np.abs(cQ - Q)))
    iY = int(np.argmin(np.abs(cY - Y)))
    print(f"[cache] nearest Q={cQ[iQ]:.4g} (want {Q}), Y={cY[iY]:.4g} (want {Y})")

    results = {"bT": bT}
    for qt in QTS:
        # SCETlib full NP-on integrand + DE truth
        set_full_np(qT_mod, sigma)
        W_full = np.asarray(
            sigma.resummed_bT_integrand(Q, Y, qt, bT.tolist()), dtype=float
        )
        sval = sigma(Q, Y, qt).val
        simp, quadv, quaderr = my_hankel(qt, bT, W_full)

        print(f"\n=== Q={Q} Y={Y} qT={qt} ===")
        print(f"  sval (SCETlib DE)          = {sval:.8g}")
        print(f"  myH_scetlib (simpson)      = {simp:.8g}   /sval = {simp/sval:.4f}")
        print(
            f"  myH_scetlib (scipy.quad)   = {quadv:.8g}   /sval = {quadv/sval:.4f}  (err~{quaderr:.1e})"
        )

        results[f"W_full_{qt:.0f}"] = W_full
        results[f"sval_{qt:.0f}"] = sval
        results[f"myH_scetlib_simp_{qt:.0f}"] = simp
        results[f"myH_scetlib_quad_{qt:.0f}"] = quadv

        # cross-check tail damping: how much integrand is beyond bT=40?
        print(
            f"  W_full(bT=40)/max|W_full|  = {W_full[-1]/np.max(np.abs(W_full)):.2e}  (truncation check)"
        )

    # ---- Dump SCETlib quantities on the cache bT grid for the reconstruction comparison ----
    print(
        "\n=== dump SCETlib W_full / W_pert / C_nu / bs on cache bT nodes (bind to wremnants recon) ==="
    )
    bs_cache = np.asarray(sigma.b_star_global(cbT.tolist()), dtype=float)
    results["cbT"] = cbT
    results["cbbar"] = cbbar
    results["bs_cache"] = bs_cache
    for qt in [90.0, 100.0]:
        set_full_np(qT_mod, sigma)
        Wfull_c = np.asarray(
            sigma.resummed_bT_integrand(Q, Y, qt, cbT.tolist()), dtype=float
        )
        Cnu_c = np.asarray(
            sigma.gamma_nu_NP_log_coeff(Q, Y, qt, cbT.tolist()), dtype=float
        )
        set_np_off(qT_mod, sigma)
        Wpert_c = np.asarray(
            sigma.resummed_bT_integrand(Q, Y, qt, cbT.tolist()), dtype=float
        )
        results[f"Wfull_scet_cache_{qt:.0f}"] = Wfull_c
        results[f"Wpert_scet_cache_{qt:.0f}"] = Wpert_c
        results[f"Cnu_scet_cache_{qt:.0f}"] = Cnu_c
    # cached I_pert row (raw npz mapping) at qT=100 for a quick sanity vs btgrid_cache later
    flat_idx = cache["flat_idx"]
    c_of_u = cache["c_of_u"]
    I_pert_u = cache["I_pert_u"]
    iqt = int(np.argmin(np.abs(cqt - 100.0)))
    row = int(flat_idx[iQ, iY, iqt])
    results["Ipert_cache_rawmap_100"] = I_pert_u[int(c_of_u[row])]
    print(f"  b_star_global identity? max|bs-cbT| = {np.max(np.abs(bs_cache-cbT)):.3e}")
    print(f"  b_bar == cbT? max|cbbar-cbT| = {np.max(np.abs(cbbar-cbT)):.3e}")

    np.savez(OUT, **results)
    print(f"\nsaved -> {OUT}")


if __name__ == "__main__":
    main()
