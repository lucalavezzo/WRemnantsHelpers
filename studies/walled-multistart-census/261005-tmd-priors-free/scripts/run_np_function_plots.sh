#!/usr/bin/env bash
# NP functions NOMTMDFREE (num) vs NOMSTIFF (den) with the existing plotter (param-model tree), raw-λ mode,
# pattern: 261005-np-forms-lattice/scripts/run_np_function_plots.sh. Physical λ + Hessian cov (fitted λ block) from
# cov_<TAG>.json written by compare.py. Held: λ_inf=1, λ4_ν=0, λ_inf_ν=2.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/261005-tmd-priors-free
PM=/home/submit/lavezzo/alphaS/WRemnants-scetlib-np-param-model
lam() { python3 -c "import json;d=json.load(open('$T/cov_$1.json'));print(','.join(f'{n}={m:.6g}' for n,m in zip(d['names'],d['mu']))+',lambda_inf=1,lambda4_nu=0,lambda_inf_nu=2')"; }
NUM=$(lam NOMTMDFREE); DEN=$(lam NOMSTIFF)
echo "num: $NUM"; echo "den: $DEN"
singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest \
  bash -lc "source /opt/venv/bin/activate; cd $PM; PYTHONPATH=$PM:/home/submit/lavezzo/alphaS/WRemnants/wums:\$PYTHONPATH python3 -m wremnants.postprocessing.scetlib_np.np_function_plots \
  --num-np-model tanh_2 --num-np-model-nu tanh_2 --den-np-model tanh_2 --den-np-model-nu tanh_2 \
  --num-lambdas $NUM --num-label postfit_NOMTMDFREE_TMD_priors_free --num-cov $T/cov_NOMTMDFREE.json \
  --den-lambdas $DEN --den-label postfit_NOMSTIFF --den-cov $T/cov_NOMSTIFF.json \
  --n-toys 1000 --no-prefit --y 0 1 2 2.5 --bT-max 4.0 -o $T/np_functions_NOMTMDFREE_vs_NOMSTIFF.png"
