#!/usr/bin/env python3
"""ONE gated cache load, no minimisation: at LATB8's minimum (data, blinding ARMED), with the fitter built from
LATB8's own command (cmds/NCHKF.cmd == LATB8's meta_info command):

R  replay: total loss with the current code (live term, syst=Jnf+Jbt) - LATB8's stored nllvalreduced (~0: pert=live
   unchanged in the full fitter, same SCETlib build).
F  the frozen term inside the fitter: (1) its gradient in x is nonzero ONLY at lambda2_nu / lambda4_nu (exactly 0 at
   alphaS and every TNP); (2) armed vs disarmed blinding: its value is bitwise identical (it cannot see alpha_s);
   (3) AD vs FD in lambda2_nu, lambda4_nu; (4) kernel snapshot status (1 = bitwise the loaded rules').
N  Newton step from LATB8 with its lattice term (live, Jnf+Jbt) swapped for each variant, using LATB8's covariance and
   the exact term gradients / Hessians AT the blinded point. Printed: Delta alphaS in sigma_NOM (vs LATB8 and vs
   NOMSTIFF, both at the point; no Delta alpha_s = 0 frame is computed), sigma ratios, the (public) CS lambdas, TNP
   shifts, and -- for frozen variants only, whose value depends on public lambdas alone -- the lattice Delta chi2 at
   LATB8's point and at the Newton point.
Never printed: an alpha_s value, a live chi2 / k1 / residual / term value.
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
L8 = f"{A}/261007_lattice_term_native/fitresults_LATB8.hdf5"
NOM = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
DROP = {"--snapshotFile", "--snapshotInterval", "-o", "--outpath", "--externalPostfit"}
NEW = (
    "wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTerm",
    "wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping",
)
FRZ = ["pert=frozen", "alphas_frozen=0.1168"]
VARIANTS = {
    "live Jnf (LATB8 minus b_T window)": ["syst=Jnf"],
    "frozen none (stat only)": ["syst=none", *FRZ],
    "frozen V1 (Jnf, nfmatch 1)": ["syst=Jnf", *FRZ, "nfmatch=1.0"],
    "frozen V2 (Jnf, nfswitch 1, nfmatch m_b)": [
        "syst=Jnf",
        *FRZ,
        "nfmatch=4.18",
        "nfswitch=1.0",
    ],
    "frozen V3 (Jnf, full n_f=4, nfmatch m_b)": [
        "syst=Jnf",
        *FRZ,
        "nfmatch=4.18",
        "nfscheme=full",
    ],
    "frozen V3lit (Jnf, nfmatch m_b)": ["syst=Jnf", *FRZ, "nfmatch=4.18"],
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
    toks = shlex.split(open(f"{TASK}/cmds/NCHKF.cmd").read())
    argv, i = [], 1
    while i < len(toks):
        if toks[i] in DROP:
            i += 2
            continue
        argv.append(toks[i])
        i += 1
    args = rabbit_fit.make_parser().parse_args(argv + ["-o", "/tmp"])
    wlogging.setup_logger("nchk_froz", args.verbose, args.noColorLogger)
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
    old = [r for r in f.regularizers if type(r).__name__ == "LatticeCSTerm"][0]
    f.defaultassign()
    f.set_nobs(f.indata.data_obs)
    f.set_blinding_offsets(blind=True)
    f.load_fitresult(L8, None, profile=True)
    print(f"[nchkf] blinding enabled = {f.blinding.enabled}", flush=True)
    names = [str(n) for n in np.asarray(f.parms).astype(str)]
    ib = [names.index(n) for n in BLOCK]
    f.arm_regularizers()
    stored = float(io_tools.get_fitresult(L8, None)["nllvalreduced"])
    L_now = float(f._compute_loss(profile=True))
    out["R_loss_minus_stored"] = L_now - stored
    print(
        f"[nchkf R] loss(current code, LATB8 command) - LATB8 stored nllvalreduced = {L_now - stored:+.3e} "
        "(must be ~0)",
        flush=True,
    )

    terms = {
        k: rh.load_regularizer(
            NEW[0],
            mh.load_mapping(NEW[1], indata, *v, "offset=min"),
            dtype=indata.dtype,
        )
        for k, v in VARIANTS.items()
    }
    xb = f.x.numpy().copy()

    # ---- F: the frozen term inside the fitter
    fz = terms["frozen V1 (Jnf, nfmatch 1)"]
    f.regularizers = [wall, fz]
    f.arm_regularizers()
    with tf.GradientTape() as t:
        c = fz.chi2_tf(f.get_x())
    g = t.gradient(c, f.x).numpy()
    nz = [names[k] for k in np.flatnonzero(g)]
    out["F1_nonzero_gradient_entries"] = nz
    out["F1_zero_at"] = {
        n: bool(g[names.index(n)] == 0.0)
        for n in ("alphaS", "resumTNP_gamma_nu", "resumTNP_gamma_cusp")
    }
    print(
        f"[nchkf F1] frozen term: nonzero gradient entries {nz} (must be lambda2_nu, lambda4_nu only); exactly 0 at "
        f"{out['F1_zero_at']}",
        flush=True,
    )
    v_armed = float(fz.chi2_tf(f.get_x()))
    f.set_blinding_offsets(blind=False)
    v_dis = float(fz.chi2_tf(f.get_x()))
    f.set_blinding_offsets(blind=True)
    out["F2_armed_equals_disarmed"] = bool(v_armed == v_dis)
    print(
        f"[nchkf F2] frozen term armed == disarmed (bitwise): {out['F2_armed_equals_disarmed']}",
        flush=True,
    )
    rel = {}
    for n in ("lambda2_nu", "lambda4_nu"):
        k = names.index(n)
        h = 1e-4 if n == "lambda2_nu" else 1e-6
        vals = []
        for s in (+1, -1):
            xx = xb.copy()
            xx[k] += s * h
            f.x.assign(xx)
            vals.append(float(fz.chi2_tf(f.get_x())))
        f.x.assign(xb)
        fd = (vals[0] - vals[1]) / (2 * h)
        rel[n] = abs(g[k] - fd) / max(abs(fd), 1e-300)
    out["F3_rel_AD_vs_FD"] = rel
    print(
        "[nchkf F3] frozen d chi2 / d x, |AD - FD| / |FD|: "
        + ", ".join(f"{k} {v:.1e}" for k, v in rel.items()),
        flush=True,
    )
    out["F4_snapshot_status"] = int(fz.core.gz.snapshot_status)
    print(
        f"[nchkf F4] kernel snapshot status = {out['F4_snapshot_status']}", flush=True
    )

    # ---- N: Newton from LATB8, at the blinded point
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
    s8 = float(np.sqrt(C8[names.index("alphaS"), names.index("alphaS")]))

    def block_gh(reg):
        with tf.GradientTape() as t:
            c = reg.chi2_tf(f.get_x())
        gg = 0.5 * t.gradient(c, f.x).numpy()
        Hb = np.zeros((len(ib), len(ib)))
        for a, k in enumerate(ib):
            e = np.zeros(len(xb))
            e[k] = 1.0
            with tf.autodiff.ForwardAccumulator(f.x, tf.constant(e)) as acc:
                with tf.GradientTape() as t:
                    c = reg.chi2_tf(f.get_x())
                gk = t.gradient(c, f.x)
            Hb[a] = 0.5 * acc.jvp(gk).numpy()[ib]
        return gg, 0.5 * (Hb + Hb.T)

    f.regularizers = [wall, old]
    f.arm_regularizers()
    g_old, H_old = block_gh(old)
    out["N"] = {}
    out["sigma_LATB8_over_sigNOM"] = s8 / sN
    out["LATB8_vs_NOMSTIFF_over_sigNOM"] = (x8 - xN) / sN
    for k, reg in terms.items():
        f.regularizers = [wall, reg]
        f.arm_regularizers()
        g_v, H_v = block_gh(reg)
        H = H8.copy()
        H[np.ix_(ib, ib)] += H_v - H_old
        dx = -np.linalg.solve(H, g_v - g_old)
        Cn = np.linalg.inv(H)
        ia = names.index("alphaS")
        row = dict(
            args=VARIANTS[k],
            dalphaS_vs_LATB8_over_sigNOM=float(dx[ia] / sN),
            dalphaS_vs_NOMSTIFF_over_sigNOM=float((x8 + dx[ia] - xN) / sN),
            sigma_ratio_vs_NOM=float(np.sqrt(Cn[ia, ia]) / sN),
            sigma_ratio_vs_LATB8=float(np.sqrt(Cn[ia, ia]) / s8),
            load_time=reg.core.summary(),
        )
        for n, (c0, c1) in PHYS.items():
            j = names.index(n)
            th8 = float(np.asarray(fr["parms"].get().values())[j])
            row[n] = c0 + c1 * (th8 + dx[j])
            row[f"d_{n}_over_sigma"] = float(dx[j] / np.sqrt(Cn[j, j]))
            row[f"sigma_{n}"] = float(c1 * np.sqrt(Cn[j, j]))
        for n in ("resumTNP_gamma_nu", "resumTNP_gamma_cusp"):
            row[f"d_{n}"] = float(dx[names.index(n)])
        if reg.pert == "frozen":  # alpha_s-independent: publishable
            row["dchi2lat_at_LATB8"] = float(reg.chi2_tf(f.get_x())) - reg.offset
            f.x.assign(xb + dx)
            row["dchi2lat_at_newton"] = float(reg.chi2_tf(f.get_x())) - reg.offset
            f.x.assign(xb)
        out["N"][k] = row
        print(
            f"[nchkf N] {k:42s}: dalphaS vs LATB8 {row['dalphaS_vs_LATB8_over_sigNOM']:+.4f} sigma_NOM, vs NOMSTIFF "
            f"{row['dalphaS_vs_NOMSTIFF_over_sigNOM']:+.4f}, sigma ratio vs NOM {row['sigma_ratio_vs_NOM']:.4f} "
            f"(vs LATB8 {row['sigma_ratio_vs_LATB8']:.4f}), lambda2_nu {row['lambda2_nu']:.4f} +- "
            f"{row['sigma_lambda2_nu']:.4f} ({row['d_lambda2_nu_over_sigma']:+.2f} sigma), lambda4_nu "
            f"{row['lambda4_nu']:.5f} +- {row['sigma_lambda4_nu']:.5f} ({row['d_lambda4_nu_over_sigma']:+.2f} sigma), "
            f"dTNP_nu {row['d_resumTNP_gamma_nu']:+.3f}, dTNP_cusp {row['d_resumTNP_gamma_cusp']:+.3f}"
            + (
                f", Dchi2_lat at LATB8 {row['dchi2lat_at_LATB8']:.3f} -> Newton {row['dchi2lat_at_newton']:.3f}"
                if "dchi2lat_at_LATB8" in row
                else ""
            ),
            flush=True,
        )
    json.dump(out, open(f"{TASK}/nchk_froz.json", "w"), indent=1, default=float)
    print("[nchkf] done", flush=True)


if __name__ == "__main__":
    main()
