"""Read postfit CS (gamma_nu) lambdas + covariance from selected real-data Z fits.
Uses the existing reader wremnants.postprocessing.scetlib_np.fitresult_lambdas (values PHYSICAL,
cov from <run>/cov/fitresults.hdf5, result group 'results'). Writes postfits.json.
Run inside the WRemnants container with PR710 tree on PYTHONPATH."""

import json, os, sys
import numpy as np
from wremnants.postprocessing.scetlib_np import fitresult_lambdas as fl
from rabbit import io_tools

B = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
M = f"{B}/260722_Z_2D_MSHT20/ZMassDilepton_ptll_yll_realdata"
RUNS = [
    ("MSHT20 2D lat-cov+TMD prior, wall |Y|<5 (keeper)", f"{M}/latticeCovCond_priors"),
    ("MSHT20 2D lat-cov+TMD prior, wall |Y|<2.5", f"{M}/latticeCovCond_priors_ymax2p5"),
    (
        "MSHT20 2D lat-cov+TMD prior, no wall, warm (keeper)",
        f"{M}/latticeCovCond_nowall_seedWalledFull",
    ),
    ("MSHT20 2D CS lat-cov only, wall", f"{M}/cs3_tmdA_wall_restart"),
    ("MSHT20 2D no priors, wall |Y|<2.5", f"{M}/seedExt_noprior_wall_ymax2p5_restart"),
    ("MSHT20 2D no priors, no wall, cold", f"{M}/seedExt_noprior_nowall"),
    (
        "CT18Z 2D no priors, wall",
        f"{B}/260806_Z_2D_CT18Z_noprior_wall/ct18z_noprior_wall_restart",
    ),
    (
        "CT18Z 2D CS lat-cov, wall",
        f"{B}/260806_Z_2D_CT18Z_noprior_wall/ct18z_latticeCS_wall_restart",
    ),
    ("CT18Z 2D wall (David's fix, reference)", f"{B}/260723_Z_2D_davidFix"),
    (
        "MSHT20aN3LO 1D ptll wall m=0",
        f"{B}/260728_Z_1D_MSHT20aN3LO/ZMassDilepton_ptll_realdata/wall_m0",
    ),
    (
        "MSHT20aN3LO 1D ptll no wall, warm",
        f"{B}/260728_Z_1D_MSHT20aN3LO/ZMassDilepton_ptll_realdata/nowall_seedWalledFull",
    ),
]
GNU = ["lambda2_nu", "lambda4_nu", "lambda_inf_nu", "lambda6_nu"]
out = []
for name, d in RUNS:
    f = f"{d}/fitresults.hdf5"
    fc = f"{d}/cov/fitresults.hdf5"
    try:
        r = fl.read_lambdas(f)
    except Exception as e:
        print("FAIL", name, e)
        continue
    models = fl._resolve_models(f)
    ent = dict(
        name=name,
        dir=d,
        freeze=r["context"]["freeze"],
        spec=r["context"]["spec"],
        np_model_nu=models[1] if isinstance(models, tuple) else str(models),
        params={},
    )
    for p in GNU:
        v = r["params"].get(p, {})
        if v.get("present"):
            ent["params"][p] = dict(
                postfit=v["postfit"],
                prefit=v["prefit"],
                frozen=v["frozen"],
                sigma_fitfile=v["postfit_sigma"],
            )
    if os.path.exists(fc):
        names, mean, cov = fl.read_lambda_covariance(fc, names=GNU)
        ent["cov_names"], ent["cov_mean"], ent["cov"] = (
            names,
            list(mean),
            np.asarray(cov).tolist(),
        )
        # sanity: cov-pass values should equal the fit pass
        ent["cov_file"] = fc
    # blinding / meta
    try:
        _, meta = io_tools.get_fitresult(f, None, meta=True)
        a = meta.get("meta_info", {}).get("args", {})
        ent["blind"] = {k: a.get(k) for k in ("unblind", "blind", "noBlind") if k in a}
        ent["regularizer"] = a.get("regularization") or a.get("r")
        ent["externalPostfit"] = a.get("externalPostfit")
    except Exception as e:
        ent["meta_err"] = str(e)
    out.append(ent)
    print(name, json.dumps(ent["params"]), ent.get("cov_names"), ent["np_model_nu"])
json.dump(
    out,
    open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "postfits.json"), "w"
    ),
    indent=1,
    default=str,
)
