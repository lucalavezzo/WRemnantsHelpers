#!/usr/bin/env python3
"""IS THE QUARTIC'S ERROR (A1 - 1) e1 D + (A2 - 1) e2 D^2/2 ?  Predicted against
measured, per node, at mode 1 and mode 3.

The claim the whole round turns on: a form that imposes r'(0) = 0 is only as
good as that premise, and the premise is FALSE at ad_muf_anl = 1.  Write the
measured residual as r(t) = e1 t + e2 t^2/2 + C t^3 + ... .  Then, exactly,

  the QUADRATIC renders e1 and e2 exactly and misses the cubic;
  the QUARTIC   renders C exactly and renders e1 with the factor
      A1 = D^2/(b-a) [ (b-D)/a^2 + (D-a)/b^2 ]
  and e2 with A2 = D (a+b-D) / (a b),

so err_quart = (A1 - 1) e1 D + (A2 - 1) e2 D^2/2 + O(D^4 content), with A1, A2
pure geometry.  e1 and e2 are fitted here from r on a SMALL-t grid (|t| <=
t_max, both signs), so the prediction uses nothing but the measurement of r near
the anchor plus the geometry -- and is then compared with the measured error at
the FULL displacement D.

If it holds, the quartic's x1,x3 explosion is not a conditioning accident to be
guarded: it is A1 (up to 8, from the collapsed stencil) times the analytic
model's own linear truncation error e1 (13.3% of the node response at the
muf_min floor at mode 1, 1.0% at mode 3).
"""
import argparse
import configparser
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.environ.get("WREM_BASE",
                                  "/home/submit/lavezzo/alphaS/WRemnants"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from residual_forms import (K_DELTA, QZ, X1A, X2A, X3A, amps, delta_delta,  # noqa
                           evo_coeffs, node_muf, w_quad, w_quart)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="/ceph/submit/data/group/cms/store/user/"
                    "lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("--pid", type=int, default=2)
    ap.add_argument("--side", type=int, default=0)
    ap.add_argument("--tmax", type=float, default=0.02)
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()

    import lhapdf
    import scetlib_qT  # noqa: F401
    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure
    from scetlib_run import config as sl_config
    _, s2 = configure(args.base, threads=args.threads, diff_scales=True)
    sing2, _ = s2.sub_pieces()
    c3 = configparser.ConfigParser(inline_comment_prefixes="#")
    c3.read(os.path.join(os.environ["SCETLIB_SRC"], "prod", "scetlib_run",
                         "defaults.conf"))
    cc = configparser.ConfigParser(inline_comment_prefixes="#")
    cc.read(args.base)
    cc["Calculation_settings"]["fixed_order"] = "n3lo"
    cc["Calculation_settings"]["calculation_piece"] = "sing"
    cc["Calculation_settings"].pop("fo_order2_analytic", None)
    with open("/tmp/_n3lo_mech.conf", "w") as fh:
        cc.write(fh)
    c3.read("/tmp/_n3lo_mech.conf")
    sing3 = sl_config.configure_calculation(c3)[4]
    pdf = lhapdf.mkPDF("CT18ZNNLO", 0)

    def als(mu):
        return pdf.alphasQ(mu) / (4.0 * math.pi)

    Y = 0.075
    x = (QZ / 13000.0) * math.exp(Y if args.side == 0 else -Y)

    def conv(muf):
        return np.asarray(sing2.conv_probe(x, muf, args.pid, args.side), float)

    def cv3(muf):
        return np.asarray(sing3.conv_probe(x, muf, args.pid, args.side), float)

    f = args.knot
    LEGS = {"x1x3": (0.3, X2A, 0.9), "x2_035": (X1A, 0.35, X3A),
            "x2_055": (X1A, 0.55, X3A)}
    rows = []
    print(f"\n{'leg':>7}{'qT':>5}{'bT':>5}{'muF_0':>8}{'mode':>6}{'D':>8}"
          f"{'A1':>7}{'A2':>7}{'e1':>9}{'e2':>10}"
          f"{'quart pred':>12}{'quart meas':>12}{'quad meas':>11}")
    for leg, (x1L, x2L, x3L) in LEGS.items():
        for qt in (19.0, 22.0, 26.0, 30.0):
            xx = qt / QZ
            for bT in (0.8, 2.0, 8.0):
                mf0 = node_muf(bT, xx, X1A, X2A, X3A, 1.0)
                mfa = node_muf(bT, xx, X1A, X2A, X3A, 1.0 / f)
                mfb = node_muf(bT, xx, X1A, X2A, X3A, f)
                mfl = node_muf(bT, xx, x1L, x2L, x3L, 1.0)
                a, b, D = (math.log(mfa / mf0), math.log(mfb / mf0),
                           math.log(mfl / mf0))
                if min(abs(a), abs(b), abs(b - a)) < 1e-10 or D == 0:
                    continue
                c0, c3v = conv(mf0), cv3(mf0)
                R = conv(mfl)[K_DELTA] - c0[K_DELTA]
                if R == 0:
                    continue
                A1c, A1, A2 = amps(D, a, b)
                for mode, full in (("m1", 0.0), ("m3", 1.0)):
                    def rr(t):
                        E = evo_coeffs(als, mf0, t, full=full)
                        return (conv(mf0 * math.exp(t))[K_DELTA] - c0[K_DELTA]
                                - delta_delta(c0, E, full=full, cv3=c3v))
                    # e1, e2 from a small-t least-squares fit of
                    # r(t) = e1 t + e2 t^2/2 + C t^3
                    ts = np.array([-1.0, -0.5, -0.25, 0.25, 0.5, 1.0]) * args.tmax
                    rv = np.array([rr(t) for t in ts])
                    M = np.stack([ts, 0.5 * ts ** 2, ts ** 3], axis=1)
                    e1, e2, C = np.linalg.lstsq(M, rv, rcond=None)[0]
                    pred = (A1 - 1.0) * e1 * D + (A2 - 1.0) * e2 * D * D / 2.0
                    wq = w_quart(D, a, b)
                    wl = w_quad(D, a, b)
                    ra, rb, rD = rr(a), rr(b), rr(D)
                    meas_q = (wq[0] * ra + wq[1] * rb - rD)
                    meas_l = (wl[0] * ra + wl[1] * rb - rD)
                    rows.append(dict(leg=leg, qt=qt, bT=bT, mf0=mf0,
                                     mode=mode, D=D, a=a, b=b, A1=A1, A2=A2,
                                     e1=e1, e2=e2, C=C, R=R, pred=pred,
                                     meas_quart=meas_q, meas_quad=meas_l))
                    print(f"{leg:>7}{qt:>5g}{bT:>5g}{mf0:>8.3f}{mode:>6}"
                          f"{D:>+8.3f}{A1:>+7.2f}{A2:>+7.2f}"
                          f"{e1 / (R / D):>+9.3f}{e2 / (R / D):>+10.2f}"
                          f"{pred / R:>+12.3f}{meas_q / R:>+12.3f}"
                          f"{meas_l / R:>+11.3f}")
    if args.out:
        import json
        json.dump(rows, open(args.out, "w"), indent=1, default=float)
        print(f"\nwrote {args.out}")
    print("\ne1, e2 are quoted divided by R/D, i.e. e1 is the analytic model's "
          "LINEAR truncation error as a fraction of the node's mean response "
          "slope; 'pred' and 'meas' are fractions of the node's own true "
          "response R.")


if __name__ == "__main__":
    main()
