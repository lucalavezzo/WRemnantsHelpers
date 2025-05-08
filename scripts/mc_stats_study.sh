# today's date in YYMMDD format
current_date=$(date +"%y%m%d")
label="2DFit"

echo "Running with"
echo "Current date: $current_date"
echo "Label: $label"

# # 1/2 MC events, MC stat uncerts.
# ./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin1_MCstats
# ./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin2_MCstats -e " --rebin 2"
# ./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin4_MCstats -e " --rebin 4"

# # 1/2 MC events, NO MC stat uncerts.
# ./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin1/ -f " --noBinByBinStat"
# ./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin2/ -f " --noBinByBinStat" -e " --rebin 2"
# ./workflows/fitter.sh -i ${MY_OUT_DIR}/250505_oneMCfileEvery2/mz_dilepton.hdf5 -o ${MY_OUT_DIR}/250505_oneMCfileEvery2/${current_date}_${label}_rebin4/ -f " --noBinByBinStat" -e " --rebin 4"

# # all MC events, MC stat uncerts.
# ./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin1_MCstats/
# ./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin2_MCstats/ -e " --rebin 2"
# ./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin4_MCstats/ -e " --rebin 4"

# # all MC events, MC stat uncerts.
# ./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin1/ -f " --noBinByBinStat"
# ./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin2/ -f " --noBinByBinStat" -e " --rebin 2"
# ./workflows/fitter.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o ${MY_OUT_DIR}/${current_date}_${label}_rebin4/ -f " --noBinByBinStat" -e " --rebin 4"

# unfolding in 3D, 1/2 MC events, no MC stat uncerts.
./workflows/unfolding.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -u $MY_OUT_DIR/250507_oneMCfileEvery2/mz_dilepton.hdf5 -o $MY_OUT_DIR/250508_unfolding_3D_oneMCfileEvery2_noBinByBinStat -f " --noBinByBinStat "

# unfolding in 3D, 1/2 MC events, MC stat uncerts.
./workflows/unfolding.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -u $MY_OUT_DIR/250507_oneMCfileEvery2/mz_dilepton.hdf5 -o $MY_OUT_DIR/250508_unfolding_3D_oneMCfileEvery2 

# unfolding in 3D, all MC events, no MC stat uncerts.
./workflows/unfolding.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -u /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o $MY_OUT_DIR/250508_unfolding_3D_noBinByBinStat -f " --noBinByBinStat "

# unfolding in 3D, all MC events, MC stat uncerts.
./workflows/unfolding.sh -i /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -u /scratch/submit/cms/alphaS/histmaker_output_250425/mz_dilepton_scetlib_dyturboCorr_maxFiles_m1.hdf5 -o $MY_OUT_DIR/250508_unfolding_3D 