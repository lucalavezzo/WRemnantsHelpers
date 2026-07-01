"""Compare alphaS, projection chi2/p-values, and key nuisance shifts across
every fit from this study. Pass any number of (label, path) pairs as args.

Usage:
    python compare_all_fits.py LABEL1=path1 LABEL2=path2 ...
"""

import sys

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")
import numpy as np
from scipy.stats import chi2 as chi2dist
from rabbit.io_tools import get_fitresult


def summarize(path):
    fr, _ = get_fitresult(path, meta=True)
    parms = fr["parms"].get()
    names = list(parms.axes[0])
    vals = parms.values()
    errs = np.sqrt(parms.variances())
    out = {"path": path, "names": names, "vals": vals, "errs": errs}
    if "pdfAlphaS" in names:
        i = names.index("pdfAlphaS")
        out["alphaS"] = (float(vals[i]), float(errs[i]))
    out["mappings"] = {}
    for k, m in fr["mappings"].items():
        c = float(m["chi2"])
        n = float(m["ndf"])
        p = chi2dist.sf(c, n) * 100
        cp = float(m["chi2_prefit"])
        pp = chi2dist.sf(cp, n) * 100
        cs = float(m.get("chi2_saturated", float("nan")))
        ps = chi2dist.sf(cs, n) * 100 if cs == cs else float("nan")
        out["mappings"][k] = (c, n, cp, cs, p, pp, ps)
    return out


def main():
    fits = []
    for spec in sys.argv[1:]:
        if "=" not in spec:
            print(f"skipping {spec} (use LABEL=path)")
            continue
        lab, p = spec.split("=", 1)
        try:
            fits.append((lab, summarize(p)))
        except Exception as e:
            print(f"ERROR loading {lab} ({p}): {e}")

    print("=" * 100)
    print(f"{'fit':30s} {'alphaS':>16s}")
    for lab, d in fits:
        a = d.get("alphaS")
        if a is None:
            print(f"{lab:30s}  no alphaS")
        else:
            print(f"{lab:30s}  {a[0]:+8.3f} +/- {a[1]:.3f}")

    # Collect the union of mappings.
    all_keys = []
    for _, d in fits:
        for k in d["mappings"]:
            if k not in all_keys:
                all_keys.append(k)

    print()
    print(f"{'mapping':40s}", end="")
    for lab, _ in fits:
        print(f"  {lab[:18]:>18s}", end="")
    print()
    for k in all_keys:
        print(f"{k:40s}", end="")
        for lab, d in fits:
            if k in d["mappings"]:
                c, n, cp, cs, p, pp, ps = d["mappings"][k]
                print(f"  {c:6.1f}/{int(n):3d} p={p:5.2f}%", end="")
            else:
                print(f"  {'-':>18s}", end="")
        print()

    # Show top 10 nuisance changes vs first fit.
    if len(fits) >= 2:
        nom_lab, nom = fits[0]
        for lab, d in fits[1:]:
            print(f"\n--- top 15 |Δθ| ({lab} − {nom_lab}) ---")
            diffs = []
            for nm in d["names"]:
                if nm not in nom["names"]:
                    continue
                i_t = d["names"].index(nm)
                i_n = nom["names"].index(nm)
                diffs.append(
                    (
                        abs(d["vals"][i_t] - nom["vals"][i_n]),
                        nm,
                        nom["vals"][i_n],
                        d["vals"][i_t],
                    )
                )
            diffs.sort(reverse=True)
            for dval, nm, v0, v1 in diffs[:15]:
                print(
                    f"  {nm:55s}  {nom_lab}={v0:+.3f} -> {lab}={v1:+.3f}  Δ={v1 - v0:+.3f}"
                )


if __name__ == "__main__":
    main()
