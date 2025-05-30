# Iterate over the toys stored in the histmaker output file
# setting up and executing the fit for each

# program quits in case of error
# set -e
force=true

run_toys_fit() {

    # arguments
    local start_index=$1 # indicies of the toys to be run
    local end_index=$2
    local indir=$3
    local postfix=$4
    local outdir=$5
    local syst=$6    

    # iterate over the toys
    for i in $(seq $start_index $end_index); do

        i_plus_one=$((i + 1))
        echo '=================================================='
        echo "Setting up Combine for toy ${i}"

        setup_command="python $WREM_BASE/scripts/combine/setupCombine.py -i ${indir} -o ${outdir} --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' --fitAlphaS --baseName nominal --pseudoData asimov --select 'toys ${i}.0j ${i_plus_one}.0j' --postfix ${postfix}_${i}_${i_plus_one} --excludeNuisances ${syst} "
        setup_output="${outdir}/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${postfix}_${i}_${i_plus_one}//ZMassDilepton.hdf5"

        if [ -f "$setup_output" ] && [ "$force" = false ]; then
            echo "Setup output already exists: ${setup_output}"
            echo "Skipping setup for toy ${i}"
        else
            echo $setup_command
            echo
            eval $setup_command
        fi
        echo
        echo

        echo "Running the fit for toy ${i}"

        fit_command="combinetf2_fit.py ${setup_output} -o $(dirname ${setup_output}) --pseudoData asimov -t 1 --toysDataRandomize none --toysSystRandomize none --toysDataMode observed --noChi2"
        fit_output="$(dirname ${setup_output})/fitresults.hdf5"

        if [ -f $fit_output ] && [ "$force" = false ]; then
            echo "Fit output already exists, ${fit_output}"
            echo "Skipping fit for toy ${i}"
        else
            echo $fit_command
            echo
            eval $fit_command
        fi
        echo
        echo
        echo

    done

}

# full systs
# systs=(massWeightZ Sin2thetaZ0p00003 scetlib_dyturboCT18Z_pdfasCorr scetlibNP scetlibNPZLambda2 scetlibNPZDelta_Lambda2 scetlibNPZLambda4 resumTNP resumTransitionFOScaleZ QCDscaleZfine QCDscaleZinclusive helicity_shower_kt pdfCT18Z pdfMSHT20mbrange pdfMSHT20mcrange ewScheme ew pythiaew_ISRCorr)
systs=(.*resum.* .*TNP.* mass.* .*scetlib.* pdf.* .*QCD.*)

for syst in ${systs[@]}; do

    echo "Excluding systematic: ${syst}"

    syst_safe=$(echo "$syst" | tr -d '*')

    run_toys_fit 0 29 "/scratch/submit/cms/alphaS/histmaker_output_toys/mz_dilepton_toys_12345.hdf5" "toys_12345" "${MY_OUT_DIR}/250526_toys_excluding_${syst_safe}/" "${syst}"
    #run_toys_fit 0 29 "/scratch/submit/cms/alphaS/histmaker_output_toys/mz_dilepton_toys_23456.hdf5" "toys_23456" "${MY_OUT_DIR}/250526_toys_excluding_${syst_safe}/" "${syst}"
    #run_toys_fit 0 29 "/scratch/submit/cms/alphaS/histmaker_output_toys/mz_dilepton_toys_34567.hdf5" "toys_34567" "${MY_OUT_DIR}/250526_toys_excluding_${syst_safe}/" "${syst}"

done