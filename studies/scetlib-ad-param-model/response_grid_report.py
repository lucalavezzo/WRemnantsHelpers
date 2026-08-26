#!/usr/bin/env python3
r"""Report on the response-matrix gen binning: the grids, the tail, the 39 directions.

Reads
  * a histmaker output carrying BOTH gen grids -- the unfolding one
    (``nominal_prefsr_yieldsUnfolding`` + ``prefsr``) and the parallel finer
    response one (``nominal_prefsr_yieldsResponse`` + ``prefsr_response``,
    written by ``mz_dilepton --responseGenBinning theoryCorr``);
  * the two ``grain_finegrid.py`` CSVs for that run (``--tail-at 44`` and
    ``--tail-at 100``), which carry the per-direction GRAIN and its alpha_s
    equivalent at every rung of the resolution ladder.

Produces the grid/nesting figure, the gen qT tail decomposition (which is what
the "the model is 15% short above 44" observation actually is), and the
per-direction comparison between the shipped grid and the correction's own grid.
"""

import argparse
import csv
import os
import sys

import numpy as np

_WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
for _p in (_WREM, os.path.join(_WREM, "scripts", "rabbit", "scetlib_ad")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SAMPLE = "Zmumu_2016PostVFP"


def _style():
    """Activate the wums/mplhep style BEFORE laying a figure out, so that
    tight_layout sees the final font sizes (otherwise labels get clipped)."""
    from wums import plot_tools  # noqa: F401


def save(fig, outdir, basename, args=None, meta=None):
    """Write png+pdf plus the provenance .log and index.php (study convention)."""
    from wremnants.postprocessing.scetlib_np import plot_output

    plot_output.save_plot(outdir, basename, fig=fig, args=args, meta_info=meta, dpi=140)


def read_csv(path):
    with open(path) as fh:
        return [
            {
                k: (float(v) if k not in ("qgrid", "ygrid", "direction") else v)
                for k, v in row.items()
            }
            for row in csv.DictReader(fh)
        ]


def pick(rows, q, y):
    return {r["direction"]: r for r in rows if r["qgrid"] == q and r["ygrid"] == y}


def load_grids(path):
    import h5py

    from wums import ioutils as wums_io

    def get(out, n):
        p = out[n]
        return p.get() if hasattr(p, "get") else p

    with h5py.File(path, "r") as f:
        out = wums_io.pickle_load_h5py(f[SAMPLE])["output"]
        hu, hr = get(out, "nominal_prefsr_yieldsUnfolding"), get(
            out, "nominal_prefsr_yieldsResponse"
        )
        gu, gr = get(out, "prefsr"), get(out, "prefsr_response")
        d = dict(
            unf_pt=np.asarray(hu.axes["ptVGen"].edges, float),
            unf_y=np.asarray(hu.axes["absYVGen"].edges, float),
            res_pt=np.asarray(hr.axes["ptVGen"].edges, float),
            res_y=np.asarray(hr.axes["absYVGen"].edges, float),
            reco_pt=np.asarray(hu.axes["ptll"].edges, float),
            reco_y=np.asarray(hu.axes["yll"].edges, float),
        )
        # gen spectrum on the response grid, with the >100 overflow kept
        g = gr.project("ptVGen")
        v = g.values(flow=True)
        uf = 1 if g.axes["ptVGen"].traits.underflow else 0
        n = g.axes["ptVGen"].size
        d["gen_pt_spectrum"] = v[uf : uf + n].astype(float)
        d["gen_pt_overflow"] = float(v[uf + n])
        # the >100 gen column's weight in the FIT's reco range (ptll in [1, 44))
        hs = hr[{"acceptance": True}].project("ptll", "yll", "ptVGen")
        vv = hs.values(flow=True)
        uf_pt = 1 if hs.axes["ptll"].traits.underflow else 0
        npt = hs.axes["ptll"].size
        # reco ptll bins of the fit: edges 1 .. 44
        pe = np.asarray(hs.axes["ptll"].edges, float)
        lo = int(np.searchsorted(pe, 1.0 - 1e-9))
        hi = int(np.searchsorted(pe, 44.0 - 1e-9))
        block = vv[uf_pt + lo : uf_pt + hi, ...]  # (ptll, yll(+flow), ptVGen(+flow))
        uf_y = 1 if hs.axes["yll"].traits.underflow else 0
        nyl = hs.axes["yll"].size
        block = block[:, uf_y : uf_y + nyl, :]
        ufg = 1 if hs.axes["ptVGen"].traits.underflow else 0
        ngen = hs.axes["ptVGen"].size
        inr = block[:, :, ufg : ufg + ngen].sum()
        over = block[:, :, ufg + ngen].sum()
        d["reco_fit_inrange"] = float(inr)
        d["reco_fit_from_gen_above_100"] = float(over)

        # The two ways a reco-selected event can have NO gen column in R, i.e.
        # `acceptance = False`, measured in the fit's reco range. The gen
        # acceptance is `absY < 2.5 && 60 < mass < 120`, so with the gen |Y|
        # overflow resolved the split is unambiguous: overflow => the |Y| cut,
        # in-range => the gen mass window.
        hy = hr.project("ptll", "absYVGen", "acceptance")
        vy = hy.values(flow=True)
        ufp = 1 if hy.axes["ptll"].traits.underflow else 0
        ufy = 1 if hy.axes["absYVGen"].traits.underflow else 0
        nY = hy.axes["absYVGen"].size
        blk = vy[ufp + lo : ufp + hi]
        Yin, Yov = blk[:, ufy : ufy + nY, :], blk[:, ufy + nY, :]
        acc = Yin[:, :, 1].sum() + Yov[:, 1].sum()
        f_Y, f_M = float(Yov[:, 0].sum()), float(Yin[:, :, 0].sum())
        tot = acc + f_Y + f_M
        d["f_leak_absY"] = f_Y / tot
        d["f_leak_mass"] = f_M / tot
        d["acc_frac"] = acc / tot
    return d


def leak_prediction(fine, d):
    """What the fiducial leak predicts for the residual left at the exact grid.

    On the correction's own grid the fold is algebraically the per-event sum (the
    applied weight is a bin lookup, constant on the cells), so granularity
    vanishes identically. What can still differ is events the fold has NO gen
    column for -- `acceptance = False`. Splitting a reco bin into the part R has
    and the part it does not,

        r_ref = (1 - f) rho_in + f rho_out ,   model = rho_in
        =>  residual ~= f |rho_out / rho_in - 1| .

    Two leaks, both measured from the same file (`d`):

    * the GEN MASS WINDOW (`f_leak_mass`): those events land in the correction's
      Q FLOW bin, which the file holds at exactly 1.0, so rho_out = 1 and the
      prediction is f_mass x |rho_in - 1| -- and |rho_in - 1| yield-weighted over
      the reco bins is exactly the `response_wmean` column already in the table.
    * gen |Y| > 2.5 (`f_leak_absY`): rho_out is the correction's own 2.5-5 cells,
      which differ from rho_in by only a few per mille, and f is 250x smaller.

    Nothing is fitted: both f come from the histogram, rho from the table.
    """
    out = {}
    for name, row in fine.items():
        resp = float(row["response_wmean"])
        out[name] = dict(
            pred_mass=d["f_leak_mass"] * resp,
            pred_absY=d["f_leak_absY"] * resp,
            response=resp,
        )
    return out


def fig_grids(d, outdir, meta=None):
    _style()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axs = plt.subplots(2, 1, figsize=(13, 6.0), height_ratios=[2, 1])
    rows = [
        ("correction grid = response gen", d["res_pt"], "tab:red"),
        ("reco ptll (the fit binning)", d["reco_pt"], "tab:gray"),
        ("unfolding gen (shipped)", d["unf_pt"], "tab:blue"),
    ]
    for i, (lab, e, c) in enumerate(rows):
        axs[0].vlines(e, i - 0.35, i + 0.35, color=c, lw=1.2)
        axs[0].text(
            101, i, f"  {lab}  ({len(e)-1} bins)", va="center", fontsize=9, color=c
        )
    axs[0].set_xscale("symlog", linthresh=1.0)
    axs[0].set_xlim(0, 100)
    axs[0].set_yticks([])
    axs[0].set_xlabel(r"gen $q_T$  [GeV]  (symlog)")
    axs[0].set_title(
        "Gen binning: the correction's own grid refines both the shipped gen grid "
        "and the reco binning",
        fontsize=10,
    )
    rows = [
        ("correction grid = response gen", d["res_y"], "tab:red"),
        ("unfolding gen (shipped)", d["unf_y"], "tab:blue"),
    ]
    for i, (lab, e, c) in enumerate(rows):
        axs[1].vlines(e, i - 0.35, i + 0.35, color=c, lw=1.2)
        axs[1].text(2.52, i, f"  {lab}  ({len(e)-1} bins)", va="center", fontsize=9, color=c)
    axs[1].set_xlim(0, 2.5)
    axs[1].set_yticks([])
    axs[1].set_xlabel(r"gen $|Y|$")
    fig.tight_layout()
    save(fig, outdir, "gen_grid_nesting", meta=meta)
    plt.close(fig)


def fig_tail(d, outdir, meta=None):
    _style()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    e = d["res_pt"]
    v = d["gen_pt_spectrum"]
    tot = v.sum() + d["gen_pt_overflow"]
    frac = v / tot
    # per GeV, so the variable bin widths (0.5 -> 1 -> 2 -> 5 -> 10 GeV) do not
    # show up as steps in what is a smooth spectrum
    dens = frac / np.diff(e)
    fig, ax = plt.subplots(figsize=(9.0, 5.4))
    ax.stairs(dens, e, color="k", lw=1.2, label="gen $q_T$ spectrum, response grid")
    ax.axvline(44, color="tab:blue", ls="--", lw=1.2)
    ax.axvline(100, color="tab:red", ls="--", lw=1.2)
    above44 = frac[e[:-1] >= 44 - 1e-9].sum() + d["gen_pt_overflow"] / tot
    above100 = d["gen_pt_overflow"] / tot
    ax.text(
        45,
        dens.max() * 0.02,
        f"gen $q_T>44$: {above44:.2%} of $N_{{gen}}$\n"
        f"  of which $>100$: {above100:.2%}\n"
        f"  = {above100/above44:.1%} of the shipped\n     overflow column",
        fontsize=9,
    )
    ax.set_yscale("log")
    ax.set_xlabel(r"gen $q_T$  [GeV]")
    ax.set_ylabel(r"$N_{gen}$ fraction / GeV")
    ax.set_title(
        "The shipped grid's last column is one bin above 44 GeV;\n"
        "17% of it is above the correction's range, where the applied weight is 1",
        fontsize=10,
    )
    ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, outdir, "gen_qt_tail", meta=meta)
    plt.close(fig)


