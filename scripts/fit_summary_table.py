#!/usr/bin/env python3
"""Cross-run fit-output summary table (LaTeX + pdf) from rabbit fitresults.

For each run directory, discovers every fitresults*.hdf5 (including the
cov/ merged/ saturated/ subdirs of the fitterSCETlibNP.py split workflow),
groups them into chains (fit pass = root; hessian/saturated/merged passes
attach to it via their --externalPostfit path), and tabulates per chain:

  * postfit NP lambdas (with postfit sigma where a cov-bearing pass exists,
    "(frozen)" where the fit froze them),
  * EDM of the fit pass (falling back to any later pass that recomputed it),
  * sigma(pdfAlphaS) from the cov-bearing pass, "---" if none exists,
  * the ptll-projection saturated-test chi2/ndf and p-value, "---" if the
    saturated pass is missing.

Runs outside the container: only rabbit + wums + the import-light
wremnants...scetlib_np.params are needed (no TF).

Usage::

    # opaque dir-basename labels:
    python3 scripts/fit_summary_table.py <run_dir> [<run_dir> ...] \
        -o ~/public_html/alphaS/260710_fit_summary/ [--compile]

    # descriptive labels from a YAML/JSON spec ({name: dir} or [{name,dir},...]):
    python3 scripts/fit_summary_table.py --spec runs.yaml \
        -o ~/public_html/alphaS/260710_fit_summary/ [--compile]
"""

import argparse
import datetime
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_WREM = os.environ.get(
    "WREM_BASE", os.path.join(os.path.dirname(os.path.dirname(_HERE)), "WRemnants")
)
for sub in ("", "rabbit", "wums"):
    p = os.path.join(_WREM, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

# Read fitresults even while a fit still holds the file lock (in-progress jobs):
# disable HDF5 file locking for our read-only opens. Must precede the h5py import.
os.environ.setdefault("HDF5_USE_FILE_LOCKING", "FALSE")
try:  # register blosc/lz4 hdf5 filters if present (some fitresults need them)
    import hdf5plugin  # noqa: F401
except ImportError:
    pass

import numpy as np
from scipy import stats

from rabbit import io_tools
from wremnants.postprocessing.scetlib_np.params import ALL_PARAMS

ALPHAS = "pdfAlphaS"
SAT_MAPPING = "Project ch0 ptll"


def frozen_matcher(freeze_exprs):
    """rabbit's --freezeParameters semantics: exact name OR anchored re.match."""
    if not freeze_exprs:
        return lambda name: False
    exact = set(freeze_exprs)
    compiled = [re.compile(e) for e in freeze_exprs]
    return lambda name: (name in exact) or any(r.match(name) for r in compiled)


def read_file(path):
    """One fitresults file -> flat record of everything the table needs."""
    fitresult, meta = io_tools.get_fitresult(path, meta=True)
    args = (meta.get("meta_info", {}) or {}).get("args", {}) or {}

    parms = fitresult["parms"].get()
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in parms.axes[0]]
    values = parms.values()
    variances = parms.variances()
    idx = {n: i for i, n in enumerate(names)}

    def val_sig(name):
        if name not in idx:
            return None
        i = idx[name]
        v = float(values[i])
        s = float("nan")
        if variances is not None and np.isfinite(variances[i]) and variances[i] >= 0:
            s = math.sqrt(float(variances[i]))
        return v, s

    sat = None
    mappings = fitresult.get("mappings") or {}
    if SAT_MAPPING in mappings and "chi2_saturated" in mappings[SAT_MAPPING]:
        m = mappings[SAT_MAPPING]
        sat = (float(m["chi2_saturated"]), int(m["ndf_saturated"]))

    ext = args.get("externalPostfit")
    if isinstance(ext, bytes):
        ext = ext.decode()

    reg = args.get("regularization") or []
    wall = any("NPDampingWall" in str(spec) for spec in reg)

    return {
        "parms_hash": hashlib.sha1(np.ascontiguousarray(values).tobytes()).hexdigest(),
        "nllvalreduced": fitresult.get("nllvalreduced"),
        "nllvalfull": fitresult.get("nllvalfull"),
        "ndfsat": fitresult.get("ndfsat"),
        "wall": wall,
        "wall_strength": args.get("regularizationStrength") if wall else None,
        "path": path,
        "edm": fitresult.get("edmval"),
        # A "fit pass" (chain root) RAN the minimizer; cov/saturated/merged passes
        # reuse a postfit via --externalPostfit --noFit and attach to it. Key on
        # noFit, NOT on ext being None: a SEEDED fit (--externalPostfit + a real
        # minimization, e.g. our walled-seeded C / funcbound runs) is a root too.
        "is_fit_pass": not bool(args.get("noFit", False)),
        "external_postfit": os.path.normpath(ext) if ext else None,
        "toy": (args.get("toys") or [None])[0],
        "freeze": args.get("freezeParameters") or [],
        "params": {n: val_sig(n) for n in list(ALL_PARAMS) + [ALPHAS]},
        "has_cov": not math.isnan((val_sig(ALPHAS) or (0, float("nan")))[1]),
        "sat": sat,
    }


