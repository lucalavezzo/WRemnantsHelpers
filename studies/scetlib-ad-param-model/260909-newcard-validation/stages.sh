#!/bin/bash
# Every command in COMMANDS.md, run for real, all plots into THIS directory.
set -u
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260909-newcard-validation
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CORRDIR=/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections
BASE=scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/260908_Z_2D_card_acceptfix/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
HM=$CEPH/260908_Z_histmaker_acceptfix/mz_dilepton_${BASE}_Corr_maxFiles_m1_corrgrid.hdf5
CORR_MAIN=$CORRDIR/${BASE}_CorrZ.pkl.lz4
CORR_AS=$CORRDIR/${BASE}_pdfas_CorrZ.pkl.lz4
CORR_PDF=$CORRDIR/${BASE}_pdfvars_CorrZ.pkl.lz4
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
FITOUT=$CEPH/study_scratch/260909-newcard-validation
mkdir -p $FITOUT
M="cache=$CACHE/cache.npz conf=$CACHE/cache.conf"

case "$1" in

# ---- Validation 2: sigma_reco vs the histmaker nominal (SHAPE) --------------
reco)
  python3 scripts/rabbit/scetlib_ad/validate_reco.py \
    --datacard $CARD --histmaker $HM \
    --cache $CACHE/cache.npz --conf $CACHE/cache.conf \
    --reference histmaker --threads 48 --tag card770 \
    --plot-dir $T/reco_central --plot-axes ptll yll ;;

# ---- Validation 2b: the same, ABSOLUTE (no global scale) -------------------
reco_abs)
  # --reference card, NOT histmaker.  The absolute comparison divides by
  # indata.norm's signal column and scales the model by the PHYSICAL
  # k = lumi*1000 (plus the x2 |Y| fold); against the histmaker there is no k,
  # so the model comes out ~1e-5 of the reference and the number is meaningless.
  python3 scripts/rabbit/scetlib_ad/validate_reco.py \
    --datacard $CARD \
    --cache $CACHE/cache.npz --conf $CACHE/cache.conf \
    --reference card --no-match-norm --threads 48 --tag acceptfix_abs \
    --plot-dir $T/reco_absolute --plot-axes ptll yll ;;

# ---- Validation 3a: variations at GEN level vs the correction --------------
gen_vars)
  python3 scripts/rabbit/scetlib_ad/validate_variations.py \
    --corr $CORR_MAIN $CORR_AS $CORR_PDF \
    --cache $CACHE/cache.npz --conf $CACHE/cache.conf \
    --threads 48 --profile --plot-dir $T/gen_variations ;;

# ---- Validation 3b: variations at RECO level vs the histmaker templates ----
reco_vars)
  python3 scripts/rabbit/scetlib_ad/validate_variations_reco.py \
    --datacard $CARD --histmaker $HM \
    --cache $CACHE/cache.npz --conf $CACHE/cache.conf \
    --corr nominal_ptll_yll_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_Corr \
           nominal_ptll_yll_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_pdfas_Corr \
           nominal_ptll_yll_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_pdfvars_Corr \
    --threads 64 --plot-dir $T/reco_variations --csv $T/reco_variations.csv ;;

# ---- Fit 1: Asimov ---------------------------------------------------------
# --saveHists --computeHistErrors are ADDED relative to the recorded AS770
# config, so there is something to plot postfit.  They do not change the fit.
asimov)
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $FITOUT \
    --postfix AS770 --saveHists --computeHistErrors \
    --paramModel $MODEL $M threads=48 ;;

# ---- Fit 2: one toy, all NPs frozen ---------------------------------------
toy)
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $FITOUT \
    --postfix TOY770NP -t 1 --earlyStopping 100 \
    --saveHists --computeHistErrors \
    --freezeParameters lambda2 lambda4 delta_lambda2 lambda2_nu lambda4_nu \
    --paramModel $MODEL $M threads=256 ;;

*) echo "unknown stage $1"; exit 2 ;;
esac
