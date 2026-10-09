#!/usr/bin/env python3
"""T6 multi-start profile of alphaS: analyse whatever PROF* fits exist and (re)make the profile plot.

    analyze_profile.py [--plot] [--json profile.json]      (in the container; one command for the final version)

Per (point, start): the result is the LAST member of its chain (PROF<pt><st>, then the relaunches PROF<pt><st>S,
...S2, ...) that has a full fitresult (> 1 MB) and `[run] exit=0`. Anything else is listed with its state and its
last logged loss (the minimiser's loss == nllvalreduced, same walled objective) -- never dropped.

Per finished fit: NLL, 2(NLL - NLL_NOMSTIFF), EDM (floating subspace: alphaS is frozen), k = (x_aS - x_aS,NOM)/sigma_NOM
(BLINDED x differences only -- no absolute alphaS anywhere), bit-exact check x_aS == seed x_aS, physical NP lambdas,
wall faces at margin 0 (census helpers), ||Delta theta/sigma_NOM|| to NOMSTIFF per family.
Per point: pairwise |dNLL|, ||Delta theta/sigma_NOM|| (all 3718 floating parameters), max component, PDF+TNP block norm.
Profile: lowest NLL per point among converged fits (EDM < --edm-max); fit 2dNLL = a k^2 + c k^3 (k = 0 is NOMSTIFF,
exactly 0), 1-sigma interval = roots of a k^2 + c k^3 = 1; symmetric/antisymmetric parts of the +-k pairs.
"""
import argparse
import glob
import json
import os
import re
import sys

import h5py
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
CENSUS = os.path.join(os.path.dirname(TASK), "261001-census-nominal", "scripts")
sys.path.insert(0, HERE)
sys.path.insert(1, CENSUS)
import analyze_census as AC  # noqa: E402  (census helpers: load_fit, physical, faces, short, family, FAMILIES)

from wremnants.postprocessing.scetlib_ad import np_damping_wall as W  # noqa: E402
from wremnants.postprocessing.scetlib_ad import response as R  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
REF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
OUT = f"{A}/261002_multistart_profile"
POINTS = [("M2", -2), ("M1", -1), ("P1", 1), ("P2", 2)]
STARTS = [("W", "warm"), ("R", "perturbed"), ("K", "PDF/TNP kick")]
KICK_RE = re.compile(r"(pdfEig\d+|resumTNP_.*)")


def chain(base):
    rel = [os.path.basename(p)[:-4] for p in glob.glob(f"{TASK}/cmds/{base}S*.cmd")]
    rel = sorted(rel, key=lambda n: (len(n), n))  # S, S2, S3, ...
    return [base] + rel


