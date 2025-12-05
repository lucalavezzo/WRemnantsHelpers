# Systematics

python scripts/plot_narf_hists.py '/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//251114_histmaker_dilepton/mz_dilepton_correctMbcIHope.hdf5' --filterProcs ZmumuPostVFP --hists nominal 'nominal_pdfCT18Z' 'nominal_pdfCT18ZUncertByHelicity' --selectByHist '' 'pdfVar 2' 'pdfVar 2' --labels nominal 'via MiNNLO' 'via helicities' --axes ptll yll --binwnorm 1 --rrange '0.97' '1.01' --noRatioErrorBars --postfix fullAngularDistribution --legLoc '0.7' '0.3'
python scripts/plot_narf_hists.py '/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//251114_histmaker_dilepton/mz_dilepton_correctMbcIHope.hdf5' --filterProcs ZmumuPostVFP --hists nominal 'nominal_pdfCT18Z' 'nominal_pdfCT18ZUncertByHelicity' --selectByHist '' 'pdfVar 2' 'pdfVar 2' --labels nominal 'via MiNNLO' 'via helicities' --axes ptll yll --binwnorm 1 --rrange '0.97' '1.01' --noRatioErrorBars --select 'cosThetaStarll_quantile 0' 'phiStarll_quantile 0' --postfix singleAngularBin --legLoc '0.7' '0.3'
python studies/pdf_bias_test/plot_results.py --input-dir '/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//251120_histmaker_dilepton/'
rabbit_plot_hists.py  $MY_OUT_DIR/251114_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5 -m "Project ch0 ptll" --prefit --config $WREM_BASE/utilities/styles/styles.py --title CMS  --titlePos 0 -o $MY_AN_DIR/Figures/systematics/ --processGrouping 'z_dilepton'  --rrange '0.88' '1.12'  --varName pdfAlphaS --varLabel '$\alpha_\mathrm{S}{\pm}1\sigma$' --yscale '1.25' --noExtraText --subtitle Preliminary --lowerLegPos "upper right" --noData --postfix alphas
rabbit_plot_hists.py  $MY_OUT_DIR/251114_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/fitresults.hdf5 -m "Project ch0 ptll" --prefit --config $WREM_BASE/utilities/styles/styles.py --title CMS  --titlePos 0 -o $MY_AN_DIR/Figures/systematics/ --processGrouping 'z_dilepton'  --rrange '0.88' '1.12'  --varName pdf22CT18ZSymAvg pdf4CT18ZSymDiff pdf26CT18ZSymDiff --varLabel 'CT18Z 22 (Avg.)' 'CT18Z 4 (Diff.)' 'CT18Z 26 (Diff.)' --yscale '1.25' --noExtraText --subtitle Preliminary --lowerLegPos "upper right" --noData --postfix pdfs --showVariations both

# Detector-level extraction

## Setup

rabbit_plot_inputdata.py  $MY_OUT_DIR/251114_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton.hdf5 --hists ptll-yll --config $WREM_BASE/utilities/styles/styles.py --title CMS  --titlePos 0 -o $MY_AN_DIR/Figures/detector_extraction/ --processGrouping 'z_dilepton'
rabbit_plot_inputdata.py  $MY_OUT_DIR/251114_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton.hdf5 -o $MY_AN_DIR/Figures/detector_extraction/ --hists phiStarll_quantile --config $WREM_BASE/utilities/styles/styles.py --title CMS  --titlePos 0  --ylim 0 1300000 --processGrouping 'z_dilepton'
rabbit_plot_inputdata.py  $MY_OUT_DIR/251114_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile/ZMassDilepton.hdf5 -o $MY_AN_DIR/Figures/detector_extraction/ --hists cosThetaStarll_quantile --config $WREM_BASE/utilities/styles/styles.py --title CMS  --titlePos 0  --ylim 0 1300000 --processGrouping 'z_dilepton'

## Results
