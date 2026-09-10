#!/usr/bin/env python3
"""Build the model on a card and report the anchor / sigma_gen invariant."""
import argparse
import os
import sys

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants")

ap = argparse.ArgumentParser()
ap.add_argument("--card", required=True)
ap.add_argument("--cache", required=True)
ap.add_argument("--conf", required=True)
ap.add_argument("--model-args", default="")
ap.add_argument("--threads", type=int, default=32)
a = ap.parse_args()

from rabbit.inputdata import FitInputData  # noqa: E402
from wremnants.postprocessing.scetlib_ad.param_model import (  # noqa: E402
    SCETlibADParamModel,
)

indata = FitInputData(a.card)
toks = [f"cache={a.cache}", f"conf={a.conf}", f"threads={a.threads}"]
toks += [t for t in a.model_args.split() if t]
print(f"\n=== spec: {' '.join(toks)}", flush=True)
try:
    model = SCETlibADParamModel.parse_args(indata, *toks, jitCompile="off")
except Exception as exc:
    print(f"\nRAISED {type(exc).__name__}:\n{exc}")
    sys.exit(3)

import numpy as np  # noqa: E402

sg = model.sigma_gen_central_flat.numpy()
print(f"\nRESULT sigma_gen(anchor).sum() = {sg.sum():.7f}   (x2 = {2*sg.sum():.7f})")
cache_anchor = np.asarray(model.core.anchor, dtype=np.float64)
d = np.abs(model._anchor - cache_anchor)
print(f"RESULT max |anchor - cache_anchor| = {d.max():.3g}")
if d.max() > 0:
    for n, x, y in zip(model.rabbit_names, model._anchor, cache_anchor):
        if abs(x - y) > 0:
            print(f"    {n}: correction {x!r} vs cache {y!r}")
print("RESULT ok")
