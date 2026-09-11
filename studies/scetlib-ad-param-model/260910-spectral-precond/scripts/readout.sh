#!/bin/bash
# Everything that has to be read once DATASPEC lands, in one go.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-spectral-precond
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
TS=$(date +%y%m%d_%H%M%S)
run() { singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG bash -lc "$1"; }

echo "############ 1/3 four-way comparison"
run "$T/scripts/run_compare.sh" > $T/logs/compare_$TS.log 2>&1 || echo "compare rc=$?"

echo "############ 2/3 postfit curvature census (all four arms)"
run "$T/scripts/run_curvature.sh \
  $CEPH/260910_blinding_final/fitresults_DATABLIND.hdf5 \
  $CEPH/260910_blinding_final/fitresults_DATAPC2.hdf5 \
  $CEPH/260910_spectral/fitresults_DATASPECPF.hdf5 \
  $CEPH/260910_wall_port/fitresults_DATAWALL5.hdf5" > $T/logs/curvature_$TS.log 2>&1 || echo "curv rc=$?"

echo "############ 3/3 trajectory figure"
run "$T/scripts/run_plots.sh" > $T/logs/plots_$TS.log 2>&1 || echo "plots rc=$?"

echo "$TS" > $T/logs/LATEST_READOUT
echo "READOUT_DONE $TS"
