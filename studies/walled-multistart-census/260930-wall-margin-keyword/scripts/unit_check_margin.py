#!/usr/bin/env python3
"""Step 1 (no cache): the margin= keyword on NPDampingWall / NPDampingMapping.

Checks, for every supported (np_model, np_model_nu) form pair and at a set of lambda points
(random, near every boundary, and exactly on it):
  A. default path BIT-IDENTICAL to the pre-change module (np_damping_wall_orig.py, the HEAD
     blob): same labels, names, bounds, coeff values and penalties (== , not isclose), numpy
     and TF evaluators;
  B. every penalty == relu2(bound - coeff) with bound = margin for the margin-carrying
     conditions, LAMBDA_INF_FLOOR for the two floors and 0 for the tanh_6 discriminants,
     for margin in {5e-3, 0};
  C. NPDampingMapping.parse_args: no margin -> margin 5e-3 exactly and key identical to the
     pre-change key; margin=0 / margin=1e-4 parsed; negative / nan / inf / junk refused;
  D. the NPDampingWall regularizer reads mapping.margin (via a stub indata carrying a real
     correction config is too heavy here -> checked in step 2 on the real card).
Run inside the container: python unit_check_margin.py
"""

import importlib.util
import itertools
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

from wremnants.postprocessing.scetlib_ad import np_damping_wall as new  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "np_damping_wall_orig", os.path.join(HERE, "np_damping_wall_orig.py")
)
orig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orig)

import tensorflow as tf  # noqa: E402

NAMES = (
    "lambda_inf",
    "lambda2",
    "lambda4",
    "delta_lambda2",
    "lambda6",
    "lambda_inf_nu",
    "lambda2_nu",
    "lambda4_nu",
    "lambda6_nu",
)
FORMS = list(itertools.product(("tanh_2", "tanh_6"), repeat=2))
YMAX = 3.5


def lambda_points(rng, n_random=200):
    pts = []
    # a physical-ish tune and the lattice-nominal-like one
    pts.append(
        dict(
            lambda_inf=1.0,
            lambda2=0.4,
            lambda4=0.01,
            delta_lambda2=0.02,
            lambda6=0.0,
            lambda_inf_nu=1.5,
            lambda2_nu=0.1345,
            lambda4_nu=0.0,
            lambda6_nu=0.0,
        )
    )
    # every lambda exactly ON 0 / on the margin / just past it
    for v in (0.0, 5e-3, 5e-3 - 1e-9, -1e-9, 2.5e-3, -0.05):
        pts.append({n: v for n in NAMES})
    for _ in range(n_random):
        pts.append(
            dict(
                lambda_inf=rng.uniform(-0.1, 3.0),
                lambda2=rng.uniform(-0.1, 1.0),
                lambda4=rng.uniform(-0.05, 0.05),
                delta_lambda2=rng.uniform(-0.1, 0.1),
                lambda6=rng.uniform(-0.01, 0.01),
                lambda_inf_nu=rng.uniform(-0.1, 3.0),
                lambda2_nu=rng.uniform(-0.1, 0.3),
                lambda4_nu=rng.uniform(-0.05, 0.05),
                lambda6_nu=rng.uniform(-0.01, 0.01),
            )
        )
    return pts


def expected_bound(label, margin):
    if "saturation scale" in label:
        return new.LAMBDA_INF_FLOOR
    if "interior" in label:
        return 0.0
    return margin


class _StubIndata:
    """Minimal indata for BaseMapping.__init__ (channel_info + procs only)."""

    channel_info = {}
    procs = []


STUB = _StubIndata()


def tf_relu2(x):
    return tf.square(tf.maximum(tf.constant(0.0, dtype=tf.float64), x))


