"""Check 1: rabbit's stored postfit ptll projection (inclusive over yll) for LATL4ZUNWCOLD vs
CCCOLDSELF (and LATL4ZWALLCOLD if readable). Needs no alpha_s value; prints none.
Also prints the NP model parameters (theta) of each fit, EXCLUDING anything alpha_s-like.
"""

import json, os, sys
import numpy as np
from rabbit import io_tools

CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
FITS = {
    "LATL4ZUNWCOLD": f"{CEPH}/260923_lattice_fits/l4zero_unwalled/fitresults_LATL4ZUNWCOLD.hdf5",
    "CCCOLDSELF": f"{CEPH}/260917_cc_selfrestart/fitresults_CCCOLDSELF.hdf5",
    "LATL4ZWALLCOLD": f"{CEPH}/260923_lattice_fits/l4zero_walled/fitresults_LATL4ZWALLCOLD.hdf5",
    "LATL4ZUNWWARM": f"{CEPH}/260923_lattice_fits/l4zero_unwalled_warm/fitresults_LATL4ZUNWWARM.hdf5",
}
NP = ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]
out = {}
for tag, fn in FITS.items():
    try:
        fr = io_tools.get_fitresult(fn)
    except Exception as e:
        print(tag, "UNREADABLE:", type(e).__name__, str(e)[:100])
        continue
    if "mappings" not in fr:
        print(tag, "INCOMPLETE fitresult (no mappings yet)")
        continue
    m = fr["mappings"]["Project ch0 ptll"]
    ch = m["channels"]["ch0"]
    hp = ch["hist_postfit_inclusive"].get()
    hd = ch["hist_data_obs"].get()
    hpre = ch["hist_prefit_inclusive"].get()
    edges = hp.axes[0].edges
    v, var = hp.values(), hp.variances()
    d = hd.values()
    parms = fr["parms"].get()
    names = list(parms.axes[0])
    np_theta = {
        n: float(parms[n].value) for n in NP if n in names and "alpha" not in n.lower()
    }
    r = dict(
        edges=edges.tolist(),
        post=v.tolist(),
        post_err=(np.sqrt(var) if var is not None else np.zeros_like(v)).tolist(),
        data=d.tolist(),
        pre=hpre.values().tolist(),
        np_theta=np_theta,
        chi2=float(m["chi2"]),
        ndf=int(m["ndf"]),
        nll=float(fr["nllvalreduced"]),
        edm=float(fr["edmval"]),
    )
    sat = m.get("saturated_fit")
    if sat is not None:
        r["sat_edm"] = float(sat["edmval"])
        r["sat_msg"] = str(sat["minimizer_status"]["message"])
        r["sat_nit"] = int(sat["minimizer_status"]["nit"])
    out[tag] = r
    print(
        f"== {tag}: nll={r['nll']:.3f} edm={r['edm']:.2e} proj chi2={r['chi2']:.2f}/{r['ndf']} sat_edm={r.get('sat_edm')} msg={r.get('sat_msg')}"
    )
    print("   NP theta:", np_theta)
    print("   min postfit", v.min(), " n<=0:", int((v <= 0).sum()))
    # second difference of log(postfit/width) -> oscillation detector
    w = np.diff(edges)
    dens = v / w
    ratio = v / d
    print("   bins    ptll_lo  ptll_hi  postfit   data   post/data   pull")
    for i in range(len(v)):
        pull = (v[i] - d[i]) / np.sqrt(d[i])
        print(
            f"   {i:3d} {edges[i]:7.2f} {edges[i+1]:7.2f} {v[i]:10.1f} {d[i]:10.1f} {ratio[i]:8.4f} {pull:7.2f}"
        )
json.dump(
    out,
    open(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "check1_ptll.json",
        ),
        "w",
    ),
    indent=1,
)
