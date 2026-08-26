#!/bin/bash
# Analytic-muF closure A/B on the 210-bin production cache, both arms from ONE
# cache: mode 1 needs no extra conv kinds, so cache_260824b (written by a
# different build, three-knot stencil, no analytic term) loads unchanged.
set -u
C=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/cache_260824b
T=/home/submit/lavezzo/alphaS/WRemnants/wremnants-data/data/TheoryCorrections
BASE=scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO
OUT=$HOME/public_html/alphaS/260826_analytic_muf_dglap/closure
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
IC=/home/submit/lavezzo/.claude/jobs/140d052c/tmp/anlmuf/incontainer_anlmuf.sh
NOISE='^X-Math|max_iterations|absl::|cpu_feature_guard|To enable the following|beamfunc::|^INFO:'
$SING $IC python3 -u /home/submit/lavezzo/.claude/jobs/140d052c/tmp/anlmuf/anlmuf_closure.py \
  --corr "$T/${BASE}_CorrZ.pkl.lz4" "$T/${BASE}_pdfas_CorrZ.pkl.lz4" \
  --cache "$C/cache.npz" --conf "$C/cache.conf" --threads "${1:-24}" \
  --mode 1 --out "$OUT" 2>&1 | grep -avE "$NOISE"
