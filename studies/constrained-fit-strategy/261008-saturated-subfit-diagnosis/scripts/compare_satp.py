#!/usr/bin/env python3
"""SATP vs SATB8: final sub-fit loss, q, and the converged vectors (by name; differences only, alphaS never printed).
Writes compare_satp.json."""
import json
import os

import h5py
import numpy as np

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"


def snap(p):
    with h5py.File(p) as h:
        return dict(zip(h["parms"][...].astype(str), h["x"][...]))


a = snap(
    f"{C}/261007_lattice_term_native/snapshot_fitresults_SATB8_saturated_Project_ch0_ptll.hdf5"
)
b = snap(
    f"{C}/261008_saturated_subfit_diag/snapshot_fitresults_SATP_saturated_Project_ch0_ptll.hdf5"
)
common = sorted(set(a) & set(b))
d = np.array([b[k] - a[k] for k in common])
i = int(np.argmax(np.abs(d)))
L_main = 376.6750870887955
res = dict(
    n_common=len(common),
    max_abs_dx=float(np.abs(d).max()),
    argmax=common[i],
    dx_alphaS=float(b["alphaS"] - a["alphaS"]),
    L_SATB8=337.47616205811795,
    L_SATP=337.47616205794884,
)
res["dL"] = res["L_SATP"] - res["L_SATB8"]
res["q_SATB8"] = 2 * (L_main - res["L_SATB8"])
res["q_SATP"] = 2 * (L_main - res["L_SATP"])
json.dump(res, open(f"{T}/compare_satp.json", "w"), indent=1)
print(json.dumps(res, indent=1))
