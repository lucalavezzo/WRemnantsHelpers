"""Sum of grid-A windows vs the single-window [60,120] probe cache (4 low-qT forward cells)."""

import numpy as np

z = np.load(
    "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/260923-qsplit-fisher/jacobians.npz"
)
probe = {
    (1.5, 2.0, 0.0, 1.0): 1.35408991,
    (2.0, 2.5, 0.0, 1.0): 1.31778249,
    (1.5, 2.0, 1.0, 2.0): 3.82927071,
    (2.0, 2.5, 1.0, 2.0): 3.72690718,
}
tags = ["q60_76", "q76_86", "q86_96", "q96_106", "q106_120"]
tot = 0
ref = 0
for (y0, y1, q0, q1), pv in probe.items():
    s = 0
    for t in tags:
        b = z[f"{t}_bins"]
        m = (
            np.isclose(b[:, 2], y0)
            & np.isclose(b[:, 3], y1)
            & np.isclose(b[:, 4], q0)
            & np.isclose(b[:, 5], q1)
        )
        s += z[f"{t}_anchor_val"][m].sum()
    print(
        f"|Y| [{y0},{y1}] qT [{q0},{q1}]: sum of windows {s:.6f}  probe[60,120] {pv:.6f}  rel {s/pv-1:+.2e}"
    )
    tot += s
    ref += pv
print(f"4-cell total: {tot:.5f} vs {ref:.5f}  rel {tot/ref-1:+.2e}")
