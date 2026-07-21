#!/usr/bin/env python3
"""Run any subset of {fit, hessian, saturated} for the alphaS analysis with the
SCETlib NP param model, on a GIVEN DATACARD (make the card separately with
setupRabbit.py; the reference command is in the datacard's own meta_info).

Steps (any subset via --steps, always run in this order):

  fit       : rabbit_fit.py --paramModel ... --noHessian. EDM and POI+NOI
              uncertainties come from rabbit's Hessian-free CG path (no
              --noEDM; the exact Hessian OOMs through the bT-fold slab, see
              wremnants/postprocessing/scetlib_np/HESSIAN_PLAN.md). Writes
              <fitdir>/fitresults.hdf5.
  hessian   : straight-through Gauss-Newton cov pass on the fit postfit
              (--externalPostfit --noFit, hessian_straightthrough=1
              hessian_gn=1) + traditional impacts + postfit hists, including
              the ptll projection with errors (-m Project ch0 ptll — the
              projection only; the saturated REFIT stays in the saturated
              step, where it runs in exact mode and much faster). Writes
              <fitdir>/cov/fitresults.hdf5. (--globalImpacts is NOT used: it
              re-differentiates the yields through the param model and OOMs.)
  saturated : saturated likelihood test on the 1D ptll projection, on the fit
              postfit (--externalPostfit --noFit -m Project ch0 ptll). The
              2D/full set is prohibitively slow, same rationale as fitter.sh.
              Runs with --noHessian --noEDM --noChi2 (the saturated chi2 needs
              only the two NLLs; the linear chi2 would need the covariance
              this step deliberately does not compute). Writes
              <fitdir>/saturated/fitresults.hdf5.

To plot the banded postfit ptll WITH the saturated p-value, merge the two
outputs (the plotter reads hists and chi2 from ONE file):
    scripts/merge_fitresults_saturated.py <fitdir>/cov/fitresults.hdf5 \\
        <fitdir>/saturated/fitresults.hdf5 -o <fitdir>/merged/fitresults.hdf5

Param-model settings (which lambdas to freeze, priors, xparam_default, ...):
  --modelArgs appends spec tokens to --paramModel for the fit step, e.g.
    --modelArgs priors=1 prior_sigmas=lambda2_nu=0.15 xparam_default=lambda2_nu=0.15,lambda4_nu=0
  --freeze replaces the default --freezeParameters list.

NP damping wall (np_damping_wall.py): --wall adds the regularizer line
  -r ...NPDampingWall ...NPDampingMapping [extra tokens, e.g. --wall smallb=0]
with --regularizationStrength <--wallStrength, default 3>. Do NOT pass -r via
-f/--extraFit: that is appended to every step and would double-count the
penalty on top of the inherited one.

INHERITANCE: hessian and saturated recover the fit step's --paramModel spec
tokens, --freezeParameters, -t/--pseudoData and the regularization
(-r lines + --regularizationStrength, so a walled fit's cov pass and
saturated refit carry the same wall penalty in the loss) from
<fitdir>/fitresults.hdf5 meta_info (rabbit stores the full argparse namespace
there), so they always profile with the same configuration as the fit —
whether the fit ran in this invocation or an earlier one. A --modelArgs given
together with those steps is appended AFTER the inherited tokens (the model's
parse_args lets a later duplicate key win), and --freeze / --wall / DATA_ARGS
given explicitly override the inherited freeze list / regularization / data
args. Inherited spec tokens are sanitized:
hessian_straightthrough=/hessian_gn= (re-added where needed) and the removed
unfolding_hdf5_path= (pre-reorg fitresults; R now comes from the datacard's
scetlib_np auxiliary) are dropped. Pre-reorg fitresults that recorded the
paths POSITIONALLY cannot be inherited from (the model will fail loudly).

SCETlib bT grid: by default the model uses _default_btgrid_dir() (the FIXED
b0=1 grid; the old /ceph/.../zstuff grid is the buggy b0=0 one — see
studies/physical-lambda/LOGBOOK.md). Set BTGRID only to override.

RUN INSIDE the wmassdev container with /opt/venv activated and
WRemnants/setup.sh sourced (rabbit_fit.py and the meta reader need
tensorflow/rabbit/wums on PYTHONPATH).

Env overrides: BTGRID, DATA_ARGS (fit default '-t 0'; hessian/saturated
inherit from the fit postfit unless DATA_ARGS is set), MAXITER, THREADS.
"""

import argparse
import os
import shlex
import subprocess
import sys

