#!/usr/bin/env python3
"""Physical NP lambdas (and theta) of the reference fits NOMSTIFF / XWSTIFF / XL4ZSTIFF. No alphaS value is read out.
physical = corr anchor + REPARAM width * theta (scetlib_ad params). Writes ../ref_points.json.
"""
import json, os
import numpy as np
from rabbit import io_tools
from wremnants.postprocessing.scetlib_ad import params as P
from wremnants.postprocessing.scetlib_ad import response as R

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits"
LAM = [
    "lambda2",
    "lambda4",
    "delta_lambda2",
    "lambda_inf",
    "lambda2_nu",
    "lambda4_nu",
    "lambda_inf_nu",
]
out = {}
for pf in ["NOMSTIFF", "XWSTIFF", "XL4ZSTIFF"]:
    fr, meta = io_tools.get_fitresult(f"{A}/fitresults_{pf}.hdf5", None, meta=True)
    h = fr["parms"].get()
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in h.axes[0]]
    x = np.asarray(h.values(), float)
    s = np.sqrt(np.asarray(h.variances(), float))
    cfg = R.corr_config_from_meta(meta)["config"]
    d = {}
    for n in LAM:
        a = P.corr_anchor_value(cfg, n)
        rp = P.reparam(n)
        if n in names:
            i = names.index(n)
            w = rp[1][0] if (rp is not None and rp[0] == "unit") else 1.0
            d[n] = dict(
                theta=float(x[i]),
                physical=float(a + w * x[i]),
                sigma_phys=float(w * s[i]),
                anchor=float(a),
                width=float(w),
                fitted=True,
            )
        else:
            d[n] = dict(
                physical=float(a), anchor=float(a), fitted=False, reparam=str(rp)
            )
    out[pf] = dict(nll=float(fr["nllvalreduced"]), n=len(names), lambdas=d)
    print(
        pf,
        out[pf]["nll"],
        {k: (round(v["physical"], 7), v["fitted"]) for k, v in d.items()},
    )
json.dump(
    out,
    open(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "ref_points.json",
        ),
        "w",
    ),
    indent=1,
)
