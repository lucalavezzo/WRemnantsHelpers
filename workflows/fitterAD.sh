#!/bin/bash
# Run the fit with the scetlib_ad param model for the alphaS analysis

usage() {
    echo "Usage: fitterAD.sh <card> -c <cache_dir> -o <output_dir>"
    echo "-f <extra arguments for rabbit_fit.py> -p <postfix>"
    echo "--asimov <Asimov instead of real data>"
    echo "--wall <add the NP damping wall (C^2 ramp by default), tau=8>"
    echo "--tau-continuation <with --wall: run a tau=5 stage first, then tau=8 warm from it (opt-in)>"
    echo "--constraints <physical NP region as HARD constraints (NPDomainConstraints) under trust-constr; no wall, no preconditioner>"
    echo "--lattice <add the ASWZ lattice CS-kernel chi2 (LatticeCSTerm, LATFROZ_V3 defaults), tau=8>"
    echo "--computeSaturatedProjectionTests <also run the ptll projected-saturated test (as rabbit_fit's flag)>"
    echo "--saturated-from <fitresults> <with --constraints: skip the main fit, run only the saturated test from this fit>"
    echo ""
    echo "Canonical nominal fit (2026-10-20): fitterAD.sh <card> -c <cache> -o <out> -p <PF> --constraints [--lattice] \\"
    echo "    [--computeSaturatedProjectionTests] -f '<param-model tokens> -v 4'"
    echo "With --constraints the main fit + post-fit (Hessian, impacts, hists) is ONE call without the preconditioner ->"
    echo "fitresults_<PF>.hdf5. --computeSaturatedProjectionTests adds a second call that loads it and runs only the ptll"
    echo "saturated test (warm start, spectral preconditioner, gtol 1e-5) -> fitresults_<PF>_sat.hdf5."
    echo "-h, --help <show this help message>"
    exit 1
}

if [ -z "$1" ]; then
    usage
fi

card=$1
shift

do_asimov=false
do_wall=false
do_tau_continuation=false
do_constraints=false
do_lattice=false
do_saturated=false
saturated_from=""

PARSED=$(getopt -o c:o:f:p:h --long cache:,output:,extra-fit:,postfix:,asimov,wall,tau-continuation,no-tau-continuation,constraints,lattice,computeSaturatedProjectionTests,saturated-from:,help -- "$@")
if [[ $? -ne 0 ]]; then
    echo "Failed to parse arguments." >&2
    exit 1
fi
eval set -- "$PARSED"

while true; do
    case "$1" in
        -c|--cache)      cache="$2"; shift 2 ;;
        -o|--output)     output_dir="$2"; shift 2 ;;
        -f|--extra-fit)  extra_fit="$2"; shift 2 ;;
        -p|--postfix)    postfix="$2"; shift 2 ;;
        --asimov)        do_asimov=true; shift ;;
        --wall)          do_wall=true; shift ;;
        --tau-continuation) do_tau_continuation=true; shift ;;
        --no-tau-continuation) do_tau_continuation=false; shift ;;  # the default since 2026-10-08, kept for old commands
        --constraints)   do_constraints=true; shift ;;
        --lattice)       do_lattice=true; shift ;;
        --computeSaturatedProjectionTests) do_saturated=true; shift ;;
        --saturated-from) saturated_from="$2"; do_saturated=true; shift 2 ;;
        -h|--help)       usage ;;
        --)              shift; break ;;
        *)               echo "Unexpected option: $1" >&2; exit 1 ;;
    esac
done

if $do_constraints && $do_wall; then
    echo "--constraints and --wall are alternatives (hard constraints vs the penalty); pick one." >&2
    exit 1
fi

if [ -n "$saturated_from" ] && ! $do_constraints; then
    echo "--saturated-from needs --constraints (it is the separate saturated-test call of the constrained fit)." >&2
    exit 1
fi

if [ -z "$cache" ]; then
    echo "Cache directory is required. Use -c to specify it."
    exit 1
fi

# check if WREM_BASE is set
if [ -z "$WREM_BASE" ]; then
    echo "WREM_BASE is not set. Please source the setup.sh in WRemnants."
    exit 1
fi
# the param model needs the SCETlib autodiff build
if [ -z "$SCETLIB_BUILD" ]; then
    echo "SCETLIB_BUILD is not set. Please source the setup.sh in the scetlib-cms build."
    exit 1
fi

if [ -z "$output_dir" ]; then
    output_dir=$(dirname "$card")
fi
if [ ! -d "$output_dir" ]; then
    mkdir -p "$output_dir"
fi
echo "Output directory: $output_dir"

if $do_asimov; then
    toys="-t -1"
else
    toys="-t 0"
fi

wall_arg=""
wall_reg=""
if $do_wall; then
    wall=wremnants.postprocessing.scetlib_ad.np_damping_wall
    wall_reg="-r ${wall}.NPDampingWall ${wall}.NPDampingMapping margin=0"
    wall_arg="--regularizationStrength 8 $wall_reg"