def fig_directions(shipped, fine, outdir, key="grain_wmean", eqkey="eq_as_grain", meta=None):
    _style()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = [n for n in shipped if n in fine]
    names.sort(key=lambda n: -shipped[n][key])
    a = np.array([shipped[n][key] for n in names])
    b = np.array([fine[n][key] for n in names])
    ea = np.array([shipped[n][eqkey] for n in names])
    eb = np.array([fine[n][eqkey] for n in names])
    sig = shipped[names[0]]["sigma_as"]

    fig, axs = plt.subplots(1, 2, figsize=(15, 9.5))
    y = np.arange(len(names))
    axs[0].barh(y - 0.2, a, height=0.4, color="tab:blue", label="shipped gen grid 21x10")
    axs[0].barh(
        y + 0.2, b, height=0.4, color="tab:red", label="response grid = CorrZ 71x11"
    )
    axs[0].set_yticks(y)
    axs[0].set_yticklabels(names, fontsize=6)
    axs[0].invert_yaxis()
    axs[0].set_xscale("log")
    axs[0].set_xlabel("GRAIN (yield-weighted)")
    axs[0].legend(fontsize=8)
    axs[0].set_title("Gen-binning granularity, per theory direction", fontsize=10)

    axs[1].barh(y - 0.2, np.abs(ea) / sig, height=0.4, color="tab:blue")
    axs[1].barh(y + 0.2, np.abs(eb) / sig, height=0.4, color="tab:red")
    axs[1].set_yticks(y)
    axs[1].set_yticklabels([])
    axs[1].set_xscale("log")
    axs[1].set_xlabel(r"$|\Delta\alpha_s|/\sigma(\alpha_s)$ per unit pull")
    axs[1].set_title(
        rf"$\alpha_s$ equivalent (Fisher proxy, $\sigma$ = {sig:.3e})", fontsize=10
    )
    fig.tight_layout()
    save(fig, outdir, "grain_per_direction", meta=meta)
    plt.close(fig)
    return names, a, b, ea, eb, sig


