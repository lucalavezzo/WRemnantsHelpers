#!/bin/bash
# Verification matrix for "the theory correction is the authority for the anchor".
#
# Environment: reuses ../260908-slides-validation/incontainer.sh, which pins
# SCETlib to the FROZEN VALIDATED SNAPSHOT every number in this study was made
# against (b66f8de, MR !9). WRemnants/scetlib-cms/build is stale (Aug 21,
# predating set_matched_partner) and must NOT be used here.
#
# Launch -- see knowledge/10_environment/runtime_bootstrap.md: /cvmfs/ in the
# bind list is NOT optional (SCETlib needs LHAPDF, and without it the failure
# reads as a missing PDF set), it must be `bash -lc` so the LOGIN profile sets
# LHAPDF_DATA_PATH, and the command must be a SCRIPT rather than an inline
# quoted string:
#
#   nohup singularity run --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ \
#       /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest \
#       bash -lc "<this script>" > logs/anchor_checks_$(date +%y%m%d_%H%M%S).log 2>&1 &
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/build
source /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/setup.sh > /dev/null

T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-corr-anchor
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/260908_Z_2D_card_corrgrid770/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CORR=$WREM_BASE/wremnants-data/data/TheoryCorrections/scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4
WORK=$CEPH/study_scratch/260910-anchor-verify
mkdir -p $WORK
cd $WREM_BASE

echo "LHAPDF_DATA_PATH=$LHAPDF_DATA_PATH"
echo "SCETLIB_BUILD=$SCETLIB_BUILD"
python3 -c "import scetlib_qT; print('scetlib_qT:', scetlib_qT.__file__)"

# The 260908 cards predate the writer, so hack the metadata into COPIES.
for M in none refuse warn missing altonly; do
  [ -f $WORK/card_$M.hdf5 ] || python3 $T/scripts/inject_corr_config.py \
      --card $CARD --corr $CORR --out $WORK/card_$M.hdf5 --mutate $M
done

set +e
run () {
  echo ""
  echo "############ TEST $1"
  python3 $T/scripts/check_anchor.py --card "$2" --cache $CACHE/cache.npz \
      --conf $CACHE/cache.conf --model-args "$3" 2>&1 \
      | grep -v -e "absl::InitializeLog" -e "cpu_feature_guard" \
                -e "To enable the following" -e "cuda_platform" -e "^ch0 {" \
                -e "^       " -e "beamfunc grids"
  echo "############ end $1"
}

run "1_unmodified_card_must_REFUSE"         "$CARD"                   ""
run "2_unmodified_card_anchor_source_cache" "$CARD"                   "anchor_source=cache"
run "3_injected_card_must_PASS"             "$WORK/card_none.hdf5"    ""
run "4_pdf_set_mismatch_must_REFUSE"        "$WORK/card_refuse.hdf5"  ""
run "5_lambda2_mismatch_must_WARN"          "$WORK/card_warn.hdf5"    ""
run "6_lambda2_absent_must_REFUSE"          "$WORK/card_missing.hdf5" ""
run "7_lambda2_absent_plus_override"        "$WORK/card_missing.hdf5" "anchor_override=lambda2=0.4"
run "8_altonly_must_REFUSE"                 "$WORK/card_altonly.hdf5" ""
run "9_retired_token_must_RAISE"            "$WORK/card_none.hdf5"    "check_anchor=0"
echo ""
echo "ALL_TESTS_DONE"
