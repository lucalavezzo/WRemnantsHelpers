#!/usr/bin/env python3
"""CONDITIONING of every candidate residual interpolant, per bT node, from
SCETlib's own scale formulas alone -- no SCETlib, no cache, no threads.

The shipped construction is, algebraically,
    cvi(D) = conv(0) + delta(D) + [ w_dn(D) r(a) + w_up(D) r(b) ],
    r(x) = conv(x) - conv(0) - delta(x),   a = mfk_dn < 0 < b = mfk_up,
with (w_dn, w_up) the quadratic Lagrange weights.  Write r's Taylor series as
    r(x) = e1 x + e2 x^2 / 2 + C x^3 + O(x^4);
e1 and e2 are the analytic model's OWN truncation error (they would vanish for
an exact delta) and C is the part delta cannot know.  Then for each candidate
form the rendering of each power is EXACT ARITHMETIC in (a, b, D):

  form      basis        exact on      amplification of the terms it misses
  quad      D , D^2      e1, e2        cubic: renders C D^3 as C D (D(a+b) - ab)
  cubic     D^2, D^3     e2, C         e1  : A1c = |D (D-a-b) / (ab)|
  quartic   D^3, D^4     C  (, D^4)    e1  : A1q = |D^2/(b-a) [(b-D)/a^2
                                                              + (D-a)/b^2]|
                                       e2  : A2q = |D (a+b-D) / (ab)|

All three are 1 at their own member and 0 at the other two, so knot exactness
(kappa_F = 1/f, 1, f bit-identical) holds for each -- and therefore for ANY
blend of them, which is the point.

Printed per node: the geometry, the amplifications, and the blend fraction
    theta = min(1, T / max(|A1q - 1|, |A2q - 1|))
which caps the quartic's amplification of delta's own truncation error at T.
"""
import numpy as np

B0 = 1.1229189671337702          # 2 exp(-gamma_E)
Q = 91.1876
MUF_MIN = 1.40
X1A, X2A, X3A = 0.2, 0.6, 1.0
VARY = 1.0                       # 2^v_muf, v_muf = 0 for the nominal muF pair
TOL = 1.0


def g_run(x, x1, x2, x3):
    if x < x1:
        return 1.0
    if x < x2:
        return 1.0 - (x - x1) ** 2 / ((x2 - x1) * (x3 - x1))
    if x < x3:
        return (x - x3) ** 2 / ((x3 - x1) * (x3 - x2))
    return 0.0


def mu_star(mu, mu_min):
    if mu_min == 0.0:
        return mu
    return (mu ** 4 + mu_min ** 4) ** 0.25       # collins_soper4


def muf(bT, x, x1, x2, x3, fstep):
    """fo_muf * fstep * f_run(x, mu_star(b0/bT, muf_min/(vary*fstep))/Q).

    fstep = 1 is mf_0, f is mf_u, 1/f is mf_d -- exactly the kernel's three.
    fo_muf = Q here (kappa_F = 1); only ln ratios are used.
    """
    y = mu_star(B0 / bT, MUF_MIN / (VARY * fstep)) / Q
    g = g_run(x, x1, x2, x3)
    return fstep * (g * y + (1.0 - g))


def geom(qt, bT, x1L, x2L, x3L, f):
    x = qt / Q
    m0 = muf(bT, x, X1A, X2A, X3A, 1.0)
    a = np.log(muf(bT, x, X1A, X2A, X3A, 1.0 / f) / m0)
    b = np.log(muf(bT, x, X1A, X2A, X3A, f) / m0)
    # the live muF uses the LIVE transition points and the SAME floor as mf_0
    d = np.log(muf(bT, x, x1L, x2L, x3L, 1.0) / m0)
    return d, a, b, m0 * Q


def forms(d, a, b):
    sep = b - a
    out = {}
    out["quad"] = (d * (d - b) / (a * (a - b)), d * (d - a) / (b * (b - a)))
    out["cubic"] = (d * d * (d - b) / (a * a * (a - b)),
                    d * d * (d - a) / (b * b * (b - a)))
    out["quartic"] = (d ** 3 * (b - d) / (sep * a ** 3),
                      d ** 3 * (d - a) / (sep * b ** 3))
    return out


def amps(d, a, b):
    sep = b - a
    A1c = abs(d * (d - a - b) / (a * b))
    A1q = abs(d * d / sep * ((b - d) / a ** 2 + (d - a) / b ** 2))
    A2q = abs(d * (a + b - d) / (a * b))
    # the quadratic's rendering of the cubic content, as a fraction of truth
    rho = (d * (a + b) - a * b) / (d * d) if d else 0.0
    return A1c, A1q, A2q, rho


def theta(d, a, b, tol=TOL):
    _, A1q, A2q, _ = amps(d, a, b)
    A = max(abs(A1q - 1.0), abs(A2q - 1.0))
    return min(1.0, tol / A) if A > 0 else 1.0


def report(qt, x1L, x2L, x3L, f=2.0,
           bTs=(0.05, 0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0, 8.0)):
    print(f"\nqT = {qt:g} (x = {qt/Q:.4f}), live [{x1L}, {x2L}, {x3L}] vs "
          f"anchor [{X1A}, {X2A}, {X3A}], f = {f:g}")
    print(f"{'bT':>6}{'muF_0':>8}{'d':>10}{'a':>10}{'b':>10}{'|d/a|':>7}"
          f"{'|d/b|':>7}{'A1cub':>9}{'A1quart':>10}{'A2quart':>10}"
          f"{'rho':>8}{'theta':>8}")
    for bT in bTs:
        d, a, b, m0 = geom(qt, bT, x1L, x2L, x3L, f)
        if min(abs(a), abs(b), abs(b - a)) < 1e-8 * np.log(f):
            print(f"{bT:>6g}{m0:>8.3f}{d:>+10.3e}{a:>+10.3e}{b:>+10.3e}"
                  f"{'DEGENERATE (guard fires, w = 0)':>60}")
            continue
        A1c, A1q, A2q, rho = amps(d, a, b)
        th = theta(d, a, b)
        print(f"{bT:>6g}{m0:>8.3f}{d:>+10.3e}{a:>+10.3e}{b:>+10.3e}"
              f"{abs(d/a):>7.2f}{abs(d/b):>7.2f}{A1c:>9.2f}{A1q:>10.2f}"
              f"{A2q:>10.2f}{rho:>8.2f}{th:>8.3f}")


LEGS_DEF = {
    "x2_035": (X1A, 0.35, X3A),
    "x2_055": (X1A, 0.55, X3A),
    "x2_075": (X1A, 0.75, X3A),
    "x1x3": (0.3, X2A, 0.9),
}

if __name__ == "__main__":
    import sys
    QTS = (19.0, 22.0, 26.0, 30.0, 38.0, 50.0, 70.0, 95.0)
    LEGS = LEGS_DEF
    only = sys.argv[1:] or list(LEGS)
    for name in only:
        print("\n" + "=" * 100)
        print(f"LEG {name}")
        print("=" * 100)
        for qt in QTS:
            report(qt, *LEGS[name])
