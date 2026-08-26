#!/usr/bin/env python3
"""Summary figures for the 62-member PDF eigenvector cache validation.

Three figures, each answering one question a per-direction response plot cannot:

  1. ``eig_vs_template``  -- max|model/template - 1| for the 58 eigenvector
     members against the non-PDF directions, as shipped and with the known
     qT [0,1] nonsingular-cutoff bin dropped. The question is whether the
     eigenvectors are in the same accuracy class as the directions already
     signed off.
  2. ``eig_convention``   -- the log-slope s per eigenvector member, with the
     values a 90%/68% CL mismatch (1.645, 1/1.645) or a sign-convention flip
     (-1) would have produced drawn in. This is the figure that says "same
     convention on both sides" with a number.
  3. ``eig_degeneracy``   -- Jacobian column norm per eigenvector and the worst
     off-diagonal cosine, i.e. whether any of the 29 directions is degenerate
     enough to make a 53-parameter fit ill-conditioned.
  4. ``other39_vs_p4``    -- the non-PDF directions on this cache against the
     published n_eig = 0 production cache, with the two-independent-builds
     reproducibility floor (3.0e-03 in the Jacobian) drawn in.

Inputs are the .npz from pdf62_eig_conventions.py and the parsed
validate_variations table, so nothing here reloads the model.
"""

import argparse
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from wums import output_tools, plot_tools  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--npz", required=True)
ap.add_argument("--valtable", required=True, help="parsed validate_variations table (tsv)")
ap.add_argument("--p4table", required=True, help="published n_eig=0 p4 table (tsv)")
ap.add_argument("--outdir", required=True)
a = ap.parse_args()
os.makedirs(a.outdir, exist_ok=True)
z = np.load(a.npz, allow_pickle=True)

CMS = dict(cms_label="Work in progress")


def read_tsv(p):
    d = {}
    for line in open(p):
        f = line.split("\t")
        if len(f) >= 3:
            d[f[0].strip()] = (float(f[1]), float(f[2]))
    return d


val = read_tsv(a.valtable)
p4 = read_tsv(a.p4table)
_PDF = re.compile(r"^pdf(\d+)$")
eig = {k: v for k, v in val.items() if _PDF.match(k)}
oth = {k: v for k, v in val.items() if not _PDF.match(k)}


def save(fig, name, meta):
    plot_tools.save_pdf_and_png(a.outdir, name, fig=fig)
    output_tools.write_index_and_log(a.outdir, name, analysis_meta_info=meta, args=None)
    plt.close(fig)


# ---------------- 1. eigenvectors against the other directions ----------------
tags = [str(t) for t in z["tags"]]
dq = z["dev_qt1"]
da = z["dev_all"]
fig, ax = plt.subplots(figsize=(9.0, 5.0))
xs = np.arange(len(tags))
ax.semilogy(xs, da, "o", ms=4, color="#5790fc", label="58 PDF eigenvector members, all qT")
ax.semilogy(xs, dq, "s", ms=4, color="#e42536", label="same, qT > 1 GeV")
ov = np.array([v[0] for v in oth.values()])
ax.axhspan(ov.min(), ov.max(), color="0.85", zorder=0,
           label=f"span of the {len(ov)} non-PDF directions ({ov.min():.0e}..{ov.max():.0e})")
ax.axhline(np.median(ov), color="0.4", ls=":", lw=1)
ax.set_xticks(xs[::2])
ax.set_xticklabels([t.replace("eig", "") for t in tags][::2], rotation=90, fontsize=6)
ax.set_xlabel("PDF eigenvector member (index + up/dn)")
ax.set_ylabel(r"max$|\sigma^{\rm model}_{\rm var}/\sigma^{\rm model}_{\rm cen}\,/\,"
              r"(\sigma^{\rm tmpl}_{\rm var}/\sigma^{\rm tmpl}_{\rm cen}) - 1|$")
