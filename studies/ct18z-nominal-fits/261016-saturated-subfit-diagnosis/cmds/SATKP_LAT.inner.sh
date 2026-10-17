#!/usr/bin/env bash
# SATKP_LAT: saturated ptll sub-fit only, from LAT's final postfit (mode krylovpc, rabbit /work/submit/lavezzo/rabbit-satdiag-base)
set -f
cd /tmp
export PYTHONPATH=/work/submit/lavezzo/rabbit-satdiag-base:${PYTHONPATH:-}
echo "[run] $(date -Is) host $(hostname) rabbit worktree /work/submit/lavezzo/rabbit-satdiag-base @ $(git -C /work/submit/lavezzo/rabbit-satdiag-base rev-parse --short HEAD)"
python3 -c "import rabbit, scetlib_tf; print('[run] rabbit from', rabbit.__file__)"
python3 /work/submit/lavezzo/rabbit-satdiag-base/bin/rabbit_fit.py /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5 --jitCompile off -o /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_saturated_subfit_diagnosis -t 0 --postfix SATKP_LAT \
  --externalPostfit /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits/fitresults_LAT.hdf5 --noFit --saveHists \
  -m Project ch0 ptll --computeSaturatedProjectionTests \
  --regularizationStrength 8 -r wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTerm wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping \
  -r wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingWall wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping margin=0 --earlyStopping 100 --precondition --preconditionParams '.*' --preconditionBlocks none --preconditionTransform spectral \
  --snapshotFile /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261016_saturated_subfit_diagnosis/snapshot_fitresults_SATKP_LAT.hdf5 --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
  cache=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25/cache.npz conf=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25/cache.conf threads=128 -v 4
echo "[run] $(date -Is) exit $?"
