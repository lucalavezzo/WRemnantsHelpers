#!/usr/bin/env bash

set -euo pipefail

SUBTITLE="Preliminary"

# Paths to helper scripts
PLOT_NARF="${MY_WORK_DIR}/scripts/plot_narf_hists.py"

# generic inputs
Z_INPUT_H5="${MY_OUT_DIR}/251114_histmaker_dilepton/mz_dilepton_correctMbcIHope.hdf5"
Z_RECO_CARROT="${MY_OUT_DIR}/251114_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_correctMbcIHope/ZMassDilepton.hdf5"
Z_RECO_FIT="${MY_OUT_DIR}/251114_histmaker_dilepton/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_correctMbcIHope/fitresults.hdf5"
W_RECO_CARROT="${MY_OUT_DIR}/251006_histmaker_unfoldingMW/WMass_pt_eta_charge/WMass.hdf5"
WZ_RECO_FIT="${MY_OUT_DIR}/251205_WZCombinedFit/Combination_ZMassDileptonWMass/fitresults_binByBinStatModeFull.hdf5"
WZ_UNFOLDING_FIT="${MY_OUT_DIR}/251209_WZCombinedUnfolding/Combination_ZMassDileptonWMass/fitresults_asimov.hdf5"
WZ_UNFOLDING_FIT_CH1="${MY_OUT_DIR}/251209_WZCombinedUnfolding/Combination_ZMassDileptonWMass/fitresults_asimov_ch1.hdf5"
WZ_GEN_CARROT="${MY_OUT_DIR}/251210_WZCombinedTheoryFit//Combination_ZMassDileptonWMass/carrot_scetlib_dyturbo_ct18z_alphaS_mW_scaled.hdf5"
WZ_GEN_FIT="${MY_OUT_DIR}/251210_WZCombinedTheoryFit//Combination_ZMassDileptonWMass/fitresults.hdf5"
Z_GEN_FIT="${MY_OUT_DIR}/251211_WZCombinedTheoryFit//Combination_ZMassDileptonWMass/fitresults.hdf5"

# study-specific inputs
PDF_BIAS_INPUT_DIR="${MY_OUT_DIR}/251120_histmaker_dilepton_pdfs/"

# output selection: default to analysis (MY_AN_DIR); or "www" -> ${MY_PLOT_DIR}/%y%m%d_AN_Figures
OUTPUT_MODE=an
SECTIONS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      OUTPUT_MODE="${2:-}"
      shift 2
      ;;
    --sections)
      shift
      while [[ $# -gt 0 && $1 != --* ]]; do
        SECTIONS+=("$1")
        shift
      done
      ;;
    --help|-h)
      echo "Usage: $0 [--output an|www] [--sections 4 [5] [6] [7]]"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--output an|www] [--sections 4 [5] [6] [7]]"
      exit 1
      ;;
  esac
done

# default sections if none provided
if [[ ${#SECTIONS[@]} -eq 0 ]]; then
  SECTIONS=(4 5 6 7)
fi

# validate sections
for sec in "${SECTIONS[@]}"; do
  if [[ "${sec}" != "4" && "${sec}" != "5" && "${sec}" != "6" && "${sec}" != "7" ]]; then
    echo "Invalid section '${sec}'. Allowed: 4 (uncertainties), 5 (detector-level extraction), 6 (unfolding), 7 (gen-level extraction)."
    exit 1
  fi
done

case "${OUTPUT_MODE}" in
  an)
    : "${MY_AN_DIR:?Set MY_AN_DIR for use --output an}"
    OUTPUT_ROOT="${MY_AN_DIR}"
    ;;
  www)
    : "${MY_PLOT_DIR:?Set MY_PLOT_DIR for --output www}"
    OUTPUT_ROOT="${MY_PLOT_DIR}/$(date +%y%m%d)_AN_Figures"
    ;;
  *)
    echo "Invalid --output '${OUTPUT_MODE}', expected 'an' or 'www'."
    exit 1
    ;;
esac

echo "Output root directory: ${OUTPUT_ROOT}"

