#!/usr/bin/env python3
"""Read the frozen-CS arm(s) against the five basin arms.

POLICY: alphaS's central value is blinded and is NEVER printed. Only
DIFFERENCES between arms (offset-free under the additive blinding of rabbit
0f64bbb: the same deterministic sha256(param_name)-seeded offset is added in
every fit on this card), sigmas, losses, EDMs and p-values appear here.

usage: analyse.py [postfix ...]        default: every arm listed in ARMS
"""
import os
import shutil
import sys
import time

import numpy as np
from scipy import stats

CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD = f"{CEPH}/study_scratch/260910-anchor-verify/card_none.hdf5"
SCRATCH = "/tmp/frzcs_read"
WIDTH_AS = 0.002
MODEL_PREFIXES = (
    "alphaS",
    "lambda",
    "delta_lambda",
    "b0_over_bmax",
    "resumTNP_",
    "resumScale",
    "resumTransition",
    "pdfEig",
)

# The five existing blinded-data arms (../260910-basins/LOGBOOK.md) plus ours.
ARMS = [
    ("plain", f"{CEPH}/260910_blinding_final/fitresults_DATABLIND.hdf5"),
    ("ridge", f"{CEPH}/260910_blinding_final/fitresults_DATAPC2.hdf5"),
    ("spectral", f"{CEPH}/260910_spectral/fitresults_DATASPECPF.hdf5"),
    ("walled", f"{CEPH}/260910_wall_port/fitresults_DATAWALL5.hdf5"),
    ("wall+ridge", f"{CEPH}/260910_basins/fitresults_DATAWALLPC.hdf5"),
    # the sixth arm: ../260911-lattice-constraints. Its card carries an extra
    # external_terms/lattice_cs group and it FREES lambda2_nu/lambda4_nu from
    # their sigma=1 theta priors, so its loss is not on the same footing --
    # but its postfit vector is index-aligned and its alphaS carries the same
    # additive blinding offset, so the L2 and the alpha_s difference are valid.
    ("lattice", f"{CEPH}/260911_lattice/fitresults_DATALAT.hdf5"),
    ("frzCS@0.15", f"{CEPH}/260911_freeze_cs/fitresults_DATAFRZCS.hdf5"),
    ("frzCS@0.00", f"{CEPH}/260911_freeze_cs/fitresults_FRZCSL000.hdf5"),
    ("frzCS@0.05", f"{CEPH}/260911_freeze_cs/fitresults_FRZCSL050.hdf5"),
    ("frzCS@0.087", f"{CEPH}/260911_freeze_cs/fitresults_FRZCSL087.hdf5"),
    ("frzCS@0.19", f"{CEPH}/260911_freeze_cs/fitresults_FRZCSL190.hdf5"),
    # the basin-controlled (warm) scan: same freeze, started from the plain
    # arm's own postfit with only the CS pair moved (scripts/make_seed.py).
    ("wfrz@0.00", f"{CEPH}/260911_freeze_cs/fitresults_WFRZ000.hdf5"),
    ("wfrz@0.05", f"{CEPH}/260911_freeze_cs/fitresults_WFRZ050.hdf5"),
    ("wfrz@0.087", f"{CEPH}/260911_freeze_cs/fitresults_WFRZ087.hdf5"),
    ("wfrz@0.15", f"{CEPH}/260911_freeze_cs/fitresults_WFRZ150.hdf5"),
    ("wfrz@0.19", f"{CEPH}/260911_freeze_cs/fitresults_WFRZ190.hdf5"),
    # CONTINUATION arms: stepped from the converged frzCS@0.087 postfit, which
    # already has lambda4_nu = 0, so only the soft lambda2_nu direction moves.
    ("cfrz@0.15", f"{CEPH}/260911_freeze_cs/fitresults_CFRZ150.hdf5"),
    ("cfrz@0.19", f"{CEPH}/260911_freeze_cs/fitresults_CFRZ190.hdf5"),
    # reversibility check: continuation BACKWARD from cfrz@0.15 to 0.087.
    ("bfrz@0.087", f"{CEPH}/260911_freeze_cs/fitresults_BFRZ087.hdf5"),
]

