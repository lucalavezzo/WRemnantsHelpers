# Decisions — validation of the production 62-member PDF eigenvector cache

Staged separately from `DECISIONS.md` because other agents are live in that
file. Owner: the pdf62 VALIDATION agent, 2026-08-26 (the build agent's file is
`DECISIONS_pdfbuild.md`; this one only validates what that one produced).

Artefact:
`/ceph/.../scetlib_ad_caches/pdf62_260826/merged_full/{cache.npz,cache.conf}`
Webdir: `~/public_html/alphaS/260826_scetlib_ad_pdf62_validation/`
SCETlib: the snapshot at `tmp/pdf62/scetlib_snapshot`, md5(libscet-qT.so)
`0c5dd7a92fea9e2ad0cb81639e9689a2` = `near-anchor-knots` `eb60a04`, the only
tree with BOTH `92f1299` (muF member coordinate, MR !8) and `3a8db11` /
`_rule_is_matched` (non-singular double count). Every number below is on it.

Inherited and NOT relitigated: D-012 (qT [0,1] cutoff mismatch reported
separately), D-013, D-016, D-023 (the memoisation trap), D-024, D-025, D-026,
D-R07, D-R13, P-001.

Status key: **SETTLED** (evidence in hand) / **PROVISIONAL** / **OPEN**.

---

### V-001 — The cache PASSES the acceptance gate and is DELIVERED — SETTLED

**What:** `backend_check.py` on the merged 210-bin, 62-member cache passes every
check. Anchor re-evaluation bit-identical `True`; Hessian symmetry
`max|H − Hᵀ|/max|H| = 0.00e+00` at shape (210, 53, 53); fold sum rule
`0.00e+00`; finite difference vs analytic worst `8.14e-07` over
{alphas, np_eff_lambda2, np_gnu_lambda2, scale_kappa_F, scale_kappa_R,
pdf_eig0, pdf_eig5, pdf_eig14, pdf_eig28} → OK. `sum(sigma) = 670.01137`.

**Why that last number matters on its own:** D-025 validated
`target_precision_rel = 1e-3` against a direct SCETlib run at cache total
670.0115 vs direct 670.018. This independently built cache lands at 670.01137,
i.e. 1.9e-07 from the number D-025 recorded and 9.9e-06 from the direct
calculation. The tolerance decision is reconfirmed on the production artefact
rather than inherited.

**Log:** `webdir/logs/backend_check.log`.
**Overturned by:** nothing short of a failing re-run; the gate is cheap (5 min
of wall clock) and should be re-run on any cache that is rebuilt.

### V-002 — `pdf_eig0`'s expected FD failure did NOT occur, and the diagnosis is now MEASURED not argued — SETTLED

**What happened:** the brief warned to expect one spurious failure —
`pdf_eig0`'s FD check against a zero-anchored parameter at `h = 1e-7`. On the
4-bin test cache it read `2.97e-04 -> FAIL`. On the production 210-bin cache it
reads **`8.14e-07 -> OK`**. Nothing was suppressed; the failure genuinely does
not happen at 210 bins.

**Why, quantitatively.** `backend_check` uses `h = 1e-4·max(|anchor|, 1e-3)`,
which is `1e-7` for every `pdf_eigN` (anchor 0). The *relative* error is the
round-off floor `~eps·sum(sigma)/h` divided by the derivative. On 4 bins
`d(sum sigma)/d(eig0)` was `3.4e-04`; on the full grid it is `−0.699`, **2000x
larger**, against a floor that grew only with `sum(sigma)` (9.75 → 670). So the
same artefact is invisible here.

**The experiment that settles it, not the argument.** A step-size scan
(`pdf62_eig_conventions.py`, folded into the same model load):

| parameter | analytic | 1e-7 | 1e-6 | 1e-5 | 1e-4 | 1e-3 | 1e-2 | 1e-1 |
|---|---|---|---|---|---|---|---|---|
| pdf_eig0  | −0.69942075 | 8.1e-07 | 8.6e-10 | 8.6e-10 | 7.7e-10 | 8.1e-09 | 8.1e-07 | 8.1e-05 |
| pdf_eig5  | −5.5893764  | 9.1e-08 | 9.3e-09 | 1.6e-10 | 5.4e-11 | 1.2e-09 | 1.2e-07 | 1.2e-05 |
| pdf_eig28 | −2.1331645  | 3.3e-07 | 4.1e-08 | 2.2e-09 | 2.4e-10 | 2.1e-09 | 2.1e-07 | 2.1e-05 |

