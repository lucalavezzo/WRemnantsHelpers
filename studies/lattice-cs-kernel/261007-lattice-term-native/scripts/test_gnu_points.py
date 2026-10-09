"""V1-V3 for the SCETlib entry point DrellYan.gamma_nu_points (scetlib-cms branch gamma-nu-points).

Run in the container against the branch build:
  agent_setup.sh --scetlib /work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build -- \
      python3 <this> [--cache <small cache.npz>] [--neig 29]

V1  value vs SCETlib's qT::Gamma_nu CLASS (analytic RGE, cache.conf settings) at the 21 ASWZ points, at the anchor and at
    displaced points (alpha_s +-0.004, TNPs +-2, lambda4_nu < 0)                 target <= 1e-12 (gamma_zeta units)
    value vs the 261007-lattice-term-design prototype output (12 printed digits)  target <= 1e-11
    value vs the OLD shipped table (exact RGE)                                     expect <= 1.9e-3
    class (EXACT RGE) vs the old table                                             expect ~1e-12
V2  snapshot status (0 without rules; 1 with a loaded cache), and value_pert == class with NP off
V3  clad gradient vs Richardson FD of the entry point; Hessian vs FD of the clad gradient; TNP-TNP block exactly 0;
    Jacobian exactly 0 outside {alphas, tnp_gamma_cusp, tnp_gamma_nu, np_gnu_*}
"""

import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
STUDY = os.path.dirname(TASK)
WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
CONF = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/ad_scetlib_caches/pdf62_y35_260921_y25/cache.conf"
INPUTS = os.path.join(
    WREM, "wremnants/postprocessing/scetlib_ad/data/lattice_aswz_inputs.npz"
)
CLASSDRV = os.path.join(TASK, "classdrv", "gz_class")
PROTO = os.path.join(STUDY, "261007-lattice-term-design", "proto")
MU = 2.0

ap = argparse.ArgumentParser()
ap.add_argument(
    "--cache",
    default=None,
    help="small cache.npz to test the bitwise snapshot check (status 1)",
)
ap.add_argument(
    "--neig", type=int, default=0, help="register this many pdf_eig params (P bucket)"
)
ap.add_argument("--out", default=os.path.join(TASK, "test_gnu_points.json"))
args = ap.parse_args()

sys.path.insert(0, WREM)
from wremnants.postprocessing.scetlib_ad import xsec_backend as xb  # noqa: E402

D = np.load(INPUTS)
b_fm = np.array(D["b_fm"], float)
FM = float(D["fm_to_gevinv"])
bT = b_fm * FM

t0 = time.time()
conf_path = args.cache.replace("cache.npz", "cache.conf") if args.cache else CONF
conf, sigma = xb.configure(conf_path, threads=8, diff_scales=True, fo_resolve_muR=True)
sing, nons = sigma.sub_pieces()
if args.neig:
    sing.set_pdf_eig_params(args.neig)
    nons.set_pdf_eig_params(args.neig)
names = list(sing.gradient_param_names())
P = len(names)
p0 = np.array(sing.gradient_central(), float)
print(
    f"configured in {time.time() - t0:.1f}s; P = {P}; scetlib_qT from {xb._import_scetlib.__module__}"
)
import scetlib_qT  # noqa: E402

print("scetlib_qT:", scetlib_qT.__file__)
res = {"P": P, "names": names, "scetlib_qT": scetlib_qT.__file__, "conf": conf_path}

ix = {n: names.index(n) for n in names}
I_AS, I_C, I_N = ix["alphas"], ix["tnp_gamma_cusp"], ix["tnp_gamma_nu"]
I_LINF, I_L2, I_L4 = ix["np_gnu_lambda_inf"], ix["np_gnu_lambda2"], ix["np_gnu_lambda4"]
ALLOWED = {
    i
    for n, i in ix.items()
    if n in ("alphas", "tnp_gamma_cusp", "tnp_gamma_nu") or n.startswith("np_gnu_")
}


def point(alphas=None, tc=0.0, tn=0.0, l2=None, l4=None, linf=None):
    p = p0.copy()
    if alphas is not None:
        p[I_AS] = alphas
    p[I_C], p[I_N] = tc, tn
    if l2 is not None:
        p[I_L2] = l2
    if l4 is not None:
        p[I_L4] = l4
    if linf is not None:
        p[I_LINF] = linf
    return p


def gnu(p, order=2):
    r = sing.gamma_nu_points(bT, MU, p, order)
    return {k: np.asarray(v) for k, v in r.items()}


def classref(p, exact=False):
    cmd = [
        CLASSDRV,
        *[repr(float(p[i])) for i in (I_AS, I_C, I_N, I_LINF, I_L2, I_L4)],
        "1" if exact else "0",
        repr(MU),
    ] + [repr(float(b)) for b in b_fm]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.split(
        "\n"
    )
    a = np.array([[float(x) for x in ln.split()[1:]] for ln in out if ln.strip()])
    return a[:, 0], a[:, 1]  # gamma_zeta full, pert


