#!/bin/bash
set -u
D=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260827-mr9-default-on
C=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/cache_260824b
T=/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections
BASE=scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
NOISE='^X-Math|max_iterations|absl::|cpu_feature_guard|To enable the following|beamfunc::|^INFO:|WARNING: All log'
$SING $D/incontainer_mr9.sh python3 -u $D/mr9_default_on.py \
  --corr "$T/${BASE}_CorrZ.pkl.lz4" "$T/${BASE}_pdfas_CorrZ.pkl.lz4" \
  --cache "$C/cache.npz" --conf "$C/cache.conf" --threads "${1:-16}" \
  --reps "${2:-3}" --npz $D/mr9_default_on.npz 2>&1 | grep -avE "$NOISE"
