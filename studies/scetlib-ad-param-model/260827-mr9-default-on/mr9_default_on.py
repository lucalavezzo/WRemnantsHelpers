#!/usr/bin/env python3
"""MR !9 with the analytic DGLAP muF evolution ON BY DEFAULT: the invariants,
the alpha_s-equivalent projection, and the cost -- all from ONE cache, in ONE
process.

WHY ONE PROCESS. Two independent runs of the same baseline differ by 0.3-3.7
percentage points of the response bin by bin, and two independently BUILT caches
of the same runcard part by up to 1.9e-03 in sigma at a displaced muF, while an
A/B taken inside one cache reproduces to 0.1 pp. So every number here is a
DIFFERENCE between two arms that share the cache, the nodes, the rules, the
members and the re-solved weights, and differ only in
``DrellYan.set_muf_analytic``.

THE THREE ARMS. off = mode 0 (the pre-MR model), on = the new DEFAULT (asserted
to be mode 1 before anything is set), and clamp = mode 1 with ad_muf_abl bit 32,
present only to prove the arms are separated: ``values_and_jacobian`` memoises
on the parameter vector ALONE, so an A/B that forgets to drop the key returns
one arm's numbers for both and shows a perfect, wrong null. Three arms must give
three different sums.

WHAT IT REPORTS
  1. the built-in default of ad_muf_anl, read back through pybind;
  2. sizeof(ad::GlobalData) as the existing cache's rule blob stores it, plus
     the fact that this build LOADS that cache (the layout check is what would
     refuse it);
  3. central and kappa_F = 0.5, 2 responses, on vs off (must be 0.000e+00);
  4. every mapped template direction, on vs off, so "36 of 39 unchanged" is a
     count rather than a claim;
  5. the residual against the production CorrZ templates per direction and arm,
     and its alpha_s-equivalent through ``lowqt_nonsingular_attribution``'s
     profiled projection (the same solve, the same nuisance basis, the same
     sigma(alpha_s) = 6.16e-4, so the ranking stays comparable to earlier
     rounds). The OFF arm is passed as its ``d`` and the ON arm as its
     ``d_aligned``, which is exactly the before/after that function scores;
  6. warm timing of values_and_jacobian and of hessian, on vs off.
"""
import argparse
import os
import struct
import sys
import time
import zipfile

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)
sys.path.insert(0, os.path.join(WREM, "scripts", "rabbit", "scetlib_ad"))
STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, STUDY)

from lowqt_nonsingular_attribution import SIG_AS, alphas_equivalents  # noqa: E402

TRANS_PREFIX = "transition_points"