def log_info(pf):
    L = f"{OUT}/{pf}.log"
    if not os.path.exists(L):
        return dict(state="not launched")
    txt = open(L, errors="replace").read()
    losses = [float(m) for m in re.findall(r"Iteration \d+: loss ([0-9.eE+-]+)", txt)]
    m = re.search(r"^\[run\] \S+ exit=(\d+)", txt, re.M)
    ex = int(m.group(1)) if m else None
    fr = f"{OUT}/fitresults_{pf}.hdf5"
    full = os.path.exists(fr) and os.path.getsize(fr) > 1_000_000
    if ex == 0 and full:
        state = "done"
    elif ex is not None:
        state = f"exit {ex}" + (" (killed)" if ex == 137 else "")
    else:
        state = "running"
    stall = "still stalling" in txt
    return dict(
        state=state,
        exit=ex,
        n_iter=len(losses),
        loss0=losses[0] if losses else None,
        last_loss=losses[-1] if losses else None,
        stall_stop=stall,
        fitresult=fr if full else None,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plot", action="store_true")
    ap.add_argument("--json", default=f"{TASK}/profile.json")
    ap.add_argument("--edm-max", type=float, default=1e-6)
    ap.add_argument("--dnll-tol", type=float, default=1e-4)
    ap.add_argument("--floor", type=float, default=1e-4)
    args = ap.parse_args()

    ref = AC.load_fit(REF)
    names = ref["names"]
    ia = names.index("alphaS")
    sig = ref["sig"]
    nll0 = ref["nll"]
    cfg = R.corr_config_from_meta(ref["meta"])["config"]
    np_model, np_model_nu = W.forms_from_corr_config(cfg)
    lam_names = tuple(
        dict.fromkeys(W._TMD_LAMBDAS[np_model] + W._CS_LAMBDAS[np_model_nu])
    )
    _, fitted = AC.physical(ref, cfg, lam_names)
    fam = np.array([AC.family(n) for n in names])
    kick = np.array([bool(KICK_RE.fullmatch(n)) for n in names])
    flo = np.ones(len(names), bool)
    flo[ia] = False

    rows, X = [], {}
    for pt, k in POINTS:
        for st, stlab in STARTS:
            base = f"PROF{pt}{st}"
            ch = chain(base)
            infos = [(pf, log_info(pf)) for pf in ch]
            res = [(pf, i) for pf, i in infos if i["state"] == "done"]
            head_pf, head = infos[-1]
            row = dict(
                point=pt,
                k=k,
                start=st,
                start_label=stlab,
                chain=[pf for pf, _ in infos],
                chain_states={pf: i["state"] for pf, i in infos},
                n_iter_total=sum(i["n_iter"] for _, i in infos),
                loss0=infos[0][1]["loss0"],
                stall_stop=any(i["stall_stop"] for _, i in infos),
            )
            if not res:
                row.update(
                    state=head["state"],
                    result_from=head_pf,
                    converged=False,
                    nll=head["last_loss"],
                    two_dnll=(
                        None
                        if head["last_loss"] is None
                        else 2 * (head["last_loss"] - nll0)
                    ),
                )
                rows.append(row)
                continue
            pf, info = res[-1]
            fit = AC.load_fit(info["fitresult"])
            assert fit["names"] == names
            with h5py.File(f"{OUT}/seeds/{base}.hdf5", "r") as h:
                xs = h["x"][...]
            frozen_ok = bool(fit["x"][ia] == xs[ia])
            kk = float((fit["x"][ia] - ref["x"][ia]) / sig[ia])
            ph, _ = AC.physical(fit, cfg, lam_names)
            fc = AC.faces(ph, fitted, np_model, np_model_nu)
            dz = (fit["x"] - ref["x"]) / sig
            row.update(
                state="done",
                result_from=pf,
                nll=fit["nll"],
                two_dnll=2 * (fit["nll"] - nll0),
                edm=fit["edm"],
                converged=bool(fit["edm"] < args.edm_max),
                k_measured=kk,
                frozen_bit_exact=frozen_ok,
                lambdas={n: float(ph[n]) for n in fitted},
                faces_on=[AC.short(r["label"]) for r in fc if r["on"]],
                faces={AC.short(r["label"]): r["coeff"] for r in fc},
                dz_nom_family={
                    lab: float(np.linalg.norm(dz[(fam == lab) & flo]))
                    for lab, _ in AC.FAMILIES
                },
                dz_nom_kick=float(np.linalg.norm(dz[kick])),
                dz_nom_all=float(np.linalg.norm(dz[flo])),
            )
            X[(pt, st)] = fit["x"]
            rows.append(row)

    # pairwise within each point
    pairs = []
    for pt, k in POINTS:
        done = [r for r in rows if r["point"] == pt and r["state"] == "done"]
        for i in range(len(done)):
            for j in range(i + 1, len(done)):
                a, b = done[i], done[j]
                d = (X[(pt, a["start"])] - X[(pt, b["start"])]) / sig
                imax = int(np.argmax(np.abs(d * flo)))
                same = (
                    abs(a["nll"] - b["nll"]) < args.dnll_tol
                    and np.linalg.norm(d[flo]) < args.floor
                )
                pairs.append(
                    dict(
                        point=pt,
                        a=a["start"],
                        b=b["start"],
                        dnll=b["nll"] - a["nll"],
                        dz=float(np.linalg.norm(d[flo])),
                        dz_max=float(abs(d[imax])),
                        dz_max_name=names[imax],
                        dz_kick=float(np.linalg.norm(d[kick])),
                        same=bool(same),
                        both_converged=a["converged"] and b["converged"],
                    )
                )

    # profile: lowest converged NLL per point
    prof = {}
    for pt, k in POINTS:
        c = [r for r in rows if r["point"] == pt and r.get("converged")]
        if c:
            best = min(c, key=lambda r: r["nll"])
            prof[k] = dict(
                two_dnll=best["two_dnll"],
                start=best["start"],
                n_conv=len(c),
                spread=max(r["two_dnll"] for r in c) - min(r["two_dnll"] for r in c),
            )
    ks = np.array(sorted(prof))
    q = np.array([prof[k]["two_dnll"] for k in ks])
    fitres = {}
    if len(ks) >= 2:
        M = np.vstack([ks**2, ks**3]).T
        (a, c), *_ = np.linalg.lstsq(M, q, rcond=None)
        resid = q - M @ np.array([a, c])
        roots = np.roots([c, a, 0, -1])
        real = sorted(r.real for r in roots if abs(r.imag) < 1e-12 and abs(r.real) < 3)
        up = min([r for r in real if r > 0], default=None)
        dn = max([r for r in real if r < 0], default=None)
        fitres = dict(
            a=float(a),
            c=float(c),
            resid=dict(zip(map(int, ks), map(float, resid))),
            interval_up=up,
            interval_down=dn,
            n_points=len(ks),
        )
        sym = {}
        for k in (1, 2):
            if k in prof and -k in prof:
                sym[k] = dict(
                    sym=(prof[k]["two_dnll"] + prof[-k]["two_dnll"]) / 2,
                    antisym=(prof[k]["two_dnll"] - prof[-k]["two_dnll"]) / 2,
                )
        fitres["sym_antisym"] = sym
        # (b) a k^2 + c k^3 + d k^4 (least squares; exact with 4 points needs 3 params -> 1 dof)
        if len(ks) >= 3:
            M4 = np.vstack([ks**2, ks**3, ks**4]).T
            (a4, c4, d4), *_ = np.linalg.lstsq(M4, q, rcond=None)
            r4 = sorted(
                r.real
                for r in np.roots([d4, c4, a4, 0, -1])
                if abs(r.imag) < 1e-12 and abs(r.real) < 3
            )
            fitres["quartic"] = dict(
                a=float(a4),
                c=float(c4),
                d=float(d4),
                interval_up=min([r for r in r4 if r > 0], default=None),
                interval_down=max([r for r in r4 if r < 0], default=None),
            )
        # (c) a k^2 + c k^3 exactly through the k = +-1 points only (local; what matters for 2dNLL = 1)
        if 1 in prof and -1 in prof:
            a1 = (prof[1]["two_dnll"] + prof[-1]["two_dnll"]) / 2
            c1 = (prof[1]["two_dnll"] - prof[-1]["two_dnll"]) / 2
            r1 = sorted(
                r.real
                for r in np.roots([c1, a1, 0, -1])
                if abs(r.imag) < 1e-12 and abs(r.real) < 3
            )
            fitres["through_pm1"] = dict(
                a=float(a1),
                c=float(c1),
                interval_up=min([r for r in r1 if r > 0], default=None),
                interval_down=max([r for r in r1 if r < 0], default=None),
            )

    # ---- print ----
    print(
        f"NOMSTIFF NLL {nll0:.10f} (walled objective); sigma_NOM(alphaS) used as the unit; blinded differences only"
    )
    print("\nper fit:")
    print(
        f"{'pt':3s} {'st':2s} {'result':10s} {'state':16s} {'k_meas':>9s} {'frozen':6s} {'2dNLL':>12s} {'EDM':>9s} "
        f"{'iters':>5s} {'||dz_NOM||':>10s} {'pdf+tnp':>8s} faces  lambdas(l2,l4,dl2,l2nu)"
    )
    for r in rows:
        if r["state"] != "done":
            tq = "-" if r["two_dnll"] is None else f"{r['two_dnll']:.6f}"
            print(
                f"{r['point']:3s} {r['start']:2s} {r['result_from']:10s} {r['state']:16s} {'':>9s} {'':6s} "
                f"{tq:>12s} (last logged loss; chain {r['chain_states']})"
            )
            continue
        lam = r["lambdas"]
        print(
            f"{r['point']:3s} {r['start']:2s} {r['result_from']:10s} {r['state']:16s} {r['k_measured']:+9.6f} "
            f"{str(r['frozen_bit_exact']):6s} {r['two_dnll']:12.6f} {r['edm']:9.2e} {r['n_iter_total']:5d} "
            f"{r['dz_nom_all']:10.4f} {r['dz_nom_kick']:8.4f} {','.join(r['faces_on']) or '-'}  "
            + " ".join(f"{lam[n]:.6f}" for n in fitted)
            + ("  [stall stop]" if r["stall_stop"] else "")
        )
    print(
        "\npairwise within a point (Delta theta in sigma_NOM over the 3718 floating parameters):"
    )
    for p in pairs:
        print(
            f"{p['point']} {p['a']}-{p['b']}: dNLL {p['dnll']:+.2e}  ||dz|| {p['dz']:.2e}  max {p['dz_max']:.2e} "
            f"({p['dz_max_name']})  pdf+tnp {p['dz_kick']:.2e}  same={p['same']}  both converged={p['both_converged']}"
        )
    print("\nprofile (lowest converged NLL per point):")
    for k in ks:
        print(
            f"k={k:+d}: 2dNLL {prof[k]['two_dnll']:.6f} (from {prof[k]['start']}; {prof[k]['n_conv']} converged, "
            f"spread {prof[k]['spread']:.2e}); k^2 = {k*k}"
        )
    if fitres:
        print(
            f"fit 2dNLL = a k^2 + c k^3: a = {fitres['a']:.5f}, c = {fitres['c']:+.5f}; residuals {fitres['resid']}"
        )
        print(
            f"1-sigma interval (2dNLL = 1): [{fitres['interval_down']}, {fitres['interval_up']}] sigma_NOM"
        )
        for key in ("quartic", "through_pm1"):
            if key in fitres:
                print(f"{key}: {fitres[key]}")
        for k, v in fitres["sym_antisym"].items():
            print(
                f"|k|={k}: symmetric {v['sym']:.6f} (k^2 = {k*k}), antisymmetric {v['antisym']:+.6f}"
            )

    json.dump(
        dict(
            reference=REF,
            nll_ref=nll0,
            rows=rows,
            pairs=pairs,
            profile={int(k): v for k, v in prof.items()},
            fit=fitres,
        ),
        open(args.json, "w"),
        indent=1,
        default=float,
    )
    print(f"\n[json] {args.json}")
    if args.plot:
        make_plot(rows, prof, fitres, args)


def make_plot(rows, prof, fitres, args):
    import hist
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from wums import plot_tools

    from plot_output import save_plot

    XL = (-2.45, 2.45)
    YTOP = 8.5
    href = hist.Hist(hist.axis.Regular(48, *XL, name="k"))
    fig, ax, rax = plot_tools.figureWithRatio(
        href,
        r"$\Delta\alpha_S / \sigma_{\rm NOMSTIFF}$  (blinded, $\alpha_S$ frozen)",
        r"$2\Delta$NLL",
        [-0.25, YTOP],
        r"$2\Delta$NLL $- k^2$",
        [-0.35, 0.35],
        automatic_scale=False,
        width_scale=1.25,
    )
    rax = rax[0]
    ax.tick_params(labelbottom=False)
    kk = np.linspace(*XL, 400)
    ax.plot(kk, kk**2, color="0.45", ls="--", lw=1.5, label=r"Hessian parabola $k^2$")
    rax.axhline(0, color="0.45", ls="--", lw=1.5)
    if fitres:
        a, c = fitres["a"], fitres["c"]
        lab = f"fit $a k^2 + c k^3$: a = {a:.4f}, c = {c:+.4f}"
        ax.plot(kk, a * kk**2 + c * kk**3, color="C0", lw=1.8, label=lab)
        rax.plot(kk, a * kk**2 + c * kk**3 - kk**2, color="C0", lw=1.8)
        q4 = fitres.get("quartic")
        if q4:
            a4, c4, d4 = q4["a"], q4["c"], q4["d"]
            f4 = a4 * kk**2 + c4 * kk**3 + d4 * kk**4
            ax.plot(
                kk,
                f4,
                color="C4",
                lw=1.6,
                ls="-.",
                label=f"fit $a k^2 + c k^3 + d k^4$: {a4:.4f}, {c4:+.4f}, {d4:+.4f}",
            )
            rax.plot(kk, f4 - kk**2, color="C4", lw=1.6, ls="-.")
        ax.axhline(1, color="0.7", lw=0.8, ls=":")
        lines = []
        for key, lab, cc in (
            ("cubic", "cubic", "C0"),
            ("quartic", "quartic", "C4"),
            ("through_pm1", "cubic through $k=\\pm1$", "0.3"),
        ):
            src = fitres if key == "cubic" else fitres.get(key)
            if (
                not src
                or src.get("interval_up") is None
                or src.get("interval_down") is None
            ):
                continue
            lines.append(
                f"[{src['interval_down']:+.3f}, {src['interval_up']:+.3f}] $\\sigma$ ({lab})"
            )
            if key != "through_pm1":
                for v in (src["interval_down"], src["interval_up"]):
                    ax.axvline(v, color=cc, lw=0.8, ls=":")
        if lines:
            ax.text(
                0.0,
                1.3,
                "$2\\Delta$NLL = 1:\n" + "\n".join(lines),
                ha="center",
                va="bottom",
                fontsize=9,
                color="0.15",
            )
    ax.scatter(
        [0], [0], marker="*", s=260, color="k", zorder=5, label="NOMSTIFF ($k = 0$)"
    )
    rax.scatter([0], [0], marker="*", s=200, color="k", zorder=5)
    mk = {"W": "o", "R": "s", "K": "^"}
    col = {"W": "C1", "R": "C2", "K": "C3"}
    off = {"W": -0.07, "R": 0.0, "K": 0.07}
    for r in rows:
        if r.get("two_dnll") is None:
            continue
        x = r["k"] + off[r["start"]]
        y = r["two_dnll"]
        filled = bool(r.get("converged"))
        kw = dict(
            marker=mk[r["start"]],
            s=90,
            zorder=4,
            edgecolors=col[r["start"]],
            linewidths=1.8,
            facecolors=col[r["start"]] if filled else "none",
        )
        if y <= YTOP:
            ax.scatter([x], [y], **kw)
            if abs(y - r["k"] ** 2) < 0.35:
                rax.scatter([x], [y - r["k"] ** 2], **kw)
        else:  # off scale: up-arrow at the top edge, small label stacked below, pointing AWAY from the legend
            ax.annotate(
                "",
                xy=(x, YTOP),
                xytext=(x, YTOP - 0.9),
                annotation_clip=False,
                arrowprops=dict(arrowstyle="-|>", color=col[r["start"]], lw=1.6),
            )
            ax.scatter([x], [YTOP - 0.9], **kw)
            yl = YTOP - 1.2 - 0.4 * ["W", "R", "K"].index(r["start"])
            ax.text(
                x,
                yl,
                f"{r['start']}: {y:.0f} ({'running' if r['state'] == 'running' else r['state']})",
                ha="center",
                va="top",
                fontsize=8,
                color=col[r["start"]],
            )
    hs = [
        Line2D(
            [],
            [],
            ls="",
            marker=mk[s],
            markersize=10,
            markeredgecolor=col[s],
            markerfacecolor=col[s],
            label=f"start {s} ({lab})",
        )
        for s, lab in STARTS
    ]
    hs.append(
        Line2D(
            [],
            [],
            ls="",
            marker="o",
            markersize=10,
            markeredgecolor="0.3",
            markerfacecolor="none",
            label=f"open: not converged / running (EDM $\\geq$ {args.edm_max:g} or no fitresult)",
        )
    )
    h0, l0 = ax.get_legend_handles_labels()
    ax.legend(
        h0 + hs,
        l0 + [h.get_label() for h in hs],
        loc="upper center",
        fontsize=10,
        ncol=1,
        frameon=False,
    )
    ax.text(
        0.0,
        4.15,
        "Real data, BLINDED (differences only)\nnominal: card A + lattice, $\\lambda_4^\\nu=0$, "
        "wall margin 0, $\\tau$=8\nindependent fits, $\\alpha_S$ frozen at each $k$",
        fontsize=9,
        va="top",
        ha="center",
    )
    plot_tools.add_cms_decor(ax, "Preliminary", data=True, lumi=16.8, loc=0)
    save_plot(
        outdir=TASK,
        basename="profile_alphas_multistart",
        fig=fig,
        args=args,
        meta_info={
            "reference": REF,
            "edm_max": args.edm_max,
            "fit": fitres,
            "profile": {int(k): v for k, v in prof.items()},
        },
    )
    print(f"[plot] {TASK}/profile_alphas_multistart.png")


if __name__ == "__main__":
    main()
