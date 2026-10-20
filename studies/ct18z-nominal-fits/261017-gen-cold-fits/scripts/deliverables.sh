#!/usr/bin/env bash
# Standard post-fit deliverables for one gen-level fit (run inside the container, all3-bf rabbit prepended):
#   agent_setup.sh --prepend-pythonpath /work/submit/lavezzo/rabbit-all3-bf -- bash deliverables.sh GEN_NOLAT|GEN_LAT
# 1. pulls + traditional & global impacts (workflows/pullsAndImpacts.sh, POI alphaS)
# 2. postfit ptVGen / absYVGen projections with the saturated-projection chi2 (plotPtll.sh's rabbit_plot_hists call,
#    with the gen-level mapping instead of 'Project ch0 ptll')
# 3. NP functions (workflows/plotNPFunctions.sh), single fit
PF=$1
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/ct18z-nominal-fits/261017-gen-cold-fits
FR=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_gen_nominal_fits/fitresults_${PF}_PF.hdf5
mkdir -p $T/$PF
bash $H/workflows/pullsAndImpacts.sh $FR -o $T/$PF/impacts -P alphaS > $T/$PF/impacts.out 2>&1; echo "impacts rc $?"
for ax in ptVGen absYVGen; do
  rabbit_plot_hists.py $FR -m "Project chSigmaUL $ax" --config "${WREM_BASE}/wremnants/utilities/styles/styles.py" \
    --title CMS --titlePos 0 --subtitle Preliminary -o $T/$PF/postfit --yscale 1.25 > $T/$PF/postfit_$ax.out 2>&1
  echo "postfit $ax rc $?"
done
bash $H/workflows/plotNPFunctions.sh $PF=$FR -o $T/$PF/np_functions > $T/$PF/np.out 2>&1; echo "np rc $?"
