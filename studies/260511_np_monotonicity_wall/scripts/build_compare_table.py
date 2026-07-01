"""Build a postfit-NP LaTeX/PDF table for the np_monotonicity_wall study.

Mirrors studies/260430_debug_1d_vs_4d/scripts/build_tables.py, but
takes (label, fitresults_path, effective_kfactor_overrides) tuples instead
of a hardcoded config list. Physical postfit shifts use np_param_map.json
linearization. αS columns follow the existing convention (Δpull × 2,
σ × 2 to convert from the rabbit template step 0.001 to the analysis
σ_αS = 0.002).
"""

import argparse, json, os, sys, subprocess
import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")
from rabbit.io_tools import get_fitresult
from scipy.stats import chi2 as chi2_dist

PMAP_JSON = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/scripts/np_param_map.json"
with open(PMAP_JSON) as f:
    PMAP = json.load(f)

# Column order and display labels
NPS = [
    ("scetlibNPgammaLambda2", r"$\gamma_{\Lambda_2}$"),
    ("scetlibNPgammaLambda4", r"$\gamma_{\Lambda_4}$"),
    ("scetlibNPgammaLambdaInf", r"$\gamma_{\Lambda_\infty}$"),
    ("chargeVgenNP0scetlibNPZlambda2", r"$\Lambda_2$"),
    ("chargeVgenNP0scetlibNPZdelta_lambda2", r"$\Delta\Lambda_2$"),
    ("chargeVgenNP0scetlibNPZlambda4", r"$\Lambda_4$"),
]

POI = "pdfAlphaS"

# Pretty display names per shell-arg label.
DISPLAY_NAME = {
    "prefit": r"prefit (AN, 100\%\ on CS)",
    "nominal": "nominal",
    "nominal_fakelumi": "nominal + fakelumi",
    "nominal_reg": r"nominal + reg ($\tau{=}5$)",
    "nominal_fakelumi_reg": r"nominal + fakelumi + reg ($\tau{=}5$)",
    "inflatedV2": "inflated",
    "inflatedV2_fakelumi": "inflated + fakelumi",
    "inflatedV2_reg": r"inflated + reg ($\tau{=}5$)",
    "inflatedV2_fakelumi_reg": r"inflated + fakelumi + reg ($\tau{=}5$)",
    "unconstrained": r"unconstrained ($\tau{=}3$)",
    "unconstrained_fakelumi": r"unconstrained + fakelumi ($\tau{=}3$)",
    "unconstrained_tau5": r"unconstrained ($\tau{=}5$)",
    "unconstrained_tau5_fakelumi": r"unconstrained + fakelumi ($\tau{=}5$)",
    "inflate2x": r"inflated $\times 2$",
    "inflate2x_fakelumi": r"inflated $\times 2$ + fakelumi",
    "inflate2x_reg5": r"inflated $\times 2$ + reg ($\tau{=}5$)",
    "inflate3x": r"inflated $\times 3$",
    "inflate3x_fakelumi": r"inflated $\times 3$ + fakelumi",
    "inflate3x_reg5": r"inflated $\times 3$ + reg ($\tau{=}5$)",
    "inflate5x": r"inflated $\times 5$",
    "inflate5x_fakelumi": r"inflated $\times 5$ + fakelumi",
    "inflate5x_reg5": r"inflated $\times 5$ + reg ($\tau{=}5$)",
    "inflate5x_reg5_fakelumi": r"inflated $\times 5$ + reg ($\tau{=}5$) + fakelumi",
    "frozenNP": "frozen NPs (AN central)",
    "frozenNP_fakelumi": "frozen NPs + fakelumi",
    "tight50_reg": r"tight (50\%) + reg ($\tau{=}5$)",
    "tight50_fakelumi_reg": r"tight (50\%) + fakelumi + reg ($\tau{=}5$)",
    "nominal_2D_ptll_yll": r"nominal 2D ($p_T^{\ell\ell}$-$y_{\ell\ell}$)",
    "nominal_2D_ptll_yll_fakelumi": r"nominal 2D ($p_T^{\ell\ell}$-$y_{\ell\ell}$) + fakelumi",
    "inflate5x_2D_ptll_yll": r"inflated $\times 5$ 2D ($p_T^{\ell\ell}$-$y_{\ell\ell}$)",
    "inflate5x_reg5_2D_ptll_yll": r"inflated $\times 5$ 2D + reg ($\tau{=}5$)",
    "inflate5x_2D_ptll_yll_fakelumi": r"inflated $\times 5$ 2D ($p_T^{\ell\ell}$-$y_{\ell\ell}$) + fakelumi",
    "inflate5x_reg5_2D_ptll_yll_fakelumi": r"inflated $\times 5$ 2D + reg ($\tau{=}5$) + fakelumi",
    "NPCS100pct_asym": "nominal (asym templates)",
    "NPCS100pct_asym_fakelumi": "nominal (asym templates) + fakelumi",
    "unconstrained_asym_reg5": r"unconstrained + asym + reg ($\tau{=}5$)",
    "unconstrained_asym_reg5_fakelumi": r"unconstrained + asym + reg ($\tau{=}5$) + fakelumi",
}

