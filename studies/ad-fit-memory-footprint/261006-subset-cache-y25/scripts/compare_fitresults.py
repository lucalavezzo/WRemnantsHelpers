#!/usr/bin/env python3
"""SUBY25 (subset cache) vs NOMSTIFF (full cache, the real fit) and MEMNOM (full cache, same --noFit recipe).
Prints only DIFFERENCES / relative differences (alphaS is blinded: no absolute parameter or NLL values).
"""
import json, sys
import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
F = dict(
    SUBY25=f"{A}/261006_subset_cache_y25/fitresults_SUBY25.hdf5",
    NOMSTIFF=f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
    MEMNOM=f"{A}/261006_memory_breakdown/fitresults_MEMNOM.hdf5",
)
R = {}
for k, p in F.items():
    fr = io_tools.get_fitresult(p, None)
    h = fr["parms"].get()
    R[k] = dict(
        nll=float(
            np.asarray(
                fr["nllvalreduced"].get()
                if hasattr(fr["nllvalreduced"], "get")
                else fr["nllvalreduced"]
            )
        ),
        edm=float(
            np.asarray(
                fr["edmval"].get() if hasattr(fr["edmval"], "get") else fr["edmval"]
            )
        ),
        names=[str(n) for n in h.axes[0]],
        x=np.asarray(h.values(), float),
        var=np.asarray(h.variances(), float),
        cov=np.asarray(fr["cov"].get().values(), float),
    )
out = {}
s = R["SUBY25"]
for ref in ("NOMSTIFF", "MEMNOM"):
    r = R[ref]
    assert r["names"] == s["names"]
    d = dict(
        nll_diff=s["nll"] - r["nll"],
        nll_rel=(s["nll"] - r["nll"]) / abs(r["nll"]),
        nll_bit_identical=bool(
            np.float64(s["nll"]).view(np.uint64) == np.float64(r["nll"]).view(np.uint64)
        ),
        edm_rel=(s["edm"] - r["edm"]) / abs(r["edm"]),
        parms_bit_identical=bool(
            np.array_equal(s["x"].view(np.uint64), r["x"].view(np.uint64))
        ),
        cov_diag_max_rel=float(
            np.max(
                np.abs(np.diag(s["cov"]) - np.diag(r["cov"]))
                / np.abs(np.diag(r["cov"]))
            )
        ),
        cov_max_abs_rel_to_diag=float(
            np.max(
                np.abs(s["cov"] - r["cov"])
                / np.sqrt(np.outer(np.diag(r["cov"]), np.diag(r["cov"])))
            )
        ),
        sigma_max_rel=float(
            np.max(np.abs(np.sqrt(s["var"]) - np.sqrt(r["var"])) / np.sqrt(r["var"]))
        ),
    )
    out[ref] = d
    print(
        f"SUBY25 vs {ref}: "
        + "  ".join(
            f"{k}={v:.3e}" if isinstance(v, float) else f"{k}={v}" for k, v in d.items()
        )
    )
print(
    f"edm SUBY25 {s['edm']:.6e}  NOMSTIFF {R['NOMSTIFF']['edm']:.6e}  MEMNOM {R['MEMNOM']['edm']:.6e}"
)
out["edm"] = {k: R[k]["edm"] for k in R}
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "/dev/null", "w"), indent=1)
