"""Our (SCETlib) full Collins-Soper kernel, evaluated at the lattice point.

    gamma_zeta(bT, mu) = 1/2 * gamma_nu(bT, mu0(bT), mu)            [SCETlib units -> lattice units]

    gamma_nu(bT, mu0, mu) = -4 eta_Gamma(mu0 -> mu)                  cusp evolution mu0 -> mu
                            + C_F sum_n a_s(mu0)^(n+1) g_n(L_b)      FO boundary at mu0, L_b = ln(mu0^2 b*^2 / b0^2)
                            + gamma_nu^NP(bT)                         -lambda_inf tanh(A(bT)), at BARE bT

which is `scet::qT::Gamma_nu::operator()` (src/qT/Gamma_nu.cpp:82-120) with the
fit's scale choices (base.conf of the AD cache / theory corrections):
    mu0 = mu_star(b0/bT, mu0_min = 1 GeV), form collins_soper4 = ((b0/bT)^4 + 1)^(1/4)
    b*  = sextic, b0/bmax_nu = 1 GeV   (NP_model_gammanu::bStar, Gamma_nu.hpp:79-82)
    run_order n3ll (N3+0LL): FO boundary through a_s^3, cusp through Gamma_3, 4-loop beta.

The lattice kernel gamma_q(bT, mu) of 2402.06725 is 2 d ln f / d ln zeta == SCETlib
gamma_zeta == gamma_nu / 2 (see the task LOGBOOK convention map).

Two flavour schemes:
    scheme="fit"     : fixed nf=5 everywhere, alpha_s^(5)(mZ) run with 5 flavours down to
                       1-2 GeV. This is EXACTLY what the fit builds.
    scheme="lattice" : nf=4 everywhere (beta, cusp, boundary coefficients), alpha_s^(4)
                       obtained from alpha_s^(5)(mZ) by 4-loop running to m_b(m_b) and
                       3-loop MSbar decoupling. This is the kernel in the lattice's
                       flavour scheme (2+1+1, no bottom, massless nf=4 matching).
The NP piece is the same function of bT in both.

Running and the cusp integral are solved numerically ("exact"); SCETlib's default
("analytic", re-expanded) differs by <= 2e-3 in gamma_zeta over 0.1-0.9 fm, see
test_our_cs_kernel.py. Units: bT in fm on input, GeV internally.
"""

import numpy as np
from scipy.integrate import quad, solve_ivp

FM_TO_GEVINV = 5.067730716  # 1 fm = 5.0677 GeV^-1  (hbar c = 0.1973269804 GeV fm)
B0 = 2.0 * np.exp(-np.euler_gamma)  # 1.12292
CF, CA, TF = 4.0 / 3.0, 3.0, 0.5
ZETA3 = 1.2020569031595942
MZ = 91.1876
MB_MSBAR = 4.18  # m_b(m_b), PDG

# Coefficients dumped from the SCETlib build this study pins
# (`driver/gamma_zeta_driver coeffs`, scetlib-ad-2da973d): beta_n (dalpha/dlnmu =
# -2 alpha sum beta_n a^(n+1), a = alpha/4pi), quark cusp Gamma_n (incl. C_F), and the
# gamma_nu boundary constants g1, g2 (C_R stripped) and g3 (colour included).
_COEFFS = {
    3: dict(
        beta=[9, 64, 643.833333333333, 12090.3781308037, 130377.906819545],
        cusp=[5.33333333333333, 48.6954431941901, 618.224869391879, 7035.15297393631],
        gnu=[47.2788930641452, 781.602770896161, 14987.0959195938],
    ),
    4: dict(
        beta=[
            8.33333333333333,
            51.3333333333333,
            406.351851851852,
            8035.18641979012,
            58310.5539697607,
        ],
        cusp=[5.33333333333333, 42.7695172682642, 429.50657475221, 3353.35417002304],
        gnu=[55.5751893604415, 917.509550937785, 15301.7369701011],
    ),
    5: dict(
        beta=[
            7.66666666666667,
            38.6666666666667,
            180.907407407407,
            4826.1563287909,
            15470.6122480472,
        ],
        cusp=[5.33333333333333, 36.8435913423382, 239.208033198959, 141.246084502924],
        gnu=[63.8714856567378, 1026.13659713584, 13364.8367227286],
    ),
}
_ORDER = {"nnll": 2, "n3ll": 3, "n4ll": 4}


# ----------------------------------------------------------------------------- coupling
def _beta_rhs(nf, nloop):
    b = _COEFFS[nf]["beta"][:nloop]

    def rhs(lnmu, y):
        a = y[0] / (4 * np.pi)
        return [-2.0 * y[0] * sum(bn * a ** (n + 1) for n, bn in enumerate(b))]

    return rhs


