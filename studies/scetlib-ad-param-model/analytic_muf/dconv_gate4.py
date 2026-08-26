#!/usr/bin/env python3
"""GATE 4: can the nested evolution integrals be written in CLOSED FORM, and does
the result hold across flavours, beams and rapidity?

Two things the kernel needs before this can be implemented.

(1) THE INTEGRALS MUST BE ANALYTIC IN D.  The path-ordered coefficients
    J1,J2,J3,K11,K12,K21,T111 are integrals of alphaS over [0, D] in ln muF, and
    D is a live function of the transition points, so a quadrature would put
    a loop on the clad tape.  With one-loop running (dg/dL = -2 b0 g^2, g =
    alphaS/4pi) they all collapse to closed forms in g0 = g(muF_anchor),
    gD = g(muF_anchor e^D) and L = ln(g0/gD):

        J1  = L/b0                     K11  = J1^2/2
        J2  = (g0-gD)/b0               K12  = [g0 L - g0 + gD]/b0^2
        J3  = (g0^2-gD^2)/(2 b0)       K21  = [g0 - gD(1+L)]/b0^2
                                       T111 = L^3/(6 b0^3)

    Both g0 and gD come from the SAME alphas_run the kernel already calls, so
    the higher-loop running is carried by the endpoints and only the SHAPE in
    between is one-loop.  This part measures that against a numerical
    integration of LHAPDF's own alphaS.

(2) FLAVOUR / BEAM / RAPIDITY ROBUSTNESS.  Part A of GATE 3 was one (x, pid,
    side).  The conv kinds are flavour-summed per channel and beam, so the same
    test has to hold for down-type, for the second beam and at high |Y|.
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

from dconv_gate3 import (K_DELTA, K_P0, K_P0P0, K_P1, K_P0P0P0, K_P0P1, K_P1P0,
                         K_P2, QZ, X1A, X2A, X3A, Alphas, _conf_fo, dglap_delta,
                         evo_coeffs, lagrange, node_muf)


def evo_coeffs_closed(als, muf0, D, b0, b1=None, loops=2):
    """Closed forms for the path-ordered coefficients from the ENDPOINT couplings.

    Everything is an integral of a power of g over [0, D] in ln muF, so changing
    variable to g with dg/dL = -2 g^2 (b0 + b1 g + ...) turns each one into an
    elementary integral in g between g0 = g(muF) and gD = g(muF e^D).  Taking
    the endpoints from the TRUE alphaS means the higher-loop running is carried
    exactly and only the SHAPE between them is truncated.

        J1 = (1/b0) ln[ g0 (b0+b1 gD) / (gD (b0+b1 g0)) ]
        J2 = (1/b1) ln[ (b0+b1 g0) / (b0+b1 gD) ]
        J3 = (1/b1) [ (g0-gD) - (b0/b1) ln((b0+b1 g0)/(b0+b1 gD)) ]
        K11 = J1^2/2        T111 = J1^3/6        (EXACT at any loop order:
                            reparametrising by s = int_0^L a1 makes them
                            int s ds and int s^2/2 ds)
        K12 = J1^2 (g0 Lm - g0 + gD)/Lm^2      Lm = ln(g0/gD)
        K21 = J1^2 (g0 - gD(1+Lm))/Lm^2
    The last two use the one-loop SHAPE g(s) = g0 exp(-b0e s) but with the
    effective slope b0e = Lm/J1 fixed by the exact endpoints, so they are exact
    in the endpoints and one-loop only in the interior.  They are the
    alphas^3 D^2 terms, ~2% of the response, so a one-loop interior costs
    O(1e-4) of it.  Both have a removable 0/0 at Lm -> 0, expanded below.
    """
    if D == 0.0:
        return dict.fromkeys("J1 J2 J3 K11 K12 K21 T111".split(), 0.0)
    if b1 is None:
        b1 = 0.0
    g0 = als.g(muf0)
    gD = als.g(muf0 * math.exp(D))
    if loops >= 2 and b1 != 0.0:
        A0, AD = b0 + b1 * g0, b0 + b1 * gD
        W = math.log(A0 / AD)
        J1 = math.log(g0 * AD / (gD * A0)) / b0
        J2 = W / b1
        J3 = ((g0 - gD) - (b0 / b1) * W) / b1
    else:
        Lm = math.log(g0 / gD)
        J1, J2, J3 = Lm / b0, (g0 - gD) / b0, (g0 ** 2 - gD ** 2) / (2 * b0)
    Lm = math.log(g0 / gD)
    if abs(Lm) > 1e-6:
        f12 = (g0 * Lm - g0 + gD) / Lm ** 2
        f21 = (g0 - gD * (1 + Lm)) / Lm ** 2
    else:                                    # removable 0/0: both -> g0/2
        f12 = f21 = 0.5 * g0
    return dict(J1=J1, J2=J2, J3=J3, K11=0.5 * J1 ** 2, K12=J1 ** 2 * f12,
                K21=J1 ** 2 * f21, T111=J1 ** 3 / 6.0)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="/ceph/submit/data/group/cms/store/user/"
                    "lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf")
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("--nf", type=int, default=5)
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
    b0 = 11.0 - 2.0 * args.nf / 3.0
    b1 = 102.0 - 38.0 * args.nf / 3.0
    h = math.log(args.knot)
    res = {"b0": b0, "h": h}

    print(f"\nb0 = 11 - 2nf/3 = {b0:.4f}, b1 = 102 - 38nf/3 = {b1:.4f}"
          f"  for nf = {args.nf}")

    # ------------------------------------------------------------------ A ---
    print("\n" + "=" * 96)
    print("A. CLOSED-FORM vs NUMERICALLY-INTEGRATED evolution coefficients")
    print("   (relative difference of each coefficient; and of the resulting")
    print("    conv[delta] response, which is the number that matters)")
    print("=" * 96)
    partA = []
    x = (QZ / 13000.0) * math.exp(0.075)
    print(f"{'muF':>7} {'D/lnf':>7} {'J1':>10} {'J2':>10} {'J3':>10} {'K11':>10} "
          f"{'K12':>10} {'K21':>10} {'T111':>10} {'resp[delta]':>12}")
    for muf in (2.0, 3.0, 6.0, 13.0, 20.0):
        c0 = dy.conv_probe(x, muf, 2, 0)
        c0 = np.asarray(c0, float)
        for r in (0.5, 1.0, 1.15, 1.74, -1.0, -1.74):
            D = r * h
            En = evo_coeffs(als, muf, D, n=256)
            Ec = evo_coeffs_closed(als, muf, D, b0, b1)
            rn = dglap_delta(c0, En) - c0[K_DELTA]
            rc = dglap_delta(c0, Ec) - c0[K_DELTA]
            line = f"{muf:7.2f} {r:7.2f}"
            for k in ("J1", "J2", "J3", "K11", "K12", "K21", "T111"):
                line += f" {Ec[k] / En[k] - 1:+10.2e}"
            line += f" {rc / rn - 1:+12.2e}"
            print(line)
            partA.append(dict(muf=muf, D=D, resp_rel=rc / rn - 1,
                              **{k: Ec[k] / En[k] - 1 for k in En}))
    res["partA"] = partA

    # ------------------------------------------------------------------ B ---
    print("\n" + "=" * 96)
    print("B. FLAVOUR / BEAM / RAPIDITY ROBUSTNESS of the four models")
    print("   qT = 30, x2: 0.6 -> 0.35, worst |error| over bT = 0.1 .. 5, in % of")
    print("   the node's true conv[delta] response.  CLOSED-FORM coefficients.")
    print("=" * 96)
    print(f"{'Y':>6} {'pid':>5} {'side':>5} {'x':>9} {'knot3real':>11} "
          f"{'dglapNNLO':>11} {'anl+corr':>11}")
    partB = []
    qt, x2live = 30.0, 0.35
    xx = qt / QZ
    for Y in (0.075, 0.8, 1.75, 2.25):
        for pid, side in ((2, 0), (1, 0), (-2, 1), (-1, 1), (3, 0)):
            xv = (QZ / 13000.0) * math.exp(Y if side == 0 else -Y)
            worst = {"knot3real": 0.0, "dglapNNLO": 0.0, "anl+corr": 0.0}
            for bT in (0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0):
                mfa = node_muf(bT, xx, X1A, X2A, X3A, 1.0)
                if mfa < 1.3:
                    continue
                D = math.log(node_muf(bT, xx, X1A, x2live, X3A, 1.0) / mfa)
                mdn = math.log(node_muf(bT, xx, X1A, X2A, X3A, 1.0 / args.knot) / mfa)
                mup = math.log(node_muf(bT, xx, X1A, X2A, X3A, args.knot) / mfa)
                c0 = np.asarray(dy.conv_probe(xv, mfa, pid, side), float)
                ex = np.asarray(dy.conv_probe(xv, mfa * math.exp(D), pid, side), float)[K_DELTA]
                resp = ex - c0[K_DELTA]
                if abs(resp) < 1e-12:
                    continue
                vdn = np.asarray(dy.conv_probe(xv, mfa * math.exp(mdn), pid, side), float)[K_DELTA]
                vup = np.asarray(dy.conv_probe(xv, mfa * math.exp(mup), pid, side), float)[K_DELTA]
                aD = dglap_delta(c0, evo_coeffs_closed(als, mfa, D, b0, b1))
                adn = dglap_delta(c0, evo_coeffs_closed(als, mfa, mdn, b0, b1))
                aup = dglap_delta(c0, evo_coeffs_closed(als, mfa, mup, b0, b1))
                m = {"knot3real": lagrange([mdn, 0.0, mup], [vdn, c0[K_DELTA], vup], D),
                     "dglapNNLO": aD,
                     "anl+corr": aD + lagrange([mdn, 0.0, mup],
                                               [vdn - adn, 0.0, vup - aup], D)}
                for k in worst:
                    worst[k] = max(worst[k], abs(100 * (m[k] - ex) / resp))
            print(f"{Y:6.3f} {pid:5d} {side:5d} {xv:9.5f} "
                  f"{worst['knot3real']:10.3f}% {worst['dglapNNLO']:10.3f}% "
                  f"{worst['anl+corr']:10.3f}%")
            partB.append(dict(Y=Y, pid=pid, side=side, x=xv, **worst))
    res["partB"] = partB

    with open(args.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