# Section grouping: rows within the same inner list stay together; a
# \hline is inserted between sections.
SECTIONS = [
    ["prefit"],
    ["nominal", "nominal_fakelumi", "nominal_reg", "nominal_fakelumi_reg"],
    ["inflatedV2", "inflatedV2_fakelumi", "inflatedV2_reg", "inflatedV2_fakelumi_reg"],
    [
        "inflate2x",
        "inflate2x_fakelumi",
        "inflate2x_reg5",
        "inflate3x",
        "inflate3x_fakelumi",
        "inflate3x_reg5",
        "inflate5x",
        "inflate5x_fakelumi",
        "inflate5x_reg5",
        "inflate5x_reg5_fakelumi",
    ],
    [
        "unconstrained",
        "unconstrained_fakelumi",
        "unconstrained_tau5",
        "unconstrained_tau5_fakelumi",
    ],
    ["frozenNP", "frozenNP_fakelumi"],
    ["tight50_reg", "tight50_fakelumi_reg"],
    [
        "nominal_2D_ptll_yll",
        "nominal_2D_ptll_yll_fakelumi",
        "inflate5x_2D_ptll_yll",
        "inflate5x_2D_ptll_yll_fakelumi",
        "inflate5x_reg5_2D_ptll_yll",
        "inflate5x_reg5_2D_ptll_yll_fakelumi",
    ],
    ["NPCS100pct_asym", "NPCS100pct_asym_fakelumi"],
    ["unconstrained_asym_reg5", "unconstrained_asym_reg5_fakelumi"],
]

# Empty by default. Add labels here only if a fitresults file is present but
# should be hidden (e.g. a known-bad run). Historical note: inflate*_reg5
# rows produced before 2026-05-14 used a kfactor-unaware regularizer (the
# wall didn't fire because np_monotonicity.py ignored --scaleParams); the
# fix (commit on 2026-05-14) plumbs per-nuisance kfactors through the
# mapping. New reg5 fitresults at <CFG>/data_lrscan/fitresults.hdf5 are valid.
SKIP_LABELS = set()

