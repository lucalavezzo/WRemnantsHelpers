#!/usr/bin/env bash
# Re-run every comparison of run_checks.sh on its existing outputs (warnings silenced),
# plus the iteration counts at the warm call sites. Inside the container.
O=${1:-/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_pr_validation/local_checks}
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH=/work/submit/lavezzo/rabbit-tc-warmstart:$PYTHONPATH PYTHONWARNINGS=ignore
c() { local n=$1 a=$2 b=$3; shift 3; r=$(python $HERE/compare_fitresults.py $O/$a/fitresults.hdf5 $O/$b/fitresults.hdf5 "$@" 2>/dev/null); rc=$?; echo "| $n | $([ $rc = 0 ] && echo PASS || echo FAIL) | $(echo "$r" | head -1) |"; [ $rc = 0 ] || echo "$r" | sed -n '2,6p'; }
c "CI nominal fit (impacts, mappings), default minimizer" ci_nominal_base ci_nominal_new
c "CI blinded fit, default minimizer (minimizer_status excluded, see notes)" ci_blinded_base ci_blinded_new --ignore meta time epoch minimizer_status
c "toys -t 3, default minimizer" ci_toys_base ci_toys_new
c "default minimizer: saturated test + scan" ci_satscan_base ci_satscan_new
c "trust-constr+constraints, cold fit" tc_cold_base tc_cold_new
c "off: saturated test" tc_sat_off_base tc_sat_off_new
c "off: --externalPostfit refit" tc_ext_off_base tc_ext_off_new
c "off: likelihood scan" tc_scan_off_base tc_scan_off_new
c "off: toys -t 3" tc_toys_off_base tc_toys_off_new
c "auto: toys -t 3 (toys start cold)" tc_toys_off_base tc_toys_auto_new
c "auto vs before: saturated test (tol 1e-5)" tc_sat_off_base tc_sat_auto_new --atol 1e-5 --rtol 1e-5 --ignore meta time epoch minimizer_status
c "auto vs before: --externalPostfit refit (tol 1e-5)" tc_ext_off_base tc_ext_auto_new --atol 1e-5 --rtol 1e-5 --ignore meta time epoch minimizer_status
c "auto vs before: likelihood scan (tol 1e-4)" tc_scan_off_base tc_scan_auto_new --atol 1e-4 --rtol 1e-4 --ignore meta time epoch minimizer_status
python - <<PY
from rabbit import io_tools
for t in ["tc_sat_off_base", "tc_sat_auto_new"]:
    r = io_tools.get_fitresult("$O/" + t + "/fitresults.hdf5")
    (m,) = r["mappings"].values()
    st = m["saturated_fit"]["minimizer_status"]
    print("SATNIT", t, st["nit"], st["status"], float(m["saturated_fit"]["nllvalreduced"]), st.get("warm_start_legs"))
for t in ["tc_ext_off_base", "tc_ext_auto_new"]:
    st = io_tools.get_fitresult("$O/" + t + "/fitresults.hdf5")["minimizer_status"]
    print("EXTNIT", t, st["nit"], st["status"], st.get("warm_start_legs"))
PY
for t in tc_scan_off_base tc_scan_auto_new; do echo "SCANTIME $t $(grep -o '[0-9.]* seconds total time' $O/$t.log)"; done
