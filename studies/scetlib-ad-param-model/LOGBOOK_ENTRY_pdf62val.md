# 2026-08-26 — the 62-member PDF eigenvector cache is VALIDATED and DELIVERED

Staged for folding into `LOGBOOK.md`. Agent: pdf62 validation. Decisions in
`DECISIONS_pdf62val.md` (V-001 .. V-011). Webdir with every figure, table and
raw log: `~/public_html/alphaS/260826_scetlib_ad_pdf62_validation/`.

## What was validated

`/ceph/.../scetlib_ad_caches/pdf62_260826/merged_full/` — 2288.8 MB, 210 gen
bins (21 ptVGen [0,100] × 10 absYVGen [0,2.5], Q [60,120]) × 62 members
(29 CT18Z eigenvector pairs + the alphaS pair + the muF pair), n_train 9,
`target_precision_rel 1e-3`, merged from the 21 ptVGen shards. 53 model
parameters. Built overnight; nothing downstream had ever been checked against it.

Everything below is on the SCETlib snapshot
`tmp/pdf62/scetlib_snapshot`, md5(libscet-qT.so)
`0c5dd7a92fea9e2ad0cb81639e9689a2` — `near-anchor-knots` `eb60a04`, the only
tree carrying both `92f1299` (muF member coordinate, MR !8) and `3a8db11` /
`_rule_is_matched` (the non-singular double count, without which every Hessian
moves by 152%).

## The five answers

**1. The gate passes.** Anchor re-evaluation bit-identical; Hessian symmetry
exactly 0.00e+00 at (210, 53, 53); fold sum rule exactly 0.00e+00; FD vs
analytic worst 8.14e-07 over nine parameters including three eigenvectors.
`sum(sigma) = 670.01137`, which is 1.9e-07 from the number D-025 recorded when
it validated `1e-3` against a direct SCETlib run — so the tolerance decision is
reconfirmed on the production artefact, not inherited. The expected spurious
`pdf_eig0` failure **did not happen**: it was a 4-bin artefact, because the
summed derivative there was 3.4e-04 against −0.699 here, 2000x smaller against
the same round-off floor. A step-size scan shows the textbook V with truncation
rising exactly as h² — a wrong gradient would be flat. (V-001, V-002)

**2. The eigenvectors reproduce the templates in the accepted class.** All 58
members, all 210 gen bins: 4.02e-04 .. 2.43e-03, median 9.03e-04; qT > 1 GeV,
2.05e-05 .. 8.23e-04. On the same cache the 39 signed-off directions run to
1.40e-02 with median 7.14e-04 — **8 of them are worse than the worst of the 58**.
Relative to each direction's own response amplitude (the D-R14 metric) the two
sets are indistinguishable: median 0.058 vs 0.037. The residual is monotonically
low-qT: above qT 16 GeV all 58 close to ≤ 1.67e-05, while the three transitions
still sit at 2.50e-03. So the eigenvectors carry none of the transitions'
high-qT problem. (V-004)

**The earlier ~1e-6 is confirmed in its window and refuted as a grid number.**
The source is `tmp/val_eig29_nt9.log`, a 4-bin cache on |Y| < 0.3, qT [20,28],
where the 58 members read 1.9e-08 .. 1.5e-06. This cache reproduces that in the
same window: the worst member here, pdf38, reads 5.5e-06 at [20,24] and 2.3e-06
at [24,28]. The full-grid number is ~1000x larger, and the six
lambda2/lambda4/lambda2_nu directions move by exactly the same factor between
the same two windows (1.50e-07 .. 6.53e-07 → 1.33e-03 .. 4.87e-03), so this is
not an eigenvector-specific degradation. Lesson recorded: no accuracy claim for
this model without its (|Y|, qT) domain. (V-005)

