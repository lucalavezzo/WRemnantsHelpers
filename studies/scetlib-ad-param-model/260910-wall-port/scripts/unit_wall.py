#!/usr/bin/env python3
"""End-to-end unit test of the ported wall through rabbit's own loaders.

Exercises the exact path rabbit_fit.py takes -- mappings.helpers.load_mapping,
regularization.helpers.load_regularizer, set_expectations(parms=...),
compute_nll_penalty(x) -- WITHOUT building the param model, so it runs in
seconds instead of loading the 8.7 GB cache. The x vector is synthesised to the
DATABLIND layout, and the TF penalty is checked against the numpy diagnostic in
verify_map.py (same Condition objects, two different evaluators).

Also checks the refusals: an unsupported form, a missing gen |Y| axis, a held
lambda that violates its own condition.
"""

import sys

import numpy as np
import tensorflow as tf

CARD = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
    "study_scratch/260910-anchor-verify/card_none.hdf5"
)
WALLMOD = "wremnants.postprocessing.scetlib_ad.np_damping_wall"

from rabbit import inputdata  # noqa: E402
from rabbit.mappings import helpers as mh  # noqa: E402
from rabbit.regularization import helpers as rh  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402

# The DATABLIND fit's model-parameter block, in order (from the fit log:
# "fitting 47 of 53 (1 POI: ['alphaS'])"). Only the names matter here.
MODEL_PARAMS = [
    "alphaS",
    "lambda2",
    "lambda4",
    "delta_lambda2",
    "lambda2_nu",
    "lambda4_nu",
]
# DATABLIND postfit thetas for the five NP lambdas (POUs -- never blinded).
POSTFIT_THETA = {
    "lambda2": -0.1987,
    "lambda4": -0.8053,
    "delta_lambda2": -0.0487,
    "lambda2_nu": -2.0828,
    "lambda4_nu": 0.1074,
}


def build(indata, *args):
    mapping = mh.load_mapping(f"{WALLMOD}.NPDampingMapping", indata, *args)
    reg = rh.load_regularizer(f"{WALLMOD}.NPDampingWall", mapping, dtype=indata.dtype)
    return mapping, reg


def synth_x(indata, thetas):
    """(x, parms) in the fitter's layout: [POI | POU | card nuisances]."""
    parms = np.concatenate([np.array([p.encode() for p in MODEL_PARAMS]), indata.systs])
    x = np.zeros(len(parms))
    for i, p in enumerate(MODEL_PARAMS):
        x[i] = thetas.get(p, 0.0)
    # alphaS slot deliberately left at 0 and never read by the wall.
    return tf.constant(x, dtype=indata.dtype), parms