def main():
    rng = np.random.default_rng(20260930)
    pts = lambda_points(rng)
    nfail = 0
    rows = []

    # ---------------- A + B
    for np_model, np_model_nu in FORMS:
        for smallb in (True, False):
            c_orig = orig.damping_conditions(np_model, np_model_nu, YMAX, smallb=smallb)
            c_def = new.damping_conditions(np_model, np_model_nu, YMAX, smallb=smallb)
            c_def_explicit = new.damping_conditions(
                np_model,
                np_model_nu,
                YMAX,
                smallb=smallb,
                margin=new._parse_margin("5e-3"),
            )
            c_m0 = new.damping_conditions(
                np_model,
                np_model_nu,
                YMAX,
                smallb=smallb,
                margin=new._parse_margin("0"),
            )
            assert [c.label for c in c_orig] == [c.label for c in c_def]
            assert [c.names for c in c_orig] == [c.names for c in c_def]
            assert [c.bound for c in c_orig] == [c.bound for c in c_def]
            assert [c.bound for c in c_orig] == [c.bound for c in c_def_explicit]
            nbitdiff = 0
            nrel = 0
            maxdev = 0.0
            for v in pts:
                vtf = {k: tf.constant(x, dtype=tf.float64) for k, x in v.items()}
                for co, cd, ce, cz in zip(c_orig, c_def, c_def_explicit, c_m0):
                    # A: bit identity, numpy and TF
                    po, pd, pe = (
                        c.penalty(v, orig.numpy_relu2 if c is co else new.numpy_relu2)
                        for c in (co, cd, ce)
                    )
                    to = float(co.penalty(vtf, tf_relu2).numpy())
                    td = float(cd.penalty(vtf, tf_relu2).numpy())
                    if not (po == pd == pe and to == td):
                        nbitdiff += 1
                    # B: penalty == relu2(bound - coeff), both margins, numpy and TF
                    for c, m in ((cd, 5e-3), (cz, 0.0)):
                        b = expected_bound(c.label, m)
                        if c.bound != b:
                            nfail += 1
                            print(f"BOUND MISMATCH {c.label}: {c.bound} != {b}")
                        coeff = float(c.value(v, new.numpy_relu2))
                        ref = max(0.0, b - coeff) ** 2
                        got = float(c.penalty(v, new.numpy_relu2))
                        got_tf = float(c.penalty(vtf, tf_relu2).numpy())
                        dev = max(abs(got - ref), abs(got_tf - ref))
                        maxdev = max(maxdev, dev)
                        if dev > 1e-15 * max(1.0, ref):
                            nrel += 1
            nfail += nbitdiff + nrel
            rows.append(
                (
                    np_model,
                    np_model_nu,
                    int(smallb),
                    len(c_def),
                    sum(c.bound == 5e-3 for c in c_def),
                    len(pts),
                    nbitdiff,
                    nrel,
                    maxdev,
                )
            )

    print(
        "| np_model | np_model_nu | smallb | #cond | #margin-carrying | #λ points "
        "| default≠orig (bits) | pen≠relu2(bound−coeff) | max abs dev |"
    )
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(str(x) for x in r[:-1]) + f" | {r[-1]:.1e} |")

    # ---------------- C: mapping parsing
    Mnew = new.NPDampingMapping
    Morig = orig.NPDampingMapping
    cases = [
        ((), None),
        (("smallb=0",), None),
        (("ymax=2.5",), None),
        (("smallb=0", "ymax=2.5"), None),
        (("margin=0",), 0.0),
        (("margin=0.0",), 0.0),
        (("margin=1e-4", "smallb=0"), 1e-4),
        (("margin=5e-3",), 5e-3),
    ]
    print("\n| -r mapping args | mapping.margin | key | key == pre-change key |")
    print("|---|---|---|---|")
    for args, want in cases:
        m = Mnew.parse_args(STUB, *args)
        exp_margin = 5e-3 if want is None else want
        if not (m.margin == exp_margin and type(m.margin) is float):
            nfail += 1
            print(f"FAIL margin {args}: {m.margin!r}")
        same = ""
        if want is None:
            mo = Morig.parse_args(STUB, *args)
            same = str(mo.key == m.key and mo.smallb == m.smallb and mo.ymax == m.ymax)
            if mo.key != m.key:
                nfail += 1
        else:
            same = "n/a (new key)"
        print(f"| `{' '.join(args) or '(none)'}` | {m.margin!r} | `{m.key}` | {same} |")

    print("\n| refused input | error |")
    print("|---|---|")
    for bad in (
        "margin=-1e-3",
        "margin=nan",
        "margin=inf",
        "margin=-0.0001",
        "margin=abc",
        "margin=",
    ):
        try:
            Mnew.parse_args(STUB, bad)
        except ValueError as e:
            print(f"| `{bad}` | {str(e).splitlines()[0][:110]} |")
            continue
        nfail += 1
        print(f"| `{bad}` | NOT REFUSED (FAIL) |")
    # -0.0 is accepted and equals 0 (IEEE: -0.0 < 0.0 is False); document it
    m = Mnew.parse_args(STUB, "margin=-0")
    print(
        f"\nmargin=-0 parses to {m.margin!r} (== 0.0: {m.margin == 0.0}); relu2 identical."
    )
    try:
        Morig.parse_args(STUB, "margin=0")
        print("pre-change module ACCEPTED margin=0 (unexpected)")
    except ValueError as e:
        print(f"pre-change module refuses margin=0 as expected: {e}")

    print(f"\nTOTAL FAILURES: {nfail}")
    return nfail


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
