#!/usr/bin/env python3
"""Split the ptll projected-saturated 2dNLL into data / card-constraint / model-prior / wall / lattice terms,
main fit vs its projection sub-fit, and list the parameters that move most. usage: decompose_projection_sat.py <fitresult>
"""
import sys, numpy as np, h5py

sys.path.insert(
    0,
    "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/260923-lattice-fits/scripts",
)
import analyze_fits as A
from rabbit import inputdata, io_tools
from wums import ioutils
from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall

path = sys.argv[1]
r = io_tools.get_fitresult(path)
meta = ioutils.pickle_load_h5py(h5py.File(path, "r")["meta"])
ind = inputdata.FitInputData(A.CARDA)
inp = wall.resolve_wall_inputs(ind)
specs = inp["specs"]
conds = wall.damping_conditions(inp["np_model"], inp["np_model_nu"], inp["ymax"])
systs = [s.decode() if isinstance(s, bytes) else str(s) for s in ind.systs]
cwd = dict(zip(systs, np.asarray(ind.constraintweights)))
pr, mu, H, C = A.term_from_card(A.LATCARD)
pp = meta["param_priors"]
pn = [p.decode() if isinstance(p, bytes) else str(p) for p in pp["params"]]
mask = np.asarray(pp["mask"], bool)
sig = np.asarray(pp["sigmas"], float)
mean = np.asarray(pp["means"], float) if pp["means"] is not None else np.zeros(len(pn))


def decomp(h, nll):
    names = [str(n) for n in h.axes[0]]
    th = dict(zip(names, h.values()))
    lcm = sum(
        0.5 * ((th[n] - mean[i]) / sig[i]) ** 2 for i, n in enumerate(pn) if mask[i]
    )
    lcc = {n: 0.5 * cwd[n] * th[n] ** 2 for n in systs if n in th}
    phys = {
        n: (
            float(wall.physical_from_theta(specs[n], th[n]))
            if n in th
            else float(inp["anchors"][n])
        )
        for n in inp["names"]
    }
    armed = [c for c in conds if any(n in th for n in c.names)]
    lpen = float(
        sum(c.penalty(phys, wall.numpy_relu2) for c in armed) * np.exp(2 * A.TAU)
    )
    t = np.array([th[n] for n in pr])
    lext = 0.5 * float((t - mu) @ H @ (t - mu))
    lcs = sum(lcc.values())
    return dict(
        nll=nll,
        lcm=lcm,
        lcc=lcs,
        lpen=lpen,
        lext=lext,
        ln=nll - lcm - lcs - lpen - lext,
        th=th,
        lccd=lcc,
        phys=phys,
    )


m = decomp(r["parms"].get(), float(r["nllvalreduced"]))
sf = r["mappings"]["Project ch0 ptll"]["saturated_fit"]
s = decomp(sf["parms"].get(), float(sf["nllvalreduced"]))
for k in ["nll", "ln", "lcm", "lcc", "lpen", "lext"]:
    print(f"{k:5s} main {m[k]:10.4f} sat {s[k]:10.4f}  2*diff {2*(m[k]-s[k]):8.3f}")
print(
    "NP phys main/sat:",
    {
        n: (round(m["phys"][n], 4), round(s["phys"][n], 4))
        for n in ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu"]
    },
)
# biggest movers
cm = [
    (n, m["th"][n], s["th"].get(n, np.nan))
    for n in m["th"]
    if n in s["th"] and not n.startswith("saturated")
]
cm.sort(key=lambda x: -abs(x[1] - x[2]))
print("top shifts (theta main -> sat):")
for n, a, b in [x for x in cm if x[0] != "alphaS"][:25]:  # alphaS: Delta only (blinded)
    print(
        f"  {n:40s} {a:+.3f} -> {b:+.3f}   dlc {2*(m['lccd'].get(n,0)-s['lccd'].get(n,0)):+.2f}"
    )
sat = np.array([s["th"][f"saturated_ch0_ptll{i}"] for i in range(39)])
print("sat params raw:", np.round(sat, 4))
print("squared:", np.round(sat**2, 4))
print("alphaS shift (theta units) main->sat:", s["th"]["alphaS"] - m["th"]["alphaS"])
