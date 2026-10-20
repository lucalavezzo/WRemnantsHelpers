from rabbit import io_tools
import numpy as np

P = {
    "PR195": "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_pr_validation/fitresults_PR195_NOLAT.hdf5",
    "NOLAT_PF": "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_nolat_postfit/fitresults_NOLAT_PF.hdf5",
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
nb, vb, sb = res["NOLAT_PF"]
assert list(na) == list(nb)
d = np.abs(va - vb) / np.where(np.isfinite(sb) & (sb > 0), sb, np.nan)
print(
    "max |dparm|/sigma (sat fit, sigma from NOLAT_PF where available):",
    np.nanmax(d),
    "n compared",
    np.sum(np.isfinite(d)),
    "max |dparm| abs",
    np.max(np.abs(va - vb)),
)
