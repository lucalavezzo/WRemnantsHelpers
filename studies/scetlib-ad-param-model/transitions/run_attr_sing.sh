#!/bin/bash
set -u
D=/home/submit/lavezzo/.claude/jobs/140d052c/tmp/trans
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
echo "=== SING-ONLY x2_035  $(date) ==="
$SING $D/incontainer_trans.sh python3 -u $D/trans_attribute.py \
  --base "$D/base_sing.conf" --knot 2.0 --threads 8 --x2 0.35 \
  --qt-lo 14 16 18 20 24 28 33 44 \
  -o "$D/attrsing_x2_035.json" > "$D/attrsing_x2_035.log" 2>&1
sed -n '/ARM SEPARATION/,$p' "$D/attrsing_x2_035.log"
echo "SING QUEUE DONE $(date)"
