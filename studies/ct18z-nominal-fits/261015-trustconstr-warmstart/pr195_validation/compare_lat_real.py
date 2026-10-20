from rabbit import io_tools
import numpy as np

P = {
    "PR195": "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_pr_validation/fitresults_PR195_LAT.hdf5",
    "SATWSPC": "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_saturated_subfit_diagnosis/fitresults_SATWSPC_LAT.hdf5",
    "PLAIN": "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits/fitresults_LAT.hdf5",
}
res = {}
for k, f in P.items():
    r = io_tools.get_fitresult(f)
    m = r["mappings"]
    key = [x for x in m if "ptll" in x][0]
    sf = m[key]["saturated_fit"]
    st = sf["minimizer_status"]
    chi = m[key].get("chi2_saturated", None)
    nll_main = float(r["nllvalreduced"])
    nll_sat = float(sf["nllvalreduced"])
    p = sf["parms"].get()
    res[k] = (np.array(p.axes[0]), p.values(), np.sqrt(p.variances()))
    print(
        k,
        "main",
        nll_main,
        "sat",
        nll_sat,
        "q",
        2 * (nll_main - nll_sat),
        {
            x: st.get(x)
            for x in (
                "status",
                "nit",
                "optimality",
                "constr_violation",
                "barrier_parameter",
                "warm_start_legs",
                "warm_start_releasing",
            )
        },
    )
    print(
        "   constraint_values",
        np.array2string(np.array(st["constraint_values"]), precision=3),
    )
na, va, sa = res["PR195"]
nb, vb, sb = res["SATWSPC"]
assert list(na) == list(nb)
d = np.abs(va - vb) / np.where(np.isfinite(sb) & (sb > 0), sb, np.nan)
print(
    "max |dparm|/sigma (sat fit, sigma from SATWSPC where available):",
    np.nanmax(d),
    "n compared",
    np.sum(np.isfinite(d)),
    "max |dparm| abs",
    np.max(np.abs(va - vb)),
)