fi

# Hard constraints (2026-10-15): the wall's own conditions as trust-constr inequality rows, so the
# physical NP region is enforced exactly with no penalty in the loss. Converges from the cold anchor
# (studies/trust-constr-nominal/261013-constraints-class-validation, V2: 104 it / 2.3 h). The
# tolerances are V2's; --earlyStopping -1 because <20 silently aborts trust-constr
# (knowledge/20_frameworks/rabbit_minimizer_tolerances.md). At an active face rabbit stores the
# face-held covariance and SKIPS --doImpacts (global impacts still run).
constraints_arg=""
if $do_constraints; then
    constraints_arg="--constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 \
--minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-8 \
--minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerMaxiter 600"
fi

# ASWZ lattice CS-kernel chi2 in the likelihood (LatticeCSTerm; its defaults ARE LATFROZ_V3) at tau=8.
# The CS lambdas are prior-free by default (WRemnants cc3859f4), so this term is their only external
# constraint. See studies/lattice-cs-kernel.
lattice_arg=""
if $do_lattice; then
    lat=wremnants.postprocessing.scetlib_ad.lattice_cs_term
    lattice_arg="-r ${lat}.LatticeCSTerm ${lat}.LatticeCSTermMapping"
    [ -z "$wall_arg" ] && lattice_arg="--regularizationStrength 8 $lattice_arg"
fi

postfix_arg=""
if [ -n "$postfix" ]; then
    postfix_arg="--postfix ${postfix}"
fi

# --jitCompile off is mandatory: the param model calls SCETlib through a
# tf.py_function, which XLA cannot lower.
# --globalImpactsDisableJVP is REQUIRED with this model, not optional: the JVP
# route uses tf.autodiff.ForwardAccumulator, which silently returns a ZERO
# tangent through the tf.py_function this model calls SCETlib with. That drops
# the ParamModel leg of dbeta/dx and makes the binByBinStat global impact
# garbage (measured 8x the total sigma, and a negative var_nobs saved as NaN).
# See studies/scetlib-ad-param-model/260914-global-impacts.
# --snapshotFile is NOT optional: rabbit's SIGTERM handler is a no-op without a
# filename (rabbit/snapshot.py), so a fit killed without one loses everything --
# and these fits run for hours.
# Named after the OUTPUT file rabbit will write, so the pair is obvious and two
# fits can never share a snapshot: rabbit's --outname defaults to
# fitresults.hdf5 and it inserts the postfix, giving fitresults_<postfix>.hdf5.
out_file="fitresults${postfix:+_${postfix}}.hdf5"
snapshot_arg="--snapshotFile ${output_dir}/snapshot_${out_file} --snapshotInterval 0.25"

# Full-scope spectral preconditioning (2026-10-09): the projected-saturated sub-fit is ill-conditioned
# (kappa ~1e9-1e10, alphaS nearly degenerate with the 39 per-bin scales); with this it needs 614 instead of
# 2150 Hessian-vector products (~3x faster, same minimum). The flag is fitter-wide, so the main fit also
# pays one Hessian (~5-15 min) to build its preconditioner. Accepted (Luca); no rabbit change for now.
# See studies/constrained-fit-strategy/261008-saturated-subfit-diagnosis.
precond_arg="--precondition --preconditionParams .* --preconditionBlocks none --preconditionTransform spectral"
# The commands are built as strings and word-split by run_cmd, so ".*" would be glob-expanded against the cwd
# (".git", "..", ...): turn globbing off. Nothing in this script relies on it.
set -f

saturated_arg=""
$do_saturated && saturated_arg="--computeSaturatedProjectionTests"
postfit_args="-m Project ch0 ptll $saturated_arg --computeHistErrors \
--doImpacts --globalImpacts --globalImpactsDisableJVP --saveHists"
model_arg="--paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
cache=$cache/cache.npz conf=$cache/cache.conf"

# Main call: fit + post-fit (Hessian, impacts, hists). The --wall (trust-krylov) path keeps the preconditioner
# and, if asked, the saturated test in this same call. Under --constraints both move to the separate call below:
# the preconditioner is harmful for the COLD trust-constr main fit (PCLAT ran ~70x behind LAT) and the saturated
# sub-fit is the only minimisation in the post-fit that needs it.
main_precond="$precond_arg"; main_postfit="$postfit_args"
if $do_constraints; then
    main_precond=""
    main_postfit="-m Project ch0 ptll --computeHistErrors --doImpacts --globalImpacts --globalImpactsDisableJVP --saveHists"
fi
fit_command="rabbit_fit.py $card --jitCompile off -o $output_dir $toys $postfix_arg \
$main_precond $main_postfit $wall_arg $lattice_arg $constraints_arg $snapshot_arg \
$model_arg $extra_fit"

