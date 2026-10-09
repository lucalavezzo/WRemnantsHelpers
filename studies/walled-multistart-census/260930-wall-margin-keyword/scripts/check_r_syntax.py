#!/usr/bin/env python3
"""How rabbit's argparse splits candidate -r lines (no cache, no fit).

-r is nargs="+", action="append": margs[0] = regularizer class, margs[1] = mapping class,
margs[2:] = mapping args -> NPDampingMapping.parse_args(indata, *margs[2:]). Anything that is not
an option keeps being swallowed by whichever nargs="+" option is open (e.g. --paramModel).
"""

import sys

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit/bin")
import rabbit_fit  # noqa: E402
from rabbit import common  # noqa: E402
from rabbit.regularization.helpers import baseline_regularizations  # noqa: E402

W = "wremnants.postprocessing.scetlib_ad.np_damping_wall"
PM = [
    "--paramModel",
    "wremnants.postprocessing.scetlib_ad.SCETlibADParamModel",
    "cache=C/cache.npz",
    "conf=C/cache.conf",
]
CASES = {
    "recommended (margin after the MAPPING class)": [
        "card.hdf5",
        "--regularizationStrength",
        "8",
        "-r",
        f"{W}.NPDampingWall",
        f"{W}.NPDampingMapping",
        "margin=0",
        *PM,
    ],
    "task's example order (margin right after the WALL class)": [
        "card.hdf5",
        "-r",
        f"{W}.NPDampingWall",
        "margin=0",
        f"{W}.NPDampingMapping",
        *PM,
    ],
    "fitterAD.sh --wall + -f 'margin=0' (lands after --paramModel)": [
        "card.hdf5",
        "--regularizationStrength",
        "5",
        "-r",
        f"{W}.NPDampingWall",
        f"{W}.NPDampingMapping",
        "--snapshotFile",
        "s.hdf5",
        *PM,
        "margin=0",
    ],
    "fitterAD.sh WITHOUT --wall, -f '... --regularizationStrength 8 -r W M margin=0'": [
        "card.hdf5",
        *PM,
        "fit_params=alphaS,lambda2",
        "--regularizationStrength",
        "8",
        "-r",
        f"{W}.NPDampingWall",
        f"{W}.NPDampingMapping",
        "margin=0",
    ],
}
p = rabbit_fit.make_parser()
for name, argv in CASES.items():
    a = p.parse_args(argv)
    print(f"--- {name}")
    print(f"    regularization = {a.regularization}")
    print(f"    paramModel     = {a.paramModel}")
    print(f"    tau            = {a.regularizationStrength}")
    for margs in a.regularization:
        try:
            common.load_class_from_module(margs[1], {}, base_dir="rabbit.mappings")
            print(
                f"    mapping class {margs[1]!r} resolves; mapping args = {margs[2:]}"
            )
        except Exception as e:  # noqa: BLE001
            print(f"    mapping class {margs[1]!r} FAILS: {type(e).__name__}: {e}")
