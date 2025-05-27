# Iterate over the toys stored in the histmaker output file
# setting up and executing the fit for each

# program quits in case of error
set -e

run_toys_fit() {

    local start_index=$1 # indicies of the toys to be run
    local end_index=$2
    local infile=$3
    local outdir=$4
    local postfix=$5

    # iterate over the toys
    for i in $(seq $start_index $end_index); do

        i_plus_one=$((i + 1))

        echo "Setting up combine unfolding for toy ${i}"
        unfolding_setup_command="python $WREM_BASE/scripts/combine/setupCombine.py -i ${infile} -o ${outdir} --analysisMode unfolding --poiAsNoi --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' --genAxes 'ptVGen-absYVGen-helicitySig' --scaleNormXsecHistYields '0.05' --allowNegativeExpectation --systematicType normal --select 'toys ${i}.0j ${i_plus_one}.0j' --postfix ${postfix}_${i}_${i_plus_one} --pseudoData nominal_asimov --unfoldingLevel prefsr"
        unfolding_setup_output="${outdir}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${postfix}_${i}_${i_plus_one}/ZMassDilepton.hdf5"

        if [ -f $unfolding_setup_output ]; then
        
            echo "Unfolding output already exists: ${unfolding_setup_output}"
            echo "Skipping unfolding for toy ${i}"
        else
            echo $unfolding_setup_command
            eval $unfolding_setup_command
        fi

        echo "Running unfolding for toy ${i}"
        unfolding_command="combinetf2_fit.py ${unfolding_setup_output} -o $(dirname ${unfolding_setup_output}) --binByBinStatType normal -t 1 --seed ${i} --toysSystRandomize bayesian --toysDataRandomize poisson --computeHistCov --saveHists --computeHistErrors -m Select ch0_masked --toysDataMode observed"
        unfolding_output="$(dirname ${unfolding_setup_output})/fitresults.hdf5"

        if [ -f $unfolding_output ]; then
            echo "Unfolding fit output already exists: ${unfolding_output}"
            echo "Skipping unfolding fit for toy ${i}"
        else
            echo $unfolding_command
            eval $unfolding_command
        fi

        echo "Setting up Combine for toy ${i}"

        setup_command="python $WREM_BASE/scripts/combine/setupCombine.py -i ${infile} -o $(dirname ${unfolding_setup_output}) --fitresult ${unfolding_output} 'Select' ch0_masked --fitvar ptVGen-absYVGen-helicitySig --fitAlphaS --allowNegativeExpectation --systematicType normal --select 'toys ${i}.0j ${i_plus_one}.0j' --baseName prefsr --postfix ${postfix}_${i}_${i_plus_one} --fitresultResult toy1"
        setup_output="$(dirname ${unfolding_setup_output})/ZMassDilepton_ptVGen_absYVGen_helicitySig_${postfix}_${i}_${i_plus_one}/ZMassDilepton.hdf5"

        if [ -f $setup_output ]; then
            echo "Setup output already exists: ${setup_output}"
            echo "Skipping setup for toy ${i}"
        else
            echo $setup_command
            eval $setup_command
        fi

        echo "Running the fit for toy ${i}"

        fit_command="combinetf2_fit.py ${setup_output} -o $(dirname ${setup_output}) -t 0 --chisqFit --externalCovariance  --binByBinStatType normal "
        fit_output="$(dirname ${setup_output})/fitresults.hdf5"

        if [ -f $fit_output ]; then
            echo "Fit output already exists, ${fit_output}"
            echo "Skipping fit for toy ${i}"
        else
            echo $fit_command
            eval $fit_command
        fi
        echo

    done

}

run_toys_fit 0 29 "${SCRATCH_DIR}/histmaker_output_toys/mz_dilepton_toys_12345.hdf5" "${MY_OUT_DIR}/250527_toys_unfolding/" "toys_12345"
