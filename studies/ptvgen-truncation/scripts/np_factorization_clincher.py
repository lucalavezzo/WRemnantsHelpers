"""DEFINITIVE NP-factorization test (bT-space, no Hankel).

The old clincher (scetlib_integrand_clincher.py) was BROKEN: configure_calculation()
sets the gamma_nu model but NOT the effective model (set_effective_model lives in the
variations flow). The C++ default NP_model_effective has lambda2=lambda4=lambda_inf=0,
np_model=identity -> F_eff == 1. So resummed_bT_integrand there returned an F_eff-OFF
integrand (undamped) -> its naive-simpson Hankel blew up (286 vs 0.15). It never tested
our NP.

Here we toggle each NP piece EXPLICITLY and use SCETlib as ground truth for its own NP:
  W_pert  = resummed_bT_integrand, gamma_nu OFF, F_eff OFF   (pure perturbative)
  W_gnu   = resummed_bT_integrand, gamma_nu ON,  F_eff OFF
  W_feff  = resummed_bT_integrand, gamma_nu OFF, F_eff ON
  W_full  = resummed_bT_integrand, gamma_nu ON,  F_eff ON
  C_nu    = gamma_nu_NP_log_coeff  (SCETlib's own C_nu(qT,bT))
  bs      = b_star_global(bT)

Tests (point-by-point in bT, the NP is analytic so this must be exact):
  (A) multiplicative factorization:   W_full/W_pert  ==  (W_gnu/W_pert)*(W_feff/W_pert)
  (B) F_eff form:                     W_feff/W_pert  ==  F_eff_analytic(Y, bs)
  (C) C_nu decomposition + gnu form:  W_gnu/W_pert   ==  exp(C_nu * gammanu_analytic(bs_nu))
  (D) qT-independence of F_eff and of extracted gamma_nu^NP (cross-checks the decomposition)

If (A)-(C) hold to ~machine precision, our bt-grid reconstruction
  W_ours = I_pert * exp(C_nu*gnu) * F_eff
is EXACTLY SCETlib's NP application, and the tail gap is 100% Hankel numerics
(the ~486x deep-tail cancellation), not the NP. Any residual vs bT localizes which piece.

Run: v15 container (scetlib_core/scetlib_qT), source /opt/env.sh, hist stub on PYTHONPATH.
"""

import sys
import numpy as np

CARD = "/scratch/submit/cms/wmass/scetlib_np/pointmode_bT_converge/pm_default.ini"
FAC = "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/prod/scetlib_run"
BUILD = "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/build/lib"
OUT = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ptvgen-truncation/np_factorization_clincher.npz"

Q, Y = 91.0, 0.0
QTS = [60.0, 90.0, 100.0]

# franksvals NP (from pm_default.ini [Nonperturbative])
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

# b0 = 2 exp(-gammaE)
B0 = 2.0 * np.exp(-np.euler_gamma)


def feff_analytic(Y, bT, p):
    """C++ NP_model_effective::operator()(Y,bT), tanh_2 branch (NP_models.hpp:71-112)."""
    l2Y = p["lambda2"] + p["delta_lambda2"] * Y**2
    arg = (l2Y + p["lambda4"] * bT**2) * bT
    li = p["lambda_inf"]
    if li == 0.0:
        return np.ones_like(bT)
    arg = arg / li
    arg = arg + (1.0 / 3.0) * (l2Y * bT / li) ** 3  # tanh_2
    return np.exp(-2.0 * li * bT * np.tanh(arg))


def bstar_nu(bT, p):
    """C++ NP_model_gammanu::bStar (Gamma_nu.hpp:79-82)."""
    if p["b0_bmax_nu"] != 0.0:
        return np.power((B0 / bT) ** 6 + p["b0_bmax_nu"] ** 6, -1.0 / 6.0)
    return bT / B0


def gammanu_analytic(bT_arg, p):
    """C++ NP_model_gammanu::model_gammanu(bT), tanh_2 (Gamma_nu.hpp:84-123).

    NOTE: caller must pass the argument SCETlib feeds model_gammanu (see call-site check).
    """
    li = p["lambda_inf_nu"]
    if li == 0.0:
        return np.zeros_like(bT_arg)
    bT2 = bT_arg**2
    arg = (p["lambda2_nu"] + p["lambda4_nu"] * bT2) * bT2 / li  # tanh_2
    return -li * np.tanh(arg)


def set_feff(qT_mod, sigma, on):
    m = qT_mod.NPModelEffective()
    if on:
        m.lambda_inf = FEFF["lambda_inf"]
        m.lambda2 = FEFF["lambda2"]
        m.delta_lambda2 = FEFF["delta_lambda2"]
        m.lambda4 = FEFF["lambda4"]
        m.lambda6 = FEFF["lambda6"]
        m.np_model = qT_mod.NPModelEffectiveModel.__members__[FEFF["np_model"]]
    # else: default -> identity, all zero -> F_eff == 1
    sigma.set_effective_model(m)


