#!/usr/bin/env python3
"""Harvest the localisation sub-fits of the LATL4ZWALLCOLD ptll tension.

For every projected-saturated mapping in every fitresult under OUTROOT:
  q = chi2_saturated, ndf, p (chi2), sub-fit EDM, and the split of q into
  data / card constraints / model priors / wall / lattice (main postfit vs sub-fit),
  plus the alpha_s shift of the sub-fit as a DELTA in theta units and in nested-sd units
  (never an absolute alpha_s: blinded).
For the yll-band mapping (PTxYB6) also plot the squared bin scales vs ptll per band.

usage: harvest.py   (inside the container, after setup.sh)
"""
import glob
import json
import os
import sys

import h5py
import numpy as np
from scipy.stats import chi2 as chi2d
from wums import ioutils

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(TASK, "..", "260923-lattice-fits", "scripts"))
import analyze_fits as A  # noqa: E402

from rabbit import inputdata, io_tools  # noqa: E402
from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402

OUTROOT = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260924_ptll_tension_loc"
)
MAIN = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260923_lattice_fits/l4zero_walled/fitresults_LATL4ZWALLCOLD.hdf5"


def setup(meta):
    ind = inputdata.FitInputData(A.CARDA)
    inp = wall.resolve_wall_inputs(ind)
    conds = wall.damping_conditions(inp["np_model"], inp["np_model_nu"], inp["ymax"])
    systs = [s.decode() if isinstance(s, bytes) else str(s) for s in ind.systs]
    cwd = dict(zip(systs, np.asarray(ind.constraintweights)))
    pr, mu, H, _ = A.term_from_card(A.LATCARD)
    pp = meta["param_priors"]
    pn = [p.decode() if isinstance(p, bytes) else str(p) for p in pp["params"]]
    mask = np.asarray(pp["mask"], bool)
    sig = np.asarray(pp["sigmas"], float)
    mean = (
        np.asarray(pp["means"], float) if pp["means"] is not None else np.zeros(len(pn))
    )

    def decomp(h, nll, cov=None):
        names = [str(n) for n in h.axes[0]]
        th = dict(zip(names, h.values()))
        lcm = sum(
            0.5 * ((th[n] - mean[i]) / sig[i]) ** 2 for i, n in enumerate(pn) if mask[i]
        )
        lcc_d = {n: 0.5 * cwd[n] * th[n] ** 2 for n in systs if n in th}
        phys = {
            n: (
                float(wall.physical_from_theta(inp["specs"][n], th[n]))
                if n in th
                else float(inp["anchors"][n])
            )
            for n in inp["names"]
        }
        armed = [c for c in conds if any(n in th for n in c.names)]
        lpen = float(
            sum(c.penalty(phys, wall.numpy_relu2) for c in armed) * np.exp(2 * A.TAU)
        )
        t = np.array([th[n] for n in pr])
        lext = 0.5 * float((t - mu) @ H @ (t - mu))
        lcc = sum(lcc_d.values())
        sas = None
        if cov is not None:
            sas = float(
                np.sqrt(cov.values()[names.index("alphaS"), names.index("alphaS")])
            )
        return dict(
            nll=nll,
            lcm=lcm,
            lcc=lcc,
            lpen=lpen,
            lext=lext,
            ln=nll - lcm - lcc - lpen - lext,
            th=th,
            lcc_d=lcc_d,
            phys=phys,
            sig_as=sas,
        )

    return decomp


