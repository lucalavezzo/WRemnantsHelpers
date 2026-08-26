#!/bin/bash
# Is the PURE analytic model with the full alphas^3 evolution AND the c_i1 term
# what closes qT 20-24? Its conv-level error at qT 22 is -0.03%, against -7% for
# the mode-1 truncation -- and the residual construction is blind to the
# difference by the degree-2 identity, so only the PURE arm can show it.
set -u
D=/home/submit/lavezzo/.claude/jobs/140d052c/tmp/trans
B=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
run () {
  tag="$1"; shift
  echo "=== $tag  $(date) ==="
  $SING $D/incontainer_trans3.sh python3 -u $D/trans_attribute.py \
    --base "$B" --knot 2.0 --threads 8 --with-i1 --with-mode3 \
    --arms shipped anl1 nomuf anl3 anl1i1only anl3only anl3i1only anl3i1 \
    --qt-lo 18 20 24 28 33 44 \
    -o "$D/m3_$tag.json" "$@" > "$D/m3_$tag.log" 2>&1
  sed -n '/ARM SEPARATION/,$p' "$D/m3_$tag.log"
}
run x2_035 --x2 0.35
run x2_055 --x2 0.55
echo "M3 QUEUE DONE $(date)"
