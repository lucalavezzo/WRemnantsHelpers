#!/usr/bin/env python3
"""ONE gated cache load, no minimisation: the geometry of the projected-ptll saturated sub-fit (SATB8).

The main fitter is built from LATB8's command (261007-lattice-term-native/cmds/LATB8.cmd) exactly as rabbit_fit builds
it, the saturated fitter exactly as rabbit_fit.save_hists builds it (the recipe of that task's satcheck.py, which
passed S1/S2 = 0). Two points:
  x_s = the sub-fit's warm start (LATB8's minimum, 39 bin scales at 1)       check: loss == 376.6751 (SATB8 log)
  x_e = SATB8's converged sub-fit vector (its 'converged' snapshot, by name)  check: loss == 337.47616205811795

Measured (each step writes its result before the next one starts, so a crash keeps what was done):
  T   timings: one loss+grad, one HVP (revrev, as the fit), one dense Hessian
  L1  loss on the straight line x_s + t (x_e - x_s)
  L2  the same line with the 39 bin scales PROFILED analytically at each t (s_j <- s_j N_j / nu_j, 4 fixed-point
      passes; exact conditional MLE for Poisson, approximate with BB-lite): does eliminating the scales remove the
      barrier / curvature of the valley?
  H   dense Hessians at x_s and x_e -> ceph npz (spectra and preconditioning analysis are done offline, numpy only)
  N   the exact Newton step from x_s (d = -|H_s|^-1 g_s, spectral abs if indefinite): predicted reduction, loss at
      x_s + a d for a in (0.25, 0.5, 1), and the same with the scales re-profiled. This is a curvature diagnostic
      (how far one exact second-order step gets), NOT a fit: nothing is minimised.
  N2  the same from a point near the end of the valley (theta = x_s + 0.9 (x_e - x_s), scales profiled; one more
      dense Hessian): does one exact Newton step close the tail (Krylov inexactness) or not (nonlinearity)?
Printed / written: losses, differences, timings, norms. alphaS is blinded: no alphaS value is ever printed or written
(x vectors go to ceph only, in the fitter's internal blinded frame, like every snapshot).
"""
import copy
import json
import os
import shlex
import sys
import time

os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=true")
import h5py  # noqa: E402
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

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAT = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/261007-lattice-term-native"
C = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
LB8 = f"{C}/261007_lattice_term_native/fitresults_LATB8.hdf5"
SNAP_E = f"{C}/261007_lattice_term_native/snapshot_fitresults_SATB8_saturated_Project_ch0_ptll.hdf5"
OUT = f"{C}/261008_saturated_subfit_diag"
DROP = {"--snapshotFile", "--snapshotInterval", "-o", "--outpath", "--externalPostfit"}
L_START_LOG = 376.6751  # SATB8 log / lattice logbook (main loss, rounded)
L_END_LOG = 337.47616205811795  # SATB8 sub-fit final loss

res = {}


def dump():
    json.dump(res, open(f"{TASK}/hess_diag.json", "w"), indent=1, default=float)