UNCERTS_OUT="${OUTPUT_ROOT}/Figures/uncertainties"
RECO_RESULTS="${OUTPUT_ROOT}/Figures/detector_extraction"
Z_RECO_RESULTS="${RECO_RESULTS}/Z_fit/"
WZ_RECO_RESULTS="${RECO_RESULTS}/WZ_fit/"
WZ_RECO_COMPARISON="${RECO_RESULTS}/comparison/"
Z_UNFOLDING_XSECS="${OUTPUT_ROOT}/Figures/unfolding/helicity_xsecs"
W_UNFOLDING_XSECS="${OUTPUT_ROOT}/Figures/unfolding/w_unfolded_xsecs"
GEN_RESULTS="${OUTPUT_ROOT}/Figures/gen_extraction"
WZ_GEN_RESULTS="${GEN_RESULTS}/WZ_fit/"
Z_GEN_RESULTS="${GEN_RESULTS}/Z_fit/"

mkdir -p "${UNCERTS_OUT}" "${RECO_RESULTS}" "${Z_RECO_RESULTS}" "${WZ_RECO_RESULTS}" "${WZ_RECO_COMPARISON}" "${Z_UNFOLDING_XSECS}" "${W_UNFOLDING_XSECS}" "${GEN_RESULTS}" "${WZ_GEN_RESULTS}" "${Z_GEN_RESULTS}"

should_run() {
  local target="$1"
  for sec in "${SECTIONS[@]}"; do
    if [[ "${sec}" == "${target}" ]]; then
      return 0
    fi
  done
  return 1
}

