#!/bin/bash
# Validate one arm's cache against the SAME production templates. Nothing here
# depends on the knot spacing: the cache carries its own _muf_lnstep and the
# members' log2 legs, so the evaluation is self-describing.
set -e
TAG="$1"
BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan
CORR=/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
$SING /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/knot_scan/incontainer_knots.sh \
   python3 -u /home/submit/lavezzo/alphaS/WRemnants/scripts/rabbit/scetlib_ad/validate_variations.py \
   --corr "$CORR/scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4" \
          "$CORR/scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_pdfas_CorrZ.pkl.lz4" \
   --cache "$BASE/$TAG/cache.npz" --conf "$BASE/$TAG/cache.conf" \
   --partial --threads 32 "${@:2}"
