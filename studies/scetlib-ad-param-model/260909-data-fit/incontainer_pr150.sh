#!/bin/bash
# Same env as the failed data fit EXCEPT rabbit, which comes from PR #150
# (preconditioning). PR #150 is a superset of our WIP for everything the model
# needs -- verified: paramPriors, prior_sigmas, externalPostfit, doImpacts and
# edmval are all present at >= our counts, and workspace.py / svd.py are
# byte-identical to ours. Only rabbit_merge_fitresults.py and io_tools.py are
# ours-only, and neither is used by a fit.
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
# override rabbit AFTER setup.sh has put the main tree's copy on the path
source /work/submit/lavezzo/alphaS/rabbit-pr150/setup.sh > /dev/null
export PYTHONPATH="/work/submit/lavezzo/alphaS/rabbit-pr150:$PYTHONPATH"
export PATH="/work/submit/lavezzo/alphaS/rabbit-pr150/bin:$PATH"
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/build
source /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/setup.sh > /dev/null
export PYTHONPATH="/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-fit-770/lib:$PYTHONPATH"
export PYTHONDONTWRITEBYTECODE=1
cd /home/submit/lavezzo/alphaS/WRemnants
python3 -c "
import rabbit, inspect
print('[env] rabbit', inspect.getsourcefile(rabbit))
import rabbit.parsing as P, inspect as i
print('[env] precondition supported:', '--precondition' in i.getsource(P))
import scetlib_tf, hashlib
print('[env] hvp zero-skip:', b'if not vv.any():' in open(inspect.getsourcefile(scetlib_tf),'rb').read())
"
exec "$@"