# ---------------- #
# Systematics (4)
# ---------------- #
if should_run 4; then
  echo "Generating Section 4 (uncertainties) figures..."

  # alphaS smoothing
  python "${PLOT_NARF}" ${MY_OUT_DIR}/260113_histmaker_dilepton/mz_dilepton.hdf5 \
    --filterProcs ZmumuPostVFP \
    --hists nominal "nominal_scetlib_dyturbo_CT18Z_N3p0LL_N2LO_pdfas_Corr" "nominal_scetlib_dyturbo_CT18Z_N3p0LL_N2LO_pdfas_CorrByHelicity" \
    --selectByHist "" "vars 1" "vars 1" \
    --labels nominal "via MiNNLO" "via helicities" \
    --axes ptll yll --binwnorm 1 --rrange 0.96 1.01 \
    --noRatioErrorBars --postfix fullAngularDistribution --legLoc 0.7 0.3 \
    -o "${UNCERTS_OUT}"

  python "${PLOT_NARF}" ${MY_OUT_DIR}/260113_histmaker_dilepton/mz_dilepton.hdf5 \
    --filterProcs ZmumuPostVFP \
    --hists nominal "nominal_scetlib_dyturbo_CT18Z_N3p0LL_N2LO_pdfas_Corr" "nominal_scetlib_dyturbo_CT18Z_N3p0LL_N2LO_pdfas_CorrByHelicity" \
    --selectByHist "" "vars 1" "vars 1" \
    --labels nominal "via MiNNLO" "via helicities" \
    --axes ptll yll --binwnorm 1 --rrange 0.96 1.01 \
    --noRatioErrorBars --select "cosThetaStarll_quantile 0" "phiStarll_quantile 0" \
    --postfix singleAngularBin --legLoc 0.7 0.3 \
    -o "${UNCERTS_OUT}"

  # PDF smoothing
  # python "${PLOT_NARF}" "${Z_INPUT_H5}" \
  #   --filterProcs ZmumuPostVFP \
  #   --hists nominal "nominal_pdfCT18Z" "nominal_pdfCT18ZUncertByHelicity" \
  #   --selectByHist "" "pdfVar 2" "pdfVar 2" \
  #   --labels nominal "via MiNNLO" "via helicities" \
  #   --axes ptll yll --binwnorm 1 --rrange 0.96 1.01 \
  #   --noRatioErrorBars --postfix fullAngularDistribution --legLoc 0.7 0.3 \
  #   -o "${UNCERTS_OUT}"

  # python "${PLOT_NARF}" "${Z_INPUT_H5}" \
  #   --filterProcs ZmumuPostVFP \
  #   --hists nominal "nominal_pdfCT18Z" "nominal_pdfCT18ZUncertByHelicity" \
  #   --selectByHist "" "pdfVar 2" "pdfVar 2" \
  #   --labels nominal "via MiNNLO" "via helicities" \
  #   --axes ptll yll --binwnorm 1 --rrange 0.96 1.01 \
  #   --noRatioErrorBars --select "cosThetaStarll_quantile 0" "phiStarll_quantile 0" \
  #   --postfix singleAngularBin --legLoc 0.7 0.3 \
  #   -o "${UNCERTS_OUT}"

  # python "${MY_WORK_DIR}/studies/pdf_bias_test/plot_results.py" --input-dir "${PDF_BIAS_INPUT_DIR}"
  # python "${MY_WORK_DIR}/studies/pdf_bias_test/plot_results.py" --input-dir "${PDF_BIAS_INPUT_DIR}" \
  #   --file-base ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_pdfBiasTest_Zmumu_scale1p0_ \
  #   --postfix scale1p0

  # python "${RABBIT_BASE}/bin//rabbit_plot_hists.py" "${Z_RECO_FIT}" \
  #   -m "Project ch0 ptll" --prefit --config "${WREM_BASE}/utilities/styles/styles.py" \
  #   --title CMS --titlePos 0 -o "${UNCERTS_OUT}/" --processGrouping z_dilepton \
  #   --rrange 0.88 1.12 --varName pdfAlphaS --varLabel "$\\alpha_\\mathrm{S}{\\pm}1\\sigma$" \
  #   --yscale 1.25 --noExtraText --subtitle ${SUBTITLE} --lowerLegPos "upper right" \
  #   --noData --postfix alphas
  # python "${RABBIT_BASE}/bin//rabbit_plot_hists.py" "${Z_RECO_FIT}" \
  #   -m "Project ch0 yll" --prefit --config "${WREM_BASE}/utilities/styles/styles.py" \
  #   --title CMS --titlePos 0 -o "${UNCERTS_OUT}/" --processGrouping z_dilepton \
  #   --rrange 0.88 1.12 --varName pdfAlphaS --varLabel "$\\alpha_\\mathrm{S}{\\pm}1\\sigma$" \
  #   --yscale 1.25 --noExtraText --subtitle ${SUBTITLE} --lowerLegPos "upper right" \
  #   --noData --postfix alphas
  # python "${RABBIT_BASE}/bin//rabbit_plot_hists.py" "${Z_RECO_FIT}" \
  #   -m "Project ch0 cosThetaStarll_quantile" --prefit --config "${WREM_BASE}/utilities/styles/styles.py" \
  #   --title CMS --titlePos 0 -o "${UNCERTS_OUT}/" --processGrouping z_dilepton \
  #   --rrange 0.88 1.12 --varName pdfAlphaS --varLabel "$\\alpha_\\mathrm{S}{\\pm}1\\sigma$" \
  #   --yscale 1.25 --noExtraText --subtitle ${SUBTITLE} --lowerLegPos "upper right" \
  #   --noData --postfix alphas
  # python "${RABBIT_BASE}/bin//rabbit_plot_hists.py" "${Z_RECO_FIT}" \
  #   -m "Project ch0 phiStarll_quantile" --prefit --config "${WREM_BASE}/utilities/styles/styles.py" \
  #   --title CMS --titlePos 0 -o "${UNCERTS_OUT}/" --processGrouping z_dilepton \
  #   --rrange 0.88 1.12 --varName pdfAlphaS --varLabel "$\\alpha_\\mathrm{S}{\\pm}1\\sigma$" \
  #   --yscale 1.25 --noExtraText --subtitle ${SUBTITLE} --lowerLegPos "upper right" \
  #   --noData --postfix alphas

  # python "${RABBIT_BASE}/bin//rabbit_plot_hists.py" "${Z_RECO_FIT}" \
  #   -m "Project ch0 ptll" --prefit --config "${WREM_BASE}/utilities/styles/styles.py" \
  #   --title CMS --titlePos 0 -o "${UNCERTS_OUT}/" --processGrouping z_dilepton \
  #   --rrange 0.88 1.12 \
  #   --varName pdf22CT18ZSymAvg pdf4CT18ZSymDiff pdf26CT18ZSymDiff \
  #   --varLabel "CT18Z 22 (Avg.)" "CT18Z 4 (Diff.)" "CT18Z 26 (Diff.)" \
  #   --yscale 1.25 --noExtraText --subtitle ${SUBTITLE} --lowerLegPos "upper right" \
  #   --noData --postfix pdfs --showVariations both
fi

