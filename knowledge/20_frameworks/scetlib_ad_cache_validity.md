# Where a SCETlib-AD cache is accurate — and two ways it is not

Two defects found in `studies/alphas-scan-discontinuity/` (2026-09-23 .. 27), plus (section 3) a PDF-threshold discontinuity found in `studies/msht20-ad-campaign/` (2026-09-30). Neither one
shows at the anchor, and neither shows in a single-parameter probe:

1. The cache's integration points are placed at the anchor. It is therefore **wrong for
   `lambda2_nu < 0`**, i.e. an anti-damping Collins-Soper NP term, at gen qT ~2.5-6 GeV.
   Both production caches have this.
2. In the qT [0, 0.5] bin, the FO PDF eigenvector cross terms of a `2dd978a`-era build are
   made from unsubtracted V+jet below the 0.1 GeV nonsingular cut. This is a build-time
   bug (MR !16). The |Y| <= 3.5 cache had it, and a quick-patched copy exists.

Related: `scetlib_diff_scales_caveats.md` covers the *Jacobian* version of the same
"validate away from the anchor" lesson. `scetlib_cache_format_versions_and_pins.md` says
which build reads which cache.

---

## 1. The integration points are chosen at the anchor, so the cache is wrong for lambda2_nu < 0

**Mechanism.** `scetlib-cms/examples/matched_ad/prepare_cache.py::build_prologue` builds
the outer node set once, at the anchor: `sigma.prepare(bins, p0)`. It adapts the matched
integrand at `p0`, and every bin rule is then built on that frozen set. At any other
parameter point the cache replays the anchor's quadrature. So it is exact only where that
quadrature still resolves the integrand. The training points do not widen this much: rule
options `n_train=9, scale=0.15`, i.e. `p_i(1 + 0.15 d_i)` for a non-zero anchor and
`0.15 d_i` absolute for a zero one (read from the `rules.npy` header of the 260827 cache).

**Direct SCETlib has the same switch.** With `sing.set_gradient_node_cache(True)`, the
first call adapts the nodes and later calls reuse them. Make that first call at the anchor
and you reproduce the cache ("frozen" mode). With `set_gradient_node_cache(False)`, every
call re-adapts, which gives the truth. Comparing the two isolates node placement.

**Measured (old `pdf62_corrgrid_260827` and new `pdf62_y35_260921` caches).** The error is
`(cache - truth)/truth`. Only the NP lambdas are moved; everything else sits at the anchor.

| tune | gen qT 2.5-6 GeV | qT 0.5-1.5 GeV | elsewhere |
|---|---|---|---|
| walled, physical (`lambda2_nu` >= 0; CCWALLWARMPF) | <= 0.03 % | <= 0.03 % | <= 0.03 % |
| unwalled fit postfit (`lambda2_nu` ~ -0.09), old cache | -0.7 .. **-2.8 %** | -0.3 .. -0.7 % (compression, not placement) | <= 0.1 % by qT 10 |
| same, new |Y|<=3.5 cache | -0.3 .. **-3.6 %** (worst at 3-3.5 GeV, |Y| 2.75) | forward |Y| 2.75-3: +1.3 .. -1.0 % | <= 0.1 % by qT 10 |
| `lambda2_nu = -0.091` alone | **-12 .. -32 %** at 2.5-3.5 GeV | | |

- **The driver is `lambda2_nu < 0` and nothing else.** A scan with one lambda moved at a
  time found `lambda2`, `lambda4` (even all the way to 0), `delta_lambda2` and
  `lambda4_nu` exact to <= 0.01 %. `lambda2_nu` = 0.10, 0.05 and 0 were exact; at -0.05
  the error was -0.5 .. -2.1 %. In the full unwalled set the other lambdas partly offset it.
- **The result is converged.** At target precision 1e-4 the re-adapted answer equals the
  1e-3 one to <= 0.01 % (0.08 % in qT 0-0.5).
- **The nonsingular (FO) piece is NP-independent by construction.** Its registered
  parameters are only `alphas, scale_kappa_R, scale_kappa_F, pdf_eig*`. NP moves act on the
  resummed piece only, so you can compare **differences from the anchor**, which lets the
  lambda-independent nonsingular cancel.