**3. Nothing already signed off moved.** Against `cache_260824b` (n_eig = 0,
same 1e-3 tolerance, read with the same nak build — chosen over the published p4
table, which is 1e-4 AND a different evaluation kernel), **34 of the 37
non-null directions are identical to 3 s.f.** `tnp_b_qqDS` is still exactly
2.22e-16 on both sides, so D-016 holds at P = 53. Only the three transitions
move, and they improve 20–39%. **Stated with its floor:** two independently
built caches agree to 3.1e-05 in sigma but only 3.0e-03 in the Jacobian, and
everything in that table except mufup, the kappaFO legs and the transitions sits
below 3.0e-03. The agreement is real; it is not evidence finer than the floor.
(V-007)

**4. The fit is affordable, and three of four prior extrapolations were
pessimistic.** Measured on the real cache against the P = 24 production cache in
matched conditions: warm value+jacobian 421 ms (not ~1.2 s — that was the cold
call), Hessian 68.9 s (not 4–5 min), peak resident 48.7 GiB (in the 50–64 GB
range, at the low end). Member count is confirmed free: 4 → 62 members is 15x,
and the cost moved 2.72x for a 2.21x growth in P. In a fit, the model is ~8% of
a P = 24 iteration (155 ms of ~2 s), so the eigenvectors add ~266 ms — ~13% per
iteration if rabbit's overhead is P-independent, at most ~2x if it scales like
the model call. The **unmeasured** cost is the iteration count. (V-010)

**5. No eigenvector is degenerate, but the block nearly is — and this is the
finding to act on.** No `pdf_eig*` column is zero (only `tnp_b_qqDS` is).
But of the 406 eigenvector pairs, 154 have |cos| > 0.8, 78 > 0.9, 37 > 0.95 and
one > 0.99 (e5 vs e23, 0.9964); the normalised 29-column block has condition
2.7e+04, only 8 singular values above 1% of the largest, and a participation
ratio of **2.76 effective shapes out of 29**. About half of a typical
eigenvector's leverage is a pure normalisation shift (shape fraction median
0.553); projecting it out drops the worst |cos| to 0.9833 and clears the >0.99
count, but 28 pairs stay above 0.9. (V-009)

## Physics read

The 29 CT18Z Hessian eigenvectors are orthogonal in PDF parameter space, not in
the space of responses of a 210-bin (qT, |Y|) Z spectrum. Projected onto this
observable they collapse to about three well-determined shapes. That is a
statement about the observable, not about the cache: a Z qT spectrum at fixed
normalisation simply cannot resolve 29 independent parton-density directions.

The consequences are concrete. The fit is well-posed — every column is nonzero
and the unit Gaussian priors supply the missing curvature — so it should be run.
But individual postfit `pdfEig{N}` values will be prior-dominated and strongly
anti-correlated, and must not be reported as measurements; the quotable outputs
are the total PDF impact on alphaS and the handful of data-constrained
combinations. And the minimiser should be expected to take more steps than the
P = 24 fit does, which is exactly the cost this study could not measure.

Two smaller physics points worth keeping. First, CT18Z's Hessian pairs are
genuinely asymmetric — `max|ln r_up + ln r_dn|` reaches 4.0e-02 — and the model
reproduces that asymmetry to 3–8%. So the continuous treatment is not a
symmetrised linear derivative; it carries both members, and the closure test has
real discriminating power because the asymmetry it must reproduce (1e-02) is an
order of magnitude larger than the residual (2.4e-03). Second, `pdf_eig0` is the
weakest direction in the set (column norm 0.070 against 0.767 for e18, 1.0e-04
of `sum(sigma)`) — which is the same fact as its FD check looking bad on a thin
cache, seen from the other side.

## Both convention traps, closed

CT18Z is a Hessian set at 90% CL, so a normalisation or sign mismatch between
the templates' raw members and the model's `pdf_eigN` would have shown as a
clean constant factor. Tested by regressing `ln r_model = s · ln r_template`
through the origin over ~200 gen bins per direction: **s = 0.999333 mean over the
58, max|s − 1| = 9.47e-03**. The signatures of the traps — 1.645, 1/1.645 =
0.608, and −1 for a down-member sign flip — are all 68x the observed scatter
away.