from rabbit import inputdata, io_tools  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402


def local_copy(path):
    os.makedirs(SCRATCH, exist_ok=True)
    dst = os.path.join(SCRATCH, os.path.basename(path))
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(path):
        shutil.copy2(path, dst)
    return dst


def read(path, tries=20, wait=15.0):
    last = None
    for k in range(tries):
        try:
            res = io_tools.get_fitresult(local_copy(path))
            h = res["parms"].get()
            names = [str(n) for n in h.axes[0]]
            out = dict(names=names, vals=h.values(), errs=np.sqrt(h.variances()))
            for key in ("edmval", "nllvalreduced", "ndfsat"):
                if key in res:
                    try:
                        out[key] = float(
                            np.asarray(res[key].get().values()).reshape(-1)[0]
                        )
                    except Exception:
                        try:
                            out[key] = float(np.asarray(res[key]).reshape(-1)[0])
                        except Exception:
                            pass
            if "cov" in res:
                hc = res["cov"].get()
                out["cov"] = hc.values()
                out["covnames"] = [str(x) for x in hc.axes[0]]
            if "impacts_grouped" in res:
                out["impg"] = res["impacts_grouped"].get()
            return out
        except (BlockingIOError, OSError) as ex:
            last = ex
            time.sleep(wait)
    raise RuntimeError(f"could not read {path}: {last}")


