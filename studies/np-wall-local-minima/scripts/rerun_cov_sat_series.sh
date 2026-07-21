#!/bin/bash
# Re-run hessian(cov)+saturated for the wall fits whose cov OOM-killed when run
# 6-at-once. SERIES: one ~32 GB cov step at a time, so no memory collapse. The
# fit step already wrote each dir's fitresults.hdf5; hessian/saturated inherit the
# model/freeze/wall(margin) from its meta (read_inherited). minus0p05 already
# completed the full chain, so it is NOT in this list.
# Launch (from login node):
#   setsid nohup singularity exec --bind /scratch/,/work/,/home/,/ceph/ <img> \
#     bash rerun_cov_sat_series.sh > logs/rerun_covsat_series_<ts>.log 2>&1 < /dev/null &
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
export THREADS=32
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CARD=$CEPH/260701_Z_2D/ZMassDilepton_ptll_yll_realdata/ZMassDilepton.hdf5
for d in 260717_2D_wallmargin_plus0p005 \
         260717_2D_wallmargin_0 \
         260717_2D_wallmargin_minus0p02 \
         260717_2D_wallmargin_minus0p10 \
         260717_2D_wall_dl2frozen0; do
  echo "############## $d : hessian,saturated ($(date +%H:%M:%S)) ##############"
  # clear the partial cov/ (OOM-killed mid-write) so rabbit writes clean
  rm -rf "$CEPH/$d/cov" "$CEPH/$d/saturated"
  python workflows/fitterSCETlibNP.py "$CARD" -d "$CEPH/$d" --steps hessian,saturated \
    || echo "!!!!! $d FAILED (continuing to next) !!!!!"
done
echo "########## ALL COV+SAT DONE ($(date +%H:%M:%S)) ##########"
