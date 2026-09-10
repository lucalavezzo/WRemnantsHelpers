#!/bin/bash
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true
echo "--- after WRemnantsHelpers/setup.sh"
echo "PYTHONPATH=[$PYTHONPATH]"
python3 -c "import scetlib_qT; print('scetlib_qT:', scetlib_qT.__file__); print('set_matched_partner:', hasattr(scetlib_qT.DrellYan, 'set_matched_partner'))" 2>&1 | tail -3
source $WREM_BASE/scetlib-cms/setup.sh > /dev/null 2>&1 || true
echo "--- after scetlib-cms/setup.sh"
echo "PYTHONPATH=[$PYTHONPATH]"
python3 -c "import scetlib_qT; print('scetlib_qT:', scetlib_qT.__file__); print('set_matched_partner:', hasattr(scetlib_qT.DrellYan, 'set_matched_partner'))" 2>&1 | tail -3