def rule_globaldata_size(cache_npz):
    """sizeof(ad::GlobalData) as the cache's rule blob records it.

    Header of the compressed-rule file: the 8-byte magic SCTRULE<version> (a
    char[8], NOT NUL-terminated) then four little-endian uint32 -- the sizeof of
    Bin_rule::Site, ad::GlobalData, ad::HardData, ad::NodeData. Read here rather
    than asked of the build because the point is what is ON DISK; the build's
    own value is checked by load_bin_rules' layout_check refusing the file if it
    differs by even one byte. Streamed out of the zip member so the 1.1 GB blob
    is never materialised.
    """
    with zipfile.ZipFile(cache_npz) as z:
        with z.open("rules.npy") as f:
            head = f.read(4096)
    i = head.index(b"SCTRULE")
    sz = struct.unpack_from("<4I", head, i + 8)
    return dict(magic=head[i:i + 8].decode(), site=sz[0], globaldata=sz[1],
                harddata=sz[2], nodedata=sz[3])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--conf", required=True)
    ap.add_argument("--corr", required=True, nargs="+")
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--npz", default=None)
    args = ap.parse_args()

    import scetlib_qT
    from validate_variations import (  # noqa: E402
        central_label, load_corr, merge_matrix, variation_for,
    )
    from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

    # ---------------------------------------------------------------- (1) --
    dflt = scetlib_qT.DrellYan.muf_analytic()
    print(f"[1] BUILT-IN DEFAULT ad_muf_anl = {dflt}   (MR !9 as merged: 1)")
    print(f"    ad_muf_i1 default          = {scetlib_qT.DrellYan.muf_analytic_i1()}")
    if dflt != 1:
        raise SystemExit("this build is NOT the default-on build; refusing.")

    # ---------------------------------------------------------------- (2) --
    info = rule_globaldata_size(args.cache)
    print(f"[2] rule blob layout, as the EXISTING cache stores it: {info}")

    core = ScetlibADXsec(args.conf, args.cache, threads=args.threads)
    print(f"    cache LOADED under the default-on build: {core.n_bins} bins, "
          f"{core.n_params} params  -> the layout check passed, i.e. every "
          f"sizeof in that header equals this build's")
    names = list(core.param_names)
    b = core.bins
    yl = np.unique(np.round(b[:, 2:4], 12), axis=0)
    tl = np.unique(np.round(b[:, 4:6], 12), axis=0)
    yl, tl = yl[np.argsort(yl[:, 0])], tl[np.argsort(tl[:, 0])]
    Ye = np.concatenate([yl[:, 0], yl[-1:, 1]])
    Te = np.concatenate([tl[:, 0], tl[-1:, 1]])
    fold = core.fold_for([("ptVGen", Te), ("absYVGen", Ye)], b[0, 0], b[0, 1],
                         partial=True)
    cover = fold.covered_mask.T
    anchor = core.anchor.copy()

    def set_arm(mode, abl=0):
        """Select the arm AND drop the memo key -- see the module docstring."""
        scetlib_qT.DrellYan.set_muf_analytic(mode)
        scetlib_qT.DrellYan.set_muf_ablate(abl)
        core.tf_fn._cache_key = None
        core.tf_fn._hess_cache_key = None

    def model(overrides, raw=False):
        p = anchor.copy()
        for k, v in overrides.items():
            if k not in names:
                return None
            p[names.index(k)] = v
        vals, J = core.values_and_jacobian(p)
        g = fold(np.asarray(vals, float)).reshape(Te.size - 1, Ye.size - 1).T
        return (g, J) if raw else g

    ARMS = (("off", 0, 0), ("on", 1, 0), ("clamp", 1, 32))

    # ---------------------------------------------------------------- (3) --
    cen, Jc = {}, {}
    for tag, m, a in ARMS:
        set_arm(m, a)
        cen[tag], Jc[tag] = model({}, raw=True)
    print("\n[3] INVARIANTS, max over covered gen bins of |on/off - 1|")
    dcen = float(np.nanmax(np.abs(cen["on"] / cen["off"] - 1.0)))
    print(f"    central value                       {dcen:.3e}")
    for kf in (0.5, 2.0):
        r = {}
        for tag, m, a in ARMS:
            set_arm(m, a)
            r[tag] = model({"scale_kappa_F": kf}) / cen[tag]
        d = float(np.nanmax(np.abs(r["on"] / r["off"] - 1.0)))
        print(f"    kappa_F = {kf:<4g} response              {d:.3e}")

    # arm separation: three arms, three sums, at a transition point
    sums = {}
    for tag, m, a in ARMS:
        set_arm(m, a)
        sums[tag] = float(np.nansum(model({"scale_x2": 0.35})))
    print(f"\n    ARM SEPARATION at x2 = 0.35, sum over gen bins:")
    for tag in sums:
        print(f"      {tag:<6} {sums[tag]:.12e}")
    if len({round(v, 12) for v in sums.values()}) != 3:
        raise SystemExit("the three arms are not three arms; refusing to report.")

    # ---------------------------------------------------------------- (4) --
    set_arm(1, 0)
    _, J_on = core.values_and_jacobian(anchor)
    R_as = fold(np.asarray(J_on[:, names.index("alphas")], float)).reshape(
        Te.size - 1, Ye.size - 1).T / cen["on"]

    rows = {}
    labels_out = []
    resid = {"off": [], "on": []}
    rr_all = []
    for path in args.corr:
        h = load_corr(path)
        ax = {a.name: a for a in h.axes}
        labs = [str(x) for x in ax["vars"]]
        vv = np.asarray(h.values(flow=False))
        dims = [a.name for a in h.axes]
        vv = np.squeeze(vv, axis=(dims.index("Q"), dims.index("charge")))
        order = [d for d in dims if d not in ("Q", "charge")]
        vv = np.moveaxis(vv, [order.index("absY"), order.index("qT"),
                              order.index("vars")], [0, 1, 2])
        MY = merge_matrix(ax["absY"].edges, Ye, "absY")
        MT = merge_matrix(ax["qT"].edges, Te, "qT")

        def ref(L):
            return MY @ vv[:, :, labs.index(L)] @ MT.T

        cen_lab = central_label(labs)
        r_cen = ref(cen_lab)
        for L in labs:
            ov = variation_for(L)
            if L == cen_lab or ov is None or any(k not in names for k in ov):
                continue
            rr = ref(L) / np.where(r_cen == 0, np.nan, r_cen)
            per = {}
            for tag, m, a in ARMS[:2]:
                set_arm(m, a)
                sv = model(ov)
                rm = sv / cen[tag]
                good = cover & np.isfinite(rm) & np.isfinite(rr) & (rr != 0)
                dv = np.where(good, rm / rr - 1.0, np.nan)
                per[tag] = dict(rm=rm, d=dv,
                                maxdev=float(np.nanmax(np.abs(dv))),
                                meandev=float(np.nanmean(np.abs(dv))))
            ab = float(np.nanmax(np.abs(per["on"]["rm"] / per["off"]["rm"] - 1.0)))
            rows[L] = dict(ab=ab, off=per["off"], on=per["on"],
                           resp=float(np.nanmax(np.abs(rr - 1.0))))
            labels_out.append(L)
            resid["off"].append(per["off"]["d"])
            resid["on"].append(per["on"]["d"])
            rr_all.append(rr)

    print(f"\n[4] EVERY MAPPED TEMPLATE DIRECTION, on vs off "
          f"({len(labels_out)} directions)")
    print(f"    {'direction':<36}{'max|on/off-1|':>15}{'response':>11}"
          f"{'off max|dev|':>14}{'on max|dev|':>13}{'off mean':>11}{'on mean':>10}")
    nz = []
    for L in labels_out:
        r = rows[L]
        flag = " <-- MOVES" if r["ab"] != 0.0 else ""
        if r["ab"] != 0.0:
            nz.append(L)
        print(f"    {L:<36}{r['ab']:>15.3e}{r['resp']:>11.2e}"
              f"{r['off']['maxdev']:>14.3e}{r['on']['maxdev']:>13.3e}"
              f"{r['off']['meandev']:>11.3e}{r['on']['meandev']:>10.3e}{flag}")
    print(f"\n    directions with max|on/off - 1| EXACTLY 0.000e+00: "
          f"{len(labels_out) - len(nz)} of {len(labels_out)}")
    print(f"    directions that move: {len(nz)} -> {nz}")
    bad = [L for L in nz if not L.startswith(TRANS_PREFIX)]
    print(f"    non-transition directions that move: {len(bad)} {bad}")

    # ---------------------------------------------------------------- (5) --
    z = dict(labels=np.array(labels_out), d=np.array(resid["off"]),
             d_aligned=np.array(resid["on"]), rr=np.array(rr_all),
             R_as=R_as, s_cen=cen["on"], cover=cover, Te=Te, Ye=Ye)
    eq_bef = alphas_equivalents(z, N=1e7)
    z2 = dict(z); z2["d"], z2["d_aligned"] = z["d_aligned"], z["d"]
    eq_aft = alphas_equivalents(z2, N=1e7)
    print(f"\n[5] alpha_s-EQUIVALENT of the residual, profiled over the other "
          f"nuisances  (sigma(alpha_s) = {SIG_AS:.2e})")
    print(f"    {'direction':<36}{'before':>12}{'after':>12}"
          f"{'before/sig':>12}{'after/sig':>11}{'|after|/|before|':>18}")
    for L in labels_out:
        bfr, aft = eq_bef[L][0], eq_aft[L][0]
        rat = abs(aft) / abs(bfr) if bfr else np.nan
        star = "  <-- TRANSITION" if L.startswith(TRANS_PREFIX) else ""
        print(f"    {L:<36}{bfr:>+12.3e}{aft:>+12.3e}"
              f"{bfr/SIG_AS:>+12.4f}{aft/SIG_AS:>+11.4f}{rat:>18.3f}{star}")
    tr = [L for L in labels_out if L.startswith(TRANS_PREFIX)]
    qb = np.sqrt(sum(eq_bef[L][0] ** 2 for L in tr))
    qa = np.sqrt(sum(eq_aft[L][0] ** 2 for L in tr))
    print(f"\n    TRANSITION GROUP, quadrature over {len(tr)} directions:")
    print(f"      before {qb:.4e} = {qb/SIG_AS:.4f} sigma(alpha_s)")
    print(f"      after  {qa:.4e} = {qa/SIG_AS:.4f} sigma(alpha_s)")
    print(f"      ratio after/before {qa/qb:.4f}"
          f"   ({'IMPROVES' if qa < qb else 'WORSENS'})")
    print(f"\n    the same with qT [0,1] dropped (col 3) and [0,2] dropped (col 4):")
    for L in tr:
        print(f"      {L:<36} before {eq_bef[L][2]:+.3e} / {eq_bef[L][3]:+.3e}"
              f"   after {eq_aft[L][2]:+.3e} / {eq_aft[L][3]:+.3e}")

    # ---------------------------------------------------------------- (6) --
    print(f"\n[6] TIMING, warm, same process, same cache, {core.n_bins} bins, "
          f"threads={args.threads}, reps={args.reps}")
    print(f"    {'arm':<8}{'value+jacobian [s]':>22}{'hessian [s]':>16}")
    tt = {}
    for tag, m, a in ARMS[:2]:
        vj, hs = [], []
        for i in range(args.reps + 1):
            set_arm(m, a)
            t0 = time.perf_counter(); core.values_and_jacobian(anchor)
            t1 = time.perf_counter(); core.hessian(anchor); t2 = time.perf_counter()
            if i:                      # drop the first: warm only
                vj.append(t1 - t0); hs.append(t2 - t1)
        tt[tag] = (float(np.median(vj)), float(np.median(hs)), vj, hs)
        print(f"    {tag:<8}{np.median(vj):>22.3f}{np.median(hs):>16.3f}"
              f"   (all: {['%.3f' % x for x in vj]} / "
              f"{['%.3f' % x for x in hs]})")
    print(f"    on/off  value+jacobian {tt['on'][0]/tt['off'][0]:.4f}   "
          f"hessian {tt['on'][1]/tt['off'][1]:.4f}")

    scetlib_qT.DrellYan.set_muf_ablate(0)
    scetlib_qT.DrellYan.set_muf_analytic(dflt)
    if args.npz:
        np.savez(args.npz, labels=np.array(labels_out), d_off=np.array(resid["off"]),
                 d_on=np.array(resid["on"]), rr=np.array(rr_all), R_as=R_as,
                 s_cen=cen["on"], cover=cover, Te=Te, Ye=Ye,
                 eq_before=np.array([eq_bef[L][0] for L in labels_out]),
                 eq_after=np.array([eq_aft[L][0] for L in labels_out]),
                 timing=np.array([[tt['off'][0], tt['off'][1]],
                                  [tt['on'][0], tt['on'][1]]]),
                 cache=os.path.abspath(args.cache))
        print(f"\nwrote {args.npz}")


if __name__ == "__main__":
    main()
