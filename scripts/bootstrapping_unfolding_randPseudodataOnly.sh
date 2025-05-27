# Iterate over the toys stored in the histmaker output file
# setting up and executing the fit for each

# program quits in case of error
set -e

run_toys_fit() {

    local infile=$1
    local outdir=$2

    echo "Setting up combine unfolding"
    unfolding_setup_command="python $WREM_BASE/scripts/combine/setupCombine.py -i ${infile} -o ${outdir} --analysisMode unfolding --poiAsNoi --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' --genAxes 'ptVGen-absYVGen-helicitySig' --scaleNormXsecHistYields '0.05' --allowNegativeExpectation --systematicType normal --select 'toys 0.0j 1.0j' --postfix toy0 --pseudoData nominal_asimov --unfoldingLevel prefsr"
    unfolding_setup_output="${outdir}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toy0/ZMassDilepton.hdf5"
    if [ -f $unfolding_setup_output ]; then
    
        echo "Unfolding output already exists: ${unfolding_setup_output}"
        echo "Skipping unfolding"
    else
        echo $unfolding_setup_command
        eval $unfolding_setup_command
    fi

    #seeds=(12345 23456 34567 45678 56789 98765 87653 76543 65432 54322 )
    seeds=(12345 23456 34567 45678 56789) # reduced set for testing

    # iterate over the seeds
    for seed in ${seeds[@]}; do

        echo "Running unfolding for seed ${seed}"
        unfolding_command="combinetf2_fit.py ${unfolding_setup_output} -o $(dirname ${unfolding_setup_output}) --binByBinStatType normal -t 10 --toysSystRandomize bayesian  --toysDataRandomize poisson --toysDataMode observed --computeHistCov --saveHists --computeHistErrors -m Select ch0_masked --seed ${seed} --postfix ${seed}"
        unfolding_output="$(dirname ${unfolding_setup_output})/fitresults_${seed}.hdf5"

        if [ -f $unfolding_output ]; then
            echo "Unfolding fit output already exists: ${unfolding_output}"
            echo "Skipping unfolding fit for toy ${i}"
        else
            echo $unfolding_command
            eval $unfolding_command
        fi

        for i in $(seq 1 10); do

            echo "Setting up Combine for toy ${i}"

            setup_command="python $WREM_BASE/scripts/combine/setupCombine.py -i ${infile} -o $(dirname ${unfolding_setup_output}) --fitresult ${unfolding_output} 'Select' ch0_masked --fitvar ptVGen-absYVGen-helicitySig --fitAlphaS --allowNegativeExpectation --systematicType normal --select 'toys 0.0j 1.0j' --baseName prefsr --postfix seed${seed}_toy${i} --fitresultResult toy${i}"
            setup_output="$(dirname ${unfolding_setup_output})/ZMassDilepton_ptVGen_absYVGen_helicitySig_seed${seed}_toy${i}/ZMassDilepton.hdf5"

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

    done

}

run_toys_fit "${MY_OUT_DIR}/250516_toys_34567/mz_dilepton.hdf5" "${MY_OUT_DIR}/250525_toys_unfolding_toy0/"