def run_alphas(alpha_start, mu_start, mu, nf, nloop=4):
    """Fixed-nf MSbar running, numerical solution of the nloop beta function."""
    if np.isclose(mu, mu_start):
        return alpha_start
    sol = solve_ivp(
        _beta_rhs(nf, nloop),
        (np.log(mu_start), np.log(mu)),
        [alpha_start],
        rtol=1e-12,
        atol=1e-14,
    )
    return sol.y[0, -1]


def decouple_down(alpha_nf, nl):
    """alpha^(nl)(mu=m_h(m_h)) from alpha^(nl+1)(m_h(m_h)), 3-loop MSbar decoupling
    (Chetyrkin-Kniehl-Steinhauser, hep-ph/9706430)."""
    x = alpha_nf / np.pi
    c2 = 11.0 / 72.0
    c3 = 564731.0 / 124416.0 - 82043.0 / 27648.0 * ZETA3 - 2633.0 / 31104.0 * nl
    return alpha_nf * (1.0 + c2 * x**2 + c3 * x**3)


class Coupling:
    """alpha_s(mu) in a given flavour scheme, from alpha_s^(5)(mZ)."""

    def __init__(self, alphas_mz=0.118, scheme="fit", nloop=4, mb=MB_MSBAR):
        self.scheme, self.nloop = scheme, nloop
        if scheme == "fit":
            self.nf, self.a_ref, self.mu_ref = 5, alphas_mz, MZ
        elif scheme == "lattice":
            a5_mb = run_alphas(alphas_mz, MZ, mb, 5, nloop)
            self.nf, self.a_ref, self.mu_ref = 4, decouple_down(a5_mb, 4), mb
        else:
            raise ValueError(scheme)
        self._cache = {}

    def __call__(self, mu):
        key = round(float(mu), 12)
        if key not in self._cache:
            self._cache[key] = run_alphas(
                self.a_ref, self.mu_ref, mu, self.nf, self.nloop
            )
        return self._cache[key]


# ----------------------------------------------------------------------------- kernel pieces
def mu0_of_bT(bT_gev, mu0_min=1.0, form="collins_soper4"):
    mu = B0 / bT_gev
    if mu0_min == 0:
        return mu
    if form == "collins_soper4":
        return (mu**4 + mu0_min**4) ** 0.25
    if form == "collins_soper":
        return np.hypot(mu, mu0_min)
    raise ValueError(form)


def bstar_over_b0(bT_gev, b0_bmax_nu=1.0):
    """NP_model_gammanu::bStar: returns b*/b0 (GeV^-1), sextic."""
    if b0_bmax_nu == 0:
        return bT_gev / B0
    return ((B0 / bT_gev) ** 6 + b0_bmax_nu**6) ** (-1.0 / 6.0)


def _gnu_fo(Lb, a0, nf, n_order, tnp_nu=0.0, tnp_cusp=0.0):
    """C_F * sum a^(n+1) g_n(Lb), Gamma_nu.hpp:284-337 (Gamma_nu_formulas in newer trees)."""
    c = _COEFFS[nf]
    b0, b1, b2 = c["beta"][:3]
    G0u, G1u, G2u = (g / CF for g in c["cusp"][:3])  # 'universal' = C_R stripped
    g1, g2 = c["gnu"][0], c["gnu"][1]
    if (
        n_order == 3
    ):  # level0 TNP on the 3-loop boundary constant (make_tnps: n_noncusp = run-1)
        g2 = g2 + 4.0 * 2.0 * (4 * CA) ** 3 * (0.25 / (4 * np.pi)) * tnp_nu
    out = 0.0
    if n_order >= 1:
        out += a0 * (Lb * (-2.0 * G0u))
    if n_order >= 2:
        out += a0**2 * (g1 + Lb * (-2.0 * G1u + Lb * (-G0u * b0)))
    if n_order >= 3:
        out += a0**3 * (
            g2
            + Lb
            * (
                -2.0 * G2u
                + 2.0 * g1 * b0
                + Lb * (-G0u * b1 - 2.0 * G1u * b0 + Lb * (-2.0 / 3.0) * G0u * b0 * b0)
            )
        )
    out *= CF
    if n_order >= 4:
        G0, G1, G2 = c["cusp"][:3]
        G3 = c["cusp"][3]
        g0q, g1q, g2q, g3 = 0.0, CF * g1, CF * g2, c["gnu"][2]
        out += a0**4 * (
            g3
            + Lb
            * (
                b2 * g0q
                + 2 * b1 * g1q
                + 3 * b0 * g2q
                - 2 * G3
                + Lb
                * (
                    2.5 * b0 * b1 * g0q
                    + 3 * b0 * b0 * g1q
                    - b2 * G0
                    - 2 * b1 * G1
                    - 3 * b0 * G2
                    + Lb
                    * (
                        b0**3 * g0q
                        - 5.0 / 3.0 * b0 * b1 * G0
                        - 2 * b0 * b0 * G1
                        + Lb * (-0.5 * b0**3 * G0)
                    )
                )
            )
        )
    return out


