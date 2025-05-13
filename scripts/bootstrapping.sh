# Iterate over the toys stored in the histmaker output file
# setting up and executing the fit for each

# program quits in case of error
set -e

# indicies of the toys to be run
start_index=0
end_index=29

# iterate over the toys
for i in $(seq $start_index $end_index); do

    i_plus_one=$((i + 1))
    echo "Setting up Combine for toy ${i}"

    setup_command="python $WREM_BASE/scripts/combine/setupCombine.py -i $MY_OUT_DIR/250512_toys/mz_dilepton.hdf5 -o $MY_OUT_DIR/250512_toys/ --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' --fitAlphaS --baseName nominal --pseudoData asimov --select 'toys ${i}.0j ${i_plus_one}.0j' --postfix toys_${i}_${i_plus_one} --verbose 0"
    setup_output="${MY_OUT_DIR}/250512_toys//ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toys_${i}_${i_plus_one}//ZMassDilepton.hdf5"

    if [ -f $setup_output ]; then
        echo "Setup output already exists: ${setup_output}"
        echo "Skipping setup for toy ${i}"
    else
        echo $setup_command
        eval $setup_command
    fi

    echo "Running the fit for toy ${i}"

    fit_command="combinetf2_fit.py $MY_OUT_DIR/250512_toys/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toys_${i}_${i_plus_one}/ZMassDilepton.hdf5 -o $MY_OUT_DIR/250512_toys/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toys_${i}_${i_plus_one}/ -t 1 --toysSystRandomize frequentist --toysDataRandomize poisson --toysDataMode observed --noChi2 --verbose 0"
    fit_output="${MY_OUT_DIR}/250512_toys/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_toys_${i}_${i_plus_one}/fitresults.hdf5"

    if [ -f $fit_output ]; then
        echo "Fit output already exists, ${fit_output}"
        echo "Skipping fit for toy ${i}"
    else
        echo $fit_command
        eval $fit_command
    fi
    echo

done