def discover(run_dir):
    """All fitresults*.hdf5 in run_dir and its immediate subdirs."""
    out = []
    for root, dirs, files in os.walk(run_dir):
        depth = os.path.relpath(root, run_dir).count(os.sep)
        if depth >= 1:
            dirs[:] = []
        out += [os.path.join(root, f) for f in files if f.endswith(".hdf5")]
    return sorted(out)


def build_chains(run_dir):
    """Group the run's files into (root fit pass, attached passes) chains."""
    records = {}
    for path in discover(run_dir):
        try:
            records[os.path.normpath(path)] = read_file(path)
        except Exception as e:
            msg = str(e).lower()
            if any(
                s in msg
                for s in ("lock", "bad object header", "not in h5file", "truncated")
            ):
                print(
                    f"NOTE: {path}: in progress / no results yet — skipped",
                    file=sys.stderr,
                )
            else:
                print(f"WARNING: could not read {path}: {e}", file=sys.stderr)

    roots = {p: r for p, r in records.items() if r["is_fit_pass"]}
    chains = {p: [r] for p, r in roots.items()}
    for p, r in records.items():
        if r["is_fit_pass"]:
            continue
        # follow externalPostfit (one indirection is enough: every split-workflow
        # pass points straight at the fit pass), fall back to basename match
        target = r["external_postfit"]
        if target not in chains:
            matches = [
                q
                for q in chains
                if os.path.basename(q) == os.path.basename(target or "")
            ]
            target = matches[0] if len(matches) == 1 else None
        if target in chains:
            chains[target].append(r)
        else:
            print(
                f"WARNING: {p} externalPostfits {r['external_postfit']} which is "
                "not among the discovered fit passes; skipped",
                file=sys.stderr,
            )

    # collapse duplicate roots at the bit-identical postfit point (file copies
    # made to satisfy tool naming conventions, e.g. fitresults.hdf5 aliasing
    # fitresults_t0.hdf5); their attached passes join the surviving chain
    by_hash = {}
    for p in sorted(chains):
        h = records[p]["parms_hash"]
        if h in by_hash:
            keeper = by_hash[h]
            chains[keeper].extend(chains[p][1:])
            print(
                f"NOTE: {p} is the same postfit point as {keeper}; chains merged",
                file=sys.stderr,
            )
            del chains[p]
        else:
            by_hash[h] = p
    return chains


