#!/usr/bin/env bash
# pulls + impacts of the walled card-A fits, sorted by |pull| (workflows/pullsAndImpacts.sh, -s abspull)
set -uo pipefail
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/lattice-cs-kernel/260924-ptll-tension-localization
for spec in LATL4ZWALLCOLD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260923_lattice_fits/l4zero_walled/fitresults_LATL4ZWALLCOLD.hdf5 \
            CCWALLCOLDR=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260917_cc_fits_wall/fitresults_CCWALLCOLDR.hdf5 \
            CCWALLWARMPF=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260917_cc_fits_wall/fitresults_CCWALLWARMPF.hdf5; do
  tag=${spec%%=*}; f=${spec#*=}
  bash /home/submit/lavezzo/alphaS/WRemnantsHelpers/workflows/pullsAndImpacts.sh $f -o $T/pulls_abspull/$tag -P alphaS -e "-s abspull" 2>&1 | tee $T/logs/pulls_abspull_$tag.log
done
