Branch `autodiff-sigmaul`. Reproduced on current head `6907326` (module rebuilt 2026-08-21 10:30) and identical to 5 digits on `bc20d31` before it. Z, CT18Z, N3+0LL/NNLO, the FranksValsVars production runcard.

### Symptom

Making the same physical change two ways gives opposite answers. Change only the central transition point, x2: 0.6 -> 0.35 (`transition_points [0.2,0.6,1.0] -> [0.2,0.35,1.0]`, production variation `[35]`):

- **A** — change it in the runcard, `diff_scales` **off**, so the profile comes from `Scale_provider`
- **B** — set `scale_x2 = 0.35` as the differentiable parameter, `set_diff_scales(1)`

Response `sigma(x2)/sigma(0.6)`, Q in [60,120], |Y| in [0,0.15], `fo_resolve_muR` off on both sides:

| qT bin | A: runcard, ds off | B: parameter, ds on | production run | CorrZ template |
|---|---|---|---|---|
| [20, 24] | 0.996925 | 1.024221 | 0.997057 | 0.996925 |
| [28, 33] | 0.981782 | 1.115292 | 0.982548 | 0.981784 |
| [33, 44] | 0.966985 | 1.159163 | 0.968072 | 0.966987 |

A reproduces both the standalone `scetlib-run-qT.py` production output and the downstream CorrZ template to ~2e-6. B has the opposite sign.

### It is a wrong slope, not a large-excursion effect

At x2 = 0.6 the two agree to 4.4e-16. The error then grows linearly from zero and is already sign-flipped at dx2 = 0.01:

| x2 | dx2 | A (production) | B (diff_scales) | B/A - 1 |
|---|---|---|---|---|
| 0.61 | +0.01 | 1.000689 | 0.995273 | -5.41e-03 |
| 0.62 | +0.02 | 1.001345 | 0.990681 | -1.07e-02 |
| 0.65 | +0.05 | 1.003142 | 0.977668 | -2.54e-02 |
| 0.70 | +0.10 | 1.005653 | 0.958264 | -4.71e-02 |

(qT [33,44]. d(error)/dx2 ~ -0.27, roughly constant: `dsigma/dx2` has the wrong sign and is about -7x the production value.)

### Ruled out

- **The profile formula is shared.** `Scale_provider::_f_run`/`_g_run` call the same `formulas::f_run`/`g_run` that the AD kernel calls, so it is not `g_run` itself.
- **`calculation_piece`**: `sing` gives 1.1539 where `matched` gives 1.1592 — both wrong.
- **Rule compression**: the cached replay matches a live `sigma_binned_batch` to 2.3e-04 at x2 = 0.35 and 1e-15 at the anchor.
- **Config**: `muf_follows_muB = no` and `transition_type = slope` on both sides, same central triple.
- **Downstream**: the raw production pkl itself gives 0.9681, so it is not the correction-building step.

### kappa_R looks fine in the same test

`kappaFO=0.5, kappaf=2.` via the runcard vs `scale_kappa_R = 0.5` as a parameter agree to 1-2e-3 in these bins, so this looks specific to the transition-point terms rather than to the whole `prof_live` branch. (Separately we see an unexplained ~4e-2 `kappa_R` discrepancy against the templates in the *first* qT bin, not yet A/B tested — happy to open that separately if useful.)

### Mechanism (I think this is the actual cause)

The transition points move `muf`, and the per-node **beam convolutions are
frozen at the config's `muf`**:

1. `node_scalars_probe` says the ported profile is **exact**: `fill_node` vs
   `scales_eval` + `node_scalars_eval` agree to `0.00e+00` at x2 = 0.35 as well
   as at 0.6, with the scalars genuinely moving (one scale 741.54 -> 589.88). So
   the profile arithmetic is not at fault. The inlined copy in `node_value` also
   matches term-for-term once kappa_R = 1 collapses `kB_`/`kS_`/`kN_`/`kMB_` to 1.
2. x2: 0.6 -> 0.35 moves `muB` by ~20%, and `Lf ~ 1e-12` (muf tracks muB), so
   `muf` moves ~20% too.
3. `conv_probe` over that `muf` range: the stored convolutions change by up to
   **7-16%** (median 0.5-2.8%) — the same order as the discrepancy.
4. Changing the runcard refills the nodes, so the convolutions follow. Changing
   the **parameter** moves the scales and the logs only; the convolutions stay at
   the anchor's `muf`.

That gives exactly the measured signature: exact at the anchor, wrong slope
immediately, and the missing piece large enough to flip the sign.

**It also explains why `kappa_R` is fine.** `set_muR_factor` scales mu_R "at
FIXED mu_F (kappaFO *= factor, kappaf /= factor)", so kappa_R never needs the
convolutions to move — and the two paths do agree to 1-2e-3 for
`kappaFO=0.5, kappaf=2.`. And muF as its *own* direction has the member /
interpolation machinery from `33a126a` and `9abfcfa`. An `muf` change **induced**
by x1..x3 never reaches that machinery.

So this looks like a missing dependency edge rather than a formula error: the
induced `muf` shift from x1..x3 would need to go through the same
member/interpolation path the explicit muF direction uses.

### Unrelated regression on current head

The **3rd `configure()` in one process segfaults** on `6907326`; `bc20d31`
handled six fine (that is how the original A/B was run). Workaround is one
measurement per process. Happy to open this separately.