MODEL = "wremnants.postprocessing.scetlib_np.SCETlibNPParamModel"
# floating lambdas with the default freeze: lambda2, lambda4, delta_lambda2, lambda2_nu
DEFAULT_FREEZE = ["lambda_inf", "lambda_inf_nu", "^scetlibNP.*"]
STEP_ORDER = ["fit", "hessian", "saturated"]
# NP damping wall (see np_damping_wall.py module docstring for the -r syntax)
WALL_REG = "wremnants.postprocessing.scetlib_np.np_damping_wall.NPDampingWall"
WALL_MAP = "wremnants.postprocessing.scetlib_np.np_damping_wall.NPDampingMapping"
# Named walls selectable as the FIRST --wall token, e.g. `--wall funcbound tcs=0.2
# ttmd=0.2`. Each entry is (regularizer_class, mapping_class). If the first --wall
# token is not a known name it defaults to 'damping' (so `--wall smallb=0` still
# works). All share --wallStrength and are inherited by hessian/saturated via meta.
WALLS = {
    "damping": (WALL_REG, WALL_MAP),
    "funcbound": (
        "wremnants.postprocessing.scetlib_np.np_function_bound.NPFunctionBound",
        "wremnants.postprocessing.scetlib_np.np_function_bound.NPFunctionBoundMapping",
    ),
}


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("card", help="datacard hdf5 (from setupRabbit.py)")
    p.add_argument(
        "-s",
        "--steps",
        default="fit,hessian,saturated",
        help="comma-separated subset of fit,hessian,saturated (default: all)",
    )
    p.add_argument(
        "-d",
        "--fitdir",
        default=None,
        help="fit output dir; relative paths nest under the datacard dir "
        "(default: the datacard dir itself). fit writes there, hessian "
        "writes <fitdir>/cov, saturated <fitdir>/saturated",
    )
    p.add_argument(
        "-m",
        "--modelArgs",
        nargs="+",
        default=[],
        metavar="TOKEN",
        help="extra --paramModel spec tokens, e.g. priors=1 "
        "prior_sigmas=lambda2_nu=0.15 xparam_default=lambda2_nu=0.15,lambda4_nu=0",
    )
    p.add_argument(
        "--freeze",
        nargs="+",
        default=None,
        metavar="NAME",
        help=f"--freezeParameters list (default: {' '.join(DEFAULT_FREEZE)})",
    )
    p.add_argument(
        "--wall",
        nargs="*",
        default=None,
        metavar="TOKEN",
        help="add an NP wall regularizer. Optional first token = wall name "
        f"({'/'.join(WALLS)}; default 'damping'); remaining tokens are the "
        "wall's options, e.g. `--wall smallb=0` (damping) or "
        "`--wall funcbound tcs=0.2 ttmd=0.2`. hessian/saturated inherit the "
        "fit's regularization from the postfit unless this is given explicitly",
    )
    p.add_argument(
        "--wallStrength",
        type=float,
        default=3.0,
        help="--regularizationStrength for --wall (penalty x exp(2*tau); " "default 3)",
    )
    p.add_argument(
        "-f",
        "--extraFit",
        default="",
        help="extra rabbit_fit.py args as one string, appended to every step "
        "(e.g. '--noEDM' to skip the CG EDM in the fit step)",
    )
    p.add_argument(
        "--dryRun", action="store_true", help="print the commands without running them"
    )
    args = p.parse_args()

    args.step_set = set()
    for step in args.steps.split(","):
        step = step.strip()
        if step not in STEP_ORDER:
            p.error(f"unknown step '{step}' (known: {','.join(STEP_ORDER)})")
        args.step_set.add(step)
    return args


