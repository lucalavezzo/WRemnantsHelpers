"""Diagnose the qT>100 (ptVGen overflow) truncation from the theory correction.

The ParamModel's gen ptVGen overflow bin is [44,100] (bt-grid ceiling 100), while
the card N_gen overflow is unbounded (44,inf). This quantifies, from the official
SCETlib+DYTurbo TheoryCorrection (which HAS full qT AND a vars λ-axis):

  1. how much σ sits at qT>100 (the fraction the model drops), in the fit qT tail
     (qT>44) and overall, for |Y|<=2.5 (fit acceptance) and |Y|<=5;
  2. whether the qT>100 tail has a DIFFERENT λ-response than [44,100] — i.e. does
     truncating it bias rnorm=σ(λ)/σ(λc)?  If var/pdf0 is the same in [44,100] and
     [100,inf), the truncation cancels in the fit and needs no physics fix.

Run in the container (binds /home,/ceph,/work,/scratch,/cvmfs).
"""

import sys

import numpy as np

from wremnants.postprocessing.scetlib_np.validation.agreement import (
    load_theory_corr_hist,
)

CORRZ = sys.argv[1]
Q_LO, Q_HI = 60.0, 120.0
# qT range edges we integrate the corr into (GeV). 100 = model ceiling.
QT_EDGES = [0.0, 44.0, 100.0, 1e9]
ABSY_MAXES = [2.5, 5.0]
# λ-variation vars labels to test the tail response (must exist in the corr hist).
VARS_TRY = ["lambda21.0", "lambda2_nu0.25", "lambda40.0", "lambda2_nu0.0"]


def qt_project(h, var, absy_max):
    """(qT_edges, dsigma_per_qT_bin) for one vars label, Q-window + |Y|<=absy_max,
    charge summed. Uses flow=False (so qT overflow of the corr axis is dropped —
    but the corr qT axis runs to ~... we read its top edge and report separately)."""
    axnames = [a.name for a in h.axes]
    hv = h[{"vars": list(h.axes["vars"]).index(var)}]
    # Q window (centre in-range)
    qe = np.asarray(hv.axes["Q"].edges)
    qc = 0.5 * (qe[:-1] + qe[1:])
    qsel = np.where((qc >= Q_LO) & (qc <= Q_HI))[0]
    hv = hv[{"Q": slice(int(qsel[0]), int(qsel[-1]) + 1, sum)}]
    # charge sum
    if "charge" in [a.name for a in hv.axes]:
        hv = hv[{"charge": slice(0, hv.axes["charge"].size, sum)}]
    # |Y| <= absy_max (centre in-range). absY axis is >=0.
    ae = np.asarray(hv.axes["absY"].edges)
    ac = 0.5 * (ae[:-1] + ae[1:])
    asel = np.where(ac <= absy_max)[0]
    hv = hv[{"absY": slice(int(asel[0]), int(asel[-1]) + 1, sum)}]
    # left with qT
    qedges = np.asarray(hv.axes["qT"].edges)
    vals = np.asarray(hv.values(flow=False), dtype=np.float64)
    # also the qT overflow (beyond the last corr edge), if any
    over = float(hv.values(flow=True)[-1]) if hv.axes["qT"].traits.overflow else 0.0
    return qedges, vals, over


def integ_ranges(qedges, vals):
    """Integrate dsigma into the QT_EDGES ranges by bin-centre membership."""
    qc = 0.5 * (qedges[:-1] + qedges[1:])
    out = []
    for i in range(len(QT_EDGES) - 1):
        m = (qc >= QT_EDGES[i]) & (qc < QT_EDGES[i + 1])
        out.append(float(vals[m].sum()))
    return out  # [ [0,44), [44,100), [100,inf) ]


def main():
    h = load_theory_corr_hist(CORRZ, proc="Z")
    print("axes:", [(a.name, a.size) for a in h.axes])
    print("qT edges:", np.asarray(h.axes["qT"].edges))
    print(
        "qT has overflow:",
        h.axes["qT"].traits.overflow,
        "| top edge:",
        float(np.asarray(h.axes["qT"].edges)[-1]),
    )
    varlist = list(h.axes["vars"])
    print("n vars:", len(varlist), "| pdf0 in vars:", "pdf0" in varlist)
    print("sample vars:", [v for v in varlist[:8]])
    print()

    for absy_max in ABSY_MAXES:
        qedges, v0, over0 = qt_project(h, "pdf0", absy_max)
        r = integ_ranges(qedges, v0)
        tot = sum(r) + over0
        lo, mid, hi = r
        hi_plus = hi + over0  # qT>=100 incl. corr-axis overflow
        print(f"==== |Y| <= {absy_max}  (var=pdf0) ====")
        print(f"  σ[0,44)   = {lo:.5g}   ({lo/tot*100:.3f}%)")
        print(f"  σ[44,100) = {mid:.5g}   ({mid/tot*100:.3f}%)")
        print(
            f"  σ[100,inf)= {hi_plus:.5g}   ({hi_plus/tot*100:.3f}%)   [corr-axis overflow {over0:.4g}]"
        )
        qt44 = mid + hi_plus
        print(
            f"  --> qT>100 as a fraction of qT>44 : {hi_plus/qt44*100:.2f}%   "
            f"(this is ~the model/N_gen overflow deficit)"
        )
        print()

    # ---- λ-response of the tail vs [44,100]: does truncation bias rnorm? ----
    print("==== λ-response (var/pdf0) by qT range, |Y|<=2.5 ====")
    qedges, v0, over0 = qt_project(h, "pdf0", 2.5)
    r0 = integ_ranges(qedges, v0)
    r0[2] += over0
    for var in VARS_TRY:
        if var not in varlist:
            print(f"  (skip {var}: not in vars)")
            continue
        qe, vv, ov = qt_project(h, var, 2.5)
        rv = integ_ranges(qe, vv)
        rv[2] += ov
        ratios = [rv[i] / r0[i] if r0[i] else float("nan") for i in range(3)]
        print(
            f"  {var:16s}  var/pdf0:  [0,44)={ratios[0]:.5f}  "
            f"[44,100)={ratios[1]:.5f}  [100,inf)={ratios[2]:.5f}   "
            f"Δ(tail-[44,100))={(ratios[2]-ratios[1])*1e4:+.2f}e-4"
        )
    print("\n  If [100,inf) var/pdf0 ~= [44,100) var/pdf0, the truncation CANCELS in")
    print("  rnorm and does not bias the fit (only the absolute closure of the")
    print("  overflow/last-ptll bins is affected).")


if __name__ == "__main__":
    main()
