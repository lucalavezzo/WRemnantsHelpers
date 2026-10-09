#!/usr/bin/env bash
# NP functions with the existing plotter (wremnants.postprocessing.scetlib_np.np_function_plots, param-model tree), raw-λ mode.
# den = lattice-constrained prefit (TMD at the card anchor; CS at the 1D lattice refit λ2_ν = 0.134549, λ4_ν = 0).
# num = walled warm lattice postfit: physical λ from scripts/dump_np_cov.py (np_lambdas_cov.json).
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261005-np-forms-lattice
PM=/home/submit/lavezzo/alphaS/WRemnants-scetlib-np-param-model
run() { singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest \
  bash -lc "source /opt/venv/bin/activate; cd $PM; PYTHONPATH=$PM:/home/submit/lavezzo/alphaS/WRemnants/wums:\$PYTHONPATH python3 -m wremnants.postprocessing.scetlib_np.np_function_plots $*"; }
COMMON="--num-np-model tanh_2 --num-np-model-nu tanh_2 --den-np-model tanh_2 --den-np-model-nu tanh_2 --den-lambdas lambda2=0.4,lambda4=0.4,delta_lambda2=0,lambda_inf=1,lambda2_nu=0.134549,lambda4_nu=0,lambda_inf_nu=2 --den-label prefit_lattice_constrained --den-cov /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261005-np-forms-lattice/cov_prefit_lattice.json --n-toys 1000 --no-prefit --y 0 1 2 2.5 --bT-max 4.0"
run $COMMON --num-lambdas lambda2=0.029006,lambda4=0.087324,delta_lambda2=-0.003902,lambda_inf=1,lambda2_nu=0.063385,lambda4_nu=0,lambda_inf_nu=2 --num-label postfit_LATL4ZY35WALLWARM --num-cov /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261005-np-forms-lattice/cov_LATWARM.json -o $T/np_functions_prefit_vs_LATL4ZY35WALLWARM.png
run $COMMON --num-lambdas lambda2=0.025581,lambda4=0.087583,delta_lambda2=-0.004093,lambda_inf=1,lambda2_nu=0.06427,lambda4_nu=0,lambda_inf_nu=2 --num-label postfit_NOMSTIFF --num-cov /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261005-np-forms-lattice/cov_NOMSTIFF.json -o $T/np_functions_prefit_vs_NOMSTIFF.png