def set_gnu(qT_mod, sigma, on):
    m = qT_mod.NPModelGammaNu()
    if on:
        m.lambda_inf_nu = GNU["lambda_inf_nu"]
        m.lambda2_nu = GNU["lambda2_nu"]
        m.lambda4_nu = GNU["lambda4_nu"]
        if hasattr(m, "lambda6_nu"):
            m.lambda6_nu = GNU["lambda6_nu"]
        m.b0_bmax_nu = GNU["b0_bmax_nu"]
        m.np_model_nu = qT_mod.NPModelGammaNuModel.__members__[GNU["np_model_nu"]]
    else:
        m.lambda_inf_nu = 0.0  # -> model_gammanu == 0
    sigma.set_gamma_nu_model_params(m)


def main():
    sys.path.insert(0, FAC)
    sys.path.insert(0, BUILD)
    from scetlib_run import config as scetlib_config
    import scetlib_qT as qT_mod

    conf = scetlib_config.read_config(CARD)
    _o, _a, _d, _s, sigma = scetlib_config.configure_calculation(conf)
    if not isinstance(sigma, qT_mod.DrellYan):
        raise RuntimeError("expected DrellYan")

    bT = np.logspace(-3, np.log10(50.0), 400)
    bs = np.asarray(sigma.b_star_global(bT.tolist()), dtype=float)

    results = {"bT": bT, "bs": bs}
    for qt in QTS:
        # toggle the four states
        set_gnu(qT_mod, sigma, False)
        set_feff(qT_mod, sigma, False)
        W_pert = np.asarray(
            sigma.resummed_bT_integrand(Q, Y, qt, bT.tolist()), dtype=float
        )
        set_gnu(qT_mod, sigma, True)
        set_feff(qT_mod, sigma, False)
        W_gnu = np.asarray(
            sigma.resummed_bT_integrand(Q, Y, qt, bT.tolist()), dtype=float
        )
        set_gnu(qT_mod, sigma, False)
        set_feff(qT_mod, sigma, True)
        W_feff = np.asarray(
            sigma.resummed_bT_integrand(Q, Y, qt, bT.tolist()), dtype=float
        )
        set_gnu(qT_mod, sigma, True)
        set_feff(qT_mod, sigma, True)
        W_full = np.asarray(
            sigma.resummed_bT_integrand(Q, Y, qt, bT.tolist()), dtype=float
        )
        C_nu = np.asarray(
            sigma.gamma_nu_NP_log_coeff(Q, Y, qt, bT.tolist()), dtype=float
        )

        results[f"W_pert_{qt:.0f}"] = W_pert
        results[f"W_gnu_{qt:.0f}"] = W_gnu
        results[f"W_feff_{qt:.0f}"] = W_feff
        results[f"W_full_{qt:.0f}"] = W_full
        results[f"C_nu_{qt:.0f}"] = C_nu

        # ratios
        R_gnu = W_gnu / W_pert
        R_feff = W_feff / W_pert
        R_full = W_full / W_pert

        # analytic forms
        F_an = feff_analytic(Y, bs, FEFF)
        # Gamma_nu.cpp:117 feeds RAW bT (=bs) to model_gammanu; bStar (L102) is only for
        # the perturbative FO boundary condition, so b0_bmax_nu does NOT enter the NP fn.
        gnu_an = gammanu_analytic(bs, GNU)
        gnu_an_bstar = gammanu_analytic(
            bstar_nu(bs, GNU), GNU
        )  # diagnostic (wrong-conv)
        R_gnu_an = np.exp(C_nu * gnu_an)
        results[f"gnu_analytic_bstar"] = gnu_an_bstar

        # (A) multiplicative factorization
        A = R_full / (R_gnu * R_feff)
        # (B) F_eff form
        B = R_feff / F_an
        # (C) C_nu*gnu form
        C = R_gnu / R_gnu_an

        # focus on the physically-relevant bT window (F_eff meaningful up to bT~a few)
        sel = (bT > 0.05) & (bT < 10.0)

        def rng(x):
            xs = x[sel]
            return float(np.nanmin(xs)), float(np.nanmax(xs))

        print(f"\n=== Q={Q} Y={Y} qT={qt}  (bT in (0.05,10)) ===")
        print(f"  (A) W_full/(W_gnu*W_feff/W_pert) : {rng(A)}   [want 1]")
        print(f"  (B) R_feff / F_eff_analytic      : {rng(B)}   [want 1]")
        print(f"  (C) R_gnu  / exp(C_nu*gnu)       : {rng(C)}   [want 1]")
        # also extracted gamma_nu^NP (should be qT-independent, pure fn of bs)
        with np.errstate(divide="ignore", invalid="ignore"):
            gnu_extracted = np.log(R_gnu) / C_nu
        results[f"gnu_extracted_{qt:.0f}"] = gnu_extracted
        results[f"gnu_analytic"] = gnu_an
        results[f"F_analytic"] = F_an

    np.savez(OUT, **results)
    print(f"\nsaved -> {OUT}")


if __name__ == "__main__":
    main()
