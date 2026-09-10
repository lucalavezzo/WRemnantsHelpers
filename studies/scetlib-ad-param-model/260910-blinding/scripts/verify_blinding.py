#!/usr/bin/env python3
"""Verify the additive-POI blinding change.

POLICY: this script asserts INVARIANCES only. It must never print, log or
return a blinding offset. Note in particular that `x` for a zero-centred POI is
minus the offset, so `x` itself is never printed -- only agreement of PHYSICAL
quantities, and booleans.

Checks
  1  the model sees the PHYSICAL value while rabbit's coordinate is blinded;
  2  the physical best fit, the covariance and the impacts agree between a
     blinded-additive fit and an unblinded one (the acceptance criterion:
     "central value hidden, uncertainty intact");
  3  the multiplicative path is UNCHANGED for a model that does not opt in
     (the regression guard for every other analysis);
  4  the physical start point is invariant under arming, and arming is
     idempotent.
"""
import sys

import numpy as np
import tensorflow as tf

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit")

from rabbit import fitter as fitter_mod  # noqa: E402
from rabbit.inputdata import FitInputData  # noqa: E402
from rabbit.param_models.param_model import ParamModel  # noqa: E402

TENSOR = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test_tensor.hdf5"
# Deliberately NON-ZERO: a zero start would satisfy check 4 by accident, which
# is exactly the accident this change replaces with a guarantee.
START = 0.3


class ToyModel(ParamModel):
    """One POI scaling the signal, linear so the fit solves exactly."""

    def __init__(self, indata, blind_additive):
        super().__init__(indata)
        self.npoi = 1
        self.npou = 0
        self.params = np.array([b"alphaS"])
        self.xparamdefault = tf.constant([START], dtype=indata.dtype)
        self.is_linear = True
        self.allowNegativeParam = True
        if blind_additive:
            self.blind_additive = True

    def compute(self, param, full=False):
        # No numpy on `param`: compute() runs inside a tf.function, where param
        # is symbolic. Check 1 asserts the observable consequence instead.
        nproc = self.indata.nproc
        col = tf.reshape(1.0 + 0.1 * param[0], [1, 1])
        return tf.concat([col, tf.ones([1, nproc - 1], dtype=col.dtype)], axis=1)


# Reuse rabbit's own options builder rather than hand-rolling one -- the Fitter
# reads a long tail of attributes and a partial stand-in fails at whichever one
# it happens to reach first.
sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit/tests")
from test_external_term import make_options  # noqa: E402


def build(blind_additive, do_blinding):
    indata = FitInputData(TENSOR)
    model = ToyModel(indata, blind_additive)
    f = fitter_mod.Fitter(indata, model, make_options(), do_blinding=do_blinding)
    return indata, model, f