checks = []


def check(name, val, tol):
    ok = bool(val <= tol)
    checks.append(dict(name=name, value=float(val), tol=tol, ok=ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {val:.3e} (tol {tol:g})")


status0 = sing.gamma_nu_snapshot_status()
res["snapshot_status_live"] = int(status0)
print("snapshot status (live, before any cache):", status0)

POINTS = {
    "anchor": point(),
    "displaced_design": point(alphas=0.120, tc=1.0, tn=-1.0, l2=0.05, l4=0.008),
    "as_plus": point(alphas=0.122, tc=2.0, tn=2.0, l2=0.03, l4=0.007),
    "as_minus_l4neg": point(alphas=0.114, tc=-2.0, tn=-2.0, l2=0.18, l4=-0.006),
}
res["V1"] = {}
for nm, p in POINTS.items():
    r = gnu(p)
    full, pert = classref(p)
    d_full = np.max(np.abs(0.5 * r["value"] - full))
    d_pert = np.max(np.abs(0.5 * r["value_pert"] - pert))
    check(f"V1 {nm}: gamma_nu_points vs Gamma_nu class (analytic), full", d_full, 1e-12)
    check(f"V1 {nm}: value_pert vs class with NP off", d_pert, 1e-12)
    res["V1"][nm] = dict(
        zeta=list(0.5 * r["value"]),
        zeta_pert=list(0.5 * r["value_pert"]),
        class_full=list(full),
        max_full=d_full,
        max_pert=d_pert,
    )

# prototype outputs (12 printed digits, gamma_zeta units): columns b, class_analytic, kernel, class_exact, kernel_pert
for nm, fn, p in (
    ("anchor", "out_anchor.txt", POINTS["anchor"]),
    ("displaced", "out_displaced.txt", POINTS["displaced_design"]),
):
    rows = [
        ln.split()
        for ln in open(os.path.join(PROTO, fn))
        if ln.strip() and not ln.startswith("#")
    ]
    pb = np.array([float(x[0]) for x in rows])
    pk = np.array([float(x[2]) for x in rows])
    pg = np.array(
        [[float(v) for v in x[5:11]] for x in rows]
    )  # clad grad, gamma_zeta units, 6 params
    r = gnu(p)
    zeta = 0.5 * r["value"]
    m = [int(np.argmin(np.abs(b_fm - b))) for b in pb]
    check(
        f"V1 {nm}: vs prototype kernel (12 digits printed)",
        np.max(np.abs(zeta[m] - pk)),
        1e-11,
    )
    cols = [I_AS, I_C, I_N, I_LINF, I_L2, I_L4]
    g = 0.5 * r["grad"][m][:, cols]
    check(
        f"V1 {nm}: clad grad vs prototype clad grad (rel, 10 digits printed)",
        np.max(np.abs(g - pg) / np.maximum(1e-10, np.abs(pg))),
        1e-9,
    )

# old table: exact RGE
r = gnu(POINTS["anchor"])
pert_old = np.array(D["pert"], float)
full_ex, pert_ex = classref(POINTS["anchor"], exact=True)
diff_tab = 0.5 * r["value_pert"] - pert_old
sig = np.sqrt(np.diag(D["cov_stat"]))
res["V1"]["vs_old_table"] = dict(
    diff=list(diff_tab),
    min=float(diff_tab.min()),
    max=float(diff_tab.max()),
    max_over_sigma=float(np.max(np.abs(diff_tab) / sig)),
)
check(
    "V1 new pert (analytic) vs OLD table (exact): max|diff| (expect <= 1.9e-3)",
    np.max(np.abs(diff_tab)),
    2e-3,
)
check(
    "V1 class EXACT RGE vs OLD table (expect ~1e-12)",
    np.max(np.abs(pert_ex - pert_old)),
    1e-10,
)
print(
    f"     new - old table: {diff_tab.min():+.3e} .. {diff_tab.max():+.3e}; max |d|/sigma_lat = "
    f"{np.max(np.abs(diff_tab) / sig):.4f}"
)
# alpha_s slope vs table
das = 0.5 * r["grad"][:, I_AS]
res["V1"]["dzeta_dalphas_new"] = list(das)
res["V1"]["dzeta_dalphas_table"] = list(np.array(D["dpert_dalphas"], float))

# V3 derivatives
res["V3"] = {}
for nm, p in POINTS.items():
    r = gnu(p)
    G, H = r["grad"], r["hess"]
    # Jacobian zero outside the allowed set
    other = [i for i in range(P) if i not in ALLOWED]
    check(
        f"V3 {nm}: |grad| outside alphas/CS-TNPs/np_gnu (must be exactly 0)",
        np.max(np.abs(G[:, other])),
        0.0,
    )
    check(
        f"V3 {nm}: |hess| outside alphas/CS-TNPs/np_gnu (must be exactly 0)",
        max(np.max(np.abs(H[:, other, :])), np.max(np.abs(H[:, :, other]))),
        0.0,
    )
    check(
        f"V3 {nm}: TNP-TNP Hessian block (exactly affine -> 0)",
        np.max(np.abs(H[:, [I_C, I_N]][:, :, [I_C, I_N]])),
        0.0,
    )
    # Richardson FD of the value
    worst_g, worst_h = 0.0, 0.0
    for i in sorted(ALLOWED):
        if names[i] == "np_gnu_b0_bmax":
            h = 1e-4
        else:
            h = {
                I_AS: 2e-5,
                I_C: 0.2,
                I_N: 0.2,
                I_LINF: 1e-4,
                I_L2: 1e-4,
                I_L4: 2e-5,
            }.get(i, 1e-4)

        def fd(hh, order=0):
            q1, q2 = p.copy(), p.copy()
            q1[i] += hh
            q2[i] -= hh
            if order == 0:
                return (gnu(q1, 0)["value"] - gnu(q2, 0)["value"]) / (2 * hh)
            return (gnu(q1, 1)["grad"] - gnu(q2, 1)["grad"]) / (2 * hh)

        f1, f2 = fd(h), fd(h / 2)
        rich = (4 * f2 - f1) / 3
        scale = np.maximum(np.abs(rich), 1e-3 * np.max(np.abs(rich)) + 1e-12)
        worst_g = max(worst_g, float(np.max(np.abs(G[:, i] - rich) / scale)))
        g1, g2 = fd(h, 1), fd(h / 2, 1)
        grich = (4 * g2 - g1) / 3
        sc2 = np.maximum(np.abs(grich), 1e-3 * np.max(np.abs(grich)) + 1e-12)
        worst_h = max(worst_h, float(np.max(np.abs(H[:, i, :] - grich) / sc2)))
    check(f"V3 {nm}: clad grad vs Richardson FD (rel)", worst_g, 1e-8)
    check(f"V3 {nm}: clad Hessian vs Richardson FD of clad grad (rel)", worst_h, 1e-7)
    check(
        f"V3 {nm}: Hessian symmetric",
        np.max(np.abs(H - np.transpose(H, (0, 2, 1)))),
        1e-14,
    )
    res["V3"][nm] = dict(grad_fd=worst_g, hess_fd=worst_h)

# timing
t = time.time()
for _ in range(20):
    gnu(POINTS["displaced_design"], 2)
res["time_per_call_order2_s"] = (time.time() - t) / 20
print(
    f"time per call (21 points, value+grad+hess, P={P}): {res['time_per_call_order2_s'] * 1e3:.2f} ms"
)

if args.cache:
    from scetlib_tf import ScetlibCachedXsecTF

    t = time.time()
    fn = ScetlibCachedXsecTF.load(args.cache, sing, nons)
    print(
        f"loaded {args.cache} in {time.time() - t:.1f}s; names match: {fn.param_names == names}"
    )
    # The snapshot was taken BEFORE the rules were loaded; a reset happens only on reconfiguration. Re-check by
    # forcing a fresh snapshot through a fresh calculation is what the fit does (load first, then the term).
    conf2, sigma2 = xb.configure(
        conf_path, threads=8, diff_scales=True, fo_resolve_muR=True
    )
    s2, n2 = sigma2.sub_pieces()
    if args.neig:
        s2.set_pdf_eig_params(args.neig)
        n2.set_pdf_eig_params(args.neig)
    fn2 = ScetlibCachedXsecTF.load(args.cache, s2, n2)
    st = s2.gamma_nu_snapshot_status()
    res["snapshot_status_with_rules"] = int(st)
    check(
        "V2 snapshot bitwise == first loaded rule's GlobalData (status 1)",
        0.0 if st == 1 else 1.0,
        0.0,
    )
    r1 = sing.gamma_nu_points(bT, MU, POINTS["displaced_design"], 2)
    r2 = s2.gamma_nu_points(bT, MU, POINTS["displaced_design"], 2)
    check(
        "V2 rules-checked snapshot gives bitwise the same value/grad/hess as the live one",
        max(
            float(np.max(np.abs(np.asarray(r1[k]) - np.asarray(r2[k]))))
            for k in ("value", "grad", "hess")
        ),
        0.0,
    )
    # replay is unaffected by interleaved gamma_nu_points calls
    pp = np.array(fn2.anchor, float)
    v_before = fn2.values_and_jacobian(pp)[0].copy()
    fn2._cache_key = None
    s2.gamma_nu_points(bT, MU, POINTS["as_plus"], 2)
    v_after = fn2.values_and_jacobian(pp)[0]
    check(
        "V2 rule replay bitwise unchanged after an interleaved gamma_nu_points call",
        float(np.max(np.abs(v_after - v_before))),
        0.0,
    )

res["checks"] = checks
res["n_fail"] = sum(not c["ok"] for c in checks)
json.dump(res, open(args.out, "w"), indent=1)
print(f"\n{len(checks) - res['n_fail']}/{len(checks)} PASS -> {args.out}")
