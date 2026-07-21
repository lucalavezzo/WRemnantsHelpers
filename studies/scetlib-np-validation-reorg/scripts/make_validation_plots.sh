#!/bin/bash
# Produce the 3 validation plots via the two user endpoints, into a dated webdir.
#   1. σ_gen (cardless core) vs theory correction   [sigma_gen_at_lambda]
#   2. σ_gen  vs the datacard                        [validate_agreement --reference card]
#   3. σ_reco vs the datacard                        [validate_agreement --reference card]
# (2 and 3 come from the SAME card run: gen_*.png and reco_*.png.)
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

WEBDIR="$MY_PLOT_DIR/260702_scetlib_np_validation"
mkdir -p "$WEBDIR"

DC="/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260623_Zhistmaker/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_realdata/ZMassDilepton.hdf5"
CORRZ="$WREM_BASE/wremnants-data/data/TheoryCorrections/scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4"
M="wremnants.postprocessing.scetlib_np"

echo "webdir: $WEBDIR"

# ---- 1. σ_gen vs theory correction (ptVGen projection + ratio + differential diff) ----
python3 -m $M.sigma_gen_at_lambda \
    --datacard "$DC" --meta-from "$DC" \
    --theory-corr "$CORRZ" --plot-axis ptVGen \
    --plot "$WEBDIR/1_sigma_gen_vs_theorycorr.png"

# ---- 2 + 3. σ_gen and σ_reco vs the datacard (writes gen_*.png AND reco_*.png) ----
python3 -m $M.validate_agreement --reference card \
    --datacard "$DC" \
    --outdir "$WEBDIR"

echo "DONE_OK $(date)"
echo "  1. σ_gen vs theory-corr : $WEBDIR/1_sigma_gen_vs_theorycorr.png"
echo "  2. σ_gen  vs datacard   : $WEBDIR/gen_ptVGen.png , gen_absYVGen.png"
echo "  3. σ_reco vs datacard   : $WEBDIR/reco_ptll.png , reco_yll.png , reco_cosThetaStarll_quantile.png , reco_phiStarll_quantile.png"
