"""NPDampingWall + constraint_spec, for rabbit's --minimizerMethod trust-constr.

Task-local shim (study trust-constr-nominal, 261005-trust-constr-port): the main
WRemnants checkout must not be modified while production fits run from it, so
the one method the hard-constraint path needs is added in a subclass here. The
proposed permanent change is the same method on
wremnants/postprocessing/scetlib_ad/np_damping_wall.py::NPDampingWall.

Use on the -r line in place of the wall class (the mapping is unchanged):
    -r npwall_tc.NPDampingWallTC
       wremnants.postprocessing.scetlib_ad.np_damping_wall.NPDampingMapping margin=0
with this directory on PYTHONPATH.

The feasible set is exactly the penalty's: each ACTIVE condition (the ones the
wall arms in set_expectations; conditions reading held lambdas only are already
checked and dropped there) contributes ``cond.value(physical lambdas) >=
cond.bound``, and the penalty is ``sum relu2(bound - value) * exp(2 tau)``.
"""

import tensorflow as tf

from wremnants.postprocessing.scetlib_ad import np_damping_wall as _w

NPDampingMapping = _w.NPDampingMapping


class NPDampingWallTC(_w.NPDampingWall):
    def constraint_spec(self, params, observables):
        if not self._active:
            raise ValueError(
                "NPDampingWallTC: no active condition (not armed yet, or every "
                "condition reads held lambdas only)"
            )
        values = self._physical(params)
        vals = tf.stack(
            [tf.cast(c.value(values, self._relu2_tf), self.dtype) for c in self._active]
        )
        lbs = tf.constant([float(c.bound) for c in self._active], dtype=self.dtype)
        return vals, lbs

    def constraint_labels(self):
        return [c.label for c in self._active]
