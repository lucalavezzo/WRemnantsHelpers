#!/bin/bash
# Resume after the submit82 reboot cut the series mid-run. All fit steps survived.
# +0.005: cov (115M) survived, only saturated was cut off -> saturated only.
# 0, -0.02, -0.10, +dl2=0: cov is still the OOM stub -> full hessian,saturated.
# -0.05 already fully complete -> not here. SERIES (one ~32 GB cov at a time).
# Launch:
#   setsid nohup singularity exec --bind /scratch/,/work/,/home/,/ceph/ <img> \
#     bash rerun_covsat_after_reboot.sh > logs/rerun_covsat2_<ts>.log 2>&1 < /dev/null &
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
export THREADS=32
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CARD=$CEPH/260701_Z_2D/ZMassDilepton_ptll_yll_realdata/ZMassDilepton.hdf5
run_full() {
  echo "############## $1 : hessian,saturated ($(date +%H:%M:%S)) ##############"
  rm -rf "$CEPH/$1/cov" "$CEPH/$1/saturated"
  python workflows/fitterSCETlibNP.py "$CARD" -d "$CEPH/$1" --steps hessian,saturated \
    || echo "!!!!! $1 FAILED (continuing) !!!!!"
}
run_sat() {
  echo "############## $1 : saturated only, cov kept ($(date +%H:%M:%S)) ##############"
  rm -rf "$CEPH/$1/saturated"
  python workflows/fitterSCETlibNP.py "$CARD" -d "$CEPH/$1" --steps saturated \
    || echo "!!!!! $1 FAILED (continuing) !!!!!"
}
run_sat  260717_2D_wallmargin_plus0p005
run_full 260717_2D_wallmargin_0
run_full 260717_2D_wallmargin_minus0p02
run_full 260717_2D_wallmargin_minus0p10
run_full 260717_2D_wall_dl2frozen0
echo "########## ALL COVSAT-RESUME DONE ($(date +%H:%M:%S)) ##########"