def summarize_chain(root_path, chain):
    root = chain[0]
    is_frozen = frozen_matcher(root["freeze"])
    cov_rec = next((r for r in chain if r["has_cov"]), None)
    sat_rec = next((r for r in chain if r["sat"]), None)

    edm, edm_src = root["edm"], "fit"
    if edm is None:
        alt = next((r for r in chain if r["edm"] is not None), None)
        if alt:
            edm, edm_src = alt["edm"], os.path.relpath(
                alt["path"], os.path.dirname(root_path)
            )

    params = {}
    for name in list(ALL_PARAMS) + [ALPHAS]:
        best = (cov_rec or root)["params"][name] or root["params"][name]
        if best is None:
            params[name] = None
            continue
        v, s = best
        params[name] = {"value": v, "sigma": s, "frozen": is_frozen(name)}

    suffix = re.sub(r"^fitresults_?|\.hdf5$", "", os.path.basename(root_path))
    label = os.path.basename(os.path.dirname(os.path.normpath(root_path)))
    if label in ("cov", "merged", "saturated"):
        label = os.path.basename(
            os.path.dirname(os.path.dirname(os.path.normpath(root_path)))
        )
    if suffix and suffix not in ("t0",):
        label += f" [{suffix}]"
    if root["toy"] == -1:
        label += " (Asimov)"

    sat_chi2, sat_ndf, sat_p = None, None, None
    if sat_rec:
        sat_chi2, sat_ndf = sat_rec["sat"]
        sat_p = float(stats.chi2.sf(sat_chi2, sat_ndf))

    # full saturated-model GOF of the fit itself: 2*nll relative to saturated
    full_chi2, full_ndf, full_p = None, None, None
    if root["nllvalreduced"] is not None and root["ndfsat"]:
        full_chi2 = 2 * float(root["nllvalreduced"])
        full_ndf = int(root["ndfsat"])
        full_p = float(stats.chi2.sf(full_chi2, full_ndf))

    # full NLL (constant terms included): only stored when the pass ran with
    # --fullNll; any pass in the chain evaluates at the same postfit point
    nll_full = next(
        (r["nllvalfull"] for r in chain if r["nllvalfull"] is not None), None
    )

    return {
        "wall": root["wall"],
        "wall_strength": root["wall_strength"],
        "full_chi2": full_chi2,
        "full_ndf": full_ndf,
        "full_p": full_p,
        "nll_full": nll_full,
        "label": label,
        "params": params,
        "edm": edm,
        "edm_src": edm_src,
        "sigma_alphaS": params[ALPHAS]["sigma"] if params[ALPHAS] else float("nan"),
        "alphaS": params[ALPHAS]["value"] if params[ALPHAS] else float("nan"),
        "sat_chi2": sat_chi2,
        "sat_ndf": sat_ndf,
        "sat_p": sat_p,
        "missing_cov": cov_rec is None,
        "missing_sat": sat_rec is None,
        "files": [r["path"] for r in chain],
    }


# ---------------------------------------------------------------------------
# LaTeX
# ---------------------------------------------------------------------------


def tex_escape(s):
    """Escape underscores OUTSIDE $...$ math, leaving math segments verbatim — so a
    label can carry real subscripts (e.g. ``$F_{eff}$``, ``$\\Delta\\lambda_2$``)
    while a plain dir-basename label still gets its ``_`` escaped."""
    parts = s.split("$")
    for i in range(0, len(parts), 2):  # even segments are outside math
        parts[i] = parts[i].replace("_", r"\_")
    return "$".join(parts)


LAMBDA_HEADERS = {
    "lambda2_nu": r"$\lambda_2^\nu$",
    "lambda4_nu": r"$\lambda_4^\nu$",
    "lambda6_nu": r"$\lambda_6^\nu$",
    "lambda_inf_nu": r"$\lambda_\infty^\nu$",
    "lambda2": r"$\lambda_2$",
    "lambda4": r"$\lambda_4$",
    "lambda6": r"$\lambda_6$",
    "delta_lambda2": r"$\delta\lambda_2$",
    "lambda_inf": r"$\lambda_\infty$",
}


def fmt_lambda(p):
    if p is None:
        return "---"
    if p["frozen"]:
        return f"{p['value']:.3g}\\,(fr.)"
    if math.isnan(p["sigma"]):
        return f"{p['value']:+.3f}"
    return f"{p['value']:+.3f} $\\pm$ {p['sigma']:.3f}"


def fmt_edm(edm, src):
    if edm is None:
        return "---"
    s = f"{edm:.1e}"
    if src != "fit":
        s += r"\,\dag"
    if edm > 1e-3:
        s = r"\textbf{" + s + "}"
    return s


