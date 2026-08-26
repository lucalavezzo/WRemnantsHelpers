#!/usr/bin/env python3
"""Where the transition-induced muF shift sits inside the muF member stencil.

Pure arithmetic from SCETlib's own scale formulas (scales_formulas.hpp), no
SCETlib needed. For each bT node it computes

   D_trans  = ln[ muF(live x1,x2,x3) / muF(anchor) ]        the displacement
   D_up/dn  = ln[ muF(member leg +-1) / muF(anchor) ]        the two knots

both at kappa_F = 1, leg 0, in the muf_follows_muB = no branch:

   muF ~ fo_muf * f^leg * f_run(x, mu_star(b0/bT, muf_min/f^leg)/Q, x1,x2,x3)

A 3-point quadratic through (D_dn, 0, D_up) evaluated at D has error
   E = (F'''/6) (D - D_dn) D (D - D_up)
so the bracket C(D) = (D - D_dn) D (D - D_up) is the whole knot-spacing
dependence, with F''' a property of the beam convolution alone. Comparing C at
two spacings predicts the gain from tightening the knots AT THAT VARIATION SIZE
-- which is a different question from the anchor derivative, where the error is
(h^2/6) F'''/F' and always falls as h^2.
"""
import numpy as np

B0 = 2.0 * np.exp(-np.euler_gamma)      # 1.1229189671...
Q = 91.1876
MUF_MIN = 1.40
X1A, X2A, X3A = 0.2, 0.6, 1.0


def g_run(x, x1, x2, x3):
    x = np.asarray(x, float)
    out = np.zeros_like(x)
    out = np.where(x < x3, (x - x3) ** 2 / ((x3 - x1) * (x3 - x2)), 0.0)
    out = np.where(x < x2, 1.0 - (x - x1) ** 2 / ((x2 - x1) * (x3 - x1)), out)
    out = np.where(x < x1, 1.0, out)
    return out


def mu_star(mu, mu_min):          # collins_soper4
    return (mu ** 4 + mu_min ** 4) ** 0.25


def muf(bT, x, x1, x2, x3, leg, f):
    """muF / fo_muf at one node."""
    fac = f ** leg
    y = mu_star(B0 / bT, MUF_MIN / fac) / Q
    g = g_run(x, x1, x2, x3)
    return fac * (g * y + (1.0 - g))


def report(qt, x2live, x1live=X1A, x3live=X3A,
           bTs=(0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0)):
    x = qt / Q
    print(f"\nqT = {qt:g}  (x = {x:.4f}),  transition "
          f"[{x1live}, {x2live}, {x3live}] vs anchor [{X1A}, {X2A}, {X3A}]")
    print(f"{'bT':>7}{'D_trans':>10}"
          + "".join(f"{'D_dn(f=' + s + ')':>15}{'D_up(f=' + s + ')':>15}"
                    f"{'C(f=' + s + ')':>13}" for s in ("2", "sqrt2"))
          + f"{'C2/Csq2':>10}")
    rows = []
    for bT in bTs:
        m0 = muf(bT, x, X1A, X2A, X3A, 0, 2.0)
        mL = muf(bT, x, x1live, x2live, x3live, 0, 2.0)
        Dt = np.log(mL / m0)
        line = f"{bT:>7g}{Dt:>10.4f}"
        Cs = []
        for f in (2.0, np.sqrt(2.0)):
            Du = np.log(muf(bT, x, X1A, X2A, X3A, +1, f) / m0)
            Dd = np.log(muf(bT, x, X1A, X2A, X3A, -1, f) / m0)
            C = (Dt - Dd) * Dt * (Dt - Du)
            Cs.append(C)
            line += f"{Dd:>15.4f}{Du:>15.4f}{C:>13.4e}"
        line += f"{Cs[0] / Cs[1] if Cs[1] else np.nan:>10.2f}"
        print(line)
        rows.append((bT, Dt, Cs[0], Cs[1]))
    return rows


if __name__ == "__main__":
    for qt in (18.0, 22.0, 26.0, 30.0, 38.0):
        for x2 in (0.35, 0.55, 0.75):
            report(qt, x2)
    print("\n--- x1 direction (0.3, 0.6, 0.9), the joint x1/x3 template variation")
    for qt in (22.0, 26.0, 30.0, 38.0):
        report(qt, 0.6, x1live=0.3, x3live=0.9)
