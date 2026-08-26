#!/bin/bash
# Closure against the production CorrZ templates, BOTH ARMS FROM ONE CACHE.
# $1 = threads, $2 = ad_muf_abl mask for the analytic arm, $3 = out subdir
set -u
C=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/cache_260824b
T=/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections
BASE=scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO
D=/home/submit/lavezzo/.claude/jobs/140d052c/tmp/trans
OUT=$HOME/public_html/alphaS/260826_transition_analytic_e2e/closure/${3:-mode1}
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
IC=$D/${4:-incontainer_trans.sh}
NOISE='^X-Math|max_iterations|absl::|cpu_feature_guard|To enable the following|beamfunc::|^INFO:|WARNING: All log'
$SING $IC python3 -u $D/trans_closure.py \
  --corr "$T/${BASE}_CorrZ.pkl.lz4" "$T/${BASE}_pdfas_CorrZ.pkl.lz4" \
  --cache "$C/cache.npz" --conf "$C/cache.conf" --threads "${1:-16}" \
  --mode 1 --abl "${2:-0}" --out "$OUT" 2>&1 | grep -avE "$NOISE"