# -------------------------- #
# Detector-level extraction (5)
# -------------------------- #
if should_run 5; then
  echo "Generating Section 5 (detector-level extraction) figures..."

  # setup
  # "${RABBIT_BASE}/bin/rabbit_plot_inputdata.py" "${Z_RECO_CARROT}" \
  #   --hists ptll-yll --config "${WREM_BASE}/utilities/styles/styles.py" \
  #   --title CMS --titlePos 0 -o "${RECO_RESULTS}/" --processGrouping z_dilepton \
  #   --noData
  # "${RABBIT_BASE}/bin/rabbit_plot_inputdata.py" "${Z_RECO_CARROT}" \
  #   -o "${RECO_RESULTS}/" --hists phiStarll_quantile --config "${WREM_BASE}/utilities/styles/styles.py" \
  #   --title CMS --titlePos 0 --ylim 0 1300000 --processGrouping z_dilepton \
  #   --noData
  # "${RABBIT_BASE}/bin/rabbit_plot_inputdata.py" "${Z_RECO_CARROT}" \
  #   -o "${RECO_RESULTS}/" --hists cosThetaStarll_quantile --config "${WREM_BASE}/utilities/styles/styles.py" \
  #   --title CMS --titlePos 0 --ylim 0 1300000 --processGrouping z_dilepton \
  #   --noData
  "${RABBIT_BASE}/bin/rabbit_plot_inputdata.py" "${W_RECO_CARROT}" \
    --hists 'pt-eta' --config "${WREM_BASE}/utilities/styles/styles.py" \
    --title CMS --titlePos 0 -o "${RECO_RESULTS}/" --processGrouping 'w_mass' \
    --selectionAxes charge --postfix 'single_muon' \
    --noData

  # Z reco results
  # "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${Z_RECO_FIT}" \
  #   --poi pdfAlphaS --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts 2.0 \
  #   --showNumbers --oneSidedImpacts --grouping min -o ${Z_RECO_RESULTS} --otherExtensions pdf png \
  #   -n 50 --poi pdfAlphaS --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>'\
  #   --title CMS --subtitle ${SUBTITLE}
  # "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${Z_RECO_FIT}" \
  #   --poi pdfAlphaS --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts 2.0 \
  #   --showNumbers --oneSidedImpacts --grouping min -o ${Z_RECO_RESULTS} --otherExtensions pdf png \
  #   -n 50 --poi pdfAlphaS --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>'\
  #   --title CMS --subtitle ${SUBTITLE} --globalImpacts
  # # higher orders
  # python studies/higher_orders/plot_results.py --input-dir  $MY_OUT_DIR/251124_histmaker_dilepton_ho/ \
  #   --output-dir "${Z_RECO_RESULTS}"
  # # alternate pdfs
  # python studies/alternate_pdfs/plot_results.py --input-dir $MY_OUT_DIR/251120_histmaker_dilepton_pdfs/ \
  #   --output-dir "${Z_RECO_RESULTS}"

  # # WZ reco results
  # "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${WZ_RECO_FIT}" \
  #   --poi pdfAlphaS --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '2.0' \
  #   --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
  #   --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle ${SUBTITLE} \
  #   -o "${WZ_RECO_RESULTS}"
  # "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${WZ_RECO_FIT}" \
  #   --poi massShiftW100MeV --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '100.0' \
  #   --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
  #   --impactTitle '<i>m</i><sub>W</sub> in MeV' --title CMS --subtitle ${SUBTITLE} \
  #   -o "${WZ_RECO_RESULTS}"
  #   "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${WZ_RECO_FIT}" \
  #   --poi pdfAlphaS --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '2.0' \
  #   --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
  #   --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle ${SUBTITLE} \
  #   -o "${WZ_RECO_RESULTS}" --globalImpacts
  # "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${WZ_RECO_FIT}" \
  #   --poi massShiftW100MeV --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '100.0' \
  #   --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
  #   --impactTitle '<i>m</i><sub>W</sub> in MeV' --title CMS --subtitle ${SUBTITLE} \
  #   -o "${WZ_RECO_RESULTS}" --globalImpacts

  # # comparison
  # "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${Z_RECO_FIT}" \
  #   --poi pdfAlphaS --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '2.0' \
  #   --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
  #   --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle ${SUBTITLE} \
  #   -o "${WZ_RECO_COMPARISON}" \
  #   -r "${WZ_RECO_FIT}" --refName 'W+Z' --name 'Z only' --globalImpacts
  # "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${Z_RECO_FIT}" \
  #   --poi pdfAlphaS --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '2.0' \
  #   --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
  #   --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle ${SUBTITLE} \
  #   -o "${WZ_RECO_COMPARISON}" \
  #   -r "${WZ_RECO_FIT}" --refName 'W+Z' --name 'Z only'
