"""
Build 4D and 1D tables for 260430_debug_1d_vs_4d.

Per (config, param) the cell value is

  raw mode    : rabbit_pull * scaleParams_factor
                (units = Nominal-config prior σ for that NP)
  physical    : raw * σ_phys
                (units = natural physical units of the NP, where
                 σ_phys = base_kfactor * template half-range)

Default is --physical. Pass --no-physical to keep raw rescaled pulls.
"""

import argparse, os, re, sys, math
import numpy as np
from rabbit.io_tools import get_fitresult
from scipy.stats import chi2 as chi2_dist


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--physical",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="If set (default), multiply each NP cell by its prefit physical "
        "1σ_prior (base kfactor × template half-range). With "
        "--no-physical, cells are raw rabbit pulls multiplied only by "
        "the --scaleParams factor relative to Nominal.",
    )
    return p.parse_args()


ARGS = parse_args()

OUT_DIR = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260430_debug"
LOG_4D_BASE = None  # 4D pre-existing, no log needed
LOG_1D_MAIN = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/logs/ptll_debug_fits_260501_084355.log"
LOG_1D_NCST = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/logs/scetlibNoConstraint_260501_090633.log"

POI = "pdfAlphaS"

#  Per-NP prefit prior 1-sigma in *physical* units.
#  Computed as base_kfactor * |up_template - down_template| / 2, where:
#    - chargeVgenNP0scetlibNPZ{lambda2,delta_lambda2,lambda4}: kfactor base = 1
#      (rabbit_theory_helper.py:866). np_map values give the physical lambda
#      template extrema (line 828-830).
#    - scetlibNPgamma{Lambda2,Lambda4,LambdaInf}: kfactor base = 10
#      (rabbit_theory_helper.py:737). lattice_vals give the `nu` template
#      extrema (line 686-693).
#  Multiplying the rabbit pull by this number gives the physical postfit
#  shift of the underlying NP in its natural (Nominal-config) units.
#
#  NPS entries: (rabbit_name, display_label, sigma_phys, prefit_central)
#  Prefit centrals from analysis note AN-25-085 theory.tex (eq. 5.2 lattice
#  values for gamma NPs; eq. 5.3 Cridge values for charge-V chargeVgenNP0
#  NPs). For fakelumi the cell is a *fractional* norm shift around the
#  nominal multiplier 1.0, so we record prefit=0 (cell = postfit shift).
NPS = [
    ("chargeVgenNP0scetlibNPZlambda2", r"$\lambda_2$", 1.0 * (0.5 - 0.0) / 2, 0.25),
    (
        "chargeVgenNP0scetlibNPZdelta_lambda2",
        r"$\Delta\lambda_2$",
        1.0 * (0.02 + 0.02) / 2,
        0.125,
    ),
    ("chargeVgenNP0scetlibNPZlambda4", r"$\lambda_4$", 1.0 * (0.12 - 0.01) / 2, 0.06),
    (
        "scetlibNPgammaLambda2",
        r"$\gamma_{\Lambda_2}$",
        10.0 * (0.1202 - 0.0538) / 2,
        0.0870,
    ),
    (
        "scetlibNPgammaLambda4",
        r"$\gamma_{\Lambda_4}$",
        10.0 * (0.014 - 0.0008) / 2,
        0.0074,
    ),
    (
        "scetlibNPgammaLambdaInf",
        r"$\gamma_{\Lambda_\infty}$",
        10.0 * (2.1922 - 1.1784) / 2,
        1.6853,
    ),
    # fakelumi: norm systematic added by setupRabbit when --fakelumi 1.1
    # (10% mirrored norm uncertainty on MCwithLumiNorm). It's
    # noConstraint=True, so the postfit pull is purely data-driven; the
    # cell is the fractional norm shift, so prefit "central"=0.
    # Only present in configs that pass --fakelumi; cell shows "—" otherwise.
    ("fakelumi", r"$f_{\rm fake}$", 0.1, 0.0),
]
NP_NAMES = [n for n, _, _, _ in NPS]
SIGMA_PHYS = {n: s for n, _, s, _ in NPS}
PREFIT = {n: c for n, _, _, c in NPS}

