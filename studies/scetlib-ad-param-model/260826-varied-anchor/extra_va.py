#!/usr/bin/env python3
"""Two things the headline table does not carry:

  RECOVERED  the fraction of the true finite shift the displaced cache actually
             delivers, both directions -- 1 - err/dS, stated per leg with its
             OWN shift, so forward and reverse are comparable.
  rule/live  at the DISPLACED point, from the SAME object: `live` re-integrates
             the calculation at the new parameter point with no rule and no
             member interpolation, so it separates the frozen sites/weights and
             the interpolated node values from everything upstream of them.
"""
import json, os
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
QT = ["[20,24]", "[24,28]", "[28,33]", "[33,44]", "[44,100]"]
L = lambda t: json.load(open(os.path.join(H, f"{t}.json")))
a = lambda d, k, w="rule": np.asarray(d["points"][k][w], float)

nom, nomb, var, x13 = L("nomA"), L("nomB"), L("varA"), L("x13A")
A0 = np.asarray(nom["direct_at_anchor"], float)

for name, vd, kvar, knom_in_var in (
        ("x2 0.6 -> 0.35", var, "-,0.35,-", "-,0.6,-"),
        ("x1,x3 0.2,1.0 -> 0.3,0.9", x13, "0.3,-,0.9", "0.2,-,1.0")):
    A = np.asarray(vd["direct_at_anchor"], float)
    C0, C = a(nom, "-,-,-"), a(nom, kvar)
    B, D = a(vd, kvar), a(vd, knom_in_var)
    Cb = a(nomb, kvar)
    dS = A - A0
    print(f"\n{'='*104}\n{name}\n{'='*104}")
    print(f"{'qT':>10}{'true resp':>12}"
          f"{'FWD recovered':>15}{'REV recovered':>15}"
          f"{'rule/live displ FWD':>21}{'live/direct displ FWD':>23}")
    for i, q in enumerate(QT):
        fwd = (C[i] - C0[i]) / dS[i]              # nominal cache: shift delivered
        rev = (D[i] - B[i]) / (-dS[i])            # varied  cache: shift delivered
        lv = a(nom, kvar, "live")[i]
        print(f"{q:>10}{dS[i]/A0[i]:>+12.3e}{fwd:>15.4f}{rev:>15.4f}"
              f"{C[i]/lv-1:>+21.3e}{lv/A[i]-1:>+23.3e}")
    print(f"\n{'qT':>10}{'signal (C-B)/dS':>18}{'floor (Cb-C)/dS':>18}"
          f"{'|signal|/|floor|':>18}{'floor abs Cb/C-1':>19}")
    for i, q in enumerate(QT):
        s = (C[i] - B[i]) / dS[i]
        f = (Cb[i] - C[i]) / dS[i]
        print(f"{q:>10}{100*s:>17.1f}%{100*f:>17.1f}%"
              f"{abs(s)/abs(f) if f else float('inf'):>18.1f}{Cb[i]/C[i]-1:>+19.3e}")

print("\n\nBY-PRODUCT, and NOT a live calculation: `live` at a DISPLACED point")
print("re-sweeps the kernels over the NodeData FROZEN at the anchor")
print("(set_gradient_node_cache(True) caches the profile scales and the")
print("PDF/beam-grid convolutions), so it is the frozen-conv path WITHOUT the")
print("muF member interpolation. Response it delivers, as a fraction of dS:")
for name, vd, kvar in (("x2 0.6 -> 0.35", var, "-,0.35,-"),
                       ("x1,x3 0.2,1.0 -> 0.3,0.9", x13, "0.3,-,0.9")):
    A = np.asarray(vd["direct_at_anchor"], float)
    dS = A - A0
    C0 = a(nom, "-,-,-")
    print(f"\n  {name}")
    print(f"  {'qT':>10}{'frozen-node only':>19}{'+ members (rule)':>19}")
    for i, q in enumerate(QT):
        lv = a(nom, kvar, "live")[i]
        Cc = a(nom, kvar)[i]
        print(f"  {q:>10}{(lv-C0[i])/dS[i]:>19.3f}{(Cc-C0[i])/dS[i]:>19.3f}")
