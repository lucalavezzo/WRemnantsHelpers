#!/usr/bin/env python3
"""GATE 5: how the evolution coefficients must be computed, and with WHOSE alphaS.

GATE 4 found the endpoint closed forms (one- or two-loop, fixed nf) are NOT good
enough: they are 0.3-0.6% off the numerically integrated coefficients above
muF ~ 6 GeV and 5-14% off below it, because the interval crosses the b (and c)
thresholds where LHAPDF's alphaS changes nf and no fixed-nf closed form can
follow.  0.3% on J1 is 0.3% on the response, which is 6x the 0.05% the exact
integrals reach.

THE FIX TESTED HERE: model g(L) = alphaS(muF e^L)/4pi as a QUADRATIC in L through
three alphaS evaluations (L = 0, D/2, D) and integrate that exactly.  Everything
then has a closed polynomial form, three alphaS calls per node, no quadrature
loop on the clad tape, and thresholds are followed as well as a quadratic can.

    g(u) = A + B u + C u^2,  A = g(0), B, C from g(D/2), g(D)
    P_n(u) = int_0^u 2 g^n            (polynomials, integrated exactly)
    J_n = P_n(D)
    K11 = J1^2/2,  T111 = J1^3/6      (exact for ANY g: reparametrise by
                                       s = int_0^L 2g, they become int s ds)
    K12 = int_0^D 2 g P_2,  K21 = int_0^D 2 g^2 P_1   (5-point Gauss-Legendre,
                                       which is exact for these polynomials)

ALSO MEASURED: whose alphaS.  The conv objects are LHAPDF grids evolved with
LHAPDF's OWN variable-nf alphaS, while the SCETlib kernel runs a FIXED nf = 5
solution from alphaS(mZ) = 0.118.  Below m_b those are not the same function.
"""
import argparse
import configparser
import json
import math
import os
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dconv_gate3 import (K_DELTA, QZ, X1A, X2A, X3A, Alphas, _conf_fo,
                         dglap_delta, evo_coeffs, lagrange, node_muf)

# 5-point Gauss-Legendre on [-1, 1]
GL_X = np.array([-0.9061798459386640, -0.5384693101056831, 0.0,
                 0.5384693101056831, 0.9061798459386640])
GL_W = np.array([0.2369268850561891, 0.4786286704993665, 0.5688888888888889,
                 0.4786286704993665, 0.2369268850561891])


class AlphasSCET:
    """Fixed-nf, N-loop running from alphaS(mu0) -- the kernel's own solution."""

    def __init__(self, nf=5, mu0=91.1876, as0=0.118, loops=4):
        self.b = [11.0 - 2.0 * nf / 3.0,
                  102.0 - 38.0 * nf / 3.0,
                  2857.0 / 2.0 - 5033.0 * nf / 18.0 + 325.0 * nf * nf / 54.0,
                  29243.0 - 6946.3 * nf + 405.089 * nf * nf + 1.49931 * nf ** 3]
        self.loops, self.mu0, self.as0 = loops, mu0, as0
        self._cache = {}

    def _rhs(self, lnmu, a):
        g = a / (4.0 * math.pi)
        s = sum(self.b[n] * g ** (n + 1) for n in range(self.loops))
        return -2.0 * a * s

    def alphas(self, mu):
        key = round(math.log(mu), 10)
        if key in self._cache:
            return self._cache[key]
        t1 = math.log(mu)
        t0 = math.log(self.mu0)
        n = max(64, int(400 * abs(t1 - t0)) + 64)
        hstep = (t1 - t0) / n
        a = self.as0
        t = t0
        for _ in range(n):                       # RK4
            k1 = self._rhs(t, a)
            k2 = self._rhs(t + hstep / 2, a + hstep * k1 / 2)
            k3 = self._rhs(t + hstep / 2, a + hstep * k2 / 2)
            k4 = self._rhs(t + hstep, a + hstep * k3)
            a += hstep * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
            t += hstep
        self._cache[key] = a
        return a

    def g(self, mu):
        return self.alphas(mu) / (4.0 * math.pi)