**What this looked like.** In a ratio of gen sigma to the unwalled tune, 0.5 GeV bins at
gen qT < 4 GeV jumped by +48 %, -25 %, ... from bin to bin. That looked like a cache
artefact. **Below 2.5 GeV it is not one.** Direct SCETlib shows the same pattern, so it is
real model behaviour at those lambdas. The artefact lives at 2.5-6 GeV, is 1-3 %, and is
smooth enough to miss. Also: the jumps showed up in *every* curve only because the ratio's
denominator was the unwalled tune.

**Decision (Luca, 2026-09-27).** Unwalled / unphysical (`lambda2_nu < 0`) fits on these
caches are **not trusted**, and no cache fix is being pursued for now. The walled (physical)
results stand: the cache is exact where the wall keeps the fit. If you need a trusted fit
with `lambda2_nu < 0`, you need a cache whose node set was also adapted there, or a
fit-level impact study. Neither exists yet.

**Cost of the check.** For 42 bins, the one-off anchor adaptation took **3.3 h** on a node
at load ~470. After that, each re-adapted evaluation took 6-10 s, which makes a lambda scan
cheap. Loading the new cache cold from /scratch took 55 min.

Evidence: `studies/alphas-scan-discontinuity/260925-np-far-anchor-validity/`. The scripts
there are `direct_vs_cache.py` (frozen vs adaptive), `scan_driver.py` (one lambda at a
time), `newcache_check.py` and `plot_direct_vs_cache.py`. Outputs are in `out/*.npz` and
`logs_run/`.

---

## 2. qT [0, 0.5]: the FO PDF cross terms ignored the nonsingular cut

**Mechanism** (scetlib-cms at `2dd978a`, `py/qT/DrellYanAD.cpp`). A cross term is built as
`B_ef = 1/2 [S(f0+d_e+d_f) - S(f0+d_e) - S(f0+d_f) + S(f0)]`. Each `S` is the sum of two
halves, and different code computes each half:

- the **V+jet half**, all combinations in one traversal: `_fo_bilin_vjet_all`;
- the **singular half**, through the ordinary per-node evaluator.

The matched calculation sets `set_nons_qt_cut(0.1)`, so the nonsingular vanishes below
qT = 0.1 GeV. The per-node evaluator honours that cut (`_nons_is_zero(qT)`).
`_fo_bilin_vjet_all` did not. Below 0.1 GeV it added the raw, log-divergent V+jet to
combinations whose singular half was zero. Only the production bin qT [0, 0.5] has nodes
below the cut, since the cut is also a split point.

**What it looked like.** A warm fit seeded at the old minimum started at loss **1989.95**
instead of **365.49**. A swap test (new rabbit with the old cache gave the old loss exactly)
ruled out rabbit.

- The whole gap sat in one gen bin, qT [0, 0.5] at every |Y|, and reached the fit through
  reco ptll < 2 GeV.
- **Any single eigenvector displaced alone was exact.** Displacing all 29 scaled as t^2 and
  drove sigma **negative** (-176 % at |Y| < 0.15).
- The kappa_F slope in that bin was absurd (-20 .. +89 against ~0.01).

The diagonal and linear terms come from member rows that go through the guarded evaluator,
which is why a one-at-a-time check passes. And the central correction still matched to 2e-5,
because B_00 is not taken from the form.
Evidence: `studies/alphas-scan-discontinuity/260923-oldmin-loss-gap/` and `260924-bilin-nons-cut/`.

**Fix.** `if (_nons_is_zero(node.qT)) return;` in the `_fo_bilin_vjet_all` node loop. It
is commit `1da6b2e` on branch `fix-bilin-vjet-nons-cut`, **scetlib-cms MR !16**, which was
**open** as of 2026-09-24. A patched 4-bin test cache agrees with the old build to
5e-06 .. 2e-05 in the cut bin (unpatched: -176 %). With the artefact removed, bin 0's
genuine cross terms match bin 1's to 1 % (4.90e-4 vs 4.85e-4 of sigma), which is the smooth
behaviour a real PDF-bilinear term must have. The next full rebuild with MR !16 replaces the
quick patch below.

