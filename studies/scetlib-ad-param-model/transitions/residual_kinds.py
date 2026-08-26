#!/usr/bin/env python3
"""Does the quadratic member interpolation get EVERY conv kind right, or only
conv[c_delta]?

`residual_forms.py` scores the forms on conv[c_delta] alone, which is I0 of the
beam function. But the interpolated vector `cvi` feeds beam_I_coeffs in full:
c_p0 and c_i1_* multiply the explicit ln(muB/muF) logs at O(alphas), c_p1 /
c_p0p0 / c_i1p0 / c_i2_* at O(alphas^2). The muF cancellation those logs
implement is the ~9x amplifier, so a kind that is BADLY interpolated would show
up in sigma even though c_delta is fine.

This prints, per node, the quadratic's interpolation error on EVERY kind as a
fraction of that kind's OWN response -- and, because a kind with a tiny response
can carry a large fractional error harmlessly, also as a fraction of
conv[c_delta]'s response weighted by that kind's O(alphas^n) prefactor.
"""
import argparse
import math
import os
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)

KINDS = ["delta", "p0", "i1_qq", "i1_qg", "p0p0", "p1", "i1p0",
         "i2_qqV", "i2_qqbarV", "i2_qqS", "i2_qg"]
AS_ORDER = [0, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2]   # the alphaS power each enters at

B0 = 2.0 * math.exp(-np.euler_gamma)
QZ = 91.1876
MUF_MIN = 1.40
X1A, X2A, X3A = 0.2, 0.6, 1.0
GV = [0.046910077030668, 0.230765344947158, 0.5,
      0.769234655052842, 0.953089922969332]
GW = [0.118463442528095, 0.239314335249683, 0.284444444444444,
      0.239314335249683, 0.118463442528095]
K_DELTA, K_P0, K_P0P0, K_P1, K_I1P0 = 0, 1, 4, 5, 6
K_I1QQ, K_I1QG = 2, 3


def g_run(x, x1, x2, x3):
    if x < x1:
        return 1.0
    if x < x2:
        return 1.0 - (x - x1) ** 2 / ((x2 - x1) * (x3 - x1))
    if x < x3:
        return (x - x3) ** 2 / ((x3 - x1) * (x3 - x2))
    return 0.0


def node_muf(bT, xx, x1, x2, x3, ratio=1.0):
    y = ((B0 / bT) ** 4 + (MUF_MIN / ratio) ** 4) ** 0.25 / QZ
    g = g_run(xx, x1, x2, x3)
    return QZ * ratio * (g * y + (1.0 - g))


def evo(als, muf, D):
    if D == 0.0:
        return [0.0] * 7
    g0, gh, gD = als(muf), als(muf * math.exp(0.5 * D)), als(muf * math.exp(D))
    c0 = g0
    c1 = 4.0 * gh - 3.0 * g0 - gD
    c2 = 2.0 * (g0 - 2.0 * gh + gD)
    J1 = J2 = 0.0
    for v, w in zip(GV, GW):
        g = c0 + v * (c1 + v * c2)
        J1 += w * 2.0 * g
        J2 += w * 2.0 * g * g
    out = [J1 * D, J2 * D, 0.0, 0.0, 0.0, 0.0, 0.0]
    out[3] = 0.5 * out[0] * out[0]
    return out


def delta_vec(cv0, E):
    """The kernel's shift of the WHOLE prefix at ad_muf_anl = 1: c_delta, c_p0
    and (with ad_muf_i1 on, which is production) c_i1_qq."""
    dv = np.zeros_like(cv0)
    dv[K_DELTA] = E[0] * cv0[K_P0] + E[1] * cv0[K_P1] + E[3] * cv0[K_P0P0]
    dv[K_P0] = E[0] * cv0[K_P0P0]
    dv[K_I1QQ] = E[0] * cv0[K_I1P0]
    return dv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="/ceph/submit/data/group/cms/store/user/"
                    "lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("--pdf-set", default="CT18ZNNLO")
    ap.add_argument("--pids", type=int, nargs="+", default=[2, 1, 21])
    args = ap.parse_args()

    import lhapdf
    import scetlib_qT  # noqa: F401
    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure
    _, s2 = configure(args.base, threads=args.threads, diff_scales=True)
    sing2, _ = s2.sub_pieces()
    pdf = lhapdf.mkPDF(args.pdf_set, 0)

    def als(mu):
        return pdf.alphasQ(mu) / (4.0 * math.pi)

    f = args.knot
    Y = 0.075
    LEGS = {"x2_035": (X1A, 0.35, X3A), "x1x3": (0.3, X2A, 0.9)}
    for pid in args.pids:
        for side in (0, 1):
            x = (QZ / 13000.0) * math.exp(Y if side == 0 else -Y)
            def conv(muf):
                return np.asarray(sing2.conv_probe(x, muf, pid, side), float)
            for leg, (x1L, x2L, x3L) in LEGS.items():
                print("\n" + "=" * 118)
                print(f"pid {pid} side {side} leg {leg}: quadratic member "
                      f"interpolation error per conv kind, as a fraction of "
                      f"that kind's OWN response")
                print("=" * 118)
                print(f"{'qT':>5}{'bT':>6}{'muF_0':>8}{'D':>8}", end="")
                for k in KINDS:
                    print(f"{k:>11}", end="")
                print()
                for qt in (19.0, 22.0, 26.0, 30.0, 38.0):
                    xx = qt / QZ
                    for bT in (0.2, 0.8, 2.0, 8.0):
                        mf0 = node_muf(bT, xx, X1A, X2A, X3A, 1.0)
                        mfa = node_muf(bT, xx, X1A, X2A, X3A, 1.0 / f)
                        mfb = node_muf(bT, xx, X1A, X2A, X3A, f)
                        mfl = node_muf(bT, xx, x1L, x2L, x3L, 1.0)
                        a, b, D = (math.log(mfa / mf0), math.log(mfb / mf0),
                                   math.log(mfl / mf0))
                        if min(abs(a), abs(b), abs(b - a)) < 1e-10 or D == 0:
                            continue
                        c0, ca, cb, cD = (conv(mf0), conv(mfa), conv(mfb),
                                          conv(mfl))
                        ra = ca - c0 - delta_vec(c0, evo(als, mf0, a))
                        rb = cb - c0 - delta_vec(c0, evo(als, mf0, b))
                        rD = cD - c0 - delta_vec(c0, evo(als, mf0, D))
                        wdn = D * (D - b) / (a * (a - b))
                        wup = D * (D - a) / (b * (b - a))
                        err = wdn * ra + wup * rb - rD
                        R = cD - c0
                        print(f"{qt:>5g}{bT:>6g}{mf0:>8.3f}{D:>+8.3f}", end="")
                        for i in range(len(KINDS)):
                            v = err[i] / R[i] if R[i] else float("nan")
                            print(f"{v:>+11.4f}", end="")
                        print()


if __name__ == "__main__":
    main()
