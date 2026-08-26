#!/usr/bin/env python3
"""Where the transition-induced muF shift sits inside a 3- vs 5-knot stencil.

Pure arithmetic from SCETlib's own scale formulas (scales_formulas.hpp); no
SCETlib, no threads, no cache. Extends stencil_geometry.py with the two extra
knots at kappa_F = f^+-1/2 and with BOTH Lagrange remainder brackets:

  3 knots   R3(D) = (D - D_dn) D (D - D_up)                 error = R3 F'''/3!
  5 knots   R5(D) = (D - D_dn)(D - D_din) D (D - D_uin)(D - D_up)
                                                            error = R5 F^(5)/5!

R5/R3 is the only part of the gain that geometry can predict; the rest is
F^(5)/F''', a property of the beam convolution's muF dependence alone and the
same for every qT bin. So a qT bin where R5/R3 is anomalously LARGE is one
where five knots is expected to do worse, and that is a prediction the measured
deviations can be checked against rather than a story fitted to them.

The number that matters is |D| against the knot positions: inside the inner
pair the quartic is interpolating, beyond the outer pair it is extrapolating,
and a quartic extrapolates far worse than a quadratic.
"""
import numpy as np

B0 = 2.0 * np.exp(-np.euler_gamma)
Q = 91.1876
MUF_MIN = 1.40
X1A, X2A, X3A = 0.2, 0.6, 1.0


def g_run(x, x1, x2, x3):
    x = np.asarray(x, float)
    out = np.where(x < x3, (x - x3) ** 2 / ((x3 - x1) * (x3 - x2)), 0.0)
    out = np.where(x < x2, 1.0 - (x - x1) ** 2 / ((x2 - x1) * (x3 - x1)), out)
    out = np.where(x < x1, 1.0, out)
    return out


def mu_star(mu, mu_min):
    return (mu ** 4 + mu_min ** 4) ** 0.25


def muf(bT, x, x1, x2, x3, ratio):
    """muF / fo_muf at one node, for a member staged at kappa_F = ratio."""
    y = mu_star(B0 / bT, MUF_MIN / ratio) / Q
    g = g_run(x, x1, x2, x3)
    return ratio * (g * y + (1.0 - g))


def knots(bT, x, f):
    """[lo_out, hi_out, lo_in, hi_in] positions in ln(muF), relative to anchor."""
    m0 = muf(bT, x, X1A, X2A, X3A, 1.0)
    return np.array([np.log(muf(bT, x, X1A, X2A, X3A, r) / m0)
                     for r in (1.0 / f, f, f ** -0.5, f ** 0.5)]), m0


def report(qt, x2live, x1live=X1A, x3live=X3A, f=2.0,
           bTs=(0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0)):
    x = qt / Q
    L = np.log(f)
    print(f"\nqT = {qt:g} (x = {x:.4f}), transition [{x1live}, {x2live}, "
          f"{x3live}] vs anchor [{X1A}, {X2A}, {X3A}], f = {f:g} (ln f = {L:.4f})")
    print(f"{'bT':>6}{'D':>9}{'D/lnf':>8}{'dn':>8}{'din':>8}{'uin':>8}{'up':>8}"
          f"{'R3':>11}{'R5':>11}{'R5/R3':>9}  where")
    for bT in bTs:
        k, m0 = knots(bT, x, f)
        mL = muf(bT, x, x1live, x2live, x3live, 1.0)
        D = np.log(mL / m0)
        dn, up, din, uin = k
        R3 = (D - dn) * D * (D - up)
        R5 = (D - dn) * (D - din) * D * (D - uin) * (D - up)
        if D > up or D < dn:
            where = "EXTRAPOLATING (outside the outer knots)"
        elif D > uin or D < din:
            where = "between inner and outer knot"
        else:
            where = "inside the inner knots"
        print(f"{bT:>6g}{D:>9.4f}{D / L:>8.3f}{dn:>8.4f}{din:>8.4f}{uin:>8.4f}"
              f"{up:>8.4f}{R3:>11.3e}{R5:>11.3e}{R5 / R3 if R3 else np.nan:>9.4f}"
              f"  {where}")


if __name__ == "__main__":
    import sys
    x2s = [float(v) for v in sys.argv[1:]] or [0.35, 0.55, 0.75]
    for qt in (19.0, 22.0, 26.0, 30.0, 38.0, 60.0):
        for x2 in x2s:
            report(qt, x2)
