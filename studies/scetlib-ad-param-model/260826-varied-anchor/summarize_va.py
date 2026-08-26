#!/usr/bin/env python3
"""The three-way comparison, stated as DIFFERENCES and in ONE unit.

Notation, per bin, all of them sigma in pb:

  A0  direct runcard refill at the NOMINAL point           (live, no cache)
  A   direct runcard refill at the VARIED point            (live, no cache)
  C0  cache built at NOMINAL, evaluated at its OWN anchor
  C   cache built at NOMINAL, evaluated at the VARIED point   <- displaced
  B   cache built at VARIED,  evaluated at its OWN anchor     <- the new reference
  D   cache built at VARIED,  evaluated at the NOMINAL point  <- displaced, reverse
  Cb  a SECOND independent build of the NOMINAL runcard, same points (the floor)

The true finite shift the displacement has to traverse is  dS = A - A0.
Every error is quoted as a fraction of dS, which is the "% of the direction's
response" the previous rounds used, and the decomposition is exact:

  (C - A)/dS   =   (C - B)/dS   +   (B - A)/dS
  what every       PURE            CACHE
  previous round   DISPLACEMENT    CONSTRUCTION
  measured         error           error (anchor-exactness of the new cache)
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
QT = ["[20,24]", "[24,28]", "[28,33]", "[33,44]", "[44,100]"]


def load(tag):
    with open(os.path.join(HERE, f"{tag}.json")) as f:
        return json.load(f)


def arr(d, key, which="rule"):
    return np.asarray(d["points"][key][which], float)


def leg(name, nom, nomb, var, key_var, key_nom, key_nom_in_var=None):
    """One transition leg: nominal <-> varied."""
    A0 = np.asarray(nom["direct_at_anchor"], float)
    A = np.asarray(var["direct_at_anchor"], float)
    C0 = arr(nom, key_nom)
    C = arr(nom, key_var)
    B = arr(var, key_var)
    D = arr(var, key_nom_in_var or key_nom)
    dS = A - A0

    print(f"\n{'='*100}\nLEG {name}   (|Y| [0, 0.15], knot f = 2, n_eig 0, "
          f"alphaS pair off)\n{'='*100}")
    print(f"{'qT':>10}{'A0 (nom)':>14}{'A (var)':>14}{'dS = A-A0':>13}"
          f"{'dS/A0':>11}")
    for i, q in enumerate(QT):
        print(f"{q:>10}{A0[i]:>14.7g}{A[i]:>14.7g}{dS[i]:>+13.4e}"
              f"{dS[i]/A0[i]:>+11.3e}")

    print("\n-- 1. VALIDATION of the two caches AT THEIR OWN ANCHOR "
          "(cache replay vs the live runcard at the same point)")
    print(f"{'qT':>10}{'C0/A0-1 (nom)':>16}{'B/A-1 (var)':>16}"
          f"{'(C0-A0)/dS':>14}{'(B-A)/dS':>14}")
    for i, q in enumerate(QT):
        print(f"{q:>10}{C0[i]/A0[i]-1:>+16.3e}{B[i]/A[i]-1:>+16.3e}"
              f"{(C0[i]-A0[i])/dS[i]:>+14.4f}{(B[i]-A[i])/dS[i]:>+14.4f}")

    print("\n-- 1b. the same split into rule-vs-live INSIDE one object, and "
          "live-vs-direct ACROSS two configures")
    print(f"{'qT':>10}{'rule/live-1 nom':>18}{'rule/live-1 var':>18}"
          f"{'live/direct-1 nom':>20}{'live/direct-1 var':>20}")
    for i, q in enumerate(QT):
        ln = arr(nom, key_nom, "live")[i]
        lv = arr(var, key_var, "live")[i]
        print(f"{q:>10}{C0[i]/ln-1:>+18.3e}{B[i]/lv-1:>+18.3e}"
              f"{ln/A0[i]-1:>+20.3e}{lv/A[i]-1:>+20.3e}")

    if nomb is not None:
        Cb0 = arr(nomb, key_nom)
        Cb = arr(nomb, key_var)
        print("\n-- 2. IN-SITU BUILD-TO-BUILD FLOOR: two independent builds of "
              "the SAME (nominal) runcard")
        print(f"{'qT':>10}{'at anchor':>16}{'at displaced':>16}"
              f"{'(Cb-C)/dS':>14}")
        for i, q in enumerate(QT):
            print(f"{q:>10}{Cb0[i]/C0[i]-1:>+16.3e}{Cb[i]/C[i]-1:>+16.3e}"
                  f"{(Cb[i]-C[i])/dS[i]:>+14.4f}")

    print("\n-- 3. THE MEASUREMENT.  Errors as a FRACTION OF THE TRUE SHIFT dS")
    print(f"{'qT':>10}{'OLD (C-A)/dS':>16}{'PURE DISPL (C-B)/dS':>22}"
          f"{'CACHE CONSTR (B-A)/dS':>24}{'REVERSE (D-A0)/dS':>20}")
    for i, q in enumerate(QT):
        print(f"{q:>10}{(C[i]-A[i])/dS[i]:>+16.4f}{(C[i]-B[i])/dS[i]:>+22.4f}"
              f"{(B[i]-A[i])/dS[i]:>+24.4f}{(D[i]-A0[i])/dS[i]:>+20.4f}")

    print("\n   the same in PERCENT of the response, the units the previous "
          "rounds published")
    print(f"{'qT':>10}{'true resp':>13}{'OLD':>11}{'PURE DISPL':>13}"
          f"{'CACHE CONSTR':>15}{'REVERSE':>11}")
    for i, q in enumerate(QT):
        print(f"{q:>10}{dS[i]/A0[i]:>+13.3e}"
              f"{100*(C[i]-A[i])/dS[i]:>+10.1f}%"
              f"{100*(C[i]-B[i])/dS[i]:>+12.1f}%"
              f"{100*(B[i]-A[i])/dS[i]:>+14.1f}%"
              f"{100*(D[i]-A0[i])/dS[i]:>+10.1f}%")

    return dict(A0=A0, A=A, C0=C0, C=C, B=B, D=D, dS=dS)


def main():
    nom = load("nomA")
    nomb = load("nomB") if os.path.exists(os.path.join(HERE, "nomB.json")) else None
    print(__doc__)
    if os.path.exists(os.path.join(HERE, "varA.json")):
        leg("x2: 0.6 -> 0.35  (FINITE variation, what the templates carry)",
            nom, nomb, load("varA"), "-,0.35,-", "-,-,-", "-,0.6,-")
    if os.path.exists(os.path.join(HERE, "x13A.json")):
        x13 = load("x13A")
        # the x13 cache's "nominal" eval key is the explicit 0.2,-,1.0
        A0 = np.asarray(nom["direct_at_anchor"], float)
        A = np.asarray(x13["direct_at_anchor"], float)
        C0 = arr(nom, "-,-,-")
        C = arr(nom, "0.3,-,0.9")
        B = arr(x13, "0.3,-,0.9")
        D = arr(x13, "0.2,-,1.0")
        dS = A - A0
        print(f"\n{'='*100}\nLEG x1,x3: 0.2,1.0 -> 0.3,0.9  (FINITE variation)"
              f"\n{'='*100}")
        print(f"{'qT':>10}{'true resp':>13}{'OLD (C-A)/dS':>15}"
              f"{'PURE DISPL':>13}{'CACHE CONSTR':>15}{'REVERSE':>11}"
              f"{'anchor B/A-1':>15}")
        for i, q in enumerate(QT):
            print(f"{q:>10}{dS[i]/A0[i]:>+13.3e}"
                  f"{100*(C[i]-A[i])/dS[i]:>+14.1f}%"
                  f"{100*(C[i]-B[i])/dS[i]:>+12.1f}%"
                  f"{100*(B[i]-A[i])/dS[i]:>+14.1f}%"
                  f"{100*(D[i]-A0[i])/dS[i]:>+10.1f}%"
                  f"{B[i]/A[i]-1:>+15.3e}")
        if nomb is not None:
            Cb = arr(nomb, "0.3,-,0.9")
            print(f"\n{'qT':>10}{'FLOOR (Cb-C)/dS':>18}")
            for i, q in enumerate(QT):
                print(f"{q:>10}{100*(Cb[i]-C[i])/dS[i]:>+17.1f}%")


if __name__ == "__main__":
    main()
