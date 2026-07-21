"""Decisive test (Luca's framing): the nonsingular is SHARED, so model−corr =
resum_model − resum_corr. Compare our bt-grid resum DIRECTLY to the SCETlib
resummed spectrum (the input make_theory_corr used), per fine qT bin, |Y|<2.5.

No TF model build (avoids OOM): model resum-only values are pasted from the
--no-nonsingular run (resumonly_fine.log); the SCETlib resum is read + projected
by resum_validation.resum_from_correction. If resum_model is ~0.72 low at [90,100],
the deficit is unambiguously the bt-grid resum → Luca's finer-qT btgrid run is the fix.
"""

import numpy as np

from wremnants.postprocessing.scetlib_np.validation.resum_validation import (
    RESUM_PKL,
    resum_from_correction,
)

FINE = [
    0,
    0.5,
    1,
    1.5,
    2,
    2.5,
    3,
    3.5,
    4,
    4.5,
    5,
    5.5,
    6,
    6.5,
    7,
    7.5,
    8,
    8.5,
    9,
    9.5,
    10,
    10.5,
    11,
    11.5,
    12,
    12.5,
    13,
    13.5,
    14,
    14.5,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    42,
    44,
    46,
    48,
    50,
    52,
    54,
    56,
    58,
    60,
    65,
    70,
    80,
    90,
    100,
]

# model RESUM-ONLY σ_gen, |Y|<2.5, on FINE edges (resumonly_fine.log)
RESUM_MODEL = [
    3.5909,
    10.5888,
    17.0605,
    22.7342,
    27.4339,
    31.0836,
    33.696,
    35.353,
    36.1819,
    36.334,
    35.9643,
    35.2179,
    34.22,
    33.0716,
    31.8495,
    30.6079,
    29.3826,
    28.1952,
    27.0571,
    25.9728,
    24.9429,
    23.9654,
    23.0376,
    22.1562,
    21.3184,
    20.5213,
    19.7627,
    19.0403,
    18.3521,
    17.6962,
    33.5453,
    31.267,
    29.1884,
    27.2867,
    25.5401,
    23.93,
    22.442,
    21.0638,
    19.7851,
    18.5952,
    17.495,
    16.4963,
    15.5628,
    14.6862,
    13.8683,
    13.1046,
    12.3902,
    11.7208,
    11.093,
    10.5033,
    9.9489,
    9.4272,
    8.9358,
    8.4724,
    8.035,
    14.8529,
    13.3729,
    12.0446,
    10.8488,
    9.7693,
    8.7928,
    7.9072,
    7.1029,
    6.3744,
    5.7153,
    11.7939,
    8.839,
    11.0916,
    4.8905,
    0.5587,
]


def main():
    edges = np.array(FINE, dtype=float)
    rm = np.array(RESUM_MODEL, dtype=float)
    gen_axes = [("ptVGen", edges), ("absYVGen", np.array([0.0, 2.5]))]
    rs = resum_from_correction(RESUM_PKL, gen_axes, 60.0, 120.0, 0)
    rs = np.asarray(rs, dtype=float).reshape(-1)
    assert rm.size == rs.size == edges.size - 1, (rm.size, rs.size, edges.size - 1)
    ratio = np.where(rs != 0, rm / rs, np.nan)
    print(
        f"{'qT bin':>14} {'resum_model':>12} {'resum_SCETlib':>14} {'model/SCETlib':>13}"
    )
    for i in range(rm.size):
        tag = "  <-- tail" if edges[i] >= 44 else ""
        print(
            f"[{edges[i]:5.1f},{edges[i+1]:6.1f}) {rm[i]:12.4g} {rs[i]:14.4g} "
            f"{ratio[i]:13.5f}{tag}"
        )
    ctr = 0.5 * (edges[:-1] + edges[1:])
    for lab, msk in [("qT<44", ctr < 44), ("qT>=44 tail", ctr >= 44)]:
        r = ratio[msk][np.isfinite(ratio[msk])]
        print(
            f"\n  {lab:12s}: model/SCETlib range [{r.min():.4f},{r.max():.4f}]  ({r.size} bins)"
        )
    # the decisive number: resum deficit at [90,100] vs the matched deficit 0.72
    print(
        f"\n  [90,100): resum_model={rm[-1]:.4g}  resum_SCETlib={rs[-1]:.4g}  "
        f"deficit={rs[-1]-rm[-1]:+.4g}  (matched deficit there was ~0.72)"
    )


if __name__ == "__main__":
    main()