**The quick-patched production cache** is
`pdf62_y35_260921/merged_full_bin0xzero`. It is on ceph, with an md5-identical /scratch
mirror that also carries an extracted `cache.rules.bin`. In it:

- In the 15 qT [0, 0.5] bins, every off-diagonal `d1 != d2 >= 1` entry of the FO quadratic
  form is zeroed: eigenvectors **and** the alphaS direction, in all 3 muF slots. So are the
  kappa_F-shift slots of the diagonal. Everything else is byte-identical to `merged_full`.
- It was made by byte surgery (`260924-bilin-nons-cut/scripts/zero_bin0_crossterms.py` and
  `assemble_cache.sh`).
- **Cost:** it drops the genuine cross terms in that bin, +2.7e-4 .. +4.9e-4 of sigma at the
  seed's eigenvector displacement, growing as c^2.
- **Validation:** the seed loss is 365.677, against 365.488 on the 260827 cache.

**Do not use the unpatched `pdf62_y35_260921/merged_full` for fits.**

**Regression check this family needs:** displace **two** eigenvectors, in the bin that
contains the cut. A one-at-a-time check cannot see an off-diagonal term.

**Still unexplained (small; do not over-read agreement below these levels):**

- In qT [0, 0.5], the patched build and the old `b66f8de` build differ by an offset that
  does not depend on the eigenvectors: 1e-3 .. 5e-3 in size, with a sign that changes
  with |Y|. It is present with every `c = 0`.
- ~2e-2 .. 2.6e-2 differences at |Y| 2-2.5, qT < 1.5 GeV with the eigenvectors at zero
  (`260923-oldmin-loss-gap`, compare_anchor table). Not chased.
- Two builds of the same runcard with different node counts differ in the nominal of a
  bin: a subset test build trained at a median of 201 nodes/bin vs 378 in production gave
  +1.2e-3 in qT [0.5, 1]. This is the non-reproducibility described in
  `scetlib_ad_cache_build_parallelism.md`. **So when patching a production cache, splice
  only the block you are fixing. Never swap whole bins in from a separately built cache.**

## 3. A PDF that jumps at mb makes the likelihood a staircase in anything that moves muF

Added 2026-09-30 from `studies/msht20-ad-campaign/260930-edm-cache-derivs/` (physics-reviewed).
This is not a cache bug: the value, the gradient and the Hessian are all correct inside each
smooth piece. The loss itself is discontinuous.

- **What happens.** The AD kernel evaluates each resummed node's beam convolutions at the
  node's live muF, through one polynomial per interval between the PDF's own Q knots
  (`ad_kernel.hpp`, "conv(muF) is smooth only BETWEEN the PDF's own Q knots").
  `MSHT20nnlo_as118` is a VFNS grid with a true step at mb = 4.75 GeV: gluon +1.2 % / +0.36 %
  at x = 1e-3 / 1e-2, light quarks ~1e-4, independent of the probe width. `CT18ZNNLO` is
  continuous there. SCETlib runs at fixed nf = 5 (cache.conf `[QCD]`), so nothing
  compensates the jump. A consistent VFNS would compensate it by switching nf in alpha_s and
  in the matching coefficients.
- **Which parameters see it.** Only parameters that move the resummed muF: the transition
  points (`resumTransition2` among the fitted ones), and kappa_F if it is floated. Not
  kappa_R, which works at fixed muF. Not the lambdas, TNPs, alphaS or pdfEig. The FO muF is
  `_muFO(Q)`, which does not depend on the transition points.
- **mc is never crossed.** With `muf_follows_muB = no`, muf = Q[g muf_0/Q + (1-g)] with
  muf_0 >= muf_min = 1.40 = mc. The lowest muf, 1.4g + (1-g)Q, drops below 4.75 only for
  (x-x1)^2 < 0.32 x 3.35/(Q-1.4). That is gen qT ~18-28 GeV at Q = 91, and ~12-35 GeV over
  Q in [60, 120]. The steps are largest at the upper edge, and the observed window is
  17-37 GeV, peaking at 24-30 GeV.
