#!/usr/bin/env bash

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <uncert>" >&2
  exit 1
fi

uncert_pattern="$1"
postfix_uncert="${uncert_pattern//[\(\)\/\*\|]/}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fitter_script="$MY_WORK_DIR/workflows/mW/fitterMW.sh"
pulls_script="$MY_WORK_DIR/workflows/mW/pullsAndImpactsMW.sh"

inputs=(
  "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//251006_histmaker_unfoldingMW/mw_with_mu_eta_pt_scetlib_dyturboCorr_maxFiles_m1.hdf5"
  "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//251006_histmaker_unfoldingMW/mw_with_mu_eta_pt_scetlib_dyturboCorr_maxFiles_m1_oneMCfileEvery2.hdf5"
)

echo "Running fitter for ${#inputs[@]} inputs with nuisance pattern '${uncert_pattern}' and postfix fragment '${postfix_uncert}'"
for input in "${inputs[@]}"; do
  echo "-> ${input}"
  postfix_suffix=""
  if [[ $input == *oneMCfileEvery2.hdf5 ]]; then
    postfix_suffix="_oneMCfileEvery2"
  fi
  postfix="breitwigner_${postfix_uncert}${postfix_suffix}"
  echo "$fitter_script $input" \
    -e "--postfix ${postfix} --excludeNuisances '.*' --keepNuisances '(dummy|massShift*|${uncert_pattern})' --breitwignerWMassWeights " \
    -f " --noBinByBinStat "
  "$fitter_script" "$input" \
    -e " --postfix ${postfix} --excludeNuisances '.*' --keepNuisances '(dummy|massShift*|${uncert_pattern})' --breitwignerWMassWeights " \
    -f " --noBinByBinStat "
done

result_half="/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//251006_histmaker_unfoldingMW/WMass_pt_eta_charge_breitwigner_${postfix_uncert}_oneMCfileEvery2/fitresults.hdf5"
result_full="/ceph/submit/data/group/cms/store/user/lavezzo/alphaS//251006_histmaker_unfoldingMW/WMass_pt_eta_charge_breitwigner_${postfix_uncert}/fitresults.hdf5"

echo "$pulls_script" "$result_half" \
  -e " -r ${result_full} --refName full --name '1/2 MC' --postfix breitwigner_exclude${postfix_uncert}_oneMCfileEvery2" \
  -o $MY_PLOT_DIR/$(date +%y%m%d)_mW_pulls_and_impacts_excludeUncerts/

"$pulls_script" "$result_half" \
  -e " -r ${result_full} --refName full --name '1/2 MC' --postfix breitwigner_exclude${postfix_uncert}_oneMCfileEvery2" \
  -o $MY_PLOT_DIR/$(date +%y%m%d)_mW_pulls_and_impacts_excludeUncerts/