def main():
    indata = inputdata.FitInputData(CARD)
    nfail = 0

    for label, args, thetas in (
        ("ANCHOR (all theta = 0)", (), {}),
        ("DATABLIND postfit", (), POSTFIT_THETA),
        ("DATABLIND postfit, smallb=0", ("smallb=0",), POSTFIT_THETA),
        ("DATABLIND postfit, ymax=5", ("ymax=5",), POSTFIT_THETA),
    ):
        print("=" * 78)
        print(f"CASE {label}   args={args}")
        print("=" * 78)
        mapping, reg = build(indata, *args)
        x, parms = synth_x(indata, thetas)
        reg.set_expectations(x, None, parms=parms)
        tf_pen = float(reg.compute_nll_penalty(x, None).numpy())

        # numpy reference: the same Condition objects, evaluated on the physical
        # lambdas built by the same map.
        values = {}
        for n in reg.inputs["names"]:
            if n in reg._idx:
                values[n] = float(
                    wall.physical_from_theta(reg.inputs["specs"][n], thetas.get(n, 0.0))
                )
            else:
                values[n] = reg._held[n]
        np_pen = float(sum(c.penalty(values, wall.numpy_relu2) for c in reg._active))
        ok = abs(tf_pen - np_pen) <= 1e-14 * max(1.0, abs(np_pen))
        print(
            f"  physical lambdas: "
            + ", ".join(f"{k}={v:.6g}" for k, v in values.items())
        )
        print(
            f"  penalty  TF = {tf_pen:.12g}   numpy = {np_pen:.12g}   "
            f"{'MATCH' if ok else 'MISMATCH'}"
        )
        nfail += 0 if ok else 1

        # The gradient is what actually steers the fit: check it is finite and
        # nonzero exactly on the walled directions.
        with tf.GradientTape() as t:
            t.watch(x)
            pen = reg.compute_nll_penalty(x, None)
        g = t.gradient(pen, x)
        g = np.zeros(x.shape) if g is None else g.numpy()
        active = {
            MODEL_PARAMS[i]: float(g[i])
            for i in range(len(MODEL_PARAMS))
            if g[i] != 0.0
        }
        print(f"  d(penalty)/d(theta) nonzero on: {active}")
        if not np.all(np.isfinite(g)):
            print("  NON-FINITE GRADIENT")
            nfail += 1
        if float(g[0]) != 0.0:
            print("  GRADIENT LEAKED ONTO THE alphaS POI SLOT")
            nfail += 1
        print()

    # ---- refusals
    print("=" * 78)
    print("REFUSALS")
    print("=" * 78)

    class FakeIndata:
        dtype = np.float64
        systs = np.array([b"n1"])
        auxiliary = {}
        channel_info = {}

        def __init__(self, meta):
            self.metadata = meta

    def corrmeta(np_model="tanh_2", np_model_nu="tanh_2", extra=None, aux=True):
        cfg = {
            "Nonperturbative": {
                "np_model": np_model,
                "np_model_nu": np_model_nu,
                "np_model_tmd": "off",
                "lambda2": "0.4",
                "lambda4": "0.4",
                "lambda6": "0.",
                "delta_lambda2": "0.0",
                "lambda_inf": "1.",
                "lambda2_nu": "0.15",
                "lambda4_nu": "0.",
                "lambda6_nu": "0.",
            }
        }
        if extra:
            cfg["Nonperturbative"].update(extra)
        f = FakeIndata(
            {
                "scetlib_corr_config": {
                    "Z": {"config": cfg, "tag": "fake", "applied_to_nominal": True}
                }
            }
        )
        if aux:
            f.auxiliary = {
                "g": {
                    "gen_axes": ["absYVGen"],
                    "edges__absYVGen": np.linspace(0, 2.5, 12),
                }
            }
        return f

    def expect_raise(what, fn, needle):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            got = needle.lower() in str(exc).lower()
            print(
                f"  {'OK  ' if got else 'BAD '} {what}: "
                f"{type(exc).__name__}: {str(exc).splitlines()[0][:90]}"
            )
            return 0 if got else 1
        print(f"  BAD  {what}: no exception raised")
        return 1

    nfail += expect_raise(
        "unsupported CS form (frac_2)",
        lambda: wall.resolve_wall_inputs(corrmeta(np_model_nu="frac_2")),
        "no damping walls",
    )
    nfail += expect_raise(
        "unsupported TMD form (identity)",
        lambda: wall.resolve_wall_inputs(corrmeta(np_model="identity")),
        "no damping walls",
    )
    nfail += expect_raise(
        "np_model_tmd on",
        lambda: wall.resolve_wall_inputs(corrmeta(extra={"np_model_tmd": "gaussian"})),
        "np_model_tmd",
    )
    nfail += expect_raise(
        "no gen |Y| axis",
        lambda: wall.resolve_wall_inputs(corrmeta(aux=False)),
        "no gen rapidity axis",
    )
    nfail += expect_raise(
        "no correction config at all",
        lambda: wall.resolve_wall_inputs(FakeIndata({})),
        "records no theory-correction config",
    )

    # A held lambda that violates its own condition: lambda_inf_nu = -1 in the
    # runcard, never fitted -> unrepairable, must raise at set_expectations.
    def held_violation():
        f = corrmeta(extra={"lambda_inf_nu": "-1."})
        mapping = mh.load_mapping(f"{WALLMOD}.NPDampingMapping", f)
        reg = rh.load_regularizer(f"{WALLMOD}.NPDampingWall", mapping, dtype=np.float64)
        parms = np.array(
            [b"lambda2", b"lambda4", b"delta_lambda2", b"lambda2_nu", b"lambda4_nu"]
        )
        reg.set_expectations(tf.zeros(5, dtype=tf.float64), None, parms=parms)

    nfail += expect_raise(
        "held lambda violates its condition", held_violation, "VIOLATED"
    )
    nfail += expect_raise(
        "unknown -r option",
        lambda: mh.load_mapping(f"{WALLMOD}.NPDampingMapping", indata, "margin=0.1"),
        "unknown key",
    )
    nfail += expect_raise(
        "parms not passed to set_expectations",
        lambda: build(indata)[1].set_expectations(tf.zeros(6, dtype=tf.float64), None),
        "parameter NAMES",
    )

    print()
    if nfail:
        sys.exit(f"UNIT_WALL_FAILED nfail={nfail}")
    print("UNIT_WALL_DONE all checks passed")


if __name__ == "__main__":
    main()
