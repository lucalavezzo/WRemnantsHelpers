"""Theorist-facing plot: the high-qT tail deficit is the cache bT grid's small-bT lower cut.

Reads btgrid_range_isolation.npz (SCETlib full NP-on integrand W(bT) at Q=91,Y=0, qT=90/100,
plus the DE reference sval). Shows:
  (left)  the Hankel integrand qT*bf*J0(qT bf)*W(bf) vs bT -- a huge oscillatory cancellation,
          with real support down to bT<<1e-3; the cache grid starts at 1e-3 (shaded = missing).
  (right) h(bmin)/sval vs the lower cutoff bmin: DE is recovered (->1) only for bmin<~1e-5;
          the cache's bmin=1e-3 lands at 0.44 (qT=100). Density and bmax are irrelevant.

Run: wremnants container (latest) + venv + setup.sh.
"""

import numpy as np

NPZ = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ptvgen-truncation/btgrid_range_isolation.npz"
WEBDIR = "/home/submit/lavezzo/public_html/alphaS/260703_btgrid_small_bT_rootcause"
CACHE_BMIN = 1e-3
Q, Y = 91.0, 0.0


def main():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.interpolate import CubicSpline
    from scipy.integrate import simpson
    from scipy.special import j0
    from wremnants.postprocessing.scetlib_np import plot_output

    d = np.load(NPZ)
    bT = d["bT_m"]
    qts = [90.0, 100.0]
    colors = {90.0: "C0", 100.0: "C3"}

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 5.2))

    # ---- left: Hankel integrand density (y-zoom reveals the small-bT ramp; big lobes clipped) ----
    qt = 100.0
    W = d[f"W_m_{qt:.0f}"]
    sval = float(d[f"sval_{qt:.0f}"])
    spl = CubicSpline(bT, W)
    bf = np.logspace(-6, np.log10(12.0), 2_000_000)
    dens = qt * bf * j0(qt * bf) * spl(bf)
    axL.plot(bf, dens, color="C3", lw=0.7)
    axL.axvspan(bf.min(), CACHE_BMIN, color="0.85", zorder=0)
    small = bf < CACHE_BMIN
    axL.fill_between(
        bf[small],
        0,
        dens[small],
        color="C0",
        alpha=0.6,
        label=r"small-$b_T$ area missing from cache",
    )
    axL.axvline(CACHE_BMIN, color="k", ls=":", lw=1)
    axL.axhline(0, color="k", lw=0.6)
    axL.set_xscale("log")
    axL.set_ylim(-8, 12)
    axL.set_xlabel(r"$b_T$  [GeV$^{-1}$]")
    axL.set_ylabel(r"$q_T\, b_T\, J_0(q_T b_T)\, W(b_T)$")
    axL.set_title(
        f"Hankel integrand (Q={Q:.0f}, Y={Y:.0f}, qT={qt:.0f})\n"
        r"big lobes reach $\pm$100 (clipped) & cancel; small-$b_T$ area does not"
    )
    axL.text(
        2e-2,
        9.5,
        r"oscillations $\pm$100" + "\n(off scale, cancel)",
        fontsize=8,
        color="0.3",
    )
    axL.legend(fontsize=8, loc="lower left")
    axL.grid(alpha=0.3)

    # ---- right: h(bmin)/sval cliff ----
    for qt in qts:
        W = d[f"W_m_{qt:.0f}"]
        sval = float(d[f"sval_{qt:.0f}"])
        spl = CubicSpline(bT, W)
        bmins = np.logspace(-6, -2.2, 60)
        hb = (
            np.array(
                [
                    qt
                    * simpson(
                        (g := np.linspace(bm, 50.0, 800_000)) * j0(qt * g) * spl(g), x=g
                    )
                    for bm in bmins
                ]
            )
            / sval
        )
        axR.plot(bmins, hb, "o-", ms=3, color=colors[qt], label=f"qT={qt:.0f} GeV")

    axR.axhline(1.0, color="k", lw=1, ls="--", label="SCETlib DE (truth)")
    axR.axvline(CACHE_BMIN, color="0.4", ls=":", lw=1.2)
    axR.annotate(
        f"cache $b_T^{{min}}$={CACHE_BMIN:g}",
        xy=(CACHE_BMIN, 0.45),
        xytext=(1.3e-3, 0.15),
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color="0.4"),
    )
    axR.set_xscale("log")
    axR.set_ylim(-0.2, 1.15)
    axR.set_xlabel(r"integration lower limit $b_T^{\min}$  [GeV$^{-1}$]")
    axR.set_ylabel(r"reconstructed $\sigma$ / SCETlib DE")
    axR.set_title("Recovering the DE integrator needs the small-$b_T$ tail")
    axR.legend(fontsize=8, loc="lower left")
    axR.grid(alpha=0.3)

    fig.tight_layout()
    plot_output.save_plot(
        WEBDIR,
        "btgrid_small_bT_rootcause",
        fig=fig,
        meta_info={
            "study": "ptvgen-truncation",
            "finding": "high-qT tail deficit = cache bT grid lower limit (min=1e-3) truncates "
            "the small-bT part of the deeply-cancelling Hankel integrand",
            "evidence": "bmin 1e-3->0.444, 1e-5->0.999, 1e-6->0.9997 at qT=100 (Q=91,Y=0); "
            "node density (2000..64000) and bmax irrelevant; NP factorization exact to 1e-12",
            "fix": "extend [bT_grid] min to ~1e-6 and regenerate the btgrid cache",
        },
    )
    print(f"saved -> {WEBDIR}/btgrid_small_bT_rootcause.{{png,pdf}}")


if __name__ == "__main__":
    main()