# Configs paired so each fakelumi variant sits directly below its
# sans-fakelumi partner. Ordering is roughly: nominal → single-NP stress →
# all-NP stress → ×5 with γ_Λ∞ default → ×2 → fully unconstrained →
# unconstrained with γ_Λ∞ default. Within each pair: no-fakelumi first.
CONFIGS = [
    # (postfix, display, dropped?, scaleParams_list)
    # Nominal pair
    ("LatticeNoConstraints", "Nominal", False, []),
    ("LatticeNoConstraints_fakelumi", "Nominal + fakelumi", False, []),
    # Λ4 × 5 pair
    (
        "LatticeNoConstraints_chargeVgenNP0scetlibNPZlambda4Scale5p0",
        r"$\Lambda_4 \times 5$",
        False,
        [("chargeVgenNP0scetlibNPZlambda4", 5.0)],
    ),
    (
        "LatticeNoConstraints_chargeVgenNP0scetlibNPZlambda4Scale5p0_fakelumi",
        r"$\Lambda_4 \times 5$ + fakelumi",
        False,
        [("chargeVgenNP0scetlibNPZlambda4", 5.0)],
    ),
    # Λs × 5 (charge-V chargeVgenNP0scetlibNP*) pair
    (
        "LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0",
        r"$\Lambda$s $\times 5$",
        False,
        [("chargeVgenNP0scetlibNP", 5.0)],
    ),
    (
        "LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0_fakelumi",
        r"$\Lambda$s $\times 5$ + fakelumi",
        False,
        [("chargeVgenNP0scetlibNP", 5.0)],
    ),
    # all NP asymmetric pair
    ("LatticeNoConstraints_ScetlibNoSymmetrize", "all NP asym.", False, []),
    (
        "LatticeNoConstraints_ScetlibNoSymmetrize_fakelumi",
        "all NP asym. + fakelumi",
        False,
        [],
    ),
    # all NP × 5 pair
    (
        "LatticeNoConstraints_scetlibScale5p0",
        r"all NP $\times 5$",
        False,
        [("scetlib", 5.0)],
    ),
    (
        "LatticeNoConstraints_scetlibScale5p0_fakelumi",
        r"all NP $\times 5$ + fakelumi",
        False,
        [("scetlib", 5.0)],
    ),
    # all NP × 5, γ_Λ∞ default pair
    (
        "LatticeNoConstraints_scetlibNoLambdaInfScale5p0",
        r"all NP $\times 5$, $\gamma_{\Lambda_\infty}$ default",
        False,
        [("scetlib(?!.*LambdaInf)", 5.0)],
    ),
    (
        "LatticeNoConstraints_scetlibNoLambdaInfScale5p0_fakelumi",
        r"all NP $\times 5$, $\gamma_{\Lambda_\infty}$ default + fakelumi",
        False,
        [("scetlib(?!.*LambdaInf)", 5.0)],
    ),
    # all NP × 2 pair
    (
        "LatticeNoConstraints_scetlibScale2p0",
        r"all NP $\times 2$",
        False,
        [("scetlib", 2.0)],
    ),
    (
        "LatticeNoConstraints_scetlibScale2p0_fakelumi",
        r"all NP $\times 2$ + fakelumi",
        False,
        [("scetlib", 2.0)],
    ),
    # all NP unconstrained pair
    ("LatticeNoConstraints_scetlibNoConstraint", "all NP unconstrained", False, []),
    (
        "LatticeNoConstraints_scetlibNoConstraint_fakelumi",
        "all NP unconstrained + fakelumi",
        False,
        [],
    ),
    # all NP unconstrained, γ_Λ∞ default pair
    (
        "LatticeNoConstraints_scetlibNoLambdaInfNoConstraint",
        r"all NP unconstr., $\gamma_{\Lambda_\infty}$ default",
        False,
        [],
    ),
    (
        "LatticeNoConstraints_scetlibNoLambdaInfNoConstraint_fakelumi",
        r"all NP unconstr., $\gamma_{\Lambda_\infty}$ default + fakelumi",
        False,
        [],
    ),
    # γ_Λ∞ tightened: kfactor 3 (constrained); other 5 NPs unconstrained
    # at their (un-inflated) lattice σ.
    (
        "LatticeNoConstraints_LambdaInfTight3_fakelumi",
        r"$\gamma_{\Lambda_\infty}$ constr.\@$\times3$, others unconstr. + fakelumi",
        False,
        [
            ("scetlibNPgammaLambda2|scetlibNPgammaLambda4", 0.1),
            ("scetlibNPgammaLambdaInf", 0.3),
        ],
    ),
    # All 3 γ NPs constrained at ×3 the lattice σ (down from ×10);
    # chargeV NPs unconstrained.
    (
        "LatticeNoConstraints_gammaTight3_fakelumi",
        r"all $\gamma$ NPs constr.\@$\times3$, chargeV unconstr. + fakelumi",
        False,
        [("scetlibNPgamma", 0.3)],
    ),
    # All 6 SCETlib NPs constrained at ×3 their lattice / cookbook σ.
    (
        "LatticeNoConstraints_allNPConstr3",
        r"all NPs constr.\@$\times3$",
        False,
        [("scetlibNPgamma", 0.3), ("chargeVgenNP0scetlibNP", 3.0)],
    ),
    (
        "LatticeNoConstraints_allNPConstr3_fakelumi",
        r"all NPs constr.\@$\times3$ + fakelumi",
        False,
        [("scetlibNPgamma", 0.3), ("chargeVgenNP0scetlibNP", 3.0)],
    ),
]

