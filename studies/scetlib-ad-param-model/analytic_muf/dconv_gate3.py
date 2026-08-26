#!/usr/bin/env python3
"""GATE 3: the FULL alphas^3 truncated DGLAP evolution of the beam convolutions
over a finite ln(muF) interval, and a Hermite hybrid, against LHAPDF itself.

GATE 2 showed two things.  (i) The analytic DERIVATIVE at D -> 0 needs the P2
(NNLO splitting) column: with P0+P1 alone it is 1-8% off LHAPDF's own grid
evolution, with P2 it is 1e-4 .. 5e-3.  (ii) At the template-sized displacement
D ~ 1.15 ln f the single-derivative-plus-P0xP0 model drifts to 1-2.5%, i.e.
WORSE than the shipped three-knot interpolation, because the D^2 and D^3 terms
of the path-ordered exponential were truncated at order alphas^2.

This script closes that: the path-ordered solution of

   d/dL conv = [a1 P0 + a2 P1 + a3 P2] (x) conv,
   a_n(L) = 2 (alphaS(muF e^L)/4pi)^n

kept to TOTAL order alphas^3 is

   f(D) = f + J1 P0f + J2 P1f + J3 P2f
            + K11 (P0xP0)f + K12 (P0xP1)f + K21 (P1xP0)f
            + T111 (P0xP0xP0)f + O(alphas^4)

   J_n  = int_0^D a_n
   K_mn = int_0^D a_m(L1) int_0^L1 a_n(L2)          (OUTER kernel is the LEFT one)
   T111 = the triple nested integral of a1

and EVERY ONE of those seven objects is an existing SCETlib conv kind
(c_p0, c_p1, c_p2, c_p0p0, c_p0p1, c_p1p0, c_p0p0p0) with grids already on disk
for CT18ZNNLO.  Four of them (p2, p0p1, p1p0, p0p0p0) are not FILLED at
fo_lvl = 2, which is what production runs; they are filled at fo_lvl = 3.

MODELS COMPARED (error on conv[c_delta] as a % of the true response):
  knot3real   the SHIPPED model: Lagrange quadratic through the two members
              Vary.muf actually builds (floor compensation included)
  dglapNLO    J1,J2,K11 only            -- the "P0+P1, nilpotent" of GATE 2
  dglapNNLO   all seven terms above
  hermite     cubic Hermite through both members AND the exact analytic anchor
              derivative -- keeps kappa_F = 1/f, f EXACT while making the
              transition response first-order exact
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

K_DELTA, K_P0, K_I1QQ, K_I1QG, K_P0P0, K_P1, K_I1P0 = 0, 1, 2, 3, 4, 5, 6
K_P0P0P0, K_P0P1, K_P1P0, K_P2 = 11, 12, 13, 14

B0 = 2.0 * math.exp(-np.euler_gamma)
QZ = 91.1876
MUF_MIN = 1.40
X1A, X2A, X3A = 0.2, 0.6, 1.0


def g_run(x, x1, x2, x3):
    if x < x1:
        return 1.0
    if x < x2:
        return 1.0 - (x - x1) ** 2 / ((x2 - x1) * (x3 - x1))
    if x < x3:
        return (x - x3) ** 2 / ((x3 - x1) * (x3 - x2))
    return 0.0


def mu_star(mu, mu_min):
    return (mu ** 4 + mu_min ** 4) ** 0.25


def node_muf(bT, xx, x1, x2, x3, ratio=1.0, fo_muf=QZ):
    y = mu_star(B0 / bT, MUF_MIN / ratio) / QZ
    g = g_run(xx, x1, x2, x3)
    return fo_muf * ratio * (g * y + (1.0 - g))


class Alphas:
    def __init__(self, setname):
        import lhapdf
        self._p = lhapdf.mkPDF(setname, 0)

    def g(self, mu):
        return self._p.alphasQ(mu) / (4.0 * math.pi)


def _cum(y, L):
    return np.concatenate(([0.0], np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(L))))


def evo_coeffs(als, muf0, D, n=128):
    """J1,J2,J3,K11,K12,K21,T111 for the path-ordered solution over [0, D]."""
    if D == 0.0:
        return dict.fromkeys("J1 J2 J3 K11 K12 K21 T111".split(), 0.0)
    L = np.linspace(0.0, D, n + 1)
    g = np.array([als.g(muf0 * math.exp(l)) for l in L])
    a1, a2, a3 = 2 * g, 2 * g ** 2, 2 * g ** 3
    c1, c2 = _cum(a1, L), _cum(a2, L)
    c11 = _cum(a1 * c1, L)
    return dict(J1=c1[-1], J2=c2[-1], J3=_cum(a3, L)[-1],
                K11=c11[-1], K12=_cum(a1 * c2, L)[-1], K21=_cum(a2 * c1, L)[-1],
                T111=_cum(a1 * c11, L)[-1])


def dglap_delta(c3, E, nnlo=True):
    """conv[delta] evolved by D. `c3` is the fo_lvl = 3 conv vector."""
    v = c3[K_DELTA] + E["J1"] * c3[K_P0] + E["J2"] * c3[K_P1] + E["K11"] * c3[K_P0P0]
    if nnlo:
        v += (E["J3"] * c3[K_P2] + E["K12"] * c3[K_P0P1] + E["K21"] * c3[K_P1P0]
              + E["T111"] * c3[K_P0P0P0])
    return v


def dconv_dlnmuf_delta(c3, g):
    """The exact-at-D->0 analytic derivative of conv[delta]."""
    return 2 * g * c3[K_P0] + 2 * g ** 2 * c3[K_P1] + 2 * g ** 3 * c3[K_P2]


def lagrange(nodes, values, D):
    nodes = np.asarray(nodes, float)
    out = 0.0
    for i, xi in enumerate(nodes):
        w = 1.0
        for j, xj in enumerate(nodes):
            if i != j:
                w *= (D - xj) / (xi - xj)
        out = out + w * values[i]
    return out


def hermite(mdn, mup, v_dn, v0, v_up, d0, D):
    """Cubic through (mdn,v_dn), (0,v0), (mup,v_up) with slope d0 at 0.

    Basis: v0 + d0 D + A D^2 + B D^3, A and B fixed by the two members. Keeps
    both members EXACT (so kappa_F = 1/f, f stay exact) and the anchor
    derivative EXACT.
    """
    M = np.array([[mdn ** 2, mdn ** 3], [mup ** 2, mup ** 3]], float)
    r = np.array([v_dn - v0 - d0 * mdn, v_up - v0 - d0 * mup], float)
    try:
        A, Bc = np.linalg.solve(M, r)
    except np.linalg.LinAlgError:
        return float("nan")
    return v0 + d0 * D + A * D ** 2 + Bc * D ** 3


def anl_corr(als, mfa, mdn, mup, v_dn, v0, v_up, c0, D):
    """ANALYTIC EVOLUTION + INTERPOLATED RESIDUAL -- the construction that keeps
    every property that matters.

        conv(D) = conv_anl(D) + Lagrange[R](D),    R(d) = conv_true(d) - conv_anl(d)

    R is known exactly at the two member positions (R(0) = 0 identically), so
    the model is EXACT at kappa_F = 1/f, 1, f -- the members and the central
    value do not move, which is what keeps the 36 non-transition directions
    bit-identical.  Away from the members the interpolation error is the
    quadratic remainder of R, and R is only the ~0.5% residual of the analytic
    evolution rather than the ~6-9% conv response itself, so it is ~20x smaller
    than the remainder the shipped model carries.
    """
    a_dn = dglap_delta(c0, evo_coeffs(als, mfa, mdn))
    a_up = dglap_delta(c0, evo_coeffs(als, mfa, mup))
    a_D = dglap_delta(c0, evo_coeffs(als, mfa, D))
    return a_D + lagrange([mdn, 0.0, mup], [v_dn - a_dn, 0.0, v_up - a_up], D)


def _conf_fo(base, out, fo):
    c = configparser.ConfigParser(inline_comment_prefixes="#")
    c.read(base)
    c["Calculation_settings"]["fixed_order"] = fo
    c["Calculation_settings"]["calculation_piece"] = "sing"
    c["Calculation_settings"].pop("fo_order2_analytic", None)
    with open(out, "w") as f:
        c.write(f)
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="/ceph/submit/data/group/cms/store/user/"
                    "lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("--pid", type=int, default=2)
    ap.add_argument("--side", type=int, default=0)
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
    als = Alphas(args.pdf_set)

    def conv(x, muf):
        return np.asarray(dy.conv_probe(x, muf, args.pid, args.side), float)

    h = math.log(args.knot)
    Y = 0.075
    x = (QZ / 13000.0) * math.exp(Y if args.side == 0 else -Y)
    res = {"h": h, "x": x, "pid": args.pid, "side": args.side, "knot": args.knot}

    # ------------------------------------------------------------------ A ---
    print("\n" + "=" * 104)
    print("A. FINITE-D EVOLUTION OF conv[delta] -- error as a % of the TRUE response")
    print("   plain muF ladder, anchor -> anchor*exp(D). No node geometry involved.")
    print("=" * 104)
    partA = []
    for muf in (3.0, 5.0, 8.0, 13.0, 20.0):
        c0 = conv(x, muf)
        vdn, vup = conv(x, muf / args.knot)[K_DELTA], conv(x, muf * args.knot)[K_DELTA]
        d0 = dconv_dlnmuf_delta(c0, als.g(muf))
        print(f"\n  muF_anchor = {muf:g} GeV, alphaS = {4 * math.pi * als.g(muf):.4f}")
        print(f"{'D/lnf':>7} {'true resp':>12} {'knot3(+-lnf)':>13} {'dglapNLO':>11} "
              f"{'dglapNNLO':>11} {'hermite':>11}")
        for r in (0.1, 0.25, 0.5, 0.75, 1.0, 1.15, 1.5, 1.74, -0.5, -1.0, -1.15):
            D = r * h
            ex = conv(x, muf * math.exp(D))[K_DELTA]
            resp = ex - c0[K_DELTA]
            E = evo_coeffs(als, muf, D)
            m = {"knot3": lagrange([-h, 0.0, h], [vdn, c0[K_DELTA], vup], D),
                 "dglapNLO": dglap_delta(c0, E, nnlo=False),
                 "dglapNNLO": dglap_delta(c0, E, nnlo=True),
                 "hermite": hermite(-h, h, vdn, c0[K_DELTA], vup, d0, D)}
            line = f"{r:7.2f} {resp:12.4e}"
            row = dict(muf=muf, D=D, true_resp=resp)
            for k in ("knot3", "dglapNLO", "dglapNNLO", "hermite"):
                e = m[k] - ex
                row[k] = e
                row[k + "_frac"] = e / resp
                line += f" {100 * e / resp:+12.3f}%"
            print(line)
            partA.append(row)
    res["partA"] = partA

    # ------------------------------------------------------------------ B ---
    print("\n" + "=" * 104)
    print("B. AT THE REAL NODES, REAL MEMBER POSITIONS (floor compensation included)")
    print("=" * 104)
    partB = []
    for qt, x2live, x1live, x3live, lab in (
            (22.0, 0.35, X1A, X3A, "template leg"),
            (26.0, 0.35, X1A, X3A, "template leg"),
            (30.0, 0.35, X1A, X3A, "template leg"),
            (38.0, 0.35, X1A, X3A, "template leg"),
            (30.0, 0.55, X1A, X3A, "near anchor"),
            (30.0, X2A, 0.3, 0.9, "x1,x3 leg")):
        xx = qt / QZ
        print(f"\n  qT = {qt:g} (x = {xx:.4f}), (x1,x2,x3): ({X1A},{X2A},{X3A}) -> "
              f"({x1live},{x2live},{x3live})   [{lab}]")
        print(f"{'bT':>6} {'muF_a':>8} {'D/lnf':>7} {'mem-/lnf':>9} {'mem+/lnf':>9} "
              f"{'where':>5} {'true resp':>12} {'knot3real':>11} {'dglapNNLO':>11} "
              f"{'hermite':>11} {'anl+corr':>11}")
        for bT in (0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0):
            mfa = node_muf(bT, xx, X1A, X2A, X3A, 1.0)
            if mfa < 1.3:
                continue
            mfl = node_muf(bT, xx, x1live, x2live, x3live, 1.0)
            D = math.log(mfl / mfa)
            mdn = math.log(node_muf(bT, xx, X1A, X2A, X3A, 1.0 / args.knot) / mfa)
            mup = math.log(node_muf(bT, xx, X1A, X2A, X3A, args.knot) / mfa)
            c0 = conv(x, mfa)
            ex = conv(x, mfa * math.exp(D))[K_DELTA]
            resp = ex - c0[K_DELTA]
            vdn = conv(x, mfa * math.exp(mdn))[K_DELTA]
            vup = conv(x, mfa * math.exp(mup))[K_DELTA]
            d0 = dconv_dlnmuf_delta(c0, als.g(mfa))
            E = evo_coeffs(als, mfa, D)
            m = {"knot3real": lagrange([mdn, 0.0, mup], [vdn, c0[K_DELTA], vup], D),
                 "dglapNNLO": dglap_delta(c0, E, nnlo=True),
                 "hermite": hermite(mdn, mup, vdn, c0[K_DELTA], vup, d0, D),
                 "anl+corr": anl_corr(als, mfa, mdn, mup, vdn, c0[K_DELTA], vup,
                                      c0, D)}
            where = "OUT" if (D > mup or D < mdn) else "in"
            line = (f"{bT:6g} {mfa:8.3f} {D / h:7.3f} {mdn / h:9.3f} {mup / h:9.3f} "
                    f"{where:>5} {resp:12.4e}")
            row = dict(qt=qt, x1live=x1live, x2live=x2live, x3live=x3live, bT=bT,
                       muf_a=mfa, D=D, mdn=mdn, mup=mup, true_resp=resp, where=where)
            for k in ("knot3real", "dglapNNLO", "hermite", "anl+corr"):
                e = m[k] - ex
                row[k] = e
                row[k + "_frac"] = e / resp if resp else float("nan")
                line += f" {100 * e / resp:+10.3f}%" if resp else f"{'--':>11}"
            print(line)
            partB.append(row)
    res["partB"] = partB

    # ------------------------------------------------------------------ C ---
    print("\n" + "=" * 104)
    print("C. kappa_F ITSELF: the members must stay exact.  D = ln(kappa_F) per node,")
    print("   i.e. exactly the member position, so knot3real and hermite are exact")
    print("   BY CONSTRUCTION; the analytic routes are not, and this sizes that.")
    print("=" * 104)
    partC = []
    for qt in (22.0, 30.0):
        xx = qt / QZ
        print(f"\n  qT = {qt:g}")
        print(f"{'bT':>6} {'muF_a':>8} {'kappa_F':>8} {'D':>8} {'true resp':>12} "
              f"{'dglapNNLO':>11} {'hermite':>10}")
        for bT in (0.2, 0.5, 1.2, 3.0):
            mfa = node_muf(bT, xx, X1A, X2A, X3A, 1.0)
            if mfa < 1.3:
                continue
            for kF in (2.0, 0.5):
                mfl = node_muf(bT, xx, X1A, X2A, X3A, kF)
                D = math.log(mfl / mfa)
                c0 = conv(x, mfa)
                ex = conv(x, mfa * math.exp(D))[K_DELTA]
                resp = ex - c0[K_DELTA]
                E = evo_coeffs(als, mfa, D)
                dg = dglap_delta(c0, E, nnlo=True)
                vdn = conv(x, mfa * math.exp(math.log(node_muf(bT, xx, X1A, X2A, X3A, 1.0 / args.knot) / mfa)))[K_DELTA]
                vup = conv(x, mfa * math.exp(math.log(node_muf(bT, xx, X1A, X2A, X3A, args.knot) / mfa)))[K_DELTA]
                mdn = math.log(node_muf(bT, xx, X1A, X2A, X3A, 1.0 / args.knot) / mfa)
                mup = math.log(node_muf(bT, xx, X1A, X2A, X3A, args.knot) / mfa)
                ac = anl_corr(als, mfa, mdn, mup, vdn, c0[K_DELTA], vup, c0, D)
                print(f"{bT:6g} {mfa:8.3f} {kF:8g} {D:8.4f} {resp:12.4e} "
                      f"{100 * (dg - ex) / resp:+10.3f}% {100 * (ac - ex) / resp:+9.3e}%")
                partC.append(dict(qt=qt, bT=bT, kF=kF, D=D, true_resp=resp,
                                  dglapNNLO=dg - ex))
    res["partC"] = partC

    with open(args.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