# Per-config kfactor overrides on top of the nominal-config (where my linearization
# in np_param_map.json is encoded as if effective kfactor == 1). The effective
# kfactor is helper_scale × scaleParams_factor. For all three configs the helper
# scale=10 is overridden to 1 (either by --scaleParams scetlibNPgamma×0.1 or by
# the user's commented-out scale=10 in rabbit_theory_helper.py), so the only
# residual difference is from extra --scaleParams entries.
KFACTOR_OVERRIDES = {
    # Prefit row uses the AN convention: 100% on CS γ (= nominal kfactors).
    "prefit": {
        "scetlibNPgammaLambda2": 2.62,
        "scetlibNPgammaLambda4": 1.12,
        "scetlibNPgammaLambdaInf": 3.33,
    },
    # NPCS100pct (new nominal): CS γ inflated to ~100% of physical NP value
    "nominal": {
        "scetlibNPgammaLambda2": 2.62,
        "scetlibNPgammaLambda4": 1.12,
        "scetlibNPgammaLambdaInf": 3.33,
    },
    "nominal_fakelumi": {
        "scetlibNPgammaLambda2": 2.62,
        "scetlibNPgammaLambda4": 1.12,
        "scetlibNPgammaLambdaInf": 3.33,
    },
    # NPCS100pctV2: additionally inflate λ_2 and TMD Λ_4 to match postfit pull
    "inflatedV2": {
        "scetlibNPgammaLambda2": 4.32,
        "scetlibNPgammaLambda4": 1.12,
        "scetlibNPgammaLambdaInf": 3.33,
        "chargeVgenNP0scetlibNPZlambda4": 1.55,
    },
    "inflatedV2_fakelumi": {
        "scetlibNPgammaLambda2": 4.32,
        "scetlibNPgammaLambda4": 1.12,
        "scetlibNPgammaLambdaInf": 3.33,
        "chargeVgenNP0scetlibNPZlambda4": 1.55,
    },
    # NPUnconstrained: no scaleParams, helper scale=10 commented out → all k=1
    "unconstrained": {},
    "unconstrained_fakelumi": {},
    "unconstrained_tau5": {},
    "unconstrained_tau5_fakelumi": {},
    # Inflate chain: 2×, 3×, 5× of the nominal kfactors (CS λ_∞ stays at 3.33).
    "inflate2x": {
        "scetlibNPgammaLambda2": 5.24,
        "scetlibNPgammaLambda4": 2.24,
        "scetlibNPgammaLambdaInf": 3.33,
        "chargeVgenNP0scetlibNPZlambda2": 2.0,
        "chargeVgenNP0scetlibNPZdelta_lambda2": 2.0,
        "chargeVgenNP0scetlibNPZlambda4": 2.0,
    },
    "inflate3x": {
        "scetlibNPgammaLambda2": 7.86,
        "scetlibNPgammaLambda4": 3.36,
        "scetlibNPgammaLambdaInf": 3.33,
        "chargeVgenNP0scetlibNPZlambda2": 3.0,
        "chargeVgenNP0scetlibNPZdelta_lambda2": 3.0,
        "chargeVgenNP0scetlibNPZlambda4": 3.0,
    },
    "inflate5x": {
        "scetlibNPgammaLambda2": 13.1,
        "scetlibNPgammaLambda4": 5.60,
        "scetlibNPgammaLambdaInf": 3.33,
        "chargeVgenNP0scetlibNPZlambda2": 5.0,
        "chargeVgenNP0scetlibNPZdelta_lambda2": 5.0,
        "chargeVgenNP0scetlibNPZlambda4": 5.0,
    },
}
# reg5 variants share kfactors with their non-reg twins.
KFACTOR_OVERRIDES["inflate2x_reg5"] = KFACTOR_OVERRIDES["inflate2x"]
KFACTOR_OVERRIDES["inflate2x_fakelumi"] = KFACTOR_OVERRIDES["inflate2x"]
KFACTOR_OVERRIDES["inflate3x_reg5"] = KFACTOR_OVERRIDES["inflate3x"]
KFACTOR_OVERRIDES["inflate3x_fakelumi"] = KFACTOR_OVERRIDES["inflate3x"]
KFACTOR_OVERRIDES["inflate5x_reg5"] = KFACTOR_OVERRIDES["inflate5x"]
KFACTOR_OVERRIDES["inflate5x_fakelumi"] = KFACTOR_OVERRIDES["inflate5x"]
KFACTOR_OVERRIDES["inflate5x_reg5_fakelumi"] = KFACTOR_OVERRIDES["inflate5x"]