# Drop _fakelumi_noAlphaS and plain LatticeNoConstraints duplicates per the README
# (the README excludes LatticeNoConstraints? actually it says "plain LatticeNoConstraints"
# meaning the no-alphaS variant — the Nominal IS plain LatticeNoConstraints with alphaS).
# We keep Nominal.


def fourd_dir(p):
    return f"{OUT_DIR}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_{p}/fitresults.hdf5"


def oned_dir(p):
    return f"{OUT_DIR}/ZMassDilepton_ptll_{p}/fitresults.hdf5"


def kfactor_scale(param_name, scaleParams_list):
    """Multiplier on the postfit pull to put a config on the same physical
    footing as the Nominal config (which is also LatticeNoConstraints, so the
    baseline gamma kfactor of 10 cancels and is omitted here). The only
    cross-config variation comes from --scaleParams REGEX=FACTOR, which
    inflates the kfactor of any matching NP relative to Nominal."""
    factor = 1.0
    for regex, f in scaleParams_list:
        if re.search(regex, param_name):
            factor *= f
    return factor


def get_parm(parms, name):
    ax = parms.axes[0]
    names = list(ax)
    if name not in names:
        return None, None
    idx = names.index(name)
    vals = parms.values()
    vars_ = parms.variances()
    return float(vals[idx]), float(np.sqrt(vars_[idx]))


def fmt_pair(val, err, scale):
    """Return the physical postfit shift of the NP in its natural units.

    scale = scaleParams_factor * sigma_phys, where:
      - scaleParams_factor: 1 in Nominal, 5 in matching Scale5p0 cells.
      - sigma_phys = base_kfactor * template_half_range, the physical
        prefit prior sigma of the NP in the Nominal config (constant
        per column).
    """
    if val is None or err is None:
        return "---"
    pv = val * scale
    pe = err * scale
    fmt = "{:+.3f}" if max(abs(pv), abs(pe)) < 10 else "{:+.2f}"
    return f"${fmt.format(pv)}\\pm{fmt.format(pe).lstrip('+')}$"


