#!/usr/bin/env python3
"""GATE 6b: the T1 tier (no new conv kinds) across flavours, beams and rapidity."""
import configparser, json, math, os, sys
import numpy as np
WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dconv_gate3 import (K_DELTA, K_P0, K_P0P0, K_P1, QZ, X1A, X2A, X3A,
                         _conf_fo, lagrange, node_muf)
from dconv_gate5 import AlphasSCET, evo_coeffs_poly

BASE = ("/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
        "scetlib_ad_caches/knot_scan/base.conf")
KNOT = 2.0

def dd(c, E):                       # T1: J1 P0 + J2 P1 + K11 P0xP0
    return E["J1"] * c[K_P0] + E["J2"] * c[K_P1] + E["K11"] * c[K_P0P0]

def main():
    import scetlib_qT  # noqa
    from scetlib_run import config as sl_config
    tmp = os.path.dirname(os.path.abspath(__file__))
    c3 = configparser.ConfigParser(inline_comment_prefixes="#")
    c3.read(os.path.join(os.environ["SCETLIB_SRC"], "prod", "scetlib_run", "defaults.conf"))
    c3.read(_conf_fo(BASE, os.path.join(tmp, "_n3lo.conf"), "n3lo"))
    dy = sl_config.configure_calculation(c3)[4]
    als = AlphasSCET()
    out = []
    print("\nT1 (no new conv kinds) vs the shipped model, worst |error| over the bT")
    print("ladder, in % of the node's true conv[delta] response.")
    print("=" * 96)
    print(f"{'qT':>4} {'dirn':>14} {'Y':>6} {'pid':>4} {'sd':>3} {'x':>9} "
          f"{'shipped':>10} {'T1':>10} {'gain':>7}")
    for qt, x1l, x2l, x3l, lab in ((22.0, X1A, .35, X3A, "x2=0.35"),
                                   (30.0, X1A, .35, X3A, "x2=0.35"),
                                   (38.0, X1A, .35, X3A, "x2=0.35"),
                                   (26.0, X1A, .75, X3A, "x2=0.75"),
                                   (30.0, X1A, .55, X3A, "x2=0.55 anchor"),
                                   (30.0, 0.3, X2A, 0.9, "x1,x3")):
        xx = qt / QZ
        for Y in (0.075, 0.8, 1.75, 2.25):
            for pid, sd in ((2, 0), (1, 0), (-2, 1), (-1, 1), (3, 0), (-3, 1)):
                xv = (QZ / 13000.0) * math.exp(Y if sd == 0 else -Y)
                w0 = w1 = 0.0
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
                    if abs(resp) < 1e-11 * max(1.0, abs(c0[K_DELTA])):
                        continue
                    vdn = np.asarray(dy.conv_probe(xv, mfa*math.exp(mdn), pid, sd), float)[K_DELTA]
                    vup = np.asarray(dy.conv_probe(xv, mfa*math.exp(mup), pid, sd), float)[K_DELTA]
                    base = lagrange([mdn, 0.0, mup], [vdn, c0[K_DELTA], vup], D)
                    w0 = max(w0, abs(100*(base-ex)/resp))
                    dD = dd(c0, evo_coeffs_poly(als, mfa, D))
                    ddn = dd(c0, evo_coeffs_poly(als, mfa, mdn))
                    dup = dd(c0, evo_coeffs_poly(als, mfa, mup))
                    v = base + dD - lagrange([mdn, 0.0, mup], [ddn, 0.0, dup], D)
                    w1 = max(w1, abs(100*(v-ex)/resp))
                print(f"{qt:4g} {lab:>14} {Y:6.3f} {pid:4d} {sd:3d} {xv:9.5f} "
                      f"{w0:9.3f}% {w1:9.3f}% {w0/w1 if w1 else float('inf'):6.1f}x")
                out.append(dict(qt=qt, dirn=lab, Y=Y, pid=pid, side=sd, x=xv,
                                shipped=w0, T1=w1))
    json.dump(out, open(os.path.join(tmp, "gate6b.json"), "w"), indent=1, default=float)
    a = np.array([[r["shipped"], r["T1"]] for r in out])
    print(f"\nover all {len(out)} (qT, direction, Y, flavour, beam) cells:")
    print(f"  worst shipped {a[:,0].max():.3f}%   worst T1 {a[:,1].max():.3f}%")
    print(f"  median shipped {np.median(a[:,0]):.3f}%   median T1 {np.median(a[:,1]):.3f}%")
    print(f"  T1 worse than shipped in {int((a[:,1] > a[:,0]).sum())} of {len(out)} cells")

main()