def say(msg):
    print(f"[diag {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    toks = shlex.split(open(f"{LAT}/cmds/LATB8.cmd").read())
    argv, i = [], 1
    while i < len(toks):
        if toks[i] in DROP:
            i += 2
            continue
        argv.append(toks[i])
        i += 1
    args = rabbit_fit.make_parser().parse_args(argv + ["-o", OUT])
    wlogging.setup_logger("hess_diag", args.verbose, args.noColorLogger)
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
    loss_main = float(f._compute_loss(profile=True))

    # ---- the saturated fitter, as rabbit_fit.save_hists builds it (copied from satcheck.py)
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
    del f
    res["t_build_s"] = time.time() - t0
    names = np.asarray(fs.parms).astype(str)
    n = len(names)
    isat = np.array([k for k, p in enumerate(names) if p.startswith("saturated_")])
    jsat = np.array([int(names[k].rsplit("ptll", 1)[1]) for k in isat])
    assert sorted(jsat.tolist()) == list(
        range(len(isat))
    ), "unexpected saturated parameter names"
    idx_out = np.asarray(
        mapping.output_indices()["ch0"]
    )  # flat ch0 bin -> ptll output bin
    assert (
        idx_out.min() >= 0
    ), "projection leaves ch0 bins unused; the profiling below assumes it does not"
    nobs = fs.nobs.numpy()
    N_j = np.bincount(idx_out, weights=nobs, minlength=len(isat))
    res["n_params"] = n
    res["n_sat"] = int(len(isat))
    res["cw_zero"] = [str(p) for p in names[fs.cw.numpy() == 0]]
    say(
        f"built in {res['t_build_s']:.0f} s; {n} params, {len(isat)} bin scales; main loss {loss_main:.6f}"
    )

    def lg():
        v, g = fs.loss_val_grad()
        return float(v), g.numpy()

    yfun = tf.function(
        lambda: fs._compute_yields(inclusive=True, profile=True, full=False)
    )

    def profile_scales(npass=4):
        """s_j <- s_j * N_j / nu_j(current) at fixed theta; x_sat = sqrt(s)."""
        x = fs.x.numpy().copy()
        for _ in range(npass):
            nu = yfun().numpy()
            nu_j = np.bincount(idx_out, weights=nu, minlength=len(isat))
            s = x[isat] ** 2
            s = s * N_j[jsat] / nu_j[jsat]
            x[isat] = np.sqrt(s)
            fs.x.assign(x)
        return x

    # ---- start point, timings
    x_s = fs.x.numpy().copy()
    t = time.time()
    L_s, g_s = lg()
    res["t_lossgrad_first_s"] = time.time() - t
    t = time.time()
    L_s, g_s = lg()
    res["t_lossgrad_s"] = time.time() - t
    res["L_s"] = L_s
    res["L_s_minus_log"] = L_s - L_START_LOG
    res["L_s_minus_main"] = L_s - loss_main
    v = np.random.default_rng(1).standard_normal(n)
    v /= np.linalg.norm(v)
    t = time.time()
    fs.loss_val_grad_hessp(tf.constant(v))
    res["t_hvp_first_s"] = time.time() - t
    t = time.time()
    _, _, hv_rev = fs.loss_val_grad_hessp(tf.constant(v))
    res["t_hvp_s"] = time.time() - t
    try:  # the other autodiff mode (--hvpMethod fwdrev): cost and agreement only
        fs.loss_val_grad_hessp_fwdrev(tf.constant(v))
        t = time.time()
        _, _, hv_fwd = fs.loss_val_grad_hessp_fwdrev(tf.constant(v))
        res["t_hvp_fwdrev_s"] = time.time() - t
        res["hvp_fwdrev_vs_revrev_rel"] = float(
            np.linalg.norm(hv_fwd.numpy() - hv_rev.numpy())
            / np.linalg.norm(hv_rev.numpy())
        )
    except Exception as ex:  # noqa: BLE001
        res["hvp_fwdrev_error"] = str(ex)[:300]
    res["gnorm_s"] = float(np.linalg.norm(g_s))
    res["gnorm_s_sat"] = float(np.linalg.norm(g_s[isat]))
    say(
        f"x_s: loss {L_s:.6f} (- log {res['L_s_minus_log']:+.2e}, - main {res['L_s_minus_main']:+.2e}); "
        f"loss+grad {res['t_lossgrad_s']:.1f} s, HVP {res['t_hvp_s']:.1f} s; |g| {res['gnorm_s']:.3e} "
        f"(bin scales {res['gnorm_s_sat']:.3e})"
    )
    dump()

    # ---- end point
    with h5py.File(SNAP_E, "r") as h:
        pe = h["parms"][...].astype(str)
        xe_raw = h["x"][...]
    pos = {p: k for k, p in enumerate(pe)}
    missing = [p for p in names if p not in pos]
    assert not missing, f"end snapshot lacks {missing[:5]}"
    x_e = np.array([xe_raw[pos[p]] for p in names])
    fs.x.assign(x_e)
    L_e, g_e = lg()
    res["L_e"] = L_e
    res["L_e_minus_log"] = L_e - L_END_LOG
    res["gnorm_e"] = float(np.linalg.norm(g_e))
    say(
        f"x_e: loss {L_e:.10f} (- SATB8 final {res['L_e_minus_log']:+.2e}); |g| {res['gnorm_e']:.3e}"
    )
    dump()
    D = x_e - x_s

    # ---- L1 / L2: straight line, raw and with the scales profiled
    res["line_raw"] = {}
    res["line_prof"] = {}
    for tt in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]:
        if 0.0 < tt < 1.0:
            fs.x.assign(x_s + tt * D)
            res["line_raw"][f"{tt:g}"] = lg()[0]
        fs.x.assign(x_s + tt * D)
        xp = profile_scales()
        Lp = lg()[0]
        res["line_prof"][f"{tt:g}"] = Lp
        res.setdefault("line_prof_scale_rms_minus1", {})[f"{tt:g}"] = float(
            np.sqrt(np.mean((xp[isat] ** 2 - 1) ** 2))
        )
        say(
            f"line t={tt:g}: raw {res['line_raw'].get(f'{tt:g}', float('nan')):.4f}  profiled-scales {Lp:.4f}"
        )
        dump()

    # ---- H at x_s
    fs.x.assign(x_s)
    t = time.time()
    _, g, H = fs.loss_val_grad_hess()
    res["t_hess_s"] = time.time() - t
    H_s = H.numpy()
    del H, g
    H_s = 0.5 * (H_s + H_s.T)
    np.savez(
        f"{OUT}/hess_start.npz",
        H=H_s,
        g=g_s,
        names=names,
        cw=fs.cw.numpy(),
        isat=isat,
        N_j=N_j,
    )
    say(f"H_s in {res['t_hess_s']:.0f} s, saved")
    dump()

    # ---- Newton step from x_s
    w, Q = np.linalg.eigh(H_s)
    res["H_s_eig_min"] = float(w.min())
    res["H_s_eig_max"] = float(w.max())
    res["H_s_n_neg"] = int((w < 0).sum())
    wa = np.abs(w)
    floor = wa.max() * 1e-15
    wa = np.maximum(wa, floor)
    d = -Q @ ((Q.T @ g_s) / wa)
    pred = -(g_s @ d + 0.5 * d @ H_s @ d)
    res["newton_pred_reduction"] = float(pred)
    res["newton_edm_s"] = float(0.5 * g_s @ (Q @ ((Q.T @ g_s) / wa)))
    res["newton_norm_d"] = float(np.linalg.norm(d))
    res["newton_norm_D"] = float(np.linalg.norm(D))
    res["newton_cos_d_D"] = float(d @ D / np.linalg.norm(d) / np.linalg.norm(D))
    res["newton_proj_d_on_D"] = float(d @ D / (D @ D))
    res["newton"] = {}
    for a in [0.25, 0.5, 1.0]:
        fs.x.assign(x_s + a * d)
        Lr = lg()[0]
        profile_scales()
        Lp = lg()[0]
        res["newton"][f"{a:g}"] = dict(
            raw=Lr,
            prof=Lp,
            quad_pred=float(L_s + a * g_s @ d + 0.5 * a * a * d @ H_s @ d),
        )
        say(
            f"Newton a={a:g}: raw {Lr:.4f}, scales re-profiled {Lp:.4f}, quadratic model {res['newton'][f'{a:g}']['quad_pred']:.4f}"
        )
        dump()
    np.savez(f"{OUT}/newton_start.npz", d=d, D=D)
    del Q

    # ---- H at x_e
    fs.x.assign(x_e)
    t = time.time()
    _, g, H = fs.loss_val_grad_hess()
    res["t_hess_e"] = time.time() - t
    H_e = H.numpy()
    del H, g
    H_e = 0.5 * (H_e + H_e.T)
    np.savez(
        f"{OUT}/hess_end.npz",
        H=H_e,
        g=g_e,
        names=names,
        cw=fs.cw.numpy(),
        isat=isat,
        N_j=N_j,
    )
    say(f"H_e in {res['t_hess_e']:.0f} s, saved")
    dump()

    # ---- N2: exact Newton from a point near the end of the valley: theta = x_s + 0.9 D, scales profiled.
    # Tests whether the slow tail is a Krylov-inexactness problem (one exact Newton step lands on x_e) or a
    # nonlinearity problem (it does not).
    fs.x.assign(x_s + 0.9 * D)
    x_p = profile_scales()
    L_p, g_p = lg()
    t = time.time()
    _, g, H = fs.loss_val_grad_hess()
    res["t_hess_p"] = time.time() - t
    H_p = 0.5 * (H.numpy() + H.numpy().T)
    del H, g
    w, Q = np.linalg.eigh(H_p)
    wa = np.maximum(np.abs(w), np.abs(w).max() * 1e-15)
    dp = -Q @ ((Q.T @ g_p) / wa)
    res["N2"] = dict(
        L_p=L_p,
        L_p_minus_final=L_p - L_e,
        n_neg=int((w < 0).sum()),
        edm_p=float(0.5 * g_p @ (Q @ ((Q.T @ g_p) / wa))),
        dist_p_to_e=float(np.linalg.norm(x_p - x_e)),
        steps={},
    )
    for a in [0.5, 1.0]:
        fs.x.assign(x_p + a * dp)
        Lr = lg()[0]
        profile_scales()
        Lq = lg()[0]
        res["N2"]["steps"][f"{a:g}"] = dict(
            raw_minus_final=Lr - L_e,
            prof_minus_final=Lq - L_e,
            dist_to_e=float(np.linalg.norm(x_p + a * dp - x_e)),
        )
        say(
            f"N2 a={a:g}: loss - final raw {Lr - L_e:+.4e}, re-profiled {Lq - L_e:+.4e}; start {L_p - L_e:+.4e}"
        )
        dump()
    del Q
    res["t_total_s"] = time.time() - t0
    dump()
    say("done")


if __name__ == "__main__":
    main()
