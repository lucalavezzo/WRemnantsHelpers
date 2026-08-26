#!/usr/bin/env python3
"""GATE 2: the analytic d(conv)/d(ln muF), measured against LHAPDF itself.

Extends dconv_dlnmuf.py with the two things that make it decisive:

 1. THE P2 TERM.  Production runs `fixed_order = nnlo` -> fo_lvl = 2, so the
    conv kinds stop at order alphas^2 and the analytic derivative can only use
    P0 and P1.  The NNLO splitting kernel P2 exists in SCETlib and its grids are
    already on disk (share/scetlib/beamfunc/CT18ZNNLO_beamfunc/CT18ZNNLO_P2_*),
    they are simply not FILLED at fo_lvl = 2.  A second probe configured at
    fixed_order = n3lo exposes them, so the question "does P0+P1+P2 reproduce
    LHAPDF's own evolution?" can be answered before writing any kernel code.

 2. THE REAL MEMBER POSITIONS.  Vary.muf scales muF by f^leg AND divides the
    muf_min floor by f^leg, so per NODE the two members do NOT sit at +-ln f:
    they collapse toward zero where the floor dominates and are strongly
    asymmetric in between.  Idealising them at +-ln f flatters the shipped
    scheme.  Here the stencil is built from SCETlib's own scale formulas at
    the anchor transition points, exactly as the kernel does after 92f1299.

METRIC.  Error on conv[c_delta] as a fraction of that point's TRUE response
conv(D) - conv(0).  conv[c_delta] is I[0] of the beam function.  Because the
explicit ln(muB/muF) in the matching coefficients cancels the PDF evolution to
the computed order, the NET transition response is ~9x smaller than the
convolution half alone (measured at qT [20,24]: +2.43% analytic, -2.66%
convolution, -0.23% net) -- so a x% error here costs ~9x% on the answer, and
the target for a 3% net is ~0.3% here.
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
NKIND2 = 11

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
    """muF at one bT node.  `ratio` = kappa_F of a staged member: it scales muF
    AND divides the floor, exactly as Scale_provider does."""
    y = mu_star(B0 / bT, MUF_MIN / ratio) / QZ
    g = g_run(xx, x1, x2, x3)
    return fo_muf * ratio * (g * y + (1.0 - g))


class Alphas:
    def __init__(self, setname):
        import lhapdf
        self._p = lhapdf.mkPDF(setname, 0)

    def g(self, mu):
        return self._p.alphasQ(mu) / (4.0 * math.pi)


def _trapz(y, x):
    return np.trapezoid(y, x) if hasattr(np, "trapezoid") else np.trapz(y, x)


def integrals(als, muf0, D, running=True, n=64):
    """I1 = int 2g, I2 = int 2g^2, I3 = int 2g^3, I11 = int 2g(L)[int 2g],
    I12 = int 2g(L)[int 2g^2] + int 2g^2(L)[int 2g], I111 = the triple."""
    if D == 0.0:
        return dict(I1=0.0, I2=0.0, I3=0.0, I11=0.0, I111=0.0)
    if not running:
        g = als.g(muf0)
        return dict(I1=2 * g * D, I2=2 * g * g * D, I3=2 * g ** 3 * D,
                    I11=2 * g * g * D * D, I111=(4. / 3.) * g ** 3 * D ** 3)
    L = np.linspace(0.0, D, n + 1)
    g = np.array([als.g(muf0 * math.exp(l)) for l in L])
    tg = 2.0 * g
    cum1 = np.concatenate(([0.0], np.cumsum(0.5 * (tg[1:] + tg[:-1]) * np.diff(L))))
    I11int = tg * cum1
    cum11 = np.concatenate(([0.0], np.cumsum(0.5 * (I11int[1:] + I11int[:-1]) * np.diff(L))))
    return dict(I1=cum1[-1], I2=_trapz(2 * g * g, L), I3=_trapz(2 * g ** 3, L),
                I11=cum11[-1], I111=_trapz(tg * cum11, L))


def dglap_shift(cv0, I, order=2, use_p2=False, cv_p2=0.0):
    """Truncated-DGLAP evolution of the fo_lvl=2 conv prefix by D.

    order = 1  keep only the first derivative column (linear in D)
    order = 2  the full nilpotent series (exact in D at fo_lvl = 2)
    use_p2     add the 2g^3 P2 term, which fo_lvl = 2 does not store
    """
    out = cv0.copy()
    out[K_DELTA] = cv0[K_DELTA] + I["I1"] * cv0[K_P0] + I["I2"] * cv0[K_P1]
    if use_p2:
        out[K_DELTA] += I["I3"] * cv_p2
    if order >= 2:
        out[K_DELTA] += I["I11"] * cv0[K_P0P0]
    out[K_P0] = cv0[K_P0] + I["I1"] * cv0[K_P0P0]
    i1tot = cv0[K_I1QQ] + cv0[K_I1QG]
    wqq = cv0[K_I1QQ] / i1tot if i1tot else 1.0
    out[K_I1QQ] = cv0[K_I1QQ] + I["I1"] * cv0[K_I1P0] * wqq
    out[K_I1QG] = cv0[K_I1QG] + I["I1"] * cv0[K_I1P0] * (1.0 - wqq)
    return out


def lagrange(nodes, values, D):
    nodes = np.asarray(nodes, float)
    out = np.zeros_like(values[0])
    for i, xi in enumerate(nodes):
        w = 1.0
        for j, xj in enumerate(nodes):
            if i != j:
                w *= (D - xj) / (xi - xj)
        out = out + w * values[i]
    return out


def _conf_fo(base, out, fo):
    """A SINGULAR-only clone of the runcard at a different fixed order.

    Only the beam convolutions are wanted, and the matched/nonsingular piece
    refuses to build above NNLO ("only available through NNLO"), so the probe
    drops to calculation_piece = sing.  The PDF set, nf and the beamfunc grid
    directory are untouched, which is what conv_probe depends on.
    """
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
    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    tmpdir = os.path.dirname(os.path.abspath(args.out))
    _, s2 = configure(args.base, threads=args.threads, diff_scales=True)
    sing2, _ = s2.sub_pieces()
    # The N3LO probe is built directly, not through xsec_backend.configure:
    # that helper assumes the matched (sing + nons) layout and calls
    # sigma.sub_pieces(), which a singular-only DrellYan does not have. Nothing
    # it does beyond configure_calculation affects conv_probe, which depends
    # only on the PDF set and the beamfunc grids.
    from scetlib_run import config as sl_config
    c3 = configparser.ConfigParser(inline_comment_prefixes="#")
    c3.read(os.path.join(os.environ["SCETLIB_SRC"], "prod", "scetlib_run",
                         "defaults.conf"))
    c3.read(_conf_fo(args.base, os.path.join(tmpdir, "_n3lo.conf"), "n3lo"))
    sing3 = sl_config.configure_calculation(c3)[4]
    als = Alphas(args.pdf_set)

    def conv2(x, muf):
        return np.asarray(sing2.conv_probe(x, muf, args.pid, args.side), float)

    def conv3(x, muf):
        return np.asarray(sing3.conv_probe(x, muf, args.pid, args.side), float)

    h = math.log(args.knot)
    Y = 0.075
    x = (QZ / 13000.0) * math.exp(Y if args.side == 0 else -Y)
    res = {"h": h, "x": x, "pid": args.pid, "side": args.side, "knot": args.knot}

    # cross-check: the fo_lvl = 2 prefix must be IDENTICAL between the two probes
    d = np.max(np.abs(conv3(x, 10.0)[:NKIND2] / conv2(x, 10.0)[:NKIND2] - 1.0))
    print(f"\nfo_lvl 2 vs 3 probe, max|rel diff| on the shared prefix: {d:.3e}"
          f"   ({'OK' if d < 1e-12 else 'DIFFERENT -- investigate'})")
    res["prefix_check"] = d

    # ------------------------------------------------------------------ A ---
    print("\n" + "=" * 92)
    print("A. THE ANALYTIC DERIVATIVE vs A CONVERGED CENTRAL DIFFERENCE OF conv_probe")
    print("   d(conv_delta)/dlnmuF = 2g P0 + 2g^2 P1 + 2g^3 P2,  g = alphaS(muF)/4pi")
    print("   Columns: relative difference of each truncation from the FD truth.")
    print("=" * 92)
    print(f"{'muF':>8} {'alphaS':>8} {'FD d/dlnmuF':>14} {'P0 only':>11} "
          f"{'P0+P1':>11} {'P0+P1+P2':>11} {'|P2 term|/FD':>13}")
    partA = []
    # DOWN TO THE muf_min FLOOR. The transition response of the low-qT bins
    # comes from the large-bT nodes where the profile has pinned muF at
    # muf_min = 1.4 GeV, so how well fixed-order DGLAP tracks LHAPDF's own
    # grid evolution THERE is what caps those bins.
    for muf in (1.4, 1.5, 1.6, 1.8, 1.9, 2.0, 2.5, 3.0, 4.0, 5.0, 8.0,
                13.0, 20.0, 45.0, 91.1876):
        eps = 1e-3
        fd = (conv2(x, muf * math.exp(eps))[K_DELTA]
              - conv2(x, muf * math.exp(-eps))[K_DELTA]) / (2.0 * eps)
        c2 = conv2(x, muf)
        c3 = conv3(x, muf)
        g = als.g(muf)
        t0 = 2 * g * c2[K_P0]
        t1 = t0 + 2 * g * g * c2[K_P1]
        t2 = t1 + 2 * g ** 3 * c3[K_P2]
        row = dict(muf=muf, alphaS=4 * math.pi * g, fd=fd, p0=t0, p0p1=t1, p0p1p2=t2)
        partA.append(row)
        print(f"{muf:8.3f} {4 * math.pi * g:8.4f} {fd:14.6e} {t0 / fd - 1:+11.2e} "
              f"{t1 / fd - 1:+11.2e} {t2 / fd - 1:+11.2e} "
              f"{abs(2 * g ** 3 * c3[K_P2] / fd):13.2e}")
    res["partA"] = partA

    # ------------------------------------------------------------------ B ---
    print("\n" + "=" * 92)
    print("B. FINITE D, REAL PER-NODE MEMBER POSITIONS vs the idealised +-ln f")
    print("   knot3real: Lagrange through the members Vary.muf ACTUALLY builds")
    print("              (muF scaled by f^leg AND the floor divided by f^leg)")
    print("   knot3ideal: the same quadratic with the members forced to +-ln f")
    print("   dglap2:    nilpotent truncated DGLAP, running alphaS, P0+P1")
    print("   dglap2P2:  the same with the P2 column added")
    print("   error as a % of the TRUE response of conv[delta]")
    print("=" * 92)
    partB = []
    for qt, x2live, lab in ((22.0, 0.35, "template leg"), (26.0, 0.35, "template leg"),
                            (30.0, 0.35, "template leg"), (38.0, 0.35, "template leg"),
                            (30.0, 0.55, "near anchor"), (26.0, 0.55, "near anchor")):
        xx = qt / QZ
        print(f"\n  qT = {qt:g} (x = {xx:.4f}), x2: {X2A} -> {x2live}   [{lab}]")
        print(f"{'bT':>6} {'muF_a':>8} {'D/lnf':>7} {'mem-/lnf':>9} {'mem+/lnf':>9} "
              f"{'where':>6} {'true resp':>12} {'knot3real':>11} {'knot3idl':>10} "
              f"{'dglap2':>10} {'dglap2P2':>10}")
        for bT in (0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0):
            mfa = node_muf(bT, xx, X1A, X2A, X3A, 1.0)
            if mfa < 1.3:
                continue
            mfl = node_muf(bT, xx, X1A, x2live, X3A, 1.0)
            D = math.log(mfl / mfa)
            mdn = math.log(node_muf(bT, xx, X1A, X2A, X3A, 1.0 / args.knot) / mfa)
            mup = math.log(node_muf(bT, xx, X1A, X2A, X3A, args.knot) / mfa)
            c0 = conv2(x, mfa)
            ex = conv2(x, mfa * math.exp(D))
            resp = ex[K_DELTA] - c0[K_DELTA]
            vr = [conv2(x, mfa * math.exp(mdn)), c0, conv2(x, mfa * math.exp(mup))]
            vi = [conv2(x, mfa * math.exp(-h)), c0, conv2(x, mfa * math.exp(h))]
            I = integrals(als, mfa, D, running=True)
            cp2 = conv3(x, mfa)[K_P2]
            m = {
                "knot3real": lagrange([mdn, 0.0, mup], vr, D),
                "knot3ideal": lagrange([-h, 0.0, h], vi, D),
                "dglap2": dglap_shift(c0, I, order=2),
                "dglap2P2": dglap_shift(c0, I, order=2, use_p2=True, cv_p2=cp2),
            }
            where = "OUT" if (D > mup or D < mdn) else "in"
            line = (f"{bT:6g} {mfa:8.3f} {D / h:7.3f} {mdn / h:9.3f} {mup / h:9.3f} "
                    f"{where:>6} {resp:12.4e}")
            row = dict(qt=qt, x2live=x2live, bT=bT, muf_a=mfa, D=D, mdn=mdn, mup=mup,
                       true_resp=resp, where=where)
            for k in ("knot3real", "knot3ideal", "dglap2", "dglap2P2"):
                e = m[k][K_DELTA] - ex[K_DELTA]
                row[k] = e
                row[k + "_frac"] = e / resp if resp else float("nan")
                line += f" {100 * e / resp:+9.2f}%" if resp else f"{'--':>10}"
            print(line)
            partB.append(row)
    res["partB"] = partB

    with open(args.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
