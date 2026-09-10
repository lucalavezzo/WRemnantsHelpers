#!/usr/bin/env python3
"""Verification 3: start invariance under arming, on the REAL 770-bin card.

The toy checks prove the mechanism; this proves OUR configuration -- the actual
SCETlibADParamModel, with alphaS as POI slot 0 and blind_additive set.

POLICY: invariances and booleans only. Never print `x`, nor `get_poi() - x`
(that IS the offset), nor any post-fit physical value. get_poi() is read only at
the START point, where the physical value is theta = 0 -- a public number.
"""
import sys

import numpy as np
import tensorflow as tf

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit/tests")

from rabbit import fitter as fitter_mod  # noqa: E402
from rabbit.inputdata import FitInputData  # noqa: E402
from test_external_term import make_options  # noqa: E402
from wremnants.postprocessing.scetlib_ad.param_model import (  # noqa: E402
    SCETlibADParamModel,
)

CARD, CACHE, CONF = sys.argv[1], sys.argv[2], sys.argv[3]
SIGMA_GEN_REF = 670.0283701  # the invariant the anchor work established

fails = []


def check(name, ok, extra=""):
    print(
        f"  [{'PASS' if ok else 'FAIL'}] {name}{(' -- ' + extra) if extra else ''}",
        flush=True,
    )
    if not ok:
        fails.append(name)


indata = FitInputData(CARD)
model = SCETlibADParamModel.parse_args(
    indata, f"cache={CACHE}", f"conf={CONF}", "threads=48", jitCompile="off"
)

print(
    f"POIs: {[p.decode() for p in model.params[: model.npoi]]}  "
    f"npoi={model.npoi} npou={model.npou}"
)
check("the model declares blind_additive", getattr(model, "blind_additive", False))

sg = model.sigma_gen_central_flat.numpy().sum()
check(
    "sigma_gen at the anchor is the established invariant",
    np.isclose(sg, SIGMA_GEN_REF, rtol=0, atol=1e-6),
    f"{sg:.7f}",
)

f = fitter_mod.Fitter(indata, model, make_options(), do_blinding=True)
f.defaultassign()

p_dis = f.get_poi().numpy().copy()
check(
    "disarmed: the POI start is theta = 0", np.allclose(p_dis, 0.0, rtol=0, atol=1e-14)
)

f.set_blinding_offsets(True)
p_arm = f.get_poi().numpy()
check(
    "ARMED: the POI start is STILL theta = 0 (so SCETlib gets the anchor)",
    np.allclose(p_arm, 0.0, rtol=0, atol=1e-12),
    f"max |theta| = {np.max(np.abs(p_arm)):.3g}",
)
check(
    "the internal coordinate DID move (so it is blinded)",
    not np.allclose(f.x[: model.npoi].numpy(), p_arm, rtol=0, atol=1e-9),
)

# The prediction the model hands rabbit must be exactly 1 at the start: that is
# "the ratio is 1 at the fit start", the property the whole anchor design rests
# on, now verified with blinding ARMED rather than only disarmed.
rnorm = model.compute(tf.concat([f.get_poi(), f.get_model_nui()], axis=0)).numpy()
col = rnorm[0, model.signal_proc_idx]
check(
    "armed: the model's ratio for the signal column is exactly 1",
    np.isclose(col, 1.0, rtol=0, atol=1e-12),
    f"|ratio - 1| = {abs(col - 1):.3g}",
)

f.set_blinding_offsets(True)
check(
    "arming twice is idempotent",
    np.allclose(f.get_poi().numpy(), p_arm, rtol=0, atol=1e-14),
)

print()
print(f"FAILED {len(fails)}: {fails}" if fails else "ALL REAL-CARD CHECKS PASSED")
sys.exit(1 if fails else 0)
