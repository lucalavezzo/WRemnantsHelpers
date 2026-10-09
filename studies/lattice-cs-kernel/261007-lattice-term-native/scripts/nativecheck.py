#!/usr/bin/env python3
"""ONE gated cache load, no minimisation: replay (V5), blinding (V6) and the at-the-point Newton step (V8 prediction)
for the native lattice term, on DATA with blinding ARMED, at LATFULL8's vector.

The fitter is built from cmds/NCHK.cmd (= LATFULL8's command: wall + the OLD table term) exactly as rabbit_fit builds
it, with the gamma-nu-points SCETlib build. Printed: ONLY differences, booleans, parameter names, public load-time
numbers, and Newton shifts in units of sigma_NOM (never an alpha_s value, a live chi2, k1, residual or term value).

V5  a. total loss (new build, old term) - LATFULL8's stored nllvalreduced            (== 0: the new SCETlib build
       replays the cache exactly; the old term does not touch SCETlib)
    b. data+BB+constraint part with the new term - with the old term                   (== 0 bitwise)
    c. Delta NLL total (new term - old term) at LATFULL8's point                       (a total-NLL difference)
V6  A. p_full seen by the term - p_full the param model builds from (get_poi, get_model_nui)  (== 0, every entry)
    B. armed: the term's alpha_s differs from the same map applied to the blinded internal x (bool); disarmed: equal
    C. d term / d x: autodiff vs central FD (alphaS, lambda2_nu, lambda4_nu, both CS TNPs), relative only
    D. the term's gradient is exactly 0 outside those five parameters (names of nonzero entries printed)
    E. kernel snapshot status (1 = bitwise the loaded rules')
V8  Newton step from LATFULL8 with the old term swapped for each new-term variant, using LATFULL8's covariance and the
    exact term gradients / Hessians AT the blinded point (no Delta alpha_s = 0 approximation): shifts in sigma_NOM.
"""
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
from rabbit import inputdata, io_tools  # noqa: E402
from rabbit.mappings import helpers as mh  # noqa: E402
from rabbit.param_models import helpers as ph  # noqa: E402
from rabbit.regularization import helpers as rh  # noqa: E402
from wums import logging as wlogging  # noqa: E402

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
L8 = f"{A}/261006_lattice_chi2_in_fit/fitresults_LATFULL8.hdf5"
NOM = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
DROP = {"--snapshotFile", "--snapshotInterval", "-o", "--outpath", "--externalPostfit"}
NEW = (
    "wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTerm",
    "wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping",
)
VARIANTS = {
    "new Jnf+Jbt (default)": ["syst=Jnf+Jbt"],
    "new Jnf (no b_T window)": ["syst=Jnf"],
    "new Jbt (no n_f syst)": ["syst=Jbt"],
    "new none (stat only)": ["syst=none"],
    "new direct_nf+Jbt": ["syst=direct_nf+Jbt"],
}
BLOCK = (
    "alphaS",
    "lambda2_nu",
    "lambda4_nu",
    "resumTNP_gamma_nu",
    "resumTNP_gamma_cusp",
)
PHYS = dict(
    lambda2_nu=(0.15, 0.1), lambda4_nu=(0.0, 0.5)
)  # public REPARAM maps (anchor + width * theta)