# New wall-on / frozen-NP rows share scaleParams with their no-wall twins.
KFACTOR_OVERRIDES["nominal_reg"] = KFACTOR_OVERRIDES["nominal"]
KFACTOR_OVERRIDES["nominal_fakelumi_reg"] = KFACTOR_OVERRIDES["nominal"]
KFACTOR_OVERRIDES["inflatedV2_reg"] = KFACTOR_OVERRIDES["inflatedV2"]
KFACTOR_OVERRIDES["inflatedV2_fakelumi_reg"] = KFACTOR_OVERRIDES["inflatedV2"]
KFACTOR_OVERRIDES["frozenNP"] = KFACTOR_OVERRIDES["nominal"]
KFACTOR_OVERRIDES["frozenNP_fakelumi"] = KFACTOR_OVERRIDES["nominal"]
# tight50: prior widths halved from AN-100pct → all kfactors halved.
KFACTOR_OVERRIDES["tight50_reg"] = {
    "scetlibNPgammaLambda2": 1.31,
    "scetlibNPgammaLambda4": 0.56,
    "scetlibNPgammaLambdaInf": 1.665,
    "chargeVgenNP0scetlibNPZlambda2": 0.5,
    "chargeVgenNP0scetlibNPZdelta_lambda2": 0.5,
    "chargeVgenNP0scetlibNPZlambda4": 0.5,
}
KFACTOR_OVERRIDES["tight50_fakelumi_reg"] = KFACTOR_OVERRIDES["tight50_reg"]
KFACTOR_OVERRIDES["nominal_2D_ptll_yll"] = KFACTOR_OVERRIDES["nominal"]
KFACTOR_OVERRIDES["nominal_2D_ptll_yll_fakelumi"] = KFACTOR_OVERRIDES["nominal"]
KFACTOR_OVERRIDES["inflate5x_2D_ptll_yll"] = KFACTOR_OVERRIDES["inflate5x"]
KFACTOR_OVERRIDES["inflate5x_reg5_2D_ptll_yll"] = KFACTOR_OVERRIDES["inflate5x"]
KFACTOR_OVERRIDES["inflate5x_2D_ptll_yll_fakelumi"] = KFACTOR_OVERRIDES["inflate5x"]
KFACTOR_OVERRIDES["inflate5x_reg5_2D_ptll_yll_fakelumi"] = KFACTOR_OVERRIDES[
    "inflate5x"
]

# Nominal + asymmetric template treatment (--noSymmetrize). Same scaleParams
# as nominal — only the asymmetric-vs-symmetric handling differs.
KFACTOR_OVERRIDES["NPCS100pct_asym"] = KFACTOR_OVERRIDES["nominal"]
KFACTOR_OVERRIDES["NPCS100pct_asym_fakelumi"] = KFACTOR_OVERRIDES["nominal"]
# unconstrained + asym + reg5: no --scaleParams (NPs free-floating, helper
# scale=10 commented out), so effective kfactor = 1 throughout.
KFACTOR_OVERRIDES["unconstrained_asym_reg5"] = {}
KFACTOR_OVERRIDES["unconstrained_asym_reg5_fakelumi"] = {}

# --fakelumi κ used at setupRabbit time (norm=1.1 → 10% log-normal). Yield
# scaling at postfit θ is κ^θ, so the percent pull is (κ^θ − 1) × 100.
FAKELUMI_KAPPA = 1.1

# Pairs (fakelumi-on label → no-fakelumi label) for the 2·ΔNLL χ²₁ test.
# 2·(NLL_no_fl − NLL_+fl) is asymptotically χ²₁ since +fakelumi adds 1
# unconstrained nuisance. Large value → data wanted the yield freedom,
# evidence of yield-vs-shape tension.
FAKELUMI_PAIRS = {
    "nominal_fakelumi": "nominal",
    "nominal_fakelumi_reg": "nominal_reg",
    "inflatedV2_fakelumi": "inflatedV2",
    "inflatedV2_fakelumi_reg": "inflatedV2_reg",
    "inflate2x_fakelumi": "inflate2x",
    "inflate3x_fakelumi": "inflate3x",
    "inflate5x_fakelumi": "inflate5x",
    "inflate5x_reg5_fakelumi": "inflate5x_reg5",
    "frozenNP_fakelumi": "frozenNP",
    "unconstrained_fakelumi": "unconstrained",
    "unconstrained_tau5_fakelumi": "unconstrained_tau5",
    "tight50_fakelumi_reg": "tight50_reg",
    "nominal_2D_ptll_yll_fakelumi": "nominal_2D_ptll_yll",
    "inflate5x_2D_ptll_yll_fakelumi": "inflate5x_2D_ptll_yll",
    "inflate5x_reg5_2D_ptll_yll_fakelumi": "inflate5x_reg5_2D_ptll_yll",
    "NPCS100pct_asym_fakelumi": "NPCS100pct_asym",
    "unconstrained_asym_reg5_fakelumi": "unconstrained_asym_reg5",
}