def extract_one_fit(fpath, scaleParams_list):
    """Returns dict per param of (pull_val, pull_err, scale, phys_val, phys_err)
    plus alphaS pull and total sigma. Also tries the sister
    fitresults_asimov.hdf5 in the same dir and stores the asimov POI
    uncertainty under "alphaS_asimov" (None if missing).

    Asimov is read independently of the data fit so a missing/in-flight
    fitresults.hdf5 doesn't blank out the asimov column."""
    out = {
        "params": {},
        "alphaS": (None, None),
        "alphaS_asimov": None,
        "ok": False,
        "err": None,
    }

    # Try the data fitresults.
    if os.path.exists(fpath):
        try:
            fr, meta = get_fitresult(fpath, meta=True)
            parms = fr["parms"].get()
            for name in NP_NAMES:
                v, e = get_parm(parms, name)
                s = kfactor_scale(name, scaleParams_list)
                if ARGS.physical:
                    s = s * SIGMA_PHYS[name]
                if v is None:
                    out["params"][name] = (None, None, s, None, None)
                else:
                    out["params"][name] = (v, e, s, v * s, e * s)
            v, e = get_parm(parms, POI)
            out["alphaS"] = (v, e)
            out["ok"] = True
        except Exception as e:
            out["err"] = f"open: {e}"
    else:
        out["err"] = f"missing {fpath}"

    # Try the asimov sister file independently.
    asimov_path = os.path.join(os.path.dirname(fpath), "fitresults_asimov.hdf5")
    if os.path.exists(asimov_path):
        try:
            fr_a, _ = get_fitresult(asimov_path, meta=True)
            parms_a = fr_a["parms"].get()
            _, ea = get_parm(parms_a, POI)
            out["alphaS_asimov"] = ea
        except Exception:
            pass
    return out


def parse_oned_sat(postfix):
    """Return (ndf, chi2, pvalue%) parsed from rabbit_fit log.
    Only the original 9 1D fits have logs; everything else returns None."""
    if postfix.endswith("scetlibNoConstraint"):
        log = LOG_1D_NCST
        with open(log) as fh:
            text = fh.read()
        # ANSI color codes in this log break a strict line-by-line pattern,
        # so use DOTALL with non-greedy .*?. There are multiple Saturated chi2
        # blocks (per fit iteration); take the last.
        ms = re.findall(
            r"Saturated chi2:.*?ndof:\s*(\d+).*?2\*deltaNLL:\s*([\d.]+).*?p-value:\s*([\d.]+)%",
            text,
            re.DOTALL,
        )
        if ms:
            ndof, c, p = ms[-1]
            return int(ndof), float(c), float(p)
        return None, None, None
    log = LOG_1D_MAIN
    with open(log) as fh:
        text = fh.read()
    pat = re.compile(
        r"postfix="
        + re.escape(postfix)
        + r"\s*\n(.*?)--- DONE.*?postfix="
        + re.escape(postfix),
        re.DOTALL,
    )
    m = pat.search(text)
    if not m:
        return None, None, None
    block = m.group(1)
    sat = re.search(
        r"Saturated chi2:.*?ndof:\s*(\d+).*?2\*deltaNLL:\s*([\d.]+).*?p-value:\s*([\d.]+)%",
        block,
        re.DOTALL,
    )
    if sat:
        return int(sat.group(1)), float(sat.group(2)), float(sat.group(3))
    return None, None, None


def fourd_sat(fpath):
    """Return (ndf, chi2, pvalue%) from the saturated projection test, or
    a special sentinel ('CHOLESKY_FAILED', None, None) if the run script
    flagged this dir as having had a Cholesky failure during sat-tests
    post-processing (touchfile cholesky_failed.flag in the dir)."""
    flag = os.path.join(os.path.dirname(fpath), "cholesky_failed.flag")
    if os.path.exists(flag):
        return ("CHOLESKY_FAILED", None, None)
    fr = get_fitresult(fpath)
    mp = fr["mappings"]["Project ch0 ptll"]
    ndf = int(mp["ndf_saturated"])
    c = float(mp["chi2_saturated"])
    pv = chi2_dist.sf(c, ndf) * 100
    return ndf, c, pv


