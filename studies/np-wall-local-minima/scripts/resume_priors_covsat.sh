#!/bin/bash
# Resume the priors sigma=0.5 run: fit is already complete on ceph, so run only
# the cov (hessian) + saturated steps. Model/freeze/priors are inherited from the
# fit postfit meta_info (read_inherited in fitterSCETlibNP), so no -m/--freeze here.
# Launch (from the login node):
#   nohup singularity run --bind /scratch/,/work/,/home/,/ceph/ \
#     /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest \
#     <this script> > logs/260717_2D_priors_sig0p5_covsat_<ts>.log 2>&1 &
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
python workflows/fitterSCETlibNP.py \
  /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260701_Z_2D/ZMassDilepton_ptll_yll_realdata/ZMassDilepton.hdf5 \
  -d /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260717_2D_priors_sig0p5/ \
  --steps hessian,saturated