def make_tex(rows):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lam_cols = " ".join(["l"] + ["r"] * len(ALL_PARAMS))
    lam_head = " & ".join(["run"] + [LAMBDA_HEADERS[n] for n in ALL_PARAMS])

    lam_body = []
    for r in rows:
        cells = [tex_escape(r["label"])] + [
            fmt_lambda(r["params"][n]) for n in ALL_PARAMS
        ]
        lam_body.append(" & ".join(cells) + r" \\")

    sum_body = []
    for r in rows:
        a = f"{r['alphaS']:+.3f}"
        sa = "---" if math.isnan(r["sigma_alphaS"]) else f"{r['sigma_alphaS']:.3f}"
        full = (
            f"{r['full_chi2']:.1f}/{r['full_ndf']}"
            if r["full_chi2"] is not None
            else "---"
        )
        fullp = f"{100 * r['full_p']:.0f}\\%" if r["full_p"] is not None else "---"
        sat = (
            f"{r['sat_chi2']:.1f}/{r['sat_ndf']}"
            if r["sat_chi2"] is not None
            else "---"
        )
        satp = f"{100 * r['sat_p']:.2f}\\%" if r["sat_p"] is not None else "---"
        # full NLL (constant terms included): only stored by --fullNll passes
        nllfull = f"{r['nll_full']:.1f}" if r["nll_full"] is not None else "---"
        sum_body.append(
            " & ".join(
                [
                    tex_escape(r["label"]),
                    a,
                    sa,
                    fmt_edm(r["edm"], r["edm_src"]),
                    nllfull,
                    full,
                    fullp,
                    sat,
                    satp,
                ]
            )
            + r" \\"
        )

    return rf"""\documentclass[10pt]{{article}}
\usepackage[a4paper,landscape,margin=0.8cm]{{geometry}}
\usepackage{{booktabs}}
\pagestyle{{empty}}
\begin{{document}}
\begin{{center}}\Large Fit-output summary \quad {{\normalsize (generated {now})}}\end{{center}}

\begin{{center}}\scriptsize
\begin{{tabular}}{{{lam_cols}}}
\toprule
{lam_head} \\
\midrule
{chr(10).join(lam_body)}
\bottomrule
\end{{tabular}}

\vspace{{1.5em}}
\small
\begin{{tabular}}{{lrrrrrrrr}}
\toprule
run & $\hat\theta_{{\alpha_S}}$ & $\sigma_{{\alpha_S}}$ & EDM & NLL (full) & full sat.\ $\chi^2$/ndf & $p$ & sat.\ $\chi^2$/ndf ($p_T^{{\ell\ell}}$) & sat.\ $p$-value \\
\midrule
{chr(10).join(sum_body)}
\bottomrule
\end{{tabular}}
\end{{center}}
\end{{document}}
"""


