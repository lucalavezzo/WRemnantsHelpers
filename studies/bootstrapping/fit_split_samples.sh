# Iterate over the samples stored in the histmaker output file
# setting up and executing the fit for each

# program quits in case of error
# set -e
force=false
force_fit=false
dry=false

# Parse command line options
while [[ $# -gt 0 ]]; do
    case "$1" in
        --force)
            force=true
            shift
            ;;
        --force-fit)
            force_fit=true
            shift
            ;;
        --dry)
            dry=true
            shift
            ;;
        --)
            shift
            break
            ;;
        *)
            break
            ;;
    esac
done

run_fit() {

    # arguments
    local start_index=$1 # indices of the samples to be run
    local end_index=$2
    local infile=$3
    local outdir=$4
    local postfix=$5
    local fit_postfix=$6

    if [ -z "$postfix" ] || [ "$postfix" = "" ]; then
        local _postfix=""
    else
        local _postfix="_${postfix}"
        postfix="${postfix}_" # expect the toy number to be appended later
    fi

    if [ -z "$fit_postfix" ]; then
        local _fit_postfix=""
    else
        local _fit_postfix="_${fit_postfix}"
        fit_postfix="--postfix ${fit_postfix}"
    fi

    # iterate over the toys
    for i in $(seq $start_index $end_index); do

        i_plus_one=$((i + 1))
        echo '=================================================='
        echo "Setting up Combine for sample ${i}"
        echo

        setup_command="python $WREM_BASE/scripts/combine/setupCombine.py -i ${infile}_sample_split_${i}.hdf5 -o ${outdir} --fitvar 'ptll-yll' --fitAlphaS --baseName nominal --pseudoData asimov --postfix ${postfix}sample_${i} --systematicType normal"
        setup_output="${outdir}/ZMassDilepton_ptll_yll${_postfix}_sample_${i}//ZMassDilepton.hdf5"

        if [ -f "$setup_output" ] && [ "$force" = false ]; then
            echo "Setup output already exists: ${setup_output}"
            echo "Skipping setup for sample ${i}"
        else
            echo $setup_command
            echo
            if [ "$dry" = false ]; then
                eval $setup_command
            else
                echo "Dry run: not executing the setup command"
            fi
        fi
        echo
        echo

        echo "Running the fit for sample ${i}"
        echo

        fit_command="combinetf2_fit.py ${setup_output} -o $(dirname ${setup_output}) --pseudoData asimov -t 1 --seed ${i} --toysDataRandomize none --toysSystRandomize none  --toysDataMode observed --noChi2 --chisqFit --binByBinStatType normal ${fit_postfix}"
        fit_output="$(dirname ${setup_output})/fitresults${_fit_postfix}.hdf5"

        if [ -f $fit_output ] && [ "$force_fit" = false ]; then
            echo "Fit output already exists, ${fit_output}"
            echo "Skipping fit for sample ${i}"
        else
            echo $fit_command
            echo
            if [ "$dry" = false ]; then 
                eval $fit_command
            else
                echo "Dry run: not executing the fit command"
            fi
        fi
        echo
        echo
        echo

    done

}


run_fit 1 25 "${MY_OUT_DIR}/250615_split25_seed1776_oneMCfileEvery4/mz_dilepton_split25_seed1776_oneMCfileEvery4" "${MY_OUT_DIR}/250615_split25_seed1776_oneMCfileEvery4/" "" ""
# run_fit 1 30 "${SCRATCH_DIR}/histmaker_output_toys/mz_dilepton_toys_23456" "${MY_OUT_DIR}/250605_default/" "seed_23456"
# run_fit 1 30 "${SCRATCH_DIR}/histmaker_output_toys/mz_dilepton_toys_34567" "${MY_OUT_DIR}/250605_default/" "seed_34567"

# run_fit 0 29 "/scratch/submit/cms/alphaS/histmaker_output_toys/mz_dilepton_toys_12345.hdf5" "${MY_OUT_DIR}/250521_toys_systematicTypeNormal/" "dataRandomize_systRandomize"
# run_fit 0 29 "/scratch/submit/cms/alphaS/histmaker_output_toys/mz_dilepton_toys_23456.hdf5" "toys_23456" "${MY_OUT_DIR}/250521_toys_systematicTypeNormal/" "dataRandomize_systRandomize"
# run_fit 0 29 "/scratch/submit/cms/alphaS/histmaker_output_toys/mz_dilepton_toys_34567.hdf5" "toys_34567" "${MY_OUT_DIR}/250521_toys_systematicTypeNormal/" "dataRandomize_systRandomize"