run_cmd() {
    echo "$1"
    if [ -t 1 ]; then
        $1 2>&1 | tee /dev/tty
        return ${PIPESTATUS[0]}
    else
        $1 2>&1
    fi
}

# tau-continuation (OPT-IN since 2026-10-08, --tau-continuation). The wall is now C^2 by
# default (np_damping_wall smooth=c2), which removes the crawl this stage was added for
# (studies/constrained-fit-strategy/261008-c2-wall-test), so it only costs a cache load.
# History: started far from the minimum, trust-krylov with the relu^2 wall
# can lock in at a stiff (tau=8) relu^2 face: the step zig-zags across the face and
# scipy's radius rule freezes the trust radius at ~1/k, so the fit crawls for hours
# (CENS03, CMR1A). A tau=5 stage gets to the face region without locking in; the
# tau=8 stage then starts on the face and only removes the ~1e-4 overshoot, so the
# result IS the tau=8 answer. Costs one extra cache load.
# See studies/constrained-fit-strategy/261006-diagnosis.
if $do_wall && $do_tau_continuation; then
    pf1="${postfix:+${postfix}_}tau5"
    stage1_file="${output_dir}/fitresults_${pf1}.hdf5"
    stage1_command="rabbit_fit.py $card --jitCompile off -o $output_dir $toys \
--postfix $pf1 --noHessian --noEDM --regularizationStrength 5 $wall_reg \
--snapshotFile ${output_dir}/snapshot_fitresults_${pf1}.hdf5 --snapshotInterval 0.25 \
--paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
cache=$cache/cache.npz conf=$cache/cache.conf $extra_fit"
    echo "[fitterAD] tau-continuation, stage 1 of 2: tau=5"
    run_cmd "$stage1_command"
    rc=$?
    if [ $rc -ne 0 ] || [ ! -s "$stage1_file" ]; then
        echo "[fitterAD] stage 1 (tau=5) failed (exit $rc, output $stage1_file); not running stage 2" >&2
        exit 1
    fi
    # appended last, so it overrides any --externalPostfit given in -f (argparse: last wins)
    fit_command="$fit_command --externalPostfit $stage1_file"
    echo "[fitterAD] tau-continuation, stage 2 of 2: tau=8, warm from $stage1_file"
fi

main_file="${output_dir}/${out_file}"
if [ -z "$saturated_from" ]; then
    run_cmd "$fit_command"
    rc=$?
    if [ $rc -ne 0 ]; then exit $rc; fi
else
    main_file="$saturated_from"
fi
if ! $do_constraints || ! $do_saturated; then
    exit 0
fi

# --constraints --computeSaturatedProjectionTests: the ptll saturated test as its own call (2026-10-20,
# studies/ct18z-nominal-fits). It loads the main fit (incl. its face-held covariance, so no Hessian is recomputed)
# and runs only the saturated sub-fit, which starts at the main minimum: rabbit's warm start (#195) + the full
# spectral preconditioner (#194) make it 4.75x cheaper and properly converged. gtol 1e-5: on a warm leg the
# barrier already starts below barrier_tol and optimality floors at ~1e-6, so 1e-8 only buys an xtol tail
# (dloss <= 3e-8 measured). The ptll hists are re-saved so the saturated chi2 sits next to them (plotPtll.sh).
rabbit_dir=$(python3 -c "import os, rabbit; print(os.path.dirname(rabbit.__file__))" 2>/dev/null)
if ! grep -qs "minimizerWarmStart" "$rabbit_dir/parsing.py" || ! grep -rqs "jac_to_internal" "$rabbit_dir"; then
    echo "[fitterAD] the imported rabbit ($rabbit_dir) lacks the trust-constr warm start (#195) and/or" >&2
    echo "           --precondition with --constraints (#194), needed for the saturated test. Use a rabbit with both." >&2
    exit 1
fi
if [ ! -s "$main_file" ]; then
    echo "[fitterAD] no main fit result at $main_file; not running the saturated test" >&2
    exit 1
fi
pf_sat="${postfix:+${postfix}_}sat"
# --externalPostfit/--noFit come last so they override anything in -f (argparse: last wins).
sat_command="rabbit_fit.py $card --jitCompile off -o $output_dir $toys --postfix $pf_sat \
$precond_arg -m Project ch0 ptll --computeSaturatedProjectionTests --computeHistErrors --saveHists \
$lattice_arg $constraints_arg --minimizerWarmStart auto --minimizerGtol 1e-5 \
--snapshotFile ${output_dir}/snapshot_fitresults_${pf_sat}.hdf5 --snapshotInterval 0.25 \
$model_arg $extra_fit --externalPostfit $main_file --noFit"
echo "[fitterAD] saturated ptll test from $main_file -> ${output_dir}/fitresults_${pf_sat}.hdf5"
run_cmd "$sat_command"
