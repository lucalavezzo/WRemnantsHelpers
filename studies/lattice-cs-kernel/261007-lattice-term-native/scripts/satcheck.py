#!/usr/bin/env python3
"""ONE gated cache load, no minimisation: the native lattice term inside the SATURATED-test fitter (rabbit
CompositeParamModel), on DATA with blinding ARMED, at LATB8's vector.

The main fitter is built from cmds/LATB8.cmd exactly as rabbit_fit builds it; the saturated fitter is then built the
way rabbit_fit.save_hists builds it for `-m Project ch0 ptll --computeSaturatedProjectionTests` (SaturatedProjectModel,
CompositeParamModel([model, saturated]), deepcopy, init_fit_parms, regularizers re-attached and armed, blinding
re-armed, x copied with the composite permutation). Printed: ONLY differences, booleans and names.

S1  lattice term (saturated fitter) - lattice term (main fitter), same physical point     (== 0)
S2  total loss (saturated, bin scales 1) - total loss (main)                                 (== 0)
A   p_full seen by the term - SCETlib submodel's scetlib_full_vector_tf of the vector the composite's own compute()
    hands it (recorded), all 53 entries; and - the main fitter's p_full                       (== 0)
B   armed: term alpha_s differs from the same map on the blinded internal x (bool); disarmed: equal (bool)
C   d chi2_lat / d x (saturated fitter): AD vs central FD, relative
D   nonzero term-gradient entries outside the 5 kernel parameters (incl. the saturated bin scales): must be none
E   kernel snapshot status
"""
import copy
import json
import os
import shlex
import sys

os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=true")
import numpy as np  # noqa: E402
import tensorflow as tf  # noqa: E402

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit/bin")
import rabbit_fit  # noqa: E402
from rabbit import fitter as rfitter  # noqa: E402
from rabbit import inputdata  # noqa: E402
from rabbit.mappings import helpers as mh  # noqa: E402
from rabbit.param_models import helpers as ph  # noqa: E402
from rabbit.param_models import param_model as rpm  # noqa: E402
from rabbit.regularization import helpers as rh  # noqa: E402
from wums import logging as wlogging  # noqa: E402

from wremnants.postprocessing.scetlib_ad import lattice_cs_term as LT  # noqa: E402

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LB8 = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261007_lattice_term_native/fitresults_LATB8.hdf5"
DROP = {"--snapshotFile", "--snapshotInterval", "-o", "--outpath", "--externalPostfit"}
BLOCK = (
    "alphaS",
    "lambda2_nu",
    "lambda4_nu",
    "resumTNP_gamma_nu",
    "resumTNP_gamma_cusp",
)


