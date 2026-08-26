#!/usr/bin/env python3
r"""Emit the RESPONSE / CORRECTION gen-binning specification as literal numbers.

The response matrix's gen axes and the theory correction's axes have to be
identical edge for edge: the templates apply the correction as a bin lookup while
the differentiable model calculates on the response grid, so a boundary that
exists on one side and not the other makes the two sides compute different things
in the same bin.  This writes that grid out as plain numbers -- a JSON file, a
Python literal and a plain-text table -- so it can be pasted into a
correction-production config with nothing left to interpret.

The qT axis below 100 GeV and the whole Q and |Y| axes are READ OUT OF THE
EXISTING CORRECTION FILE, not retyped, so they cannot drift.  Only the edges
above 100 are new.
"""

import argparse
import json
import os
import sys

import numpy as np

_WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
if _WREM not in sys.path:
    sys.path.insert(0, _WREM)

GEN = "scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO"


def fmt(edges):
    return "[" + ", ".join(f"{e:g}" for e in edges) + "]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generator", default=GEN)
    ap.add_argument("--extend", nargs="+", type=float, required=True,
                    help="the new qT edges ABOVE 100, in GeV")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--y-acceptance", type=float, default=2.5,
                    help="the response's |Y| upper edge (the gen acceptance)")
    args = ap.parse_args()

    from wremnants.production import theory_corrections as tc

    ce = tc.get_corr_grid_edges(args.generator, "Z")
    qT = list(np.asarray(ce["qT"], float)) + [float(x) for x in args.extend]
    absY = list(np.asarray(ce["absY"], float))
    Q = list(np.asarray(ce["Q"], float))
    absY_resp = [e for e in absY if e <= args.y_acceptance + 1e-9]

    os.makedirs(args.outdir, exist_ok=True)
    spec = {
        "units": "GeV for Q and qT; |Y| dimensionless. Every list is BIN EDGES, "
                 "low edge first, N+1 edges for N bins. A bin is [lo, hi): the "
                 "low edge is inclusive, the high edge exclusive, which is the "
                 "boost-histogram convention both sides already use.",
        "provenance": {
            "correction_file_read": args.generator,
            "unchanged_axes": ["Q", "absY"],
            "changed_axis": "qT",
            "new_qT_edges_above_100": [float(x) for x in args.extend],
        },
        "correction": {
            "Q": Q,
            "absY": absY,
            "qT": qT,
        },
        "response_matrix": {
            "note": "the response truncates |Y| at the gen acceptance edge; that "
                    "is a sub-union of the correction's absY grid and is "
                    "deliberate (measured yield above it is exactly 0 at "
                    "acceptance=True). Q is a single cell = the gen mass window.",
            "Q": Q,
            "absYVGen": absY_resp,
            "ptVGen": qT,
        },
        "counts": {
            "correction_qT_bins": len(qT) - 1,
            "correction_absY_bins": len(absY) - 1,
            "response_ptVGen_bins": len(qT) - 1,
            "response_absYVGen_bins": len(absY_resp) - 1,
            "response_gen_bins": (len(qT) - 1) * (len(absY_resp) - 1),
        },
    }
    p = os.path.join(args.outdir, "gen_binning_spec.json")
    with open(p, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"wrote {p}")

    p2 = os.path.join(args.outdir, "gen_binning_spec.txt")
    with open(p2, "w") as f:
        f.write(
            "RESPONSE-MATRIX / THEORY-CORRECTION GEN BINNING SPECIFICATION\n"
            "=============================================================\n\n"
            "UNITS AND CONVENTION\n"
            "  Q and qT in GeV, |Y| dimensionless.  Every list below is BIN\n"
            "  EDGES: N+1 numbers for N bins, ascending.  A bin is [lo, hi) --\n"
            "  low edge INCLUSIVE, high edge EXCLUSIVE (boost-histogram, which\n"
            "  is what both the correction file and the histmaker already use).\n"
            "  There is no overflow bin in the specification: everything above\n"
            "  the last qT edge is outside it.\n\n"
            f"  Read out of {args.generator}_CorrZ.pkl.lz4 -- only the qT edges\n"
            f"  above 100 are new: {fmt(args.extend)}\n\n"
            "1. THE CORRECTION (all three axes; Q and absY UNCHANGED)\n"
            f"   Q     ({len(Q)-1} bin)   {fmt(Q)}\n\n"
            f"   absY  ({len(absY)-1} bins)\n     {fmt(absY)}\n\n"
            f"   qT    ({len(qT)-1} bins)\n     {fmt(qT)}\n\n"
            "2. THE RESPONSE MATRIX'S GEN AXES (what mz_dilepton builds)\n"
            f"   Q            single cell {fmt(Q)}  (= the gen mass window)\n"
            f"   absYVGen  ({len(absY_resp)-1} bins) {fmt(absY_resp)}\n"
            f"     -- the correction's absY truncated at the gen acceptance edge\n"
            f"        {args.y_acceptance:g}; a sub-union, deliberate.\n"
            f"   ptVGen    ({len(qT)-1} bins) IDENTICAL to the correction's qT above\n"
            f"   -> {(len(qT)-1)*(len(absY_resp)-1)} gen bins\n\n"
            "3. WHAT MUST HOLD BETWEEN THE TWO SIDES\n"
            "   The response's ptVGen edges must be EXACTLY the correction's qT\n"
            "   edges, and the response's absYVGen edges must be a sub-union of\n"
            "   the correction's absY edges.  Nothing may extend beyond the\n"
            "   correction's last qT edge.\n\n"
            "   This is asserted in code, not left as a note:\n"
            "     wremnants/production/theory_corrections.py\n"
            "       check_gen_grid_vs_correction()\n"
            "   called from\n"
            "     scripts/histmakers/mz_dilepton.py            (when the response\n"
            "         grid is built -- so a bad grid never reaches a histogram)\n"
            "     scripts/rabbit/scetlib_ad/prepare_cache_for_card.py\n"
            "         (gen_axes_from_card -- so the SCETlib runcard, which is\n"
            "          written from these very edges, cannot inherit a mismatch)\n"
            "   The datacard carries the correction's NAME in its response\n"
            "   auxiliary ('corr_generator'), which is what makes the second\n"
            "   check automatic rather than something to remember to pass.\n\n"
            "4. PRODUCTION CHAIN THAT HAS TO CARRY THESE EDGES\n"
            "   make_theory_corr rebins its inputs to their COMMON binning\n"
            "   (input_tools.read_matched_scetlib_hist), so an edge missing from\n"
            "   ANY input is missing from the correction:\n"
            "     a) SCETlib resummed run          qT grid must contain them\n"
            "     b) SCETlib nnlo_sing run         qT grid must contain them\n"
            "     c) DYTurbo fixed order (7 scale files)   same\n"
            "     d) the MiNNLO w_z_gen_dists file  ptVgen must contain them --\n"
            "        the current one has a SINGLE bin [100, 13000] above 100, so\n"
            "        it has to be remade or the common rebinning collapses the\n"
            "        whole region to one cell.\n"
            "   After that, mz_dilepton --responseGenBinning theoryCorr reads the\n"
            "   grid out of the new correction file and needs NO flag and no code\n"
            "   change; likewise the cache, which reads its binning from the\n"
            "   card's response auxiliary.\n"
        )
    print(f"wrote {p2}")

    p3 = os.path.join(args.outdir, "gen_binning_spec.py")
    with open(p3, "w") as f:
        f.write(
            '"""Gen binning for the response matrix and the theory correction.\n\n'
            "Edges in GeV (|Y| dimensionless); bins are [lo, hi).\n"
            f'Generated from {args.generator}_CorrZ.pkl.lz4 plus the new qT edges\n'
            f'above 100: {fmt(args.extend)}\n"""\n\n'
            f"Q = {fmt(Q)}\n\n"
            f"absY = {fmt(absY)}   # {len(absY)-1} bins, the correction's own\n\n"
            f"qT = {fmt(qT)}   # {len(qT)-1} bins\n\n"
            f"absYVGen_response = {fmt(absY_resp)}   # truncated at the gen "
            f"acceptance {args.y_acceptance:g}\n"
            f"ptVGen_response = qT\n"
        )
    print(f"wrote {p3}")
    print(f"\nqT: {len(qT)-1} bins, last edge {qT[-1]:g}")
    print(f"response gen bins: {(len(qT)-1)*(len(absY_resp)-1)}")


if __name__ == "__main__":
    main()
