import sys, os, glob

sys.path.append("/home/submit/lavezzo/alphaS/WRemnants/")
import rabbit.io_tools
import numpy as np

base = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260430_debug/"
poi = "pdfAlphaS"

# all 4D fits
dirs = sorted(
    [
        d
        for d in os.listdir(base)
        if d.startswith(
            "ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_LatticeNoConstraints"
        )
    ]
)

ref = "ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_LatticeNoConstraints"


def get_pull(fpath):
    try:
        fitresult, meta = rabbit.io_tools.get_fitresult(fpath, meta=True)
    except Exception as e:
        return None, None, f"open err: {e}"
    parms = fitresult["parms"].get()
    try:
        h = parms[poi]
        val = float(h.value)
        err = float(np.sqrt(h.variance))
        return val, err, None
    except Exception as e:
        # parms is a hist.Hist with StrCategory axis
        try:
            ax = parms.axes[0]
            names = list(ax)
            idx = names.index(poi)
            vals = parms.values()
            vars_ = parms.variances()
            return float(vals[idx]), float(np.sqrt(vars_[idx])), None
        except Exception as e2:
            return None, None, f"err: {e}; {e2}"


results = {}
for d in dirs:
    fpath = os.path.join(base, d, "fitresults.hdf5")
    if not os.path.exists(fpath):
        results[d] = (None, None, "no fitresults.hdf5")
        continue
    val, err, err_msg = get_pull(fpath)
    results[d] = (val, err, err_msg)

ref_val, ref_err, _ = results[ref]
print(f"Reference: {ref}")
print(f"  pull (value) = {ref_val:.6f}, sigma = {ref_err:.6f}")
print()
print(f"{'fit':<110} {'pull':>10} {'sigma':>10} {'Δpull':>10}  {'Δσ%':>8}")
for d in dirs:
    val, err, em = results[d]
    if val is None:
        print(f"{d:<110}  ERROR: {em}")
        continue
    dpull = val - ref_val
    dsig = (err / ref_err - 1.0) * 100 if ref_err else 0
    print(f"{d:<110} {val:>10.5f} {err:>10.5f} {dpull:>+10.5f}  {dsig:>+7.1f}%")