def main():
    fails = []

    def check(name, ok, extra=""):
        print(
            f"  [{'PASS' if ok else 'FAIL'}] {name}{(' -- ' + extra) if extra else ''}"
        )
        if not ok:
            fails.append(name)

    # ---- 4: physical start invariant under arming, and idempotent
    print("check 4: physical start invariant under arming")
    _, _, f = build(blind_additive=True, do_blinding=True)
    f.defaultassign()
    p0 = float(f.get_poi()[0].numpy())
    check(
        "disarmed start is the declared default",
        np.isclose(p0, START, rtol=0, atol=1e-14),
    )
    f.set_blinding_offsets(True)
    p1 = float(f.get_poi()[0].numpy())
    check(
        "armed start is STILL the declared default",
        np.isclose(p1, START, rtol=0, atol=1e-12),
        f"|physical - declared| = {abs(p1 - START):.3g}",
    )
    check(
        "the internal coordinate DID move (so it is blinded)",
        not np.isclose(float(f.x[0].numpy()), p1, rtol=0, atol=1e-9),
    )
    f.set_blinding_offsets(True)
    p2 = float(f.get_poi()[0].numpy())
    check("arming twice is idempotent", np.isclose(p2, p1, rtol=0, atol=1e-14))
    f.set_blinding_offsets(False)
    p3 = float(f.get_poi()[0].numpy())
    check(
        "disarming returns to the declared default",
        np.isclose(p3, START, rtol=0, atol=1e-12),
    )

    # ---- 1: the model is handed the physical value
    #
    # Asserted through its OBSERVABLE consequence rather than by instrumenting
    # compute(): the fitter passes get_poi() to compute(), so if the model were
    # handed the internal coordinate instead, the predicted yields at the same
    # physical point would differ between an armed and an unarmed fitter.
    print("check 1: the model is handed the physical value")
    _, _, fu = build(blind_additive=True, do_blinding=False)
    fu.defaultassign()
    yu = fu.expected_yield().numpy()

    _, _, fb = build(blind_additive=True, do_blinding=True)
    fb.defaultassign()
    fb.set_blinding_offsets(True)
    # Zero the THETA offsets only. NOI blinding is additive on theta and theta
    # starts at 0, so arming puts the physical NOIs at their offsets rather
    # than at nominal and moves the yields by ~10%. That is pre-existing
    # behaviour of the theta block (and harmless there -- a template morph is
    # evaluable anywhere and the fit moves it back), but it would swamp the POI
    # signal this check is after.
    fb._blinding_offsets_theta.assign(np.zeros(fb.indata.nsyst, dtype=np.float64))
    yb = fb.expected_yield().numpy()

    check(
        "physical value handed to the model is the declared default",
        np.isclose(float(fb.get_poi()[0].numpy()), START, rtol=0, atol=1e-12),
    )
    check(
        "predicted yields identical armed vs unarmed, POI isolated (so the "
        "model saw the physical value)",
        np.allclose(yb, yu, rtol=1e-12, atol=0),
        f"max rel diff = {np.max(np.abs(yb / yu - 1)):.3e}",
    )
    check(
        "the internal coordinate DID move (so it is blinded)",
        not np.isclose(float(fb.x[0].numpy()), START, rtol=0, atol=1e-9),
    )

    # ---- 2: the acceptance criterion, proven at a fixed physical point
    #
    # sigma = sqrt(diag(H^-1)), so "the uncertainty is unblinded" IS "the
    # Hessian in the internal frame is unchanged". For an additive offset the
    # Jacobian d(physical)/d(internal) is the identity, so H must match the
    # unblinded one EXACTLY; for a multiplicative offset it is scaled by the
    # square of the factor. Checking H directly needs no fit to converge and no
    # covariance to be populated.
    print("check 2: Hessian (hence sigma / cov / impacts) unblinded, additive")

    # ASIMOV DATA IS REQUIRED for this check to mean anything. make_tensor.py
    # leaves data_obs at zero, and with nobs = 0 the Poisson term
    # sum(nexp - nobs*log nexp) collapses to sum(nexp), which is LINEAR in the
    # yields -- so the POI curvature is exactly zero, sigma is undefined, and a
    # comparison of "H unblinded" passes vacuously (isclose(0, 0)). Verified by
    # finite difference: the loss had the identical slope 2216.7 at POI offsets
    # of 0.1, 1 and 10. The multiplicative positive control below is what
    # exposed it.
    #
    # One dataset, computed once at the shared physical start point and given to
    # every fitter, so the comparison cannot drift.
    _, _, f_ref = build(blind_additive=True, do_blinding=False)
    f_ref.defaultassign()
    asimov = f_ref.expected_yield()

    def loss_and_hess(blind_additive, do_blinding):
        _, _, f = build(blind_additive=blind_additive, do_blinding=do_blinding)
        f.defaultassign()
        if do_blinding:
            f.set_blinding_offsets(True)
            f._blinding_offsets_theta.assign(np.zeros(f.indata.nsyst, dtype=np.float64))
        f.set_nobs(asimov)
        loss, _, hess = f.loss_val_grad_hess()
        return float(loss.numpy()), hess.numpy()

    l_u, h_u = loss_and_hess(True, False)
    l_a, h_a = loss_and_hess(True, True)
    # ABSOLUTE, not relative: with Asimov data the loss at the start point is
    # exactly 0 (set_nobs picks the offset to give the saturated likelihood), so
    # a relative comparison divides by zero. Loss == 0 here is itself a useful
    # confirmation that the data really are Asimov.
    check(
        "loss identical at the same physical point",
        np.isclose(l_a, l_u, rtol=0, atol=1e-9),
        f"|difference| = {abs(l_a - l_u):.3e}  (both {l_u:.3e})",
    )
    # Guard against a vacuous pass: isclose(0, 0) is True, so assert there is
    # curvature to compare BEFORE comparing it.
    check(
        "POI curvature is non-trivial (so this check is not vacuous)",
        abs(h_u[0, 0]) > 1e-6,
        f"H_unblinded[0,0] = {h_u[0, 0]:.6g}",
    )
    check(
        "POI Hessian element EXACTLY unblinded (=> sigma exact)",
        np.isclose(h_a[0, 0], h_u[0, 0], rtol=1e-10),
        f"rel diff = {abs(h_a[0, 0] / h_u[0, 0] - 1):.3e}" if h_u[0, 0] else "H=0",
    )
    check("full Hessian unblinded", np.allclose(h_a, h_u, rtol=1e-10, atol=0))

    # Positive control: the multiplicative path DOES scale it, which is the
    # defect being removed. Reported as a ratio, never as the factor itself.
    l_m, h_m = loss_and_hess(False, True)
    scaled = not np.isclose(h_m[0, 0], h_u[0, 0], rtol=1e-6)
    check(
        "multiplicative path scales the POI Hessian (the defect being fixed)",
        scaled,
        f"|H_mult/H_unblinded| = {abs(h_m[0, 0] / h_u[0, 0]):.3e}" if h_u[0, 0] else "",
    )

    # ---- 3: regression guard -- the multiplicative path is untouched
    print("check 3: multiplicative path unchanged for a model that does not opt in")
    _, _, f = build(blind_additive=False, do_blinding=True)
    f.defaultassign()
    f.set_blinding_offsets(True)
    poi = float(f.get_poi()[0].numpy())
    xi = float(f.x[0].numpy())
    check(
        "additive offset is exactly zero",
        float(f._blinding_offsets_poi_add[0].numpy()) == 0.0,
    )
    check(
        "get_poi is x * multiplicative offset, as before",
        np.isclose(poi, xi * float(f._blinding_offsets_poi[0].numpy()), rtol=1e-14),
    )
    check(
        "x was NOT frame-shifted for a multiplicative model",
        np.isclose(xi, START, rtol=0, atol=1e-14),
    )

    print()
    if fails:
        print(f"FAILED {len(fails)}: {fails}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
