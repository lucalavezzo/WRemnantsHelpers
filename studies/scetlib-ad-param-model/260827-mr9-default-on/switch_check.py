#!/usr/bin/env python3
"""Does the FLIP work? A construction check, not a physics measurement.

The physics of mode 1 was measured in the round that produced MR !9 and does not
change by being reached from a default rather than from a flag: same code path,
same switch value. All that is new is which value the switch holds when nobody
passes one. So: read it with nothing passed, disable it explicitly and read it
back, and re-enable. No cache, no direction scan.
"""
import scetlib_qT as s

D = s.DrellYan
print(f"nothing passed          muf_analytic() = {D.muf_analytic()}   "
      f"(the flip: must be 1)")
assert D.muf_analytic() == 1, "the default did not flip"
D.set_muf_analytic(0)
print(f"set_muf_analytic(0)     muf_analytic() = {D.muf_analytic()}   "
      f"(the off switch survives: must be 0)")
assert D.muf_analytic() == 0, "the off switch is gone"
D.set_muf_analytic(1)
print(f"set_muf_analytic(1)     muf_analytic() = {D.muf_analytic()}")
assert D.muf_analytic() == 1
print(f"i1 companion, untouched muf_analytic_i1() = {D.muf_analytic_i1()}")
print("\nFLIP OK: on when nothing is passed, still off when explicitly disabled.")