ax.grid(alpha=0.3)
ax.legend(fontsize=7, loc="upper left")
fig.tight_layout()
save(fig, "eig_vs_template", {
    "what": "worst-bin closure of each PDF eigenvector member against its template",
    "cache": "pdf62_260826/merged_full, 210 gen bins, 62 members, n_eig=29",
    "reference": "..._pdfvars_CorrZ.pkl.lz4, pdf(2i+1)/pdf(2i+2) over pdf0",
    "grey band": "the non-PDF directions on the SAME cache, for scale",
    "qT>1 series": "the qT [0,1] gen bin carries a known nonsingular-cutoff "
                   "convention difference (model 0.1 GeV, templates 1.0 GeV)",
    "worst eigenvector, all qT": f"{da.max():.3e} ({tags[int(np.argmax(da))]})",
    "worst eigenvector, qT>1": f"{dq.max():.3e} ({tags[int(np.argmax(dq))]})",
})

# ---------------- 2. convention ----------------
s = z["slope_qt1"]
sp = z["slope_partner"]
fig, ax = plt.subplots(figsize=(9.0, 4.6))
ax.plot(xs, s, "o", ms=4, color="#e42536", label=r"$s$ from $\ln r_{\rm model} = s\,\ln r_{\rm template}$")
ax.plot(xs, sp, "x", ms=4, color="#5790fc", label=r"$s$ against the PARTNER member (sign test)")
for y, lab, c in ((1.0, "same convention", "0.3"),
                  (1.645, r"templates 68% CL / model 90% CL", "#f89c20"),
                  (1 / 1.645, r"templates 90% CL / model 68% CL", "#964a8b"),
                  (-1.0, "down-member sign flip", "#7a21dd")):
    ax.axhline(y, ls="--", lw=1, color=c)
    ax.text(len(tags) * 1.005, y, lab, fontsize=6, va="center", color=c)
ax.set_xticks(xs[::2])
ax.set_xticklabels([t.replace("eig", "") for t in tags][::2], rotation=90, fontsize=6)
ax.set_xlabel("PDF eigenvector member")
ax.set_ylabel(r"log-response slope $s$")
ax.set_ylim(-1.4, 2.0)
ax.grid(alpha=0.3)
ax.legend(fontsize=7, loc="lower left")
fig.tight_layout()
save(fig, "eig_convention", {
    "what": "CT18Z eigenvector CONVENTION test, model against templates",
    "method": "least squares through the origin of ln r_model on ln r_template "
              "over the gen bins with |ln r_template| > 1e-4 and qT > 1 GeV",
    "reading": "s = 1 -> both sides are the raw Hessian member, per pair, "
               "c_e = +-1. A CL mismatch is a flat 1.645 or 1/1.645; a "
               "down-member sign flip is -1 against its own member and +1 "
               "against its partner.",
    "measured": f"mean s = {s.mean():.6f}, max|s-1| = {np.max(np.abs(s-1)):.2e}",
    "partner slope": f"mean {sp.mean():.4f} (expected ~ -1 for a symmetric "
                     f"Hessian pair, which is what a NON-flipped sign gives)",
})

# ---------------- 3. degeneracy ----------------
jac, names = z["jac"], [str(x) for x in z["names"]]
ie = z["eig_cols"]
Je = jac[:, ie]
nrm = np.linalg.norm(Je, axis=0)
U = Je / nrm
C = U.T @ U
fig, axs = plt.subplots(1, 2, figsize=(11.0, 4.4))
axs[0].bar(np.arange(len(nrm)), nrm, color="#5790fc")
axs[0].set_yscale("log")
axs[0].set_xlabel(r"eigenvector index $e$")
axs[0].set_ylabel(r"$\|\partial\sigma/\partial c_e\|_2$ over the 210 gen bins")
axs[0].grid(alpha=0.3)
axs[0].set_title(f"weakest / strongest = {nrm.min()/nrm.max():.2e}", fontsize=9)
Cd = C.copy()
np.fill_diagonal(Cd, np.nan)
im = axs[1].imshow(np.abs(Cd), vmin=0, vmax=1, cmap="viridis")
axs[1].set_xlabel(r"$e$")
axs[1].set_ylabel(r"$e'$")
k = np.unravel_index(np.nanargmax(np.abs(Cd)), Cd.shape)
axs[1].set_title(rf"$\max_{{e\neq e'}}|\cos| = {np.nanmax(np.abs(Cd)):.3f}$"
                 rf"  ({k[0]},{k[1]})", fontsize=9)
