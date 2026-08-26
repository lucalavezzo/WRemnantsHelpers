Follow-up: I think I have the mechanism, and it explains why `kappa_R` is *not* affected.

**It is not the profile arithmetic.** `node_scalars_probe` compares the 25 node scalars both ways — `fill_node` vs `scales_eval` + `node_scalars_eval` — and they agree to `0.00e+00` at x2 = 0.35 as well as at 0.6, with the scalars genuinely moving (one scale 741.54 -> 589.88). The inlined copy in `node_value` also matches term-for-term once `kappa_R = 1` collapses `kB_`/`kS_`/`kN_`/`kMB_` to 1. So `scales_eval`, `node_scalars_eval`, `fill_node` and the inlined block all handle x2 identically and correctly.

**It is the beam convolutions not following the induced `muf` shift.**

1. x2: 0.6 -> 0.35 moves `muB` by ~20%, and `Lf ~ 1e-12` (muf tracks muB), so `muf` moves ~20% too.
2. `conv_probe` over that `muf` range: the stored convolutions change by up to **7-16%** (median 0.5-2.8%) — the same order as the discrepancy.
3. Changing the runcard refills the nodes, so the convolutions follow. Changing the **parameter** moves the scales and the logs only; the convolutions stay at the anchor's `muf`.

Hence exact at the anchor, wrong slope immediately, and the missing piece large enough to flip the sign — exactly the measured signature.

**Why `kappa_R` is fine.** `set_muR_factor` scales mu_R "at FIXED mu_F (kappaFO *= factor, kappaf /= factor)", so it never needs the convolutions to move. (Correction to an earlier version of this comment: we had said the two paths "agree to 1-2e-3" for `kappaFO=0.5, kappaf=2.`. That was measured over too narrow a qT range. `kappa_R` in fact had a *separate* bug of its own below qT ~ 5 -- the live `kappa_R` was not scaling the minimum-scale compensation, so the large-bT floor moved with it -- worth 3.3e-02. That is MR !3. With it applied the two `kappa_R` routes agree to **9.1e-06** in every bin, and the transition points are bit-unchanged, which separates the two problems cleanly rather than muddying them.) muF as its *own* direction has the member/interpolation machinery from `33a126a` and `9abfcfa`. An `muf` change **induced** by x1..x3 never reaches that machinery. So this looks like a missing dependency edge rather than a formula error.

**On fixing it**, the obvious route does not seem to work: the muF direction reaches the convolutions through a *global* interpolation coordinate (`tf = log(kF)/ad_g.var_muf_lnstep`), built from members at fixed kappa_F, whereas the transition points induce a **per-node** `muf` shift (a function of qT/Q and bT through `f_run`). And `DrellYan.hpp:586` suggests carrying `dconv` per member per node was already considered and rejected. So the way forward looks like your call rather than something we should guess at.

Two things we are happy to write as MRs if useful:

1. **A regression test for the gap this fell through.** `node_scalars_probe` validates the profile arithmetic and passes; nothing validates the *parameter* route's value against the *runcard* route. A test asserting `sigma(param x2) == sigma(runcard x2)` for x1..x3 and kappa_R would have caught this immediately.
2. **Making the failure loud.** `set_diff_scales` already refuses `muf_follows_muB = yes` with precisely the right reasoning — "the beam convolutions stay frozen at their own muF and cannot follow, so the derivative would be wrong by the size of the muF dependence with nothing to indicate it." That applies verbatim to x1..x3 moving `muf`, so the same guard could refuse to register them (or flag them unvalidated) rather than returning a wrong-signed derivative.

Unrelated, on current head `6907326`: **the 3rd `configure()` in one process segfaults** (`bc20d31` handled six; that is how the original A/B was run). Workaround is one measurement per process. Happy to open that separately.