def main():
    out = {}
    toks = shlex.split(open(f"{TASK}/cmds/NCHK.cmd").read())
    argv, i = [], 1
    while i < len(toks):
        if toks[i] in DROP:
            i += 2
            continue
        argv.append(toks[i])
        i += 1
    args = rabbit_fit.make_parser().parse_args(argv + ["-o", "/tmp"])
    wlogging.setup_logger("nativecheck", args.verbose, args.noColorLogger)
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
    wall = [r for r in f.regularizers if type(r).__name__ == "NPDampingWall"][0]
    old = [r for r in f.regularizers if type(r).__name__ == "LatticeCSChi2"][0]
    f.defaultassign()
    f.set_nobs(f.indata.data_obs)
    f.set_blinding_offsets(blind=True)
    f.load_fitresult(L8, None, profile=True)
    print(f"[nchk] blinding enabled = {f.blinding.enabled}", flush=True)
    names = [str(n) for n in np.asarray(f.parms).astype(str)]
    ib = [names.index(n) for n in BLOCK]

    def comps():
        ln, lc, lbeta, lpen, _ = f._compute_nll_components(profile=True)
        d = float(ln + lc + (lbeta if lbeta is not None else 0.0))
        return d, float(f._compute_loss(profile=True))

    stored = float(io_tools.get_fitresult(L8, None)["nllvalreduced"])
    d_old, L_old = comps()
    out["V5a_loss_newbuild_oldterm_minus_stored"] = L_old - stored
    print(
        f"[nchk V5a] loss(new SCETlib build, old term) - LATFULL8 stored nllvalreduced = {L_old - stored:+.3e} "
        "(must be ~0)",
        flush=True,
    )

    def make_new(extra):
        reg = rh.load_regularizer(
            NEW[0],
            mh.load_mapping(NEW[1], indata, *extra, "offset=min"),
            dtype=indata.dtype,
        )
        return reg

    terms = {k: make_new(v) for k, v in VARIANTS.items()}
    new = terms["new Jnf+Jbt (default)"]
    f.regularizers = [wall, new]
    f.arm_regularizers()
    d_new, L_new = comps()
    out["V5b_data_part_new_minus_old"] = d_new - d_old
    out["V5c_dNLL_total_new_minus_old"] = L_new - L_old
    print(
        f"[nchk V5b] data+BB+constraints (new term config) - (old term config) = {d_new - d_old:+.3e} (must be 0)",
        flush=True,
    )
    print(
        f"[nchk V5c] Delta NLL total (new term - old term) at LATFULL8's point = {L_new - L_old:+.6f}",
        flush=True,
    )

    # ---- V6 blinding
    npm = int(pm.nparams)
    pt = new.p_full_tf(f.get_x()).numpy()
    pmod = pm.scetlib_full_vector_tf(
        tf.concat([f.get_poi(), f.get_model_nui()], axis=0)
    ).numpy()
    out["V6A_max_abs_pfull_term_minus_model"] = float(np.max(np.abs(pt - pmod)))
    print(
        f"[nchk V6A] max |p_full(term) - p_full(param model)| over all {len(pt)} SCETlib entries = "
        f"{out['V6A_max_abs_pfull_term_minus_model']:.3e} (must be 0)",
        flush=True,
    )
    ias = pm.scetlib_names.index("alphas")
    raw = pm.scetlib_full_vector_tf(f.x[:npm]).numpy()
    out["V6B_armed_differs_from_raw_x"] = bool(abs(pt[ias] - raw[ias]) > 0)
    print(
        f"[nchk V6B] armed: term alpha_s differs from the map on the blinded internal x: "
        f"{out['V6B_armed_differs_from_raw_x']}",
        flush=True,
    )
    xb = f.x.numpy().copy()

    def term_grad(reg):
        with tf.GradientTape() as t:
            c = reg.chi2_tf(f.get_x())
        return t.gradient(c, f.x).numpy()

    g = term_grad(new)
    rel = {}
    for n in BLOCK:
        k = names.index(n)
        h = 1e-4
        vals = []
        for s in (+1, -1):
            xx = xb.copy()
            xx[k] += s * h
            f.x.assign(xx)
            vals.append(float(new.chi2_tf(f.get_x())))
        f.x.assign(xb)
        fd = (vals[0] - vals[1]) / (2 * h)
        rel[n] = abs(g[k] - fd) / max(abs(fd), 1e-300)
    out["V6C_rel_AD_vs_FD"] = rel
    print(
        "[nchk V6C] d chi2_lat / d x, |AD - FD| / |FD|: "
        + ", ".join(f"{k} {v:.1e}" for k, v in rel.items()),
        flush=True,
    )
    nz = [names[k] for k in np.flatnonzero(g) if names[k] not in BLOCK]
    out["V6D_nonzero_outside_block"] = nz
    print(
        f"[nchk V6D] nonzero gradient entries outside {BLOCK}: {nz} (must be [])",
        flush=True,
    )
    out["V6E_snapshot_status"] = int(new.core.gz.snapshot_status)
    print(
        f"[nchk V6E] kernel snapshot status = {out['V6E_snapshot_status']} (1 = bitwise the loaded rules')",
        flush=True,
    )

    # ---- V8: Newton from LATFULL8 with the old term swapped for each variant, at the (blinded) point itself
    fr = io_tools.get_fitresult(L8, None)
    C8 = np.asarray(fr["cov"].get().values(), float)
    H8 = np.linalg.inv(C8)
    frN = io_tools.get_fitresult(NOM, None)
    hN = frN["parms"].get()
    nN = [str(n) for n in hN.axes[0]]
    sN = float(
        np.sqrt(
            np.asarray(frN["cov"].get().values())[
                nN.index("alphaS"), nN.index("alphaS")
            ]
        )
    )
    xN = float(np.asarray(hN.values())[nN.index("alphaS")])
    x8 = float(np.asarray(fr["parms"].get().values())[names.index("alphaS")])

    def block_gh(reg, chi2_fn):
        """gradient (full) and the BLOCK x BLOCK Hessian of 1/2 chi2 (the NLL contribution, tau compensated)."""
        with tf.GradientTape() as t:
            c = chi2_fn(f.get_x())
        gg = 0.5 * t.gradient(c, f.x).numpy()
        Hb = np.zeros((len(ib), len(ib)))
        for a, k in enumerate(ib):
            e = np.zeros(len(xb))
            e[k] = 1.0
            with tf.autodiff.ForwardAccumulator(f.x, tf.constant(e)) as acc:
                with tf.GradientTape() as t:
                    c = chi2_fn(f.get_x())
                gk = t.gradient(c, f.x)
            Hb[a] = 0.5 * acc.jvp(gk).numpy()[ib]
        return gg, 0.5 * (Hb + Hb.T)

    g_old, H_old = block_gh(old, old.chi2_tf)
    out["V8"] = {}
    # K: the kernel swap alone -- SCETlib's (analytic-RGE, exact) gamma_zeta at p_full, with the OLD term's own
    # covariance (old Jnf + Jbt rows) and data: isolates analytic-vs-exact RGE (+ the table's expansion) from the
    # covariance change (n_f definition, rows recomputed on SCETlib's kernel).
    M_old = tf.constant(old.core.M, dtype=tf.float64)
    y_old = tf.constant(old.core.y, dtype=tf.float64)

    def chi2_K(params):
        r = 0.5 * new._gz(new.p_full_tf(params)) - y_old
        return tf.tensordot(r, tf.linalg.matvec(M_old, r), 1)

    todo = dict(terms)
    todo["K kernel swap only (old cov)"] = None
    for k, reg in todo.items():
        if reg is None:
            f.regularizers = [wall, new]
            f.arm_regularizers()
            g_v, H_v = block_gh(new, chi2_K)
        else:
            f.regularizers = [wall, reg]
            f.arm_regularizers()
            g_v, H_v = block_gh(reg, reg.chi2_tf)
        H = H8.copy()
        H[np.ix_(ib, ib)] += H_v - H_old
        dg = g_v - g_old
        dx = -np.linalg.solve(H, dg)
        Cn = np.linalg.inv(H)
        ia = names.index("alphaS")
        row = dict(
            dalphaS_vs_LATFULL8_over_sigNOM=float(dx[ia] / sN),
            dalphaS_vs_NOMSTIFF_over_sigNOM=float((x8 + dx[ia] - xN) / sN),
            sigma_ratio_vs_NOM=float(np.sqrt(Cn[ia, ia]) / sN),
            load_time=(reg or new).core.summary(),
        )
        for n, (c0, c1) in PHYS.items():
            j = names.index(n)
            th8 = float(np.asarray(fr["parms"].get().values())[j])
            row[n] = c0 + c1 * (th8 + dx[j])
            row[f"d_{n}_over_sigma"] = float(dx[j] / np.sqrt(Cn[j, j]))
            row[f"sigma_{n}"] = float(c1 * np.sqrt(Cn[j, j]))
        for n in ("resumTNP_gamma_nu", "resumTNP_gamma_cusp"):
            j = names.index(n)
            row[f"d_{n}"] = float(dx[j])
        out["V8"][k] = row
        print(
            f"[nchk V8] {k:26s}: dalphaS vs LATFULL8 {row['dalphaS_vs_LATFULL8_over_sigNOM']:+.4f} sigma_NOM, vs "
            f"NOMSTIFF {row['dalphaS_vs_NOMSTIFF_over_sigNOM']:+.4f}, sigma ratio {row['sigma_ratio_vs_NOM']:.4f}, "
            f"lambda2_nu {row['lambda2_nu']:.4f} ({row['d_lambda2_nu_over_sigma']:+.2f} sigma), lambda4_nu "
            f"{row['lambda4_nu']:.5f} ({row['d_lambda4_nu_over_sigma']:+.2f} sigma), dTNP_nu "
            f"{row['d_resumTNP_gamma_nu']:+.3f}, dTNP_cusp {row['d_resumTNP_gamma_cusp']:+.3f}",
            flush=True,
        )
    f.set_blinding_offsets(blind=False)
    pt2 = new.p_full_tf(f.get_x()).numpy()
    raw2 = pm.scetlib_full_vector_tf(f.x[:npm]).numpy()
    out["V6B_disarmed_equal"] = bool(pt2[ias] == raw2[ias])
    print(
        f"[nchk V6B'] disarmed: term alpha_s == map on x: {out['V6B_disarmed_equal']}",
        flush=True,
    )
    json.dump(
        out,
        open(f"{TASK}/{os.environ.get('NCHK_OUT', 'nativecheck.json')}", "w"),
        indent=1,
        default=float,
    )
    print("[nchk] done", flush=True)


if __name__ == "__main__":
    main()