fig.colorbar(im, ax=axs[1], label=r"$|\cos(\partial_e\sigma, \partial_{e'}\sigma)|$")
fig.tight_layout()
sv = np.linalg.svd(U, compute_uv=False)
save(fig, "eig_degeneracy", {
    "what": "are any of the 29 eigenvector directions degenerate at the anchor",
    "why": "the backend refuses an identically-zero column (that is how "
           "tnp_b_qqDS was caught for the Z); a NEAR-degenerate direction is "
           "invisible to that guard and would make a 53-parameter fit "
           "ill-conditioned",
    "column norms": f"max {nrm.max():.4g}, min {nrm.min():.4g} "
                    f"(pdf_eig{int(np.argmin(nrm))}), ratio {nrm.min()/nrm.max():.2e}",
    "worst |cos|": f"{np.nanmax(np.abs(Cd)):.4f} between pdf_eig{k[0]} and pdf_eig{k[1]}",
    "cond of the normalised 29-column block": f"{sv[0]/sv[-1]:.4g}",
})

# ---------------- 4. the other 39 (+2 alphaS) against the n_eig=0 cache -------
common = [k for k in oth if k in p4]
xv = np.array([p4[k][0] for k in common])
yv = np.array([oth[k][0] for k in common])
fig, ax = plt.subplots(figsize=(6.2, 6.0))
lo, hi = 1e-6, 3e-2
ax.plot([lo, hi], [lo, hi], "-", color="0.5", lw=1)
for f, c, lab in ((1.3, "#f89c20", None), (2.0, "#964a8b", None)):
    ax.plot([lo, hi], [lo * f, hi * f], ":", color=c, lw=1, label=lab)
    ax.plot([lo, hi], [lo / f, hi / f], ":", color=c, lw=1)
ax.axhspan(lo, 3.0e-3, color="0.9", zorder=0,
           label="below the two-build reproducibility floor (3.0e-03, Jacobian)")
ax.loglog(np.maximum(xv, lo), np.maximum(yv, lo), "o", ms=5, color="#e42536")
for k, x_, y_ in zip(common, xv, yv):
    if max(x_, y_) > 2e-3:
        ax.annotate(k, (max(x_, lo), max(y_, lo)), fontsize=5,
                    xytext=(3, 3), textcoords="offset points")
ax.set_xlim(lo, hi)
ax.set_ylim(lo, hi)
ax.set_xlabel(r"max$|$dev$|$, published $n_{\rm eig}=0$ cache (cache_260825_p4)")
ax.set_ylabel(r"max$|$dev$|$, this 62-member cache ($n_{\rm eig}=29$)")
ax.grid(alpha=0.3, which="both")
ax.legend(fontsize=7, loc="upper left")
fig.tight_layout()
r = yv / np.where(xv == 0, np.nan, xv)
save(fig, "other39_vs_p4", {
    "what": "the non-PDF directions: does turning the eigenvectors ON "
            "perturb anything already signed off",
    "x": "cache_260825_p4, 210 bins, n_eig=0, P=24, target_precision_rel 1e-3",
    "y": "pdf62_260826/merged_full, 210 bins, n_eig=29, P=53, same runcard base",
    "NOT an A/B in one process": "two INDEPENDENTLY built caches; the builder "
        "is not node-reproducible, and the measured floor between two builds of "
        "the same runcard is 3.1e-05 in sigma but 3.0e-03 in the Jacobian at a "
        "displaced point -- which is where most of these residuals sit",
    "ratio y/x": f"median {np.nanmedian(r):.3f}, "
                 f"range {np.nanmin(r):.3f} .. {np.nanmax(r):.3f}",
})
print("wrote 4 figures to", a.outdir)
