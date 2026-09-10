#!/bin/bash
# Verification for the additive-POI blinding change.
# Launch (see knowledge/10_environment/runtime_bootstrap.md -- /cvmfs/ in the
# bind list, `bash -lc`, and a SCRIPT rather than an inline quoted string):
#   nohup singularity run --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ <img> \
#       bash -lc "<this script>" > logs/verify_<ts>.log 2>&1 &
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-blinding
cd /home/submit/lavezzo/alphaS/WRemnants/rabbit

# The suite costs ~15 min; the blinding checks cost ~1. Set SKIP_SUITE=1 to
# iterate on the checks alone.
if [ "${SKIP_SUITE:-0}" = "1" ]; then
  echo "############ existing test suite SKIPPED (SKIP_SUITE=1)"
else
echo "############ existing test suite (regression guard)"
# CI runs these as SCRIPTS -- `python tests/<file>` (.github/workflows/main.yml
# :162) -- not under pytest. That matters twice over: the files are not
# pytest-shaped (pytest collects nothing from some of them), and running as a
# script puts tests/ on sys.path[0], which is what makes
# test_external_nll_constant.py's `from test_external_term import ...` resolve.
# CI's matrix is only 5 files; test_snapshot / test_restart / test_preconditioner*
# came with our own preconditioner work, so run those too.
# TWO STYLES COEXIST in this repo, so dispatch per file:
#   * script style -- `python tests/X.py`, which is what CI does
#     (.github/workflows/main.yml:162) and what its five matrix entries need;
#     running as a script also puts tests/ on sys.path[0], which is how
#     test_external_nll_constant.py's absolute `from test_external_term import`
#     resolves.
#   * package style -- `python -m tests.X`, needed by the files using RELATIVE
#     imports (`from .test_sparse_fit import ...`): test_preconditioner,
#     test_restart, test_snapshot, all of which came with our preconditioner
#     work and are normally run under pytest.
rc_all=0
for f in tests/test_*.py; do
  name=$(basename "$f" .py)
  if grep -q "^from \\." "$f"; then
    cmd="python3 -m tests.$name"; style="pkg"
  else
    cmd="python3 $f"; style="script"
  fi
  if $cmd > /tmp/rabbit_test_$$.log 2>&1; then
    echo "  OK   $name ($style)"
  else
    echo "  FAIL $name ($style)"
    tail -4 /tmp/rabbit_test_$$.log | sed 's/^/         /'
    rc_all=1
  fi
done
rm -f /tmp/rabbit_test_$$.log
echo "SUITE_RC=$rc_all"
fi

echo ""
echo "############ build a test tensor"
python3 tests/make_tensor.py -o "$T/logs"

echo ""
echo "############ blinding verification"
python3 -u "$T/scripts/verify_blinding.py" "$T/logs/test_tensor.hdf5"
echo "############ VERIFY_DONE rc=$?"
