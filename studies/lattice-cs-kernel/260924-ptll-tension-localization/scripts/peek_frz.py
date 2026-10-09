import numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260924_ptll_tension_loc"
m = io_tools.get_fitresult(
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260923_lattice_fits/l4zero_walled/fitresults_LATL4ZWALLCOLD.hdf5"
)
mp = m["parms"].get()
mn = [str(n) for n in mp.axes[0]]
for tag, f in [
    ("free", "PT3044/fitresults_PT3044.hdf5"),
    ("FRZAS", "FRZAS/fitresults_FRZAS.hdf5"),
]:
    r = io_tools.get_fitresult(f"{A}/{f}")
    mpg = r["mappings"]["Project ch0 ptll"]
    sf = mpg["saturated_fit"]
    h = sf["parms"].get()
    n = [str(x) for x in h.axes[0]]
    v = h.values()
    e = np.sqrt(np.diag(sf["cov"].get().values()))
    s = np.array([v[n.index(f"saturated_ch0_ptll{i}")] for i in range(39)])
    es = np.array([e[n.index(f"saturated_ch0_ptll{i}")] for i in range(39)])
    print(
        tag,
        "q",
        mpg["chi2_saturated"],
        "edm",
        sf["edmval"],
        "dAs(theta)",
        v[n.index("alphaS")] - mp.values()[mn.index("alphaS")],
    )
    print("  scale^2:", np.round(s**2, 4))
    print("  err(scale^2):", np.round(2 * s * es, 4))
