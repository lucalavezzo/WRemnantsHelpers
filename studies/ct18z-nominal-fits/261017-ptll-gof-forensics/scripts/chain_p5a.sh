#!/usr/bin/env bash
# queue P5a only after P2_THx2_LAT has left the gate, so the agreed order (A0x2, THx2, then P5a) holds
until grep -q launching /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261018_ptll_gof_tests/P2_THx2_LAT.gate; do sleep 60; done
echo "[chain] $(date -Is) THx2 launched; gating P5a"
exec bash /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/alphas-scan-discontinuity/scripts/mem_gate.sh 260 /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261018_ptll_gof_tests/P5A_FREELUMI_LAT.log -- /home/submit/lavezzo/alphaS/WRemnantsHelpers/agent_setup.sh --scetlib /work/submit/lavezzo/alphaS/scetlib-gamma-nu-points/scetlib-cms/build --prepend-pythonpath /work/submit/lavezzo/rabbit-all3 -- bash /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ct18z-nominal-fits/261017-ptll-gof-forensics/scripts/run_p5a.sh FREELUMI