def read_inherited(postfit):
    """(model_tokens, freeze, data_args, reg_args) recorded in the postfit's
    meta_info."""
    import h5py
    from wums import ioutils

    # read only the meta group directly: io_tools.get_fitresult would also
    # insist on a results group, whose name varies with the dataset (results,
    # results_asimov, results_nominal, ...)
    with h5py.File(postfit, "r") as f:
        # meta is written at startup, results* only at the very end — an
        # aborted fit leaves a meta-only stub that --externalPostfit would
        # later reject with a misleading error (see
        # knowledge/20_frameworks/nominal_workflow.md)
        if not any(k.startswith("results") for k in f.keys()):
            sys.exit(
                f"{postfit} has no results group (only {list(f.keys())}) — "
                "stale stub from an aborted fit; rerun the 'fit' step."
            )
        meta = ioutils.pickle_load_h5py(f["meta"])
    fit_args = (meta.get("meta_info", {}) or {}).get("args", {})

    pm = fit_args.get("paramModel") or []
    tokens = pm[0] if pm and isinstance(pm[0], (list, tuple)) else pm
    tokens = [t.decode() if isinstance(t, bytes) else str(t) for t in tokens]
    drop = ("hessian_straightthrough=", "hessian_gn=", "unfolding_hdf5_path=")
    tokens = [t for t in tokens if not t.startswith(drop)]
    if not tokens:
        sys.exit(f"no --paramModel recorded in {postfit} meta_info; cannot inherit")

    freeze = [str(x) for x in (fit_args.get("freezeParameters") or [])]

    data = []
    toys = fit_args.get("toys")
    if toys:
        data += ["-t", *[str(int(t)) for t in toys]]
    pseudo = fit_args.get("pseudoData")
    if pseudo:
        data += ["--pseudoData", *[str(x) for x in pseudo]]

    # regularization (-r is append+nargs -> list of token lists): the penalty
    # is part of the loss, so the cov pass and the saturated refit must carry
    # the same -r lines and strength as the fit
    reg = []
    for line in fit_args.get("regularization") or []:
        reg += ["-r", *[str(x) for x in line]]
    if reg:
        strength = fit_args.get("regularizationStrength", 0.0)
        reg += ["--regularizationStrength", str(float(strength))]
    return tokens, freeze, data, reg


def run(cmd, dry_run, cwd=None):
    print(" ".join(shlex.quote(c) for c in cmd), flush=True)
    if dry_run:
        return
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
    except subprocess.CalledProcessError as exc:
        sys.exit(f"Command failed (exit {exc.returncode}).")
    except FileNotFoundError:
        sys.exit(
            f"{cmd[0]} not found on PATH — run inside the wmassdev container "
            "with WRemnants/setup.sh sourced."
        )