fi

if should_run 6; then
  echo "Generating Section 6 (unfolding) figures..."

  # Z cross sections
  "${RABBIT_BASE}/bin/rabbit_plot_hists.py" "${WZ_UNFOLDING_FIT}" \
    -o "${Z_UNFOLDING_XSECS}" \
    -m Project --selectionAxes helicitySig --channels 'ch0_masked' \
    --unfoldedXsec \
    --extraTextLoc '0.35' '0.9' --legCols 1 --yscale '1.2' --title CMS --titlePos 0 \
    --subtitle ${SUBTITLE} --rrange '0.8' '1.2' \
    --config "${WREM_BASE}/utilities/styles/styles.py"
  "${RABBIT_BASE}/bin/rabbit_plot_hists_uncertainties.py" "${WZ_UNFOLDING_FIT}" \
    -o "${Z_UNFOLDING_XSECS}" \
    -m Project --selectionAxes helicitySig --channels 'ch0_masked' \
    --absolute \
    --extraTextLoc '0.05' '0.95' --legCols 2 --yscale '1.5' --title CMS --titlePos 0 \
    --subtitle ${SUBTITLE} --grouping unfolding \
    --config "${WREM_BASE}/utilities/styles/styles.py" 
  "${RABBIT_BASE}/bin/rabbit_plot_hists_cov.py" "${WZ_UNFOLDING_FIT}" \
    -o "${Z_UNFOLDING_XSECS}" \
    -m Project --selectionAxes helicitySig \
    --correlation \
    --title CMS --subtitle ${SUBTITLE} --titlePos 0 --subtitle ${SUBTITLE} \
    --config "${WREM_BASE}/utilities/styles/styles.py"

  # W cross sections
  "${RABBIT_BASE}/bin/rabbit_plot_hists.py" "${WZ_UNFOLDING_FIT_CH1}" \
    -o "${W_UNFOLDING_XSECS}" \
    -m Select --selectionAxes qGen --channels 'ch1_masked' \
    --unfoldedXsec \
    --extraTextLoc '0.35' '0.9' --legCols 1 --yscale '1.2' --title CMS --titlePos 0 \
    --subtitle ${SUBTITLE} --rrange '0.8' '1.2' \
    --invertAxes \
    --customFigureWidth 2.5 \
    --config "${WREM_BASE}/utilities/styles/styles.py"
  "${RABBIT_BASE}/bin/rabbit_plot_hists_uncertainties.py" "${WZ_UNFOLDING_FIT_CH1}" \
    -o "${W_UNFOLDING_XSECS}" \
    -m Select --selectionAxes qGen --channels 'ch1_masked' \
    --extraTextLoc '0.05' '0.95' --legCols 2 --yscale '1.5' --title CMS --titlePos 0 \
    --subtitle ${SUBTITLE} --grouping unfolding \
    --invertAxes \
    --customFigureWidth 2.5 \
    --config "${WREM_BASE}/utilities/styles/styles.py" 
  "${RABBIT_BASE}/bin/rabbit_plot_hists.py" "${WZ_UNFOLDING_FIT_CH1}" \
    -o "${W_UNFOLDING_XSECS}" \
    -m Project --selectionAxes qGen --channels 'ch1_masked' \
    --unfoldedXsec \
    --extraTextLoc '0.35' '0.9' --legCols 1 --yscale '1.2' --title CMS --titlePos 0 \
    --subtitle ${SUBTITLE} --rrange '0.8' '1.2' \
    --invertAxes \
    --config "${WREM_BASE}/utilities/styles/styles.py"
  "${RABBIT_BASE}/bin/rabbit_plot_hists_uncertainties.py" "${WZ_UNFOLDING_FIT_CH1}" \
    -o "${W_UNFOLDING_XSECS}" \
    -m Project --selectionAxes qGen --channels 'ch1_masked' \
    --extraTextLoc '0.05' '0.95' --legCols 2 --yscale '1.5' --title CMS --titlePos 0 \
    --subtitle ${SUBTITLE} --grouping unfolding \
    --invertAxes \
    --config "${WREM_BASE}/utilities/styles/styles.py" 
  "${RABBIT_BASE}/bin/rabbit_plot_hists_cov.py" "${WZ_UNFOLDING_FIT_CH1}" \
    -o "${W_UNFOLDING_XSECS}" \
    -m Project --selectionAxes qGen \
    --correlation \
    --title CMS --subtitle ${SUBTITLE} --titlePos 0 --subtitle ${SUBTITLE} \
    --config "${WREM_BASE}/utilities/styles/styles.py"

  # angular coefficients
  # TODO David hasn't told me how he made those plots