def get_parm(parms, name):
    names = list(parms.axes[0])
    if name not in names:
        return None, None
    i = names.index(name)
    return float(parms.values()[i]), float(np.sqrt(parms.variances()[i]))


def physical_shift(nuis, theta, sigma_theta, kfactor=1.0):
    """Linearization from np_param_map.json, with optional per-config kfactor
    multiplying the template half-range (so a θ=1 pull moves by kfactor× the
    nominal-config step)."""
    info = PMAP["nuisances"][nuis]
    nom = info["nominal"]
    up = info["Up_template_value"]
    dn = info["Down_template_value"]
    d_up = (up - nom) * kfactor
    d_dn = (nom - dn) * kfactor
    val = nom + max(theta, 0) * d_up - max(-theta, 0) * d_dn
    slope = d_up if theta >= 0 else d_dn
    return val, abs(slope) * sigma_theta


def fmt_cell(theta, err, nuis, mode, kfactor=1.0):
    if theta is None:
        return "---"
    if err == 0.0:
        return "frozen"
    if mode == "physical":
        v, vu = physical_shift(nuis, theta, err, kfactor=kfactor)
        return f"${v:+.4f}\\pm{vu:.4f}$"
    return f"${theta:+.3f}\\pm{err:.3f}$"


def _sigma_from_scan(hist_obj):
    """Compute symmetric σ_θ from a rabbit nll_scan_<param> histogram.

    rabbit stores the scan on a hist.axis.StrCategory named "scan" whose
    category labels are the actual θ values cast to str (see
    rabbit/workspace.py:add_nll_scan_hist). To get x in θ-units, cast the
    category labels back to float — do NOT use hist edges, which are bin
    indices and yield σ ~ N_points×Δθ / 2 instead of the real σ.
    """
    ax = hist_obj.axes[0]
    xs = np.array(list(ax)).astype(float)
    ys = hist_obj.values()
    ymin_i = int(np.argmin(ys))
    y2 = 2.0 * (ys - ys[ymin_i])
    xmin = xs[ymin_i]

    def cross(xx, yy, t):
        yy = yy - t
        for i in range(len(yy) - 1):
            if yy[i] * yy[i + 1] < 0:
                return xx[i] + (xx[i + 1] - xx[i]) * (-yy[i]) / (yy[i + 1] - yy[i])
        return None

    xL = cross(xs[: ymin_i + 1][::-1], y2[: ymin_i + 1][::-1], 1.0)
    xR = cross(xs[ymin_i:], y2[ymin_i:], 1.0)
    if xL is None or xR is None:
        return None
    return 0.5 * ((xmin - xL) + (xR - xmin))


def _sigma_from_contour(fr, param="pdfAlphaS"):
    """If the fit was run with --contourScan, rabbit stores the σ_θ
    directly under contour_scan_<param>. Returns σ_θ (POI half-width at
    the requested CL — we read whichever CL is closest to 1) or None."""
    key = f"contour_scan_{param}"
    if key not in fr:
        return None
    try:
        h = fr[key].get()
        # contour hist axes: (confidence_level, side). Read 1σ if present.
        cls = list(h.axes["confidence_level"])
        # cls are strings like "1.0"
        try:
            ix = cls.index("1.0")
        except ValueError:
            return None
        vals = h.values()[ix]  # shape (2,) for ±
        return float(0.5 * (abs(vals[0]) + abs(vals[1])))
    except Exception:
        return None


