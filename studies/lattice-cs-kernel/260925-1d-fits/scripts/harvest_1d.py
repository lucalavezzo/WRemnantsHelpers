import sys, numpy as np

sys.path.insert(
    0,
    "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/260923-lattice-fits/scripts",
)
from rabbit import io_tools, inputdata
from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
ind = inputdata.FitInputData(
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
inp = wall.resolve_wall_inputs(ind)
specs = inp["specs"]
fits = {
    "P1DUNWNODL2W": "260925_1d_fits/P1DUNWNODL2W/fitresults_P1DUNWNODL2W.hdf5",
    "P1DWALLNODL2W": "260925_1d_fits/P1DWALLNODL2W/fitresults_P1DWALLNODL2W.hdf5",
    "P1DWALL": "260925_1d_fits/P1DWALL/fitresults_P1DWALL.hdf5",
    "P1DUNW": "260925_1d_fits/P1DUNW/fitresults_P1DUNW.hdf5",
    "CCWALLWARMPF": "260917_cc_fits_wall/fitresults_CCWALLWARMPF.hdf5",
    "CCWALLCOLDR": "260917_cc_fits_wall/fitresults_CCWALLCOLDR.hdf5",
    "CCKRYLOVWARM": "260917_cc_fits_hvpfix/fitresults_CCKRYLOVWARM.hdf5",
}
R = {}
for k, f in fits.items():
    r = io_tools.get_fitresult(f"{A}/{f}")
    h = r["parms"].get()
    n = [str(x) for x in h.axes[0]]
    v = dict(zip(n, h.values()))
    e = dict(zip(n, np.sqrt(h.variances())))
    phys = {
        x: float(wall.physical_from_theta(specs[x], v[x]))
        for x in ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]
        if x in v
    }
    R[k] = dict(
        v=v,
        e=e,
        nll=float(r["nllvalreduced"]),
        ndfsat=r.get("ndfsat"),
        edm=float(r["edmval"]),
        phys=phys,
    )
    print(
        f"{k:13s} NLL {R[k]['nll']:8.3f} ndfsat {R[k]['ndfsat']} EDM {R[k]['edm']:.1e} sigma_as[1e-3] {2*e['alphaS']:.3f}  "
        + " ".join(f"{x}={y:+.4f}" for x, y in phys.items())
    )
    print(
        "    pulls: A0_15_20 %+.2f lumi %+.2f mb_up %+.2f weak %+.2f FSR %+.2f"
        % tuple(
            v.get(x, np.nan)
            for x in [
                "QCDscaleZfine_PtV15_20helicity_0_SymAvg",
                "lumi",
                "mb_up",
                "weak_default",
                "horacelophotosmecoffew_FSR_Corr0",
            ]
        )
    )


def d(a, b):
    return (R[a]["v"]["alphaS"] - R[b]["v"]["alphaS"]) / R[b]["e"]["alphaS"]


print(
    "dAlphaS (sigma of 2nd): P1DWALL-CCWALLWARMPF %+.2f ; P1DWALL-CCWALLCOLDR %+.2f ; P1DUNW-CCKRYLOVWARM %+.2f ; P1DUNW-P1DWALL %+.2f"
    % (
        d("P1DWALL", "CCWALLWARMPF"),
        d("P1DWALL", "CCWALLCOLDR"),
        d("P1DUNW", "CCKRYLOVWARM"),
        d("P1DUNW", "P1DWALL"),
    )
)
ref = "CCWALLWARMPF"
print("Delta alphaS vs", ref)
for k in [
    "P1DUNWNODL2W",
    "P1DWALLNODL2W",
    "P1DWALL",
    "P1DUNW",
    "CCWALLWARMPF",
    "CCKRYLOVWARM",
    "CCWALLCOLDR",
]:
    dth = R[k]["v"]["alphaS"] - R[ref]["v"]["alphaS"]
    print(f"  {k:13s} d={2*dth:+.3f}e-3  = {dth/R[ref]['e']['alphaS']:+.2f} sigma_ref")
