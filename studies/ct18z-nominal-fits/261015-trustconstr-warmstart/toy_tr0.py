#!/usr/bin/env python3
"""Does the initial trust radius matter for a warm restart? S0 (rabbit now) and S3
(fast warm) with initial_tr_radius 1 (scipy default), 1e-2, 1e-4, seeds 3 5 7."""
import numpy as np

import toy_grid as G
import toy_strategies as S
import toy_warmstart as T

for seed in (3, 5, 7):
    starts, _ = G.build_starts(seed)
    for sname in ("at_min", "on_face", "infeas_1e-4", "toy0.1s_0"):
        pseed, scale, itoy, x0 = starts[sname]
        p = (
            T.make_problem(seed=seed)
            if pseed is None
            else G.perturbed(pseed, scale, itoy)
        )
        (xs, fs), _ = G.reference(p, np.zeros(p["n"]))
        row = []
        for strat in ("S0 rabbit-now", "S3 fast-warm"):
            for tr0 in (None, 1e-2, 1e-4):
                kw = dict(S.STRATS[strat])
                if tr0:
                    kw["tr0"] = tr0
                r, h = T.solve(p, x0, **G.PROD, **kw)
                exc = max([hh["fun"] for hh in h] + [p["f"](x0)]) - p["f"](x0)
                row.append(
                    f"{strat[:2]} tr0={tr0}: {r.nit:4d} exc={exc:.0e} df={r.fun - fs:+.0e}"
                )
        print(seed, f"{sname:12s}", " | ".join(row))
