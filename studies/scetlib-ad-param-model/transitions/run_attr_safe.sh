#!/bin/bash
# THE GATE. x1,x3 FIRST -- every construction in this project has been designed
# on the x2 legs and broken on the x1,x3 leg, whose displacement leaves the
# collapsed stencil by up to 8x (A1 = 8.0 at qT 26, large bT).
set -u
D=/home/submit/lavezzo/.claude/jobs/140d052c/tmp/safeint
B=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
run () {
  tag="$1"; shift
  echo "=== $tag  $(date) ==="
  $SING $D/incontainer_safeint.sh python3 -u $D/trans_attribute.py \
    --base "$B" --knot 2.0 --threads 8 --with-safe \
    --arms shipped anl1 anl1cub anl1quart anl1bq03 anl1bq1 anl1bq1a anl1clip anl1bc1 anl1herm \
    --qt-lo 18 20 24 28 33 44 \
    -o "$D/safe_$tag.json" "$@" > "$D/safe_$tag.log" 2>&1
  sed -n '/ARM SEPARATION/,$p' "$D/safe_$tag.log"
}
run x1x3   --x1 0.3 --x3 0.9
run x2_035 --x2 0.35
run x2_055 --x2 0.55
run x2_075 --x2 0.75
echo "SAFE QUEUE DONE $(date)"
