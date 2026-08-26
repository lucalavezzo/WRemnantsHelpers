#!/bin/bash
set -e
J=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/nak
OUT=/home/submit/lavezzo/public_html/alphaS/260825_transition_muf_coordinate_fix/knots
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
P="$SING /home/submit/lavezzo/.claude/jobs/140d052c/tmp/incontainer_nak_lean.sh python3 /home/submit/lavezzo/.claude/jobs/140d052c/tmp/plot_knot_response.py"
$P --json $J/fix_x2_035_k2.json $J/fix_x2_035_ksqrt2.json \
   --label "model, muF knots f=2 (production)" "model, muF knots f=sqrt2" \
   --title "transition_points 0.2_0.35_1.0 (FINITE variation)" \
   --name knots_x2_035 --outdir $OUT
$P --json $J/fix_x2_075_k2.json $J/fix_x2_075_ksqrt2.json \
   --label "model, muF knots f=2 (production)" "model, muF knots f=sqrt2" \
   --title "transition_points 0.2_0.75_1.0 (FINITE variation)" \
   --name knots_x2_075 --outdir $OUT
$P --json $J/fix_x2_055_k2.json $J/fix_x2_055_ksqrt2.json $J/fix_x2_055_k4.json \
   --label "model, muF knots f=2 (production)" "model, muF knots f=sqrt2" "model, muF knots f=4" \
   --title "transition_points 0.2_0.55_1.0 (NEAR-ANCHOR probe)" \
   --name knots_x2_055 --outdir $OUT
