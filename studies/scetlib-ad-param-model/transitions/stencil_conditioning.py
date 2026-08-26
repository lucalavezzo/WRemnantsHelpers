#!/usr/bin/env python3
"""CONDITIONING of the muF member stencil, per bT node, from SCETlib's own scale
formulas alone (scales_formulas.hpp; no SCETlib, no cache, no threads).

The kernel builds the beam convolution at the live muF as a Lagrange quadratic
through the THREE muF samples it stores, at their own per-node positions:

    w_up = d (d - m_dn) / (m_up  (m_up - m_dn))
    w_dn = d (d - m_up) / (m_dn  (m_dn - m_up))
    w_0  = 1 - w_up - w_dn
    conv(d) = w_0 conv_0 + w_dn conv_dn + w_up conv_up

`Vary.muf` scales muF by f AND divides the muf_min floor by f, so once the floor
dominates a node the three samples COLLAPSE: m_up, m_dn -> 0 while d, which is
driven by the transition points reshaping the profile, does NOT. The weights then
diverge like d^2 / (m_up m_dn) while the three convolutions they multiply become
equal, and `ad_nd.conv` is stored as FLOAT. So the interpolation degenerates into
a catastrophic cancellation amplified by a huge weight -- noise, not a small
error.

This prints, per node, d, m_dn, m_up, the weights, and

    noise ~ (|w_dn| + |w_up| + |w_0|) * 6e-8

the float-epsilon floor on |conv(d)/conv_0 - 1| that the weights impose, against
the response the node actually has, |d| * |dlnconv/dlnmuF| ~ |d| * 2 g P0/f
(taken as |d| x 0.05, the measured order at these scales). Where noise exceeds
response, the node's muF response is dominated by rounding.

The degeneracy guard in eb60a04 is ABSOLUTE, eps = 1e-8 ln f, so it does not
fire here: the collapsed positions are far above it.
"""
import numpy as np

B0 = 2.0 * np.exp(-np.euler_gamma)
Q = 91.1876
MUF_MIN = 1.40
X1A, X2A, X3A = 0.2, 0.6, 1.0
FLOAT_EPS = 6e-8
DLNCONV = 0.05      # order of |d ln conv / d ln muF| at these scales


def g_run(x, x1, x2, x3):
    x = np.asarray(x, float)
    out = np.where(x < x3, (x - x3) ** 2 / ((x3 - x1) * (x3 - x2)), 0.0)
    out = np.where(x < x2, 1.0 - (x - x1) ** 2 / ((x2 - x1) * (x3 - x1)), out)
    out = np.where(x < x1, 1.0, out)
    return out


def muf(bT, x, x1, x2, x3, ratio):
    y = (( (B0 / bT) ** 4 + (MUF_MIN / ratio) ** 4) ** 0.25) / Q
    g = g_run(x, x1, x2, x3)
    return ratio * (g * y + (1.0 - g))


def report(qt, x2live, x1live=X1A, x3live=X3A, f=2.0,
           bTs=(0.05, 0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0, 8.0)):
    x = qt / Q
    L = np.log(f)
    print(f"\nqT = {qt:g} (x = qT/Q = {x:.4f}), live [{x1live}, {x2live}, "
          f"{x3live}] vs anchor [{X1A}, {X2A}, {X3A}], f = {f:g}")
    print(f"{'bT':>6}{'muF_0':>9}{'d':>11}{'m_dn':>11}{'m_up':>11}"
          f"{'d/|m_up|':>10}{'w_dn':>11}{'w_up':>11}{'w_0':>11}"
          f"{'noise':>10}{'resp':>10}{'n/r':>9}")
    for bT in bTs:
        m0 = muf(bT, x, X1A, X2A, X3A, 1.0)
        mdn = np.log(muf(bT, x, X1A, X2A, X3A, 1.0 / f) / m0)
        mup = np.log(muf(bT, x, X1A, X2A, X3A, f) / m0)
        d = np.log(muf(bT, x, x1live, x2live, x3live, 1.0) / m0)
        sep = mup - mdn
        if abs(mup) > 1e-8 * L and abs(mdn) > 1e-8 * L and abs(sep) > 1e-8 * L:
            wup = d * (d - mdn) / (mup * sep)
            wdn = d * (d - mup) / (mdn * (-sep))
        else:
            wup = wdn = 0.0
        w0 = 1.0 - wup - wdn
        noise = (abs(wdn) + abs(wup) + abs(w0)) * FLOAT_EPS
        resp = abs(d) * DLNCONV
        print(f"{bT:>6g}{m0 * Q:>9.3f}{d:>+11.3e}{mdn:>+11.3e}{mup:>+11.3e}"
              f"{abs(d) / max(abs(mup), 1e-300):>10.2f}{wdn:>+11.3e}"
              f"{wup:>+11.3e}{w0:>+11.3e}{noise:>10.2e}{resp:>10.2e}"
              f"{noise / max(resp, 1e-300):>9.2f}")


if __name__ == "__main__":
    import sys
    x2s = [float(v) for v in sys.argv[1:]] or [0.35]
    for qt in (19.0, 22.0, 26.0, 30.0, 38.0):
        for x2 in x2s:
            report(qt, x2)
