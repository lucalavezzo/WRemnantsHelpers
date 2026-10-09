#!/usr/bin/env python3
"""C2A / R2A (fitresult or snapshot) vs NOMSTIFF: dNLL, dalphaS/sigma (blinded: differences only), ||dtheta/sigma||,
EDM, and every active wall condition's value at each point, raw and in units of the NP exponent at b_max = 12.6
(c~ = scale * c; < 0 is a violation). Conditions come from np_damping_wall.damping_conditions itself; theta -> physical
from the wall's own printed map (lambda2, lambda4 = 0.4 + 0.5 t; delta_lambda2 = 0.5 t; lambda2_nu = 0.15 + 0.1 t;
lambda_inf = 1, lambda_inf_nu = 2, lambda4_nu = 0 held). Run in the container. Writes compare_points.json.

    python3 compare_points.py [NAME=path ...]   (default: C2A, R2A results/snapshots if present)
"""
import json
import os
import sys

import h5py
import numpy as np
from rabbit import io_tools

from wremnants.postprocessing.scetlib_ad import np_damping_wall as W

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
O = f"{A}/261008_c2_wall_test"
NOM = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
MAP = {
    "lambda2": (0.4, 0.5),
    "lambda4": (0.4, 0.5),
    "delta_lambda2": (0.0, 0.5),
    "lambda2_nu": (0.15, 0.1),
}
HELD = {"lambda_inf": 1.0, "lambda_inf_nu": 2.0, "lambda4_nu": 0.0}


def load(path):
    try:
        fr = io_tools.get_fitresult(path, None)
        h = fr["parms"].get()
        names = [str(n) for n in h.axes[0]]
        x = np.asarray(h.values(), float)
        return dict(
            kind="fitresult",
            names=names,
            x=x,
            sig=np.sqrt(np.asarray(h.variances(), float)),
            nll=float(fr["nllvalreduced"]),
            edm=float(fr["edmval"]),
        )
    except Exception:  # noqa: BLE001  -- a snapshot is a bare (x, parms) file
        with h5py.File(path, "r") as f:
            return dict(
                kind="snapshot",
                names=list(f["parms"][...].astype(str)),
                x=f["x"][...],
                sig=None,
                nll=None,
                edm=None,
                reason=str(f.attrs.get("reason", "")),
            )


def faces(names, x):
    v = dict(HELD)
    for n, (a, w) in MAP.items():
        v[n] = a + w * x[names.index(n)]
    out = {}
    for c in W.damping_conditions("tanh_2", "tanh_2", 2.5):
        if all(n in HELD for n in c.names):
            continue
        raw = float(c.value(v, W.numpy_relu2) - c.bound)
        out[c.label] = dict(
            raw=raw, normalised=raw * c.scale, c2_width_raw=1e-3 / c.scale
        )
    return out


def main():
    pts = {}
    for a in sys.argv[1:]:
        k, p = a.split("=", 1)
        pts[k] = p
    if not pts:
        for pf in ("C2A", "R2A"):
            for p in (
                f"{O}/fitresults_{pf}.hdf5",
                f"{O}/snapshot_fitresults_{pf}.hdf5",
            ):
                if os.path.exists(p) and os.path.getsize(p) > 200000:
                    pts[pf] = p
                    break
    ref = load(NOM)
    ia = ref["names"].index("alphaS")
    res = {
        "NOMSTIFF": dict(
            file=NOM,
            nll=ref["nll"],
            edm=ref["edm"],
            faces=faces(ref["names"], ref["x"]),
        )
    }
    for k, p in pts.items():
        d = load(p)
        assert d["names"] == ref["names"], f"{k}: parameter layout differs"
        r = dict(
            file=p,
            kind=d["kind"],
            reason=d.get("reason"),
            edm=d["edm"],
            dnll_vs_nomstiff=None if d["nll"] is None else d["nll"] - ref["nll"],
            dalphaS_over_sigma=float((d["x"][ia] - ref["x"][ia]) / ref["sig"][ia]),
            norm_dtheta_over_sigma=float(
                np.linalg.norm((d["x"] - ref["x"]) / ref["sig"])
            ),
            max_abs_dtheta_over_sigma=float(
                np.max(np.abs((d["x"] - ref["x"]) / ref["sig"]))
            ),
            faces=faces(d["names"], d["x"]),
        )
        if d["sig"] is not None:
            r["sigma_alphaS_ratio"] = float(d["sig"][ia] / ref["sig"][ia])
        res[k] = r
    json.dump(res, open(f"{T}/compare_points.json", "w"), indent=1)
    for k, r in res.items():
        print(
            f"== {k}: "
            + ", ".join(
                f"{q}={r.get(q)}"
                for q in (
                    "kind",
                    "reason",
                    "dnll_vs_nomstiff",
                    "edm",
                    "dalphaS_over_sigma",
                    "norm_dtheta_over_sigma",
                    "max_abs_dtheta_over_sigma",
                    "sigma_alphaS_ratio",
                )
                if q in r
            )
        )
        for lab, f in r["faces"].items():
            if f["normalised"] < 1e-2:
                print(
                    f"   {lab}: raw {f['raw']:.4g}, normalised {f['normalised']:.4g} (c2 width {f['c2_width_raw']:.3g})"
                )


if __name__ == "__main__":
    main()
