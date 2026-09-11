#!/usr/bin/env python3
"""Verify the ported wall's theta -> physical map BEFORE running any fit.

Three checks, in order of how badly a failure would mislead us:

  1. theta = 0 reproduces the theory correction's OWN anchor lambdas, exactly.
     This is the model's own invariant (param_model._register_params raises if
     its REPARAM maps do not satisfy it), so a wall that satisfies it with the
     same params.REPARAM widths IS on the same coordinate as the model.
  2. Feeding the DATABLIND postfit thetas reproduces the physical lambdas
     quoted for that fit.
  3. Every damping condition, evaluated at the anchor and at that postfit
     point: which are satisfied, which are violated, and by how much. This is
     what the walled fit will have to move.

Nothing here prints alphaS: it is a blinded POI. The lambdas are POUs, which
rabbit never blinds, so their fitresult values are the true ones.
"""

import sys

import numpy as np

CARD = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
    "study_scratch/260910-anchor-verify/card_none.hdf5"
)
FITRESULT = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
    "260910_blinding_final/fitresults_DATABLIND.hdf5"
)

# The physical values quoted for the DATABLIND postfit in the task brief,
# rounded to 3 decimals. Check 2 is against these.
QUOTED_PHYSICAL = {
    "lambda2": 0.301,
    "lambda4": -0.003,
    "delta_lambda2": -0.024,
    "lambda2_nu": -0.058,
    "lambda4_nu": 0.054,
}

from rabbit import inputdata, io_tools  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402


def main():
    indata = inputdata.FitInputData(CARD)
    inp = wall.resolve_wall_inputs(indata)

    print("=" * 78)
    print("WALL INPUTS, all resolved from the card")
    print("=" * 78)
    print(f"correction tag : {inp['corr_tag']}")
    print(f"np_model (TMD) : {inp['np_model']}")
    print(f"np_model_nu(CS): {inp['np_model_nu']}")
    print(f"binding |Y|    : {inp['ymax']:g}   from {inp['ymax_source']}")
    print(f"lambdas needed : {list(inp['names'])}")
    print()
    print(f"{'lambda':16s} {'map':32s} {'anchor':>10s}")
    print("-" * 62)
    for n in inp["names"]:
        kind, coeffs = inp["specs"][n]
        if kind is None:
            desc = "theta (identity, no REPARAM entry)"
        elif kind == "quad":
            desc = f"{coeffs[0]:g} + {coeffs[1]:g}*theta"
        else:
            desc = f"{kind} {coeffs}"
        print(f"{n:16s} {desc:32s} {inp['anchors'][n]:10.5f}")

    # ---- check 1: the map must reproduce the anchor at the fit's START point,
    # which is NOT theta = 0 for every parameter. param_model._register_params
    # zeroes the start value only for REPARAMETRISED entries
    # (defaults[~self._rp_id] = 0.0) and leaves an identity parameter at its
    # anchor -- for lambda_inf / lambda_inf_nu, which have no params.REPARAM
    # entry, the fit coordinate IS the physical lambda. So the invariant to
    # check is per-kind, and getting it wrong in either direction is exactly
    # the bug this port had to avoid.
    print()
    print("=" * 78)
    print("CHECK 1  the map must reproduce the anchor at the fit's start point")
    print("=" * 78)
    bad = []
    for n in inp["names"]:
        kind = inp["specs"][n][0]
        start = 0.0 if kind is not None else float(inp["anchors"][n])
        got = float(wall.physical_from_theta(inp["specs"][n], start))
        want = float(inp["anchors"][n])
        ok = abs(got - want) <= 1e-12
        note = (
            "reparametrised, start theta=0"
            if kind is not None
            else ("identity: fit coordinate IS physical, start = anchor")
        )
        print(
            f"  {n:16s} start {start:9.5f} -> {got:12.8f}   anchor "
            f"{want:12.8f}  {'OK' if ok else 'MISMATCH'}   ({note})"
        )
        if not ok:
            bad.append((n, got, want))
    if bad:
        sys.exit(f"CHECK 1 FAILED: {bad}")
    print("  CHECK 1 PASSED")

    # ---- check 2: the DATABLIND postfit thetas -> the quoted physical values.
    res = io_tools.get_fitresult(FITRESULT)
    h = res["parms"].get()
    names = np.asarray([str(n) for n in h.axes[0]])
    vals, errs = h.values(), np.sqrt(h.variances())
    theta = {n: float(vals[i]) for i, n in enumerate(names)}
    sigma = {n: float(errs[i]) for i, n in enumerate(names)}

    print()
    print("=" * 78)
    print("CHECK 2  DATABLIND postfit theta -> physical lambda")
    print("=" * 78)
    print(
        f"{'lambda':16s} {'theta':>11s} {'sigma(theta)':>13s} "
        f"{'physical':>11s} {'quoted':>9s}"
    )
    print("-" * 66)
    postfit = {}
    bad = []
    for n in inp["names"]:
        if n in theta:
            phys = float(wall.physical_from_theta(inp["specs"][n], theta[n]))
            q = QUOTED_PHYSICAL.get(n)
            flag = ""
            if q is not None:
                if abs(phys - q) > 5.1e-4:
                    flag = "  <== DISAGREES WITH QUOTE"
                    bad.append((n, phys, q))
            print(
                f"{n:16s} {theta[n]:11.4f} {sigma[n]:13.4f} {phys:11.6f} "
                f"{'' if q is None else f'{q:9.3f}'}{flag}"
            )
        else:
            phys = float(inp["anchors"][n])
            print(
                f"{n:16s} {'(held)':>11s} {'-':>13s} {phys:11.6f}    "
                f"(correction anchor)"
            )
        postfit[n] = phys
    if bad:
        sys.exit(f"CHECK 2 FAILED: {bad}")
    print("  CHECK 2 PASSED (every quoted value reproduced to < 5.1e-4)")

    # ---- check 3: the conditions, at the anchor and at the postfit point.
    anchor = {n: float(inp["anchors"][n]) for n in inp["names"]}
    for tag, values in (("ANCHOR (theta = 0)", anchor), ("DATABLIND POSTFIT", postfit)):
        for smallb in (True, False):
            conds = wall.damping_conditions(
                inp["np_model"], inp["np_model_nu"], inp["ymax"], smallb=smallb
            )
            print()
            print("=" * 78)
            print(f"CHECK 3  damping conditions at {tag}   (smallb={int(smallb)})")
            print("=" * 78)
            total = 0.0
            for c in conds:
                v = float(c.value(values, wall.numpy_relu2))
                pen = float(c.penalty(values, wall.numpy_relu2))
                total += pen
                mark = "ok    " if pen == 0.0 else "WALLED"
                print(
                    f"  {mark} {c.label:64s} coeff {v:+12.6g}  "
                    f"bound {c.bound:8.4g}  penalty {pen:.6g}"
                )
            print(f"  TOTAL bare penalty = {total:.6g}")
            for tau in (3.0, 4.0, 5.0):
                print(
                    f"    x exp(2*tau={tau:g}) = {total * np.exp(2 * tau):12.4g}"
                    "   (this is what is ADDED to the NLL)"
                )
    print()
    print("VERIFY_MAP_DONE")


if __name__ == "__main__":
    main()