def fig_leak(names, measured, predicted, outdir, meta=None):
    _style()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.6, 7.0))
    isas = np.array(["as_0" in n for n in names])
    ax.scatter(predicted[~isas], measured[~isas], s=18, color="tab:blue",
               label="theory directions (pure bin lookup)")
    ax.scatter(predicted[isas], measured[isas], s=40, color="tab:red", marker="s",
               label=r"$\alpha_s$ legs (event-level PDF weight)")
    lim = [
        0.5 * min(predicted[predicted > 0].min(), measured[measured > 0].min()),
        2 * max(predicted.max(), measured.max()),
    ]
    ax.plot(lim, lim, "k--", lw=1, label="measured = predicted")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("predicted, gen mass-window leak")
    ax.set_ylabel("measured residual")
    ax.set_title(
        "At the correction's own grid the residual is no longer granularity",
        fontsize=10,
    )
    ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, outdir, "leftover_vs_leak", meta=meta)
    plt.close(fig)


def fig_sawtooth(npz_path, outdir, gen_edges, meta=None):
    """|GRAIN| per reco ptll bin: the saw-tooth on the shipped grid, and its end."""
    _style()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = np.load(npz_path)
    pt = d["ptll_edges"]
    ctr = 0.5 * (pt[:-1] + pt[1:])
    out = {}
    for k in d.files:
        if "__" not in k:
            continue
        q, L = k.split("__", 1)
        out.setdefault(q, {})[L] = d[k]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    styles = {"card": ("tab:blue", "shipped gen grid (1 gen bin per 2 reco bins)"),
              "fine": ("tab:red", "response grid = the correction's cells")}
    for q, (c, lab) in styles.items():
        if q not in out:
            continue
        P = np.array([v for k, v in sorted(out[q].items()) if "as_0" not in k])
        ax.plot(ctr, np.median(P, axis=0), "o-", ms=3, color=c, lw=1.2, label=lab)
    for e in gen_edges:
        if pt[0] <= e <= pt[-1]:
            ax.axvline(e, color="0.85", lw=0.7, zorder=0)
    ax.set_yscale("log")
    ax.set_xlabel(r"reco $p_T^{\ell\ell}$  [GeV]")
    ax.set_ylabel(r"median $|$GRAIN$|$")
    ax.set_title(
        "The residual alternates with the shipped gen-bin boundaries (grey) "
        "and stops doing so\non the correction's own grid",
        fontsize=10,
    )
    ax.legend(fontsize=8)
    fig.tight_layout()
    save(fig, outdir, "grain_sawtooth_killed", meta=meta)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--histmaker", required=True)
    ap.add_argument("--csv-tail44", required=True)
    ap.add_argument("--csv-tail100", required=True)
    ap.add_argument("-o", "--outdir", required=True)
    ap.add_argument("--profile-npz", default=None,
                    help="the --profile-npz written by grain_finegrid.py --tail-at 100")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    d = load_grids(args.histmaker)
    print("GEN GRIDS")
    print(f"  unfolding : ptVGen {len(d['unf_pt'])-1} bins to {d['unf_pt'][-1]:g} "
          f"(+overflow), absYVGen {len(d['unf_y'])-1} to {d['unf_y'][-1]:g}")
    print(f"  response  : ptVGen {len(d['res_pt'])-1} bins to {d['res_pt'][-1]:g} "
          f"(+overflow), absYVGen {len(d['res_y'])-1} to {d['res_y'][-1]:g}")
    for name, fine, coarse in (
        ("qT  unfolding in response", d["res_pt"], d["unf_pt"]),
        ("qT  reco ptll in response", d["res_pt"], d["reco_pt"]),
        ("|Y| unfolding in response", d["res_y"], d["unf_y"]),
    ):
        bad = [
            float(x) for x in coarse if not np.any(np.abs(fine - x) < 1e-9)
        ]
        print(f"  nesting {name}: {'ALL NEST' if not bad else f'NOT NESTED: {bad}'}")

    tot = d["gen_pt_spectrum"].sum() + d["gen_pt_overflow"]
    a44 = d["gen_pt_spectrum"][d["res_pt"][:-1] >= 44 - 1e-9].sum() + d["gen_pt_overflow"]
    print("\nGEN qT TAIL")
    print(f"  N_gen above 44         : {a44/tot:.4%}  (the shipped grid's last column)")
    print(f"  N_gen above 100        : {d['gen_pt_overflow']/tot:.4%}  "
          f"= {d['gen_pt_overflow']/a44:.2%} of that column")
    print(f"  reco yield in the fit range (ptll 1-44) fed by gen qT > 100: "
          f"{d['reco_fit_from_gen_above_100']/d['reco_fit_inrange']:.3e} of it")

    ship = pick(read_csv(args.csv_tail44), "card", "card")
    fine = pick(read_csv(args.csv_tail100), "fine", "fine")
    meta = {
        "histmaker": args.histmaker,
        "csv tail44": args.csv_tail44,
        "csv tail100": args.csv_tail100,
        "gen grids": (
            f"unfolding ptVGen {len(d['unf_pt'])-1}+of x absYVGen {len(d['unf_y'])-1}; "
            f"response ptVGen {len(d['res_pt'])-1}+of x absYVGen {len(d['res_y'])-1}"
        ),
    }
    names, a, b, ea, eb, sig = fig_directions(ship, fine, args.outdir, meta=meta)
    fig_grids(d, args.outdir, meta=meta)
    fig_tail(d, args.outdir, meta=meta)
    if args.profile_npz:
        fig_sawtooth(args.profile_npz, args.outdir, d["unf_pt"], meta=meta)

    print(f"\n39 DIRECTIONS: GRAIN (yield-weighted mean |dev|), sigma(alpha_s) = {sig:.4e}")
    print(f"  median   shipped {np.median(a):.3e} -> response {np.median(b):.3e}  "
          f"({np.median(a)/np.median(b):.1f}x)")
    print(f"  worst    shipped {a.max():.3e} ({names[int(np.argmax(a))]}) -> "
          f"response {b.max():.3e} ({names[int(np.argmax(b))]})")
    print(f"  alpha_s equivalent, worst : {np.abs(ea).max()/sig:.4f} -> "
          f"{np.abs(eb).max()/sig:.4f} sigma")
    print(f"  alpha_s equivalent, quad  : {np.sqrt((ea**2).sum())/sig:.4f} -> "
          f"{np.sqrt((eb**2).sum())/sig:.4f} sigma")
    aslegs = [i for i, n in enumerate(names) if "as_0" in n]
    keep = [i for i in range(len(names)) if i not in aslegs]
    print(f"  alpha_s equivalent, worst excluding the two alpha_s legs: "
          f"{np.abs(ea[keep]).max()/sig:.4f} -> {np.abs(eb[keep]).max()/sig:.4f} sigma")

    with open(os.path.join(args.outdir, "directions.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(
            ["direction", "grain_shipped", "grain_response", "ratio",
             "eqas_shipped_sigma", "eqas_response_sigma",
             "grain_max_shipped", "grain_max_response", "response_size"]
        )
        for i, n in enumerate(names):
            wr.writerow([
                n, f"{a[i]:.6e}", f"{b[i]:.6e}", f"{a[i]/max(b[i],1e-30):.2f}",
                f"{abs(ea[i])/sig:.5f}", f"{abs(eb[i])/sig:.5f}",
                f"{ship[n]['grain_max']:.6e}", f"{fine[n]['grain_max']:.6e}",
                f"{ship[n]['response_wmean']:.6e}",
            ])
    # ---- what is LEFT at the correction's own grid, and whether it is the leak
    pred = leak_prediction(fine, d)
    have = [n for n in names if n in pred and pred[n]["response"] > 1e-6]
    m = np.array([fine[n]["grain_wmean"] for n in have])
    q = np.array([pred[n]["pred_mass"] for n in have])
    qy = np.array([pred[n]["pred_absY"] for n in have])
    keep = [i for i, n in enumerate(have) if "as_0" not in n]
    print("\nWHAT IS LEFT AT THE CORRECTION'S OWN GRID")
    print(f"  the two fiducial leaks, measured in the fit's reco range: "
          f"gen mass window {d['f_leak_mass']:.3e}, "
          f"gen |Y| > 2.5 {d['f_leak_absY']:.3e} "
          f"(acceptance = True {d['acc_frac']:.6%})")
    print(f"  measured  median {np.median(m[keep]):.3e}  "
          f"({len(keep)} directions, excluding the alpha_s legs)")
    print(f"  predicted by the GEN MASS WINDOW leak, median {np.median(q[keep]):.3e}")
    print(f"  predicted by the |Y| > 2.5 leak,       median {np.median(qy[keep]):.3e}"
          "   <- cannot be it")
    ratio = m[keep] / q[keep]
    print(f"  measured / predicted (mass window): median {np.median(ratio):.2f}, "
          f"10th-90th pct {np.percentile(ratio, 10):.2f} - "
          f"{np.percentile(ratio, 90):.2f}")
    rho = np.corrcoef(np.log10(m[keep]), np.log10(q[keep]))[0, 1]
    print(f"  log-log correlation: {rho:+.4f}")
    for i, n in enumerate(have):
        if "as_0" in n:
            print(f"  [alpha_s leg] {n}: measured {m[i]:.3e} against {q[i]:.3e} "
                  f"predicted, a factor {m[i]/q[i]:.0f} -> the event-level PDF weight")
    fig_leak(have, m, q, args.outdir, meta=meta)

    print(f"\nper-direction table -> {args.outdir}/directions.csv")
    print("plots -> gen_grid_nesting, gen_qt_tail, grain_per_direction (.png/.pdf)")


if __name__ == "__main__":
    main()
