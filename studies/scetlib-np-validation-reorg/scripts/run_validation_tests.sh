#!/bin/bash
# Run the 3 before/after invariance tests for the scetlib_np validation reorg.
# Usage (inside the wmass container):  run_validation_tests.sh <outdir-tag>
#   <outdir-tag> = e.g. "baseline" or "after"  (relative to the study dir)
#
# Captures FULL stdout of each comparison (the per-bin numbers are the invariant
# the reorg must preserve) + the plots. Tests 1/2/3 must be byte-identical
# before vs after the pure-refactor reorg.
set -e   # NOT -u (setup.sh echoes can trip it)
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

STUDY="$MY_WORK_DIR/studies/scetlib-np-validation-reorg"
TAG="${1:?need an output tag, e.g. baseline}"
OUT="$STUDY/$TAG"
mkdir -p "$OUT/plots"

DC="/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260623_Zhistmaker/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_realdata/ZMassDilepton.hdf5"
CORRZ="$WREM_BASE/wremnants-data/data/TheoryCorrections/scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksVals_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4"

echo "=== inputs ==="
echo "datacard  : $DC"
echo "theorycorr: $CORRZ"
echo "btgrid    : (script default _default_btgrid_dir())"
echo

M="wremnants.postprocessing.scetlib_np"

# ---- Test 1: sigma_gen (cardless core) vs theory correction ----
echo "########## TEST 1: sigma_gen vs theory-corr ##########"
python3 -m $M.sigma_gen_at_lambda \
    --datacard "$DC" --meta-from "$DC" \
    --theory-corr "$CORRZ" --plot-axis ptVGen \
    --plot "$OUT/plots/test1_sigmagen_vs_theorycorr.png" \
    > "$OUT/test1_sigmagen_vs_theorycorr.txt" 2>&1 || echo "TEST1 EXIT=$?"
echo "  -> $OUT/test1_sigmagen_vs_theorycorr.txt"

# ---- Tests 2 & 3: sigma_gen AND sigma_reco vs the datacard ----
# validate_agreement --reference card does reco (test 3) + gen (test 2) in one run.
echo "########## TESTS 2+3: sigma_gen & sigma_reco vs datacard ##########"
python3 -m $M.validate_agreement --reference card \
    --datacard "$DC" \
    --outdir "$OUT/plots/test23_paramdiag" \
    > "$OUT/test23_sigma_vs_datacard.txt" 2>&1 || echo "TEST23 EXIT=$?"
echo "  -> $OUT/test23_sigma_vs_datacard.txt"

echo
echo "DONE_OK $(date)"
