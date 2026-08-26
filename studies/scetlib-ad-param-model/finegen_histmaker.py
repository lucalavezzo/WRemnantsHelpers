#!/usr/bin/env python3
r"""Run mz_dilepton with a FINER gen (unfolding) grid, without touching the tree.

Why this exists
---------------
The response matrix R = R_raw/N_gen the param model folds through is not ours to
rebin at analysis time: it comes out of the histmaker's
``nominal_prefsr_yieldsUnfolding``, whose gen axes are fixed by

    ptVGen  = rebin_pt(reco ptll edges)   -> ONE gen bin per TWO reco bins
    absYVGen = positive half of the reco yll edges

(``wremnants/utilities/binning.py:get_unfolding_dilepton_axes`` and
``wremnants/production/unfolding_tools.py:rebin_pt``). So the card's 21 x 10 gen
grid is the finest R that exists on disk, and measuring what a FINER grid would
buy needs a histmaker rerun -- a finer SCETlib cache alone buys nothing, because
folding sigma_gen(fine) through a P(b|g) that only resolves the coarse bins is
algebraically the same as folding sigma_gen(coarse).

What it changes, and what it deliberately does not
--------------------------------------------------
``get_unfolding_dilepton_axes`` is monkeypatched IN THIS PROCESS ONLY, so the
shared WRemnants checkout is untouched (three other sessions are live in it).
Two axes are replaced after the original builds them:

  ptVGen   -> the FULL reco ptll edges [0, 1, 1.5, ..., 37, 44, 100], 40 bins.
              That is 2x finer than shipped over 0-44 AND it resolves [44, 100]
              explicitly instead of dumping every qT > 44 into an overflow --
              the two distinct gen-grid defects, fixed by one change.
  absYVGen -> the shipped |Y| edges with a midpoint inserted in each, 20 bins.
              Midpoints, not new quantiles, so that summing pairs recovers the
              shipped grid EXACTLY and the coarse-vs-fine comparison is internal
              to one run.

The RECO binning is left exactly as the card's, so the per-event reference
``nominal_<corr>_Corr`` comes out on the card's own (ptll, yll) grid and needs no
rebinning. ``helicitySig`` is dropped from the unfolding axes on purpose: the
joint hist is then filled with ``nominal_weight`` instead of the
``nominal_weight_helicity`` partition, and since the partition is recovered by
SUMMING helicitySig (see scetlib_np/response_matrix.py) the two are the same R --
9x smaller, and it skips the helicity-xsec rebinning that a finer gen grid would
otherwise have to satisfy.

Usage
-----
    ./incontainer.sh python3 finegen_histmaker.py -o <outdir> [extra mz_dilepton args]

Everything after the recognised options is forwarded to mz_dilepton verbatim.
"""

import os
import runpy
import sys

import numpy as np

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, WREM)


# The theory correction is applied as a BIN LOOKUP on the correction file's own
# grid (correctionsTensor_helper.makeCorrectionsTensor: "returns what is in the
# bin of the histogram" -- no interpolation), so the per-event response is
# piecewise constant on these cells. A gen grid that REFINES them therefore
# makes the bin-averaged response exact and drives the granularity term to zero
# by construction rather than asymptotically. These are the edges of
# scetlib_dyturbo_..._CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4 (qT: 70 bins to 100 GeV;
# absY: 17 bins to 5, truncated here at the 2.5 acceptance edge).
CORR_QT_EDGES = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5,
                 8, 8.5, 9, 9.5, 10, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14,
                 14.5, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
                 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 42, 44, 46, 48,
                 50, 52, 54, 56, 58, 60, 65, 70, 80, 90, 100]
CORR_Y_EDGES = [0, 0.15, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.8, 2.0, 2.5]


def _refine_y(edges):
    """Insert the midpoint of every bin: summing pairs gives ``edges`` back."""
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        out += [float(a), 0.5 * (float(a) + float(b))]
    return out + [float(edges[-1])]


def install_patch(y_refine=2, qt_full=True, verbose=True, preset="reco"):
    import hist

    from wremnants.utilities import binning

    orig = binning.get_unfolding_dilepton_axes

    def patched(gen_vars, reco_edges, gen_level, **kw):
        axes, cols, sels = orig(gen_vars, reco_edges, gen_level, **kw)
        new = []
        for ax in axes:
            if ax.name == "ptVGen" and preset == "corr":
                ax = hist.axis.Variable(
                    np.asarray(CORR_QT_EDGES, float), name="ptVGen",
                    underflow=False, overflow=True,
                )
            elif ax.name == "absYVGen" and preset == "corr":
                ax = hist.axis.Variable(
                    np.asarray(CORR_Y_EDGES, float), name="absYVGen",
                    underflow=False, overflow=ax.traits.overflow,
                )
            elif ax.name == "ptVGen" and qt_full:
                e = np.asarray(reco_edges["ptll"], float)
                ax = hist.axis.Variable(
                    e, name="ptVGen", underflow=False, overflow=True
                )
            elif ax.name == "absYVGen" and y_refine > 1:
                e = np.asarray(ax.edges, float)
                for _ in range(int(np.log2(y_refine))):
                    e = np.asarray(_refine_y(e), float)
                ax = hist.axis.Variable(
                    e, name="absYVGen", underflow=False,
                    overflow=ax.traits.overflow,
                )
            new.append(ax)
        if verbose:
            for ax in new:
                if ax.name in ("ptVGen", "absYVGen"):
                    print(f"[finegen] {ax.name}: {ax.size} bins  {list(ax.edges)}",
                          flush=True)
        return new, cols, sels

    binning.get_unfolding_dilepton_axes = patched
    # unfolding_tools imported the name directly, so rebind it there too.
    from wremnants.production import unfolding_tools
    if hasattr(unfolding_tools, "binning"):
        unfolding_tools.binning.get_unfolding_dilepton_axes = patched


def main():
    argv = sys.argv[1:]
    y_refine, qt_full, preset = 2, True, "reco"
    fwd = []
    it = iter(range(len(argv)))
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--yRefine":
            y_refine = int(argv[i + 1]); i += 2; continue
        if a == "--noQtFull":
            qt_full = False; i += 1; continue
        if a == "--preset":
            preset = argv[i + 1]; i += 2; continue
        fwd.append(a); i += 1
    install_patch(y_refine=y_refine, qt_full=qt_full, preset=preset)
    script = os.path.join(WREM, "scripts", "histmakers", "mz_dilepton.py")
    sys.argv = [script] + fwd
    print(f"[finegen] running {script} with:\n  " + " ".join(fwd), flush=True)
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