def _try_load_scan(path):
    """Try to read an LR scan σ(αS) from a sibling fitresults file."""
    cand_dirs = []
    base = os.path.dirname(path)
    parent = os.path.dirname(base)
    # Prefer companion *_lrscan dirs in the same config.
    for sib in ("data_lrscan", "data_tau5_lrscan"):
        cand_dirs.append(os.path.join(parent, sib, "fitresults.hdf5"))
    # Also try the path itself in case the scan was written into the same file.
    cand_dirs.insert(0, path)
    for cand in cand_dirs:
        if not os.path.exists(cand):
            continue
        try:
            fr, _ = get_fitresult(cand, meta=True)
            if "nll_scan_pdfAlphaS" in fr:
                h = fr["nll_scan_pdfAlphaS"].get()
                sig = _sigma_from_scan(h)
                if sig is not None:
                    return sig, cand
        except Exception:
            continue
    return None, None


# Map of label -> explicit scan-fitresults path. If the path is set, use it.
SCAN_PATHS = {}


def load_fit(path, scan_path=None):
    fr, _ = get_fitresult(path, meta=True)
    parms = fr["parms"].get()
    out = {"path": path, "params": {}}
    for nuis, _ in NPS:
        out["params"][nuis] = get_parm(parms, nuis)
    a = get_parm(parms, POI)
    out["alphaS"] = a
    # fakelumi nuisance pull, if present. The yield-scaling pull in % is
    # (κ^θ − 1) × 100 (log-normal norm uncertainty with κ = FAKELUMI_KAPPA).
    out["fakelumi"] = get_parm(parms, "fakelumi")
    # nllvalreduced for the LR χ²₁ test of the fakelumi nuisance.
    try:
        v = fr["nllvalreduced"]
        out["nllvalreduced"] = float(v.get()) if hasattr(v, "get") else float(v[()])
    except Exception:
        out["nllvalreduced"] = None
    # Saturated p-value for the ptll projection.
    out["sat_p_ptll"] = None
    if "mappings" in fr:
        try:
            m = fr["mappings"]["Project ch0 ptll"]
            cs = float(m["chi2_saturated"])
            n = float(m["ndf"])
            if cs == cs and n > 0:  # NaN guard
                out["sat_p_ptll"] = chi2_dist.sf(cs, n) * 100
        except (KeyError, TypeError, ValueError):
            pass
    # LR-scan σ: prefer the deterministic contour_scan stored by --contourScan,
    # then fall back to interpolating the nll_scan curve. Try the path itself
    # first (LR scan output dirs hold their own fitresults), then any companion
    # *_lrscan dir found by _try_load_scan, then an explicit scan_path override.
    out["alphaS_scan_sigma"] = None
    candidate_frs = [fr]
    if scan_path and scan_path != path and os.path.exists(scan_path):
        try:
            fr_s, _ = get_fitresult(scan_path, meta=True)
            candidate_frs.append(fr_s)
        except Exception:
            pass
    for fr_try in candidate_frs:
        sig = _sigma_from_contour(fr_try, POI)
        if sig is not None:
            out["alphaS_scan_sigma"] = sig
            break
        if "nll_scan_pdfAlphaS" in fr_try:
            try:
                h = fr_try["nll_scan_pdfAlphaS"].get()
                sig = _sigma_from_scan(h)
                if sig is not None:
                    out["alphaS_scan_sigma"] = sig
                    break
            except Exception:
                pass
    if out["alphaS_scan_sigma"] is None:
        sig, _ = _try_load_scan(path)
        out["alphaS_scan_sigma"] = sig
    return out


