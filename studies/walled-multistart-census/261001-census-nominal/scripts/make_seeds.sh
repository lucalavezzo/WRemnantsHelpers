#!/usr/bin/env bash
# T4 census seeds (run OUTSIDE the container; wraps incontainer.sh). No cache load.
# Generator: T3's make_random_starts.py (run read-only from its task dir). Ref = NOMSTIFF. Master seed 20261001
# (T3's test draws used 20260930). SeedSequence(S).spawn(n): seed k depends only on (S, k), so the step-0 variants
# with --n 3 reproduce the census seeds 000-002 component by component.
set -euo pipefail
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census
GEN=$T/260930-random-starts/scripts/make_random_starts.py
I=$T/261001-census-nominal/scripts/incontainer.sh
REF=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5
O=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261001_census_nominal/seeds
S=20261001
mkdir -p $O/step0
# census: 8 perturbed (s=0.5, NP uniform over T3 default physical boxes, alphaS u ~ U[-2,2]) + 2 cold_except_alphas (u ~ U[-2,2])
$I python3 $GEN --ref $REF --n 8 --seed $S --s 0.5 --alphas-u 2 --out $O --prefix pert \
   --plot-sample 3000 --plot-dir $T/261001-census-nominal --plot-name np_lambda_draws_census
$I python3 $GEN --ref $REF --n 2 --seed $S --mode cold_except_alphas --cold-alphas-u 2 --out $O --prefix cold
# step 0 variants for seeds 000-002 (alphaS at the reference in a, b, c0)
$I python3 $GEN --ref $REF --n 3 --seed $S --s 0   --alphas-u 0 --out $O/step0 --prefix a_nponly
$I python3 $GEN --ref $REF --n 3 --seed $S --s 0.5 --alphas-u 0 --no-np-draw --out $O/step0 --prefix b_nonnponly
$I python3 $GEN --ref $REF --n 3 --seed $S --s 0.5 --alphas-u 0 --out $O/step0 --prefix c0_both_noalphas
