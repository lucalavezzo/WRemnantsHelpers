# NP-function plot for one or two scetlib_ad fitresults: ONE figure, two panels -- the CS kernel gamma_nu^NP(b_T)
# and the TMD factor F_eff(b_T, y) -- each fit postfit (solid, 68 % band from its covariance) over its prefit
# (dashed), with the lattice-fit CS kernel and MAP22 as external references. Thin wrapper around
#   python -m wremnants.postprocessing.scetlib_ad.np_function_plots
# (the scetlib_np plotter ported to the analysis branch, with a scetlib_ad fitresults reader); see its --help.
#
#   plotNPFunctions.sh <fitresults_A.hdf5> [<fitresults_B.hdf5>] -o <output_dir> [-e "<extra args>"]
#
# A is the numerator tune (viridis), B the denominator (plasma); at most two fits (the plotter's num/den). A path
# may be given as LABEL=PATH to set its legend label. Default rapidities --y 0 2.5 (the fit acceptance); override
# with -e "--y 0 2.5 5". For a study, -o is the task directory. Runs from the host too (enters the container).

if [ -z "$1" ] || [[ "$1" == -* ]]; then
    echo "Usage: plotNPFunctions.sh <fitresults_A> [<fitresults_B>] -o <output_dir> -e <extra_args>"
    echo "       (extra args go to wremnants.postprocessing.scetlib_ad.np_function_plots; see its --help)"
    exit 1
fi

# not in the WRemnants environment yet: re-enter through agent_setup.sh (container + setup.sh)
if [ -z "$WREM_BASE" ]; then
    HELPERS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    exec "$HELPERS/agent_setup.sh" -- bash "$HELPERS/workflows/plotNPFunctions.sh" "$@"
fi

fits=()
while [ -n "$1" ] && [[ "$1" != -* ]]; do
    fits+=("$1")
    shift
done
if [ ${#fits[@]} -gt 2 ]; then
    echo "plotNPFunctions.sh: at most two fitresults (numerator, denominator), got ${#fits[@]}" >&2
    exit 1
fi

extra=""

while getopts "o:e:" opt; do
    case $opt in
        o)
            output_dir=$OPTARG
            ;;
        e)
            extra=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

if [ -z "$output_dir" ]; then
    current_date=$(date +"%y%m%d")
    output_dir=~/public_html/alphaS/${current_date}_np_functions/
fi

tune_args=""
sides=(num den)
for i in "${!fits[@]}"; do
    f="${fits[$i]}"
    side="${sides[$i]}"
    if [[ "$f" == *=* ]]; then
        tune_args+=" --${side}-label $(printf '%q' "${f%%=*}")"
        f="${f#*=}"
    fi
    tune_args+=" --${side}-fitresult $(printf '%q' "$f")"
done

echo "Output directory: $output_dir"
mkdir -p "$output_dir"

command="python3 -m wremnants.postprocessing.scetlib_ad.np_function_plots ${tune_args} --y 0 2.5 -o ${output_dir%/}/ ${extra}"

echo "Executing command: $command"
eval $command
