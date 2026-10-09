#!/usr/bin/env python3
"""tau-continuation on the surrogate: trust-krylov at a soft wall (tau_1), then warm at tau_2 (and tau_3).

The zero-code recipe: every stage is an ordinary rabbit fit (--regularizationStrength tau_i, warm via
--externalPostfit). Reports per-stage and total loss+grad / HVP counts and the final face overshoot.
usage: cont_surrogate.py <start> tau1,tau2[,tau3]
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_surrogate import OUT, fstar_walled, load_start, trust_krylov  # noqa: E402
from surrogate import Surrogate  # noqa: E402

start, taus = sys.argv[1], [float(t) for t in sys.argv[2].split(",")]
x = None
stages, nf, nh = [], 0, 0
for tau in taus:
    S = Surrogate(tau=tau)
    if x is None:
        x = load_start(start, S.names)
    fs, _ = fstar_walled(S)
    S.n_f = S.n_hvp = 0
    x, hist, sec, f0 = trust_krylov(S, x, maxiter=20000, ftarget=fs + 1e-9)
    nf += S.n_f
    nh += S.n_hvp
    stages.append(
        dict(
            tau=tau,
            n_f=S.n_f,
            n_hvp=S.n_hvp,
            f_end_minus_fstar=float(S.fun(x)[0] - fs),
            face=float(S.conds(x)[0][S.iface]),
            rejected=int(sum(1 for h in hist if "acc" in h and not h["acc"])),
        )
    )
res = dict(
    start=start,
    taus=taus,
    stages=stages,
    n_f=nf,
    n_hvp=nh,
    hours_est=(27 * nf + 13 * nh) / 3600,
)
json.dump(
    res,
    open(f"{OUT}/cont_{start}_{'-'.join(f'{t:g}' for t in taus)}.json", "w"),
    indent=1,
)
print(json.dumps(res))
