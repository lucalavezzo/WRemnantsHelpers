#!/bin/bash
# Clean re-run of the delta_lambda2=0 test (C_dl2frozen0): full fit,hessian,saturated.
# Start point seeded at C's postfit lambdas via xparam_default, with delta_lambda2=0
# and FROZEN. Unlike the original bare rabbit_fit launch (--postfix t0), this writes
# plain fitresults.hdf5 so the hessian/saturated steps chain automatically.
# Launch (from the login node):
#   nohup singularity run --bind /scratch/,/work/,/home/,/ceph/ \
#     /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest \
#     <this script> > logs/260717_2D_C_dl2frozen0_<ts>.log 2>&1 &
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh
python workflows/fitterSCETlibNP.py \
  /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260701_Z_2D/ZMassDilepton_ptll_yll_realdata/ZMassDilepton.hdf5 \
  -d /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260717_2D_C_dl2frozen0/ \
  -m np_model_nu_fit=tanh_6 np_model_fit=tanh_6 \
     xparam_default=lambda2=1.10002,lambda4=-0.60818,lambda2_nu=-0.35987,lambda4_nu=0.15995,delta_lambda2=0,lambda6=0.01,lambda6_nu=0.01 \
  --freeze lambda_inf lambda_inf_nu lambda6 lambda6_nu delta_lambda2 \
  --steps fit,hessian,saturated
