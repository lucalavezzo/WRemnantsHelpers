#!/usr/bin/env python3
r"""The gen qT > 100 region of the response matrix: spectrum, reco feed, controls.

The theory correction (CorrZ) stops at gen qT 100 and its flow bins are EXACTLY
1.0, so the histmaker's MiNNLO events above 100 are uncorrected while the
differentiable model would predict a corrected cross section there.  Luca's
decision is to extend the CORRECTION above 100, which makes the two sides
consistent again -- and makes the response gen binning above 100 a
SPECIFICATION that his production has to match edge for edge.

This measures the numbers that specification needs, off one histmaker run made
with

    mz_dilepton --responseGenBinning theoryCorr --responseGenPtVExtend ...

i.e. the correction's own 70-bin qT grid plus a fine DIAGNOSTIC extension above
100.  Because R_raw is additive under gen rebinning, any candidate final grid
whose edges are a sub-union of the diagnostic ones is obtained by summing
columns -- so one run scores every candidate.

Reported per above-100 bin:
  * N_gen fraction (of the gen-fiducial total, |Y| < 2.5, all qT)
  * the reco yield it feeds INTO THE FIT's reco bins (ptll < 44), absolute and
    as a fraction of that bin's total corrected-MC yield
  * the same for reco ptll [44, 100], which the fit does not use today

Controls (each an identity, not an approximation):
  * the extended response summed over gen qT < 100 reproduces the unextended one
  * the extended response coarsened onto the unfolding grid equals the unfolding
    hist summed over its helicity partition
  * every gen bin has N_gen > 0, so the grid tiles exactly for GenFold
"""

import argparse
import os
import sys

import numpy as np

_WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
if _WREM not in sys.path:
    sys.path.insert(0, _WREM)

SAMPLE = "Zmumu_2016PostVFP"


def load(path, names):
    import h5py

    from wums import ioutils as wums_io

    out = {}
    with h5py.File(path, "r") as f:
        s = wums_io.pickle_load_h5py(f[SAMPLE])
        for n in names:
            if n not in s["output"]:
                out[n] = None
                continue
            p = s["output"][n]
            out[n] = p.get() if hasattr(p, "get") else p
    return out


def resp_arrays(h):
    """(R_raw in-range, R_raw gen-qT-overflow) at acceptance=True, reco (yll,ptll)."""
    hp = h[{"acceptance": True}].project("yll", "ptll", "ptVGen", "absYVGen")
    full = hp.values(flow=True)
    ny, npt = hp.axes["yll"].size, hp.axes["ptll"].size
    nq, nay = hp.axes["ptVGen"].size, hp.axes["absYVGen"].size
    yoff = 1 if hp.axes["yll"].traits.underflow else 0
    inr = full[yoff : yoff + ny, 0:npt, 0:nq, 0:nay]
    ov = full[yoff : yoff + ny, 0:npt, nq, 0:nay]
    return (
        np.asarray(inr, dtype=np.float64),
        np.asarray(ov, dtype=np.float64),
        {n: np.asarray(hp.axes[n].edges, float) for n in ("yll", "ptll", "ptVGen", "absYVGen")},
    )


def gen_arrays(h):
    v = h.values(flow=True)
    nq, nay = h.axes["ptVGen"].size, h.axes["absYVGen"].size
    return (
        np.asarray(v[0:nq, 0:nay], float),
        float(v[nq, 0:nay].sum()),
        np.asarray(h.axes["ptVGen"].edges, float),
        np.asarray(h.axes["absYVGen"].edges, float),
    )


