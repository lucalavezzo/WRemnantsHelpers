#!/usr/bin/env python3
"""Wall conditions at the sub-fit start (LATB8) and end (SATB8 sub-fit), from stored parameter values only.
theta -> physical map as printed by NPDampingWall in SATB8.log: lambda2 = lambda4 = 0.4 + 0.5 th, delta_lambda2 = 0.5 th,
lambda2_nu = 0.15 + 0.1 th, lambda4_nu = 0.5 th; held lambda_inf = 1, lambda_inf_nu = 2.
Conditions (np_parametrization_constraints / 261006-diagnosis table): lambda2_nu >= 0, lambda4_nu >= 0,
L2(Y) = lambda2 + delta_lambda2 Y^2 >= 0 at Y = 0 and 2.5, B(Y) = 3 lambda_inf^2 lambda4 + L2(Y)^3 >= 0.
"""
import json
import os
import sys

import h5py
import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/wums")
from wums import ioutils  # noqa: E402

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_lattice_term_native"


def vals(path, sub=False):
    r = ioutils.pickle_load_h5py(h5py.File(path)["results"])
    if sub:
        r = r["mappings"]["Project ch0 ptll"]["saturated_fit"]
    h = r["parms"].get()
    return dict(zip(list(h.axes[0]), h.values()))


def conds(v):
    l2 = 0.4 + 0.5 * v["lambda2"]
    l4 = 0.4 + 0.5 * v["lambda4"]
    dl2 = 0.5 * v["delta_lambda2"]
    l2n = 0.15 + 0.1 * v["lambda2_nu"]
    l4n = 0.5 * v["lambda4_nu"]
    out = dict(lambda2_nu=l2n, lambda4_nu=l4n)
    for Y in (0.0, 2.5):
        L2 = l2 + dl2 * Y**2
        out[f"L2(Y={Y})"] = L2
        out[f"B(Y={Y})"] = 3 * 1.0**2 * l4 + L2**3
    out["phys"] = dict(lambda2=l2, lambda4=l4, delta_lambda2=dl2)
    return out


res = dict(
    start_LATB8=conds(vals(f"{D}/fitresults_LATB8.hdf5")),
    end_SATB8=conds(vals(f"{D}/fitresults_SATB8.hdf5", True)),
)
json.dump(res, open(f"{T}/wall_faces.json", "w"), indent=1)
print(json.dumps(res, indent=1))