def main():
    out = {}
    toks = shlex.split(open(f"{TASK}/cmds/LATB8.cmd").read())
    argv, i = [], 1
    while i < len(toks):
        if toks[i] in DROP:
            i += 2
            continue
        argv.append(toks[i])
        i += 1
    args = rabbit_fit.make_parser().parse_args(argv + ["-o", "/tmp"])
    wlogging.setup_logger("satcheck", args.verbose, args.noColorLogger)
    indata = inputdata.FitInputData(args.filename, args.pseudoData, host_memory=False)
    pm = ph.load_models(args.paramModel, indata, **vars(args))
    f = rfitter.make_fitter(
        indata,
        pm,
        args,
        do_blinding=True,
        globalImpactsFromJVP=not args.globalImpactsDisableJVP,
    )
    f.tau.assign(args.regularizationStrength)
    f.regularizers = [
        rh.load_regularizer(
            m[0], mh.load_mapping(m[1], indata, *m[2:]), dtype=indata.dtype
        )
        for m in args.regularization
    ]
    f.defaultassign()
    f.set_nobs(f.indata.data_obs)
    f.set_blinding_offsets(blind=True)
    f.load_fitresult(LB8, None, profile=True)
    term = [r for r in f.regularizers if type(r).__name__ == "LatticeCSTerm"][0]
    pen_main = float(term.compute_nll_penalty(f.get_x(), None))
    loss_main = float(f._compute_loss(profile=True))
    pf_main = term.p_full_tf(f.get_x()).numpy()

    # ---- the saturated fitter, as rabbit_fit.save_hists builds it
    mapping = mh.load_mapping("Project", indata, "ch0", "ptll")
    sat = rpm.SaturatedProjectModel(
        indata,
        mapping.channel_info,
        mapping.output_indices(),
        allowNegativeParam=f.param_model.allowNegativeParam,
    )
    comp = rpm.CompositeParamModel([f.param_model, sat])
    fs = copy.deepcopy(f)
    orig = fs.param_model
    toy_x0 = tf.identity(fs.x0.value())
    saved, saved_tau = fs.regularizers, float(fs.tau.numpy())
    fs.init_fit_parms(
        comp,
        args.setConstraintMinimum,
        unblind=args.unblind,
        blinding_group=args.blindingGroup,
        freeze_parameters=args.freezeParameters,
    )
    fs.x0[comp.nparams :].assign(toy_x0[orig.nparams :])
    fs.x0[: orig.npoi].assign(toy_x0[: orig.npoi])
    fs.x0[comp.npoi : comp.npoi + orig.npou].assign(toy_x0[orig.npoi : orig.nparams])
    fs.regularizers = saved
    fs.tau.assign(saved_tau)
    fs.xdefaultassign()
    fs.arm_regularizers()
    fs.set_blinding_offsets(blind=True)
    xm = f.x.numpy()
    fs.x[: orig.npoi].assign(xm[: orig.npoi])
    fs.x[comp.npoi : comp.npoi + orig.npou].assign(xm[orig.npoi : orig.nparams])
    fs.x[comp.nparams :].assign(xm[orig.nparams :])
    fs.arm_regularizers()
    tsat = [r for r in fs.regularizers if type(r).__name__ == "LatticeCSTerm"][0]
    print(
        f"[sat] blinding enabled main {f.blinding.enabled}, saturated {fs.blinding.enabled}; term in the saturated "
        f"fitter is a distinct object: {tsat is not term}; its model: {type(tsat._pm).__name__}, SCETlib submodel "
        f"#{tsat._k}",
        flush=True,
    )

    out["S1_term_sat_minus_main"] = (
        float(tsat.compute_nll_penalty(fs.get_x(), None)) - pen_main
    )
    out["S2_loss_sat_minus_main"] = float(fs._compute_loss(profile=True)) - loss_main
    print(
        f"[sat S1] lattice term (saturated fitter) - (main fitter) = {out['S1_term_sat_minus_main']:+.3e}",
        flush=True,
    )
    print(
        f"[sat S2] total loss (saturated, bin scales 1) - (main) = {out['S2_loss_sat_minus_main']:+.3e}",
        flush=True,
    )

    # A: record what the composite's own compute() hands the SCETlib submodel (no cross-section evaluation)
    sub = comp.param_models[0]
    seen = {}
    real = sub.compute
    sub.compute = lambda p, full=False: (seen.__setitem__("p", p), 1.0)[1]  # noqa: E731
    try:
        comp.compute(tf.concat([fs.get_poi(), fs.get_model_nui()], axis=0))
    finally:
        sub.compute = real
    pf_sat = tsat.p_full_tf(fs.get_x()).numpy()
    pf_rec = sub.scetlib_full_vector_tf(seen["p"]).numpy()
    out["A_pfull_term_minus_compute_recorded"] = float(np.max(np.abs(pf_sat - pf_rec)))
    out["A_pfull_sat_minus_main"] = float(np.max(np.abs(pf_sat - pf_main)))
    print(
        f"[sat A] max |p_full(term) - p_full(vector composite.compute hands the SCETlib model)| = "
        f"{out['A_pfull_term_minus_compute_recorded']:.3e}; max |p_full(saturated) - p_full(main)| = "
        f"{out['A_pfull_sat_minus_main']:.3e} (both must be 0)",
        flush=True,
    )

    ias = sub.scetlib_names.index("alphas")
    raw = sub.scetlib_full_vector_tf(
        LT.submodel_vector(comp, 0, fs.x[: comp.nparams])
    ).numpy()
    out["B_armed_differs"] = bool(abs(pf_sat[ias] - raw[ias]) > 0)
    print(
        f"[sat B] armed: term alpha_s differs from the map on the blinded internal x: {out['B_armed_differs']}",
        flush=True,
    )

    names = [str(n) for n in np.asarray(fs.parms).astype(str)]
    with tf.GradientTape() as t:
        c = tsat.chi2_tf(fs.get_x())
    g = t.gradient(c, fs.x).numpy()
    xb = fs.x.numpy().copy()
    rel = {}
    for n in BLOCK:
        k = names.index(n)
        vals = []
        for s in (+1, -1):
            xx = xb.copy()
            xx[k] += s * 1e-4
            fs.x.assign(xx)
            vals.append(float(tsat.chi2_tf(fs.get_x())))
        fs.x.assign(xb)
        fd = (vals[0] - vals[1]) / 2e-4
        rel[n] = abs(g[names.index(n)] - fd) / max(abs(fd), 1e-300)
    out["C_rel_AD_vs_FD"] = rel
    print(
        "[sat C] |AD - FD| / |FD|: "
        + ", ".join(f"{k} {v:.1e}" for k, v in rel.items()),
        flush=True,
    )
    nz = [names[k] for k in np.flatnonzero(g) if names[k] not in BLOCK]
    nsat = sum(1 for n in names if n in set(np.asarray(sat.params).astype(str)))
    out["D_nonzero_outside_block"] = nz
    print(
        f"[sat D] nonzero term-gradient entries outside the kernel parameters ({nsat} saturated bin scales "
        f"included in the check): {nz} (must be [])",
        flush=True,
    )
    out["E_snapshot_status"] = int(tsat.core.gz.snapshot_status)
    print(f"[sat E] kernel snapshot status = {out['E_snapshot_status']}", flush=True)
    fs.set_blinding_offsets(blind=False)
    pf2 = tsat.p_full_tf(fs.get_x()).numpy()
    raw2 = sub.scetlib_full_vector_tf(
        LT.submodel_vector(comp, 0, fs.x[: comp.nparams])
    ).numpy()
    out["B_disarmed_equal"] = bool(pf2[ias] == raw2[ias])
    print(
        f"[sat B'] disarmed: term alpha_s == map on x: {out['B_disarmed_equal']}",
        flush=True,
    )
    json.dump(out, open(f"{TASK}/satcheck.json", "w"), indent=1, default=float)
    print("[sat] done", flush=True)


if __name__ == "__main__":
    main()
