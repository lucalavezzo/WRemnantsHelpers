# blinded: prints only differences in sigma units
import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
F = {
    "XWSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
    "XL4ZSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XL4ZSTIFF.hdf5",
    "NOMSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
    "LATB8": f"{A}/261007_lattice_term_native/fitresults_LATB8.hdf5",
    "V1": f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V1.hdf5",
    "V2": f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V2.hdf5",
    "V3": f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5",
}
R = {}
for k, p in F.items():
    fr = io_tools.get_fitresult(p, None)
    h = fr["parms"].get()
    names = list(h.axes[0])
    i = names.index("alphaS")
    R[k] = (
        h.values()[i],
        np.sqrt(h.variances()[i]),
        {
            n: (h.values()[names.index(n)])
            for n in ("lambda2_nu", "lambda4_nu")
            if n in names
        },
    )
for ref in ("XWSTIFF", "XL4ZSTIFF"):
    v0, s0, _ = R[ref]
    print(f"--- vs {ref} (sigma_ref units)")
    for k, (v, s, l) in R.items():
        print(
            f"{k:10s} dalphaS/sig={(v-v0)/s0:+.3f}  sigma ratio={s/s0:.3f}  theta(l2nu,l4nu)={l}"
        )
