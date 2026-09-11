#!/bin/bash
# One in-container pass over everything, once all five fits have finished.
#   1. compare_warm.py  per arm  -- the purpose-built tool, one table each
#   2. check_minimum.py          -- eigendecompose every new postfit covariance
#   3. build_spec.py             -- the cross-arm view + the JSON the figures read
#   4. compare_five.py           -- the four existing arms plus wall+ridge
#   5. plot_basins.py            -- the two figures, into the task dir
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/build
source /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/setup.sh > /dev/null
export PYTHONPATH="/work/submit/lavezzo/alphaS/rabbit-blinding:/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-fit-770/lib:$PYTHONPATH"
export PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-basins
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
TOOL=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-fit-770/compare_warm.py
CHK=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-blinding/scripts/check_minimum.py
S=/tmp/basins_warm; mkdir -p $S
cd /home/submit/lavezzo/alphaS/WRemnants

seed_of () { case $1 in
  plain)    echo $CEPH/260910_blinding_final/fitresults_DATABLIND.hdf5;;
  ridge)    echo $CEPH/260910_blinding_final/fitresults_DATAPC2.hdf5;;
  spectral) echo $CEPH/260910_spectral/fitresults_DATASPECPF.hdf5;;
  walled)   echo $CEPH/260910_wall_port/fitresults_DATAWALL5.hdf5;; esac; }
warm_of () { case $1 in
  plain) echo $CEPH/260910_basins/fitresults_WARMPLAIN.hdf5;;
  ridge) echo $CEPH/260910_basins/fitresults_WARMRIDGE.hdf5;;
  spectral) echo $CEPH/260910_basins/fitresults_WARMSPEC.hdf5;;
  walled) echo $CEPH/260910_basins/fitresults_WARMWALL.hdf5;; esac; }

for arm in plain ridge spectral walled; do
  A=$(seed_of $arm); B=$(warm_of $arm)
  [ -f "$B" ] || { echo "### $arm: no warm fitresult, skipped"; continue; }
  cp -n "$A" $S/ 2>/dev/null || true; cp -n "$B" $S/ 2>/dev/null || true
  echo; echo "##################### ARM: $arm"
  echo "  seed $A"; echo "  warm $B"
  python3 -u $TOOL $S/$(basename $A) $S/$(basename $B) --json $T/warm_$arm.json --top 20
done

echo; echo "##################### postfit covariance eigendecomposition (new fits)"
python3 -u $CHK $CEPH/260910_basins/fitresults_*.hdf5

echo; echo "##################### cross-arm"
python3 -u $T/scripts/build_spec.py $T/basins.json

if [ -f $CEPH/260910_basins/fitresults_DATAWALLPC.hdf5 ]; then
  echo; echo "##################### five-way"
  python3 -u $T/scripts/compare_five.py $(cat $T/logs/LATEST_WALLPC)
fi

echo; echo "##################### figures"
python3 -u $T/scripts/plot_basins.py $T $T/basins.json
echo ANALYSE_ALL_DONE
