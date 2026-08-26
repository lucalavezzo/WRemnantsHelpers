#!/usr/bin/env python3
"""GATE 6: HOW MANY extra conv kinds does the analytic route actually need?

The full alphas^3 evolution uses seven conv kinds; at the production fo_lvl = 2
FOUR of them (p2, p0p1, p1p0, p0p0p0) are not filled, and filling them means
loading 16 more beamfunc grid families (~260 MB for CT18ZNNLO) and extending the
stored conv prefix from 11 to 15.  That is the whole cost of the proposal, so it
is worth knowing what each tier buys -- especially because the anl+corr
construction interpolates the analytic model's OWN residual through the two
members, and a smooth truncation error is partly absorbed by that.

TIERS (all inside anl+corr, so all EXACT at kappa_F = 1/f, 1, f):
  T0  no analytic term at all          = the SHIPPED three-knot model
  T1  J1,J2,K11        -- NO new kinds, nothing new on disk, no cache change
  T2  + J3             -- adds P2 only            (5 grid families, ~81 MB)
  T3  + K12,K21,T111   -- adds P0xP1, P1xP0, P0xP0xP0  (11 more, ~180 MB)
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
                         K_P2, QZ, X1A, X2A, X3A, _conf_fo, lagrange, node_muf)
from dconv_gate5 import AlphasSCET, evo_coeffs_poly

TIERS = {"T1(no new kinds)": ("J1", "J2", "K11"),
         "T2(+P2)": ("J1", "J2", "J3", "K11"),
         "T3(all 7)": ("J1", "J2", "J3", "K11", "K12", "K21", "T111")}
KIND_OF = {"J1": K_P0, "J2": K_P1, "J3": K_P2, "K11": K_P0P0, "K12": K_P0P1,
           "K21": K_P1P0, "T111": K_P0P0P0}


def delta_delta(c, E, terms):
    return sum(E[t] * c[KIND_OF[t]] for t in terms)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="/ceph/submit/data/group/cms/store/user/"
                    "lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf")
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    import scetlib_qT  # noqa: F401
    from scetlib_run import config as sl_config

    tmpdir = os.path.dirname(os.path.abspath(args.out))
    c3 = configparser.ConfigParser(inline_comment_prefixes="#")
    c3.read(os.path.join(os.environ["SCETLIB_SRC"], "prod", "scetlib_run", "defaults.conf"))
    c3.read(_conf_fo(args.base, os.path.join(tmpdir, "_n3lo.conf"), "n3lo"))
    dy = sl_config.configure_calculation(c3)[4]
    als = AlphasSCET(nf=5, mu0=91.1876, as0=0.118, loops=4)
    h = math.log(args.knot)
    x = (QZ / 13000.0) * math.exp(0.075)

    print("\nerror on conv[delta] as a % of the true response; the kernel's own alphaS")
    print("=" * 100)
    rows = []
    for qt, x1l, x2l, x3l, lab in ((22.0, X1A, 0.35, X3A, "x2=0.35 template"),
                                   (26.0, X1A, 0.35, X3A, "x2=0.35 template"),
                                   (30.0, X1A, 0.35, X3A, "x2=0.35 template"),
                                   (38.0, X1A, 0.35, X3A, "x2=0.35 template"),
                                   (30.0, X1A, 0.55, X3A, "x2=0.55 near-anchor"),
                                   (26.0, X1A, 0.75, X3A, "x2=0.75 template"),
                                   (30.0, 0.3, X2A, 0.9, "x1,x3=0.3,0.9")):
        xx = qt / QZ
        worst = {k: 0.0 for k in ["T0(shipped)"] + list(TIERS)}
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
            if abs(resp) < 1e-12:
                continue
            vdn = np.asarray(dy.conv_probe(x, mfa * math.exp(mdn), 2, 0), float)[K_DELTA]
            vup = np.asarray(dy.conv_probe(x, mfa * math.exp(mup), 2, 0), float)[K_DELTA]
            base = lagrange([mdn, 0.0, mup], [vdn, c0[K_DELTA], vup], D)
            worst["T0(shipped)"] = max(worst["T0(shipped)"],
                                       abs(100 * (base - ex) / resp))
            ED = evo_coeffs_poly(als, mfa, D)
            Edn = evo_coeffs_poly(als, mfa, mdn)
            Eup = evo_coeffs_poly(als, mfa, mup)
            for name, terms in TIERS.items():
                dD = delta_delta(c0, ED, terms)
                ddn = delta_delta(c0, Edn, terms)
                dup = delta_delta(c0, Eup, terms)
                v = base + dD - lagrange([mdn, 0.0, mup], [ddn, 0.0, dup], D)
                worst[name] = max(worst[name], abs(100 * (v - ex) / resp))
        rows.append(dict(qt=qt, label=lab, **worst))
    hdr = f"{'qT':>5} {'direction':>20}"
    for k in ["T0(shipped)"] + list(TIERS):
        hdr += f" {k:>18}"
    print(hdr)
    for r in rows:
        line = f"{r['qt']:5g} {r['label']:>20}"
        for k in ["T0(shipped)"] + list(TIERS):
            line += f" {r[k]:17.3f}%"
        print(line)
    json.dump(rows, open(args.out, "w"), indent=1, default=float)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
