#!/usr/bin/env python3
"""THE RESIDUAL r(D), MEASURED, AND EVERY CANDIDATE INTERPOLANT SCORED ON IT.

The shipped construction is, algebraically,
    cvi(D) = conv(0) + delta(D) + [ w_dn(D) r(a) + w_up(D) r(b) ],
    r(t)   = conv(t) - conv(0) - delta(t),     a = mfk_dn < 0 < b = mfk_up,
with (w_dn, w_up) the quadratic Lagrange weights.  `conv` is measurable at ANY
muF with `DrellYan.conv_probe` -- the same interpolant SCETlib itself uses -- and
`delta` is the kernel's own truncated DGLAP evolution, replicated here term for
term from muf_evo_coeffs (mode 1: J1 D, J2 D, K11 = I1^2/2; 5-point
Gauss-Legendre on a quadratic model of g on [0, D]).  So r is MEASURED, not
modelled, and every candidate form can be scored EXACTLY at the node level
before any kernel code is written.

CAVEAT, stated once and meant.  The previous round measured that the node-level
error UNDER-predicts the sigma-level residual by 5x (shipped) to 50x (analytic),
because a bin sums nodes through an oscillatory bT integral with a ~9x muF
cancellation on top.  So this is a SCREEN -- it ranks forms and it catches
blow-ups (the quartic's x1,x3 explosion is visible here) -- and the sigma-level
attribution is the decision.

Metric: node error as a fraction of that node's OWN true response
conv[c_delta](D) - conv[c_delta](0), the same metric gate2_lowmuf.py part B uses.
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

B0 = 2.0 * math.exp(-np.euler_gamma)
QZ = 91.1876
MUF_MIN = 1.40
X1A, X2A, X3A = 0.2, 0.6, 1.0

GV = [0.046910077030668, 0.230765344947158, 0.5,
      0.769234655052842, 0.953089922969332]
GW = [0.118463442528095, 0.239314335249683, 0.284444444444444,
      0.239314335249683, 0.118463442528095]


def g_run(x, x1, x2, x3):
    if x < x1:
        return 1.0
    if x < x2:
        return 1.0 - (x - x1) ** 2 / ((x2 - x1) * (x3 - x1))
    if x < x3:
        return (x - x3) ** 2 / ((x3 - x1) * (x3 - x2))
    return 0.0


def node_muf(bT, xx, x1, x2, x3, ratio=1.0, fo_muf=QZ):
    y = ((B0 / bT) ** 4 + (MUF_MIN / ratio) ** 4) ** 0.25 / QZ
    g = g_run(xx, x1, x2, x3)
    return fo_muf * ratio * (g * y + (1.0 - g))


def evo_coeffs(als, muf, D, full=0.0):
    """muf_evo_coeffs, term for term.  out[0] = J1 D, out[1] = J2 D,
    out[3] = I1^2/2; the alphas^3 entries are gated by `full` exactly as there."""
    if D == 0.0:
        return [0.0] * 7
    g0 = als(muf)
    gh = als(muf * math.exp(0.5 * D))
    gD = als(muf * math.exp(D))
    c0 = g0
    c1 = 4.0 * gh - 3.0 * g0 - gD
    c2 = 2.0 * (g0 - 2.0 * gh + gD)
    a0, a1 = c0 * c0, 2.0 * c0 * c1
    a2, a3, a4 = c1 * c1 + 2.0 * c0 * c2, 2.0 * c1 * c2, c2 * c2
    J1 = J2 = J3 = K12 = K21 = 0.0
    for v, w in zip(GV, GW):
        g = c0 + v * (c1 + v * c2)
        J1 += w * 2.0 * g
        J2 += w * 2.0 * g * g
        J3 += w * 2.0 * g ** 3
        F1 = 2.0 * D * v * (c0 + v * (c1 / 2.0 + v * (c2 / 3.0)))
        F2 = 2.0 * D * v * (a0 + v * (a1 / 2.0 + v * (a2 / 3.0
                            + v * (a3 / 4.0 + v * (a4 / 5.0)))))
        K12 += w * 2.0 * g * F2
        K21 += w * 2.0 * g * g * F1
    out = [J1 * D, J2 * D, full * J3 * D, 0.0, full * K12 * D, full * K21 * D, 0.0]
    out[3] = 0.5 * out[0] * out[0]
    out[6] = full * out[0] ** 3 / 6.0
    return out


K_P0P0P0, K_P0P1, K_P1P0, K_P2 = 11, 12, 13, 14


def delta_delta(cv0, E, full=0.0, cv3=None):
    """The kernel's shift of conv[c_delta] alone (the response is dominated by
    it; c_p0 and c_i1_qq are shifted too and enter the beam function at higher
    order in alphas).

    At full = 1 the four alphas^3 columns are added exactly as the kernel does.
    They live one fixed order above nnlo, so `cv3` must come from an n3lo-
    configured probe."""
    dd = E[0] * cv0[K_P0] + E[1] * cv0[K_P1] + E[3] * cv0[K_P0P0]
    if full:
        dd += (E[2] * cv3[K_P2] + E[4] * cv3[K_P0P1] + E[5] * cv3[K_P1P0]
               + E[6] * cv3[K_P0P0P0])
    return dd


# ---------------------------------------------------------------- forms ----
def w_quad(D, a, b):
    return (D * (D - b) / (a * (a - b)), D * (D - a) / (b * (b - a)))


def w_cubic(D, a, b):
    return (D * D * (D - b) / (a * a * (a - b)),
            D * D * (D - a) / (b * b * (b - a)))


def w_quart(D, a, b):
    sep = b - a
    return (D ** 3 * (b - D) / (sep * a ** 3), D ** 3 * (D - a) / (sep * b ** 3))


def amps(D, a, b):
    sep = b - a
    A1c = D * (D - a - b) / (a * b)
    A1q = D * D / sep * ((b - D) / a ** 2 + (D - a) / b ** 2)
    A2q = D * (a + b - D) / (a * b)
    return A1c, A1q, A2q


def theta_q(D, a, b, tol):
    _, A1q, A2q = amps(D, a, b)
    A = max(abs(A1q - 1.0), abs(A2q - 1.0))
    return min(1.0, tol / A) if A > 0 else 1.0


def theta_c(D, a, b, tol):
    A1c, _, _ = amps(D, a, b)
    A = abs(A1c - 1.0)
    return min(1.0, tol / A) if A > 0 else 1.0


def blend(w1, w2, th):
    return ((1.0 - th) * w1[0] + th * w2[0], (1.0 - th) * w1[1] + th * w2[1])


def w_clipfac(D, a, b, k):
    L = w_quad(D, a, b)
    def s(t):
        if k == 1:
            return max(-1.0, min(1.0, t))
        return min(1.0, t * t)
    return (L[0] * s(D / a), L[1] * s(D / b))


def w_onesided(D, a, b):
    if D < 0:
        return ((D / a) ** 3, 0.0)
    return (0.0, (D / b) ** 3)


def all_forms(D, a, b, tols):
    f = {"quad": w_quad(D, a, b), "cubic": w_cubic(D, a, b),
         "quart": w_quart(D, a, b)}
    for t in tols:
        f[f"bq{t:g}"] = blend(f["quad"], f["quart"], theta_q(D, a, b, t))
        f[f"bc{t:g}"] = blend(f["quad"], f["cubic"], theta_c(D, a, b, t))
    f["clip1"] = w_clipfac(D, a, b, 1)
    f["clip2"] = w_clipfac(D, a, b, 2)
    f["oneside"] = w_onesided(D, a, b)
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="/ceph/submit/data/group/cms/store/user/"
                    "lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--knot", type=float, default=2.0)
    ap.add_argument("--pid", type=int, default=2)
    ap.add_argument("--side", type=int, default=0)
    ap.add_argument("--pdf-set", default="CT18ZNNLO")
    ap.add_argument("--tols", type=float, nargs="+", default=[0.3, 1.0, 3.0])
    ap.add_argument("--mode3", action="store_true",
                    help="delta at ad_muf_anl = 3: the full alphas^3 evolution "
                         "(J3 P2, K12, K21, T111). P2 is not filled at "
                         "fixed_order = nnlo, so it comes from a second probe "
                         "configured at n3lo, exactly as gate2_lowmuf.py does.")
    ap.add_argument("--legs", nargs="+",
                    default=["x2_035", "x2_055", "x2_075", "x1x3"])
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    import lhapdf
    import scetlib_qT  # noqa: F401
    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    _, s2 = configure(args.base, threads=args.threads, diff_scales=True)
    sing2, _ = s2.sub_pieces()
    sing3 = None
    if args.mode3:
        from scetlib_run import config as sl_config
        c3 = configparser.ConfigParser(inline_comment_prefixes="#")
        c3.read(os.path.join(os.environ["SCETLIB_SRC"], "prod", "scetlib_run",
                             "defaults.conf"))
        cc = configparser.ConfigParser(inline_comment_prefixes="#")
        cc.read(args.base)
        cc["Calculation_settings"]["fixed_order"] = "n3lo"
        cc["Calculation_settings"]["calculation_piece"] = "sing"
        cc["Calculation_settings"].pop("fo_order2_analytic", None)
        tmp3 = os.path.join(os.path.dirname(os.path.abspath(args.out)),
                            "_n3lo_probe.conf")
        with open(tmp3, "w") as fh:
            cc.write(fh)
        c3.read(tmp3)
        sing3 = sl_config.configure_calculation(c3)[4]
    pdf = lhapdf.mkPDF(args.pdf_set, 0)

    def als(mu):
        return pdf.alphasQ(mu) / (4.0 * math.pi)

    def conv(x, muf):
        return np.asarray(sing2.conv_probe(x, muf, args.pid, args.side), float)

    def conv3v(x, muf):
        if sing3 is None:
            return None
        return np.asarray(sing3.conv_probe(x, muf, args.pid, args.side), float)

    Y = 0.075
    x = (QZ / 13000.0) * math.exp(Y if args.side == 0 else -Y)
    f = args.knot
    LEGS = {"x2_035": (X1A, 0.35, X3A), "x2_055": (X1A, 0.55, X3A),
            "x2_075": (X1A, 0.75, X3A), "x1x3": (0.3, X2A, 0.9)}
    QTS = (19.0, 22.0, 26.0, 30.0, 38.0, 50.0, 70.0)
    BTS = (0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0, 8.0)
    names = ["quad", "cubic", "quart"] \
        + [f"bq{t:g}" for t in args.tols] + [f"bc{t:g}" for t in args.tols] \
        + ["clip1", "clip2", "oneside"]
    rows = []
    for leg in args.legs:
        x1L, x2L, x3L = LEGS[leg]
        print("\n" + "=" * 132)
        print(f"LEG {leg}: transition points [{x1L}, {x2L}, {x3L}] vs anchor "
              f"[{X1A}, {X2A}, {X3A}], f = {f:g}, pid = {args.pid}, "
              f"side = {args.side}, x = {x:.5f}")
        print("=" * 132)
        for qt in QTS:
            xx = qt / QZ
            print(f"\n  qT = {qt:g} (x = {xx:.4f})")
            hdr = (f"{'bT':>5}{'muF_0':>8}{'D':>9}{'a':>9}{'b':>9}"
                   f"{'trueresp':>11}{'r(D)/R':>8}{'A1q':>7}{'A2q':>7}"
                   f"{'thq1':>6}{'pure':>8}")
            for n in names:
                hdr += f"{n:>9}"
            print(hdr)
            for bT in BTS:
                mf0 = node_muf(bT, xx, X1A, X2A, X3A, 1.0)
                mfa = node_muf(bT, xx, X1A, X2A, X3A, 1.0 / f)
                mfb = node_muf(bT, xx, X1A, X2A, X3A, f)
                mfl = node_muf(bT, xx, x1L, x2L, x3L, 1.0)
                a, b, D = (math.log(mfa / mf0), math.log(mfb / mf0),
                           math.log(mfl / mf0))
                if min(abs(a), abs(b), abs(b - a)) < 1e-8 * math.log(f) or D == 0:
                    continue
                c0 = conv(x, mf0)
                R = conv(x, mfl)[K_DELTA] - c0[K_DELTA]
                if R == 0.0:
                    continue
                rr = {}
                full = 1.0 if args.mode3 else 0.0
                cv3 = conv3v(x, mf0)
                for lab, t, mu in (("a", a, mfa), ("b", b, mfb), ("D", D, mfl)):
                    E = evo_coeffs(als, mf0, t, full=full)
                    rr[lab] = (conv(x, mu)[K_DELTA] - c0[K_DELTA]
                               - delta_delta(c0, E, full=full, cv3=cv3))
                A1c, A1q, A2q = amps(D, a, b)
                fw = all_forms(D, a, b, args.tols)
                errs = {n: (fw[n][0] * rr["a"] + fw[n][1] * rr["b"] - rr["D"]) / R
                        for n in names}
                # the SHIPPED model: no delta at all, quadratic on the raw conv
                La, Lb = w_quad(D, a, b)
                ship = (La * (conv(x, mfa)[K_DELTA] - c0[K_DELTA])
                        + Lb * (conv(x, mfb)[K_DELTA] - c0[K_DELTA]) - R) / R
                line = (f"{bT:>5g}{mf0:>8.3f}{D:>+9.3f}{a:>+9.3f}{b:>+9.3f}"
                        f"{R:>+11.3e}{rr['D']/R:>+8.3f}{A1q:>+7.2f}{A2q:>+7.2f}"
                        f"{theta_q(D, a, b, 1.0):>6.2f}{-rr['D']/R:>+8.3f}")
                for n in names:
                    line += f"{errs[n]:>+9.3f}"
                print(line + f"   ship {ship:+.3f}")
                rows.append(dict(leg=leg, qt=qt, bT=bT, mf0=mf0, D=D, a=a, b=b,
                                 R=R, rD=rr["D"], ra=rr["a"], rb=rr["b"],
                                 A1c=A1c, A1q=A1q, A2q=A2q, ship=ship,
                                 **{f"err_{n}": errs[n] for n in names}))
    json.dump(dict(rows=rows, names=names, tols=args.tols,
                   pid=args.pid, side=args.side, x=x), open(args.out, "w"),
              indent=1, default=float)
    print(f"\nwrote {args.out}")

    # ---- summary: max and rms |error| per form per leg ---------------------
    print("\n" + "=" * 132)
    print("SUMMARY  |node error| as a fraction of the node's own true response, "
          "over all (qT, bT) of each leg")
    print("=" * 132)
    print(f"{'leg':>8}{'stat':>6}{'ship':>9}{'pure':>9}", end="")
    for n in names:
        print(f"{n:>9}", end="")
    print()
    for leg in args.legs:
        sub = [r for r in rows if r["leg"] == leg]
        if not sub:
            continue
        for stat, fn in (("max", max), ("rms", lambda v: math.sqrt(
                sum(t * t for t in v) / len(v)))):
            print(f"{leg:>8}{stat:>6}"
                  f"{fn([abs(r['ship']) for r in sub]):>9.2f}"
                  f"{fn([abs(r['rD'] / r['R']) for r in sub]):>9.2f}", end="")
            for n in names:
                print(f"{fn([abs(r[f'err_{n}']) for r in sub]):>9.2f}", end="")
            print()


if __name__ == "__main__":
    main()
