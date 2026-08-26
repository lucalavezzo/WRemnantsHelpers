#!/bin/bash
# validate_variations on cache_260824b, with the SCETlib build chosen by $2.
set -e
OUTDIR="$1"; ENTRY="$2"; shift 2
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/cache_260824b
CORR=/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
$SING /home/submit/lavezzo/.claude/jobs/140d052c/tmp/$ENTRY \
   python3 -u /home/submit/lavezzo/alphaS/WRemnants/scripts/rabbit/scetlib_ad/validate_variations.py \
   --corr "$CORR/scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4" \
          "$CORR/scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_pdfas_CorrZ.pkl.lz4" \
   --cache "$CACHE/cache.npz" --conf "$CACHE/cache.conf" \
   --threads 32 --plot-dir "$OUTDIR" "$@"
