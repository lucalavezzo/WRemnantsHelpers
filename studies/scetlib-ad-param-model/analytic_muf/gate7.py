#!/usr/bin/env python3
"""GATE 7: tier comparison across flavour, beam and rapidity, with a guard on
the size of the response so that tiny-denominator cells cannot dominate.

A cell is DIAGNOSABLE only if |conv(D) - conv(0)| / |conv(0)| > 1e-3, i.e. the
node's own muF response is at least a per-mille of its convolution.  Below that
the fractional metric is a ratio of two small numbers and says nothing, exactly
as the sigma-level rule "do not diagnose on bins whose response is under 1e-4".
"""
import configparser, json, math, os, sys
import numpy as np
WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dconv_gate3 import (K_DELTA, K_P0, K_P0P0, K_P1, K_P0P0P0, K_P0P1, K_P1P0,
                         K_P2, QZ, X1A, X2A, X3A, _conf_fo, lagrange, node_muf)
from dconv_gate5 import AlphasSCET, evo_coeffs_poly

BASE = ("/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
        "scetlib_ad_caches/knot_scan/base.conf")
KNOT = 2.0
TIERS = {"T1": ("J1", "J2", "K11"),
         "T2": ("J1", "J2", "J3", "K11"),
         "T3": ("J1", "J2", "J3", "K11", "K12", "K21", "T111")}
KIND_OF = {"J1": K_P0, "J2": K_P1, "J3": K_P2, "K11": K_P0P0, "K12": K_P0P1,
           "K21": K_P1P0, "T111": K_P0P0P0}


def main():
    import scetlib_qT  # noqa
    from scetlib_run import config as sl_config
    tmp = os.path.dirname(os.path.abspath(__file__))
    c3 = configparser.ConfigParser(inline_comment_prefixes="#")
    c3.read(os.path.join(os.environ["SCETLIB_SRC"], "prod", "scetlib_run", "defaults.conf"))
    c3.read(_conf_fo(BASE, os.path.join(tmp, "_n3lo.conf"), "n3lo"))
    dy = sl_config.configure_calculation(c3)[4]
    als = AlphasSCET()
    rows = []
    print("\nWorst |error| on conv[delta] over the bT ladder, in % of the node's true")
    print("response, DIAGNOSABLE nodes only (|resp|/|conv| > 1e-3). nD = how many of")
    print("the 9 bT nodes qualified.")
    print("=" * 104)
    print(f"{'qT':>4} {'dirn':>10} {'Y':>6} {'pid':>4} {'sd':>3} {'x':>9} {'nD':>3} "
          f"{'shipped':>9} {'T1':>9} {'T2':>9} {'T3':>9}")
    for qt, x1l, x2l, x3l, lab in ((22.0, X1A, .35, X3A, "x2=0.35"),
                                   (30.0, X1A, .35, X3A, "x2=0.35"),
                                   (38.0, X1A, .35, X3A, "x2=0.35"),
                                   (26.0, X1A, .75, X3A, "x2=0.75"),
                                   (30.0, X1A, .55, X3A, "x2=0.55"),
                                   (30.0, 0.3, X2A, 0.9, "x1,x3")):
        xx = qt / QZ
        for Y in (0.075, 0.8, 1.75, 2.25):
            for pid, sd in ((2, 0), (1, 0), (-2, 1), (-1, 1)):
                xv = (QZ / 13000.0) * math.exp(Y if sd == 0 else -Y)
                w = {k: 0.0 for k in ["T0"] + list(TIERS)}
                nD = 0
                for bT in (0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0):
                    mfa = node_muf(bT, xx, X1A, X2A, X3A, 1.0)
                    if mfa < 1.3:
                        continue
                    D = math.log(node_muf(bT, xx, x1l, x2l, x3l, 1.0) / mfa)
                    mdn = math.log(node_muf(bT, xx, X1A, X2A, X3A, 1/KNOT)/mfa)
                    mup = math.log(node_muf(bT, xx, X1A, X2A, X3A, KNOT)/mfa)
                    c0 = np.asarray(dy.conv_probe(xv, mfa, pid, sd), float)
                    ex = np.asarray(dy.conv_probe(xv, mfa*math.exp(D), pid, sd), float)[K_DELTA]
                    resp = ex - c0[K_DELTA]
                    if abs(c0[K_DELTA]) <= 0 or abs(resp / c0[K_DELTA]) < 1e-3:
                        continue
                    nD += 1
                    vdn = np.asarray(dy.conv_probe(xv, mfa*math.exp(mdn), pid, sd), float)[K_DELTA]
                    vup = np.asarray(dy.conv_probe(xv, mfa*math.exp(mup), pid, sd), float)[K_DELTA]
                    base = lagrange([mdn, 0.0, mup], [vdn, c0[K_DELTA], vup], D)
                    w["T0"] = max(w["T0"], abs(100*(base-ex)/resp))
                    ED = evo_coeffs_poly(als, mfa, D)
                    Edn = evo_coeffs_poly(als, mfa, mdn)
                    Eup = evo_coeffs_poly(als, mfa, mup)
                    for name, terms in TIERS.items():
                        f = lambda E: sum(E[t]*c0[KIND_OF[t]] for t in terms)
                        v = base + f(ED) - lagrange([mdn, 0.0, mup],
                                                    [f(Edn), 0.0, f(Eup)], D)
                        w[name] = max(w[name], abs(100*(v-ex)/resp))
                if nD == 0:
                    continue
                print(f"{qt:4g} {lab:>10} {Y:6.3f} {pid:4d} {sd:3d} {xv:9.5f} {nD:3d} "
                      f"{w['T0']:8.3f}% {w['T1']:8.3f}% {w['T2']:8.3f}% {w['T3']:8.3f}%")
                rows.append(dict(qt=qt, dirn=lab, Y=Y, pid=pid, side=sd, x=xv, nD=nD, **w))
    json.dump(rows, open(os.path.join(tmp, "gate7.json"), "w"), indent=1, default=float)
    a = {k: np.array([r[k] for r in rows]) for k in ["T0"] + list(TIERS)}
    print(f"\nover {len(rows)} diagnosable cells:")
    for k in ["T0"] + list(TIERS):
        print(f"  {k:>3}: worst {a[k].max():8.3f}%   median {np.median(a[k]):7.3f}%   "
              f"90th pct {np.percentile(a[k], 90):7.3f}%   "
              f"worse-than-shipped in {int((a[k] > a['T0']).sum())} cells")

main()
