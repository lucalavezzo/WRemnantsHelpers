#!/bin/bash
# Two-step fit for the alphaS analysis with the SCETlib NP param model.
#
# Step 0 (optional): setupRabbit.py — datacard with the scetlibNP lambda
#         nuisance templates EXCLUDED (the param model replaces them).
# Step 1 (pass A)  : rabbit_fit.py with --paramModel, --noHessian (the exact
#         Hessian OOMs through the bT-fold slab; see
#         wremnants/postprocessing/scetlib_np/HESSIAN_PLAN.md).
# Step 2 (pass B)  : straight-through Gauss-Newton cov pass on the pass-A
#         postfit (--externalPostfit --noFit, hessian_straightthrough=1
#         hessian_gn=1) + impacts, ptll projection, saturated p-value.
#
# RUN INSIDE the wmassdev container with /opt/venv activated and
# WRemnants/setup.sh sourced (rabbit_fit.py needs tensorflow).
#
# NB vs fitter.sh: --globalImpacts is NOT used — it re-differentiates the
# yields through the param model and OOMs; pass B keeps the traditional
# --doImpacts. The saturated test runs only against the 1D ptll projection
# (2D/full set is prohibitively slow, same rationale as fitter.sh).

usage() {
    echo "Usage: fitterSCETlibNP.sh <infile> -o <output_dir>"
    echo "<infile> is the histmaker hdf5; with --noSetup it is the datacard (carrot)"
    echo "-e <extra arguments for setupRabbit.py>"
    echo "-f <extra arguments for rabbit_fit.py, appended to BOTH passes>"
    echo "-p <postfix for setupRabbit, default excludeSCETlibNP>"
    echo "--priors <Gaussian priors on the lambdas: priors=1 model spec token, both passes>"
    echo "--noSetup <skip setupRabbit.py call, carrot is infile>"
    echo "--noFit <skip pass A; reuse <fit dir>/fitresults.hdf5 for the cov pass>"
    echo "-d|--fitdir <fit output dir; relative paths nest under the datacard dir."
    echo "            Default: the datacard dir itself. Lets one datacard host several"
    echo "            passes (e.g. -d freeze, -d remoteStart); pass A writes"
    echo "            <fit dir>/fitresults.hdf5, pass B writes <fit dir>/cov/>"
    echo "--2D <run 2D fit, ptll-yll>"
    echo "env overrides: UNFOLD, BTGRID, DATA_ARGS (default '-t 0', both passes), MAXITER, THREADS"
    echo "-h, --help <show this help message>"
    exit 1
}

if [ -z "$1" ]; then
    usage
fi

input_file=$1
shift

do_setup=true
do_fit=true
do_2D=false
do_priors=false
postfix="excludeSCETlibNP"

PARSED=$(getopt -o o:e:f:hp:d: --long output:,extra-setup:,extra-fit:,postfix:,fitdir:,priors,noSetup,noFit,2D,help -- "$@")
if [[ $? -ne 0 ]]; then
    echo "Failed to parse arguments." >&2
    exit 1
fi
eval set -- "$PARSED"

while true; do
    case "$1" in
        -o|--output)
            output_dir="$2"
            shift 2
            ;;
        -e|--extra-setup)
            extra_setup="$2"
            shift 2
            ;;
        -f|--extra-fit)
            extra_fit="$2"
            shift 2
            ;;
        -p|--postfix)
            postfix="$2"
            shift 2
            ;;
        -d|--fitdir)
            fitdir="$2"
            shift 2
            ;;
        --priors)
            do_priors=true
            shift
            ;;
        --noSetup)
            do_setup=false
            shift
            ;;
        --noFit)
            do_fit=false
            shift
            ;;
        --2D)
            do_2D=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Unexpected option: $1" >&2
            exit 1
            ;;
    esac
done

if [ -z "$input_file" ]; then
    echo "Input file is required."
    exit 1
fi
# the commands below carry regexes (^scetlibNP.*, --excludeNuisances ...) as
# unquoted words; disable pathname expansion so they reach python verbatim
set -f
if [ -z "$WREM_BASE" ]; then
    echo "WREM_BASE is not set. Please source the setup.sh in WRemnants."
    exit 1
fi
if [ -z "$output_dir" ]; then
    output_dir=$(dirname "$input_file")
fi
mkdir -p "$output_dir"
echo "Output directory: $output_dir" # setupRabbit will create a subdir in here

# ---------- param model inputs (env-overridable) ------------------------------
# unfolding histmaker output (R response + N_gen) and the SCETlib bT grid
UNFOLD=${UNFOLD:-/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260411_histmaker_dilepton_unfolding/mz_dilepton.hdf5}
BTGRID=${BTGRID:-/ceph/submit/data/user/l/lavezzo/zstuff/Z_COM13_CT18Z_N3p0LL_btgrid_fineall/}
MODEL=wremnants.postprocessing.scetlib_np.SCETlibNPParamModel
# Gaussian priors on the lambdas are the model's own decision (rabbit#133
# dropped the --paramModelPriors CLA): the priors=1 spec token goes in BOTH
# passes so the prior penalty also enters the Hessian.
priors_tok=""
if $do_priors; then
    priors_tok="priors=1"
