# SCETlib `set_diff_scales`: what is differentiable, and what is WRONG

Branch `autodiff-sigmaul`. Status as of 2026-08-21 (HEAD `6907326`, plus the
local fixes in `scetlib-cms` MRs !3 and !4).

`set_diff_scales(1)` is what makes the profile scales differentiable at all: it
registers `scale_kappa_R`, `scale_x1..x3` and an (inert) `scale_kappa_F`. Without
it those parameters do not exist and clad returns a **silently zero** adjoint --
so it is not optional, it is the mechanism.

Turning it on does **not** change the central prediction: the anchor agrees with
`diff_scales` off to 4.4e-16.

## `scale_x1..x3` (the matching transition points) are WRONG -- do not float them

The VALUE is exact at the anchor but its SLOPE in x2 has the **wrong sign** and
is about **-7x** too large, visible already at `dx2 = 0.01`. Since a fit
differentiates the same value function, the fit derivative inherits the sign
error. Measured, Z / CT18Z / N3+0LL, Q in [60,120], |Y| in [0,0.15]:

```
 x2      runcard, diff_scales OFF   parameter, diff_scales ON   production run
0.35 [33,44]      0.966985                   1.159163              0.968072
0.75 [33,44]      1.007698                   0.941312              1.007448
```
The runcard route reproduces the reference to 2e-6; the parameter route does not.

**Mechanism.** The transition points move `muf` (~20% for x2: 0.6 -> 0.35, since
`Lf ~ 1e-12` means muf tracks muB), and the per-node BEAM CONVOLUTIONS are frozen
at the config's `muf` -- `conv_probe` shows they change by 7-16% over that range.
Changing the runcard refills the nodes so they follow; changing the parameter
moves only the scales and the logs.

**Why `kappa_R` escapes THIS bug:** `set_muR_factor` scales mu_R *at FIXED mu_F*
("kappaFO *= factor, kappaf /= factor"), so the convolutions never need to move.
And muF as its OWN direction has member/interpolation machinery. An `muf` change
**induced** by x1..x3 never reaches that machinery. (`kappa_R` had a *separate*
bug of its own -- see the next section -- so "agrees above qT ~ 8" was true and
"agrees" was not.)

## `scale_kappa_R` had a floor-compensation bug -- FIXED, needs MR !3

`Scale_provider::operator()` compensates the mu_B/mu_S/nu_S minimum-scale floors
by `w_fo = mu_FO/Q` when `compensate_fo` is set, so a fixed-order scale variation
leaves the large-b_T floor where it was. The AD live-profile branch scaled
`fo_mu` by the live `kappa_R` but passed `ad_g.prof_w_fo`, frozen at configure
time as `_muFO_mu/Q` -- so the floor landed at `muB_min * kappa_R` instead of
`muB_min`. Below qT ~ 5 GeV, where the floor is what sets the scales, the
response was wrong by up to **3.3%**; above qT ~ 8 it was fine, which is why it
read as agreement.

Measured, Z / CT18Z / N3+0LL, Q in [60,120], |Y| in [0,0.15], each column a ratio
to its own central (`kappaFO0.5-kappaf2.`):

```
 qT      runcard (ADoff)   param, FIXED   param, before   CorrZ template
[0,1]       0.940886         0.940888        0.910108        0.946789
[2,3]       0.951370         0.951370        0.945731        0.952038
[8,9]       0.995254         0.995254        0.994576        0.995209
[33,44]     1.015613         1.015613        1.015610        1.015527
```
max deviation from the runcard route: **9.1e-06 fixed, 3.3e-02 before**.

Fix: `prof_compensate_fo` as its own flag, and `prof_w_fo * kR` at both live
sites in `ad_kernel.hpp`. `prof_w_fo` alone cannot stand in for it -- it is
exactly 1.0 for the usual central runcard whether compensation is on or off.

**Why the upstream bit-for-bit check missed it:** `examples/matched_ad/matched.conf`
sets no `mu0_min/muB_min/muS_min/muf_min` (default 0) and no `compensate_fo`
(`Scale_provider::_compensate_fo {false}`) -- invisible twice over. Same class as
`b919b61` ("Node_shared is not bT-independent", whose comment records "exactly 0
with the floors removed"). **Any AD-vs-production check on a card without the
floors is not testing the floors.**

`kappa_R` is still only LINEAR with sigma = 0.5, so +-1 sigma spans [0.5, 1.5]
while the production template varies [0.5, 2.0]: the up direction is understated.
That is an approximation, not a bug.

Reported upstream (issue on `scetlib/contrib/scetlib-cms`). The obvious fix does
not work: the muF machinery is a GLOBAL member interpolation
(`tf = log(kF)/var_muf_lnstep`) while the induced shift is PER NODE, and
`DrellYan.hpp:586` shows per-node `dconv` was considered and rejected.

## Other things that bite

- **`kappa_F` is inert** unless the cache was built with the muF member pair
  (`has_muf`). A fit that floats it is refused (`_check_no_inert_params`), but
  setting it directly in an offline script silently does nothing.
- **The POD-layout guard invalidates caches across builds.** `load_bin_rules`
  refuses a cache whose `sizeof(ad::GlobalData)` differs (e.g. 2368 -> 2424
  across the 2026-08-21 pull) rather than reinterpreting raw bytes. Expect to
  rebuild every cache after pulling SCETlib.
- **The variation weight re-solve is ridge-limited** (`rule_min_norm_update`,
  used by `build_pdf_variations`). It solves
  `w = w0 + A^T (A A^T + lambda I)^-1 (b - A w0)` with
  `lambda = 1e-10 * tr(A A^T)/m`, so ONE pass leaves
  `lambda/(sigma^2 + lambda)` of the residual per eigendirection -- a floor right
  at the 1e-6 the caller then *checks*. Any change tightening the Gram spectrum
  trips it with no bug present (the kappa_R fix did: a purer perturbative
  gradient row sits closer to the alphaS/muF rows). Fixed by iterating the
  correction on the same Cholesky factor (MR !4). **Read the printed residual
  carefully: a value exactly equal to the tolerance is the signature of a check
  bounded by its own regularizer, not of a physics failure.** The genuinely
  unsatisfiable case is instead `nsel < m = 1 + n_train_var*(1+P)`, which no
  amount of refinement helps -- lower `n_train_var` or retain more nodes.
- **The 3rd `configure()` in one process segfaults** on `6907326` (`bc20d31`
  handled six). Use one process per measurement in any script that configures
  repeatedly.
- **Diagnostics worth knowing:** `node_scalars_probe(Q, Y, x, qT)` returns the 25
  node scalars BOTH ways (`fill_node`, then the ported `scales_eval` +
  `node_scalars_eval`) -- it validates the profile arithmetic and passes even
  where the parameter route is wrong. `conv_probe(x, muf, pid, side)` gives the
  stored beam convolutions at an arbitrary muf. Both are on the underlying
  `DrellYan`, not the python config wrapper -- reach them via
  `sigma.sub_pieces()[0]`.
- **Bisect modes** `diff_scales = 10..19` restrict `kappa_R` to one scale group
  (10 beam, 11 soft, 12 evolution, 13 hard, 14 muB alone, 15 nuB alone) so a
  restricted derivative can be compared against a value sweep of the same
  restriction. They gate kappa_R only, not the transition points.