The classic V, with truncation rising **exactly as h²** (1e-2 → 1e-1 is a factor
100 for all three) and round-off falling as 1/h below. A wrong analytic gradient
would be FLAT. The eigenvector gradients are correct.

**Decision:** do NOT "fix" `backend_check`'s step rule. It is only misleading on
a thin cache, where the summed derivative can nearly cancel; on any production
cache it passes, and a step that adapts to the derivative would hide the
information that the FD is at its floor. **Do** read a `pdf_eig*` FD failure on
a small cache as a step-size artefact and confirm with the scan.
**Overturned by:** a scan that is flat in h.

### V-003 — The 21-shard PRODUCTION merge is bit-exact against its parents — SETTLED

D-033 validated the MECHANISM on a two-shard test. This is the production
merge, in **three separate processes** because `values_and_jacobian` memoises on
the parameter vector alone (D-023) and an in-process A/B can return a perfect
and wrong null.

At the anchor and at a displaced point moving alphas, `np_eff_lambda2`,
`scale_kappa_F` and **all 29 eigenvectors** at once:

| selection | sum(sigma), 12 digits | sum|jac| | sum(jac[:,alphas]) |
|---|---|---|---|
| merged, all 210 | 670.011373467717 | 7372.0288930663 | 5632.8534612831 |
| merged, ptV bin 10 | 23.803535871830 | 286.4425915645 | 274.9971260457 |
| **shard qt10** | **23.803535871830** | **286.4425915645** | **274.9971260457** |
| merged, ptV bin 5 | 34.925188425489 | 107.4837964497 | 89.9805604447 |
| **shard qt5** | **34.925188425489** | **107.4837964497** | **89.9805604447** |

Identical to all twelve digits in value AND Jacobian, and **the arms are
provably separated** — the three totals are different, so no memoised
collision. qt5's 34.925188 also reproduces the figure D-033 recorded for the
same shard in a different session.

Cheap structural check alongside it (numpy only, no model load): the 21
`qt*` shards' bin lists are EXACTLY the merged 210 bins, in order, zero
duplicates, and every shard carries `n_eig 29 / has_as 1 / has_muf 1`. The five
`qt0y*` sub-shards are correctly absent — including them would have duplicated
qt0's ten bins, which `merge_bin_caches` refuses loudly (P-006).

**Overturned by:** nothing; this is the check to repeat verbatim on any future
merge, and `pdf62_merge_ab.py` exists for that.

### V-004 — The eigenvector variations reproduce the templates in the accuracy class already accepted — SETTLED

Measured with `validate_variations.py` (reused, not reimplemented; `--partial`
not needed since the cache tiles the full grid) against
`..._pdfvars_CorrZ.pkl.lz4`, all 58 members, all 210 gen bins:

| | min | median | max |
|---|---|---|---|
| max\|dev\|, all qT | 4.02e-04 | 9.03e-04 | **2.43e-03** (pdf38) |
| max\|dev\|, qT > 1 GeV | 2.05e-05 | 2.61e-04 | 8.23e-04 |
| mean\|dev\| | 1.05e-05 | 2.91e-05 | 7.89e-05 |

