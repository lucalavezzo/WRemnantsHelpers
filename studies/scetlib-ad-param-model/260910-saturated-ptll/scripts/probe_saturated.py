"""Cheap probe: does the saturated PROJECTION test's CompositeParamModel refuse
our param model?  No 8.7 GB SCETlib cache is loaded -- the clash (if any) is in
CompositeParamModel.__init__, which only sees npoi / npou / allowNegativeParam.

Uses the REAL card, the REAL 'Project ch0 ptll' mapping and the REAL
SaturatedProjectModel built from its output_indices, against a stub standing in
for SCETlibADParamModel (npoi=1 alphaS, npou=N, allowNegativeParam=True,
blind_additive=True) -- the flags are read straight out of the model source, so
the stub only avoids the cache load, it does not soften the test.
"""

import sys

import numpy as np
import tensorflow as tf

from rabbit import inputdata
from rabbit.mappings import helpers as mh
from rabbit.param_models import param_model as pm

CARD = sys.argv[1]
CH, AX = sys.argv[2], sys.argv[3]

indata = inputdata.FitInputData(CARD)
print("[probe] channels:")
for k, v in indata.channel_info.items():
    print(
        f"  {k}: masked={v['masked']} axes={[(a.name, a.size) for a in v['axes']]} "
        f"start={v['start']} stop={v['stop']}"
    )
print(f"[probe] nbins={indata.nbins} nsyst={indata.nsyst} nproc={indata.nproc}")

mapping = mh.load_mapping("Project", indata, CH, AX)
print(
    f"[probe] mapping key={mapping.key} has_data={mapping.has_data} "
    f"skip_incusive={mapping.skip_incusive}"
)
idx = mapping.output_indices()
sat = pm.SaturatedProjectModel(indata, mapping.channel_info, idx)
print(
    f"[probe] SaturatedProjectModel: npoi={sat.npoi} npou={sat.npou} "
    f"allowNegativeParam={sat.allowNegativeParam} "
    f"xparamdefault[:3]={sat.xparamdefault.numpy()[:3]}"
)
print(f"[probe] saturated param names: {[p.decode() for p in sat.params]}")


class StubAD(pm.ParamModel):
    """Exactly SCETlibADParamModel's fitter-facing declaration, no cache."""

    def __init__(self, indata, npou):
        self.indata = indata
        self.npoi = 1
        self.npou = npou
        self.params = np.array([b"alphaS"] + [f"stub{i}".encode() for i in range(npou)])
        self.allowNegativeParam = True  # param_model.py:731
        self.blind_additive = True  # param_model.py:~760
        self.is_linear = False
        self.xparamdefault = tf.zeros([self.nparams], dtype=indata.dtype)

    def compute(self, param, full=False):
        return tf.ones([1, 1], dtype=self.indata.dtype)


stub = StubAD(indata, 8)
print("[probe] constructing CompositeParamModel([StubAD, SaturatedProjectModel]) ...")
try:
    comp = pm.CompositeParamModel([stub, sat])
    print(
        f"[probe] RESULT: constructed OK. npoi={comp.npoi} npou={comp.npou} "
        f"allowNegativeParam={comp.allowNegativeParam} "
        f"blind_additive={getattr(comp, 'blind_additive', None)}"
    )
except Exception as e:
    print(f"[probe] RESULT: RAISED {type(e).__name__}: {e}")

print(
    "[probe] control: composite of the same saturated model with a "
    "Mu-like POI model (allowNegativeParam=False) ..."
)
try:
    mu = pm.Mu(indata)
    print(
        f"[probe]   Mu: npoi={mu.npoi} npou={mu.npou} "
        f"allowNegativeParam={mu.allowNegativeParam}"
    )
    comp2 = pm.CompositeParamModel([mu, sat])
    print(
        f"[probe]   RESULT: constructed OK. npoi={comp2.npoi} "
        f"allowNegativeParam={comp2.allowNegativeParam}"
    )
except Exception as e:
    print(f"[probe]   RESULT: RAISED {type(e).__name__}: {e}")