fi
# floating lambdas: lambda2, lambda4, lambda2_nu, delta_lambda2
FREEZE=(lambda_inf lambda6 lambda_inf_nu lambda4_nu '^scetlibNP.*')
# Asimov by default; override for data/toys (applied to BOTH passes so the
# cov pass profiles against the same dataset pass A fit)
DATA_ARGS=${DATA_ARGS:--t 0}
MAXITER=${MAXITER:-1000}

if [ -n "$THREADS" ]; then
    export OMP_NUM_THREADS="$THREADS"
    export TF_NUM_INTRAOP_THREADS="$THREADS"
    export TF_NUM_INTEROP_THREADS=2
fi

# ---------- step 0: datacard ---------------------------------------------------
if $do_setup; then
    echo "Setting up rabbit..."

    if $do_2D; then
        fitvar='ptll-yll'
    else
        fitvar='ptll-yll-cosThetaStarll_quantile-phiStarll_quantile'
    fi

    # exact command the validated excludeSCETlibNP datacard was made with
    # (recovered via scripts/inspect/print_command.py), minus the redundant -p
    setup_command="python ${WREM_BASE}/scripts/rabbit/setupRabbit.py -i $input_file --fitvar $fitvar -o $output_dir --noi alphaS --pdfUncFromCorr --npUnc LatticeNoConstraintsFranks --axlim ptll 0j 44j --pseudoData nominal --excludeNuisances ^(.*scetlibNPZ.*lambda.*|.*scetlibNP.*)$ --postfix ${postfix} $extra_setup"

    echo "$setup_command"
    if [ -t 1 ]; then
        setup_output=$($setup_command 2>&1 | tee /dev/tty)
    else
        setup_output=$($setup_command 2>&1)
        echo "$setup_output"
    fi

    carrot=$(echo "$setup_output" | grep -oP '(?<=Write output file ).*')
    carrot=$(echo "$carrot" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g') # sanitize the output
    if [ -z "$carrot" ]; then
        echo "Could not extract the datacard path from setupRabbit output."
        exit 1
    fi
else
    echo "Skipping setup rabbit..."
    carrot=$input_file
fi

carrot=$(readlink -f "$carrot") # pass B cd's to WREM_BASE; paths must be absolute
echo "Rabbit file: $carrot"
output=$(dirname "$carrot")
# fit outputs can be nested under the datacard dir (-d/--fitdir), so one
# datacard can host several pass-A/pass-B variants side by side
if [ -n "$fitdir" ]; then
    case "$fitdir" in
        /*) ;;                       # absolute: use as given
        *) fitdir="$output/$fitdir" ;; # relative: nest under the datacard dir
    esac
else
    fitdir=$output
fi
mkdir -p "$fitdir"
echo "Output: $fitdir"

# ---------- step 1 (pass A): fit, no Hessian -----------------------------------
if $do_fit; then
    echo
    echo "Running pass A (fit, --noHessian)..."
    fit_command="rabbit_fit.py $carrot -v 4 \
        --paramModel $MODEL unfolding_hdf5_path=$UNFOLD btgrid_dir=$BTGRID $priors_tok \
        --freezeParameters ${FREEZE[*]} \
        --minimizerMaxiter $MAXITER \
        $DATA_ARGS \
        --noHessian --noEDM \
        -o $fitdir $extra_fit"
    echo "$fit_command"
    if ! $fit_command; then
        echo "Pass A failed; not running the cov pass."
        exit 1
    fi
else
    echo "Skipping pass A; reusing $fitdir/fitresults.hdf5"
fi

if [ ! -f "$fitdir/fitresults.hdf5" ]; then
    echo "Pass A postfit $fitdir/fitresults.hdf5 not found; cannot run the cov pass."
    exit 1
fi

# ---------- step 2 (pass B): straight-through GN cov + impacts -----------------
# hessian_straightthrough=1 hessian_gn=1 (GN exact on Asimov) make the Hessian,
# the saturated-model refit, and the hist errors/impacts differentiate through
# the compact J path instead of the bT-fold slab. The spec tokens are stored in
# fitresults meta_info.args (env vars would not be).
echo
echo "Running pass B (straight-through GN cov pass: impacts, ptll projection, saturated test)..."
cd "$WREM_BASE"
cov_command="rabbit_fit.py $carrot -v 4 \
    --paramModel $MODEL unfolding_hdf5_path=$UNFOLD btgrid_dir=$BTGRID $priors_tok hessian_straightthrough=1 hessian_gn=1 \
    --freezeParameters ${FREEZE[*]} \
    --externalPostfit $fitdir/fitresults.hdf5 --noFit \
    --minimizerMaxiter $MAXITER \
    $DATA_ARGS \
    --doImpacts \
    -m Project ch0 ptll \
    --computeSaturatedProjectionTests \
    --computeVariations --computeHistErrors --computeHistImpacts \
    --saveHists --saveHistsPerProcess \
    -o $fitdir/cov $extra_fit"
echo "$cov_command"
if ! $cov_command; then
    echo "Pass B (cov pass) failed."
    exit 1
fi

echo
echo "Done. Postfit: $fitdir/fitresults.hdf5 ; cov/impacts/hists: $fitdir/cov/fitresults.hdf5"