def build_one_table(
    dim_label, dirfn, sat_extract_fn, include_alphas=True, ref_postfix=None
):
    rows = []
    ref_alphas = None
    for postfix, label, dropped, sp in CONFIGS:
        if dropped:
            continue
        fpath = dirfn(postfix)
        info = extract_one_fit(fpath, sp)
        if not info["ok"] and dim_label == "4D":
            print(f"WARN ({dim_label} {postfix}): {info['err']}", file=sys.stderr)
        # saturated
        try:
            sat = sat_extract_fn(fpath if dim_label == "4D" else postfix)
        except Exception as e:
            sat = (None, None, None)
        info["sat"] = sat
        info["label"] = label
        info["postfix"] = postfix
        rows.append(info)
        if include_alphas and postfix == "LatticeNoConstraints":
            ref_alphas = info["alphaS"]
    return rows, ref_alphas


def render_table(rows, dim_label, include_alphas=False, ref_alphas=None):
    """Render one LaTeX table for the given dimension."""
    n_np = len(NPS)
    base_cols = "l" + "c" * n_np + "c"
    if include_alphas:
        base_cols += "rrr"

    lines = []
    cap = (
        rf"Postfit nuisance pulls and saturated $p$-value for the {dim_label} fit "
        r"($p_T^{\ell\ell}\times y^{\ell\ell}\times\cos\theta^*_{\ell\ell}\times\phi^*_{\ell\ell}$"
        if dim_label == "4D"
        else rf"Postfit nuisance pulls and saturated $p$-value for the 1D fit "
        r"($p_T^{\ell\ell}$"
    )
    if ARGS.physical:
        cap += (
            "). Each NP cell is the physical postfit shift "
            "(rabbit pull $\\times$ Nominal-config prior $\\sigma$ in "
            "physical units), so values are directly in the natural units "
            "of each NP (GeV$^2$-like for $\\lambda$'s, $\\nu$ for the "
            "lattice $\\gamma$ parameters). Per-column "
            "$1\\sigma_{\\mathrm{prior}}$ in the header is "
            "base kfactor $\\times$ template half-range. "
            "\\texttt{--scaleParams} factors in Scale5p0 configs are "
            "additionally absorbed into the cell so that a 1-$\\sigma$ "
            "pull in any config maps to the same physical shift."
        )
    else:
        cap += (
            "). Each NP cell is the rabbit postfit pull (prefit "
            "$\\theta\\sim\\mathcal{N}(0,1)$ in Nominal), with "
            "\\texttt{--scaleParams} factors in Scale5p0 configs absorbed "
            "into the cell so that a value of 1 maps to the same physical "
            "template shift across configurations. The baseline $\\times 10$ "
            "kfactor on $\\gamma$ NPs from \\texttt{LatticeNoConstraints} "
            "is constant across all 9 configs and therefore cancels."
        )
    if include_alphas:
        cap += (
            " $\\Delta$pull on $\\alpha_S$ is relative to Nominal and "
            "scaled $\\times 2$ to convert from the rabbit template step "
            "(0.001) to the analysis's quoted $1\\sigma_{\\alpha_S}=0.002$ "
            "(matches \\texttt{pullsAndImpacts.sh --scaleImpacts 2.0}); "
            "$\\sigma(\\alpha_S)$ is the absolute postfit total uncertainty "
            "in the same $10^{-3}$ units. The \\textit{Asimov} column is "
            "the postfit $\\sigma(\\alpha_S)$ from a separate "
            "\\texttt{rabbit\\_fit -t -1} run on the same \\texttt{ZMassDilepton.hdf5} "
            "(expected uncertainty under nominal-MC truth). "
            "Sat. $p$ entries showing `---' are configurations where the "
            "saturated covariance Cholesky factorisation failed "
            "(Hessian not positive-definite) so the test could not be "
            "computed; the rest of the fit is unaffected."
        )

    lines.append(r"\begin{table}[h]")
    lines.append(r"  \centering")
    lines.append(r"  \caption{" + cap + r"}")
    lines.append(rf"  \label{{tab:debug_{dim_label.lower()}}}")
    lines.append(r"  \resizebox{\textwidth}{!}{%")
    lines.append(rf"  \begin{{tabular}}{{{base_cols}}}")
    lines.append(r"    \hline\hline")
    if ARGS.physical:
        header = (
            ["Configuration"]
            + [
                f"\\shortstack{{{lab} \\\\ "
                f"($\\mathrm{{prefit}}={c:g},\\,1\\sigma_{{\\mathrm{{prior}}}}={s:g}$)}}"
                for _, lab, s, c in NPS
            ]
            + ["Sat. $p$"]
        )
    else:
        header = ["Configuration"] + [lab for _, lab, _, _ in NPS] + ["Sat. $p$"]
    if include_alphas:
        header += [
            r"$\Delta$pull($\alpha_S$) [$10^{-3}$]",
            r"$\sigma(\alpha_S)$ [$10^{-3}$]",
            r"$\sigma(\alpha_S)$ Asimov [$10^{-3}$]",
        ]
    lines.append("    " + " & ".join(header) + r" \\")
    lines.append(r"    \hline")
    # CONFIGS is structured in pairs (no-fakelumi, +fakelumi), so emit
    # \hline after every 2nd row to visually separate sections.
    for i, info in enumerate(rows):
        cells = [info["label"]]
        for name in NP_NAMES:
            v, e, s, pv, pe = info["params"].get(name, (None,) * 5)
            cells.append(fmt_pair(v, e, s))
        ndf, c, p = info["sat"]
        # `---` covers both "no sat tests run" and "sat tests crashed
        # (Cholesky); see cholesky_failed.flag in the dir for the latter".
        cells.append(f"{p:.2f}\\%" if p is not None else "---")
        if include_alphas:
            v, e = info["alphaS"]
            ref_v, ref_e = ref_alphas
            # alphaS POI: rabbit template variation = 0.001 but quoted
            # 1 sigma_alphaS = 0.002, so the analysis convention scales
            # alphaS quantities by 2 (matches pullsAndImpacts.sh
            # --scaleImpacts 2.0). Both Delta-pull (vs Nominal) and the
            # absolute postfit total sigma are multiplied.
            if v is None or ref_v is None:
                cells.append("---")
            elif info["postfix"] == "LatticeNoConstraints":
                cells.append("ref")
            else:
                cells.append(f"${2.0 * (v - ref_v):+.2f}$")
            cells.append(f"${2.0 * e:.3f}$" if e is not None else "---")
            ea = info.get("alphaS_asimov")
            cells.append(f"${2.0 * ea:.3f}$" if ea is not None else "---")
        lines.append("    " + " & ".join(cells) + r" \\")
        # Section break after each pair (every 2nd row), but not after the
        # last row (which is followed by \hline\hline below).
        if i % 2 == 1 and i < len(rows) - 1:
            lines.append(r"    \hline")
    lines.append(r"    \hline\hline")
    lines.append(r"  \end{tabular}%")
    lines.append(r"  }")
    lines.append(r"\end{table}")
    return "\n".join(lines)