def _cusp_coeffs(nf, n_order, tnp_cusp=0.0):
    cusp = list(_COEFFS[nf]["cusp"])
    ncoef = n_order + 1 if n_order <= 3 else 4  # N4LL: SCETlib has no 5-loop cusp
    cusp = cusp[:ncoef]
    if n_order == 3:  # level0 TNP on Gamma_3 (make_tnps: n_cusp = run order)
        cusp[3] += CF * 2.0 * (4 * CA) ** 4 * (0.25 / (4 * np.pi)) * tnp_cusp
    return cusp


def eta_cusp(coupling, mu0, mu, nf, n_order, tnp_cusp=0.0):
    """int_{ln mu0}^{ln mu} Gamma_cusp^q[alpha_s(mu')] dln mu'."""
    cusp = _cusp_coeffs(nf, n_order, tnp_cusp)

    def integrand(lnmu):
        a = coupling(np.exp(lnmu)) / (4 * np.pi)
        return sum(g * a ** (n + 1) for n, g in enumerate(cusp))

    return quad(integrand, np.log(mu0), np.log(mu), epsabs=1e-12, epsrel=1e-10)[0]


def gamma_nu_np(bT_gev, lambdas, np_model_nu="tanh_2"):
    """NP_model_gammanu::model_gammanu, gamma_nu units. lambdas: dict with
    lambda_inf_nu, lambda2_nu [GeV^2], lambda4_nu [GeV^4], (lambda6_nu [GeV^6])."""
    linf = lambdas["lambda_inf_nu"]
    if linf == 0:
        return 0.0 * bT_gev
    b2 = bT_gev**2
    arg = (lambdas["lambda2_nu"] + lambdas.get("lambda4_nu", 0.0) * b2) * b2 / linf
    if np_model_nu == "tanh_6":
        arg = arg + lambdas.get("lambda6_nu", 0.0) * b2**3 / linf
    elif np_model_nu != "tanh_2":
        raise ValueError(np_model_nu)
    return -linf * np.tanh(arg)


# ----------------------------------------------------------------------------- public API
def our_cs_kernel(
    bT_fm,
    lambdas,
    alphas_mz=0.118,
    mu=2.0,
    scheme="lattice",
    order="n3ll",
    np_model_nu="tanh_2",
    mu0_min=1.0,
    b0_bmax_nu=1.0,
    form="collins_soper4",
    tnp_nu=0.0,
    tnp_cusp=0.0,
    parts=False,
    coupling=None,
):
    """Full SCETlib CS kernel gamma_zeta(bT, mu) in LATTICE normalisation
    (== gamma_q of 2402.06725 == gamma_nu/2), bT in fm, mu in GeV.

    lambdas: SCETlib gamma_nu-unit NP parameters (the fit's lambda_*_nu); pass
             {"lambda_inf_nu": 0} for the perturbative kernel alone.
    scheme:  "lattice" (nf=4, decoupled alpha_s, default: compare to lattice numbers)
             or "fit" (nf=5 fixed, exactly what the fit uses).
    Returns array gamma_zeta; with parts=True a dict with pert / np / full / mu0 / alphas_mu0.
    """
    bT_fm = np.atleast_1d(np.asarray(bT_fm, dtype=float))
    n_order = _ORDER[order]
    cpl = coupling or Coupling(alphas_mz, scheme, nloop=min(n_order + 1, 5))
    nf = cpl.nf
    pert, mu0s, a0s = [], [], []
    for bT in bT_fm * FM_TO_GEVINV:
        mu0 = mu0_of_bT(bT, mu0_min, form)
        a0 = cpl(mu0) / (4 * np.pi)
        Lb = 2.0 * np.log(mu0 * bstar_over_b0(bT, b0_bmax_nu))
        gnu = -4.0 * eta_cusp(cpl, mu0, mu, nf, n_order, tnp_cusp) + _gnu_fo(
            Lb, a0, nf, n_order, tnp_nu, tnp_cusp
        )
        pert.append(0.5 * gnu)
        mu0s.append(mu0)
        a0s.append(4 * np.pi * a0)
    pert = np.array(pert)
    npk = 0.5 * gamma_nu_np(bT_fm * FM_TO_GEVINV, lambdas, np_model_nu)
    if parts:
        return dict(
            pert=pert,
            np=npk,
            full=pert + npk,
            mu0=np.array(mu0s),
            alphas_mu0=np.array(a0s),
            nf=nf,
        )
    return pert + npk


# Reference tunes (gamma_nu units, as in the SCETlib runcards)
AN_CRIDGE_TUNE = dict(
    lambda_inf_nu=1.6853, lambda2_nu=0.0870, lambda4_nu=0.0074
)  # AN theory.tex / 2506.13874 eq 3.34