def merge_axis(a, axis, group_edges, edges):
    """Sum ``a`` along ``axis`` into the bins of ``group_edges`` (a sub-union)."""
    idx = [int(np.argmin(np.abs(edges - e))) for e in group_edges]
    for k, e in zip(idx, group_edges):
        if abs(edges[k] - e) > 1e-9:
            raise SystemExit(f"edge {e} not on the axis ({edges[k]} nearest)")
    parts = [
        a.take(range(idx[i], idx[i + 1]), axis=axis).sum(axis=axis, keepdims=True)
        for i in range(len(idx) - 1)
    ]
    return np.concatenate(parts, axis=axis)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--histmaker", required=True, help="the EXTENDED run")
    ap.add_argument("--ref-histmaker", default=None,
                    help="an UNEXTENDED run, for the restriction control")
    ap.add_argument("--fit-ptll-bins", type=int, default=39,
                    help="number of reco ptll bins the fit uses (from 0)")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--candidates", nargs="*", default=None,
                    help="candidate final grids above 100, each a comma list of "
                         "edges starting at 100, e.g. 100,120,150 100,120,160,220")
    args = ap.parse_args()

    H = load(args.histmaker, ["nominal_prefsr_yieldsResponse", "prefsr_response",
                              "nominal_prefsr_yieldsUnfolding", "prefsr", "nominal"])
    R_in, R_ov, ax = resp_arrays(H["nominal_prefsr_yieldsResponse"])
    N_in, N_ov, qt, ay = gen_arrays(H["prefsr_response"])
    npt_fit = args.fit_ptll_bins
    ptl = ax["ptll"]
    i100 = int(np.where(np.isclose(qt, 100.0))[0][0])

    Ntot = N_in.sum() + N_ov
    print("=" * 78)
    print("GEN GRID")
    print(f"  ptVGen  {len(qt)-1} bins, last edge {qt[-1]:g}; above 100: "
          f"{len(qt)-1-i100} bins {list(qt[i100:])}")
    print(f"  absYVGen {len(ay)-1} bins to {ay[-1]:g}")
    print(f"  N_gen total (gen-fiducial, incl. qT overflow) {Ntot:.6e}")
    print(f"  N_gen above the axis (qT > {qt[-1]:g})  {N_ov:.6e}   "
          f"frac {N_ov/Ntot:.4e}")
    above = N_in[i100:, :].sum() + N_ov
    print(f"  N_gen qT > 100  {above:.6e}   frac {above/Ntot:.6f}")

    # ---- per above-100 bin: gen fraction and reco feed
    fit_tot = R_in[:, :npt_fit].sum() + R_ov[:, :npt_fit].sum()
    hi_tot = R_in[:, npt_fit:].sum() + R_ov[:, npt_fit:].sum()
    print()
    print("=" * 78)
    print("PER BIN ABOVE 100  (feed = corrected-MC reco yield fed by that gen bin)")
    print(f"{'gen qT bin':>18} {'N_gen frac':>11} {'tail>lo':>10} "
          f"{'feed fit':>11} {'/fit yield':>11} {'feed 44-100':>12} {'/that bin':>10}")
    rows = []
    for i in range(i100, len(qt) - 1):
        ng = N_in[i].sum()
        tail = N_in[i:].sum() + N_ov
        ffit = R_in[:, :npt_fit, i, :].sum()
        fhi = R_in[:, npt_fit:, i, :].sum()
        rows.append((qt[i], qt[i + 1], ng / Ntot, tail / Ntot, ffit, ffit / fit_tot,
                     fhi, fhi / hi_tot))
        print(f"  [{qt[i]:7.1f},{qt[i+1]:7.1f}] {ng/Ntot:11.4e} {tail/Ntot:10.4e} "
              f"{ffit:11.4e} {ffit/fit_tot:11.3e} {fhi:12.4e} {fhi/hi_tot:10.3e}")
    ng_ov, ffit_ov, fhi_ov = N_ov, R_ov[:, :npt_fit].sum(), R_ov[:, npt_fit:].sum()
    print(f"  [{qt[-1]:7.1f},    inf] {ng_ov/Ntot:11.4e} {ng_ov/Ntot:10.4e} "
          f"{ffit_ov:11.4e} {ffit_ov/fit_tot:11.3e} {fhi_ov:12.4e} {fhi_ov/hi_tot:10.3e}")
    print(f"  TOTAL above 100      {above/Ntot:11.4e}            "
          f"{R_in[:, :npt_fit, i100:, :].sum()+ffit_ov:11.4e} "
          f"{(R_in[:, :npt_fit, i100:, :].sum()+ffit_ov)/fit_tot:11.3e} "
          f"{R_in[:, npt_fit:, i100:, :].sum()+fhi_ov:12.4e} "
          f"{(R_in[:, npt_fit:, i100:, :].sum()+fhi_ov)/hi_tot:10.3e}")

    # ---- per-reco-bin worst case inside the fit
    num = R_in[:, :npt_fit, i100:, :].sum(axis=(2, 3)) + R_ov[:, :npt_fit].sum(axis=2)
    den = R_in[:, :npt_fit].sum(axis=(2, 3)) + R_ov[:, :npt_fit].sum(axis=2)
    frac = np.where(den > 0, num / np.where(den > 0, den, 1), 0.0)
    j = np.unravel_index(np.argmax(frac), frac.shape)
    print()
    print(f"  worst single FIT reco bin: yll [{ax['yll'][j[0]]:g},"
          f"{ax['yll'][j[0]+1]:g}] x ptll [{ptl[j[1]]:g},{ptl[j[1]+1]:g}]  "
          f"frac {frac[j]:.4e}")
    print(f"  fit-range total fraction from gen qT > 100: "
          f"{num.sum()/den.sum():.4e}   nonzero bins {int((frac>0).sum())}/{frac.size}")
    print("  per reco ptll bin (summed over yll):")
    for k in range(npt_fit):
        f = num[:, k].sum() / den[:, k].sum()
        if f > 0:
            print(f"     ptll [{ptl[k]:6.1f},{ptl[k+1]:6.1f}]  {f:.3e}")

    # ---- candidate groupings
    if args.candidates:
        print()
        print("=" * 78)
        print("CANDIDATE FINAL GRIDS ABOVE 100")
        for cand in args.candidates:
            ed = [float(x) for x in cand.split(",")]
            print(f"\n  candidate {ed}  ({len(ed)-1} bins)")
            Ng = merge_axis(N_in[i100:, :], 0, ed, qt[i100:])
            Rf = merge_axis(R_in[:, :npt_fit, i100:, :], 2, ed, qt[i100:])
            Rh = merge_axis(R_in[:, npt_fit:, i100:, :], 2, ed, qt[i100:])
            for i in range(len(ed) - 1):
                print(f"    [{ed[i]:7.1f},{ed[i+1]:7.1f}]  N_gen frac "
                      f"{Ng[i].sum()/Ntot:.4e}   feed fit {Rf[:,:,i,:].sum():.4e} "
                      f"({Rf[:,:,i,:].sum()/fit_tot:.3e})   feed 44-100 "
                      f"{Rh[:,:,i,:].sum():.4e} ({Rh[:,:,i,:].sum()/hi_tot:.3e})")
            drop = N_in[i100:].sum() + N_ov - Ng.sum()
            print(f"    DROPPED above {ed[-1]:g}: N_gen frac {drop/Ntot:.4e}, "
                  f"feed fit {R_in[:, :npt_fit, :, :].sum() + R_ov[:, :npt_fit].sum() - R_in[:, :npt_fit, :i100, :].sum() - Rf.sum():.4e}")

    # ---- controls
    print()
    print("=" * 78)
    print("CONTROLS")
    nz = int((N_in > 0).sum())
    print(f"  gen bins with N_gen > 0: {nz}/{N_in.size}"
          + ("  (exact tiling for GenFold OK)" if nz == N_in.size else "  <-- HOLES"))
    hu = H["nominal_prefsr_yieldsUnfolding"]
    hus = hu[{"acceptance": True}].project("yll", "ptll", "ptVGen", "absYVGen")
    fu = hus.values(flow=True)
    nyu, nptu = hus.axes["yll"].size, hus.axes["ptll"].size
    nqu, nayu = hus.axes["ptVGen"].size, hus.axes["absYVGen"].size
    yoff = 1 if hus.axes["yll"].traits.underflow else 0
    U_in = fu[yoff:yoff+nyu, 0:nptu, 0:nqu, 0:nayu]
    U_ov = fu[yoff:yoff+nyu, 0:nptu, nqu, 0:nayu]
    uqt = np.asarray(hus.axes["ptVGen"].edges, float)
    uay = np.asarray(hus.axes["absYVGen"].edges, float)
    # coarsen the response onto the unfolding grid; the unfolding overflow (>44)
    # must match everything the response has above 44 including its own overflow
    Rc = merge_axis(merge_axis(R_in, 2, uqt, qt), 3, uay, ay)
    i44 = int(np.where(np.isclose(qt, 44.0))[0][0])
    Rov44 = R_in[:, :, i44:, :].sum(axis=2) + R_ov
    Rov44 = merge_axis(Rov44, 2, uay, ay)
    d1 = np.abs(Rc - U_in).max()
    d2 = np.abs(Rov44 - U_ov).max()
    print(f"  response coarsened onto the unfolding grid vs unfolding hist:")
    print(f"     in-range max|diff| {d1:.3e}  (largest bin {np.abs(U_in).max():.4e}"
          f" -> rel {d1/max(np.abs(U_in).max(),1):.2e})")
    print(f"     >44 overflow column max|diff| {d2:.3e}")
    if args.ref_histmaker:
        Hr = load(args.ref_histmaker, ["nominal_prefsr_yieldsResponse", "prefsr_response"])
        Rr_in, Rr_ov, axr = resp_arrays(Hr["nominal_prefsr_yieldsResponse"])
        Nr_in, Nr_ov, qtr, ayr = gen_arrays(Hr["prefsr_response"])
        n = len(qtr) - 1
        d = np.abs(R_in[:, :, :n, :] - Rr_in).max()
        dg = np.abs(N_in[:n, :] - Nr_in).max()
        ovd = abs((R_in[:, :, n:, :].sum() + R_ov.sum()) - Rr_ov.sum())
        print(f"  vs the UNEXTENDED run, gen qT < {qtr[-1]:g}:")
        print(f"     R_raw max|diff| {d:.3e} (bitwise identical: "
              f"{np.array_equal(R_in[:, :, :n, :], Rr_in)})")
        print(f"     N_gen max|diff| {dg:.3e} (bitwise identical: "
              f"{np.array_equal(N_in[:n, :], Nr_in)})")
        print(f"     its overflow column vs the sum of the new ones: {ovd:.3e} "
              f"(of {Rr_ov.sum():.4e})")

    if args.csv:
        import csv
        with open(args.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["qt_lo", "qt_hi", "Ngen_frac", "tail_frac_above_lo",
                        "feed_fit", "feed_fit_frac", "feed_ptll44_100",
                        "feed_ptll44_100_frac"])
            for r in rows:
                w.writerow([f"{x:.6g}" for x in r])
        print(f"\nwrote {args.csv}")


if __name__ == "__main__":
    main()