# Build
rows4d, ref4d = build_one_table("4D", fourd_dir, fourd_sat, include_alphas=True)
rows1d, _ = build_one_table("1D", oned_dir, parse_oned_sat, include_alphas=False)

doc = []
doc.append(r"\documentclass[landscape]{article}")
doc.append(r"\usepackage[margin=1.5cm,landscape]{geometry}")
doc.append(r"\usepackage{graphicx}")
doc.append(r"\usepackage{booktabs}")
doc.append(r"\begin{document}")
doc.append("")
mode_str = "physical" if ARGS.physical else "raw (Nominal-prior σ)"
doc.append(
    rf"% Postfit NP table for the 260430_debug 1D-vs-4D study (mode: {mode_str})."
)
if ARGS.physical:
    doc.append(r"% cell = rabbit_pull × scaleParams_factor × σ_phys")
    doc.append(r"% σ_phys = base_kfactor × template half-range (per-column constant)")
else:
    doc.append(r"% cell = rabbit_pull × scaleParams_factor")
    doc.append(r"% (Nominal cells = raw rabbit pull; Scale5p0 cells include the ×5)")
doc.append("")
doc.append(render_table(rows4d, "4D", include_alphas=True, ref_alphas=ref4d))
doc.append("")
doc.append(render_table(rows1d, "1D"))
doc.append("")
doc.append(r"\end{document}")
print("\n".join(doc))
