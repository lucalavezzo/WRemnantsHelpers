#!/usr/bin/env python3
"""Read a walled fitresult: are the physical lambdas in the damping region?

Prints, for each of the wall's damping conditions, the coefficient at the
postfit tune and whether it is >= 0 (the acceptance test) and >= the margin
(where the soft wall's knee is). Then the penalty at that point, which is what
has to be subtracted from the reported loss to compare against an unwalled fit.

usage: read_walled.py <fitresult.hdf5> [tau]

alphaS is a blinded POI and is never printed. The lambdas are POUs, which
rabbit does not blind.
"""

import sys

import numpy as np

CARD = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
    "study_scratch/260910-anchor-verify/card_none.hdf5"
)
# The unwalled reference: ../260910-blinding, fit_DATABLIND_260910_151034.log.
REF = dict(
    loss=405.5608736721634,
    edm=1.3863650682068962e-3,
    nit=221,
    sat_ndof=733,
    sat_2dnll=811.12,
    sat_p=2.33,
    lin_ndof=780,
    lin_chi2=809.0,
    lin_p=22.66,
    status=2,
)
REF_THETA = {
    "lambda2": -0.1987,
    "lambda4": -0.8053,
    "delta_lambda2": -0.0487,
    "lambda2_nu": -2.0828,
    "lambda4_nu": 0.1074,
}
REF_SIGMA = {
    "lambda2": 0.3463,
    "lambda4": 0.0115,
    "delta_lambda2": 0.0194,
    "lambda2_nu": 0.7712,
    "lambda4_nu": 0.0244,
}

from rabbit import inputdata, io_tools  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402


def main():
    path = sys.argv[1]
    tau = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0

    inp = wall.resolve_wall_inputs(inputdata.FitInputData(CARD))
    res, meta = io_tools.get_fitresult(path, meta=True)
    h = res["parms"].get()
    names = np.asarray([str(n) for n in h.axes[0]])
    vals, errs = h.values(), np.sqrt(h.variances())
    theta = {n: float(vals[i]) for i, n in enumerate(names)}
    sigma = {n: float(errs[i]) for i, n in enumerate(names)}

    print("=" * 84)
    print(f"WALLED POSTFIT  {path}")
    print("=" * 84)
    print(
        f"{'lambda':16s} {'theta':>10s} {'sig(th)':>9s} {'physical':>11s} "
        f"{'unwalled th':>12s} {'unw sig':>9s}"
    )
    print("-" * 72)
    values = {}
    for n in inp["names"]:
        if n in theta:
            values[n] = float(wall.physical_from_theta(inp["specs"][n], theta[n]))
            print(
                f"{n:16s} {theta[n]:10.4f} {sigma[n]:9.4f} {values[n]:11.6f} "
                f"{REF_THETA.get(n, float('nan')):12.4f} "
                f"{REF_SIGMA.get(n, float('nan')):9.4f}"
            )
        else:
            values[n] = float(inp["anchors"][n])
            print(f"{n:16s} {'(held)':>10s} {'-':>9s} {values[n]:11.6f}")

    conds = wall.damping_conditions(inp["np_model"], inp["np_model_nu"], inp["ymax"])
    print()
    print("=" * 84)
    print(f"DAMPING CONDITIONS at the walled tune (ymax={inp['ymax']:g})")
    print("=" * 84)
    total, nbad = 0.0, 0
    for c in conds:
        v = float(c.value(values, wall.numpy_relu2))
        pen = float(c.penalty(values, wall.numpy_relu2))
        total += pen
        phys = "PHYSICAL" if v >= 0.0 else "UNPHYSICAL"
        nbad += 0 if v >= 0.0 else 1
        print(
            f"  {phys:10s} {c.label:62s} coeff {v:+12.6g} "
            f"bound {c.bound:8.4g} pen {pen:.4g}"
        )
    print(f"  {nbad} condition(s) UNPHYSICAL (coeff < 0)")
    pen_nll = total * np.exp(2 * tau)
    print(f"  bare penalty {total:.6g}  x exp(2*{tau:g}) = {pen_nll:.6g} in NLL")

    print()
    print("=" * 84)
    print("CONVERGENCE, walled vs the unwalled DATABLIND reference")
    print("=" * 84)
    print(
        f"  unwalled: loss {REF['loss']:.6f}  edm {REF['edm']:.4e}  "
        f"status {REF['status']}  nit {REF['nit']}"
    )
    print(
        f"            saturated 2dNLL {REF['sat_2dnll']:.2f}/{REF['sat_ndof']}"
        f" p={REF['sat_p']:.2f}%   linear chi2 {REF['lin_chi2']:.0f}/"
        f"{REF['lin_ndof']} p={REF['lin_p']:.2f}%"
    )
    print("  walled  : read loss / edm / p-value off the fit log; then")
    print(
        f"            Delta(pure NLL) = loss_walled - {pen_nll:.6g} - "
        f"{REF['loss']:.6f}"
    )
    print("READ_WALLED_DONE")


if __name__ == "__main__":
    main()
