# diff_scales: the transition-point VALUE response has the wrong sign

Branch `autodiff-sigmaul`, tested at `bc20d31` (module built 2026-08-20 08:33).
Z, CT18Z, N3+0LL/NNLO, the FranksValsVars production runcard.

**Symptom.** Making the same physical change two ways gives opposite answers.
Change only the central transition point, x2: 0.6 -> 0.35
(`transition_points [0.2,0.6,1.0] -> [0.2,0.35,1.0]`, production variation [35]).

  * **A** — change it in the runcard, `diff_scales` OFF (so the profile comes
    from `Scale_provider`)
  * **B** — set `scale_x2 = 0.35` as the differentiable parameter, `set_diff_scales(1)`

Response sigma(x2)/sigma(0.6), Q in [60,120], |Y| in [0,0.15],
`fo_resolve_muR` off on both sides:

```
 qT bin     A: runcard, diff_scales off   B: parameter, diff_scales on   production run   CorrZ template
[20, 24]              0.996925                      1.024221               0.997057         0.996925
[28, 33]              0.981782                      1.115292               0.982548         0.981784
[33, 44]              0.966985                      1.159163               0.968072         0.966987
```

A reproduces both the standalone `scetlib-run-qT.py` production output and the
downstream CorrZ template to ~2e-6. B has the opposite sign.

**It is a wrong slope, not a large-excursion effect.** At x2 = 0.6 the two agree
to 4.4e-16. The error then grows LINEARLY from zero and is already sign-flipped
at dx2 = 0.01:

```
   x2     dx2    A (production)   B (diff_scales)   B/A - 1
 0.61   +0.01        1.000689         0.995273      -5.41e-03
 0.62   +0.02        1.001345         0.990681      -1.07e-02
 0.65   +0.05        1.003142         0.977668      -2.54e-02
 0.70   +0.10        1.005653         0.958264      -4.71e-02
```
(qT [33,44]; d(error)/dx2 ~ -0.27, roughly constant, i.e. dsigma/dx2 has the
wrong sign and is about -7x the production value.)

**Ruled out.**
* The profile formula is shared: `Scale_provider::_f_run`/`_g_run` call the same
  `formulas::f_run`/`g_run` the AD kernel calls.
* `calculation_piece`: `sing` gives 1.1539 where `matched` gives 1.1592 -- both wrong.
* The rule cache: cached replay matches a live `sigma_binned_batch` to 2.3e-04 at
  x2 = 0.35 and 1e-15 at the anchor, so this is not rule compression.
* Config: `muf_follows_muB = no` and `transition_type = slope` on both sides, same
  central triple.
* Downstream: the raw production pkl itself gives 0.9681, so it is not the
  correction-building step.

**kappa_R looks fine in the same test.** `kappaFO=0.5, kappaf=2.` via the runcard
vs `scale_kappa_R = 0.5` as a parameter agree to 1-2e-3 in these bins, so this
looks specific to the transition-point terms rather than the whole `prof_live`
branch. (We have a separate, unexplained ~4e-2 kappa_R discrepancy against the
templates in the FIRST qT bin, not yet A/B-tested.)

Given `1bab661` ("value path proven exact; clad adjoint for the scales confirmed
wrong"), this may be a case the value-path check did not cover.