def load_runs(spec_path):
    """Parse a YAML/JSON run spec -> ordered list of (descriptive_name, dir).

    Accepts a list of ``{name, dir}`` (or ``[name, dir]``) entries, or a
    ``{name: dir}`` mapping. Order is preserved -> table row order."""
    with open(spec_path) as f:
        text = f.read()
    if spec_path.endswith((".yaml", ".yml")):
        try:
            import yaml
        except ImportError:
            sys.exit("PyYAML not available; use a JSON spec or `pip install pyyaml`.")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    runs = []
    if isinstance(data, dict):
        runs = [(str(k), str(v)) for k, v in data.items()]
    elif isinstance(data, list):
        for e in data:
            if isinstance(e, dict):
                runs.append((str(e["name"]), str(e["dir"])))
            elif isinstance(e, (list, tuple)) and len(e) == 2:
                runs.append((str(e[0]), str(e[1])))
            else:
                raise ValueError(
                    f"bad run entry (need {{name,dir}} or [name,dir]): {e!r}"
                )
    else:
        raise ValueError("spec must be a list of {name,dir} or a {name: dir} mapping")
    return runs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "run_dirs",
        nargs="*",
        default=[],
        help="fit output directories (row label = dir basename); or use --spec",
    )
    ap.add_argument(
        "--spec",
        default=None,
        help="YAML/JSON of runs with DESCRIPTIVE names: a {name: dir} mapping or a "
        "list of {name, dir}. Overrides the opaque dir-basename row labels.",
    )
    ap.add_argument("-o", "--outdir", required=True)
    ap.add_argument("--name", default="fit_summary", help="basename for .tex/.pdf")
    ap.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        metavar="SUBSTR",
        help="drop chains whose root fitresults path contains any of these substrings",
    )
    ap.add_argument("--compile", action="store_true", help="run pdflatex on the output")
    args = ap.parse_args()

    # (descriptive_name | None, dir): --spec gives names, positional dirs don't
    if args.spec:
        named = load_runs(args.spec)
    elif args.run_dirs:
        named = [(None, d) for d in args.run_dirs]
    else:
        ap.error("give one or more run_dirs, or --spec")

    rows = []
    for name, d in named:
        d = os.path.normpath(d)
        chains = build_chains(d)
        if not chains:
            print(f"WARNING: no fit passes found in {d}", file=sys.stderr)
        keep = [rp for rp in sorted(chains) if not any(s in rp for s in args.exclude)]
        # A named run should be one row: if a dir holds several fit chains (side
        # variants like *_newbtgrid, *_ptllSatTest), prefer the canonical output
        # and drop the rest. Point --spec dir at a specific *.hdf5 to override.
        if name is not None and len(keep) > 1:
            canon = [
                rp
                for rp in keep
                if os.path.basename(rp) in ("fitresults.hdf5", "fitresults_t0.hdf5")
            ]
            if canon:
                dropped = [os.path.basename(rp) for rp in keep if rp not in canon]
                print(
                    f"NOTE: {d}: multiple chains; using {[os.path.basename(rp) for rp in canon]}, dropping {dropped}",
                    file=sys.stderr,
                )
                keep = canon
        for i, root_path in enumerate(keep):
            row = summarize_chain(root_path, chains[root_path])
            if name is not None:  # descriptive name overrides the dir-basename label
                row["label"] = name if len(keep) == 1 else f"{name} [{i + 1}]"
            rows.append(row)

    command = "python3 " + " ".join(sys.argv)

    # console summary + what is missing
    for r in rows:
        missing = [
            w
            for w, m in (
                ("cov/sigma_alphaS", r["missing_cov"]),
                ("ptll sat test", r["missing_sat"]),
            )
            if m
        ]
        print(
            f"{r['label']}: alphaS={r['alphaS']:+.3f}",
            f"MISSING: {', '.join(missing)}" if missing else "complete",
        )

    os.makedirs(args.outdir, exist_ok=True)
    tex_path = os.path.join(args.outdir, args.name + ".tex")
    with open(tex_path, "w") as f:
        f.write(make_tex(rows))
    # .command.log, NOT .log — pdflatex writes <name>.log and would clobber it
    with open(os.path.join(args.outdir, args.name + ".command.log"), "w") as f:
        f.write(f"# {datetime.datetime.now().isoformat()}\n# {command}\n\n")
        for r in rows:
            f.write(f"{r['label']}:\n")
            for p in r["files"]:
                f.write(f"  {p}\n")
    print(f"\nWrote {tex_path}")

    if args.compile:
        try:
            res = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    args.name + ".tex",
                ],
                cwd=args.outdir,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            print(
                "WARNING: pdflatex not found (are you inside the container? it has no "
                "TeX). The .tex was written — compile it on a login node / outside "
                "the container, or drop --compile.",
                file=sys.stderr,
            )
            return
        if res.returncode != 0:
            print(res.stdout[-3000:], file=sys.stderr)
            sys.exit("pdflatex failed")
        for ext in (".aux",):
            try:
                os.remove(os.path.join(args.outdir, args.name + ext))
            except OSError:
                pass
        print(f"Wrote {os.path.join(args.outdir, args.name + '.pdf')}")
        # standard plot-browser index if the parent webdir uses one
        idx = os.path.join(args.outdir, "index.php")
        template = os.path.join(
            os.path.dirname(os.path.normpath(args.outdir)), "index.php"
        )
        if not os.path.exists(idx) and os.path.exists(template):
            shutil.copy(template, idx)


if __name__ == "__main__":
    main()
