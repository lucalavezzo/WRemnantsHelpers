#!/bin/bash
# One (x2, knot) point of the isolated interpolation-error A/B, on the
# near-anchor-knots build (muF coordinate fix + settable knot spacing).
set -e
X2="$1"; KNOT="$2"; TAG="$3"; ENTRY="${4:-incontainer_nak_lean.sh}"
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/nak
BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
$SING /home/submit/lavezzo/.claude/jobs/140d052c/tmp/$ENTRY \
   python3 -u /home/submit/lavezzo/.claude/jobs/140d052c/tmp/knot_interp_error.py \
   --base "$BASE" --x2 "$X2" --knot "$KNOT" --threads 8 -o "$OUT/$TAG.json"