def main():
    args = parse_args()

    card = os.path.realpath(args.card)
    if not os.path.isfile(card) and not args.dryRun:
        sys.exit(f"Datacard not found: {card}")
    wrem_base = os.environ.get("WREM_BASE")
    if not wrem_base:
        sys.exit("WREM_BASE is not set. Please source the setup.sh in WRemnants.")

    fitdir = args.fitdir or os.path.dirname(card)
    if not os.path.isabs(fitdir):  # relative: nest under the datacard dir
        fitdir = os.path.join(os.path.dirname(card), fitdir)
    os.makedirs(fitdir, exist_ok=True)
    fitdir = os.path.realpath(fitdir)
    print(f"Datacard: {card}")
    print(f"Fit dir : {fitdir}")
    print(f"Steps   : {','.join(s for s in STEP_ORDER if s in args.step_set)}")

    model_args = list(args.modelArgs)
    btgrid = os.environ.get("BTGRID")
    if btgrid:
        model_args = [f"btgrid_dir={btgrid}", *model_args]
    freeze = args.freeze if args.freeze is not None else list(DEFAULT_FREEZE)
    # fit-step dataset args; hessian/saturated inherit from the fit postfit
    # unless DATA_ARGS is set explicitly in the environment
    data_args_set = "DATA_ARGS" in os.environ
    data = shlex.split(os.environ.get("DATA_ARGS", "-t 0"))
    maxiter = os.environ.get("MAXITER", "1000")
    extra = shlex.split(args.extraFit)
    if "-r" in extra or "--regularization" in extra:
        sys.exit(
            "pass the regularizer via --wall, not -f/--extraFit: extraFit is "
            "appended to every step and would double-count the penalty on top "
            "of the inherited -r."
        )
    # NP damping wall regularizer (part of the loss -> must be identical in
    # every step; hessian/saturated inherit it from the fit postfit)
    wall = []
    if args.wall is not None:
        # First token selects the wall by name (default 'damping'); the rest are
        # that wall's option tokens. `--wall smallb=0` → damping + smallb=0.
        tokens = list(args.wall)
        name = tokens.pop(0) if (tokens and tokens[0] in WALLS) else "damping"
        reg_cls, map_cls = WALLS[name]
        # fmt: off
        wall = [
            "-r", reg_cls, map_cls, *tokens,
            "--regularizationStrength", str(args.wallStrength),
        ]
        # fmt: on

    threads = os.environ.get("THREADS")
    if threads:
        os.environ["OMP_NUM_THREADS"] = threads
        os.environ["TF_NUM_INTRAOP_THREADS"] = threads
        os.environ["TF_NUM_INTEROP_THREADS"] = "2"

    # ---- step: fit (+ Hessian-free CG EDM) -----------------------------------
    if "fit" in args.step_set:
        print("\nRunning step 'fit' (--noHessian; EDM via the Hessian-free CG path)...")
        # fmt: off
        run(
            [
                "rabbit_fit.py", card, "-v", "4",
                "--paramModel", MODEL, *model_args,
                "--freezeParameters", *freeze,
                *wall,
                "--minimizerMaxiter", maxiter,
                *data,
                "--noHessian",
                # store the full NLL (constant terms included) next to the
                # reduced one; one extra NLL eval, needed by fit_summary_table.py
                "--fullNll",
                "-o", fitdir, *extra,
            ],
            args.dryRun,
        )
        # fmt: on

    postfit = os.path.join(fitdir, "fitresults.hdf5")
    if args.step_set & {"hessian", "saturated"}:
        if os.path.isfile(postfit):
            in_model, in_freeze, in_data, in_reg = read_inherited(postfit)
            # explicit CLI/env settings override the inherited ones. --modelArgs
            # tokens are appended AFTER the inherited ones (later duplicate key
            # wins in the model's parse_args); tokens already recorded verbatim
            # (the same-invocation case) are skipped.
            in_model += [t for t in model_args if t not in in_model]
            if args.freeze is not None:
                in_freeze = freeze
            if args.wall is not None:
                in_reg = wall
            if data_args_set:
                in_data = data
            print(f"\nInherited from {postfit}:")
            print(f"  --paramModel        {' '.join(in_model)}")
            print(f"  --freezeParameters  {' '.join(in_freeze)}")
            print(f"  data args           {' '.join(in_data)}")
            print(f"  regularization      {' '.join(in_reg) or '(none)'}")
        elif args.dryRun:
            # dry run without a readable postfit: this invocation's settings
            in_model = [MODEL, *model_args]
            in_freeze, in_data, in_reg = freeze, data, wall
        else:
            sys.exit(f"Fit postfit {postfit} not found; run the 'fit' step first.")

    # ---- step: hessian (straight-through GN cov + impacts) -------------------
    # hessian_straightthrough=1 hessian_gn=1 (GN exact on Asimov) make the
    # Hessian and the hist errors/impacts differentiate through the compact J
    # path instead of the bT-fold slab.
    if "hessian" in args.step_set:
        print(
            "\nRunning step 'hessian' (straight-through GN cov pass: impacts, postfit hists)..."
        )
        # fmt: off
        run(
            [
                "rabbit_fit.py", card, "-v", "4",
                "--paramModel", *in_model, "hessian_straightthrough=1", "hessian_gn=1",
                "--freezeParameters", *in_freeze,
                *in_reg,
                "--externalPostfit", postfit, "--noFit",
                "--minimizerMaxiter", maxiter,
                *in_data,
                "--doImpacts",
                "-m", "Project", "ch0", "ptll",
                "--computeVariations", "--computeHistErrors", "--computeHistImpacts",
                "--saveHists", "--saveHistsPerProcess",
                "-o", os.path.join(fitdir, "cov"), *extra,
            ],
            args.dryRun,
            cwd=wrem_base,
        )
        # fmt: on

    # ---- step: saturated (ptll projection saturated test) --------------------
    # The saturated refit only minimizes (gradients, like the fit step) and
    # compares NLLs, so no Hessian/EDM/linear-chi2 is computed here.
    if "saturated" in args.step_set:
        print("\nRunning step 'saturated' (ptll projection saturated test)...")
        # fmt: off
        run(
            [
                "rabbit_fit.py", card, "-v", "4",
                "--paramModel", *in_model,
                "--freezeParameters", *in_freeze,
                *in_reg,
                "--externalPostfit", postfit, "--noFit",
                "--minimizerMaxiter", maxiter,
                *in_data,
                "--noHessian", "--noEDM", "--noChi2",
                "-m", "Project", "ch0", "ptll",
                "--computeSaturatedProjectionTests",
                "--saveHists",
                "-o", os.path.join(fitdir, "saturated"), *extra,
            ],
            args.dryRun,
            cwd=wrem_base,
        )
        # fmt: on

    print(f"\nDone. Outputs under {fitdir}:")
    if "fit" in args.step_set:
        print(f"  fit       : {fitdir}/fitresults.hdf5")
    if "hessian" in args.step_set:
        print(f"  hessian   : {fitdir}/cov/fitresults.hdf5")
    if "saturated" in args.step_set:
        print(f"  saturated : {fitdir}/saturated/fitresults.hdf5")


if __name__ == "__main__":
    main()