def main():
    want = sys.argv[1:]
    indata = inputdata.FitInputData(CARD)
    inp = wall.resolve_wall_inputs(indata)
    conds = wall.damping_conditions(inp["np_model"], inp["np_model_nu"], inp["ymax"])

    live = []
    for tag, path in ARMS:
        if want and tag not in want:
            continue
        if not os.path.exists(path) or os.path.getsize(path) < 10_000_000:
            state = (
                "missing"
                if not os.path.exists(path)
                else f"still being written ({os.path.getsize(path)/1e6:.1f} MB)"
            )
            print(f"[skip] {tag:12s} {state}")
            continue
        a = read(path)
        a["tag"] = tag
        a["nfrozen"] = 2 if tag.startswith(("frzCS", "wfrz", "cfrz", "bfrz")) else 0
        a["theta"] = {n: float(a["vals"][i]) for i, n in enumerate(a["names"])}
        a["sig"] = {n: float(a["errs"][i]) for i, n in enumerate(a["names"])}
        a["phys"] = {
            n: (
                float(wall.physical_from_theta(inp["specs"][n], a["theta"][n]))
                if n in a["theta"]
                else float(inp["anchors"][n])
            )
            for n in inp["names"]
        }
        live.append(a)
    if not live:
        print("nothing to read")
        return

    W = 14

    def row(label, fn, fmt=".6g"):
        cells = ""
        for a in live:
            v = fn(a)
            cells += "n/a".rjust(W) if v is None else format(v, fmt).rjust(W)
        print(f"  {label:30s}{cells}")

    print("=" * (32 + W * len(live)))
    print("ARMS")
    print("=" * (32 + W * len(live)))
    print("  " + "tag".ljust(30) + "".join(a["tag"].rjust(W) for a in live))
    print("-" * (32 + W * len(live)))
    row("EDM", lambda a: a.get("edmval"), ".3e")
    # rabbit prints chi2 = 2 * nllvalreduced against ndfsat (rabbit_fit.py:703-712).
    row("reduced NLL", lambda a: a.get("nllvalreduced"), ".4f")
    row(
        "saturated 2*dNLL",
        lambda a: 2 * a["nllvalreduced"] if a.get("nllvalreduced") else None,
        ".2f",
    )
    row("  ndf as logged", lambda a: a.get("ndfsat"), ".0f")
    row(
        "  p [%] as logged",
        lambda a: (
            (100 * stats.chi2.sf(2 * a["nllvalreduced"], a["ndfsat"]))
            if a.get("nllvalreduced") and a.get("ndfsat")
            else None
        ),
        ".2f",
    )
    # ndfsat = nobs - param_model.nparams - nsystnoconstraint and does NOT know
    # about --freezeParameters, so a frozen arm is short by one dof per frozen
    # model parameter. Corrected below; the difference is small but it is a real
    # bookkeeping error, first recorded in studies/np-wall-local-minima.
    row(
        "  ndf corrected",
        lambda a: (a["ndfsat"] + a.get("nfrozen", 0)) if a.get("ndfsat") else None,
        ".0f",
    )
    row(
        "  p [%] corrected",
        lambda a: (
            (
                100
                * stats.chi2.sf(
                    2 * a["nllvalreduced"], a["ndfsat"] + a.get("nfrozen", 0)
                )
            )
            if a.get("nllvalreduced") and a.get("ndfsat")
            else None
        ),
        ".2f",
    )
    row("sigma(alpha_s)", lambda a: a["sig"]["alphaS"] * WIDTH_AS, ".6f")
    print("  [alphaS CENTRAL VALUE IS BLINDED - never printed]")

    print()
    print("--- alpha_s DIFFERENCES, in units of the LARGER of the two sigmas ---")
    print(
        "    (offset-free: additive blinding, same deterministic offset in every arm)"
    )
    print("  " + " " * 14 + "".join(a["tag"].rjust(W) for a in live))
    for a in live:
        cells = ""
        for b in live:
            d = (a["theta"]["alphaS"] - b["theta"]["alphaS"]) * WIDTH_AS
            s = max(a["sig"]["alphaS"], b["sig"]["alphaS"]) * WIDTH_AS
            cells += format(d / s, "+.3f").rjust(W)
        print(f"  {a['tag']:14s}{cells}")
    print()
    print("  and the same in raw Delta(alpha_s):")
    print("  " + " " * 14 + "".join(a["tag"].rjust(W) for a in live))
    for a in live:
        cells = "".join(
            format(
                (a["theta"]["alphaS"] - b["theta"]["alphaS"]) * WIDTH_AS, "+.2e"
            ).rjust(W)
            for b in live
        )
        print(f"  {a['tag']:14s}{cells}")

    print()
    print("--- basin: L2 over the 46 non-alphaS model parameters (theta units) ---")
    keys = [
        n for n in live[0]["names"] if n.startswith(MODEL_PREFIXES) and n != "alphaS"
    ]
    npkeys = [k for k in keys if k.startswith(("lambda", "delta_lambda", "b0_over"))]
    otherkeys = [k for k in keys if k not in npkeys]
    for label, kk in (
        ("ALL 46", keys),
        (f"NP block ({len(npkeys)})", npkeys),
        (f"rest ({len(otherkeys)})", otherkeys),
    ):
        print(f"  [{label}]")
        print("  " + " " * 14 + "".join(a["tag"].rjust(W) for a in live))
        for a in live:
            cells = "".join(
                format(
                    np.linalg.norm([a["theta"][k] - b["theta"][k] for k in kk]), ".3f"
                ).rjust(W)
                for b in live
            )
            print(f"  {a['tag']:14s}{cells}")

    print()
    print("--- physical NP tune (anchor + width*theta); frozen entries flagged ---")
    print(
        "  "
        + "lambda".ljust(18)
        + "anchor".rjust(10)
        + "".join(a["tag"].rjust(W) for a in live)
    )
    for n in inp["names"]:
        cells = "".join(format(a["phys"][n], ".5f").rjust(W) for a in live)
        print(f"  {n:18s}{float(inp['anchors'][n]):10.5f}{cells}")

    print()
    print("--- damping conditions violated (coeff < 0) ---")
    for a in live:
        bad = [
            (c.label, float(c.value(a["phys"], wall.numpy_relu2)))
            for c in conds
            if float(c.value(a["phys"], wall.numpy_relu2)) < 0.0
        ]
        pen = sum(float(c.penalty(a["phys"], wall.numpy_relu2)) for c in conds)
        print(
            f"  {a['tag']:12s} {len(bad)}/{len(conds)} unphysical, bare penalty {pen:.4g}"
        )
        for lab, v in bad:
            print(f"      {lab:60s} {v:+12.5g}")

    print()
    print("--- postfit correlations in the NP block + alphaS ---")
    want_c = [
        "alphaS",
        "lambda2",
        "lambda4",
        "delta_lambda2",
        "lambda2_nu",
        "lambda4_nu",
    ]
    for a in live:
        if "cov" not in a:
            continue
        idx = {n: i for i, n in enumerate(a["covnames"])}
        C = a["cov"]
        d = np.sqrt(np.diag(C))
        print(f"  [{a['tag']}]")
        ww = [w for w in want_c if w in idx]
        print("      " + "".join(w.rjust(13) for w in ww))
        for x in ww:
            r = "".join(
                format(C[idx[x], idx[y]] / (d[idx[x]] * d[idx[y]]), "+.4f").rjust(13)
                for y in ww
            )
            print(f"  {x:16s}{r}")
        print(
            "      (frozen parameters keep their PREFIT row: cov is initialised to "
            "diag(var_prefit) and only the floating block is overwritten)"
        )

    print()
    print("--- card nuisances ---")
    for a in live:
        cn = [n for n in a["names"] if not n.startswith(MODEL_PREFIXES)]
        cv = np.array([a["theta"][n] for n in cn])
        i = int(np.argmax(np.abs(cv)))
        print(
            f"  {a['tag']:12s} n={len(cv)}  max|pull| {abs(cv[i]):.3f} ({cn[i]})"
            f"   >2sig: {int((np.abs(cv) > 2).sum())}   >3sig: {int((np.abs(cv) > 3).sum())}"
        )
    # --- dump the numbers the plot script needs -------------------------
    # NB: alphaS's own coordinate is NOT written to this file. The blinding
    # offset is a deterministic sha256(param_name) draw recomputable from
    # rabbit's source (../260910-blinding/LOGBOOK.md finding 3), and this
    # directory is served on the web with no authentication, so the blinded
    # coordinate is as good as the value. Only DIFFERENCES go in.
    import json

    out = {"arms": {}, "keys": keys, "npkeys": npkeys}
    base = next((a for a in live if a["tag"] == "plain"), None)
    for a in live:
        e = dict(
            tag=a["tag"],
            sigma_alphas=a["sig"]["alphaS"] * WIDTH_AS,
            edm=a.get("edmval"),
            sat_2dnll=(2 * a["nllvalreduced"]) if a.get("nllvalreduced") else None,
            ndfsat_logged=a.get("ndfsat"),
            nfrozen=a["nfrozen"],
            theta={k: a["theta"][k] for k in keys},
            phys={n: a["phys"][n] for n in inp["names"]},
        )
        if base is not None:
            d = (a["theta"]["alphaS"] - base["theta"]["alphaS"]) * WIDTH_AS
            e["d_alphas_vs_plain"] = d
            e["d_over_sigma_plain"] = d / (base["sig"]["alphaS"] * WIDTH_AS)
            e["d_over_sigma_own"] = d / (a["sig"]["alphaS"] * WIDTH_AS)
            e["d_over_sigma_max"] = d / (
                max(a["sig"]["alphaS"], base["sig"]["alphaS"]) * WIDTH_AS
            )
        out["arms"][a["tag"]] = e
    out["anchors"] = {n: float(inp["anchors"][n]) for n in inp["names"]}
    dest = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frzcs.json"
    )
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"wrote {dest}")
    print("ANALYSE_DONE")


if __name__ == "__main__":
    main()
