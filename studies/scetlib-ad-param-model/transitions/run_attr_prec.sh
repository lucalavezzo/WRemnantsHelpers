#!/bin/bash
# Does the low-qT shortfall shrink when the outer node ladder is TIGHTENED?
# A frozen-quadrature error scales with the target; a modelling gap does not.
set -u
D=/home/submit/lavezzo/.claude/jobs/140d052c/tmp/trans
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
echo "=== prec 1e-5, x2 = 0.35  $(date) ==="
$SING $D/incontainer_trans.sh python3 -u $D/trans_attribute.py \
  --base "$D/base_p5.conf" --knot 2.0 --threads 16 --x2 0.35 \
  --arms shipped anl1 nomuf --qt-lo 18 20 24 28 33 \
  -o "$D/prec5_x2_035.json" > "$D/prec5_x2_035.log" 2>&1
sed -n '/ARM SEPARATION/,$p' "$D/prec5_x2_035.log"
echo "PREC QUEUE DONE $(date)"
