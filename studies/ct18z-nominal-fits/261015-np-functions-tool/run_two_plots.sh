#!/usr/bin/env bash
# RETIRED 2026-10-15: scripts/np_functions/ was deleted (superseded by scetlib_ad/np_function_plots); kept as the record of the runs.
# The DEFAULT output (cs_kernel + tmd_bc) for LATFROZ_V3 + XWSTIFF, through the workflow wrapper.
# two_plots/: with the lattice-only band (stage 1 with SCETlib); two_plots/no_lattice/: --no-lattice (reader only).
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
O=$H/studies/ct18z-nominal-fits/261015-np-functions-tool/two_plots
F="LATFROZ_V3=$A/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5 XWSTIFF=$A/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5"
L="--label 'LATFROZ_V3=Z + lattice (LATFROZ V3)' --label 'XWSTIFF=Z only (XWSTIFF)'"
bash $H/workflows/plotNPFunctions.sh $F -o $O -e "$L" && \
bash $H/workflows/plotNPFunctions.sh $F -o $O/no_lattice -e "$L --no-lattice"