def main():
    r0 = io_tools.get_fitresult(MAIN)
    meta = ioutils.pickle_load_h5py(h5py.File(MAIN, "r")["meta"])
    decomp = setup(meta)
    m = decomp(r0["parms"].get(), float(r0["nllvalreduced"]), r0["cov"].get())

    rows = []
    for f in sorted(glob.glob(f"{OUTROOT}/*/fitresults_*.hdf5")):
        tag = os.path.basename(os.path.dirname(f))
        r = io_tools.get_fitresult(f)
        if abs(float(r["nllvalreduced"]) - m["nll"]) > 1e-6:
            print(
                f"!! {tag}: loaded NLL {float(r['nllvalreduced']):.8f} != main {m['nll']:.8f}"
            )
        for key, mp in r["mappings"].items():
            if "chi2_saturated" not in mp:
                continue
            sf = mp["saturated_fit"]
            s = decomp(sf["parms"].get(), float(sf["nllvalreduced"]), sf["cov"].get())
            q, ndf = float(mp["chi2_saturated"]), int(mp["ndf_saturated"])
            das = s["th"]["alphaS"] - m["th"]["alphaS"]
            v = s["sig_as"] ** 2 - m["sig_as"] ** 2
            nsd = (
                np.sqrt(v) if v > 1e-3 * m["sig_as"] ** 2 else np.nan
            )  # undefined when freeing costs no alpha_s precision
            movers = sorted(
                ((n, m["lcc_d"][n] - s["lcc_d"].get(n, 0.0)) for n in m["lcc_d"]),
                key=lambda x: -abs(x[1]),
            )[:6]
            row = dict(
                tag=tag,
                mapping=key,
                q=q,
                ndf=ndf,
                p=float(chi2d.sf(q, ndf)),
                edm=float(sf["edmval"]),
                d_data=2 * (m["ln"] - s["ln"]),
                d_card=2 * (m["lcc"] - s["lcc"]),
                d_model=2 * (m["lcm"] - s["lcm"]),
                d_wall=2 * (m["lpen"] - s["lpen"]),
                d_lat=2 * (m["lext"] - s["lext"]),
                dalphaS_theta=das,
                sig_as_sub_theta=s["sig_as"],
                dalphaS_nested_sd=das / nsd,
                dalphaS_main_sd=das / m["sig_as"],
                sig_ratio=s["sig_as"] / m["sig_as"],
                lambda_sub={
                    k: s["phys"][k]
                    for k in ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu"]
                },
                top_card_relief=[(n, 2 * v) for n, v in movers],
            )
            rows.append(row)
            if tag == "PTxYB6":
                plot_bands(sf["parms"].get(), mp)

    hdr = f"{'tag':7s} {'mapping':48s} {'q':>7s} {'ndf':>4s} {'q/ndf':>6s} {'p':>9s} {'EDM':>8s} | {'data':>6s} {'card':>6s} {'model':>6s} {'lat':>5s} | {'dAs[th]':>7s} {'sd_nest':>7s} {'/sd_main':>8s} {'s_sub/s':>7s}"
    print(hdr)
    for w in rows:
        print(
            f"{w['tag']:7s} {w['mapping'][:48]:48s} {w['q']:7.2f} {w['ndf']:4d} {w['q']/w['ndf']:6.2f} {w['p']:9.2e} {w['edm']:8.1e} | "
            f"{w['d_data']:6.2f} {w['d_card']:6.2f} {w['d_model']:6.2f} {w['d_lat']:5.2f} | {w['dalphaS_theta']:+7.2f} {w['dalphaS_nested_sd']:+7.2f} {w['dalphaS_main_sd']:+8.2f} {w['sig_ratio']:7.3f}"
        )
    for w in rows:
        print(
            f"  {w['tag']}: top card relief {[(n, round(v, 2)) for n, v in w['top_card_relief']]}  lambda_sub {w['lambda_sub']}"
        )
    with open(os.path.join(TASK, "harvest.json"), "w") as fo:
        json.dump(rows, fo, indent=1, default=float)


def plot_bands(h, mp):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from wums import plot_tools
    from plot_output import save_plot  # 260923-lattice-fits/scripts (on sys.path)

    names = [str(n) for n in h.axes[0]]
    vals = h.values()
    ptedges = np.array(
        [
            0,
            1,
            1.5,
            2,
            2.5,
            3,
            3.5,
            4,
            4.5,
            5,
            5.5,
            6,
            6.5,
            7,
            7.5,
            8,
            8.5,
            9,
            9.5,
            10,
            10.5,
            11,
            11.5,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            22,
            24,
            26,
            28,
            30,
            33,
            37,
            44,
        ],
        float,
    )
    bands = [(-2.5, -1.5), (-1.5, -0.7), (-0.7, 0), (0, 0.7), (0.7, 1.5), (1.5, 2.5)]
    S = np.array(
        [
            [vals[names.index(f"saturated_ch0_ptll{i}_yll{j}")] ** 2 for j in range(6)]
            for i in range(39)
        ]
    )
    fig, (ax, axr) = plt.subplots(
        2, 1, figsize=(8, 7), sharex=True, gridspec_kw=dict(height_ratios=[2, 1])
    )
    x = 0.5 * (ptedges[1:] + ptedges[:-1])
    cmap = plt.get_cmap("coolwarm")
    avg = S.mean(axis=1)
    for j, (a, b) in enumerate(bands):
        c = cmap(j / 5)
        ax.step(
            ptedges,
            np.append(S[:, j], S[-1, j]),
            where="post",
            color=c,
            label=f"$y_{{\\ell\\ell}}\\in[{a},{b}]$",
        )
        axr.step(
            ptedges, np.append(S[:, j] / avg, S[-1, j] / avg[-1]), where="post", color=c
        )
    ax.set_ylabel("fitted scale")
    axr.set_ylabel("band / mean")
    axr.set_xlabel(r"$p_{T}^{\ell\ell}$ (GeV)")
    ax.legend(fontsize=9, ncol=2)
    ax.set_xlim(0, 44)  # linear: the real bin edges, 0 included
    plot_tools.add_cms_decor(ax, "Preliminary", data=True, lumi=16.8, loc=0)
    save_plot(
        TASK,
        "ptll_scales_by_yll_band",
        fig=fig,
        meta_info={
            "note": "scales absorb the sub-fit's alpha_s/NP shift; band-to-band differences are the signal"
        },
    )


if __name__ == "__main__":
    main()