def evo_coeffs_poly(als, muf0, D):
    """Quadratic-in-L model of g, integrated exactly.  Three alphaS calls."""
    if D == 0.0:
        return dict.fromkeys("J1 J2 J3 K11 K12 K21 T111".split(), 0.0)
    A = als.g(muf0)
    gm = als.g(muf0 * math.exp(0.5 * D))
    gD = als.g(muf0 * math.exp(D))
    B = (4.0 * gm - 3.0 * A - gD) / D
    C = 2.0 * (A - 2.0 * gm + gD) / (D * D)

    def gpoly(u):
        return A + B * u + C * u * u

    def P(n, u):                       # int_0^u 2 g^n, by GL (exact: polynomial)
        xm, xr = 0.5 * u, 0.5 * u
        return xr * np.sum(GL_W * 2.0 * gpoly(xm + xr * GL_X) ** n)

    J1, J2, J3 = P(1, D), P(2, D), P(3, D)
    xm = xr = 0.5 * D
    us = xm + xr * GL_X
    gv = gpoly(us)
    P1v = np.array([P(1, u) for u in us])
    P2v = np.array([P(2, u) for u in us])
    K12 = xr * np.sum(GL_W * 2.0 * gv * P2v)
    K21 = xr * np.sum(GL_W * 2.0 * gv * gv * P1v)
    return dict(J1=J1, J2=J2, J3=J3, K11=0.5 * J1 * J1, K12=K12, K21=K21,
                T111=J1 ** 3 / 6.0)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="/ceph/submit/data/group/cms/store/user/"
                    "lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf")
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("--pdf-set", default="CT18ZNNLO")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    import scetlib_qT  # noqa: F401
    from scetlib_run import config as sl_config

    tmpdir = os.path.dirname(os.path.abspath(args.out))
    c3 = configparser.ConfigParser(inline_comment_prefixes="#")
    c3.read(os.path.join(os.environ["SCETLIB_SRC"], "prod", "scetlib_run", "defaults.conf"))
    c3.read(_conf_fo(args.base, os.path.join(tmpdir, "_n3lo.conf"), "n3lo"))
    dy = sl_config.configure_calculation(c3)[4]
    lh = Alphas(args.pdf_set)
    sc = AlphasSCET(nf=5, mu0=91.1876, as0=0.118, loops=4)
    h = math.log(args.knot)
    res = {}

    print("\n" + "=" * 78)
    print("A. WHOSE alphaS: LHAPDF (variable nf, what evolved the grids) vs the")
    print("   kernel's fixed-nf=5 4-loop solution from alphaS(mZ) = 0.118")
    print("=" * 78)
    print(f"{'mu':>8} {'LHAPDF':>10} {'SCETlib nf5':>12} {'rel diff':>10}")
    partA = []
    for mu in (1.5, 2.0, 3.0, 4.0, 4.75, 6.0, 8.0, 13.0, 20.0, 45.0, 91.1876):
        a, b = lh.g(mu) * 4 * math.pi, sc.alphas(mu)
        print(f"{mu:8.3f} {a:10.5f} {b:12.5f} {b / a - 1:+10.2e}")
        partA.append(dict(mu=mu, lhapdf=a, scet=b))
    res["partA"] = partA

    print("\n" + "=" * 78)
    print("B. QUADRATIC-g COEFFICIENTS vs a 256-point numerical integration")
    print("   (both with LHAPDF alphaS, so this isolates the g model alone)")
    print("=" * 78)
    print(f"{'muF':>7} {'D/lnf':>7} {'J1':>10} {'J2':>10} {'J3':>10} {'K12':>10} "
          f"{'K21':>10}")
    partB = []
    for muf in (2.0, 3.0, 6.0, 13.0, 20.0):
        for r in (0.5, 1.0, 1.15, 1.74, -1.0, -1.74):
            D = r * h
            En = evo_coeffs(lh, muf, D, n=256)
            Ep = evo_coeffs_poly(lh, muf, D)
            line = f"{muf:7.2f} {r:7.2f}"
            for k in ("J1", "J2", "J3", "K12", "K21"):
                line += f" {Ep[k] / En[k] - 1:+10.2e}"
            print(line)
            partB.append(dict(muf=muf, D=D, **{k: Ep[k] / En[k] - 1 for k in En}))
    res["partB"] = partB

    print("\n" + "=" * 78)
    print("C. THE MODEL, with the quadratic-g coefficients, at the real nodes.")
    print("   'anl+corr(LH)' uses LHAPDF alphaS, 'anl+corr(SC)' the kernel's own.")
    print("   error on conv[delta] as a % of the true response")
    print("=" * 78)
    partC = []
    x = (QZ / 13000.0) * math.exp(0.075)
    for qt, x1l, x2l, x3l, lab in ((22.0, X1A, 0.35, X3A, "template leg"),
                                   (26.0, X1A, 0.35, X3A, "template leg"),
                                   (30.0, X1A, 0.35, X3A, "template leg"),
                                   (38.0, X1A, 0.35, X3A, "template leg"),
                                   (30.0, X1A, 0.55, X3A, "near anchor"),
                                   (30.0, 0.3, X2A, 0.9, "x1,x3 leg")):
        xx = qt / QZ
        print(f"\n  qT = {qt:g}  ({x1l},{x2l},{x3l})   [{lab}]")
        print(f"{'bT':>6} {'muF_a':>8} {'D/lnf':>7} {'true resp':>12} "
              f"{'knot3real':>11} {'anl+corr(LH)':>13} {'anl+corr(SC)':>13}")
        for bT in (0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0):
            mfa = node_muf(bT, xx, X1A, X2A, X3A, 1.0)
            if mfa < 1.3:
                continue
            D = math.log(node_muf(bT, xx, x1l, x2l, x3l, 1.0) / mfa)
            mdn = math.log(node_muf(bT, xx, X1A, X2A, X3A, 1.0 / args.knot) / mfa)
            mup = math.log(node_muf(bT, xx, X1A, X2A, X3A, args.knot) / mfa)
            c0 = np.asarray(dy.conv_probe(x, mfa, 2, 0), float)
            ex = np.asarray(dy.conv_probe(x, mfa * math.exp(D), 2, 0), float)[K_DELTA]
            resp = ex - c0[K_DELTA]
            vdn = np.asarray(dy.conv_probe(x, mfa * math.exp(mdn), 2, 0), float)[K_DELTA]
            vup = np.asarray(dy.conv_probe(x, mfa * math.exp(mup), 2, 0), float)[K_DELTA]
            row = dict(qt=qt, bT=bT, muf_a=mfa, D=D, true_resp=resp)
            line = f"{bT:6g} {mfa:8.3f} {D / h:7.3f} {resp:12.4e}"
            k3 = lagrange([mdn, 0.0, mup], [vdn, c0[K_DELTA], vup], D)
            row["knot3real"] = k3 - ex
            line += f" {100 * (k3 - ex) / resp:+10.3f}%"
            for tag, als in (("LH", lh), ("SC", sc)):
                aD = dglap_delta(c0, evo_coeffs_poly(als, mfa, D))
                adn = dglap_delta(c0, evo_coeffs_poly(als, mfa, mdn))
                aup = dglap_delta(c0, evo_coeffs_poly(als, mfa, mup))
                v = aD + lagrange([mdn, 0.0, mup], [vdn - adn, 0.0, vup - aup], D)
                row["anlcorr_" + tag] = v - ex
                line += f" {100 * (v - ex) / resp:+12.3f}%"
            print(line)
            partC.append(row)
    res["partC"] = partC

    with open(args.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
