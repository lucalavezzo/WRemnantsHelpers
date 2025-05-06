# today's date in YYMMDD format
current_date=$(date +"%y%m%d")
label="1DFit"

echo "Running with"
echo "Current date: $current_date"
echo "Label: $label"

# 1/2 MC events, MC stat uncerts.
./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin1_MCstats
./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin2_MCstats -e " --rebin 2"
./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin4_MCstats -e " --rebin 4"

# 1/2 MC events, NO MC stat uncerts.
./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin1/ -f " --noBinByBinStat"
./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin2/ -f " --noBinByBinStat" -e " --rebin 2"
./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin4/ -f " --noBinByBinStat" -e " --rebin 4"

# all MC events, MC stat uncerts.
./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin1_MCstats/
./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin2_MCstats/ -e " --rebin 2"
./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin4_MCstats/ -e " --rebin 4"

# all MC events, MC stat uncerts.
./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin1/ -f " --noBinByBinStat"
./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin2/ -f " --noBinByBinStat" -e " --rebin 2"
./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin4/ -f " --noBinByBinStat" -e " --rebin 4"