import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
MAP = {"lambda2_nu": (0.15, 0.1), "lambda4_nu": (0.0, 0.5)}
for k, p in [
    ("XWSTIFF (Z only, l4nu free)", "260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5"),
    ("XL4ZSTIFF (Z only, l4nu=0)", "260930_stiff_wall_fits/fitresults_XL4ZSTIFF.hdf5"),
    (
        "NOMSTIFF (1D Gauss lattice, l4nu=0)",
        "260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5",
    ),
    ("LATFROZ_V3 (joint)", "261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5"),
]:
    fr = io_tools.get_fitresult(f"{A}/{p}", None)
    h = fr["parms"].get()
    names = list(h.axes[0])
    cov = fr["cov"].get().values()
    ii = [names.index(n) for n in MAP if n in names]
    out = []
    for n in MAP:
        if n not in names:
            out.append(f"{n} fixed")
            continue
        i = names.index(n)
        c0, c1 = MAP[n]
        out.append(f"{n}={c0+c1*h.values()[i]:.4f}+-{c1*np.sqrt(cov[i,i]):.4f}")
    if len(ii) == 2:
        r = cov[ii[0], ii[1]] / np.sqrt(cov[ii[0], ii[0]] * cov[ii[1], ii[1]])
        out.append(f"rho={r:.3f}")
    print("RES", k, "  ".join(out))