fi

if should_run 7; then
  echo "Generating Section 7 (gen-level extraction) figures..."

  # WZ setup
  "${RABBIT_BASE}/bin/rabbit_plot_hists.py" "${WZ_GEN_FIT}" \
    -o "${WZ_GEN_RESULTS}" \
    --prefit --channels chW --selectionAxes qGen --invertAxes -m Basemodel \
    --varName massShiftW100MeV --varLabel "$\Delta m_{W}{\\pm}100\\mathrm{MeV}$" \
    --extraTextLoc '0.04' '0.9' --legCols 1 --yscale '1.2' --title CMS --titlePos 0 \
    --chisq none \
    --subtitle ${SUBTITLE} --rrange '0.95' '1.05' \
    --config "${WREM_BASE}/utilities/styles/styles.py"\
    --customFigureWidth 2.5 \
    --subplotSizes 1 1 \
    --lowerLegPos 'upper right'
  "${RABBIT_BASE}/bin/rabbit_plot_hists.py" "${WZ_GEN_FIT}" \
    -o "${WZ_GEN_RESULTS}" \
    --prefit --channels chSigmaUL -m Basemodel \
    --varName pdfAlphaS --varLabel "$\\alpha_\\mathrm{S}{\\pm}1\\sigma$" \
    --extraTextLoc '0.04' '0.9' --legCols 1 --yscale '1.2' --title CMS --titlePos 0 \
    --chisq none \
    --subtitle ${SUBTITLE} --rrange '0.85' '1.15' \
    --config "${WREM_BASE}/utilities/styles/styles.py"\
    --customFigureWidth 2.5 \
    --subplotSizes 1 1 \
    --lowerLegPos 'upper right'

  # Z gen results
  "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${Z_GEN_FIT}" \
    --poi pdfAlphaS --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '2.0' \
    --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
    --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle ${SUBTITLE} \
    -o "${Z_GEN_RESULTS}"
  "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${Z_GEN_FIT}" \
    --poi pdfAlphaS --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '2.0' \
    --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
    --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle ${SUBTITLE} \
    -o "${Z_GEN_RESULTS}" --globalImpacts

  # WZ gen results
  "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${WZ_GEN_FIT}" \
    --poi pdfAlphaS --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '2.0' \
    --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
    --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle ${SUBTITLE} \
    -o "${WZ_GEN_RESULTS}"
  "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${WZ_GEN_FIT}" \
    --poi massShiftW100MeV --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '100.0' \
    --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
    --impactTitle '<i>m</i><sub>W</sub> in MeV' --title CMS --subtitle ${SUBTITLE} \
    -o "${WZ_GEN_RESULTS}"
    "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${WZ_GEN_FIT}" \
    --poi pdfAlphaS --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '2.0' \
    --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
    --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle ${SUBTITLE} \
    -o "${WZ_GEN_RESULTS}" --globalImpacts
  "${RABBIT_BASE}/bin/rabbit_plot_pulls_and_impacts.py" "${WZ_GEN_FIT}" \
    --poi massShiftW100MeV --config "${WREM_BASE}/utilities/styles/styles.py" --scaleImpacts '100.0' \
    --showNumbers --oneSidedImpacts --grouping min --otherExtensions pdf png -n 50 \
    --impactTitle '<i>m</i><sub>W</sub> in MeV' --title CMS --subtitle ${SUBTITLE} \
    -o "${WZ_GEN_RESULTS}" --globalImpacts
    
  fi