Against the 39 directions already signed off **on the same cache**: max
1.40e-02 (mufup), median 7.14e-04. **8 of those 39 are worse than the worst of
the 58**, and 16 are worse than the eigenvector median. Relative accuracy
(residual / that direction's own response amplitude, the D-R14 metric):
eigenvectors median 0.058 / worst 0.238, the 39 others median 0.037 / worst
0.252 — the same class.

**Where the residual lives, which is what decides whether it is a model error.**
Monotonically concentrated at low qT. pdf38: 2.43e-03 at [0,1] → 8.23e-04 at
[1,2] → 2.4e-04 at [2,3] → ~1e-05 by qT 12 → 2.3e-06 at [24,28]. Above qT 16
GeV **all 58 close to ≤ 1.67e-05**, while the three transition directions still
sit at 2.50e-03. The eigenvectors have no high-qT pathology; their residual is
the same low-qT nonsingular-cutoff / template-precision effect every other
direction shows (D-012).

**Overturned by:** a finer gen grid whose eigenvector residual does not fall at
low qT — that would make it a calculation error rather than a binning/cutoff one.

### V-005 — The earlier "~1e-6" is CONFIRMED in its window and REFUTED as a full-grid number — SETTLED

The 2026-08-25 measurement on |Y| < 0.3, qT [20,28] gave 6e-08 .. 1.5e-06 for
the 58 members. This cache reproduces that (pdf38 at [20,24] / [24,28] =
5.5e-06 / 2.3e-06). The full-grid number is ~1000x larger, and **that is not a
degradation specific to the eigenvectors**: the NP lambdas move by the same
factor between the same two windows (1.5e-07 .. 6.5e-07 on the window,
1.3e-03 .. 4.9e-03 on the grid). The window number was not wrong; it simply
never described the grid, because the grid contains qT [0,1] and the forward
|Y| bins.

**Decision:** stop quoting window numbers for this model without the window.
Any accuracy claim carries its (|Y|, qT) domain or it is not a claim.

### V-006 — CONVENTION: templates and model are the SAME convention. Both traps checked and cleared — SETTLED

**Method** (`pdf62_eig_conventions.py`): regress `ln r_model = s · ln r_template`
by least squares through the origin over the gen bins with
`|ln r_template| > 1e-4` and qT > 1 GeV (~200 of 210 per direction). A
normalisation mismatch is a CONSTANT s; a down-member sign flip is s = −1.

**Result over the 58 directions:** mean **0.999333**, min 0.990531, max
1.003886, **max|s − 1| = 9.47e-03**. A 90%-vs-68% CL mismatch would read 1.645
or 1/1.645 = 0.608; a sign flip would read −1. Both are **68x the observed
scatter away**. Figure `eig_convention.png`.

**The convention, stated on each side, which is the part that goes in the card
note:**
* **templates** — raw CT18ZNNLO Hessian members. `pdfvars_CorrZ` carries `pdf0`
  as its central and `pdf(2i+1)`/`pdf(2i+2)` as eigenvector i up/down: the
  LHAPDF members themselves, at CT18Z's native 90% CL, one member per column,
  no rescaling.
* **model** — `pdf_eig{i}` is the coefficient `c_e` of that same raw member
  pair, `c_e = +1 → pdf(2i+1)`, `c_e = −1 → pdf(2i+2)`, anchored at 0. 90% CL by
  inheritance. **There is no 1/1.645 anywhere in the model.**
* **per-pair, not per-member** — one parameter covers both members and s = 1 on
  BOTH signs, so it is not a half-step.

**Consequence:** `pdf{N}CT18ZSym{Avg,Diff}` and `pdfEig{N}` are the same units.
The D-R07 exclusion swap is one-for-one and needs **no factor on either side**.

**A result that came out of the same test and strengthens all of it.** CT18Z
Hessian pairs are NOT symmetric: `max|ln r_up + ln r_dn|` runs 4.2e-03 .. 4.0e-02
over the 29 pairs (median 1.0e-02). The model reproduces that asymmetry to a
ratio of 0.967 .. 1.082 (median 1.027). So the model is **not** a symmetrised
linear derivative in `c_e` — it carries both members — and V-004's closure is
therefore testing an asymmetric response, not a slope. The asymmetry (1e-02) is
an order of magnitude larger than the closure residual (2.4e-03), so the test
has real discriminating power.

**Overturned by:** a template file regenerated with a different member
normalisation, which the slope test would catch immediately.

### V-007 — Turning the eigenvectors ON perturbs NOTHING already signed off — SETTLED (with the floor stated)

Reference chosen: **`cache_260824b`** (210 bins, `n_eig = 0`, P = 24,
`target_precision_rel 1e-3`) read with the SAME nak build
(`tmp/val_after.log`). **Not** the published `cache_260825_p4` table, because
p4 runs 1e-4 and was read with a build lacking `92f1299` — two variables at
once. Against 260824b, the diff is `n_eig 0 → 29` and the build, and the
runcards are byte-identical apart from `target_precision_rel`. The p4 column is
carried alongside anyway.

**34 of the 37 non-null directions are identical to the printed 3 s.f.**
(ratio 1.000). The two `b_qqDS` directions are exactly 2.22e-16 on both — D-016
holds at P = 53. Only the three transition directions move, and they **improve**
(ratios 0.799, 0.786, 0.610). Figure `other39_vs_neig0.png`, Table 1.

**The floor, stated where the comparison sits on it.** Two independently built
caches of the same runcard agree to 3.1e-05 in sigma but only **3.0e-03 in the
Jacobian at a displaced point**. Everything in Table 1 except mufup, the two
kappaFO legs and the transitions sits BELOW that. The agreement is real but it
is not evidence at a precision finer than the floor, and the shading on
`other39_vs_neig0.png` says so on the figure.

### V-008 — The transition improvement is REAL but NOT ATTRIBUTED; here is the experiment — OPEN

Transitions: 3.13 → 2.50e-03, 2.85 → 2.24e-03, 1.12 → 6.83e-04 against
cache_260824b. **Plausible cause:** this is the first cache whose rules were
TRAINED with the fixed muF member coordinate as well as READ with it — 260824b
was trained pre-fix and only read post-fix (which is exactly what
`val_before` → `val_after` measured: only the transitions moved there too).
**Why I cannot claim it:** the shift is 4e-04 .. 6e-04, INSIDE the 3.0e-03
two-build Jacobian floor of V-007. Build noise and a real improvement are not
separable from this comparison.

**The experiment that would separate them:** read THIS cache with a build that
lacks `92f1299` — one cache, two readers, so the node set, the rules and the
member convolutions are bit-identical between arms and the only difference is
the muF member coordinate. That is the D-020/`set_muf_knots_used` clamp trick
applied to a different knob, and it is the only clean form of this A/B.
**Not run:** it needs a second SCETlib build snapshot and was outside the
delivery gate. Flagged rather than guessed.

### V-009 — No eigenvector direction is NULL, but the 29 are strongly COLLINEAR — SETTLED (and it is the finding to act on)

The model refuses an identically-zero Jacobian column, which is how
`tnp_b_qqDS` was caught (D-016). Checked at the anchor on all 53 columns:

* **exactly-zero columns: only `tnp_b_qqDS`.** No eigenvector is null. Column
  norms `‖∂sigma/∂c_e‖₂` run 0.0702 (e0) .. 0.767 (e18), ratio 9.1e-02; as a
  fraction of `sum(sigma) = 670`, 1.0e-04 .. 1.1e-03. So e0 is *weak*, not
  degenerate — and note it is exactly the direction whose FD check looked bad
  (V-002): the two facts are the same fact.
* **but the block is nearly rank-deficient.** Of the 406 pairs,
  **154 have |cos| > 0.8, 78 > 0.9, 37 > 0.95, 1 > 0.99** (worst: e5 vs e23 at
  **0.9964**). Condition number of the normalised 29-column block **2.72e+04**;
  only **8 of 29** singular values exceed 1% of the largest; the participation
  ratio is **2.76 effective shapes of 29**. Full 52-column Jacobian: cond
  9.2e+05.
* **how much is just normalisation.** Projecting out the pure-normalisation
  direction (sigma itself), the shape fraction `‖J⊥‖/‖J‖` is 0.223 (e25) ..
  0.993 (e7), median 0.553 — about half a typical eigenvector's leverage is a
  flat rescaling. The worst |cos| falls 0.9964 → 0.9833 and the >0.99 count goes
  to zero, but 28 pairs remain above 0.9 and the shape block still has cond
  1.34e+04.

**Physics read.** The 29 eigenvectors are orthogonal in CT18Z's parameter space,
not in the space of responses of a 210-bin (qT, |Y|) Z spectrum. On this
observable they collapse to ~3 well-determined shapes (8 counting every singular
value above 1%).

**Decision, and it is a fit-design decision, not a cache one.** The fit is not
singular — every column is nonzero and the unit Gaussian priors regularise the
rest — so **run it**. But:
1. individual postfit `pdfEig{N}` values will be prior-dominated and strongly
   anti-correlated and **must not be reported as measurements**;
2. the quotable outputs are the **total PDF impact on alphaS** and the few
   data-constrained combinations;
3. expect the minimiser to need more iterations than the P = 24 fit — this is
   the one cost V-010 could not measure.

**Overturned by:** a fit whose eigenvector block is better conditioned than this
predicts, e.g. because the reco response matrix R re-mixes the gen bins in a way
the gen-level Jacobian does not show. Worth checking at reco level.

### V-010 — Fit-readiness, MEASURED; three of the four prior extrapolations were pessimistic — SETTLED

Same node, same `--threads 64`, same library, one model at a time.

| quantity | p4 (P=24, n_eig=0) | pdf62 (P=53, n_eig=29) | factor |
|---|---|---|---|
| cache.npz on disk | 222 MB | 2289 MB | 10.3x |
| load | 23.1 s | 233.4 s | 10.1x |
| value+jacobian, first call | 283 ms | 1269 ms | 4.5x |
| **value+jacobian, WARM** | **155 ms** | **421 ms** | **2.72x** |
| **Hessian (210 × P × P)** | **12.58 s** | **68.86 s** | **5.47x** |
| **peak resident** | 5.42 GiB | **48.7 GiB** | 9.0x |
| sum(sigma) at the anchor | 670.01772 | 670.01137 | — |

**Corrections to the extrapolations the build was planned on (D-027):**
* "value+jacobian ~1.2 s" — right for the COLD call (1.27 s), **2.9x
  pessimistic** for the warm call, which is what a minimiser iteration pays.
* "Hessian ~4–5 min" — measured **68.9 s**, 3.5–4.4x pessimistic.
* "50–64 GB resident" — **48.7 GiB (52.3 GB)** peak, at the low end of the
  range. CORRECT, and still the binding constraint: it rules out a wide
  concurrent toy ensemble with eigenvectors.
* "cost scales with bins × retained nodes × P, NOT with member count" —
  **CONFIRMED**. 4 → 62 members is a 15x member increase; the warm
  value+jacobian grew 2.72x for a 2.21x growth in P, and the Hessian 5.47x
  against (53/24)² = 4.9. Both P-driven, neither member-driven.

**Affordability, said carefully.** A gen-level fit runs ~150 s in ~56 iterations
at ~2 s each at P = 24 — and the model's own warm value+jacobian there is only
**155 ms, ~8% of an iteration**. Turning the eigenvectors on adds 266 ms, so the
per-iteration cost grows by **~13% if rabbit's overhead is P-independent** and by
at most ~2x if that overhead scales with P as the model call does. The
covariance pass is one 69 s Hessian. **The unmeasured cost is the ITERATION
COUNT** — 29 extra, strongly collinear parameters (V-009) may need many more
steps. That is the experiment: run the fit. `--jitCompile off` remains mandatory
(the model calls SCETlib through `tf.py_function`).

### V-011 — D-004 / D-R07 are now OVERTURNED as they said they would be — SETTLED

D-R07's stated overturning condition was verbatim: "a cache built with
`--pdf-eig 29` whose eigenvector response is validated across the full grid
(currently ~1e-6 in one window only). At that point
`scetlib_dyturbo_..._pdfvars_Corr` joins the exclusion list and `pdfEig{0..28}`
float instead." **That condition is met** by V-001, V-004 and V-006: the cache
exists, registers 29 `pdf_eig*` parameters, and its eigenvector response is
validated on all 210 gen bins at ≤ 2.4e-03 in the same convention as the
templates.

**So the next card change is:** add `scetlib_dyturbo_.*pdfvars` to
`--excludeNuisances` (matching the SYSTEMATIC name, D-R02 / D-006 — the 58
`pdf{N}CT18ZSym*` nuisances cannot be targeted individually), and float
`pdfEig{0..28}`. **The 4 `pdfMSHT20m{b,c}range` nuisances stay** — the model has
no quark-mass parameter, that part of D-R03 is untouched.
**Not done here, on purpose:** making the card and running the fit are separate
tasks with their own gates, and the reco-level eigenvector closure has not been
measured at all (this is gen-level only). Recommended, not executed.
**Overturned by:** a reco-level eigenvector closure that is materially worse
than the gen-level one, which would put the GRAIN term (D-R11) in charge.
