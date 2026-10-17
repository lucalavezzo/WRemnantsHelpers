#!/usr/bin/env bash
# Writes cmds/<NAME>.inner.sh for one saturated-sub-fit-only run from LAT's final result.
# usage: make_inner.sh NAME RABBIT_WORKTREE MODE   (MODE: tc | tcpc | krylovpc | krylov)
set -eu
NAME=$1; RB=$2; MODE=$3
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ct18z-nominal-fits/261016-saturated-subfit-diagnosis
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_saturated_subfit_diagnosis
LATDIR=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25
LATREG="-r wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTerm wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping"
TC="--constraints wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDomainConstraints margin=0 --minimizerMethod trust-constr --earlyStopping -1 --maxRestarts 0 --minimizerGtol 1e-8 --minimizerXtol 1e-10 --minimizerBarrierTol 1e-9 --minimizerMaxiter 600"
WALL="-r wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping margin=0 --earlyStopping 100"
PC="--precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral"
case $MODE in
  tc) MIN="$TC" ;;
  tcpc) MIN="$TC $PC" ;;
  krylovpc) MIN="$WALL $PC" ;;
  krylov) MIN="$WALL" ;;
  *) echo "bad mode"; exit 2 ;;
esac
cat > $T/cmds/$NAME.inner.sh <<EOI
#!/usr/bin/env bash
# $NAME: saturated ptll sub-fit only, from LAT's final postfit (mode $MODE, rabbit $RB)
set -f
cd /tmp
export PYTHONPATH=$RB:\${PYTHONPATH:-}
echo "[run] \$(date -Is) host \$(hostname) rabbit worktree $RB @ \$(git -C $RB rev-parse --short HEAD)"
python3 -c "import rabbit, scetlib_tf; print('[run] rabbit from', rabbit.__file__)"
python3 $RB/bin/rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix $NAME \\
  --externalPostfit $LATDIR/fitresults_LAT.hdf5 --noFit --saveHists \\
  -m Project ch0 ptll --computeSaturatedProjectionTests \\
  --regularizationStrength 8 $LATREG \\
  $MIN \\
  --snapshotFile $OUT/snapshot_fitresults_$NAME.hdf5 --snapshotInterval 0.25 \\
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \\
  cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128 -v 4
echo "[run] \$(date -Is) exit \$?"
EOI
echo "wrote $T/cmds/$NAME.inner.sh"
