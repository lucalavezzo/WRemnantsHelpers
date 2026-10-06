#!/bin/bash
# Run the fit with the scetlib_ad param model for the alphaS analysis

usage() {
    echo "Usage: fitterAD.sh <card> -c <cache_dir> -o <output_dir>"
    echo "-f <extra arguments for rabbit_fit.py> -p <postfix>"
    echo "--asimov <Asimov instead of real data>"
    echo "--wall <add the NP damping wall; runs a tau=5 stage, then tau=8 warm from it>"
    echo "--no-tau-continuation <with --wall: go straight to tau=8 (fine for warm starts at the minimum)>"
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
do_tau_continuation=true

PARSED=$(getopt -o c:o:f:p:h --long cache:,output:,extra-fit:,postfix:,asimov,wall,no-tau-continuation,help -- "$@")
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
        --no-tau-continuation) do_tau_continuation=false; shift ;;
        -h|--help)       usage ;;
        --)              shift; break ;;
        *)               echo "Unexpected option: $1" >&2; exit 1 ;;
    esac
done

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

fit_command="rabbit_fit.py $card --jitCompile off -o $output_dir $toys $postfix_arg \
-m Project ch0 ptll --computeSaturatedProjectionTests --computeHistErrors \
--doImpacts --globalImpacts --globalImpactsDisableJVP \
--saveHists $wall_arg $snapshot_arg \
--paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
cache=$cache/cache.npz conf=$cache/cache.conf $extra_fit"

run_cmd() {
    echo "$1"
    if [ -t 1 ]; then
        $1 2>&1 | tee /dev/tty
        return ${PIPESTATUS[0]}
    else
        $1 2>&1
    fi
}

# tau-continuation (default with --wall). Started far from the minimum, trust-krylov
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

run_cmd "$fit_command"
