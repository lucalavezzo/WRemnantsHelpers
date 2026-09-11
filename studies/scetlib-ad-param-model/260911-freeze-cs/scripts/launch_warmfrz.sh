#!/bin/bash
# THE BASIN-CONTROLLED SCAN.  Same freeze as launch_frzcs.sh, but started from
# the PLAIN arm's own postfit with only the two CS parameters moved to the
# frozen target (scripts/make_seed.py).  That is the operational form of
# knowledge/.../np_parametrization_constraints.md §11 item 3: "stand at the
# plain minimum, fix the CS kernel, reminimise, and see how far alpha_s moves".
#
# WHY IT IS NEEDED.  The COLD scan (launch_frzcs.sh) changes two things at once.
# At lambda2_nu = 0.15 the cold arm landed 2.07-2.86 away in L2 from every other
# arm -- including 1.96-2.55 in the 41 non-NP parameters -- i.e. in a different
# basin, and ../260910-basins measured alpha_s to be basin-dependent at the
# 3.5 sigma level on this card.  So the cold 0.15 point's alpha_s is not a clean
# CS response, and the warm arm separates the two effects.
#
# --noPostfitProfileBB IS REQUIRED with --externalPostfit under --noBinByBinStat
# or load_fitresult dies in _profile_beta AFTER writing a ~44 KB stub.  It also
# switches which "Linear chi2" is printed (../260910-basins finding 8), so that
# statistic is not comparable to the cold arms'.  The saturated 2*dNLL is.
#
# The frozen value comes from the SEED, not from xparam_default: freeze_params()
# runs in Fitter.__init__ and load_fitresult() runs after it, so the seed wins.
# xparam_default is still passed so the PRIOR MEAN of lambda2_nu moves with it
# and the frozen parameter contributes zero prior penalty, keeping the losses
# comparable across scan points exactly as in the cold scan.
#
# usage: launch_warmfrz.sh <000|050|087|150|190>
set -e
TAG=$1
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-freeze-cs
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260911_freeze_cs
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
M="cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128"
case $TAG in
  000) TH=-1.5  ;;
  050) TH=-1.0  ;;
  087) TH=-0.63 ;;
  150) TH=0.0   ;;
  190) TH=0.4   ;;
  *) echo "usage: launch_warmfrz.sh <000|050|087|150|190>"; exit 2 ;;
esac
SEED=$OUT/seeds/seed_plain_L$TAG.hdf5
POSTFIX=WFRZ$TAG
LOG=$T/logs/fit_${POSTFIX}_$(date +%y%m%d_%H%M%S).log
echo "$LOG" > $T/logs/LATEST_$POSTFIX
echo "[warmfrz] tag=$TAG theta=$TH seed=$SEED"
exec $T/scripts/run.sh $LOG \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix $POSTFIX -t 0 --earlyStopping 100 \
    --externalPostfit $SEED --noPostfitProfileBB \
    --freezeParameters lambda2_nu lambda4_nu \
    --snapshotFile $OUT/snapshot_$POSTFIX.hdf5 --snapshotInterval 0.25 \
    --saveHists --computeHistErrors \
    --paramModel $MODEL $M xparam_default=lambda2_nu=$TH
