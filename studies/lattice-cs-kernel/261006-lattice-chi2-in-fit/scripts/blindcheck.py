#!/usr/bin/env python3
"""Blinding-safe runtime check of the alpha_s source of the LIVE lattice term (one gated cache load, no minimisation).

The fitter is built from cmds/BLINDCHK.cmd (= the LATLIVE8 command) exactly as rabbit_fit.main() builds it (cf.
walled-multistart-census/261005-cold-min-restart/scripts/term_eval.py), on DATA, blinding offsets ARMED, at LATCHI8's
vector. Then, printing ONLY differences, booleans and public map coefficients (never an alpha_s value, a chi2 or a
residual):
  A. alpha_s seen by the term (its map on get_x()[i_alphaS]) - alpha_s seen by the param model
     (param_model._physical_tf(concat(get_poi(), get_model_nui()))[alphaS]) == 0 exactly;
  B. the term does NOT read the blinded internal coordinate Fitter.x: with blinding armed its alpha_s differs from the
     map applied to x[i_alphaS] (boolean only), and with blinding disarmed the two coincide (boolean);
  C. d(term)/d x[alphaS]: autodiff vs central finite differences in x (relative difference only);
  D. d(alpha_s model)/d x[alphaS] == the term's map slope (public: 0.002).
"""
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
from rabbit.regularization import helpers as rh  # noqa: E402
from wums import logging as wlogging  # noqa: E402

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L8 = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_lattice_chi2_in_fit/fitresults_LATCHI8.hdf5"
DROP = {"--snapshotFile", "--snapshotInterval", "-o", "--outpath", "--externalPostfit"}


def main():
    cmdfile = sys.argv[1] if len(sys.argv) > 1 else f"{TASK}/cmds/BLINDCHK.cmd"
    print(f"[chk] command from {cmdfile}", flush=True)
    toks = shlex.split(open(cmdfile).read())
    argv, i = [], 1
    while i < len(toks):
        if toks[i] in DROP:
            i += 2
            continue
        argv.append(toks[i])
        i += 1
    args = rabbit_fit.make_parser().parse_args(argv + ["-o", "/tmp"])
    wlogging.setup_logger("blindchk", args.verbose, args.noColorLogger)
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
    f.load_fitresult(L8, None, profile=True)
    reg = [r for r in f.regularizers if type(r).__name__ == "LatticeCSChi2"][0]
    print(
        f"[chk] blinding enabled={f.blinding.enabled}; term alphas mode={reg.alphas_mode}; map (public) {reg.as_map}",
        flush=True,
    )
    model = f.param_model
    j = list(model._scetlib_order).index("alphaS")
    ias = reg._ias
    print(
        f"[chk] alphaS index: get_x() {ias}, param model block {j}; model map c0,c1 = "
        f"{float(model._rp_c[0, j])}, {float(model._rp_c[1, j])}",
        flush=True,
    )

    def a_term():
        return float(reg.as_map[0] + reg.as_map[1] * f.get_x()[ias])

    def a_model():
        p = tf.concat([f.get_poi(), f.get_model_nui()], axis=0)
        return float(model._physical_tf(p[: model._n_scetlib])[j])

    def a_raw():
        return float(reg.as_map[0] + reg.as_map[1] * f.x[ias])

    dA = a_term() - a_model()
    print(
        f"[chk A] alpha_s(term) - alpha_s(param model) = {dA:+.3e}  (must be exactly 0)",
        flush=True,
    )
    print(
        f"[chk B] armed: term alpha_s differs from the map on the blinded internal x: {abs(a_term() - a_raw()) > 0}",
        flush=True,
    )
    # C. AD vs FD of the term in the internal coordinate (relative difference only)
    with tf.GradientTape() as t:
        pen = reg.compute_nll_penalty(f.get_x(), None)
    g = t.gradient(pen, f.x).numpy()[ias]
    x0 = f.x.numpy().copy()
    e = 1e-5
    vals = []
    for s in (+1, -1):
        xx = x0.copy()
        xx[ias] += s * e
        f.x.assign(xx)
        vals.append(float(reg.compute_nll_penalty(f.get_x(), None)))
    f.x.assign(x0)
    fd = (vals[0] - vals[1]) / (2 * e)
    print(
        f"[chk C] d term / d x[alphaS]: |AD - FD| / |FD| = {abs(g - fd) / max(abs(fd), 1e-300):.2e}",
        flush=True,
    )
    with tf.GradientTape() as t:
        p = tf.concat([f.get_poi(), f.get_model_nui()], axis=0)
        am = model._physical_tf(p[: model._n_scetlib])[j]
    dm = float(t.gradient(am, f.x).numpy()[ias])
    print(
        f"[chk D] d alpha_s(model) / d x[alphaS] = {dm:.6g}; term slope {reg.as_map[1]:.6g}; equal: {abs(dm - reg.as_map[1]) < 1e-15}",
        flush=True,
    )
    f.set_blinding_offsets(blind=False)
    # E (pert=live): each CS-kernel TNP seen by the term == the value the param model hands SCETlib; AD == FD
    for tn, it in getattr(reg, "_itnp", {}).items():
        jt = list(model._scetlib_order).index(tn)
        tt = float(reg.tnp_tf(f.get_x(), tn))
        p = tf.concat([f.get_poi(), f.get_model_nui()], axis=0)
        tm = float(model._physical_tf(p[: model._n_scetlib])[jt])
        with tf.GradientTape() as t:
            pen = reg.compute_nll_penalty(f.get_x(), None)
        gt = t.gradient(pen, f.x).numpy()[it]
        x0 = f.x.numpy().copy()
        vals = []
        for s_ in (+1, -1):
            xx = x0.copy()
            xx[it] += s_ * 1e-5
            f.x.assign(xx)
            vals.append(float(reg.compute_nll_penalty(f.get_x(), None)))
        f.x.assign(x0)
        fdt = (vals[0] - vals[1]) / 2e-5
        print(
            f"[chk E] {tn}: term - model = {tt - tm:+.3e} (must be 0); |AD - FD|/|FD| = "
            f"{abs(gt - fdt) / max(abs(fdt), 1e-300):.2e}",
            flush=True,
        )
    print(
        f"[chk B'] disarmed: term alpha_s == map on x: {abs(a_term() - a_raw()) == 0}; "
        f"term - model = {a_term() - a_model():+.3e}",
        flush=True,
    )
    print("[chk] done", flush=True)


if __name__ == "__main__":
    main()
