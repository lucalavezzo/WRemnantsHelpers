#!/bin/bash
# Run the fit with the scetlib_ad param model for the alphaS analysis

usage() {
    echo "Usage: fitterAD.sh <card> -c <cache_dir> -o <output_dir>"
    echo "-f <extra arguments for rabbit_fit.py> -p <postfix>"
    echo "--asimov <Asimov instead of real data>"
    echo "--wall <add the NP damping wall>"
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

PARSED=$(getopt -o c:o:f:p:h --long cache:,output:,extra-fit:,postfix:,asimov,wall,help -- "$@")
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
if $do_wall; then
    wall=wremnants.postprocessing.scetlib_ad.np_damping_wall
    wall_arg="--regularizationStrength 5 -r ${wall}.NPDampingWall ${wall}.NPDampingMapping"
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

echo "$fit_command"

if [ -t 1 ]; then
    $fit_command 2>&1 | tee /dev/tty
else
    $fit_command 2>&1
fi
