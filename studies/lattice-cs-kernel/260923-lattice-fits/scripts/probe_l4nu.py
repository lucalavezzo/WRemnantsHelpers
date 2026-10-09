"""Probe the PRODUCTION AD cache (pdf62_corrgrid_260827/merged_full, authval b66f8de)
for lambda4_nu in [-0.012, 0]: sigma and the AD Jacobian, all else at the anchor.

Why: on the Q-split cache (260923-qsplit-fisher) sigma(qT 0-1) went NEGATIVE at
lambda4_nu = -0.01 and fwd/bwd FDs disagreed by 20-100 % at the lattice point.
The lattice prefers lambda4_nu ~ -0.006, so before an UNWALLED lattice fit we must
know whether the production cache is sane there.

Two lines are scanned: lambda2_nu = 0.15 (anchor) and 0.184 (lattice mean).
Checks per point:
  * min sigma over the 770 gen bins, and any sigma <= 0
  * ratio sigma/sigma(lambda4_nu=0) vs the LINEAR prediction 1 + dl4 * J/sigma
    from the AD Jacobian at lambda4_nu = 0 (a smooth b^4 response should be
    near-linear over |dl4| <= 0.012; the Q-split cache was not)
  * AD d sigma / d lambda4_nu vs one-sided FDs (h = 1e-4) fwd and bwd, as a
    fraction of max|J| (the qsplit criterion) and per bin in qT < 5 GeV
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot  # noqa: E402

from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument(
    "--cache",
    default="/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full",
)
p.add_argument("--threads", type=int, default=128)
p.add_argument(
    "--outdir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
args = p.parse_args()

core = ScetlibADXsec(
    f"{args.cache}/cache.conf", f"{args.cache}/cache.npz", threads=args.threads
)
nm = list(core.param_names)
a = core.anchor.copy()
i2, i4 = nm.index("np_gnu_lambda2"), nm.index("np_gnu_lambda4")
print(
    "anchor lambda2_nu",
    a[i2],
    "lambda4_nu",
    a[i4],
    "linf_nu",
    a[nm.index("np_gnu_lambda_inf")],
)
bins = core.bins
print("bins shape", bins.shape, "columns (Qlo,Qhi,Ylo,Yhi,qTlo,qThi)")
qlo = bins[:, 4]
low = qlo < 5.0


def vj(p):
    v, J = core.values_and_jacobian(p)
    return np.asarray(v), np.asarray(J)


L4 = [
    0.0,
    -0.001,
    -0.002,
    -0.003,
    -0.004,
    -0.005,
    -0.006,
    -0.007,
    -0.008,
    -0.010,
    -0.012,
]
H = 1e-4
out = {}
for l2 in [a[i2], 0.184]:
    p0 = a.copy()
    p0[i2] = l2
    v0, J0 = vj(p0)
    lin = J0[:, i4] / v0
    rows = []
    for l4 in L4:
        p = p0.copy()
        p[i4] = l4
        v, J = vj(p)
        pp = p.copy()
        pp[i4] += H
        pm = p.copy()
        pm[i4] -= H
        vp, _ = vj(pp)
        vm, _ = vj(pm)
        fwd, bwd = (vp - v) / H, (v - vm) / H
        ad = J[:, i4]
        scale = np.max(np.abs(ad))
        r = v / v0
        linpred = 1 + (l4 - 0.0) * lin
        row = dict(
            l2=float(l2),
            l4=l4,
            min_sigma=float(v.min()),
            n_nonpos=int((v <= 0).sum()),
            max_dev_ratio_low=float(np.max(np.abs(r[low] - 1))),
            max_dev_from_linear_low=float(np.max(np.abs(r[low] - linpred[low]))),
            fd_ad_fwd_rel=float(np.max(np.abs(fwd - ad)) / scale),
            fd_ad_bwd_rel=float(np.max(np.abs(bwd - ad)) / scale),
            fd_fwd_bwd_perbin_low=float(
                np.max(
                    np.abs(fwd[low] - bwd[low])
                    / np.maximum(np.abs(ad[low]), 1e-3 * scale)
                )
            ),
            dlogsig_dl4_low_range=[
                float((ad / v)[low].min()),
                float((ad / v)[low].max()),
            ],
        )
        rows.append(row)
        print(json.dumps(row))
        out.setdefault(f"{l2:.3f}", {})[f"{l4:+.3f}"] = dict(
            ratio=r.tolist(), ad=(ad / v).tolist()
        )
    out[f"rows_{l2:.3f}"] = rows

np.savez(
    os.path.join(args.outdir, "probe_l4nu.npz"),
    bins=bins,
    L4=np.array(L4),
    **{
        k: np.array([[out[k][f"{l4:+.3f}"]["ratio"] for l4 in L4]])
        for k in out
        if not k.startswith("rows")
    },
)
json.dump(
    {k: v for k, v in out.items() if k.startswith("rows")},
    open(os.path.join(args.outdir, "probe_l4nu.json"), "w"),
    indent=1,
)

# --- plot: ratio vs qT, lowest |Y| row, both lambda2_nu lines --------------
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

fig, axs = plt.subplots(1, 2, figsize=(12, 4.6), sharey=False)
y0 = bins[:, 2] == bins[:, 2].min()
qc = 0.5 * (bins[y0, 4] + bins[y0, 5])
cm = plt.get_cmap("viridis")
for ax, key in zip(axs, [f"{a[i2]:.3f}", "0.184"]):
    for k, l4 in enumerate(L4):
        r = np.array(out[key][f"{l4:+.3f}"]["ratio"])[y0]
        ax.plot(
            qc,
            r,
            marker=".",
            color=cm(k / (len(L4) - 1)),
            label=f"$\\lambda_4^\\nu$={l4:+.3f}",
        )
    ax.set_xscale("log")
    ax.set_xlabel("$q_T$ bin centre [GeV]  (|Y| lowest row)")
    ax.set_ylabel(r"$\sigma(\lambda_4^\nu)/\sigma(\lambda_4^\nu=0)$")
    ax.set_title(f"production cache, $\\lambda_2^\\nu$={key}, rest at anchor")
    ax.axhline(1, color="k", lw=0.5)
axs[0].legend(fontsize=7, ncol=2)
fig.tight_layout()
save_plot(
    args.outdir,
    "probe_l4nu_ratio",
    fig=fig,
    args=args,
    meta_info={"cache": args.cache, "SCETLIB_BUILD": os.environ.get("SCETLIB_BUILD")},
)
print("PROBE_DONE")
