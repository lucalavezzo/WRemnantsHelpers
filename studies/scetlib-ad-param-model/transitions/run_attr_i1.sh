#!/bin/bash
set -u
D=/home/submit/lavezzo/.claude/jobs/140d052c/tmp/trans
B=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
run () {
  tag="$1"; shift
  echo "=== $tag  $(date) ==="
  $SING $D/incontainer_trans2.sh python3 -u $D/trans_attribute.py \
    --base "$B" --knot 2.0 --threads 8 --with-i1 \
    --arms shipped anl1 anl1i1 anl1i1only nomuf \
    --qt-lo 14 16 18 20 24 28 33 44 \
    -o "$D/i1_$tag.json" "$@" > "$D/i1_$tag.log" 2>&1
  sed -n '/ARM SEPARATION/,$p' "$D/i1_$tag.log"
}
run x2_035 --x2 0.35
run x2_055 --x2 0.55
echo "I1 QUEUE DONE $(date)"