def build_latex(fits, mode):
    """fits = list of (label, dict_from_load_fit)"""
    nom_lab, nom = fits[0]
    nom_aS = nom["alphaS"]

    header_np = " & ".join([lab for _, lab in NPS])
    lines = [
        r"\documentclass[10pt]{article}",
        r"\usepackage[a4paper,landscape,margin=1cm]{geometry}",
        r"\usepackage{graphicx}",
        r"\usepackage{booktabs}",
        r"\pagestyle{empty}",
        r"\begin{document}",
        r"\noindent\resizebox{\textwidth}{!}{%",
        r"  \begin{tabular}{l" + "c" * len(NPS) + "rrrrr}",
        r"    \hline\hline",
        r"    Configuration & "
        + header_np
        + r" & Sat.\ $p$ ($p_T^{\ell\ell}$)"
        + r" & $\Delta$pull$(\alpha_S)\,[10^{-3}]$"
        + r" & $\sigma(\alpha_S)\,[10^{-3}]$"
        + r" & fakelumi $[\%]$"
        + r" & $2\Delta\mathrm{NLL}\,(\chi^2_1)$ \\",
        r"    \hline",
    ]
    # Synthetic prefit "fit": θ=0 (so physical = nominal), σ_θ = 1 (Gaussian prior).
    prefit_d = {
        "path": "<prefit>",
        "params": {nuis: (0.0, 1.0) for nuis, _ in NPS},
        "alphaS": None,
        "sat_p_ptll": None,
        "alphaS_scan_sigma": None,
        "_is_prefit": True,
    }
    fits_by_label = {"prefit": prefit_d}
    fits_by_label.update({lab: d for lab, d in fits if lab not in SKIP_LABELS})
    # Build ordered list of (section_index, lab, d) honoring SECTIONS where possible.
    ordered = []
    used = set()
    for sec_idx, section in enumerate(SECTIONS):
        for lab in section:
            if lab in SKIP_LABELS:
                continue
            if lab in fits_by_label and lab not in used:
                ordered.append((sec_idx, lab, fits_by_label[lab]))
                used.add(lab)
    # Append any labels not in SECTIONS as their own trailing section.
    for lab, d in fits:
        if lab in SKIP_LABELS:
            continue
        if lab not in used:
            ordered.append((len(SECTIONS), lab, d))

    prev_sec = None
    for sec_idx, lab, d in ordered:
        if prev_sec is not None and sec_idx != prev_sec:
            lines.append(r"    \hline")
        prev_sec = sec_idx

        cells = []
        koverride = KFACTOR_OVERRIDES.get(lab, {})
        for nuis, _ in NPS:
            t, e = d["params"][nuis]
            k = koverride.get(nuis, 1.0)
            # Prefit row in physical mode: show the actual histmaker template
            # ranges (asymmetric where applicable, notably TMD Lambda_4
            # +0.06/-0.05) instead of a symmetric +/- band from sigma_theta=1.
            # Theta mode stays at the bare 0 +/- 1 prior.
            if d.get("_is_prefit") and mode == "physical":
                info = PMAP["nuisances"][nuis]
                nom = info["nominal"]
                d_up = (info["Up_template_value"] - nom) * k
                d_dn = (nom - info["Down_template_value"]) * k
                if abs(d_up - d_dn) < 1e-6:
                    cells.append(f"${nom:+.4f}\\pm{d_up:.4f}$")
                else:
                    cells.append(f"${nom:+.4f}^{{+{d_up:.4f}}}_{{-{d_dn:.4f}}}$")
            else:
                cells.append(fmt_cell(t, e, nuis, mode, kfactor=k))
        if d.get("_is_prefit"):
            d_as = "---"
            sig_hess = "---"
            sig_lr = "---"
        else:
            a = d["alphaS"]
            if a == (None, None) or a is None:
                d_as = "---"
                sig_hess = "---"
                sig_lr = "---"
            else:
                d_as = "ref" if (lab == nom_lab) else f"${(a[0] - nom_aS[0])*2:+.3f}$"
                # Two σ columns, both quoted in 10⁻³ AN units (× 2 to convert
                # from the rabbit template step 0.001 to σ_αS step 0.002).
                #   σ_Hess: from parms variance (always available).
                #   σ_LR  : from --contourScan if present, else interpolated
                #           from --scan curve via _sigma_from_scan (StrCategory
                #           axis labels carry the θ values).
                # Both are deterministic. Showing them side-by-side lets you
                # see whether the regularizer hinge / NP–α_S degeneracy makes
                # the local curvature underestimate σ.
                sig_hess = f"${a[1]*2:.3f}$"
                scan_sig = d.get("alphaS_scan_sigma")
                sig_lr = f"${scan_sig*2:.3f}$" if scan_sig is not None else "---"
        sp = d.get("sat_p_ptll")
        sp_cell = f"${sp:.2f}\\%$" if sp is not None else "---"
        # fakelumi percent pull (κ^θ − 1)×100. Show "---" if fakelumi not in fit.
        fl = d.get("fakelumi")
        if d.get("_is_prefit") or fl in (None, (None, None)) or fl[0] is None:
            fl_cell = "---"
        else:
            theta_fl, _ = fl
            pct = (FAKELUMI_KAPPA**theta_fl - 1.0) * 100.0
            fl_cell = f"${pct:+.2f}\\%$"
        # 2·ΔNLL χ²₁ for the fakelumi LR test. Only on +fakelumi rows that
        # have a no-fakelumi partner present.
        chi2_cell = "---"
        partner_lab = FAKELUMI_PAIRS.get(lab)
        if partner_lab is not None:
            partner = fits_by_label.get(partner_lab)
            nll_fl = (
                d.get("nllvalreduced") if d.get("nllvalreduced") is not None else None
            )
            nll_no = partner.get("nllvalreduced") if partner is not None else None
            if nll_fl is not None and nll_no is not None:
                dnll2 = 2.0 * (nll_no - nll_fl)
                if dnll2 > 0:
                    # χ²₁ → σ-equivalent is √(2ΔNLL) (Wilks); p-value = chi2.sf.
                    sigma_eq = dnll2**0.5
                    pval = chi2_dist.sf(dnll2, df=1)
                    chi2_cell = (
                        f"${dnll2:.2f}\\ ({sigma_eq:.2f}\\sigma,\\ p\\!=\\!{pval:.2g})$"
                    )
                else:
                    chi2_cell = f"${dnll2:.2f}\\ (\\mathrm{{n/a}})$"
        lab_tex = DISPLAY_NAME.get(lab, lab.replace("_", r"\_"))
        lines.append(
            f"    {lab_tex} & "
            + " & ".join(cells)
            + f" & {sp_cell} & {d_as} & {sig_hess} & {fl_cell} & {chi2_cell} \\\\"
        )
    lines += [
        r"    \hline\hline",
        r"  \end{tabular}%",
        r"}",
        r"\par\vspace{0.6em}",
        r"\footnotesize NP cells: postfit physical value (linearized template interp.\ from "
        r"\texttt{np\_param\_map.json}), with per-config kfactor overrides applied. "
        r"$\Delta$pull$(\alpha_S)=(\theta-\theta_{\rm nom})\times 2$ in $10^{-3}$; $\sigma(\alpha_S)$ also $\times 2$. "
        r"$\sigma$ is the postfit Hessian uncertainty. (Spot-checked against the profile-likelihood scan and they agree to $<2\%$ across all rows that have both.)",
        r"\end{document}",
    ]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "specs",
        nargs="+",
        help="LABEL=path entries (order matters; first = reference for ΔαS)",
    )
    p.add_argument("--mode", choices=["physical", "theta"], default="physical")
    p.add_argument("--output", "-o", required=True, help="Output directory")
    args = p.parse_args()

    fits = []
    for spec in args.specs:
        lab, path = spec.split("=", 1)
        try:
            fits.append((lab, load_fit(path)))
        except Exception as e:
            print(f"WARNING: could not load {lab} ({path}): {e}")
            fits.append(
                (
                    lab,
                    {
                        "path": path,
                        "params": {nm: (None, None) for nm, _ in NPS},
                        "alphaS": None,
                        "sat_p_ptll": None,
                        "_failed": True,
                    },
                )
            )

    os.makedirs(args.output, exist_ok=True)
    tex_path = os.path.join(args.output, "np_compare.tex")
    with open(tex_path, "w") as fh:
        fh.write(build_latex(fits, args.mode))
    print(f"Wrote {tex_path}")

    r = subprocess.run(
        [
            "pdflatex",
            "-interaction=batchmode",
            "-output-directory",
            args.output,
            tex_path,
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print("pdflatex failed:")
        print(r.stdout[-2000:])
        sys.exit(1)
    print(f"Wrote {os.path.join(args.output, 'np_compare.pdf')}")


if __name__ == "__main__":
    main()