Stated on each side: the templates carry the raw CT18ZNNLO LHAPDF members
(`pdf0` central, `pdf(2i+1)`/`pdf(2i+2)` up/down) at CT18Z's native 90% CL with
no rescaling; the model's `pdf_eig{i}` is the coefficient of that same raw pair,
`+1 → pdf(2i+1)`, `−1 → pdf(2i+2)`, anchored at 0, 90% CL by inheritance, one
parameter per pair with s = 1 on both signs. **There is no 1/1.645 anywhere.**
The practical consequence: `pdf{N}CT18ZSym{Avg,Diff}` and `pdfEig{N}` are the
same units, so the datacard swap is one-for-one and needs no factor. (V-006)

## What this unblocks, and what it does not

D-004 / D-R07 stated their own overturning condition — "a cache built with
`--pdf-eig 29` whose eigenvector response is validated across the full grid" —
and that condition is now met. So the next card change is to add
`scetlib_dyturbo_.*pdfvars` to `--excludeNuisances` (against the SYSTEMATIC
name, D-R02: the 58 `pdf{N}CT18ZSym*` nuisances cannot be targeted individually)
and float `pdfEig{0..28}`. The 4 `pdfMSHT20m{b,c}range` nuisances stay — the
model still has no quark-mass parameter.

**Not done, deliberately:** the card was not remade and no fit was run; those
are separate tasks with their own gates. And **this is gen-level only** — the
reco-level eigenvector closure has not been measured at all, and D-R11 says the
GRAIN term (bin-averaged response against per-event reweighting) exceeds CALC in
32 of 39 directions there. Gen-level validation is necessary, not sufficient.

## The one thing I could not separate

The three transition directions improve 20–39% against `cache_260824b`. The
plausible cause is that this is the first cache whose rules were **trained** with
the fixed muF member coordinate as well as **read** with it. But the shift is
4e-04 .. 6e-04, inside the 3.0e-03 two-build Jacobian reproducibility floor, so
build noise and a real improvement are not separable from this comparison. The
experiment that would separate them: read THIS cache with a build lacking
`92f1299` — one cache, two readers, node set and rules bit-identical between
arms, the D-020 clamp trick applied to a different knob. Not run; it needs a
second build snapshot and sat outside the delivery gate. (V-008)

## Tooling added

New, under `studies/scetlib-ad-param-model/`:
* `pdf62_eig_conventions.py` — the convention slope test, the degeneracy /
  collinearity analysis, and the FD step-size scan, all off ONE model load, and
  it dumps every response to an `.npz` so the tables and plots are remade
  without paying 233 s and 49 GiB again. Reuses `validate_variations`'s corr
  readers by import rather than reimplementing them.
* `pdf62_merge_ab.py` — the parent-vs-merged A/B, one cache per process, several
  bin selections per process, with the memoisation trap written into the
  docstring. Re-run this on any future merge.
* `pdf62_summary_plots.py` — the four summary figures, offline from the `.npz`.

`validate_variations.py` and `backend_check.py` were used unmodified; no
parallel comparison was written.

## START HERE (for this workstream only)

* **State:** the 62-member cache PASSES and is delivered. Gen-level eigenvector
  response validated on all 210 bins at ≤ 2.4e-03, same convention as the
  templates, 39 other directions unperturbed, fit cost measured and affordable.
* **Next step:** either (a) remake the reco card with `pdfvars` excluded and
  `pdfEig{0..28}` floating and run the first 53-parameter fit — the per-step
  budget says try it — or (b) measure the reco-level eigenvector closure first,
  since gen-level says nothing about GRAIN.
* **Carry into either:** V-009. Do not report per-eigenvector postfit values;
  report the total PDF impact. Expect extra minimiser iterations.
* **Blocking:** nothing.
