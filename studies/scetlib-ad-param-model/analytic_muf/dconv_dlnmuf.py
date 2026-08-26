#!/usr/bin/env python3
"""Is an ANALYTIC d(conv)/d(ln muF) enough where D ~ 1.15 ln f?

THE GATE EXPERIMENT for the analytic-DGLAP route.  It needs no prototype and no
cross-section run: `DrellYan.conv_probe(x, muf, pid, side)` returns exactly the
beam convolutions the node cache freezes, at ANY muF, so the exact muF
dependence can be sampled directly and every candidate model tested against it.

WHAT IS COMPARED, all at the same (x, muf_anchor) and displacement
D = ln(muF_live / muF_frozen):

  exact      conv_probe(x, muf_anchor * exp(D))          -- LHAPDF, no model
  knot3      Lagrange quadratic through D = -h, 0, +h    -- THE SHIPPED MODEL
             (h = ln f, and the stencil is placed at EXACTLY +-h, which is the
             most generous possible reading of the shipped scheme: per node the
             real member positions collapse toward zero at large bT)
  knot5      Lagrange quartic through -h, -h/2, 0, h/2, h
  dglap1     conv + D (dconv/dlnmuF)_DGLAP              -- ONE analytic column
  dglap2     the TRUNCATED DGLAP evolution to ALL orders in D

THE POINT OF dglap2.  d/dlnmuF raises the alphas order of a conv kind by one
(f -> P0 (x) f -> P0 (x) P0 (x) f), and the kind set is truncated at fo_lvl.  So
the generator M is NILPOTENT: M^(fo_lvl+1) = 0 identically, and exp(D M) is a
POLYNOMIAL of degree fo_lvl.  At fo_lvl = 2 that is
    delta(D) = delta + I1 P0 + I2 P1 + I11 P0xP0
    P0(D)    = P0 + I1 P0xP0
    I1c(D)   = I1c + I1 (I1xP0)
    everything else: derivative is order alphas^3, i.e. beyond the computed
    order, so it is truncated to zero -- consistently, since those kinds are
    multiplied by alphas^2 in the kernel.
with  I1 = int 2g,  I2 = int 2g^2,  I11 = int 2g(L) [int 2g],  g = alphas/(4pi),
alphas at muF and RUNNING over the interval (the fixed-alphas variant is also
reported).  There is therefore NO O(D^2) truncation to worry about: the D series
terminates exactly.  The only question left is how well the fixed-order DGLAP
kernels reproduce LHAPDF's OWN grid evolution, which is what this measures.

CONVENTION, fixed from SCETlib's own I1 (Beam_coeffs_quark_formulas.hpp):
    k[0] = 2 Lf P0 + I1,   Lf = log(muB/muF)
muF-independence at O(alphas) then forces
    d(conv)/d(ln muF) = 2 (as/4pi) P0(x)conv + 2 (as/4pi)^2 P1(x)conv + ...
and the O(alphas^2) Lf terms of I2 reproduce the same relation with alphas at
muF (checked analytically; the b0 Lf leftover is exactly the running of alphas).

NO conv kind that the model does not ALREADY store is needed: P0(x)f, P1(x)f,
P0xP0(x)f, I1xP0(x)f are conv kinds c_p0, c_p1, c_p0p0, c_i1p0.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)

# ad::Conv_kind, fo_lvl = 2 prefix
K_DELTA, K_P0, K_I1QQ, K_I1QG, K_P0P0, K_P1, K_I1P0 = 0, 1, 2, 3, 4, 5, 6
K_I2 = (7, 8, 9, 10)
NKIND = 11
KIND_NAME = ["delta", "p0", "i1_qq", "i1_qg", "p0p0", "p1", "i1p0",
             "i2_qqV", "i2_qqbarV", "i2_qqS", "i2_qg"]
KIND_ORDER = [0, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2]

B0 = 2.0 * math.exp(-np.euler_gamma)
QZ = 91.1876
MUF_MIN = 1.40
X1A, X2A, X3A = 0.2, 0.6, 1.0


# ---------------------------------------------------------------- geometry ---
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


def node_muf(bT, xx, x1, x2, x3, fo_muf=QZ):
    """muF at one bT node for transition points (x1,x2,x3), kappa_F = 1."""
    y = mu_star(B0 / bT, MUF_MIN) / QZ
    g = g_run(xx, x1, x2, x3)
    return fo_muf * (g * y + (1.0 - g))


# ------------------------------------------------------------------ alphas ---
class Alphas:
    """PDF-set alphaS; g = alphas/(4 pi)."""

    def __init__(self, setname):
        import lhapdf
        self._p = lhapdf.mkPDF(setname, 0)

    def g(self, mu):
        return self._p.alphasQ(mu) / (4.0 * math.pi)


def integrals(als, muf0, D, running=True, n=64):
    """I1 = int_0^D 2g, I2 = int_0^D 2g^2, I11 = int_0^D 2g(L) [int_0^L 2g]."""
    if not running:
        g = als.g(muf0)
        return 2.0 * g * D, 2.0 * g * g * D, 2.0 * g * g * D * D
    if D == 0.0:
        return 0.0, 0.0, 0.0
    L = np.linspace(0.0, D, n + 1)
    g = np.array([als.g(muf0 * math.exp(l)) for l in L])
    two_g = 2.0 * g
    # cumulative trapezoid of 2g
    cum = np.concatenate(([0.0], np.cumsum(0.5 * (two_g[1:] + two_g[:-1]) * np.diff(L))))
    I1 = cum[-1]
    I2 = np.trapezoid(2.0 * g * g, L) if hasattr(np, "trapezoid") else np.trapz(2.0 * g * g, L)
    integ = two_g * cum
    I11 = np.trapezoid(integ, L) if hasattr(np, "trapezoid") else np.trapz(integ, L)
    return I1, I2, I11


# ------------------------------------------------------------------- models ---
def dglap_shift(cv0, I1, I2, I11, order=2, split_i1=True):
    """Truncated-DGLAP evolution of the conv vector by displacement D.

    order=1 keeps only the single derivative column (D^1);
    order=2 keeps the full nilpotent series (exact in D for fo_lvl = 2).
    """
    out = cv0.copy()
    out[K_DELTA] = cv0[K_DELTA] + I1 * cv0[K_P0] + I2 * cv0[K_P1]
    if order >= 2:
        out[K_DELTA] += I11 * cv0[K_P0P0]
    out[K_P0] = cv0[K_P0] + I1 * cv0[K_P0P0]
    # I1xP0 is stored only as the TOTAL; split it between the qq and qg TNP
    # slots in the ratio of the I1 pieces themselves so the SUM is exact.
    i1tot = cv0[K_I1QQ] + cv0[K_I1QG]
    if split_i1 and i1tot != 0.0:
        wqq = cv0[K_I1QQ] / i1tot
    else:
        wqq = 1.0
    out[K_I1QQ] = cv0[K_I1QQ] + I1 * cv0[K_I1P0] * wqq
    out[K_I1QG] = cv0[K_I1QG] + I1 * cv0[K_I1P0] * (1.0 - wqq)
    # order-2 kinds: their derivative is order alphas^3 -> truncated
    return out


def lagrange(nodes, values, D):
    """Lagrange interpolation of vector-valued `values` at `nodes`, at D."""
    nodes = np.asarray(nodes, float)
    out = np.zeros_like(values[0])
    for i, xi in enumerate(nodes):
        w = 1.0
        for j, xj in enumerate(nodes):
            if i != j:
                w *= (D - xj) / (xi - xj)
        out = out + w * values[i]
    return out


# --------------------------------------------------------------------- main ---
def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="/ceph/submit/data/group/cms/store/user/"
                    "lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--knot", type=float, default=2.0, help="outer knot f")
    ap.add_argument("--pid", type=int, default=2)
    ap.add_argument("--side", type=int, default=0)
    ap.add_argument("--pdf-set", default="CT18ZNNLO")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()

    import scetlib_qT  # noqa: F401
    from wremnants.postprocessing.scetlib_ad.xsec_backend import configure

    _, s = configure(args.base, threads=args.threads, diff_scales=True)
    sing, _ = s.sub_pieces()
    als = Alphas(args.pdf_set)

    def conv(x, muf):
        return np.asarray(sing.conv_probe(x, muf, args.pid, args.side), float)[:NKIND]

    h = math.log(args.knot)
    Y = 0.075
    xA = (QZ / 13000.0) * math.exp(Y)
    xB = (QZ / 13000.0) * math.exp(-Y)
    x = xA if args.side == 0 else xB

    results = {"h": h, "x": x, "pid": args.pid, "side": args.side, "cases": []}

    # ---------------------------------------------------------------------
    # PART A. Is the analytic derivative the RIGHT derivative?  Compare it with
    # a converged central difference of conv_probe itself.
    # ---------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("A. ANALYTIC dconv/dlnmuF vs a converged CENTRAL DIFFERENCE of conv_probe")
    print("   (relative difference; this measures fixed-order DGLAP against")
    print("    LHAPDF's own grid evolution, and nothing else)")
    print("=" * 78)
    print(f"{'muF':>7} {'kind':>8} {'d/dlnmuF (FD)':>16} {'analytic':>14} "
          f"{'rel diff':>11} {'only 2g P0':>12}")
    partA = []
    for muf in (3.0, 5.0, 8.0, 13.0, 20.0, 45.0, 91.1876):
        eps = 1e-3
        cvp = conv(x, muf * math.exp(eps))
        cvm = conv(x, muf * math.exp(-eps))
        cv0 = conv(x, muf)
        fd = (cvp - cvm) / (2.0 * eps)
        g = als.g(muf)
        an_lo = 2.0 * g * cv0[K_P0]
        an = an_lo + 2.0 * g * g * cv0[K_P1]
        row = dict(muf=muf, fd_delta=fd[K_DELTA], an_delta=an,
                   an_lo_delta=an_lo,
                   fd_p0=fd[K_P0], an_p0=2.0 * g * cv0[K_P0P0],
                   fd_i1=fd[K_I1QQ] + fd[K_I1QG], an_i1=2.0 * g * cv0[K_I1P0])
        partA.append(row)
        print(f"{muf:7.2f} {'delta':>8} {fd[K_DELTA]:16.6e} {an:14.6e} "
              f"{an / fd[K_DELTA] - 1.0:+11.2e} {an_lo / fd[K_DELTA] - 1.0:+12.2e}")
        print(f"{'':7} {'p0':>8} {fd[K_P0]:16.6e} {2.0 * g * cv0[K_P0P0]:14.6e} "
              f"{2.0 * g * cv0[K_P0P0] / fd[K_P0] - 1.0:+11.2e}")
        i1fd = fd[K_I1QQ] + fd[K_I1QG]
        print(f"{'':7} {'i1(sum)':>8} {i1fd:16.6e} {2.0 * g * cv0[K_I1P0]:14.6e} "
              f"{2.0 * g * cv0[K_I1P0] / i1fd - 1.0:+11.2e}")
    results["partA"] = partA

    # ---------------------------------------------------------------------
    # PART B. Model error at FINITE D, including the template-sized D.
    # ---------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("B. MODEL ERROR AT FINITE D -- error as a FRACTION OF THE TRUE RESPONSE")
    print("   of conv[delta], which is I[0] of the beam function.")
    print(f"   knots at +-{h:.4f} (= ln {args.knot:g}) and, for knot5, +-{h/2:.4f}")
    print("=" * 78)
    Ds = [0.1 * h, 0.25 * h, 0.5 * h, 0.75 * h, 1.0 * h, 1.15 * h, 1.5 * h, 1.74 * h,
          -0.5 * h, -1.0 * h, -1.15 * h]
    partB = []
    for muf in (5.0, 8.0, 13.0, 20.0):
        cv0 = conv(x, muf)
        kn3 = [conv(x, muf * math.exp(d)) for d in (-h, 0.0, h)]
        kn5 = [conv(x, muf * math.exp(d)) for d in (-h, -h / 2, 0.0, h / 2, h)]
        print(f"\n  muF_anchor = {muf:g} GeV   (x = {x:.5f}, alphaS = "
              f"{4 * math.pi * als.g(muf):.4f})")
        print(f"{'D/lnf':>7} {'true resp':>12} {'knot3':>11} {'knot5':>11} "
              f"{'dglap1':>11} {'dglap2':>11} {'dglap2fix':>11}")
        for D in Ds:
            ex = conv(x, muf * math.exp(D))
            resp = ex[K_DELTA] - cv0[K_DELTA]
            I1, I2, I11 = integrals(als, muf, D, running=True)
            I1f, I2f, I11f = integrals(als, muf, D, running=False)
            m = {
                "knot3": lagrange([-h, 0.0, h], kn3, D),
                "knot5": lagrange([-h, -h / 2, 0.0, h / 2, h], kn5, D),
                "dglap1": dglap_shift(cv0, I1, I2, I11, order=1),
                "dglap2": dglap_shift(cv0, I1, I2, I11, order=2),
                "dglap2fix": dglap_shift(cv0, I1f, I2f, I11f, order=2),
            }
            row = dict(muf=muf, D=D, D_over_h=D / h, true_resp=resp,
                       cv0_delta=cv0[K_DELTA])
            line = f"{D / h:7.2f} {resp:12.4e}"
            for k in ("knot3", "knot5", "dglap1", "dglap2", "dglap2fix"):
                e = m[k][K_DELTA] - ex[K_DELTA]
                row[k] = e
                row[k + "_frac"] = e / resp if resp else float("nan")
                line += f" {100.0 * e / resp:+10.2f}%" if resp else f" {'--':>11}"
            print(line)
            partB.append(row)
    results["partB"] = partB

    # ---------------------------------------------------------------------
    # PART C. The REAL nodes of the x2 = 0.35 template leg: (muF_anchor, D)
    # pairs taken from SCETlib's own scale formulas, and the model error there.
    # ---------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("C. AT THE REAL NODES OF THE TEMPLATE LEG  x2: 0.6 -> 0.35")
    print("   muF_anchor and D from SCETlib's scale formulas per (qT, bT) node.")
    print("   Error on conv[delta] as a fraction of that node's TRUE response.")
    print("=" * 78)
    partC = []
    for qt, x2live in ((22.0, 0.35), (26.0, 0.35), (30.0, 0.35), (38.0, 0.35),
                       (30.0, 0.55)):
        xx = qt / QZ
        print(f"\n  qT = {qt:g}  (x = {xx:.4f}), x2: {X2A} -> {x2live}")
        print(f"{'bT':>6} {'muF_a':>8} {'D':>8} {'D/lnf':>7} {'true resp':>12} "
              f"{'knot3':>11} {'knot5':>11} {'dglap1':>11} {'dglap2':>11}")
        for bT in (0.1, 0.2, 0.35, 0.5, 0.8, 1.2, 2.0, 3.0, 5.0):
            mfa = node_muf(bT, xx, X1A, X2A, X3A)
            mfl = node_muf(bT, xx, X1A, x2live, X3A)
            D = math.log(mfl / mfa)
            if mfa < 1.3:
                continue
            cv0 = conv(x, mfa)
            ex = conv(x, mfa * math.exp(D))
            resp = ex[K_DELTA] - cv0[K_DELTA]
            kn3 = [conv(x, mfa * math.exp(d)) for d in (-h, 0.0, h)]
            kn5 = [conv(x, mfa * math.exp(d)) for d in (-h, -h / 2, 0.0, h / 2, h)]
            I1, I2, I11 = integrals(als, mfa, D, running=True)
            m = {
                "knot3": lagrange([-h, 0.0, h], kn3, D),
                "knot5": lagrange([-h, -h / 2, 0.0, h / 2, h], kn5, D),
                "dglap1": dglap_shift(cv0, I1, I2, I11, order=1),
                "dglap2": dglap_shift(cv0, I1, I2, I11, order=2),
            }
            line = (f"{bT:6g} {mfa:8.3f} {D:8.4f} {D / h:7.3f} {resp:12.4e}")
            row = dict(qt=qt, x2live=x2live, bT=bT, muf_a=mfa, D=D,
                       true_resp=resp, cv0_delta=cv0[K_DELTA])
            for k in ("knot3", "knot5", "dglap1", "dglap2"):
                e = m[k][K_DELTA] - ex[K_DELTA]
                row[k] = e
                row[k + "_frac"] = e / resp if resp else float("nan")
                line += f" {100.0 * e / resp:+10.2f}%" if resp else f" {'--':>11}"
            print(line)
            partC.append(row)
    results["partC"] = partC

    with open(args.out, "w") as f:
        json.dump(results, f, indent=1, default=float)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