- **What it does to a fit.** The loss along `resumTransition2` is a sawtooth, with steps
  up to 6.5e-3 NLL per 0.001 sigma. trust-krylov stalls with status 2 and a finite EDM
  (MSWALLCOLD: 1.2e-3; CT18Z twin 2.8e-17). **EDM is not a usable convergence certificate
  for an MSHT20 fit that floats a transition point.** Freeze it at its postfit value to
  certify one.
- **Freezing the transition point fixes it** (2026-09-30): warm refits with `--freezeParameters resumTransition2` at the
  postfit value reach EDM 6e-11 (lattice arm) and 6e-17 (base arm). Do this to certify any MSHT20 minimum.
- **The stall CAN move alpha_s.** On the lattice arm the stalled stop (EDM 0.14) was 0.098 in NLL above the certified
  minimum and alpha_s moved by +0.075 sigma. On the base arm (EDM 1.2e-3) the gain was 1e-3 and alpha_s is safe. So
  a stalled MSHT20 result is not quotable until refit with the transition point frozen.
- **What the staircase itself does NOT do.** It does not move the exact minimum's alpha_s. The step positions depend only on the
  transition point, so the staircase cancels in the alpha_s profile. Two same-basin fits
  from different starts differ by -0.0043 sigma(alpha_s). rho(alphaS, resumTransition2) =
  0.008, but rho alone does not bound a discontinuity.
- **It is in plain SCETlib too; the AD cache inherits it** (2026-09-30, physics-reviewed; evidence:
  `studies/msht20-ad-campaign/260930-mb-jump-direct/`).
  - SCETlib's b_T integral is an Ooura-Mori double-exponential oscillatory rule. Its nodes lie on an
    integrand-independent lattice in qT·bT (tail nodes near kπ/2), and it converges after one mesh
    halving, by its own test, below its iteration cap. So the nodes do not follow the b*(x2) where
    muF = mb, and each node crossing is a step in plain `operator()` output.
  - At (mZ, 0, 28.5 GeV): 14 steps for x2 in [0.6, 0.8], up to 7e-4, each matched to a predicted
    node crossing. The step size is independent of `target_precision_rel`. The AD point replay with
    frozen nodes matches plain to 5e-10.
  - Same pin and runcard with only the PDF changed to CT18ZNNLO: smooth.
  - NOT `max_iterations = 2`: that is the class default, and raising it would only halve the steps.
  - The exact b_T integral is continuous in x2 (single jump at b*, bounded integrand). This is
    analytic, not tested at b_T level; bin-level output converging toward continuity as the outer
    precision tightens is indirect support. So: **the prediction as computed is discontinuous; the
    exact integral is not.**
  - **Point mode misses its requested precision near a crossing:** step 5.7e-4 vs a b_T target of
    1e-4..1e-8 (precision_buffer_bT = 0.1). The DE error estimate does not flag an interior jump,
    and point `operator()` discards the error (DrellYan.cpp:595/799/843). Bin mode stays within its
    Cuhre error.
  - The production cache replays with conv-refill OFF. In a bin (473) it shows one 2.9e-4 step
    where plain SCETlib shows many small ones; that mechanism is untested.
  - The AD path with the node cache OFF is wrong for x2 moves: 2e-5 at x2 = 0.61 up to 2.4e-3 at
    0.75, for both PDFs. For NP-λ moves it was fine (inherited from 260925-np-far-anchor-validity).
    Keep the node cache on for scale/profile scans.
- **Caveats.** The CT18Z control differs from MSHT20 only in the PDF (same pin and runcard). The
  cache's single-riser concentration in a bin is unexplained. The worse-EDM lattice stops (0.07-0.14),
  first suspected to involve a separate pdfEig13/pdfEig3 valley, converge cleanly once the transition
  point is frozen. So the staircase alone explains them.
- **Possible fixes, none done yet:**
  1. Split the b_T integral at b*, where muF = mb. This fixes point and bin output, and fits the
     DE rule's lower limit.
  2. nf-consistent threshold treatment, or an nf = 5-continuous PDF.
  3. Smooth the beam-function/PDF interpolation in μ across mb (conv(muF) in the AD kernel). This
     is a numerical patch.
