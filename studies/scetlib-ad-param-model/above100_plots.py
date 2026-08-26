#!/usr/bin/env python3
r"""Figures for the gen qT > 100 extension of the response matrix.

  above100_tail       the MiNNLO gen qT spectrum through and past 100 GeV, with
                      the chosen edges and the cumulative tail fraction -- the
                      figure the upper edge is justified from
  above100_migration  where events from each above-100 gen bin RECONSTRUCT: the
                      reco ptll spectrum they feed, which is what decides whether
                      an above-100 bin can touch the fit at all
  above100_correction the PROVISIONAL model-implied correction above 100, with
                      the credibility test (anchored at qT 44, predicting 44-100
                      against the true CorrZ ratio) on the same axes
"""

import argparse
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
for _p in (_WREM, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SAMPLE = "Zmumu_2016PostVFP"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--histmaker", required=True)
    ap.add_argument("--model-npz", default=None, help="output of above100_model.py --out")
    ap.add_argument("--chosen", nargs="*", type=float, default=None,
                    help="the chosen edges above 100 (drawn as vertical lines)")
    ap.add_argument("--fit-ptll-bins", type=int, default=39)
    ap.add_argument("--plot-dir", required=True)
    args = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import h5py
    from wums import ioutils as wums_io
    from wremnants.postprocessing.scetlib_np import plot_output

    with h5py.File(args.histmaker, "r") as f:
        o = wums_io.pickle_load_h5py(f[SAMPLE])["output"]
        hr = o["nominal_prefsr_yieldsResponse"]
        hr = hr.get() if hasattr(hr, "get") else hr
        hg = o["prefsr_response"]
        hg = hg.get() if hasattr(hg, "get") else hg
    hp = hr[{"acceptance": True}].project("ptll", "ptVGen", "absYVGen")
    fl = hp.values(flow=True)
    npt, nq, nay = hp.axes["ptll"].size, hp.axes["ptVGen"].size, hp.axes["absYVGen"].size
    R = np.asarray(fl[0:npt, 0:nq, 0:nay], float)
    Rov = np.asarray(fl[0:npt, nq, 0:nay], float)
    ptl = np.asarray(hp.axes["ptll"].edges, float)
    qt = np.asarray(hp.axes["ptVGen"].edges, float)
    gv = hg.values(flow=True)
    N = np.asarray(gv[0:nq, 0:nay], float)
    Nov = float(gv[nq, 0:nay].sum())
    Ntot = N.sum() + Nov
    i100 = int(np.argmin(np.abs(qt - 100.0)))
    meta = {"histmaker": args.histmaker,
            "gen qT > 100 fraction of N_gen": f"{(N[i100:].sum()+Nov)/Ntot:.6f}",
            "chosen edges above 100": str(args.chosen)}

    # ---- fig 1: the tail
    n1d = N.sum(axis=1)
    w = np.diff(qt)
    fig, axs = plt.subplots(2, 1, figsize=(8.6, 6.4), sharex=True,
                            gridspec_kw=dict(height_ratios=[2, 1]))
    axs[0].stairs(n1d / w / Ntot, qt, color="#5790fc", lw=1.8,
                  label="MiNNLO gen $q_T$, gen-fiducial")
    axs[0].set_yscale("log")
    axs[0].set_xscale("log")
    axs[0].set_ylabel(r"$(1/N)\,dN/dq_T$  [1/GeV]", fontsize=11)
    axs[0].axvline(100, color="#e42536", lw=1.6, ls="--",
                   label="correction's last edge, 100 GeV")
    tail = np.array([n1d[k:].sum() + Nov for k in range(len(n1d) + 1)]) / Ntot
    axs[1].stairs(tail[:-1], qt, color="#964a8b", lw=1.8, baseline=None)
    axs[1].set_yscale("log")
    axs[1].set_xscale("log")
    axs[1].set_ylabel("fraction of $N_{gen}$\nabove the edge", fontsize=10)
    axs[1].set_xlabel(r"gen $q_T$ [GeV]")
    axs[1].axvline(100, color="#e42536", lw=1.6, ls="--")
    for a in axs:
        a.set_xlim(60, max(qt[-1], 1000))
        a.grid(alpha=0.3, which="both")
    if args.chosen:
        for e in args.chosen:
            for a in axs:
                a.axvline(e, color="k", lw=1.0, ls=":")
        axs[0].plot([], [], color="k", lw=1.0, ls=":", label="new gen bin edges")
        for e in args.chosen:
            k = int(np.argmin(np.abs(qt - e)))
            axs[1].annotate(f"{tail[k]:.1e}", (e, tail[k]), fontsize=8,
                            xytext=(3, 4), textcoords="offset points")
    axs[0].legend(fontsize=9)
    axs[0].set_title("the gen $q_T$ tail the response matrix has to cover "
                     "(the upper edge is read off the lower panel)", fontsize=10)
    fig.tight_layout()
    plot_output.save_plot(args.plot_dir, "above100_tail", fig=fig, args=args,
                          meta_info=meta, dpi=140)

    # ---- fig 2: migration reach
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    cols = plt.get_cmap("viridis")(np.linspace(0.05, 0.92, nq - i100))
    tot_pt = R.sum(axis=(1, 2)) + Rov.sum(axis=1)
    for j, k in enumerate(range(i100, nq)):
        y = R[:, k, :].sum(axis=1)
        if y.sum() <= 0:
            continue
        ax.stairs(np.where(tot_pt > 0, y / tot_pt, 0), ptl, color=cols[j], lw=1.5,
                  label=f"gen $q_T$ [{qt[k]:g}, {qt[k+1]:g}]")
    ax.set_yscale("log")
    ax.set_xlabel(r"reco $p_T^{\ell\ell}$ [GeV]")
    ax.set_ylabel("fraction of that reco bin's corrected-MC yield")
    ax.axvline(ptl[args.fit_ptll_bins], color="#e42536", lw=1.8, ls="--",
               label=f"top of the fit's reco range ({ptl[args.fit_ptll_bins]:g} GeV)")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=8, ncol=2)
    ax.set_title("how far down each above-100 gen bin reconstructs", fontsize=10)
    fig.tight_layout()
    plot_output.save_plot(args.plot_dir, "above100_migration", fig=fig, args=args,
                          meta_info=meta, dpi=140)

    # ---- fig 3: the provisional correction
    if args.model_npz and os.path.exists(args.model_npz):
        d = np.load(args.model_npz)
        qtc, N_g = d["qt"], d["N_gen"]
        imp, tru, nb = d["imp_all"], d["t_all"], int(d["n_below"])
        wq = N_g / np.maximum(N_g.sum(axis=1, keepdims=True), 1e-30)
        imp1 = (imp * wq).sum(axis=1)
        tru1 = (tru * wq[:nb]).sum(axis=1)
        fig, ax = plt.subplots(figsize=(8.6, 5.0))
        ax.stairs(tru1, qtc[: nb + 1], color="#5790fc", lw=2.0,
                  label="CorrZ, the correction that exists (qT < 100)")
        ax.stairs(imp1[:nb], qtc[: nb + 1], color="#964a8b", lw=1.4, ls="--",
                  label="model-implied, anchored at [90, 100] -- where truth exists")
        ax.stairs(imp1[nb:], qtc[nb:], color="#e42536", lw=2.2,
                  label="model-implied, PROVISIONAL (no correction there yet)")
        ax.axvline(100, color="k", lw=1.2, ls="--")
        ax.set_xscale("log")
        ax.set_xlabel(r"gen $q_T$ [GeV]")
        ax.set_ylabel(r"$\sigma_{\rm theory}/\sigma_{\rm MiNNLO}$")
        ax.grid(alpha=0.3, which="both")
        ax.legend(fontsize=9)
        ax.set_title("what the correction above 100 will look like: a PREVIEW, "
                     "not a validation", fontsize=10)
        fig.tight_layout()
        plot_output.save_plot(args.plot_dir, "above100_correction", fig=fig,
                              args=args, meta_info=meta, dpi=140)
    print(f"plots -> {args.plot_dir}")


if __name__ == "__main__":
    main()
