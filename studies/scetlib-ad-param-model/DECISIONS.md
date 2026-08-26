# scetlib_ad — decision record

One line per decision, newest block first. Every entry says WHAT was decided,
WHY, WHAT EVIDENCE backed it, and WHAT WOULD OVERTURN it. This exists so a
review can check the reasoning, not just the outcome. Narrative lives in
`LOGBOOK.md`; this file is only decisions.

Status key: **SETTLED** (evidence in hand) / **PROVISIONAL** (acting on it, could
flip) / **OPEN** (needs Luca) / **SUPERSEDED** (kept for the audit trail).

---

## 2026-08-25 overnight session (autonomous, ~21:30 -> 08:00)

### D-019 — DO NOT merge five knots to fix the transitions — SETTLED (measured)
**Why:** it makes the transition closure against CorrZ WORSE, and the mechanism
is now measured rather than argued. At the FINITE variation the templates carry,
the per-node muF displacement D reaches **1.15 x ln f** (and 1.74 x ln f for the
x1,x3 leg) -- i.e. OUTSIDE kappa_F = 2. The model is EXTRAPOLATING there, and a
quartic extrapolates worse than a quadratic. More interior knots refine the
interior; the template legs are not in it.
**Evidence:** 80-bin closure, one cache read two ways so node set, rules and
members are bit-identical between arms.
  x2=0.35   2.85e-03 -> 5.37e-03
  x2=0.75   1.12e-03 -> 1.56e-03
  x1,x3     4.22e-03 -> **7.60e-01**
36 of 39 directions are BIT-IDENTICAL, so nothing else degrades.
**Overturned by:** a stencil wide enough to contain D at the template legs -- but
see D-020, the one wide geometry tried is not validated.

### D-020 — RETRACTION: the wide (kappa_F 1/4..4) geometry is NOT a measurement — SETTLED
It was first written up as "measured bad" at 31% of sigma. It fails its own knot
test (kappa_F = 4 must be exact; returns -3.7e+08). Kept behind `muf_nmem = -4`,
labelled UNVALIDATED. Chasing it did find a real bug -- the degeneracy guard was
absolute rather than relative to the node's spread -- and fixing that left the
no-op check and the narrow closure bit-identical, so the narrow numbers stand.

### D-021 — The five-knot work is still valuable, just not for the transitions — SETTLED
At kappa_F = sqrt2, against an exact runcard refill: **2.94e-03 -> 3.60e-05 of
sigma, 82x**. That doubles as the construction check AND reveals that the SHIPPED
model is **0.3% of sigma wrong at half a knot step** -- invisible to every
existing validation, all of which sit AT kappa_F = 0.5/2. Near-anchor derivative
(x2 = 0.55, what a fit uses) improves 2.9x / 33x / 6x in three bins; [24,28] does
not move, an order-independent floor already known to be spacing-independent and
bracketed by node_cval's measured bound.
Branch `muf-five-knots` (`61123f2`) pushed, **no MR opened**.

### D-022 — Next route for the transitions: the analytic d(conv)/d(ln muF) column — PROVISIONAL
**Why it is now better motivated than before:** it is first-order exact in D, so
unlike knots it does not care that D leaves the stencil at exactly the template's
variation size. One column per node instead of two member builds per bin; no
member staging, no re-solved weights.
**Open question it must answer:** whether ONE column suffices where D ~ 1.15 ln f.

### D-023 — Two traps to keep — SETTLED
1. `ScetlibCachedXsecTF.values_and_jacobian` memoises on the parameter vector
   ALONE. A first closure run returned ratio exactly 1.00 for all 39 directions
   -- a perfect and WRONG null. Any A/B between two builds must prove the arms
   are separated before reporting agreement.
2. Any global the kernel reads must NOT be `thread_local`: `_stage_var_meta`
   runs inside the TBB workers.

### D-024 — `--n-train 9` (the default). The worry was BACKWARDS — SETTLED
**Why:** the rule solve's unknowns are retained SITE weights, not parameters.
`blk = 1 + P + n_hvp*P`, `nrow = 1 + n_train*blk` -- every parameter adds TWO
ROWS per training point and almost no unknowns. So `n_train/n_params = 0.17`
compares two quantities on opposite sides of the equation.
**Evidence:** constraints per unknown, parsed per bin on the real 210-bin card:
production `cache_260825_p4` (n_train 9, P 24) = **1.51** rows/site, worst bin
1.09; the full card with 29 eigenvector pairs (n_train 9, P 53) = **3.48**.
Turning the eigenvectors ON makes the solve **2.3x better conditioned than every
cache the analysis has used to date**, and keeps FEWER sites (277 vs 292).
Against the templates, accuracy is flat from 9 up and alpha_s is identical
(1.88e-05) at n_train 5, 9, 14, 27. In sigma(alpha_s) units the n_train 9
residual is **1e-5 sigma** where the fit sits.
**Do NOT raise it:** 9 -> 27 doubles the retained nodes, hence the cache
(13 -> 28 GB), the fit's RAM, every iteration and the covariance pass.
**Caveat, stated:** no 210-bin cache was built at two n_train values (that is the
full build, twice). The bridge is that a bin's rule is self-contained -- which is
why bins from separate processes merge byte-exactly -- plus coverage of the
card's site range. Argument plus coverage, not a direct 210-bin scan.

### D-025 — Build the PDF cache at `target_precision_rel = 1e-3`, NOT 1e-4 — SETTLED
**Why:** it is a 13x lever that nobody had costed, and 1e-4 is not an option.
**Evidence:** production `cache_260825_p4` runs 1e-4 with `abs 0`; its 4-member
fixed-order stage took **715.6 min against 54.8** at 1e-3, and its node set
325.3 min against 21.9. For 62 members that is **~8.7 h at 1e-3 against ~114 h
at 1e-4**. The cost of 1e-3 is x25 on NP lambda and x28 on TNP residuals --
leaving them at 1.5e-05, still far below the muF residual -- and only **x1.08 on
alpha_s**, the parameter we actually quote.
**Note:** this makes the PDF cache a different tolerance from the reco-closure
cache. 1e-3 was already validated independently (cache total 670.0115 against a
direct 670.018).
**Overturned by:** evidence that the x25 on the NP lambdas matters somewhere it
currently does not.

### D-026 — Split the build by BINS so partial progress is usable — SETTLED
**Why:** there is a hard deadline (08:00) and an ~8.7 h job. Bin groups merge
EXACTLY (0.000e+00 in value and Jacobian), so whatever finishes is a usable
cache on a partial grid; a single monolithic build that is 80% done at 08:00 is
worth nothing. Members must never be split (D-013).
**Cost note:** bins are wildly unequal (2.3 min vs ~25 min for the same
members), so groups must be balanced by COST, not by count.

### D-027 — The Hessian "3.2x for two parameters" scaling worry is REFUTED — SETTLED
**Why it looked real:** the 8.1 s -> 25.4 s pair came from two SEPARATE
`backend_check` runs on a node at load 250-570.
**Measured properly**, interleaved in ONE process: P 24 -> 26 is **x1.09**,
P 24 -> 53 is **x2.95**. Not a scaling law. Projected to 210 bins at P = 53:
value+jacobian ~1.2 s, Hessian ~4-5 min (two independent extrapolations; the
P=24 bin-extrapolation reproduces the measured 89.8 s to 3%).
**Cost scales with bins x retained nodes x P, NOT with member count** -- 4 -> 62
members at fixed nodes is free.
**The real binding constraint is MEMORY: 50-64 GB per loaded model**, which rules
out a wide concurrent toy ensemble with eigenvectors.

### D-028 — CORRECTION: too small an n_train degrades SILENTLY — SETTLED
An inherited claim that "n_train 5 would make the build ABORT" is false. The
guard is a residual check; a thin-bin cache at n_train 5 wrote itself at
7.1e-09 residual while being 9.3x worse in the NP lambdas. Nothing warns.

### D-029 — `py/scetlib_tf.py` committed in the shared checkout — SETTLED
It sat UNCOMMITTED while matching `origin/autodiff-sigmaul` (where MR !7 is
merged). Any checkout or stash in that tree would have silently reverted it, and
without it **every Hessian changes by 152%**. Committed as `cc4ece2`.

### D-030 — Cap the TF thread pools for cache builds — SETTLED (measured)
**Why:** the "~1800 OS threads per build process whatever `--threads` says" is an
ARTEFACT, not a property of the build. `prepare_cache_for_card.py` never uses
TensorFlow; TF arrives transitively through `wremnants` and grabs one
`tf_Compute` thread per core.
**Evidence:** in-container, one `env -u` apart -- 1665 threads uncapped
(768 tf_Compute + 895 python3) against **135** with
`TF_NUM_INTRAOP_THREADS=4, TF_NUM_INTEROP_THREADS=2`. On the real 21-shard build,
groups launched before the fix sit at 1808/2432/2429 threads and groups launched
after at **262-902** for the same work at the same `--threads 128`.
**Consequence:** the practical concurrency ceiling is not ~15 build processes but
several times that. The 32768-threads-per-user limit fails SILENTLY and is
MISATTRIBUTED -- `pthread_create has failed`, exit 134, landing on whichever
process next asks for a thread rather than the one that exhausted the pool.
**Do NOT apply to rabbit fits** -- those genuinely use TF.

### D-031 — The build library is `build-nak` (eb60a04), and why — SETTLED
It is the ONLY tree carrying BOTH `92f1299` (the muF member-coordinate fix the
build requires) and `3a8db11` / `_rule_is_matched` (the non-singular
double-count fix). `build-fix` has the second but not the first; `build-trans`
has the first but its `py/` has zero occurrences of the second. Snapshotted so a
concurrent rebuild cannot move the results:
`tmp/pdf62/scetlib_snapshot`, md5(libscet-qT.so) 0c5dd7a92fea9e2ad0cb81639e9689a2.

### D-032 — Shards are queued in ASCENDING ptV order — SETTLED
So that whatever completes is a CONTIGUOUS run and never a hole. `GenFold`
refuses a merged cache that does not exactly tile its gen bins, so a hole is
fatal while a short contiguous run is a valid rectangle. The scheduler is
thread-aware (re-reads a budget every 30 s, refuses to launch above it) and
retries any group without a `done` marker, so a repeat of the qt4 abort cannot
silently leave a gap.

### D-033 — The bin-split build WORKS, proven bit-exact with the null excluded — SETTLED
Two INDEPENDENTLY built shards (qt2 + qt5, each carrying the full 62-member list)
merged to 20 bins x 62 members, 180.4 MB. Evaluated in THREE SEPARATE PROCESSES:
merged vs each parent gives **0.000e+00** on anchor value, anchor Jacobian,
displaced value and displaced Jacobian.
**And the arms are provably separated**, which is the point -- the
`values_and_jacobian` memoisation trap makes "a perfect and wrong null" look
exactly like success. Three arms returned three DIFFERENT sums satisfying the
additive rule: merged 63.6503485923, qt2 28.725160, qt5 34.925188, parts-vs-whole
7.1e-15. A memoised collision would have returned the same number three times.

### D-034 — An eigenvector member is the CHEAP kind; the ~14 h estimate over-counted — SETTLED
Same card, same runcard, same threads, launched together, four members each:
`m210_eig` (2 eigenvector pairs) 46.9 min fixed-order against `m210_asmuf`
(alphaS pair + muF pair) 96.9 min. Ratio **2.07** -> an eigenvector member is
~11.7 min at 210 bins and a muF member ~36.8 min. The 13.7 min/member average
came from a 4-member build that was ONLY the two expensive kinds. A 62-member
build is 58 cheap members plus two expensive pairs, so the true monolithic total
is **7.3-12.9 h**, not ~14 h.
*Caveat:* the two fixed-order stages did not overlap in time, so 2.07 is an
UPPER bound on the ratio.

### D-036 — CORRECTION to D-035's premise: the qt0 split is INSURANCE, not speed — SETTLED
My direction rested on "qt0 is under-utilised at ~43 of 128 cores, so ten bins
cannot feed the thread pool." **Measured, that is wrong.** The limit is per BIN,
not per pool: qt0 runs at 3.41 cores/bin in its node-set stage and each |Y|
sub-shard at 2.75-4.23 cores/bin -- the same rate. Five sub-shards sum to the
same ~34 cores, having started 34 minutes later, so the split **cannot overtake
the parent**.
**Kept running anyway, for a smaller and different reason:** qt0 is the single
point of failure for the whole partition (GenFold refuses a hole) and is one of
three processes launched BEFORE the TF thread cap, so it still holds 1808 threads
and is the most exposed to another `pthread_create` abort. The hedge costs ~20
cores on a node with headroom.
**Generalises:** do not expect a bin split to accelerate a build whose cost is in
the NODE-SET stage; that stage scales with bins, not threads. Split bins for
partial-result safety and for the MEMBER loop. Written into the knowledge note.

### D-035 — qt0 split FIVE ways by |Y|, hedged rather than switched — SETTLED
Two is only a 2x hedge on the bin that sets the wall time; ten multiplies a fixed
per-process cost by ten on the most expensive bin of the card. Five keeps two
bins per sub-shard to parallelise over and -- the deciding reason -- **can be
launched in waves as the thread budget allows**, which a fixed 3-way split
cannot, since the |Y| partition must be chosen before the first sub-shard starts.
The original qt0 is left running: its node-set work is not checkpointed, so
killing it would throw away 27 min for certain in exchange for an expected but
unmeasured speedup.

### D-037 — Response matrix gets the CORRECTION's gen grid; unfolding untouched — SETTLED (Luca)
`--responseGenBinning theoryCorr`, default OFF, two EXTRA hists beside the
untouched unfolding pair. Proof: `-j 1`, **464 histograms bit-identical, exactly
2 new**; and the response hist coarsened onto the unfolding grid equals the
unfolding hist summed over `helicitySig` to 2.8e-14. Grid read from the corr
file: Q already exact (the gen acceptance IS its single Q cell), |Y| truncated at
2.5 = its 11 bins, qT full range so gen qT>44 (11.65% of N_gen) is resolved. All
shipped axes nest. Cost 32:17 wall; the flag is +1.9%.

### D-038 — The model is now CALCULATION-limited at reco level — SETTLED (measured)
GRAIN yield-weighted median 5.357e-05 -> 3.410e-06 (15.7x); GRAIN>CALC in 32/39
directions -> 4/39 (the two zero-derivative `b_qqDS` and the two alphaS legs);
alpha_s-equivalent worst 0.152 -> 0.034 sigma, 0.0017 excluding those legs. TOTAL
max|dev| median 7.77e-04 -> 2.25e-04 and now EQUALS CALC alone -- no binning
headroom remains. `mufup` 7.07e-03 unmoved (qT[0,1] cutoff convention).

### D-039 — RETRACTION: the -7.5e-04 central offset is the gen MASS window, not |Y|>2.5 — SETTLED
Measured acceptance=False split: mass window **7.470e-04** vs |Y|>2.5
**2.950e-06**; the |Y| hypothesis predicts 0.4% of the measurement. Real effect:
reco m(ll) in-window while preFSR mass is not, given the correction's Q FLOW bin
(exactly 1.0). Predicted with no free parameter by `f_mass * |rho-1|`,
f_mass = 7.47e-04 -- measured/predicted 1.11 median, log-log corr +0.9989 over 35
directions. It under-shoots the two alphaS legs by x23, confirming those are the
event-level LHAPDF weight rather than a fold error.

### D-040 — CLOSED: the 15.3% deficit above qT 44 is the tail — SETTLED
gen qT>100 is 1.977% of N_gen = **16.97%** of the shipped overflow column against
17.0% measured. Corr flow bins are exactly 1.0; nothing is missing.

### D-041 — OPEN (needs Luca): the 781-bin cache costs ~55-80 h
TOTAL/CALC on the new grid need a cache over 781 gen bins; none exists.
~55-80 h at 210 threads, ~800 MB -- 3-4.5x the shipped 17.6 h, because the new
grid splits BOTH expensive fixed-order qT cells ([0,1] and [44,100]).
**Run the 1-bin `--subset` timing test on the new runcard first** (minutes) to
replace the bracket with a measurement. Also the strongest argument yet for
fixing the member-loop barrier rather than sharding around it.

### D-042 — The 62-member production cache PASSES and is DELIVERED — SETTLED
Hessian symmetry exactly **0.00e+00** at (210,53,53); fold sum rule exactly
**0.00e+00**; FD-vs-analytic worst **8.14e-07**; anchor re-evaluation
bit-identical. `sum(sigma) = 670.01137`, 1.9e-07 from the number D-025 used to
validate `rel 1e-3` -- so that tolerance decision is reconfirmed on the
production artefact.
The warned-of `pdf_eig0` FD failure **did not occur** (8.14e-07 OK vs 2.97e-04
FAIL on the 4-bin cache): the summed derivative is -0.699 here against 3.4e-04
there, 2000x larger against the same round-off floor. Step-size scan gives the
textbook V with truncation rising **exactly as h^2**; a wrong gradient is flat.
Merge re-validated in three separate processes: merged-restricted-to-one-ptV-bin
equals that shard to all 12 digits in value AND Jacobian, at the anchor AND at a
point moving all 29 eigenvectors, with the three totals differing (not a
memoisation collision).

### D-043 — The PDF response closes, better than most of what we already accepted — SETTLED
All 58 eigenvector directions, full grid: **4.02e-04 … 2.43e-03, median
9.03e-04**; above qT 1 GeV, 2.05e-05 … 8.23e-04. On the SAME cache the 39
signed-off directions run to 1.40e-02, median 7.14e-04, and **8 of them are worse
than the worst of the 58**. Above qT 16 GeV all 58 close to <= 1.67e-05 while the
transitions still sit at 2.50e-03.
The earlier "~1e-6" is **confirmed in its window, refuted as a grid number**, and
is not eigenvector-specific -- the NP lambdas degrade by the identical factor
between the same two windows.

### D-044 — No PDF convention factor on either side; the swap is one-for-one — SETTLED
Regressing `ln r_model = s * ln r_template` over ~200 bins per direction:
**s = 0.999333 mean, max|s-1| = 9.47e-03**. The trap signatures (1.645, 0.608,
-1) sit 68x the scatter away. Templates carry raw CT18ZNNLO members at native
90% CL and `pdf_eig{i}` is that same raw pair's coefficient (+1 -> pdf(2i+1),
-1 -> pdf(2i+2)), per pair, no 1/1.645 anywhere.
Real discriminating power: CT18Z pairs are ASYMMETRIC (max|ln r_up + ln r_dn| to
4.0e-02) and the model reproduces that to 3-8%, so it is not a symmetrised
linear derivative.

### D-045 — 29 PDF eigenvectors carry only ~2.76 EFFECTIVE shapes — SETTLED (act on this)
No `pdf_eig*` column is null (only `tnp_b_qqDS`). But of 406 pairs, **154 have
|cos| > 0.8, 78 > 0.9, 37 > 0.95, one > 0.99** (e5/e23 at 0.9964); block
condition **2.7e+04**; 8 of 29 singular values above 1%; **participation ratio
2.76 effective shapes of 29**. Half a typical eigenvector's leverage is pure
normalisation (shape fraction median 0.553), and projecting that out still leaves
28 pairs above 0.9.
**Physics:** the eigenvectors are orthogonal in PDF space, NOT in the space of
210-bin (qT,|Y|) Z-spectrum responses. The fit stays well-posed because the
priors regularise it, **but per-eigenvector postfit values must NOT be reported
as measurements -- quote the total PDF impact** -- and expect more minimiser steps.

### D-046 — D-004 is OVERTURNED on its own stated condition — SETTLED
D-004 kept the eigenvectors as templates because no production eigenvector cache
existed. One now exists and validates. Next card change: exclude
`scetlib_dyturbo_.*pdfvars` (against the SYSTEMATIC name, per D-006) and float
`pdfEig{0..28}`, keeping the 4 MSHT20 mb/mc nuisances, which the model does not
provide. **Not executed** -- separate task, separate gate.
This validation is **gen-level only**; reco-level eigenvector closure is
unmeasured, and that is where D-038 says granularity used to dominate.

### D-047 — Fit-readiness measured; the earlier projections were pessimistic — SETTLED
Warm value+jacobian **421 ms** at P=53 against 155 ms at P=24 -- the "~1.2 s"
figure was the COLD call (1.27 s), 2.9x pessimistic. Hessian **68.9 s**, not the
projected 4-5 min. Peak resident **48.7 GiB**, low end of the 50-64 GB band and
still the constraint on concurrency.
Member count confirmed free: 15x the members cost 2.72x, for 2.21x in P. In a fit
the model is ~8% of a P=24 iteration, so eigenvectors add ~266 ms, about 13% per
iteration if rabbit's overhead is P-independent. **Unmeasured: the iteration
count**, which D-045's conditioning may raise.

### D-048 — The transitions' 20-39% improvement here is NOT attributable — SETTLED
34 of 37 non-null directions identical to 3 s.f. against `cache_260824b` (n_eig=0,
same 1e-3, same nak build -- chosen over the published p4 table, which changes
tolerance AND kernel). Only the transitions move, by 4-6e-04, **inside the
3.0e-03 two-build Jacobian floor**. Separating experiment: read THIS cache with a
build lacking `92f1299` -- one cache, two readers, no build-to-build floor.

### D-005 — The 260820 card's exclusion regex was OVER-BROAD; card remade — SETTLED
**Why:** its `scetlib_.*` branch silently deleted the 58 PDF eigenvector
nuisances and the 4 mb/mc ones, while its `muF.*` branch matched nothing.
**Evidence:** `bcQuarkMass` 5 -> 1 is the fingerprint; set-diff against the
full-template card `260723_Z_2D_card_davidFix` on the NEW card shows exactly the
intended 15 removed and nothing else.
**Consequence:** any fit run on the 260820 card was missing the PDF and quark-mass
uncertainties entirely. New card:
`260826_Z_2D_card_scetlib_ad/ZMassDilepton_ptll_yll_adexcl/`.

### D-006 — `--excludeNuisances` matches the SYSTEMATIC name, not the nuisance — SETTLED
`re.match` against `addSystematic`'s `name=` (falling back to `histname`), so
`^pdfAlphaS$` would NOT have worked. The transition and FO-scale nuisances are
four outputs of ONE systematic, hence all-or-nothing. Recorded because this is
the single most error-prone step in building the reco card.

### D-007 — D-004 CONFIRMED by fact, not by schedule — SETTLED
PDF eigenvectors stay as templates because every production cache has
`n_eig = 0`, so the model registers no `pdfEig*` and nothing can double count.
**Overturned by:** a production eigenvector cache landing — at which point the
58 `pdf{N}CT18ZSym*` MUST be excluded or they double count.

### D-008 — Reference for reco variations = the histmaker's OWN reco variation
hists, not the card's `hlogk` — SETTLED
**Why:** `hlogk` is symmetrised into SymAvg/SymDiff and would need un-mixing;
the histmaker hists carry the 39 directions individually and unsymmetrised.
**Evidence:** that hist's `central` equals plain `nominal` to 2.9e-14.

### D-009 — RETRACTION: the second central term is MC, not a fold error — SETTLED
First attributed to the gen fold. It is not: `R @ N_gen` reconstructs the
histmaker nominal up to a nearly flat -7.6e-4 (reco events with gen |Y| > 2.5,
dropped by the gen grid), so the central carries essentially no fold
approximation. The term is the corrected-MC gen spectrum against the correction
file. Recorded as a retraction because it was nearly published.

### D-018 — TWO ASYMMETRIES BETWEEN CARD AND MODEL — OPEN (needs Luca)
1. The card's `resumFOScaleZ` is the kappa_R envelope restricted to **qT > 20**,
   while the model's `resumScaleMuR` is **all-qT**. The model is BROADER below 20.
2. **`resumScaleMuF` has no card counterpart at all** under `--resumUnc tnp`, so
   floating it ADDS an uncertainty the template analysis never carried.
Neither is a bug; both are choices about what the analysis's uncertainty should
be, and they change the quoted sigma(alpha_s). Not relitigated by the agent.



Luca is away until 08:00 and asked for maximum progress plus a careful record of
every decision. Three agents live at handover: five-knot muF stencil, `n_train`
study, reco-2D closure.

### D-001 — Launch the full 62-member PDF cache once `n_train` is settled — PROVISIONAL
**Why:** Luca: "gate the launch of the full PDF members cache on that result."
That is explicit authorisation to launch AFTER the n_train answer, not before.
**Evidence:** eigenvector path validated at ~1e-6 against templates on
|Y|<0.3, qT[20,28] (`260825_scetlib_ad_eigenvectors`); build cost 9-15 h.
**Overturned by:** an n_train answer that implies a different build parameter, or
a five-knot decision that would change the member set (five knots CHANGES the
muF members, so a cache built at three knots would need rebuilding — see D-002).

### D-002 — Do NOT let the five-knot work block the PDF cache build — PROVISIONAL
**Why:** they touch different member groups. The PDF cache's 58 eigenvector
members are unaffected by the muF stencil; only the 2 muF members would change.
Rebuilding 2 of 62 members is ~1 h, against 9-15 h for the whole cache.
**Risk accepted:** if five knots ships, the muF members must be rebuilt and
merged. The member merge within a single build is byte-identical, but members
from INDEPENDENT builds are unmergeable (builder not reproducible), so this may
in practice mean a full rebuild. Flagged for Luca rather than assumed away.

### D-003 — Reco closure runs as ONE agent, not two — SETTLED
**Why:** central closure and variation closure share a large, error-prone setup
(response matrix, gen fold, card conventions, the three known traps). Two agents
would independently rediscover the same traps.
**Revisit:** once the card exists and the setup is proven, the variation work is
parallelisable and should be split.

### D-004 — PDF eigenvectors stay as TEMPLATES in the reco card for now — PROVISIONAL
**Why:** the model does not yet provide them continuously in a production cache,
so excluding them from the card would silently delete a real uncertainty.
**Overturned by:** the full eigenvector cache landing and validating on the full
grid. Delegated to the reco agent to confirm and justify explicitly.

---

## 2026-08-25 daytime — decisions already taken

### D-010 — Theory corrections stay applied IN the histmaker — SETTLED (Luca)
The param model supplies only the RATIO for variations. Work in the other
direction was deleted (`compare_cards.py`).

### D-011 — Fix the transitions regardless of alpha_s impact — SETTLED (Luca)
Overruled an impact-based deprioritisation. **Vindicated by measurement:** the
0.002-0.025 sigma scoring was CIRCULAR — measured on the build where the muF
interpolation the transitions route through was wrong, which made them look
harmless. Patched, the transition group carries ~3x more alpha_s.

### D-012 — Leave the non-singular qT cutoff mismatch alone — SETTLED (Luca)
Production corrections zero their non-singular below 1.0 GeV, we cut at 0.1.
Affects only qT [0,1]. Aligning is one runcard line + an 83-min rebuild; not
worth it now. Report that bin separately, never fold into a headline.

### D-013 — Never split PDF members across processes — SETTLED
The builder is not reproducible: four identical-configuration builds gave
357/359/359/371 nodes/bin, structure differing in 9 of 10 bins. A cross-build
member merge is invalid and would be SILENTLY wrong if counts coincided. Split
BINS instead (validated exact, 0.000e+00 in value and Jacobian).

### D-014 — No knot RE-SPACING; the proposal is MORE knots — SETTLED
f=sqrt2 improves the transitions ~4x but kappa_F = 0.5 and 2 stop being exact
samples and muF degrades 150-180x. Five samples (1/2, 1/sqrt2, 1, sqrt2, 2)
keep 0.5 and 2 exact. **Supersedes** the earlier "no knot feature is justified",
which was measured with the wrong member coordinate.

### D-015 — `resumTransition1/3` stay frozen; `resumTransition2` floats — SETTLED
Physics choice: the analysis varies only the central transition point.
`resumTransition2` left DEFAULT_FROZEN once its derivative was fixed.

### D-016 — `tnp_b_qqDS` cannot float for the Z — SETTLED (measured)
Its Jacobian column is EXACTLY 0.0 (every other column 7e-6..1.0 of the max);
it scales a channel that does not contribute. The model correctly refuses it as
singular. So `fit_params=all` is 18 parameters, not 19.

### D-017 — Declared priors are unphysically wide — OPEN
Drawing truth from them gives a NEGATIVE cross section in 63% of draws (up to 81
of 210 bins). `delta_lambda2`'s prior is 0.5 against a postfit constraint of
0.0065 — 80x wider than the data allows. Toy ensembles therefore use rabbit's
own machinery. **Needs Luca before the priors are used quantitatively.**

---

## Reco 2D closure (agent, 2026-08-25 night)

# Decisions — reco-level 2D (ptll, yll) closure of the scetlib_ad param model

Session: overnight 2026-08-25/26. Agent: reco-closure workstream.
Staged for folding into `studies/scetlib-ad-param-model/DECISIONS.md`.
(D-004, PDF eigenvectors stay as templates, was taken by the coordinator; it is
confirmed with evidence in D-R07 below.)

---

## D-R01 — Reference histmaker: `260723_Z_histmaker_davidFix`, NOT `260820_Z_histmaker`

**Decided.** The new card is built from
`/ceph/.../260723_Z_histmaker_davidFix/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5`.

**Why.** Three reasons, in order of force:
1. The settled configuration (logbook 2026-08-25) is *theory corrections stay
   applied IN the histmaker*. `260820_Z_histmaker/mz_dilepton_maxFiles_m1.hdf5`
   is the `--theoryCorrAltOnly` run — its central weight carries NO SCETlib
   correction — so it is the histmaker of the ABANDONED route. Using it would
   silently revive the deleted configuration.
2. Both production caches (`cache_260824b`, `cache_260825_p4`) were built with
   `prepare_cache_for_card.py --card .../260820_Z_2D_card_scetlib_ad/ZMassDilepton_ptll_yll_realdata/ZMassDilepton.hdf5`,
   and THAT card was built from the 260723_davidFix histmaker. Keeping the same
   histmaker keeps the gen grid (21 qT x 10 |Y| = 210 bins) bit-identical, so no
   cache rebuild is needed.
3. The template card used as the variation reference
   (`260723_Z_2D_card_davidFix`) is built from the same histmaker, so the model
   card and the reference card differ ONLY by the exclusion regex.

**Evidence.** `meta_info.command` of both 260820 cards (dumped 2026-08-25):
the `realdata` one reads `-i .../260723_Z_histmaker_davidFix/...Corr_maxFiles_m1.hdf5`;
the `theoryCorrAltOnly` one reads `-i .../260820_Z_histmaker/mz_dilepton_maxFiles_m1.hdf5`
plus `--resumUnc none`.

**What would overturn it.** A decision to move the correction out of the
histmaker (explicitly reopened by Luca), or a gen-binning change that forces a
cache rebuild anyway.

---

## D-R02 — `--excludeNuisances` matches the *systematic* name, not the nuisance name

**Decided.** The exclusion regex is written against the `name=`/`histname`
argument of `Datagroups.addSystematic`, because that is what
`Datagroups.isExcludedNuisance` is called on
(`wremnants/postprocessing/datagroups/datagroups.py:1420` — `if self.isExcludedNuisance(name): return`,
where `name` falls back to `histname`), and the match is `re.match`
(start-anchored), not `re.search`.

**Consequence, and it is the single biggest trap in this task.** The card-level
names one sees in `hsysts` are *outputs* of a systematic and cannot all be
targeted directly. In particular:

* `resumTransitionZSymAvg/SymDiff` and `resumFOScaleZSymAvg/SymDiff` are FOUR
  nuisances produced by ONE `addSystematic` whose name is
  `resumTransitionFOScaleZ` (`rabbit_theory_helper.py:1287`). They are
  all-or-nothing: no regex can drop the transition and keep the FO scale.
* The alphaS nuisance is called `pdfAlphaS` in the card but its systematic is
  named by its histname,
  `scetlib_dyturbo_..._CT18Z_N3p0LL_N2LO_pdfas_Corr[ByHelicity]`
  (`rabbit_theory_helper.py:1236`, `addSystematic(**as_args)` with no `name=`).
  A regex `^pdfAlphaS$` would NOT exclude it.

**Evidence.** Source reading above, plus the 260820 card: its regex
`^(.*scetlibNP.*|pdf.*|resumTNP_.*|resumTrans.*|muF.*|resum.*|scetlib_.*)$`
left `hnoiidxs` EMPTY and no `pdf*` nuisance in `hsysts` — i.e. it was the
`scetlib_.*` branch, not `pdf.*`, that removed alphaS, and the same branch also
removed the 58 CT18Z eigenvectors and the MSHT20 mb/mc-range nuisances.

**What would overturn it.** A change to `isExcludedNuisance` to match final
nuisance names.

---

## D-R03 — The 260820 exclusion list is REJECTED as over-broad; a narrow one replaces it

**Decided.** Do not reuse
`^(.*scetlibNP.*|pdf.*|resumTNP_.*|resumTrans.*|muF.*|resum.*|scetlib_.*)$`.

**Why.** Measured against the full-template card
(`260723_Z_2D_card_davidFix`, 3746 nuisances) the 260820 regex silently deletes
real uncertainties the model does not provide:

| dropped by 260820 | n | provided by the model? |
|---|---|---|
| `pdf{1..29}CT18ZSym{Avg,Diff}` (CT18Z Hessian eigenvectors) | 58 | NO — cache has `n_eig = 0` |
| `pdfMSHT20mbrangeSym{Avg,Diff}`, `pdfMSHT20mcrangeSym{Avg,Diff}` | 4 | NO — no m_b/m_c parameter exists |

`bcQuarkMass` went from 5 members (template card) to 1 (`mb_up` only) in the
260820 card — that is the visible fingerprint of the over-broad cut.
Also `muF.*` in that regex matches NOTHING (there is no card systematic whose
name starts with `muF`), which is harmless but misleading.

**What would overturn it.** A cache with `n_eig = 29` and a validated eigenvector
response; then `pdf{N}CT18Z` joins the exclusion list.

---

## D-R04 — The exclusion list (the deliverable table)

Regex used:

```
--excludeNuisances '^(resumTNP|scetlibNP|resumScaleZ|resumFOScaleZ|resumTransitionFOScale|scetlib_dyturbo.*pdfas.*)'
```

(start-anchored `re.match`, so no trailing `.*` is needed)

| card systematic (`addSystematic` name) | card nuisances it produces | n | EXCLUDED / KEPT | reason |
|---|---|---|---|---|
| `scetlib_dyturbo_..._pdfas_Corr[ByHelicity]` | `pdfAlphaS` (NOI, unconstrained) | 1 | **EXCLUDED** | model parameter `alphaS`, continuous, PHYSICAL units, built on the same CT18Z `as_0116`/`as_0120` member pair (cache `has_as=1`, central 0.1180 +- 0.0020) |
| `resumTNP` | `resumTNP_{gamma_cusp,gamma_mu_q,gamma_nu,s,h_qqV,b_qqV,b_qqbarV,b_qqS,b_qqDS,b_qg}` | 10 | **EXCLUDED** | model parameters `resumTNP_*`, one-for-one, same names, sigma = 1 |
| `resumTransitionFOScaleZ` | `resumTransitionZSym{Avg,Diff}` | 2 | **EXCLUDED** | model parameter `resumTransition2` (quad reparam through 0.35 / 0.6 / 0.75) |
| `resumTransitionFOScaleZ` (same call) | `resumFOScaleZSym{Avg,Diff}` | 2 | **EXCLUDED** | model parameter `resumScaleMuR` (log reparam, theta = +-1 -> kappa_R = 2 / 0.5). See caveat C-1. |
| `scetlibNP` | (none — `--npUnc none`) | 0 | **EXCLUDED** (belt and braces) | model parameters `lambda2, lambda4, delta_lambda2, lambda_inf, lambda2_nu, lambda4_nu, lambda_inf_nu, b0_over_bmax_nu` |
| `resumScaleZ`, `resumFOScaleZ` (the `--resumUnc scale` route) | (none — `--resumUnc tnp`) | 0 | **EXCLUDED** (belt and braces) | would be the muB/nuB/muS/nuS envelope + kappa/muF pair; superseded by the model |
| `scetlib_dyturbo_..._pdfvars_Corr[ByHelicity]` | `pdf{1..29}CT18ZSym{Avg,Diff}` | 58 | **KEPT** | model provides NOTHING here: production caches have `n_eig = 0`. Excluding would delete the PDF uncertainty outright. Confirms D-004. |
| `scetlib_dyturbo_..._MSHT20m{b,c}range_..._pdfvars_Corr` | `pdfMSHT20m{b,c}rangeSym{Avg,Diff}` | 4 | **KEPT** | m_b / m_c mass-range uncertainty; the model has no quark-mass parameter |
| (MiNNLO) | `mb_up` | 1 | **KEPT** | same |
| `qcdScaleByHelicity` | `QCDscaleZ*helicity_*_Sym{Avg,Diff}` | 176 | **KEPT** | MiNNLO fixed-order / angular-coefficient scale variations. The model varies the SCETlib resummed+matched prediction only; the MiNNLO helicity decomposition that carries the correction to reco is untouched by it. |
| `helicity_shower_kt` | `pythia_shower_kt` | 1 | **KEPT** | parton-shower k_T, not a SCETlib parameter |
| EW block | `weak_{default,aem,ps}`, `horaceqedew_FSR_Corr0`, `horacelophotosmecoffew_FSR_Corr0`, `pythiaew_ISR_Corr0` | 6 | **KEPT** | electroweak, orthogonal to the model |
| — | `massShiftZ2p1MeV`, `widthZ`, `sin2thetaZ` | 3 | **KEPT** | Z lineshape/couplings, not SCETlib |
| — | everything experimental (`effStat*`, `effSyst*`, `Scale_correction*`, `Resolution_correction*`, `ScaleClos*`, `pixel_multiplicity*`, `CMS_prefire*`, `lumi`, `CMS_background`, `CMS_PhotonInduced`) | ~3480 | **KEPT** | detector, untouched |

Caveat **C-1 — the scale sector is NOT a like-for-like swap, and this must not be
read as one.** The card's `resumFOScaleZ` is the envelope over
{central, `kappaFO0.5-kappaf2.`, `kappaFO2.-kappaf0.5`} **restricted to qT > 20 GeV**
(`wremnants/production/theory_corrections.py:757,795` — `renorm_scale_pt20_envelope`,
`slice_axis="qT", slice_val=20.0`), deliberately, "to neglect the part at low pt
which should be redundant with the TNPs". The model's `resumScaleMuR` is the full
kappa_R response at ALL qT. Direction-for-direction the model is BROADER below
qT 20.

Caveat **C-2 — `resumScaleMuF` has no card counterpart at all.** With
`--resumUnc tnp` the card carries no muF nuisance whatsoever (verified: zero
matches for `muf` in the 3746 names of the template card). Floating the model's
`resumScaleMuF` therefore ADDS an uncertainty the template analysis never had; it
is not double counting, it is a new term. Whether it should float is a physics
decision for Luca, not a card decision. (It is also why the 260820 regex's
`muF.*` branch matched nothing.)

---

## D-R05 — `--noi alphaS` is kept, and is inert

**Decided.** Keep `--noi alphaS` on the setupRabbit command even though the
alphaS systematic is excluded.

**Why.** It makes the new card differ from the card the caches were built
against (`260820_.../ZMassDilepton_ptll_yll_realdata`) in the exclusion regex and
nothing else — a clean single-variable change. `--noi alphaS` only affects the
alphaS systematic (scale 0.002 instead of 0.0015, `noConstraint=True`,
`symmetrize="average"`), which is excluded, so it has no effect on the card.

**Evidence.** The 260820 card carries `--noi alphaS` AND excludes the alphaS
systematic, and its `hnoiidxs` is an empty array — no crash, no NOI.

**What would overturn it.** Nothing physical; drop the flag for tidiness whenever
the card is next remade.

---

## D-R06 — `--npUnc none` retained

**Decided.** Keep `--npUnc none`, as both prior cards do. The eight NP lambdas
are model parameters. The regex entry `scetlibNP` is redundant with it and is
kept only so the card is safe if someone changes `--npUnc`.

---

## D-R07 — CONFIRMING D-004: PDF eigenvectors stay as templates

**Confirmed, with evidence, not merely accepted.**

The operative fact is not "the eigenvectors are still being validated" but
something stronger and checkable: **the production caches register no eigenvector
parameters at all.** `ScetlibADXsec.cache_param_names(cache_260825_p4)` returns
24 names and `n_eig = 0` in the npz; there is no `pdfEig*` among them. So there
is literally nothing in the model that could double count against
`pdf{N}CT18ZSym*`, and excluding them would delete the single largest theory
uncertainty on alpha_s with no replacement.

The alphaS/eigenvector split is clean, which is what makes this safe: in CT18Z
the alpha_s variation is a separate member pair (`as_0116`/`as_0120`), not one of
the 29 Hessian eigenvectors — the card shows `pdfCT18Z` with 59 members against
`pdfCT18ZNoAlphaS` with 58. So excluding `pdfAlphaS` while keeping all 58
eigenvector nuisances double counts nothing and drops nothing.

**What would overturn it.** A cache built with `--pdf-eig 29` whose eigenvector
response is validated across the full grid (currently ~1e-6 in one window only).
At that point `scetlib_dyturbo_..._pdfvars_Corr` joins the exclusion list and
`pdfEig{0..28}` float instead.

---

## D-R08 — SCETlib build: the PATCHED one (92f1299, MR !8)

**Decided.** All model evaluations in this workstream use
`SCETLIB_BUILD=<scratch>/scetlib_build_92f1299`, a byte-identical snapshot
(`md5(libscet-qT.so) = e6a7faf186b4fbf11974ca6fc65b924b`) of
`/work/submit/lavezzo/alphaS/scetlib-trans/build-trans`, whose worktree is clean
at `92f1299 qT/ad: the muF members are three muF samples, so interpolate in muF`.

**Why.** (1) The 2026-08-25 Asimov A/B shows the fix materially rotates the
(muR, muF, transition) block against alpha_s — two correlation sign flips and a
+78% sigma(resumScaleMuR) — so any number produced on the unpatched build is
already known to be contaminated. (2) It changes no stored quantity, so the
existing caches remain valid (`92f1299` is `bb2e7cb` plus ONE header,
`include/scetlib/qT/ad/ad_kernel.hpp`; `py/` is identical, so mixing the shared
tree's `py/` with this build's `lib/` is safe).
(3) The snapshot is taken so that another agent rebuilding `build-trans` cannot
change my results mid-run.

**What would overturn it.** MR !8 being revised before merge.

---

## D-R09 — Variation reference: the histmaker's OWN reco variation hists

**Decided.** For the reco variation closure the reference is
`nominal_ptll_yll_scetlib_dyturbo_..._CT18Z_N3p0LL_N2LO_Corr` (and its
`_pdfas_Corr` sibling for the alpha_s pair) read from the 260723_davidFix
histmaker: reference response = `H_reco[var] / H_reco[central]`, per (ptll, yll)
bin.

**Why, rather than the template card's `hlogk`.** The card's theory nuisances are
symmetrised into `SymAvg`/`SymDiff` combinations and rescaled (alphaS by
0.002/0.002, TNPs by `--scaleTNP`), so a card-level logk column is a LINEAR
COMBINATION of two directions, not a direction. Comparing per-direction model
responses against it would require undoing the symmetrisation, adding a step that
can itself be wrong. The histmaker `vars` axis carries the 39 directions
individually and unsymmetrised, exactly as the gen-level `validate_variations.py`
reference (`Corr[var]/Corr[central]`) does — so the reco table is reported in the
same terms as the gen table, which is what was asked for.

**What it costs.** The reference fold is per-event (each event weighted by the
correction ratio at its own gen qT, y), while the model folds with the
bin-averaged response matrix R. The residual therefore contains a genuine
"R-granularity" term. It is second order in the ratio (R cancels to first order)
and is bounded by the central closure, where the same effect appears at first
order.

**What would overturn it.** Finding that the histmaker's `vars` hist is stored
after helicity smoothing while the model is not, in which case the smoothing
would have to be applied to the model side too.

---

## D-R10 — RETRACTION, made before publication: the second term is NOT a fold error

**What I first wrote, and why it was wrong.** The first version of the central
decomposition labelled its second term "FOLD" and described it as "our
bin-averaged R against the histmaker's per-event reweighting". That is wrong, and
the error is worth recording because it is exactly the kind of confident
misattribution this study has published before.

**The identity that settles it.** The datacard stores `R = R_raw / N_gen`, and
the histmaker's reco nominal is `sum_g R_raw(b, g)`. Therefore

    R @ N_gen  ==  histmaker nominal   up to events with no gen column

Measured: a nearly FLAT `-7.6e-4` (per-bin max `2.3e-3`, range `-6.3e-4` at
central rapidity to `-1.2e-3` at `|yll| > 1.8`). That deficit is the reco-selected
events whose GEN `|Y|` exceeds 2.5 -- the card's gen grid stops at 2.5 and the
`absYVGen` overflow is dropped. Because it is nearly constant, the shape
comparison divides it out, and the CENTRAL prediction carries **essentially no
fold approximation**. Checked numerically at the top of both scripts, not
assumed. (I first wrote "~1e-16" in the script docstring before measuring it;
that was corrected before publication.)

**What the term actually is.** `(R @ sigma_CorrZ) / nominal` measures whether the
CORRECTED MC's own gen spectrum `N_gen(g)` has the same shape as the correction
file's `sigma(g)` on this 210-bin gen grid. It is nonzero because the histmaker
applies the correction through helicity moments on a MiNNLO sample (not the same
operation as multiplying a binned unpolarised spectrum) and because MiNNLO's
residual (Q, y, qT) correlation survives inside a gen bin. Relabelled **MC**.

**Where granularity genuinely lives: the VARIATIONS.** There the reference
reweights per event inside a gen bin while the model multiplies the whole bin, so
a real granularity term exists. The variation table therefore splits three ways
(D-R11) instead of two.

**What would overturn it.** The identity check failing (it does not: see the
number quoted in `00_README.txt`).

---

## D-R11 — The variation residual is reported as a three-term split

**Decided.** Per direction the residual is factorised exactly as

    r_model / r_ref = (r_model / r_A) x (r_A / r_B) x (r_B / r_ref)
                       \__ CALC __/     \__ WGT __/    \__ GRAIN __/

with `r_A` the correction file's gen response folded with the MODEL's anchor
spectrum as the gen weight, and `r_B` the same response folded with the MC's
`N_gen`.

* **CALC** — the model's gen-level response error. The reco image of the
  gen-level table. Fixed in SCETlib / the cache.
* **WGT** — the same response folded against two different gen weights. Nonzero
  only where the model's gen spectrum and the MC's differ in shape INSIDE a reco
  bin.
* **GRAIN** — bin-averaged response against per-event. Zero iff the correction
  ratio is constant inside every gen bin. Pure gen-binning granularity, no model
  physics. **It is a cost the discrete templates do not pay**, because those are
  built by the same per-event reweighting the reference uses.

**Why it matters and is not bookkeeping.** A single total says nothing about
whether the calculation or the binning is at fault, and the two are fixed by
different work (a SCETlib change versus a finer gen grid and a new cache).
Measured: once the qT [0,1] convention is aligned, GRAIN exceeds CALC in 32 of
39 directions. The limiting factor at reco level is the gen binning, not the
calculation.

**What would overturn it.** A card with a finer gen grid whose GRAIN term does
not fall.

---

## D-R12 — The qT [0,1] convention is reported separately, never folded into a headline

**Decided.** Every variation table is produced twice: as shipped, and with
`--fix-genbin0`, which replaces the model's gen qT [0,1] response by the
correction file's before folding. The difference between the two IS that bin's
contribution, so it is quantified rather than argued about.

**Why not just exclude the bin.** At reco level the gen qT [0,1] bin is smeared
across many reco ptll bins, so there is no reco bin to exclude. Substituting the
reference's response in that one gen row is the only clean way to isolate it.

**Evidence it is the right knob.** In the central closure the reco ptll [0,1] bin
is the single worst bin and its residual is 100% CALC (-1.55e-2) with MC
consistent with zero (-5.6e-5) -- the signature of a gen-level calculation
convention, not of anything downstream.


---

## D-R13 — ROOT CAUSE: the card's last gen bin is an OVERFLOW, not [44, 100]

**Found, and it explains the single largest central residual outside qT [0,1].**

The reco `ptll [37, 44]` bin closes at only `-1.03e-2`, and the decomposition
puts 100 % of that in the MC term (`CALC = +1.7e-4`). Cause:

* The histmaker's gen `ptVGen` axis is
  `[0, 1, 2, ..., 28, 33, 44]` with `overflow=True` -- verified on `prefsr`,
  `prefsr_full` and `nominal_prefsr_yieldsUnfolding`. Every gen histogram in the
  file stops at 44.
* The datacard's `edges__ptVGen` nevertheless declares 21 bins ending
  `..., 33, 44, 100`. The bin labelled **[44, 100] IS the overflow** and contains
  every event with gen `qT > 44` -- 11.6 % of `N_gen`.
* The correction file's own `qT` axis stops at **100 GeV** (checked: last edges
  70, 80, 90, 100), so the model can only fill 44-100.
* Measured consequence: `sigma_CorrZ / N_gen` on the gen grid is **1.020 +- 0.002
  in all 20 bins with qT < 44** (flat in `|Y|` to 0.4 %) and **0.847 in the
  overflow bin** -- a 15.3 % deficit, flat in `|Y|` (0.8425 at `|Y| < 0.15`,
  0.8586 at `|Y| > 1.8`).

**Consequence for the fit, stated plainly.** The model under-fills one gen bin by
15 %, and that bin feeds the top reco `ptll` bin. It does NOT bias the fit at
first order, because the model supplies the RATIO to its own anchor and the same
deficit sits in numerator and denominator. What it does mean is that the
*response* in `ptll [37, 44]` is computed on 44-100 GeV only while the data bin
also contains `qT > 100`.

**What I could NOT separate, and the experiment that would.** Whether the 15.3 %
is entirely the `qT > 100` tail, or partly the correction not being applied above
100 GeV in the histmaker. Every gen histogram in this histmaker file stops at 44
with an overflow, so the question cannot be answered from it. The experiment:
rerun the histmaker with a `ptVGen` axis that resolves `qT > 44` explicitly (e.g.
`..., 44, 100, 13000`) and re-measure `sigma_CorrZ / N_gen` bin by bin.

**What would overturn it.** A gen axis that genuinely ends at 100 with the
overflow separate; then the ratio in that bin should return to ~1.02.

---

## D-R14 — Reported metrics: absolute AND relative to each direction's response

**Decided.** Every variation row carries both `TOTAL yield-weighted mean|dev|`
(absolute, comparable to the gen-level table) and `rel = TOTAL / (this
direction's own yield-weighted mean |response - 1|)`.

**Why.** A residual of 1e-3 is negligible on a 3 % response and serious on a
0.06 % one. Reporting only the absolute number would have made the transition
points look like the best-behaved directions in the table when they are the
worst: absolute 2.5-4.6e-3 (middle of the pack) but 11-19 % of their own
response (the largest by a factor 3).

**One trap in the column.** `resumTNP_b_qqDS` has an identically zero response
for the Z, so `rel` is 0/0 and prints as 17.1. It is flagged in the README; do
not read it as a failure.

---

## Five-knot muF stencil (agent, 2026-08-25 night)

# Decision log — staged for studies/scetlib-ad-param-model/DECISIONS.md
# Agent: FIVE-KNOT muF STENCIL (transition-point closure vs CorrZ)
# Started 2026-08-25 evening.

## 0. READ THIS FIRST — APPARENT MIS-ROUTED INSTRUCTION (flagged, not silently ignored)

The overnight coordinator message asks this agent to complete the **right-hand
panel of `~/public_html/alphaS/260825_scetlib_ad_eigenvectors/eigenvector_validation.png`
(accuracy vs `n_train`)** and to "report `use n_train = N`" because it gates a
9-15 h 62-member PDF cache build.

**That is not this agent's brief and I have not switched to it.** My brief is:
prototype a five-knot muF stencil in SCETlib and prove or disprove that it
improves the transition-point variations' closure against the production CorrZ
templates. Nothing in it mentions `n_train`, PDF eigenvectors, or the 62-member
build; the two tasks share only the study slug.

I am flagging rather than obeying because:
 * switching would abandon the five-knot deliverable with nothing to show, and
 * an `n_train` answer produced as a by-product of a muF-knot A/B would be
   measured on a 5-10 bin subset cache with `--pdf-eig 0`, i.e. with **zero**
   eigenvector coefficients. `n_train` matters precisely through
   `n_train / n_params` once 29 coefficients are added (logbook, 2026-08-25).
   A number from an `n_eig = 0` cache would not bear on the question at all,
   and quoting it would be worse than saying nothing.

**If the coordinator does want this agent on `n_train`, say so explicitly and I
will stop the knot work.** Otherwise the `n_train` scan needs its own agent with
a cache built at `--pdf-eig > 0`.

The two generic requirements in that message DO apply and are being followed:
this file (one entry per decision, with what would overturn it), and a webdir
with a `00_README.txt` naming figure / reference / build / cache / bin count.

---

## 1. Base commit for the prototype: `near-anchor-knots` (eb60a04), own worktree

**Decided.** New worktree `/work/submit/lavezzo/alphaS/scetlib-5knot`, new branch
`muf-five-knots`, new build dir `build-5knot`. Base = `eb60a04`
= `bb2e7cb` + `92f1299` (muF member COORDINATE fix) + `83cecb2` (settable knot
spacing) + `3a8db11` + the `rule_cvals()` diagnostic.

**Why.** The brief names the coordinate fix a prerequisite, and the knot-spacing
commit already generalised `prof_v_muf` / `Bin_rule::Var::g_v_muf` from "the
Vary leg" to a **log2 exponent** — which is exactly the generalisation five
knots needs (fractional legs +-1/2 are then expressible with no new POD field).
Reimplementing it would have cost a day and would have diverged from the branch
the author already has.

**Evidence.** `git show 83cecb2` and `git show 92f1299` read in full before
writing any code; `git log --graph` confirms eb60a04 contains both.

**Would overturn it.** If the author rejects `92f1299` (MR !8), the five-knot
commit still applies but its measured "before" arm changes.

**Not touched, on purpose:** `scetlib-cms`, `build-fix`, `build-knots`,
`build-trans`, `build-nak`, `build-nakbase`, and every file under WRemnants.

---

## 2. The five-knot stencil needs NO new `ad::GlobalData` field — VERIFIED, not assumed

**Decided.** Implement five knots by (a) redefining `ad::GlobalData::var_muf`
from a FLAG to the COUNT of muF member columns (0, 2 or 4) and (b) fixing the
inner knots at HALF the outer log step, so `var_muf_lnstep` still describes the
whole stencil. No field added, no field widened.

**Why.** `sizeof(ad::GlobalData)` is written into every rule-cache file and
checked on load; any new field refuses every cache on disk. The prior analysis
asserted this was avoidable. It is, and the two ingredients above are how.

**Evidence (measured, not argued).** The 210-bin production cache
`cache_260824b` — written by a DIFFERENT build, with the three-knot stencil —
loads unchanged under the five-knot binary and reproduces the published
three-knot arm on all 39 directions:

| direction | published `after/` arm | five-knot build, 2 knots |
|---|---|---|
| transition x2 = 0.35 | 2.847e-03 | 2.85e-03 |
| transition x2 = 0.75 | 1.124e-03 | 1.12e-03 |
| transition x1,x3 | 3.133e-03 | 3.13e-03 |
| mufup | 1.398e-02 | 1.40e-02 |
| mufdown | 1.979e-03 | 1.98e-03 |
| kappa_R down / up | 7.456e-03 / 4.518e-03 | 7.46e-03 / 4.52e-03 |
| alphaS 0.116 / 0.120 | 2.152e-03 / 2.293e-03 | 2.15e-03 / 2.29e-03 |
| all 8 lambda, all 10 TNPs | — | every one identical to 3 s.f. |

Central cross section identical to 0.000e+00 relative.
Log: `tmp/noop_260824b.log`.

**What would overturn it.** Adding any further field to `ad::GlobalData` (e.g.
storing the inner knot spacing separately instead of fixing it at half a step)
would break every cache on disk and this claim with it.

**Rejected alternative:** a separate `var_muf_lnstep_inner`. Rejected for the
POD-guard reason above; the cost is that the inner knots cannot be moved
independently of the outer ones. That is not a loss for the intended use --
the outer knots are pinned at kappa_F = 1/2, 2 by the production templates.

---

## 3. Half-step members are BUILT by handing `Vary.muf` a spacing of sqrt(f)

**Decided.** An inner member (kappa_F = f^+-1/2) is built by
`set_muf_vary_factor(sqrt(f))` followed by `set_muf_keep_nodes(+-1)`, then
restoring the factor to `f`.

**Why.** `Vary.muf` scales muF by the factor AND divides `muf_min` by the same
factor, and only doing BOTH keeps the large-bT floor at `(muF/Q) muf_min` --
the compensation `Scale_provider.hpp` advertises. Inventing a fractional
`Vary_scale`, or scaling `kappaf` by hand, would move muF without moving the
floor, and the member would then sit somewhere the kernel's own knot formula
cannot reproduce. This way the inner knots are built by exactly the same
mechanism as the outer ones.

**Evidence.** The kernel builds each knot's position from the SAME expression
with `fo_muf` scaled by `f^leg` and the floor divided by `vary*f^leg`; the
member's own `g_v_muf` (a log2 exponent since commit 83cecb2) carries
`leg * ln f / ln 2`, which the AD context turns back into that same factor. The
three-knot no-op above is the check that the two constructions agree where they
overlap.

**What would overturn it.** A measured disagreement between the model at
kappa_F = f^-1/2 and an exact runcard refill at `kappaf = f^-1/2`,
`muf_min /= f^-1/2` (the non-knot reference the 2026-08-25 entry validated at
K = 2 to 9e-16). That test is the next one to run.

---

## 4. The A/B is ONE cache read two ways, not two caches

**Decided.** Added `DrellYan::set_muf_knots_used(n)` -- a documented A/B
instrument that holds the kernel's knot count down to `n`. The BEFORE arm is a
five-knot cache evaluated with `n = 2`; the AFTER arm is the same cache with
`n = 0` (all).

**Why.** Two separately built caches cannot isolate the stencil. The bT node set
is not reproducible between processes (357 / 359 / 371 nodes per bin measured,
logbook 2026-08-25), and the logbook's own reproducibility floor between two
builds of the SAME runcard is 3.1e-05 in sigma but **3.0e-03 in the Jacobian at
a displaced point** -- larger than the transition residual being measured
(1e-03 .. 3e-03 of sigma). With one cache the node set, the rules, the outer
member convolutions and the re-solved weights are bit-identical between arms and
the ONLY difference is the interpolation order.

**Evidence it is faithful.** At `n = 2` the five-knot binary reproduces the
published three-knot numbers on the production cache (decision 2), and in the
live-rule test below the `n = 2` arm reproduces the previously published
three-knot deviations bin by bin.

**Implementation note worth keeping.** The flag is a **global atomic**, not
`thread_local` like `set_rule_replay_mode`: `_stage_var_meta` runs inside the TBB
workers of `_ad_parallel_run`, so a thread-local set on the calling thread would
silently do nothing. That was caught by reading the call site, not by a test --
a test would have shown "no effect" and been read as "five knots changes
nothing".

**What would overturn it.** If `n = 2` on a five-knot cache and a separately
built three-knot cache disagreed by more than the known reproducibility floor,
the clamp would not be a faithful stand-in.

---

## 5. The inner members are CORRECT — proven at kappa_F = sqrt(2), 82x

**The sharp test.** kappa_F = sqrt(2) is a knot of the five-knot stencil and
NOT of the three-knot one, so the five-knot arm must be exact there and the
three-knot arm must not. Reference: a runcard refill with `kappaf = sqrt2` AND
`muf_min /= sqrt2` (the non-knot reference the 2026-08-25 logbook validated at
K = 2 to 9e-16). |Y| [0, 0.15], live rules, `n_train = 9`,
`target_precision_rel = 1e-4`, both arms from the SAME build and the SAME
member convolutions.

```
  qT bin      true resp    dev 3-knot    dev 5-knot     (dev = model/runcard - 1,
 [  8,  9]   -4.49e-05     +6.04e-05     -8.43e-06       as a fraction of sigma)
 [ 18, 20]   +3.40e-03     +1.44e-03     -1.83e-05
 [ 20, 24]   +7.81e-04     +2.94e-03     -2.53e-05
 [ 24, 28]   +2.16e-03     -1.00e-03     -2.46e-05
 [ 28, 33]   +1.22e-03     -1.46e-04     -3.02e-05
 [ 33, 44]   +1.30e-03     +3.13e-06     -3.60e-05
  max|dev|                  2.944e-03     3.597e-05      82x
```

**Read it as two things.**
1. A CONSTRUCTION CHECK: the half-step members land exactly where the kernel's
   knot formula puts them, floor compensation included. The residual 3.6e-05 is
   flat in qT and is the parameter-route / runcard-route reproducibility floor,
   not an interpolation error. Decision 3 is confirmed.
2. A RESULT IN ITS OWN RIGHT: the shipped model is **0.3% of sigma wrong at
   kappa_F = sqrt(2)** and no validation we own could see it, because every muF
   check sits AT kappa_F = 0.5 or 2 where a quadratic returns the stored member
   bit for bit. Five knots removes that.

**What would overturn it.** Nothing in the same measurement; a different
reference construction (e.g. forgetting to scale `muf_min`) would.

---

## 6. The five-knot stencil does NOT fix the transitions at the TEMPLATE variation, and the geometry says why

**Measured**, x2 = 0.35 (the FINITE leg the CorrZ templates carry), same
process, same rules, model against an exact runcard refill:

```
  qT bin      true resp     dev 3-knot   % of resp    dev 5-knot   % of resp
 [ 18, 20]   -4.136e-04    +1.099e-04     -26.6%     -1.081e-04     +26.1%   (*)
 [ 20, 24]   -3.075e-03    +9.801e-04     -31.9%     +3.493e-04     -11.4%
 [ 24, 28]   -7.840e-03    -8.539e-04     +10.9%     +6.775e-04      -8.6%
 [ 28, 33]   -1.822e-02    -2.151e-03     +11.8%     +3.144e-04      -1.7%
 [ 33, 44]   -3.301e-02    -3.040e-04      +0.9%     +3.820e-03     -11.6%
  max|dev|                  2.151e-03                 3.820e-03
```
(*) [18,20]'s true response is 4e-04, at the node-ladder target -- not usable.

Three of five bins improve (by 2.8x, 1.3x, 7x), [33,44] gets **12x worse**, and
the worst bin over the set goes 2.15e-03 -> 3.82e-03. **Net: worse.**

**The 3-knot column reproduces the previously published numbers**
(-26.6 / -29.2 / +10.9 / +11.8 / +1.5 % in the 2026-08-25 webdir README) bin by
bin, which is the check that the `knots_used = 2` clamp is faithful on a live
build as well as on a cache.

**WHY -- and this is the finding, not the number.** `fiveknot_stencil_geometry.py`
computes, from SCETlib's own scale formulas and with no calculation run, the
per-node displacement D = ln[muF(x2 = 0.35)/muF(anchor)] against the knot
positions. In units of ln f = ln 2:

```
  qT     D/ln f over bT = 0.1 .. 5        where the model is evaluating
  19       0.004 .. 0.033                 deep INSIDE the inner knots
  22       0.085 .. 0.510                 inner..outer, extrapolating at bT >= 2
  26       0.300 .. 0.991                 at the OUTER knot by bT 0.8
  30       0.536 .. 1.190                 EXTRAPOLATING from bT 0.5 up
  38       0.759 .. 1.154                 EXTRAPOLATING at essentially every node
  60       0.241 .. 0.282                 back inside
```

At the template's own variation size the transition-induced shift **reaches and
exceeds the outer knot** for qT ~ 26-44. There the model is not interpolating
between knots, it is EXTRAPOLATING past kappa_F = 2 -- and a quartic
extrapolates worse than a quadratic, which is exactly the sign and the location
of the [33,44] degradation.

**So "more knots" is the right medicine for the wrong ailment at this variation
size.** Interior knots refine the interior; the finite template leg is outside.

**What would overturn it.** A five-knot arm that improved [33,44] -- it does
not -- or a demonstration that the dominant bT nodes at qT 38 are the small-bT
ones where D/ln f < 1 (the geometry says D/ln f = 0.76 already at bT = 0.1).

**The prediction this makes, and which is being tested next:** at the
NEAR-ANCHOR variation (x2 = 0.55, ~12x smaller, what a FIT actually uses) D is
~12x smaller, so every node is deep inside the inner knots and five knots must
be uniformly better. If that comes out, the honest summary is "five knots helps
the fit derivative and kappa_F between knots, and does not help the template
closure", which is a different -- and more useful -- statement than either
"it works" or "it does not".

---

## 7. NEAR-ANCHOR (the regime a FIT uses): five knots nearly removes the interpolation error, and EXPOSES a separate floor

x2 = 0.55, ~12x smaller than the template leg. Same process, same rules, same
runcard reference; error as a fraction of the TRUE response.

```
  qT bin      true resp    3-knot    5-knot      gain
 [ 18, 20]   -3.47e-05    -36.5%     -4.2%       (true resp 3e-05: NOT USABLE)
 [ 20, 24]   -2.70e-04    -40.9%    -14.3%       2.9x
 [ 24, 28]   -6.60e-04    +27.1%    +28.2%       1.0x  <-- does not move
 [ 28, 33]   -1.61e-03     +8.4%     +0.3%       33x
 [ 33, 44]   -4.01e-03     +3.6%     +0.6%       6x
  max|dev| of sigma        1.79e-04  1.86e-04
```

**Three of four usable bins fall to <= 0.6% .. 14% of their own response**; one
does not move at all. `max|dev|` is therefore FLAT, and quoting only that number
would hide both halves of the result.

**[24,28] is an order-INDEPENDENT floor, and it was predicted.** The 2026-08-25
webdir README already measured a "spacing-independent floor of about 1-2e-04 per
bin" at exactly this bin and this variation (+27.1% at f = 2, +26.3% at
f = sqrt2). Five knots reproduces it (+28.2%) at 1.86e-04 of sigma. So it is not
the interpolation ORDER and not the knot SPACING. The two named candidates, from
the same README, are:
  * `node_cval`, the rule's bin-level constant, which has no bT node and so
    interpolates on the GLOBAL kappa_F label -- its response to x1..x3 is
    identically ZERO. Its measured upper bound at qT [24,28], |Y| < 0.5, is
    max|dc|/sigma = 2.3e-04 .. 3.2e-04, which BRACKETS the 1.86e-04 left over.
  * the reference's own node-ladder target, 1e-04 relative.
**The experiment that separates them:** zero the `node_cval` member
interpolation and re-measure this bin. If the 1.86e-04 moves, it is c_val; if it
does not, it is the reference. Neither has been done -- this is named as the
next measurement, not as a conclusion.

**What would overturn the rest of it.** A finer reference (target_precision_rel
below 1e-4) that moved [28,33] or [33,44]; they are quoted at 0.3% and 0.6% of
their own response, which is close enough to the floor to be worth checking.

---

## 8. WHY the two regimes disagree, in one sentence, with the figure that shows it

The interpolation error is a Lagrange remainder in the per-node displacement D.
Five knots refines the INTERIOR of the stencil. The near-anchor variation lives
in the interior (|D| <= 0.13 ln f at qT 38); the finite template leg does not
(|D| reaches 1.15 ln f at qT 38, i.e. outside kappa_F = 2). Refining the
interior cannot help a point outside it, and a quartic extrapolates worse than a
quadratic -- so the same change improves one regime and degrades the other.

Figure: `mechanism/stencil5_qT_*.png` -- per-node D against all three knot
bands, arithmetic from SCETlib's scale formulas, no calculation run.

**Decision taken from it:** test a WIDE five-knot geometry, kappa_F = 1/4, 1/2,
1, 2, 4, which keeps 1/2 and 2 exact (the templates' and the fit's points) and
BRACKETS the finite variation instead of refining the interior. Implemented as
`muf_nmem = -4`; the sign, rather than a new field, carries the geometry because
`sizeof(ad::GlobalData)` is the rule-cache guard. Prototype encoding, flagged as
such in the code: if wide is what ships it should become a real field with a
cache version bump.

---

## 9. The WIDE geometry (kappa_F = 1/4, 1/2, 1, 2, 4) is DEAD

**Measured**, x2 = 0.35, same script, same reference, same process:

```
  qT bin      true resp     dev 3-knot   % of resp   dev 5-knot WIDE   % of resp
 [ 18, 20]   -4.136e-04    +1.099e-04     -26.6%      -1.720e-02       +4158%
 [ 20, 24]   -3.075e-03    +9.725e-04     -31.6%      -1.036e-01       +3368%
 [ 24, 28]   -7.840e-03    -8.539e-04     +10.9%      -2.601e-01       +3318%
 [ 28, 33]   -1.822e-02    -2.151e-03     +11.8%      -3.145e-01       +1726%
 [ 33, 44]   -3.301e-02    -4.129e-04      +1.3%      -3.092e-01        +936%
  max|dev| of sigma          2.15e-03                  3.15e-01
```

Not a degradation: a failure. **31% of sigma.** The 3-knot column of the same
run reproduces the earlier three-knot numbers, so the build and the clamp are
fine and the failure is in the wide arm alone.

**It is NOT numerical conditioning.** The wide knot positions at
qT 38 / bT 5 are {-1.167, -0.614, 0, +0.651, +1.324} -- well separated, and the
Lagrange weights at the actual displacement d = 0.80 are O(1)
(+0.05, +1.11, -0.22, +0.08, -0.01, summing to 1). Computed by hand from
`fiveknot_stencil_geometry.py`.

**The likely reason, stated as a hypothesis with its test.** The kernel does not
interpolate a physical function alone: it interpolates the member convolutions
AND the rule's per-site weights `Var::w`, which are RE-SOLVED per member by
`rule_min_norm_update`. Those weights are a numerical artefact of the rule, not
a smooth function of ln muF, and a quartic through five of them spread over a
factor of SIXTEEN in muF has no reason to behave. Narrow keeps every member
close to the anchor and does not provoke it.
**The test that would settle it** (not yet run): interpolate the conv blocks at
5 knots while holding `wsite` at the 3-knot quadratic, and see whether the 31%
survives. If it does, the conv side is to blame; if it does not, the re-solved
weights are.

**Decision.** Do not pursue the wide geometry. It is kept in the branch behind
`muf_nmem = -4`, documented as measured-bad, so that nobody re-derives it.

**What would overturn it.** A version that stabilises the weight interpolation
(e.g. re-solving ONE weight vector against all members jointly instead of one
per member) might make a wide stencil viable. That is a much larger change than
"two more members" and is not what was proposed.

---

## 10. Threads and node conditions (for reproducing any of this)

The node carried SEVEN other heavy SCETlib cache builds all evening (another
session's `ntrain_gate` jobs); load average 400-600 of 768 cores and 23000 of
the 32768 per-user threads in use.
 * live-rule interpolation tests (`fiveknot_interp_error.py`,
   `fiveknot_kappaF_error.py`): `--threads 16` for the first two, `--threads 8`
   afterwards. 4 min each on an idle node, 10-25 min under this load.
 * the 80-bin subset cache: `--threads 64`.
 * `validate_variations` / `fiveknot_closure`: `--threads 32`.
Nothing here is thread-count sensitive in its RESULT -- both arms of every A/B
run in the SAME process -- but the wall times below are not reproducible on an
idle node.

---

## 11. RETRACTION: entry 9 said "the WIDE geometry is DEAD (measured bad)". IT IS NOT MEASURED AT ALL.

**What entry 9 claimed:** the wide stencil (kappa_F = 1/4, 1/2, 1, 2, 4)
returns 31% of sigma at x2 = 0.35, therefore the geometry is bad.

**Why that was wrong.** The wide stencil FAILS ITS OWN KNOT TEST. kappa_F = 4
is one of its knots, so the model must be exact there; it returns **-3.7e+08**
(`runcard_ref/kf4_wide_v2.log`). A stencil that cannot reproduce its own knot
is not measuring the geometry, it is reporting a defect in the prototype. The
31% is a symptom of that defect and must not be quoted as a property of the
wide geometry.

**What was fixed along the way, and what it did NOT fix.** Chasing it found a
real defect: the member-degeneracy guard used an ABSOLUTE tolerance
(1e-8 x ln f). Where the muf_min floor dominates -- qT just above x1*Q, where
1 - g falls through 1e-4 -- every knot position collapses together while
staying far above that cut, so the DIFFERENCES the Lagrange denominators are
built from are pure rounding. Three knots survives because its guard also tests
the outer separation; five does not. The guard is now relative to the spread the
node actually has. **It does not repair the wide arm** (kappa_F = 4 still
-3.7e+08), so there is a second defect that this round did not localise.

**What the fix does not change, re-run and checked:** the 39-direction no-op on
cache_260824b still reproduces every published number, and the narrow closure
table is BIT-IDENTICAL before and after. So the guard was never biting in the
narrow arm; the narrow results stand, and the x1,x3 -> 7.6e-01 there is genuine
extrapolation, not a guard artefact.

**Status of the wide geometry: UNVALIDATED.** Kept behind `muf_nmem = -4`,
labelled as such in the code and the commit message.

**What would settle it.** Localise the second defect -- the two candidates are
the per-member re-solved `Var::w` (a numerical artefact of the rule rather than
a smooth function of ln muF, here interpolated across a factor of sixteen) and
the `-4` encoding path itself, which is the least-exercised code in the patch.
The separating experiment is the one already named in entry 9: interpolate the
conv blocks at five knots while holding `wsite` at the three-knot quadratic.

**Why this is recorded rather than quietly corrected.** Several wrong
diagnoses have already been published in this study, one needing a public
correction. Entry 9 was written before the knot test existed and was one edit
away from going into the logbook as a measurement.

---

## 12. What NOT to do next, and what to do

**Do not merge five knots to fix the transitions.** It does not. `92f1299`, the
muF member coordinate fix (MR !8), still stands on its own merits and is
unaffected.

**The branch `muf-five-knots` (61123f2) is pushed and NO merge request was
opened.** The brief said to prepare one if it worked; on the question asked it
did not. If it is ever wanted it is for a different reason -- kappa_F between
knots (82x) and the fit derivative (3-33x) -- and that is Luca's call, not a
consequence of this measurement.

**The measurement that should come next, in order:**
 1. `node_cval` at qT [24,28], x2 = 0.55: zero its member interpolation and see
    whether the 1.86e-04 order-independent floor moves. Cheap, decisive, and it
    is the last unexplained piece of the near-anchor error.
 2. The analytic `d(conv)/d(ln muF)` column. Its case is now stronger than
    before, for a specific reason: the stencil geometry shows the displacement
    LEAVES the stencil at exactly the variation size the templates use, and a
    first-order-exact construction is the only one that does not care.
    Open question it must answer: whether ONE column suffices where
    D ~ 1.15 ln f, or a second derivative is wanted.

---

## n_train gate (agent, 2026-08-25 night)

# DECISIONS -- `--n-train` gate for the 62-member (29 PDF eigenvector pair) cache

Agent: n-train gate. Started 2026-08-25 21:20. Scratch:
`/home/submit/lavezzo/.claude/jobs/140d052c/tmp/ntrain/`.
Caches under `/ceph/.../scetlib_ad_caches/ntrain_gate/`.
Webdir: `~/public_html/alphaS/260825_scetlib_ad_ntrain_gate/`.

Every entry: WHAT / WHY / EVIDENCE / WHAT WOULD OVERTURN IT.


## SUMMARY OF THE DECISIONS BELOW

| # | decision | one-line evidence |
|---|---|---|
| D13 | **Use `--n-train 9`** (the default). Do not raise it, do not lower it. | 9 -> 27 is flat within a measured +-10-14% build-to-build floor in every group; 9 -> 5 is 9.3x worse in NP lambda |
| D27 | **In sigma(alpha_s) units:** at n-train 9 the rule error is **1e-5 sigma** where the fit sits and **0.003 sigma** at 8x the template step; at n-train 5 it is **0.024 sigma**, the top of the transition band | fig9 / T18 |
| D20/D21 | The "9/53 = 0.17 is under-determined" premise is BACKWARDS | the solve's unknowns are SITE WEIGHTS; P is in the rows. Constraints per unknown on the real 210-bin card: **1.51 at P=24, 3.48 at P=53** |
| D16 | **The build cost is set by the INTEGRATION TOLERANCE, not by n_train** -- a 13x lever nobody costed | 210-bin 4-member fixed-order stage: 54.8 min at rel 1e-3 vs **715.6 min** at the production rel 1e-4 + abs 0 |
| D15 | The Hessian's "3.2x for two extra parameters" is REFUTED -- it was node contention | interleaved one-process A/B: P 24 -> 26 is **x1.09**, P 24 -> 53 is x2.95. Projected 210-bin P=53 hessian ~4-5 min |
| D15 | The uncommitted `py/scetlib_tf.py` in the shared tree changes every Hessian by **152%** | toggling `_rule_is_matched` -- commit it before the build |
| D19a | The live route is BLIND to the eigenvector coefficients | `pdf_eig0 = +1` gives `max|v/v0-1| = 0.000e+00` |
| D19b | Thin bins are BETTER, not worse | per-bin, within one build, log-log corr(sites, error) = **+0.78** |
| D22 | RETRACTED: "n_train 5 shifts sigma(alpha_s) by 1%" | the build-to-build floor on that quantity is 0.70%; the test resolves nothing |
| D23 | CORRECTED: "n_train 5 would make the build ABORT" is too strong | the guard is a residual check; `thin_nt5` ran fine at 159 sites against m = 163 |
| D28 | **The thin-bin hedge is CLOSED, in the opposite direction to the worry** | the card's thinnest corner is **46x BETTER** than the corner the scan used, and 4.03 constraints per unknown against 2.65 |
| D23 | CORRECTED: `thin_nt5` has 3 of 4 bins BELOW the m=163 constraint count and did not abort | too small an n_train degrades SILENTLY, it does not refuse |
| D8/D12 | Two experiments that did NOT work, and why | the low-qT template metric is saturated by the nonsingular-cutoff difference; rule_vs_direct v1 had unphysical displacements and transition contamination |

Numbers: `ntrain/TABLES.md`. Figures: `~/public_html/alphaS/260825_scetlib_ad_ntrain_gate/`.

---

## D1. Build on the previous agent's `eig_test` caches instead of rebuilding them

**WHAT.** Reuse `/ceph/.../scetlib_ad_caches/eig_test/{ref0a,ref0b,ref0c_t64,
smoke_eig2,eig29_nt5,eig29_nt9,eig29_nt27,y20_ref0,y20_eig29,lowqt_ref0,
lowqt_eig29}` and their `val_*.log`, and only build what is missing.

**WHY.** They are a complete, same-day, same-SCETlib-build family (`build-fix`,
`libscet-qT.so` of 2026-08-25 09:20) on one runcard; rebuilding would cost hours
and would ADD a build-to-build irreproducibility term (3.1e-05 in sigma,
3.0e-03 in the Jacobian) to every comparison for no gain.

**EVIDENCE.** `eig_test/base.conf` is the 210-bin production `base.conf` with
exactly one edit (`target_precision_rel 1.e-4`, identical to production p4);
`diff` against `cache_260824b/base_from_reference.conf` shows only that line.

**WOULD OVERTURN.** If any of those caches turns out to have been built against a
different SCETlib library than the one the eigenvector build will use.

---

## D2. `eig29_nt27` existed but was never validated -- validating it is the FIRST
   thing, because it can settle the question on its own

**WHAT.** Run `validate_variations.py --partial` on the already-built
`eig29_nt27` (4 bins, P=53) before building anything new.

**WHY.** The previous agent's table left `n_train = 27` as `(PLACEHOLDER)` for
every accuracy column and concluded "keep 9" from the ROW COUNT argument and the
memory cost, not from a measured response accuracy. That is precisely the
inference the brief forbids ("a small training residual on an under-determined
solve proves nothing"). n_train 27 is 3x the default, so if 27 does not beat 9
against the production templates, the scan is answered at its expensive end
first and everything else is refinement.

**EVIDENCE.** `tmp/LOGBOOK_eigenvector_paste.md` section 3, table rows for 5 and
27 are placeholders; `eig_test/eig29_nt27/cache.npz` (105.8 MB) exists and its
build log reports "rules built in 135.3 min (median 719 nodes/bin)".

**WOULD OVERTURN.** Nothing -- this is a measurement, not a choice.

---

## D3. Figure of merit = `validate_variations.py --partial` max|dev| per GROUP
   against the production corr files, NOT the build-time training residual

**WHY.** The training residual is the in-sample fit of the rule solve. Under-
determination shows up as good in-sample fit and bad out-of-sample response,
which is the failure mode being tested. The response test is out-of-sample by
construction: the templates sit at finite variation size (lambda2 = 1.0 is 2.5x
the anchor, kappa_F = 0.5/2.0, c_e = +-1), not at the anchor where `c_val`
forces exactness regardless of `n_train`.

**EVIDENCE.** Logbook 2026-08-20 (late): "`c_val` forces exactness AT the anchor
regardless, which is why anchor checks and training residuals say nothing about
generalisation."

**WOULD OVERTURN.** Nothing.

---

## D4. Reference for "is this difference real": three independent n_eig = 0 builds

**WHAT.** Quote every n_train difference against the spread of `ref0a`, `ref0b`,
`ref0c_t64` -- same runcard, same bins, three separate processes.

**WHY.** The builder is not reproducible (median nodes/bin 357/359/359/371 over
four identical builds), so an A/B between two separately built caches has a
floor. The floor must be quoted in the SAME units as the comparison, i.e. as
`validate_variations` max|dev| per group, not as the sigma/Jacobian numbers in
the knowledge note.

**EVIDENCE.** `knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md`;
the three ref0 logs give per-group floors 7.7e-07..1.0e-06 (lambda),
1.78..1.93e-07 (TNP), 1.32..1.38e-04 (muF/kappa_R), 1.64..2.74e-03
(transitions), 1.88e-05 (alphaS, identical to 3 digits).

**WOULD OVERTURN.** Nothing; it is the floor by construction.

---

## D5. Bins: the CHEAP high-qT central corner `0,1/16,17` for the scan, plus the
   HARD low-qT corner `0,1/1,2` as the stress test

**WHAT.** Run the n_train scan on |Y| < 0.3, qT in [20,28] (4 bins), and check
the conclusion against |Y| < 0.3, qT in [1,3] (4 bins).

**WHY.** (a) cost: the cheap corner's member stage is 2.3 min against ~25 min for
ptV 18,19,20, and the lowest-qT bin alone costs more than all the others
together; (b) attribution: the cheap corner excludes qT [0,1] entirely, so the
OPEN nonsingular-cutoff difference (ours 0.1 GeV, the production templates 1.0
GeV) cannot contaminate a single number; (c) the honest hedge the brief asks
for is exactly "can this degrade elsewhere on the 210-bin card", and the low-qT
corner is where the known residual lives AND where the site count is thinnest
(228 sites/bin at nt9 against 364 in the cheap corner), i.e. closest to the real
card's thin end (min 223 / median 292 at P=24).

**EVIDENCE.** `eig_test/build.sh` header; build logs' "median N nodes/bin".

**WOULD OVERTURN.** If the two corners disagreed about n_train, the scan would
have to be repeated on a representative sample of all 210 bins.

---

## D6. Measure the EIGENVECTOR per-member cost at 210 bins directly, at
   `target_precision_rel = 1e-3`, as two shard builds

**WHAT.** Two full-210-bin builds, `--pdf-eig 29 --n-train 9 --threads 210`,
differing only in `--members`: `0:4` (eigenvector pairs 0 and 1, 4 members) and
`58:62` (the alphaS pair + the muF pair, 4 members). Launched concurrently.

**WHY.** The ~14 h / 15 h projection came from `cache_260824b`, whose 4-member
fixed-order stage (54.8 min, 13.7 min/member) was 2 alphaS + 2 muF members --
NOT PDF members. `--members 58:62` reproduces exactly that member set under
tonight's load, and `--members 0:4` is the same everything with eigenvector
members instead, so the RATIO is a controlled within-night measurement and the
absolute is directly comparable to the 13.7 that the projection used.
`target_precision_rel = 1e-3` is chosen because that is the setting
`cache_260824b` used; comparing against it at any other tolerance would confound
the member class with the tolerance.

**WHY CONCURRENT.** Any contention from the rest of the node hits both equally,
so the ratio -- the quantity item 4 needs -- is protected even if the absolutes
drift.

**EVIDENCE.** `cache_260824b/build.log`: "0 PDF eigenvector pairs for the
resummed piece in 1.6 min / ... and for the fixed-order piece in 54.8 min",
`--threads 210`, `target_precision_rel = 1.e-3`.

**WOULD OVERTURN.** If `--members 58:62` does not reproduce 54.8 min to within
~30%, tonight's load is not comparable to that build's and only the ratio may be
quoted.

---

## D7. Treat the INTEGRATION TOLERANCE as a separate, and much larger, cost axis
   than n_train -- and measure it on identical bins

**WHAT.** Also build the 4-bin cheap corner at `target_precision_rel = 1e-3`
with `--pdf-eig 29 --n-train 9`, to sit against the existing 1e-4 build of the
same 4 bins.

**WHY.** The production 210-bin cache `cache_260825_p4` runs at
`rel = 1e-4, abs = 0` and its stages were 325.3 min (node set) and 715.6 min
(4-member fixed order) -- 14.9x and 13.1x the 1e-3 build `cache_260824b`
(21.9 and 54.8 min) on the same card, same `--threads 210`. If the eigenvector
build uses production settings, the member loop is not 9-15 h but of order 100 h,
and that dwarfs anything `--n-train` does. This is a discrepancy in the premise
of the task and has to be measured, not assumed. Doing it on the identical 4 bins
removes the "different day / different load" objection to the p4-vs-260824b
comparison.

**EVIDENCE.** the two build logs; `cache_260825_p4/build.sh` documents the
`target_precision_abs 1.e-8 -> 0.` change ("relaxed on Josh's advice").

**WOULD OVERTURN.** If the 4-bin A/B does not reproduce a ~13x factor, then the
p4 build was load-contaminated and the projection reverts to the 1e-3 numbers.

---

## D8. The low-qT corner CANNOT test `n_train` through the template metric.
   Recorded as a thing that did not work.

**WHAT.** Dropped the plan to run the n_train scan at qT 1-3 GeV against
`validate_variations.py`.

**WHY.** At qT 1-3 GeV the residual against the production templates is
dominated by a difference in the CALCULATION, not by the rule: our nonsingular
vanishes below qT = 0.1 GeV, the production templates' below 1.0 GeV. Both
builds carry it identically, so the metric there is a constant, not a
measurement of compression.

**EVIDENCE.** `lowqt_ref0` (P = 24, 24 params) and `lowqt_eig29` (P = 53), two
INDEPENDENT builds, agree row for row to the printed 3 digits on 38 of 39
shared variations (`mufdown-kappaFO0.5-kappaf2.` differs in the 4th digit of the
model range only). Per group: NP lambda 6.67e-04 both, TNP 1.26e-04 both,
muF/kappa_R 3.54e-03 both, alphaS 5.09e-04 both. Two independent builds cannot
agree that well on a rule-limited quantity -- the build-to-build floor is 1e-4
in sigma -- so the residual is a common physics term. The three transition
variations are identically 1.0000 in BOTH model and reference there, i.e. the
transitions do nothing at qT < 3 GeV and carry no information at all.

**REPLACEMENT.** `ntrain/rule_vs_direct.py`: compare the rule replay against a
LIVE `sigma_binned_batch` of the same calculation at the same points. No
template, so no cutoff mismatch, and it works in any qT region.

**WOULD OVERTURN.** Aligning our nonsingular cutoff to 1.0 GeV would make the
low-qT template metric informative again.

---

## D9. Add a JOINT-displacement test, because every production template is
   single-direction and a fit is not

**WHAT.** `rule_vs_direct.py` evaluates, besides one-direction-at-a-time points,
random points with ALL rule directions displaced simultaneously, at 1x, 2x and
4x the template displacement.

**WHY.** This is the actual content of the under-determination worry. `n_train`
points sample the P-dimensional parameter space jointly; 9 points in 53
dimensions can reproduce every single-axis probe (the value row plus P gradient
rows pin the axes) while failing on a generic joint displacement. Every
production template moves ONE direction, so `validate_variations.py` cannot see
that failure mode even in principle. A fit moves 18+ at once.

**EVIDENCE.** The rows the solve is given are `1 + n_train * (1 + 2P)` -- a value
row, P gradient rows and P HVP rows per training point -- so the AXES are
constrained by construction and only the joint/cross structure depends on how
many points there are.

**WOULD OVERTURN.** Nothing; it is an added test. If joint and single agree, the
worry is empirically dead rather than argued away.

**EXCLUSION.** The member-interpolated directions (`pdf_eig*`, `alphas`,
`scale_kappa_F`) are ZEROED in this test (`--rule-only`). They do not come from
the `--n-train` solve at all: `build_pdf_variations` re-solves with its own
`n_train_var = 3` and is exact at `c_e = +-1` by construction of the quadratic
member interpolation. Including them would dilute the measurement with a
mechanism `--n-train` does not control.

---

## D10. ONE direct run serves every `n_train`

**WHAT.** `--mode direct` is run once, on `eig29_nt9`'s runcard, and every rule
run is compared against that single file.

**WHY.** `--n-train` is a build-time flag; it does not appear in the runcard.
All four caches on the cheap corner therefore share bins, anchor, parameter
names and integration tolerance, so the live calculation is the same function
for all of them. Running it once also removes the direct route's own
irreproducibility from the n_train comparison -- every n_train is measured
against the SAME reference numbers, so differences between them are pure rule.

**EVIDENCE.** `diff` of the four `cache.conf` files (identical); `--n-train`
appears only in the npz metadata.

**WOULD OVERTURN.** Nothing.

---

## D11. The "Hessian rises 3.2x for two extra parameters" premise is a THRESHOLD,
   not a scaling law -- and the numbers to check it already existed

**WHAT.** Re-derived the P-scaling of the Hessian from `backend_check` logs the
previous agent had already written, and confirmed it with contention-robust
interleaved A/B.

**EVIDENCE.** `backend_check` warm value+jacobian x its own reported Hessian
ratio, 4 bins each:
  P = 24, n_eig = 0  (`bc_ref0b.log`)     122 ms x  66 =  8.1 s
  P = 26, n_eig = 2  (`bc_smoke.log`)     205 ms x 124 = 25.4 s
  P = 53, n_eig = 29 (`bc_eig29_nt9.log`) 156 ms x 162 = 25.3 s
The 8.1 -> 25.4 s step quoted in the brief is 24 -> 26 params, and 26 -> 53
params is 25.4 -> 25.3 s, i.e. FLAT. Interleaved A/B in one process
(`ev_P24_vs_P53_4bin.log`): value+jacobian 47.5 -> 62.4 ms (x1.31), Hessian
4044 -> 11926 ms (x2.95) for P = 24 -> 53.

**READING.** The cost step is switching PDF eigenvector members ON at all
(n_eig 0 -> 2), not the number of parameters. Extrapolating 3.2x-per-2-params to
P = 53 would have predicted ~10^6 s and is simply the wrong functional form.

**WOULD OVERTURN.** A measurement at n_eig = 10-20 that does NOT sit at the
n_eig = 2 value would mean there is a slow growth on top of the step. The
interleaved P = 26 vs P = 53 A/B now running is exactly that check.

---

## D12. `rule_vs_direct.py` v1 THROWN AWAY -- what did not work, and why

**WHAT.** The first version of the generalisation test produced NaNs at 2x and
4x displacement and a joint-point deviation of 5e-02 that was IDENTICAL at
n_train 5, 9 and 27. Rewritten (v2) with an explicit physical box per parameter,
template-derived asymmetric displacements, and the direction families reported
separately.

**WHY IT FAILED.** (a) symmetric displacements: `np_eff_lambda2` sits at 0.4 with
a template endpoint at 1.0, so a symmetric "1x down" was -0.2 -- negative lambda,
which the model turns into NaN (the known negative-lambda4 trap), and 2x down on
`scale_kappa_R` was kappa_R = 0. (b) the three transition directions were mixed
into the joint points, and they carry a rule-vs-live difference of ~1.0e-01 at
1x that does NOT move with n_train (9.989e-02 / 1.002e-01 / 1.003e-01 at
n_train 5 / 9 / 27), so they set the worst-point value for every configuration
and hid everything else.

**WHAT v1 DID SHOW, and it is worth keeping.** With the transitions excluded, the
MEDIAN single-direction rule-vs-direct deviation does move with n_train, and
monotonically: 2.61e-07 (nt5) -> 1.49e-08 (nt9) -> 9.40e-10 (nt27). So the rule
solve genuinely does get better with more training points -- by 2 orders of
magnitude from 5 to 27 -- at a level 3 to 5 orders below the residual the
PRODUCTION TEMPLATES can resolve. That is the whole answer in one line: n_train
improves a quantity that is already negligible.

**AND A HANDOVER.** The ~1e-1 rule-vs-live gap on `scale_x1` at 1x, flat in
n_train, is a route difference, not a training deficiency. It belongs with the
transition-derivative work (the muF member coordinate / five-knot stencil), not
here. Attribution is not complete: it could be the frozen fixed-order piece the
rule carries (`rule.fo_w`) against the live route recomputing the nonsingular at
the new transition point, or the known frozen-beam-convolution bug. THE
EXPERIMENT THAT WOULD SEPARATE THEM: rebuild a cache from a RUNCARD with
`transition_points = [0.15, 0.6, 1.0]` and compare its anchor against the
parameter route at `scale_x1 = 0.15` -- the runcard route refills the nodes, the
parameter route cannot, and the difference is the frozen-convolution term.

---

## D13. RECOMMENDATION: keep `--n-train 9`. Do not raise it, do not lower it.

**WHAT.** The 62-member eigenvector build should use the default `--n-train 9`.

**WHY.** Two independent measurements agree, and they disagree with the
upstream heuristic `max(9, ceil(1.5 P)) = 80` for a reason that is now
understood.

**EVIDENCE 1 -- against the production templates (the figure of merit).**
4 bins, P = 53, worst max|dev| per group; the "floor" column is min..max over
three independent n_eig = 0 builds of the identical runcard:

| group | nt 5 | nt 9 | nt 14 | nt 27 | 3-build floor |
|---|---|---|---|---|---|
| NP lambda (8)   | 6.08e-06 | 6.53e-07 | 5.60e-07 | 5.72e-07 | 7.7e-07 .. 1.0e-06 |
| TNP (20)        | 2.90e-07 | 1.96e-07 | 1.89e-07 | 1.88e-07 | 1.78 .. 1.93e-07 |
| muF/kappa_R (6) | 1.57e-04 | 1.40e-04 | 1.39e-04 | 1.39e-04 | 1.32 .. 1.38e-04 |
| transitions (3) | 4.43e-03 | 2.17e-03 | 1.66e-03 | 1.76e-03 | 1.64 .. 2.74e-03 |
| alphaS (2)      | 1.88e-05 | 1.88e-05 | 1.88e-05 | 1.88e-05 | 1.88e-05 (all 3) |
| PDF eig (58)    | 1.50e-06 | 1.50e-06 | 7.65e-07 | 1.50e-06 | -- |

From 9 upward every group is flat INSIDE the build-to-build floor, and alphaS
-- the number the analysis exists for -- is identical to three digits at every
n_train. Below 9 the NP lambda response degrades by 10x, out of the floor.

**EVIDENCE 2 -- against a LIVE evaluation, no template (the sharper test).**
Worst over 12 random JOINT points, all directions of the family displaced at
once, at 1x the production template step:

| set | nt 5 | nt 9 | nt 14 | nt 27 |
|---|---|---|---|---|
| NP joint 1x  | 6.98e-06 | 6.03e-07 | 5.80e-08 | 4.63e-08 |
| TNP joint 1x | 4.92e-07 | 4.19e-08 | 1.61e-08 | 1.45e-08 |
| NP joint 8x  | 8.88e-04 | 2.17e-04 | 5.27e-05 | 2.84e-05 |

So the rule solve DOES keep improving past 9 -- by 10x from 9 to 14. It
improves a quantity that at n_train 9 is already 6e-07, i.e. 200x below the
muF/kappa_R residual (1.4e-04) and 3600x below the transition residual
(2.2e-03) that actually limit the model. Buying 10x on the smallest error in
the stack changes nothing measurable, which is exactly what EVIDENCE 1 shows.

**WHY THE 9/53 = 0.17 RATIO WAS THE WRONG QUANTITY.** The solve is not
n_train points against P unknowns. Each training point contributes a value row,
P gradient rows and n_hvp x P HVP rows, so
`rows = 1 + n_train*(1 + 2P)` -- 442 at P = 24 and **964 at P = 53**, both at
n_train = 9. The row count already scales with P; the ratio does not need to.

**COST OF RAISING IT (all measured, 4 bins, P = 53):**

| | nt 5 | nt 9 | nt 14 | nt 27 |
|---|---|---|---|---|
| retained nodes/bin | 220 | 364 | 507 | 719 |
| rules blob (4 bins) | 180.6 MB | 299.0 MB | 410.1 MB | 588.7 MB |
| fit value+jacobian | 32.8 ms | 52.9 ms | 76.7 ms | 122.5 ms |
| fit hessian | 6.47 s | 10.89 s | 15.59 s | 25.29 s |
| loaded model RSS | 1618 MB | 2058 MB | 2500 MB | 3173 MB |

n_train 9 -> 27 doubles the retained nodes and therefore doubles the cache
(2.5 -> 5.0 GB npz, 14 -> 28 GB uncompressed), doubles the fit's RAM
(55 -> 108 GB), doubles every fit iteration and doubles the covariance pass.
The rules STAGE also grows superlinearly (7.0 -> 135.3 min on 4 bins measured
under mixed load, ~n_train^2.7), but that is the least of it.

**WHY NOT LOWER.** n_train = 5 both degrades the response (above) and takes
the retained nodes to 220 on OUR bins; the member re-solve raises
"Fewer sites than constraints" when a bin has fewer than
`1 + n_train_var*(1 + P) = 1 + 3*54 = 163` at P = 53, and the real card's
thinnest bins already sit at ~223 nodes at n_train 9. Scaling 220/364 = 0.60
onto them gives ~134 -- the build would ABORT, not degrade.

**WHAT WOULD OVERTURN IT.** A demonstration that a residual of order 1e-06 in
the NP-lambda or TNP response moves sigma(alpha_s). It cannot: the alphaS
templates themselves are reproduced at 1.88e-05 independent of n_train, and
the residual-to-alpha_s projection already in the study
(`residual_structure_map.py`) scores the far larger transition residual at
0.002-0.025 sigma. Equally, if the production card were changed to bins much
thinner than 220 retained nodes, the n_train = 5 row shows what happens.

---

## D14. Test the recommendation where the real card is THINNEST, not only where
   it is cheap -- the honest hedge, made quantitative

**WHAT.** A second 4-bin scan at `--subset '0,1/5,6'` = |Y| < 0.3,
qT 5-7 GeV, at n_train 5 / 9 / 14 plus two independent n_eig = 0 builds for the
floor.

**WHY.** The scan so far lives on `0,1/16,17`, which retains 364 sites per bin.
The REAL 210-bin card is thinner than that nearly everywhere. Extracted from the
production cache's own rule blob (`ntrain/sites.py`, which parses the
`SCTRULE8` records rather than trusting the log's median):

| cache | min | p05 | q25 | median | q75 | p95 | max |
|---|---|---|---|---|---|---|---|
| `cache_260825_p4` (1e-4, P=24, nt9) | 247 | 259 | 278 | **300** | 376 | 398 | 406 |
| `cache_260824b`   (1e-3, P=24, nt9) | 223 | 244 | 270 | **292** | 371 | 392 | 404 |

and the thinnest bins are named: |Y| < 0.3 with qT between 1 and 11 GeV
(thinnest of all, 247 sites, is |Y| [0, 0.15] x qT [8, 9]). So the corner the
scan used sits at the card's q75, and the conclusion has to be checked at the
thin end before it can be quoted for 210 bins.

**WHY qT 5-7 AND NOT qT 1-3.** qT 5-7 GeV is where the thin bins are AND it is
above the nonsingular-cutoff region (the known template mismatch is confined to
qT < 3-4 GeV, and dominates below 1 GeV), so BOTH metrics -- template response
and rule-vs-live -- stay informative there. At qT 1-3 the template metric is
saturated (see D8).

**WHAT IT WOULD TAKE TO CHANGE THE ANSWER.** If the thin corner at n_train 9
lands at the n_train 5 accuracy of the thick corner (NP lambda ~6e-06 against
the templates), then thin bins ARE under-resolved at 9 and the recommendation
becomes n_train 12-14. If it lands where the thick corner's n_train 9 does, the
recommendation stands for the whole card.

**PRE-REGISTERED.** Written before the builds finished.

---

## D15. The Hessian's P-scaling: the brief's premise is REFUTED, and it was a
   contention artefact, not the `_rule_is_matched` short-circuit

**WHAT.** Two candidate explanations for "the Hessian rises 3.2x for two extra
parameters (8.1 s -> 25.4 s, P = 24 -> 26)". Both tested; the first is right.

**H1 (contention).** The 8.1 / 25.4 s pair came from two SEPARATE
`backend_check.py` runs at 14:47 and 14:52 on a node whose load average was
250-570. Interleaving the same two caches in ONE process and taking the min over
alternating rounds -- the estimator that cancels contention -- gives:

| A -> B (4 bins) | value+jacobian | hessian |
|---|---|---|
| P 24 -> 26 (n_eig 0 -> 2) | x1.01 | **x1.09** |
| P 26 -> 53 (n_eig 2 -> 29) | x1.25 | x2.77 |
| P 24 -> 53 | x1.31 | x2.95 |

So 24 -> 26 is 1.09x, not 3.2x, and the whole way to P = 53 is 2.95x. The
functional form is not "3.2x per 2 parameters" and never was.

**H2 (the uncommitted `_rule_is_matched` short-circuit removed the expensive
fixed-order Hessian block).** REFUTED by direct toggle
(`ntrain/hess_attrib.py`): at P = 24, forcing the flag off changes the Hessian
time from 8823 ms to 9017 ms -- **2%**. The block is not the cost.

**AND A SEPARATE, IMPORTANT SIDE RESULT.** Toggling that same flag changes the
Hessian VALUE by `max|H(True) - H(False)| / max|H| = 1.52`, i.e. 152%. The
uncommitted `py/scetlib_tf.py` change in the SHARED tree is therefore not a
performance tweak -- it materially determines the curvature the covariance pass
uses. It is live on `PYTHONPATH` for every session. **Anyone who stashes or
reverts that file changes every Hessian and every uncertainty by an O(1)
factor.** It should be committed (branch `fix-nons-double-count` exists) before
the eigenvector build, so the cache and the evaluation code are pinned together.

**PROJECTION (item 5).** With the correct scaling, at 210 bins and P = 53:
value+jacobian ~1.2 s and hessian ~4-5 min (two independent extrapolations,
240 s from the bins x nodes fit and 285 s from the P-ratio applied to the
measured 210-bin P = 24 Hessian of 89.8 s). The covariance pass is NOT the
binding constraint. Memory is: ~55 GB for the loaded model.

**WHAT WOULD OVERTURN IT.** A P = 53, 210-bin Hessian that is not ~5 min. The
only way to check directly is to build the cache, which is what this is gating.

---

## D16. THE PREMISE OF THE 9-15 h ESTIMATE IS AT THE WRONG TOLERANCE.
   The integration settings are a 13x lever; `--n-train` is not.

**WHAT.** Reporting, unasked, that the "~14 h / 15 h for 62 members" projection
in `knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md` was measured
at `target_precision_rel = 1e-3`, while the PRODUCTION cache
`cache_260825_p4` runs at `rel = 1e-4, abs = 0` and is 13x more expensive per
member. Nobody asked me to check this; the numbers fell out of reading the build
logs to normalise the eigenvector member cost, and the gap is far larger than
anything `--n-train` does.

**EVIDENCE.** 210 bins, `--threads 210`, 4 members (2 alphaS + 2 muF),
`--pdf-eig 0`, same card, same builder:

| cache | rel | abs | node set | rules | fixed-order member stage |
|---|---|---|---|---|---|
| cache_260824b | 1e-3 | 0 | 21.9 min | 4.4 min | **54.8 min** |
| cache_aspair_260821_kRfix | 1e-4 | 1e-8 | (not logged) | 8.5 min | 82.8 min |
| cache_260825_p4 (production) | 1e-4 | 0 | **325.3 min** | 10.6 min | **715.6 min** |

`1e-4 + abs 0` is 14.9x the node set and 13.1x the member loop of `1e-3 + abs 0`.
Of that, the `target_precision_abs 1e-8 -> 0` change alone (made 2026-08-24 "on
Josh's advice") is worth **8.6x** (715.6 / 82.8).

**NOT CONTENTION.** The p4 node-set stage ran 00:05-05:30 on a quiet node and
still took 325.3 min. And tonight, on the same card with `--threads 210`, my two
1e-3 builds took 23.3 and 23.4 min for that stage against cache_260824b's 21.9 --
6% -- so tonight's numbers are like-for-like with that build.

**WHAT IT MEANS FOR THE 62-MEMBER BUILD.** Taking the muF:PDF member ratio r and
solving `2a + 2ra = (measured 4-member stage)`, then `60a + 2(ra)` for 62:

| integration settings | per ordinary member | 62-member loop |
|---|---|---|
| rel 1e-3, abs 0 | 8.1 min | **8.7 h** |
| rel 1e-4, abs 1e-8 | 12.2 min | 13.2 h |
| rel 1e-4, abs 0 (production today) | 105 min | **114 h** |

(r = 2.4 assumed here from the previous agent's fork measurement; my own 210-bin
measurement of r is in flight -- `m210_eig` vs `m210_asmuf`.)

**ACCURACY COST OF DROPPING TO 1e-3, measured on IDENTICAL bins**
(4 bins, P = 53, n_train 9, the only difference being that one runcard line):

| group | rel 1e-4 | rel 1e-3 | ratio |
|---|---|---|---|
| NP lambda (8) | 6.53e-07 | 1.47e-05 | 22x |
| TNP (20) | 1.96e-07 | 5.45e-06 | 28x |
| muF/kappa_R (6) | 1.40e-04 | 2.07e-04 | 1.5x |
| transitions (3) | 2.17e-03 | 1.94e-03 | 0.9x |
| **alphaS (2)** | **1.88e-05** | **2.03e-05** | **1.08x** |
| PDF eig (58) | 1.50e-06 | 2.42e-06 | 1.6x |

So 1e-3 costs 22-28x on the two SMALLEST residuals, leaving them at 1.5e-05 --
still an order of magnitude below the muF/kappa_R residual and two below the
transition residual, i.e. still not what limits the model -- and it costs only
8% on alphaS, the number the analysis is for.

**THE ONE CAUTION AGAINST 1e-3.** The rule solve's worst per-bin TRAINING
residual on the 210-bin card is 6.1e-07 at 1e-3 against 2.5e-08 at 1e-4, and
`prepare_cache_for_card.py` prints a WARNING above 1e-6. 1e-3 sits a factor 1.6
under its own alarm; 1e-4 sits a factor 40 under. That is a reason to prefer
`rel 1e-4, abs 1e-8` (13 h, residual comparable to p4's) over `rel 1e-3`
(8.7 h) if a 4-hour difference is affordable.

**I AM NOT DECIDING THIS.** It is a physics/precision decision for Luca, it was
taken deliberately on Josh's advice, and reverting `abs` to 1e-8 needs the
reasoning behind aa42bbc re-read. What I am saying is that the build cannot be
costed without stating which of the three rows above it will use, and that the
answer moves the launch decision from "one night" to "five days".

**WHAT WOULD OVERTURN IT.** If `abs = 0` is required for correctness at 1e-4
(i.e. the 1e-8 absolute floor was masking a real cancellation error rather than
saving time), then 114 h is simply the price and the build must be split over
condor nodes BY BINS. That is testable: compare `cache_aspair_260821_kRfix`
(abs 1e-8) against `cache_260825_p4` (abs 0) bin by bin at the anchor and at a
displaced point -- both exist on disk, no new build needed.

---

## D17. Spend the overnight window on a PRODUCTION-tolerance 210-bin eigenvector
   member, rather than inferring it from the 1e-3 measurement

**WHAT.** Launched `m210_eig_1e4`: 210 bins, `--pdf-eig 29 --n-train 9
--members 0:2 --threads 210`, at `rel 1e-4, abs 0` -- byte-for-byte the
integration settings of the production cache `cache_260825_p4`.

**WHY.** The cost answer has one large remaining inference in it: I measure the
eigenvector member cost at `rel 1e-3` (cheap, and directly comparable to the
54.8 min / 13.7-min-per-member number the 15 h projection came from), and then
multiply by a 13.1x tolerance factor taken from a DIFFERENT member mix (2 alphaS
+ 2 muF). That product decides whether the real build is ~9 h or ~114 h -- the
single biggest number in the report -- so it should be measured, not inferred.
The prologue at these settings is ~5.5 h, which is exactly what an overnight
window is for.

**COST AND RISK.** One process, ~1874 OS threads and ~50 GB resident for ~9 h,
against a node with 1178 GB free and 768 cores. It does not gate anything else:
every other measurement is already running or done.

**WHAT IT SETTLES.** If the fixed-order stage for ONE eigenvector pair at
production settings is ~2 x 105 min, the 62-member build at those settings is
~110 h and MUST be split over condor nodes by bins (or the tolerance revisited).
If it is much less, the tolerance factor is member-class dependent and the 1e-3
scaling was wrong.

**WHAT WOULD OVERTURN IT.** Nothing -- it is the direct measurement. It can only
fail by running out of time, in which case the inferred number stands and is
labelled as inferred.

---

## D18. Take the question all the way to sigma(alpha_s), with the model's OWN
   Jacobian, rather than stopping at a response residual

**WHAT.** `ntrain/jac_vs_ntrain.py`: for each n_train cache, take
`L = d ln sigma / dp` from `values_and_jacobian`, build a toy Asimov Fisher
matrix `F = L^T W L + I` (unit Gaussian priors on all 53 nuisances,
W = 1/(0.3% per bin)^2) and read `sigma(alpha_s) = sqrt[(F^-1)_{as,as}]`.
Evaluated BOTH at the anchor and at a displaced point of postfit size
(lambda2 +0.15, lambda4 -0.10, gnu_lambda2 +0.03, every TNP and eigenvector
coefficient +-0.3).

**WHY.** A residual against a template is one step removed from the answer. The
fit does not see templates; it sees the Jacobian. And it does not sit at the
anchor, where `c_val` makes the rule exact by construction -- so the anchor
alone would be a rigged test, which is why the displaced point is there.

**WHY THE ABSOLUTE VALUE IS A TOY AND ONLY THE RATIO IS QUOTED.** 4 bins, a made-
up 0.3% per-bin uncertainty and unit priors are not the analysis; the number that
means something is the RATIO between two n_train values evaluated identically.

**RESULT so far (4 bins, P = 53):**

| | sigma(alpha_s), anchor | displaced |
|---|---|---|
| n_train 9  | 3.418177e-03 | 3.452807e-03 |
| n_train 14 | 3.415627e-03 | 3.449588e-03 |
| ratio 14/9 | 0.99925 | 0.99907 |

**0.07-0.09%**, and the two caches are separate builds so that difference also
contains the build-to-build floor. n_train 5 and 27 in flight.

**WHAT WOULD OVERTURN IT.** A ratio departing from 1 by more than the
build-to-build floor -- which is itself measurable, by running the same tool on
the two independent n_train 9 builds (`eig_test/eig29_nt9` and
`ntrain_gate/sub4_1e4_nt9b`). That control is queued.

---

## D19. TWO RESULTS THAT CHANGE HOW THE 4-BIN SCAN GENERALISES

### (a) The live route is BLIND to the eigenvector coefficients -- so those
    directions can only ever be validated against the templates

`ntrain/eig_live_probe.py`, 4 bins, P = 53, `sigma_binned_batch`:

```
pdf_eig0 = +1            max|v/v0 - 1| = 0.000e+00
pdf_eig5 = -1            max|v/v0 - 1| = 0.000e+00
lambda2  = 1.0           max|v/v0 - 1| = 1.234e-02
lambda2 = 1.0 & eig0=+1  max|v/v0 - 1| = 1.234e-02   <- identical to lambda2 alone
```

The member data that carries the eigenvector response exists only inside the
CACHE (`build_pdf_variations` writes it); a live evaluation of the same
calculation has no PDF member to interpolate and returns the c = 0 value
exactly. **Consequence:** (i) the rule-vs-live test cannot include eigenvector
directions, and cannot test lambda-x-c CROSS terms either -- there is nothing to
compare against; (ii) the eigenvector response is therefore validated ONLY
against the production `pdfvars` templates, where it is 1.50e-06 and FLAT across
n_train 5 -> 27, consistent with it not coming from the `--n-train` solve at all
(`build_pdf_variations` re-solves with its own `n_train_var = 3` and is exact at
c = +-1 by construction of the quadratic member interpolation).
**The experiment that WOULD test the cross terms** is a cache-to-cache A/B: two
caches built at different `--n-train`, compared at a joint (lambda, c) point.
That is a rule-vs-rule comparison and so carries the build-to-build floor
(3.0e-03 in the Jacobian at a displaced point), which is 3 orders above the
effect -- i.e. the test exists but has no resolution. Recorded as a genuine
limitation, not papered over.

### (b) Within ONE build, thin bins are BETTER, not worse. The thin-bin worry is
    backwards at fixed n_train.

`ntrain/perbin.py` on `y20_eig29` (20 bins, |Y| 0-2.5 at qT 20-28, P = 53,
n_train 9), per-bin worst rule-vs-live deviation over the joint 1x points
against that bin's own retained-site count:

```
log-log corr(sites, worst dev) = +0.781
thinnest quartile (359-364 sites) mean 3.62e-07
thickest quartile (392-397 sites) mean 1.64e-06
worst bin: |Y| [1.80, 2.50] x qT [20,24], 397 sites, 4.15e-06
best  bin: |Y| [0.00, 0.15] x qT [24,28], 359 sites, 8.24e-08
```

The site count is a measure of how HARD the bin's integrand is, not of how
well-determined its solve is: a bin that needs many nodes is also a bin that is
hard to compress. So "the real card has bins with only 247 sites, they may be
under-resolved" had the sign backwards -- inside a build, those are the easy
ones. This is a WITHIN-BUILD comparison, so no build-to-build term enters.

**CAVEAT, stated because it is real.** The site range here is narrow (359-397).
The genuinely thin corner of the real card is ~239-257 sites, a 1.5x
extrapolation beyond this fit. That is why the qT 5-7 GeV builds
(`thin_nt5/nt9/nt14`, and two `thin_ref0` for the floor) were launched -- they
put a measurement there rather than an extrapolation. `thin_nt9` retains
**239 nodes/bin at P = 53**, against 247 for the thinnest bin of the real
production cache: representative.

### D19 (b) -- CONFOUND, stated rather than glossed

In `fig6` the per-bin rule error is correlated with the site count (+0.78 in
log-log) but ALSO with |Y|, and the two are correlated with each other (forward
bins need more nodes). Both effects are visible separately in the same table:

* at fixed |Y| [1.80, 2.50]: qT [24,28] (385 sites) 1.32e-06 vs
  qT [20,24] (397 sites) 4.15e-06 -- more sites, 3x worse;
* at fixed qT [24,28]: |Y| [0,0.15] (359 sites) 8.24e-08 vs
  |Y| [1.80,2.50] (385 sites) 1.32e-06 -- 16x worse going forward.

So |Y| is the stronger driver and site count is partly a proxy for it. **I cannot
separate them from this dataset.** THE EXPERIMENT THAT WOULD: a cache on bins
chosen to break the correlation -- e.g. |Y| < 0.3 at qT 5-7 (thin, central) and
|Y| 1.8-2.5 at qT 44-100 (thick, forward) in the same build -- and compare the
per-bin error at matched site count across |Y|. The `thin_*` builds are the first
half of exactly that.

What the plot DOES establish, and it is the point: nothing in the measured range
says a bin with fewer retained sites is reproduced worse. The worry that
motivated raising n_train had the sign backwards.

---

## D20. THE MECHANISM, from the SCETlib source and the cache blobs:
   the unknowns are SITE WEIGHTS, not parameters, and adding the eigenvectors
   makes the solve MORE over-determined, not less

**WHAT the rule solve actually is** (`DrellYan.hpp` `Bin_rule_opts`,
`DrellYanAD.cpp::_rule_directions`, `qT.cpp` bindings):

* `n_train = K` random directions in the FULL P-dimensional parameter space,
  Gram-Schmidt orthogonalised, unit sup-norm, displaced by `scale = 0.15`
  (relative for a non-zero parameter, absolute over +-1 for one anchored at 0 --
  which is every TNP and every eigenvector coefficient);
* at each training point the solve reproduces the bin's VALUE, its GRADIENT
  (P rows) and `n_hvp = 1` HVP direction (P rows) EXACTLY;
* plus the anchor's own value and gradient;
* the UNKNOWNS are one non-negative weight per RETAINED SITE.

So the design matrix is `rows = 1 + n_train*(1 + 2P)` by `n_sites`, and P enters
the ROW count, not the unknown count. Verified in the source rather than
inferred -- `DrellYanAD.cpp` inside `build_bin_rules`:

```
const std::size_t blk  = 1 + P + (wh ? ntri : M * P);   // M = n_hvp = 1
const std::size_t nrow = 1 + K * blk;                   // K = n_train
```

i.e. `blk = 1 + 2P` and `nrow = 1 + n_train(1 + 2P)`: 442 at P = 24 and 964 at
P = 53, both at n_train = 9. The 9/53 = 0.17 "ratio" compares two things
that are not on the same side of the equation.

**MEASURED, by parsing `n_sites` and `n_sites_full` out of the rule blobs
(`ntrain/sitesfull.py`):**

| cache | n_train | P | rows | sites kept (median) | of full | **rows / sites** |
|---|---|---|---|---|---|---|
| eig29_nt5 | 5 | 53 | 536 | 220 | 17374 (1.29%) | **2.43** |
| eig29_nt9 | 9 | 53 | 964 | 364 | 17374 (2.13%) | **2.65** |
| sub4_1e4_nt14 | 14 | 53 | 1499 | 507 | 17374 (2.98%) | **2.96** |
| eig29_nt27 | 27 | 53 | 2890 | 720 | 17374 (4.27%) | **4.02** |
| y20_eig29 (20 bins) | 9 | 53 | 964 | 377 | 16731 (2.30%) | 2.56 |
| ref0a | 9 | 24 | 442 | 372 | 17374 (2.17%) | **1.19** |
| **cache_260825_p4 (production, 210 bins)** | 9 | 24 | 442 | 300 | 16731 (1.82%) | **1.47**, worst bin **1.09** |

**Read the last two rows.** The solve is over-determined at every configuration
tested -- and it is over-determined by MORE at P = 53 (2.65) than at the P = 24
of every cache the analysis has used so far (1.19-1.47, with the worst bin of
the current production cache at 1.09, i.e. barely). Registering 29 eigenvector
coefficients adds 2 rows per coefficient per training point (a gradient row and
an HVP row) while the retained site count barely moves (372 -> 364 on the same
4 bins). **Turning the eigenvectors on IMPROVES the conditioning of the rule
solve.**

That is why the P = 53 accuracy at n_train 9 equals the P = 24 accuracy at
n_train 9 in every group (D13, EVIDENCE 1, compared against the ref0 floor), and
why raising n_train does almost nothing: it mostly buys more retained sites
(1.3% -> 4.3% of the 17374 available) rather than better-determined ones.

**ONE THING TO WATCH, and it is the opposite of the original worry.** The
current PRODUCTION cache's worst bin sits at rows/sites = 1.09. If a future
cache is ever built at P = 24 with a lower n_train, or on bins that retain more
sites, that ratio can cross 1 and the solve becomes genuinely under-determined.
At P = 53 there is a factor 2.4 of headroom.

**WHAT WOULD OVERTURN IT.** A bin whose `rows/sites` at P = 53, n_train 9 is
below ~1.5. None of the 4 + 20 + 4 bins measured is (worst 2.41). The 210-bin
`m210_eig` build in flight will give the full distribution at P = 53.

---

## D21. FULL-CARD CONFIRMATION of D20 -- the 210-bin card at P = 53 is BETTER
   conditioned than the P = 24 cache in production today

**MEASURED tonight**, `m210_asmuf`, all 210 bins, `--pdf-eig 29 --n-train 9
--threads 210`, rel 1e-3 (the settings of `cache_260824b`, so like-for-like):

```
outer node set  23.3 min   (cache_260824b at P=24: 21.9 min -- 6% contention)
rules built     28.2 min   (median 277 nodes/bin, worst training residual 3.2e-08)
```

against `cache_260824b` at P = 24: 4.4 min, median 292 nodes/bin, worst residual
6.1e-07.

So on the REAL card, going P = 24 -> 53 at fixed n_train = 9:
* rows 442 -> 964,
* retained sites 292 -> 277 (it keeps FEWER),
* **constraints per unknown 1.51 -> 3.48**,
* worst training residual 6.1e-07 -> 3.2e-08 (19x better).

**This is the measurement the whole gate turned on, made on the production
binning rather than a 4-bin corner.** The concern was that adding 29 parameters
would leave the rule solve under-determined at n_train = 9. It does the
opposite. `--n-train 9` at P = 53 is better constrained than the P = 24 caches
every result so far has been built on.

**CAVEAT.** The rules stage grew 4.4 -> 28.2 min. Tonight's node carried load
average 600-690 with ~10 of my own processes, and the node-set stage of the same
build shows only a 6% contention term, so most of the 6.4x is real (2.2x the
rows, and a solve that is superlinear in rows). Even so, 28 min of rules against
a member loop of many hours is not a lever; and it is the reason I did NOT try to
extract an n_train^2.7 law from the 4-bin ladder tonight -- those timings ran
under a load that changed by a factor 20 during the evening and are not
comparable. The load-independent cost proxy is the retained site count, which is
what fig3 uses.

---

## D22. RETRACTION AND CORRECTION: the sigma(alpha_s) test does NOT resolve
   n_train = 5 either. The floor is 0.70%.

**WHAT I WROTE EARLIER (D18, and an interim reading of fig5):** "n_train 5
shifts sigma(alpha_s) by +0.75 to +1.0%; 9, 14 and 27 agree to 0.3%." The first
half of that is not supported and I am retracting it.

**WHY.** The build-to-build floor on this quantity had not been measured when I
wrote it. It now has been: a SECOND independent n_train 9 build of the identical
runcard on the identical bins (`ntrain_gate/sub4_1e4_nt9b`) gives

| | sigma(alpha_s) anchor | displaced |
|---|---|---|
| n_train 9  (eig_test/eig29_nt9)   | 3.418177e-03 | 3.452807e-03 |
| n_train 9  (ntrain_gate/sub4_1e4_nt9b) | 3.442092e-03 | 3.476730e-03 |
| **floor** | **+0.70%** | **+0.69%** |
| n_train 5  | 3.452126e-03 (+0.99%) | 3.478682e-03 (+0.75%) |
| n_train 14 | 3.415627e-03 (-0.07%) | 3.449588e-03 (-0.09%) |
| n_train 27 | 3.427039e-03 (+0.26%) | 3.460959e-03 (+0.24%) |

n_train 9, 14 and 27 all sit INSIDE the 0.70% floor. n_train 5 is the only
point that leaves it, and only at the anchor: +0.99% against a +0.70% floor
(1.4x), while its displaced point at +0.75% is on the band edge. The correct
statement is therefore: **this test cleanly resolves nothing -- not even
n_train = 5 -- and certainly does not distinguish 9 from 14 or 27.**

**THIS DOES NOT WEAKEN THE RECOMMENDATION -- it sharpens it.** n_train = 5 IS
resolved as worse by the two tests that have the resolution to see it:
* against the production templates, NP lambda 6.08e-06 vs 6.53e-07 -- a factor
  9.3, against a measured +-10-14% floor at P = 53 (T13);
* against a LIVE evaluation with ONE shared reference (so only the rule
  differs), NP joint 1x 6.98e-06 vs 6.03e-07 -- a factor 11.6.
What the sigma(alpha_s) test adds is that even a 10x worse RESPONSE does not
move the fit's alpha_s uncertainty out of the noise, because the response error
is 3 orders below what limits the model. That is the reason to keep 9 rather
than raise it, stated at the level of the actual deliverable.

**HOW THE ERROR HAPPENED, for the record.** I quoted a difference before
measuring its floor. The floor build was already queued when I wrote D18 -- the
D18 entry says so ("that control is queued") -- but the interim number went into
a figure caption before the control landed. fig5 has been regenerated with the
measured floor drawn as a band.

---

## D23. CORRECTION to an inherited claim: "n_train 5 would make the build ABORT"
   is too strong. The guard is a RESIDUAL check, not a rank check.

**THE INHERITED CLAIM** (previous agent, `LOGBOOK_eigenvector_paste.md` sec. 3):
"the member re-solve raises `Fewer sites than constraints` when a bin has fewer
sites than `m = 1 + n_train_var*(1 + P) = 163` at P = 53 ... n_train = 5 ...
would put the thinnest real bins at ~134 and the build would **ABORT**, not
merely degrade."

**WHAT THE CODE ACTUALLY DOES** (`DrellYanAD.cpp`, `build_pdf_variations`):
`m = 1 + K*(1 + P)` with `K = n_train_var = 3` is confirmed (line 4493), but the
throw is conditional on the RESIDUAL:

```
if (rmax > 1e-6 * max(bmax, 1e-300))
   throw ... + to_string(m) + " constraints on " + to_string(nsel) + " sites)."
            + (nsel < m ? " Fewer sites than constraints: ..." : "");
```

`nsel < m` only appends an explanatory sentence to an error that has already
been triggered by the residual. A bin with fewer sites than constraints can
still satisfy them to 1e-6 if the constraints are nearly consistent -- which,
for a smooth member response, they are.

**MEASURED.** `thin_nt5` (|Y| < 0.3, qT 5-7 GeV, P = 53, n_train 5) retains a
MEDIAN of **159 nodes/bin -- below the m = 163 threshold** -- and its resummed
member stage completed normally in 11.1 min with no error.

**WHY IT MATTERS.** "Do not lower n_train" is still the right advice, but it now
rests on the measured accuracy degradation (NP lambda 9.3x worse against the
templates, 11.6x worse against a live evaluation) rather than on a hard failure
that may not happen. A build at too low an n_train can therefore come out
SILENTLY worse rather than refusing -- which is the more dangerous failure mode
and is worth saying out loud.

**CONFIRMED FROM THE WRITTEN CACHE.** `thin_nt5`'s four bins retain
**154 / 159 / 160 / 164** sites (parsed per bin from the rule blob) against
`m = 163`. THREE OF FOUR are below the constraint count, the build wrote its
cache normally (23.4 MB, fixed-order stage 28.2 min) and its worst training
residual is **7.1e-09**. The claim is falsified as stated.

For completeness, the thin corner's conditioning at n_train 9:
`thin_nt9` retains 235-240 sites for 964 rows = **4.03 constraints per unknown**,
against `thin_ref0a` at P = 24 with 249-257 sites for 442 rows = **1.72**. The
same 2.3x improvement from turning the eigenvectors on that D20/D21 found in the
thick corner and on the full card.

---

## D24. FOLLOW-UP my own results opened: chase the 7.8% transition rule-vs-live
   gap far enough to hand the transition work a usable diagnosis

**WHAT.** Two extra experiments, neither of which is on the n_train critical
path, both cheap, run because fig2's black line is the largest number anywhere
in this study and nobody has attributed it:

1. **Is it an eigenvector effect?** Same rule-vs-live test on the scale family
   at P = 24 (`eig_test/ref0a`, no eigenvectors at all). If the gap is the same
   7-8% there, the eigenvectors are irrelevant to it.
2. **Does the muF-member-coordinate fix close it?** A 4-bin `--pdf-eig 29
   --n-train 9` cache built against `/work/submit/lavezzo/alphaS/scetlib-trans/
   build-trans` -- the OTHER agent's already-compiled library at 92f1299
   "qT/ad: the muF members are three muF samples, so interpolate in muF" --
   then the same test. **Read-only use of an existing build; no SCETlib was
   rebuilt, in the shared tree or anywhere else.**

**WHY THIS HYPOTHESIS.** The transition points move muF (the study's own
diagnosis: "the transition points move muf ~20% for x2"), and the cached rule
reaches muF through the muF MEMBER interpolation `tf = log(kF)/var_muf_lnstep`,
while a live parameter-route evaluation does not use members at all. A wrong muF
member coordinate would therefore show up as a rule-vs-live disagreement that is
flat in n_train -- which is exactly the observed signature (7.736e-02 /
7.855e-02 / 7.801e-02 / 7.813e-02 at n_train 5 / 9 / 14 / 27).

**WHAT IS ALREADY KNOWN AND CONSTRAINS THE ANSWER.** The cached rule reproduces
the RUNCARD-route production template `transition_points0.2_0.35_1.0` -- the
same displacement -- to 2.17e-03, while disagreeing with the LIVE PARAMETER
route by 7.9e-02 at that point. Three routes, and the rule agrees with the
runcard one. So the live parameter route is the odd one out, and this is a
diagnosis of `sigma_binned_batch` under a moved transition point, not of the
cache. `scale_kappa_R` is clean on the same test (6.0e-08 at 1x), which is the
control: kappa_R holds muF fixed by construction.

**CAVEAT ON MY OWN TEST.** Because the live parameter route is the suspect, my
rule-vs-live test is only trustworthy for the NP and TNP families, where all
three routes agree. That limitation is already reflected in fig2 (the scale
family is drawn separately and excluded from every joint set) and in D12.

**RESULT OF (1): the eigenvectors are irrelevant.** At P = 24 with `n_eig = 0`
(`eig_test/ref0a`), the same test gives `scale_x2` down = **7.842e-02** against
7.855e-02 at P = 53 -- identical to three digits, direction by direction (T14).
`scale_kappa_R` is 6.7e-07 there, five orders cleaner, which is the control.
**So the gap is present in the P = 24 configuration the analysis is using
today**; it is not something the eigenvector build introduces.

**RESULT OF (2): FALSIFIED -- `trans_nt9` shows the same 7.8%.** See D34. If `trans_nt9` shows the same 7.8%,
the muF member coordinate is not the cause and the next suspect is the frozen
beam convolutions (`bfc6be6` was supposed to let the transitions move muF for
them). That would be separated by the runcard-vs-parameter A/B the study already
has a tool for (`ab_scale_route.py`).

---

## D25. PRE-LAUNCH CHECKLIST for the 62-member build (not a decision -- the
   operational residue of everything above, in one place)

**Settings**
* `--pdf-eig 29 --n-train 9` (D13). `--threads`: 210 gave 137 busy cores tonight
  (65% of requested); the node has 768, and the knowledge note's 145/200 (72%)
  is the same number. Above ~200 the efficiency is an extrapolation, not a
  measurement.
* **DECIDE THE INTEGRATION TOLERANCE FIRST (D16).** It is a 13x lever on the
  member loop -- 8.7 h at `rel 1e-3, abs 0`, ~13 h at `rel 1e-4, abs 1e-8`,
  ~114 h at the production `rel 1e-4, abs 0`. Nothing else in this report moves
  the wall clock by more than a factor 1.2.

**Before launching**
* **COMMIT `py/scetlib_tf.py`.** The uncommitted `_rule_is_matched` change in
  the SHARED tree changes every Hessian by 152% (D15). A cache built tonight and
  evaluated after someone stashes that file would give silently different
  uncertainties. Branch `fix-nons-double-count` already exists.
* `backend_check.py` will report a SPURIOUS `pdf_eig0` FD failure: its step is
  `h = 1e-4 * max(|p|, 1e-3) = 1e-7` for a parameter anchored at 0, and every
  `pdf_eig` is. The analytic gradient is right to 5e-08 on an h-scan. Fix the
  step or expect the false alarm (inherited finding, previous agent).

**Resources, measured**
* build process: ~1874 OS threads whatever `--threads` says (TF's own pools),
  and **~60 GB resident** for 210 bins x 62 members at P = 53 (measured 47-49 GB
  at 4 members in the rules stage, plus 13 GB of member payload). At the
  32768 threads/user ceiling that is ~17 concurrent build processes.
* output: **~14.3 GB uncompressed rules, ~2.5 GB npz.** /ceph has 388 TB free.
* the FIT that loads it: **50-64 GB RSS** (a range, not a point: the linear
  RSS model and a pure RSS/rules ratio disagree by 15% when extrapolated 10x
  past the largest measured blob), ~1.2 s per value+jacobian call and
  ~4-5 min for the hessian, at 8 threads (fig4). That rules out a wide
  concurrent toy ensemble on one machine: 1447 GB / 55 GB is ~26 fits, and
  they would also contend for cores.
* if bins are split and merged: the merge wants ~4x the blob, i.e. also ~60 GB
  and ~10 min (knowledge note, measured on the 4-member 210-bin cache).

**Do NOT**
* split MEMBERS across processes (unmergeable; the node set is not
  reproducible). Split BINS with `--subset` / `--bin-groups` + `--merge-bins`.
* raise `--n-train` (D13): it doubles the cache, the fit's RAM, every fit
  iteration and the covariance pass, for an accuracy gain 3 orders below what
  limits the model.

---

## D26. A THIRD member-count point at 210 bins, because the fixed overhead of the
   member stage is NOT small and a two-point comparison cannot separate it

**WHAT.** Launched `m210_eig8`: 210 bins, `--pdf-eig 29 --n-train 9 --members
0:8 --threads 210`, rel 1e-3 -- identical to `m210_eig` except that it builds
FOUR eigenvector pairs instead of two.

**WHY.** The fixed-order member stage is `F + n_members * a`, and F is large.
On the 4-bin corner, comparing `ref0a` (4 members, FO 1.4 min) with
`eig29_nt9` (62 members, FO 7.8 min) gives a = 0.110 min/member and
**F = 0.96 min -- 69% of the 4-member stage**. Extrapolating a 4-member stage
LINEARLY to 62 members therefore over-counts badly:

* linear from 54.8 min / 4 members: 62 x 13.7 = 14.2 h
* with F separated (if F is a similar fraction at 210 bins): F + 62a could be
  half that.

The difference between those two answers is the difference between a one-night
build and a two-night one, so it has to be measured rather than assumed. Two
shards with 4 and 8 eigenvector members share F exactly, so
`a_eig = (FO_8 - FO_4)/4` and `F = FO_4 - 4 a_eig`, with no assumption at all.

**AND IT ALSO FIXES THE muF RATIO.** With `a_eig` known and `m210_asmuf`
(2 alphaS + 2 muF) measured on the same night and the same bins,
`a_muf = (FO_asmuf - F - 2 a_alphaS)/2` with `a_alphaS = a_eig` (both are one
node refill). That is a direct measurement of the 2.4x muF:PDF ratio the 15 h
projection depends on, rather than the inherited fork-based number.

**COST.** ~24 min prologue + ~30 min rules + the member stage, on a node whose
load has dropped to 270. It does not gate anything else.

**WHAT WOULD OVERTURN IT.** If `FO_8 - FO_4` is not ~2x `FO_4 - F`, the stage is
not linear in the member count and the whole cost model needs rethinking -- in
which case say so and quote the measured points only.

---

## D27. Close the loop: express the rule error as an equivalent shift on
   alpha_s, not as a residual

**WHAT.** `ntrain/resid_to_alphas.py`. For the same Fisher matrix used in D18
(`F = L^T W L + I`), a residual `r` (per bin, in ln sigma) induces the parameter
shift `dp = F^-1 L^T W r`; the alpha_s component of that, divided by the
sigma(alpha_s) the SAME matrix gives, is the number that matters. Applied to the
signed per-bin rule-vs-live residual at every point of the joint sets, on
`y20_eig29` (20 bins spanning |Y| 0-2.5 at qT 20-28, P = 53, n_train 9).

**WHY.** Every number in this report so far is a residual. A residual is only
worth something once it is projected onto d ln sigma / d alpha_s AND the other
52 nuisances have absorbed what they can -- which is exactly what the study's own
`residual_structure_map.py` does for the OTHER directions, and what makes the
transition residual worth 0.002-0.025 sigma rather than "2e-03".

**WHY THIS IS THE RIGHT CLOSING NUMBER.** It converts "the rule error at
n_train 9 is 6e-07" -- which no one can weigh -- into "the rule error at
n_train 9 is X sigma(alpha_s)", which is directly comparable to the 0.002-0.025
sigma the study already assigns to the transitions, and to the 1.0 sigma that
would make it a problem.

**CAVEAT, same as D18.** Unit priors, an invented 0.3% per-bin uncertainty and
20 of 210 bins. The FRACTION of sigma is far more robust than the absolute,
because both numerator and denominator come from the same Fisher matrix.

---

## D28. THE HEDGE IS CLOSED, and it closed in the opposite direction to the worry

**THE PRE-REGISTERED QUESTION (D14).** "If the thin corner at n_train 9 lands at
the n_train 5 accuracy of the thick corner, then thin bins ARE under-resolved at
9 and the recommendation becomes n_train 12-14. If it lands where the thick
corner's n_train 9 does, the recommendation stands for the whole card."

**THE ANSWER.** It lands 46x BETTER than the thick corner's n_train 9. Rule vs a
LIVE evaluation, worst over 12 random joint NP points at the template step,
P = 53:

| | thick (qT 20-28) | thin (qT 5-7) |
|---|---|---|
| n_train 5 | 6.98e-06 | **1.24e-07** |
| n_train 9 | 6.03e-07 | **1.31e-08** |

and the thin corner's conditioning is 4.03 constraints per unknown against 2.65
in the thick one. So the recommendation stands for the whole card, and the
reason the thin bins are thin is that their integrand is EASY, not that the
solve gave up on them -- which is the same conclusion the within-build per-bin
correlation reached (D19b), now confirmed between corners where site count and
|Y| are not confounded.

**THE ONE PLACE IT REVERSES, stated because it is real.** At 4x the template
displacement the thin corner is 9x WORSE than the thick one (4.61e-04 vs
5.15e-05 at n_train 9). Low-qT bins sit closer to the nonperturbative region, so
a large lambda excursion moves their integrand much more than it moves a
qT 20-28 bin's, and the rule extrapolates less well there. At 1x and 2x -- where
a converging fit lives -- the thin corner wins, and at 4x both are still
<= 5e-04. If a fit is ever seen wandering to several times the template
displacement in the NP directions, this is the number that would need
re-examining; nothing in the current fits does.

**WHAT I STILL CANNOT SAY.** Nothing in this study measures a 210-bin cache at
more than one n_train -- that would be the full build, twice. The argument that
carries the 4-bin and 20-bin results to 210 bins is that **a bin's rule is
self-contained**: its own outer grid, sites, node data and members, solved
independently, which is exactly why bins from separate processes merge
byte-exactly (knowledge note). Under that structure a per-bin measurement
generalises bin by bin, and the two corners bracket the card's site range
(154-164, 235-240 and 359-397 against the card's 247-406). That is an argument
plus coverage, not a direct 210-bin n_train scan, and it should be read as such.

---

## D29. Both routes of the muF-fix test must use the FIXED library

**WHAT.** `after_trans.sh` runs BOTH the rule replay and the live evaluation of
`trans_nt9` against `/work/.../scetlib-trans/build-trans`, not just the rule.

**WHY.** The hypothesis is that the muF member coordinate is wrong in the CACHE's
replay. But 92f1229 could equally change the live route. Comparing a
trans-built rule against a build-fix live evaluation would mix a code change into
a route comparison and could show a "fix" that is only the two libraries
disagreeing. The clean test is rule-vs-live INSIDE each library, then compare the
two gaps:

* build-fix: rule vs live at `scale_x2 = 0.35` = **7.855e-02** (measured)
* build-trans: the same number, to be measured

**WHAT WOULD OVERTURN THE HYPOTHESIS.** the trans gap being the same 7.8%.
**WHAT WOULD CONFIRM IT.** the trans gap collapsing toward the 2.17e-03 that the
rule already achieves against the RUNCARD-route template.
**WHAT WOULD BE AMBIGUOUS.** a partial reduction -- in which case the remaining
piece is the frozen beam convolutions and `ab_scale_route.py` (runcard vs
parameter, one library) separates them.

**SCOPE NOTE.** This is a diagnosis handed to the transition work, not a change
to anything. No SCETlib was rebuilt; the `build-trans` library was compiled by
the other agent at 14:31 today and is used read-only.

---

## D30. "Where does accuracy stop improving?" -- the honest answer is that it
   never does, and that is not the question that decides the build

**THE MEASUREMENT.** Rule vs a LIVE evaluation, worst over 12 random joint NP
points at the template step, P = 53, thick corner (|Y|<0.3, qT 20-28):

| n_train | 5 | 9 | 14 | 27 |
|---|---|---|---|---|
| joint NP 1x | 6.98e-06 | 6.03e-07 | 5.80e-08 | 4.63e-08 |
| ratio to the previous | -- | /11.6 | /10.4 | /1.25 |

and in the thin corner (qT 5-7): 1.24e-07 -> 1.31e-08 -> 3.21e-09,
i.e. /9.5 then /4.1.

So the rule solve is still improving at n_train 27 -- the curve has a knee near
14 but never flattens. **Anyone who asks "where does accuracy saturate" and
takes the answer as the recommendation will pick 14 or 27.** That would be the
wrong reading, for three reasons, each measured:

1. **Against the production TEMPLATES -- the figure of merit -- it is already
   flat from 9.** 9 -> 14 changes NP lambda by -14% and the transitions by -24%
   against a MEASURED build-to-build floor of +-10 to 14% at P = 53 (two
   independent n_train 9 builds, T13). There is nothing there to resolve.
2. **In sigma(alpha_s), 9 already costs 1e-5 sigma** at the template step and
   0.003 sigma at 8x it, against 0.002-0.025 sigma for the transitions (T18).
   14 and 27 buy a factor 5 on the smallest term in the model.
3. **The improvement is not free and the price is paid in the FIT.** 9 -> 27
   doubles the retained sites, hence the cache (13 -> 28 GB), the fit's RSS
   (51 -> 108 GB), every minimiser iteration and the covariance pass (T3).

**THE ANSWER TO GIVE.** Accuracy improves monotonically to at least 27; what
stops at 9 is any effect on a quantity anyone measures. 9 is the smallest value
with margin: it is a factor 8 above where the rule error reaches the bottom of
the transition band (n_train 5, 0.024 sigma), and a factor 10-12 better than
n_train 5 on the raw metric in both corners.

---

## D31. `target_precision_abs = 0` costs 8.6x and, on the bins tested so far,
   buys NOTHING. Testing it where it could actually matter.

**MEASURED (4 bins, |Y| < 0.3, qT 20-28, P = 53, n_train 9, rel 1e-4, the ONLY
difference being `target_precision_abs`):**

| group | abs = 0 (`sub4_1e4_nt9b`) | abs = 1e-8 (`sub4_1e4abs8_nt9`) |
|---|---|---|
| NP lambda (8) | 5.91e-07 | 6.08e-07 |
| TNP (20) | 1.95e-07 | 1.95e-07 |
| muF/kappa_R (6) | 1.39e-04 | 1.39e-04 |
| transitions (3) | 2.47e-03 | 2.47e-03 |
| alphaS (2) | 1.88e-05 | 1.88e-05 |
| PDF eig (58) | 1.50e-06 | 1.49e-06 |

Identical in every group (the NP lambda difference is 3%, against a measured
+-10-14% build-to-build floor). And on the 210-bin card that same change is
worth **8.6x** on the member loop (715.6 vs 82.8 min for 4 members) -- the
difference between a ~114 h build and a ~13 h one.

**WHY I AM NOT YET RECOMMENDING abs = 1e-8.** An ABSOLUTE floor can only bite
where the bin's cross section is SMALL. The corner tested carries ~2.4 pb per
bin; an absolute target of 1e-8 pb is 9 orders below that and cannot possibly
be reached, so this test had no power. The bins where it could matter are the
small-sigma ones: forward rapidity at high qT.

**THE TEST THAT HAS POWER, now running.** Two 4-bin caches at
`--subset '8,9/19,20'` = |Y| 1.5-2.5 x qT 33-100 -- the smallest-cross-section
corner of the card -- differing only in `target_precision_abs` (0 vs 1e-8),
compared with the same tool against the same templates.

* If they agree there too, `abs = 1e-8` is safe and the production build should
  use it: same accuracy, 8.6x cheaper, and the same setting every cache before
  2026-08-24 used.
* If `abs = 0` is measurably better in that corner, then it is buying something
  real and 114 h is the price -- in which case the build MUST be split over
  condor nodes BY BINS (which is validated exact), not run in one process.

**ATTRIBUTION LIMIT I CANNOT REMOVE TONIGHT.** Even a null result on 4 forward
bins is 4 of 210. The full statement would need the comparison on the whole
card, which is two 210-bin builds. What I can offer is a corner chosen to
maximise the chance of seeing the effect, plus the observation that every cache
built before 2026-08-24 used `abs = 1e-8` and none of the validation work in
this study found a problem attributable to it.

### D31 (correction, written before the result): my "corner with power" reasoning
    for the `target_precision_abs` test is WRONG, and I cannot fix it with a
    subset

**WHAT I ASSUMED.** That an absolute integration floor of 1e-8 pb can only bite
where the BIN cross section is small, so a forward high-qT corner would have
power.

**WHY THAT IS WRONG.** Two reasons, and I should have checked both before
launching.
1. The corner I picked is not small: `small_abs0/8` report a node-set sum of
   **40.708 pb over 4 bins = 10.2 pb/bin**, against 2.44 pb/bin for the
   qT 20-28 corner and 1.5 pb/bin for qT 1-3. The wide qT [44,100] bin
   integrates a lot. The genuinely smallest bins on the card are the NARROW
   ones (|Y| 0.15-wide x qT 1-GeV-wide), of order 0.3-1.5 pb -- still eight
   orders above 1e-8 pb.
2. More fundamentally, the tolerance is applied **per NODE**, not per bin
   ("the node ladder targets 0.0001 relative to the matched cross section at
   each node"), and p4's own build script says the `abs` change was safe
   "now that the per-bin absolute target comes from the resummed piece
   (aa42bbc) instead of a tolerance against a **cancellation residue**". The
   quantity the floor guards is a near-cancelling node-level integrand, whose
   size is not a simple function of the bin's cross section. **No choice of
   bins guarantees power.**

**WHERE THAT LEAVES IT.** Two corners (qT 20-28 at 2.4 pb/bin, and the forward
one at 10.2 pb/bin) show `abs = 0` and `abs = 1e-8` agreeing in every group to
within the build-to-build floor, with identical retained node counts. That is
evidence, not proof, and I am labelling it as such rather than turning a
null result on 8 of 210 bins into a recommendation.

**THE EXPERIMENT THAT WOULD SETTLE IT** is a 210-bin A/B at fixed rel 1e-4 --
i.e. two full builds, ~6 h at abs 1e-8 and ~18 h at abs 0 for 4 members, which
is a day of the node and is a decision for Luca, not something to start
unasked. A cheaper 80% version: build both at 210 bins with `--no-pdf` (no
member loop at all), which costs only the node set plus the rules -- about
6 h at abs 0 and 40 min at abs 1e-8 -- and compare the two caches' sigma and
Jacobian bin by bin. That isolates exactly the stage the `abs` change makes
expensive (the node set, 325.3 vs ~22 min) and needs no members.

---

## D32. Queued the cheap 210-bin `abs` A/B, but BEHIND the member-cost shards

**WHAT.** `queue_abs210.sh` waits for `m210_eig` and `m210_asmuf` to write their
caches, then launches two 210-bin `--no-pdf --threads 200` builds differing only
in `target_precision_abs` (1e-8 vs 0), both at rel 1e-4.

**WHY `--no-pdf`.** It skips the member loop entirely, so the build costs only
the node set plus the rules -- and the node set is exactly the stage the `abs`
change makes expensive (325.3 min at abs 0 against ~22 min at 1e-3; the rules
stage barely moves, 10.6 vs 4.4 min). So this isolates the effect for ~50 min
at abs 1e-8 and ~6 h at abs 0, instead of two full 18 h builds.

**WHY BEHIND, NOT NOW.** The node is at ~500 of 768 busy cores with the three
member-cost shards and the production-tolerance run. Adding two more 210-thread
builds now would slow `m210_eig`/`m210_asmuf`, and their RATIO is the deliverable
for item 4. Correctness of the primary measurement beats speed on a secondary
one.

**WHAT IT WILL AND WILL NOT SETTLE.** It compares sigma and the Jacobian bin by
bin on the FULL card at the two `abs` settings. It will NOT cover the member
data (no members are built), so if `abs` matters only through
`set_pdf_keep_nodes`, this test will miss it -- and that is a real possibility,
because the member refill is where 8.6x of the cost is. Stated so nobody reads
a null result here as a green light on its own.

---

## D33. MEMOISATION CHECK -- the arms in every comparison here are provably
   separated (prompted by another agent's exactly-1.00 null)

**THE HAZARD.** `ScetlibCachedXsecTF.values_and_jacobian` memoises on the
parameter vector ALONE, so two configurations compared inside one process can be
served the same cached result and return a perfect, meaningless null.

**WHY THIS STUDY IS NOT AFFECTED, by construction and by measurement.**
* Every `rule_vs_direct.py` arm ran in its OWN PROCESS writing its OWN npz
  (`--mode rule` and `--mode direct` are separate invocations, one per cache);
  a per-instance memo cannot cross processes.
* Every `validate_variations.py` run was one process on one cache.
* Verified from the saved data rather than argued: the nt9 arm has **245
  DISTINCT value rows out of 261 points** (the 16 repeats are the deliberately
  duplicated anchor and the points that clip onto the same physical vector), and
  sigma varies by 21% across the point set. A memo serving one result would give
  ONE distinct row.
* The arms differ: nt9-rule vs nt5-rule by 1.05e-03, rule vs direct by 2.19e-04.
  Nothing here is a 1.000 null.
* The interleaved `eval_cost_ab.py` timings use a different parameter point on
  every round and per tag, and the measured times (47-170 ms) are far above a
  dictionary hit.

**THE ONE PLACE A "TOO CLEAN" NULL DOES APPEAR, and its cause is different.**
`thin_ref0a` vs `thin_ref0b`, and `lowqt_ref0` vs `lowqt_eig29`, agree to the
printed 3 digits. Those are DIFFERENT cache FILES validated in DIFFERENT
processes, and the caches are demonstrably not the same object (257 vs 254
retained nodes/bin). The agreement is the physics floor described in T11 -- at
qT < 10 GeV the residual is a common difference between our calculation and the
production templates -- not a memo artefact. And it is not perfect: the
`mufdown-kappaFO0.5-kappaf2.` row differs in its 4th digit.

---

## D34. HYPOTHESIS FALSIFIED: the muF-member-coordinate fix does NOT close the
   transition rule-vs-live gap

**THE HYPOTHESIS (D24).** The 7.8% disagreement between the cached rule replay
and the live parameter route on the transition directions is the muF member
interpolation, because the transition points move muF and the rule reaches muF
through the member pair while the live route does not.

**THE TEST.** A 4-bin `--pdf-eig 29 --n-train 9` cache built against
`/work/submit/lavezzo/alphaS/scetlib-trans/build-trans` (92f1299, "the muF
members are three muF samples, so interpolate in muF"), with BOTH the rule
replay and the live evaluation run against that same library (D29).

**THE RESULT -- no change whatever:**

| direction, 1x down | build-fix (bb2e7cb) | muF fix (92f1299) |
|---|---|---|
| `scale_x1` | 5.308e-02 | **5.309e-02** |
| `scale_x2` | 7.855e-02 | **7.873e-02** |
| `scale_x3` | 8.025e-03 | **8.048e-03** |
| `scale_kappa_R` | 2.822e-07 | 4.352e-07 |

Three digits, direction by direction. Combined with T26 (the fix also changes
nothing against the production templates on this corner) and T14 (the gap is
identical at P = 24 with no eigenvectors at all), the transition gap is:
**independent of n_train, independent of the eigenvectors, and independent of
the muF member coordinate.**

**WHAT IS LEFT, and it is now the only candidate on the table.** The frozen beam
convolutions. The study's own diagnosis says the transition points move muF
(~20% for x2) and that the per-node beam convolutions are frozen at the config's
muf, changing by 7-16% over that range; `bfc6be6` ("let the transition points
move muF for the beam convolutions too") was supposed to address it and is in
bb2e7cb, so either it does not cover the parameter route or it does not cover
the compressed replay. `scale_kappa_R` is clean by five orders on the same test,
which is exactly the control the mechanism predicts: kappa_R holds muF fixed by
construction.

**THE EXPERIMENT THAT SEPARATES THE REMAINDER.** `ab_scale_route.py` already in
the study directory: the same transition point reached by the RUNCARD (which
refills the nodes) against the PARAMETER (which cannot), inside one library.
The rule agrees with the runcard-route production template to 2.17e-03 at
x2 = 0.35 while disagreeing with the live parameter route by 7.9e-02, so the
prediction is that the runcard-vs-parameter A/B reproduces ~7.9e-02 and the
compressed rule is not implicated at all.

**SCOPE.** Handed to the transition work. No SCETlib was rebuilt; `build-trans`
was compiled by the other agent at 14:31 today and used read-only.

---

## Gen-grid granularity (agent, 2026-08-26 overnight)

# Decisions — GRAIN vs gen-grid resolution (2026-08-25/26 overnight)

Staged for `studies/scetlib-ad-param-model/DECISIONS.md`. Follow-up to the
reco-2D closure round (`~/public_html/alphaS/260825_scetlib_ad_reco2d_closure/`),
which found that once the qT [0,1] nonsingular-cutoff convention is aligned,
GRAIN — pure gen-binning granularity — is the larger of the two error terms in
30 of 39 directions. The question here: how does GRAIN scale with the gen grid,
what would a finer grid cost, and does any of it show up in the fit.

Format: **what** / *why* / evidence / what would overturn it.

---

## D-G01 — Refine by rerunning the HISTMAKER, not by rebuilding the cache

**A finer gen grid is a histmaker change, not a cache change; a finer cache on
its own buys exactly nothing.**

*Why.* The response matrix the model folds through is
`P(b|g) = R_raw(b,g)/N_gen(g)`, read out of the datacard's auxiliary, which
setupRabbit took from the histmaker's `nominal_prefsr_yieldsUnfolding`. Its gen
axes are not free parameters of the analysis:

```
ptVGen   = rebin_pt(reco ptll edges)          # one gen bin per TWO reco bins
absYVGen = positive half of the reco yll edges
```
(`wremnants/production/unfolding_tools.py:rebin_pt`,
`wremnants/utilities/binning.py:get_unfolding_dilepton_axes`). Verified directly
on the production file: `nominal_prefsr_yieldsUnfolding` carries
ptVGen 20 bins `[0,1,2,…,12,14,16,18,20,24,28,33,44]` + overflow and absYVGen 10
bins — i.e. exactly the card's 21 × 10 gen grid. **That is the finest R that
exists on disk.**

Algebraically: if a gen bin `g` is split into sub-bins `g'` but `P` is only known
per `g`, then `Σ_{g'⊂g} P(b|g) σ(g') = P(b|g) σ(g)` — the fold is unchanged. So a
finer SCETlib cache with the shipped R is a no-op.

*Evidence.* `inspect_hists.py` on
`260723_Z_histmaker_davidFix/mz_dilepton_…_Corr_maxFiles_m1.hdf5`, axes printed
above; the algebra is one line.

*Overturned by* a histmaker output with finer gen axes already on disk (none
found: `rebin_pt` is applied unconditionally in `UnfolderZ.__init__`).

---

## D-G02 — Measure the trend by COARSENING, inside one build

**The resolution scan is built by merging gen bins of the shipped card, so every
resolution shares one cache, one set of SCETlib calls and one anchor.**

*Why.* The cache build is not reproducible — two builds of the same runcard
differ by 3.0e-03 in the Jacobian at a displaced point
(`knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md`). A scan made of
separately built caches would have a floor at the same size as the effect. Under
a merge map `M`, every object transforms in closed form,

```
R_raw_c = R_raw Mᵀ    N_gen_c = M N_gen    σ_gen_c = M σ_gen    P_c = R_raw_c/N_gen_c
```

and `σ_gen(p_v)` is evaluated ONCE per direction and re-folded at each
resolution. **The reproducibility floor does not enter the comparison at all**:
the same numbers are folded differently.

*Evidence.* `grain_vs_grid.py`. The implementation reproduces the reco agent's
published numbers exactly at the shipped grid — worst TOTAL max|dev|
**7.067e-03 (mufup)**, median **7.23e-04** as shipped, and **4.572e-03** with the
qT [0,1] alignment, against the README's 7.07e-03 / 7.2e-04 / 4.57e-03; GRAIN
median 6.745e-04 and worst 4.201e-03 against 6.7e-04 / 4.2e-03.

*Overturned by* nothing in the coarse direction; the FINE direction is an
extrapolation and is treated separately (D-G03).

---

## D-G03 — Get the finer point by MEASUREMENT, not extrapolation: rerun the histmaker

**Two dedicated histmaker runs were launched rather than extrapolating the
power law.**

*Why.* Extrapolating a coarsening power law past the finest measured point is
the weakest step in the chain, and the mechanism (D-G05) predicts the fine grid
does something the power law cannot capture.

*How, without touching the shared tree.* `finegen_histmaker.py` monkeypatches
`binning.get_unfolding_dilepton_axes` **in its own process** and then runs
`scripts/histmakers/mz_dilepton.py` through `runpy`. Three other sessions are
live in the WRemnants checkout; nothing on disk is modified. The reco binning is
left exactly at the card's, so the per-event reference `nominal_ptll_yll_*_Corr`
comes out on the card's own grid with no rebinning.

`helicitySig` is dropped from `--unfoldingAxes` deliberately: without it the
joint hist is filled with `nominal_weight` instead of the
`nominal_weight_helicity` partition, and since the partition is recovered by
SUMMING helicitySig (`scetlib_np/response_matrix.py`) the two give the same R —
9× smaller, and it skips the helicity-xsec rebinning a finer gen grid would
otherwise have to satisfy.

*Evidence that the patched run is sound.* On a 2-file smoke test,
`R` summed over gen against `nominal_ptll_yll` differs by **−6.6e-04**, i.e. the
known gen-|Y|>2.5 leak the reco agent measured as −7.6e-04, and nothing else.

*Overturned by* the coarsened fine run failing to reproduce the production
card's GRAIN at 21 × 10.

---

## D-G04 — The gen overflow is a RANGE defect, not a granularity one, and is
kept separate everywhere

**Every coarsening leaves the trailing gen qT bin untouched, and each metric is
reported with and without the top reco ptll bin.**

*Why.* The card's last gen bin is labelled [44,100] but is the histmaker's
ptVGen **overflow**, holding all gen qT > 44, while the correction file's qT axis
stops at 100. Merging it into a granularity ladder would mix two different
problems.

*Evidence.* The fine run resolves the two: of `N_gen`, **9.85 %** is in the
explicit [44,100] bin and **2.08 %** above 100 GeV (11.93 % total above 44,
matching the reco agent's 11.6 %). The 2.08/11.93 = 17 % that the correction
cannot reach is the independent confirmation of their "the model is 15.3 % short
there".

---

## D-G05 — The mechanism is a SAW-TOOTH, not curvature: one gen bin covers two
reco bins

**GRAIN at the shipped grid is, for 22 of the 25 directions above 3e-05, a
sign-alternating pattern locked to the gen bin boundary.**

*Why it matters.* A curvature-driven error falls like Δ²; a
two-reco-bins-per-gen-bin error is *structural* and disappears when the gen grid
equals the reco grid, which is a much stronger statement than any power law.

*Evidence.* Split the reco ptll bins into the first and second half of their
parent gen bin and take the yield-weighted signed GRAIN of each:

| direction | wm\|GRAIN\| | half a | half b | (a−b)/2 | (a+b)/2 | oscillating frac |
|---|---|---|---|---|---|---|
| lambda41.0 | 1.5e-04 | +6.8e-05 | −6.8e-05 | 6.8e-05 | 3.0e-07 | 1.00 |
| lambda21.0 | 3.8e-04 | +1.4e-04 | −1.5e-04 | 1.4e-04 | 7.4e-06 | 0.95 |
| s1. | 4.0e-05 | −3.7e-05 | +4.0e-05 | 3.8e-05 | 1.2e-06 | 0.97 |
| mufup | 1.9e-04 | +1.1e-04 | −7.0e-05 | 9.0e-05 | 2.0e-05 | 0.82 |
| **pdfCT18ZNNLO_as_0120** | 3.0e-04 | **+3.5e-04** | **+2.2e-04** | 6.4e-05 | 2.9e-04 | **0.18** |
| median over all directions | | | | 4.5e-05 | 2.0e-06 | **0.87** |

The α_s pair is the exception: same sign in both halves, so its GRAIN is a
coherent offset, not a saw-tooth. Figure: `grain_sawtooth.png`.

**Corrected by the measurement (D-G13).** This entry originally predicted the
α_s pair's coherent offset would "shrink like a power law rather than vanish".
It does neither: it does not shrink at all (1.06× from 21 × 10 to 71 × 11),
because it is not a granularity effect.

---

## D-G06 — The correction is a BIN LOOKUP, so GRAIN has an exact zero, not an
asymptote

**A gen grid that refines the correction file's own (absY, qT) cells makes GRAIN
identically zero.**

*Why.* `load_corr_helpers` builds the helper for a generator without "Helicity"
in its name as a plain `makeCorrectionsTensor(corrh)`, and
`correctionsTensor_helper.makeCorrectionsTensor` "returns what is in the bin of
the histogram" — no interpolation, and no angular dependence for this generator.
The per-event response ρ(x_e) is therefore piecewise constant on the correction
file's cells. If every gen bin lies inside one correction cell, the bin-averaged
ρ̄ equals ρ event by event and `r_B ≡ r_ref`.

*The correction file's grid* (`scetlib_dyturbo_…_CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4`):

```
qT   70 bins: 0.5 GeV to 15, 1 GeV to 40, then 42, 44, 46, …, 60, 65, 70, 80, 90, 100
absY 17 bins: 0, .15, .3, .5, .7, .9, 1.1, 1.3, 1.5, 1.8, 2.0, 2.5, …
```

Against it, **the card's gen |Y| grid is already the correction's grid minus a
single edge at 2.0**, and the card's gen qT grid is exactly 2× too coarse from
1 to 12 GeV and worse above. That is why coarsening in |Y| saturates
immediately (D-G07) and why the qT axis is where the gain is.

*Consequence for the recommendation.* The target grid is not "as fine as
affordable" but a specific finite one: the correction's cells.

*Overturned by* the correction being applied via helicities for this generator
(it is not — the name carries no "Helicity", and the `…CorrByHelicity` hists are
separate systematics), or by a future correction file with a finer grid.

---

## D-G07 — qT dominates; |Y| is already at the reference's resolution

**Refining gen |Y| is both more expensive and less useful than refining gen qT.**

*Evidence, measured.* Median GRAIN (yield-weighted mean over 780 reco bins,
median over 39 directions), coarsening one axis at a time from the shipped grid:

| gen qT bins (|Y| = 10) | 21 | 11 | 6 | 5 | 3 | 2 |
|---|---|---|---|---|---|---|
| median GRAIN | 6.69e-05 | 1.96e-04 | 5.27e-04 | 7.26e-04 | 2.04e-03 | 4.21e-03 |

| gen \|Y\| bins (qT = 21) | 10 | 5 | 2 | 1 |
|---|---|---|---|---|
| median GRAIN | 6.69e-05 | 1.26e-04 | 1.23e-04 | 1.23e-04 |

qT: a clean power law, local exponent p = 1.55 (21→11) and 1.04 at the coarse
end; per direction the 21→11 exponent has median **1.90**. |Y|: p = 0.92 for the
first halving and then **exactly flat** — coarsening beyond 5 bins adds nothing,
which is D-G06's prediction (the |Y| grid is already the correction's).

*Cost, from the production build log* (`cache_260825_p4/build.log`, 210 bins,
`target_precision_rel = 1e-4`, `--threads 210`): node set + matched σ **325.3
min**, rules **10.6 min**, resummed members **1.6 min**, fixed-order members
**715.6 min**; total **17.6 h**, cache 222 MB. Splitting |Y| doubles EVERY bin;
splitting qT to the reco grid splits only the cheap ones (D-G08).

---

## D-G08 — The bins are unequal in the FIXED-ORDER work, and the refinement we
want lands entirely on the cheap ones

**Contrary to the working assumption, per-bin cost at the production precision
is uniform in the resummed stage and concentrated in exactly two bins in the
fixed-order stage — and the reco-grid refinement touches neither of them.**

*Evidence.* Parsed out of `cache_260825_p4/cache.npz` (`SCTRULE8` rule records,
`build_cache_parallel.parse_rule_blob`), summed over the 10 |Y| bins:

| stage proxy | min/bin | median/bin | max/bin | total |
|---|---|---|---|---|
| outer nodes `n_sites` | 247 | 300 | 406 | 67 599 |
| fixed-order nodes `n_fo_w` | 396 | 396 | 10 824 | 134 739 |

`n_sites` per qT bin varies by only ±20 % (4.0 %–5.9 % of the total each), so the
325-min stage is essentially linear in bins. `n_fo_w` is not:

| qT bin | share of all fixed-order nodes |
|---|---|
| [0, 1] | **23.2 %** |
| [44, 100] | **18.4 %** |
| each of the other 19 | 2.9 – 3.7 % |

**41.6 % of the 715.6-min stage lives in two qT bins.** The reco-grid refinement
keeps [0,1] as one bin (the first reco ptll bin IS [0,1]) and keeps the tail as
one bin, splitting only the 19 cheap ones — whose `n_fo_w` is already at the
floor of 396, so each child costs the same as its parent.

*Cost model that follows.* Fixed-order nodes 134 739 → 213 411 (**×1.58**);
outer nodes 67 599 → ≈112 000 (**×1.66**, using the measured fact that narrower
bins need fewer nodes: the 1-GeV bins have 272–300 and the 4–11-GeV bins 372–400).
So **gen qT = reco ptll costs ≈1.6× the shipped build ≈ 28 h at 210 threads, and
≈420 MB**. Doubling |Y| instead costs ≈2.0× (35 h) because it doubles the two
expensive bins too.

*Overturned by* a per-bin wall-clock measurement (only node counts were
available here; the note's "2.3 min vs 25 min on different bin pairs" was
measured at `target_precision_rel = 1e-3` on a 10-bin subset and is consistent
with the `n_fo_w` spread, not with a spread in `n_sites`).

---

## D-G09 — The fit-level statement is a linearised Asimov Fisher proxy, and it
is only ever compared to itself

**No rabbit fit was run. Each resolution gets `F = Aᵀ diag(n) A + Prior` from the
same reco responses the closure uses, giving σ(α_s) and the α_s bias a residual
buys.**

*Why.* The real card floats 3731 nuisances and no fit has been run on it at all
(the reco agent's README says so). A Fisher matrix over the 18 theory directions
is an honest proxy for *differences between resolutions* and is not to be quoted
as the analysis' σ(α_s).

*Evidence it is in the right place.* At the shipped grid the proxy gives
σ(α_s) = **4.685e-04**, between the gen-level 9-floating 1.92e-04 and 18-floating
3.79e-04 and the earlier 6.16e-04 — the right order, from a completely different
construction.

*What it says.* Per unit pull of each nuisance, the α_s equivalent of the
residual at the shipped grid:

| | GRAIN | CALC | TOTAL |
|---|---|---|---|
| worst direction | **0.138 σ** (mufdown-kappaFO0.5-kappaf2.) | 0.091 σ (mufup) | 0.199 σ |
| median | 0.003 σ | 0.004 σ | 0.007 σ |
| quadrature over 39 | **0.291 σ** | — | — |

Read the α_s pair's own entry with care: 0.119 σ is per Δα_s = 0.002, i.e. a
2.8 % error on the *slope* of the α_s response, which over a realistic ±1σ
excursion is 0.03 σ, not 0.12 σ.

---

## D-G10 — Report the headline honestly: a finer grid CANNOT move the shipped
worst direction

**The shipped worst direction, mufup at 7.07e-03, is CALC-limited (its CALC is
7.47e-03 and its GRAIN 1.49e-03), and CALC is the known qT [0,1]
nonsingular-cutoff convention. No gen grid touches it.**

*Why this needs saying.* The natural way to phrase the deliverable — "this
resolution brings the worst direction from 7.07e-03 to X" — invites a number
that does not exist. The correct layered answer is in the README.

*Evidence.* `grain_scan_shipped.csv`, k = 1, m = 1: mufup TOTAL max 7.067e-03,
CALC max 7.465e-03, GRAIN max 1.492e-03.

---

## D-G11 — No cache was built tonight, deliberately; the recommendation's build
must be launched with TensorFlow capped

**Nothing in this round rebuilt a SCETlib cache.** The scan is coarsenings of the
shipped `cache_260825_p4`, and GRAIN on the two new histmakers is model-free, so
no result here can be moved by the build's non-reproducibility, by TF thread
pressure, or by a concurrent rebuild in the shared tree (the build was also
snapshotted read-only into scratch).

*What this means for the recommendation.* Grid D is 583 gen bins, so its build is
where the thread ceiling bites. `prepare_cache_for_card.py` never uses
TensorFlow — TF arrives transitively through `wremnants` — and uncapped each
build process holds ~1800 OS threads (768 `tf_Compute`, one per core) against
~135 capped; measured on a real 21-shard build, groups launched before the fix
sat at 1808/2432/2429 threads and after it at 262-902 for the same work at the
same `--threads 128`. The ceiling is **32768 OS threads per USER**, shared across
every session on this account, and the failure is silent and misattributed:
`pthread_create has failed: Resource temporarily unavailable`, exit 134, landing
on whichever process next asks for a thread. So:

```bash
export TF_NUM_INTRAOP_THREADS=4
export TF_NUM_INTEROP_THREADS=2      # BUILDS ONLY -- never for rabbit fits,
                                     # which really do use TF
```

and check `ps -u lavezzo -L --no-headers | wc -l` against 32768 before launching.
If grid D is sharded over bins, queue in ASCENDING BIN ORDER (a hole in the merged
cache is fatal to `GenFold`, a short contiguous prefix is a valid rectangle) and
stage ONE base runcard that is never moved (`--merge-bins` compares `cache.conf`
byte for byte, including the `# Base runcard:` comment).

*This round's own footprint, for the record.* The two histmakers are
RDataFrame, not TF (`-j 192` / `-j 160`, ~130 busy cores each) and both had
exited by 23:44. The three rabbit Asimov fits of D-G12 are genuine TF and were
correctly left UNCAPPED, at 1680 OS threads each; user-wide the pool was at
25 623 / 32 768 (78%) at 00:01 with those three running, and no
`pthread_create` failure appears in any log of this round.

*Source:* `knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md`.

---

## D-G12 — The fit-level check is a real rabbit Asimov A/B across gen
resolutions, with only the response changed

**Three Asimov fits were run on the same card, same cache, same 9 floating
parameters, differing ONLY in how finely the stored response resolves the gen
grid.**

*Why this is possible without a new cache.* Coarsening is a linear map, and
folding the original 210-column response with

```
R_raw_eff(b, g) = N_gen(g) · R_raw_c(b, G(g)) / N_gen_c(G(g))
```

is algebraically identical to folding a coarsened response with a coarsened
σ_gen. `R_raw_eff` has the shape the card already stores and divides by the same
stored `N_gen`, so `coarsen_card_R.py` rewrites exactly one dataset
(`auxiliary/scetlib_np/R`) and nothing else moves — not the cache, not the
parameter set, not the fit configuration.

*Verified before use.* The identity arm (`--kqt 1`) reproduces R to 4.4e-16 in
the reco marginal and to the last digit in the total; the k = 2 and k = 4 arms
change the marginal by ≤ 8.9e-16, as they must (each coarse group only
redistributes its own events).

*What it can and cannot show.* Asimov data is generated from the model itself, so
these fits measure the INFORMATION a coarser grid throws away, not the GRAIN
bias — the bias needs pseudo-data built from the per-event reference and is
covered by the Fisher projection instead (D-G09). Both effects are reported and
never conflated.

*Prediction under test (recorded before the fits returned).* The Fisher proxy
says σ(α_s) = 4.685e-04 → 4.833e-04 → 6.157e-04 for 21 → 11 → 6 gen qT bins,
i.e. +3.2 % and +31 %.

---

## D-G13 — The α_s legs' residual is NOT granularity: their reference carries an
event-level PDF weight

**Exactly two of the 39 directions fail to improve on any gen grid, and they are
exactly the two whose histmaker weight is not a pure bin lookup.**

*Evidence, measured.* From the shipped 21 × 10 grid to the correction's own
71 × 11 grid, every direction from the main `_Corr` file improves by 3× to 246×
(median ≈ 13×). The two `pdfCT18ZNNLO_as_*` legs improve by **1.06×**. Their
residual is a coherent offset rather than a saw-tooth (D-G05, oscillating
fraction 0.18 against a median of 0.87), it is concentrated at |y| > 1.8
(6.4e-04 against ~3e-04 centrally), and it survives refining gen qT, refining
gen |Y|, and resolving the qT 44–100 range.

*Mechanism, from the code.*
`scetlib_dyturbo_..._CT18Z_N3p0LL_N2LO_pdfas` is in `theory_corr_weight_map`
with `alphas=True, renorm=True`, so `define_theory_corr_weight_column` gives it

```
res(i) = <event-level LHAPDF member weight> * nominal_weight_uncorr / central_pdf_weight
```

and the applied response is the binned correction ratio TIMES that event-level
factor. The main `_Corr` generator is NOT in the map and gets
`Alias(corr_weight, nominal_weight_uncorr)`, i.e. a pure bin lookup. No gen
binning reproduces an event-level weight.

*Consequence.* For the α_s pair, 3.3e-04 yield-weighted and 0.034 σ on α_s is a
model-vs-template CONSTRUCTION difference, not a fold error, and it should be
reclassified out of GRAIN in the reco round's three-term split. In units that
matter: 0.034 σ is per Δα_s = 0.002, i.e. ~2.5 % on the SLOPE of the α_s
response, so ~0.01 σ of bias over a realistic ±1σ excursion.

*Overturned by* the direct experiment: rerun the histmaker with `_pdfas` removed
from `theory_corr_weight_map` so the correction is applied as a pure bin lookup,
and re-measure. Those two legs should then fall like every other direction. Until
that is done this is an attribution from code plus coincidence of the two sets,
not a demonstration.

---

## D-G14 — Recommend grid D, and stop there for α_s

**gen qT = the reco ptll edges to 44 GeV, continued above 44 by the correction
file's own edges (46, 48, …, 60, 65, 70, 80, 90, 100), plus the > 100 overflow;
gen |Y| = the card's ten edges plus one at 2.0. 52 × 11 = 583 gen bins.**

*Why not less.* Grid E (shipped qT, but with the |Y| edge and the resolved tail)
is 0.165 σ, i.e. no better than shipped — refining gen qT below 44 is the
necessary first move. Grid B (gen qT = reco ptll) is the single biggest step,
4.3× on the median and 2.0× on α_s. Grid C adds the |Y| 2.0 edge for 10 % more
bins and another 1.6× on the median.

*Why not more.* Grid G (the full correction grid, 781 bins) is 2.2× better than D
on the median but IDENTICAL on α_s (0.0341 vs 0.0345 σ), because both already sit
on the α_s-leg floor of D-G13. It costs ~34 % more bins and splits qT [0,1], the
single most expensive bin in the build (23.2 % of all fixed-order nodes).

*Evidence.* `03_candidate_grids.csv`, measured on the corr-grid histmaker so that
every row is the same events, weights and reco binning with only the gen grid
moving.

*Overturned by* someone caring about the non-α_s worst direction at the 1e-3
level rather than about α_s, in which case G is 12× better than D there
(0.0017 σ vs 0.0202 σ).

---

## Analytic dconv/dlnmuF (agent, 2026-08-26 overnight)

# scetlib_ad — decision record, ANALYTIC d(conv)/d(ln muF) round
# 2026-08-25/26 overnight (autonomous). STAGED for merge into DECISIONS.md.
# Same format as DECISIONS.md: WHAT was decided, WHY, WHAT EVIDENCE, WHAT WOULD
# OVERTURN it. Numbering continues from D-023.

---

## 2026-08-25/26 overnight session — the analytic muF route

### D-024 — THE GATE IS PASSED. The analytic route works, and the O(D^2)
###          worry named in D-022 is NOT the thing that limits it — SETTLED

**The question D-022 left open:** "whether ONE column suffices where
D ~ 1.15 ln f". Answered, and the answer is yes, but for a reason that was not
anticipated and that changes the construction.

**Why D^2 is not the problem.** d/d(ln muF) RAISES the alphaS order of a conv
kind by one (f -> P0(x)f -> P0xP0(x)f), and the kind set is truncated at
`fo_lvl`. The generator is therefore NILPOTENT and the D-series TERMINATES: at
fo_lvl = 2 the exact truncated-order solution is a quadratic in D, at fo_lvl = 3
a cubic. There is no D-truncation to worry about at all, at any D. What limits
the route is something else entirely: how well the fixed-order DGLAP kernels
reproduce LHAPDF's OWN grid evolution, which is what the runcard reference
refills against.

**Evidence (`dconv_dlnmuf.py`, `dconv_gate2.py`; `DrellYan.conv_probe` returns
the node's beam convolutions at ANY muF, so the exact muF dependence is
sampleable directly — no prototype needed to answer this).** Analytic
d(conv[delta])/d(ln muF) = 2g P0 + 2g^2 P1 + 2g^3 P2 against a converged central
difference of conv_probe, g = alphaS(muF)/4pi:

| muF | P0 only | P0+P1 | P0+P1+P2 |
|---|---|---|---|
| 2 | -45% | -8.0% | **-0.46%** |
| 5 | -30% | -2.9% | **-0.13%** |
| 13 | -22% | -1.4% | **+0.016%** |
| 45 | -17% | -0.61% | **+0.006%** |

The convention is fixed by SCETlib's own I1 (`k[0] = 2 Lf P0 + I1`,
Lf = log(muB/muF)): muF-independence at O(alphaS) forces the factor 2, and the
O(alphaS^2) Lf structure of I2 reproduces the same relation with alphaS at muF
(the leftover b0 Lf term is exactly the running of alphaS between muB and muF).

**What would overturn it:** a PDF set whose evolution is further from
fixed-order DGLAP than CT18ZNNLO's; a different `alphas_solution`.

### D-025 — The construction is ANALYTIC EVOLUTION + INTERPOLATED RESIDUAL, not
###          a replacement of the member interpolation — SETTLED (measured)

**What is added to the kernel:**

    cvi[k] = SUM_m W_m conv_m[k]                      <- unchanged, today's model
           + delta_k(D) - SUM_m W_m delta_k(m_pos)    <- NEW

with delta_k(D) the integrated DGLAP evolution of the ANCHOR conv vector by the
per-node displacement D = mfk_live, and m_pos the member positions the 92f1299
coordinate fix already computes. delta_k(0) = 0 identically.

**Why not just use the analytic evolution:** it is 0.2-0.5% wrong AT
kappa_F = 0.5 and 2, where the member interpolation is EXACT by construction
(`dconv_gate3.py` part C). kappa_F is the largest alphaS-relevant residual in
the whole model and the production templates and the fit's +-1 sigma sit exactly
there. Replacing the members would trade a fixed transition error for a new
kappa_F error.

**Why the correction form is safe:** it vanishes at the anchor AND at both
members, so every direction that sits at a knot -- kappa_F itself, the alphaS
pair, all 8 NP lambda, all 10 TNPs -- is UNCHANGED, and by construction rather
than by measurement.

**Also rejected, with numbers (`dconv_gate3.py` part B, real node geometry,
error on conv[delta] as a % of its true response, worst over bT):**

| construction | x2=0.35 qT22 | qT26 | qT30 | qT38 | x2=0.55 qT30 | x1,x3 qT30 |
|---|---|---|---|---|---|---|
| shipped 3-knot | 1.44% | 0.85% | 0.72% | 0.36% | 0.92% | 3.74% |
| analytic ALONE | 0.50% | 0.39% | 0.54% | 0.27% | 0.10% | 0.75% |
| Hermite (members + anchor slope) | 0.95% | 0.50% | 0.054% | 0.037% | 0.014% | 1.56% |
| **analytic + residual** | **0.42%** | **0.28%** | **0.052%** | **0.034%** | **0.083%** | **1.24%** |

Hermite (a cubic through both members with the exact analytic anchor slope) is
the runner-up and is exact at the members too, but it EXTRAPOLATES badly where
the member stencil has collapsed (qT 22 at large bT, and the x1,x3 leg at
D = -1.74 ln f), which is precisely where the shipped model is worst.

**What would overturn it:** a sigma-level measurement showing the correction
moves a non-transition direction (it cannot, but it must be checked, see D-028).

### D-026 — The evolution coefficients are computed from a QUADRATIC model of
###          alphaS in ln(muF), NOT from an endpoint closed form — SETTLED

**Why:** the closed forms in the endpoint couplings (one- or two-loop, fixed nf)
were derived and MEASURED against a 256-point numerical integration
(`dconv_gate4.py`): 0.3-0.6% off above muF ~ 6 GeV and 5-14% off below it. The
reason is thresholds -- the interval [muF, muF e^D] crosses m_b (and m_c) where
the PDF's own alphaS changes nf, and no fixed-nf closed form can follow that.
0.3% on J1 is 0.3% on the response, six times what is achievable.

**What is used instead** (`dconv_gate5.py`): g(L) = alphaS(muF e^L)/4pi modelled
as a QUADRATIC through three alphaS evaluations at L = 0, D/2, D, integrated
exactly. Measured against the 256-point integration: 1e-5 .. 3e-4 on every
coefficient over the whole usable range, three alphas_run calls per node, no
quadrature loop over a live bound and no division by D (the integration variable
is v = L/D), so it is a straight line for clad and smooth through D = 0.

**A second alphaS question, measured and accepted:** the conv grids were evolved
with LHAPDF's variable-nf alphaS while the kernel runs a fixed nf = 5 solution
from alphaS(mZ) = 0.118. They agree to <= 7e-4 above 6 GeV, 3e-3 at 4 GeV,
1.5e-2 at 3 GeV, 3.6e-2 at 2 GeV. Using the kernel's own alphaS costs a factor
~1.3 on the worst low-muF node (0.46% vs 0.41%) and NOTHING above muF ~ 6.
Accepted: the alternative is to carry a second coupling into the kernel.

### D-027 — TIERS. Ship mode 1 or mode 3, NOT mode 2 — PROVISIONAL (needs the
###          sigma-level A/B, which is running)

The full alphaS^3 evolution uses seven conv kinds. Four of them (P2, P0xP1,
P1xP0, P0xP0xP0) are NOT filled at the production fo_lvl = 2. Filling them means
loading 16 more beamfunc grid families (~260 MB for CT18ZNNLO) and extending the
stored conv prefix from 11 to 15 -- which needs the nodes REBUILT.

So there are two viable tiers, and the intermediate one is measured BAD:

| tier | terms | extra cost | worst over 95 cells | median | 90th pct | worse than shipped in |
|---|---|---|---|---|---|---|
| T0 shipped | -- | -- | 104.8% | 0.919% | 7.80% | -- |
| **T1** | J1,J2,K11 | **NOTHING** | 51.1% | **0.406%** | 2.72% | 17 / 95 |
| T2 | +J3 (P2) | 5 grid families | 57.8% | 0.622% | 2.94% | 34 / 95 |
| **T3** | all 7 | 16 families, rebuild | **20.3%** | **0.322%** | **1.46%** | **4 / 95** |

(`dconv_gate7.py`: 95 diagnosable (qT, direction, |Y|, flavour, beam) cells,
"diagnosable" = the node's own muF response exceeds 1e-3 of its convolution, the
conv-level analogue of the "do not diagnose below 1e-4 of sigma" rule.)

**Why T1 works with no new kinds at all, and it is not luck:** the terms it
omits are smooth, LOW-ORDER POLYNOMIALS in D (degrees 1, 2, 2, 3), and the
residual interpolation is a quadratic through three points, so it absorbs
everything up to degree 2 exactly. T2 adds back the degree-1 piece only, which
the quadratic was already absorbing, while changing the residual's shape -- which
is why the intermediate tier is worse than either end.

**T1 is the one to prototype first** because it needs no rebuild and can
therefore be A/B'd on the EXISTING production cache, both arms from one cache,
which is the only way to get a bit-identical control (the logbook's own floor
between two separately built caches is 3e-03 in the Jacobian, larger than the
effect).

### D-028 — alphaS in the correction is taken at the ANCHOR value, not the live
###          one — PROVISIONAL

`ad_g.as0_base` rather than `pval(p, ad_g.ip_as0, ...)`. The correction then
carries NO alphaS dependence at all and the alphaS direction cannot move, which
is the property the brief demands ("confirm nothing else moves"). The induced
error is second order: a ~2% shift of alphaS on a correction that is itself
~0.5% of the response. **Overturned by:** a measurement showing the alphaS
dependence of the correction matters, i.e. that the transition x alphaS
cross-term is needed.

### D-029 — Traps hit and how they were avoided — SETTLED

1. **clad codegen stack.** The first version called an evolution helper three
   times per (channel, beam) and had a mid-function `return`. clang's
   `VarBypassDetector` recursed to death generating
   `muf_evo_coeffs_pullback` (frontend exit 139). Fixed by (a) collapsing the
   three coefficient sets into ONE combined vector before the channel loop --
   the correction is linear in them -- and (b) replacing the early return with a
   0/1 multiplier, since clad turns a mid-function return into a jump.
2. **thread_local.** `ad_muf_anl` is a plain non-thread_local global, declared in
   `ad_data.hpp` (which `ad_context.cpp` sees; `ad_kernel.hpp` is NOT included
   there). A thread_local set on the caller would not be seen inside the TBB
   workers -- the trap `set_muf_knots_used` hit.
3. **Arm separation.** The A/B script REFUSES to report a null unless the two
   arms differ on the varied point, and checks that they are identical on the
   central one (the correction vanishes at D = 0). A clean null between two arms
   is this study's known signature of a shared cached result.

### D-030 — SIGMA-LEVEL, mode 1, on the 210-bin production cache: 36 of 39
###          directions BIT-IDENTICAL and the transitions improve — SETTLED

`anlmuf_closure.py`, `cache_260824b` (210 bins, all 10 |Y| x 21 qT,
`--pdf-eig 0`), CorrZ + pdfas_CorrZ, BOTH ARMS FROM ONE CACHE via
`DrellYan.set_muf_analytic(0)` vs `(1)`, so node set, rules, members and
re-solved weights are bit-identical between them.

**The guards fired first, and they are the point:**
* central analytic/shipped - 1, max over 210 bins: **0.000e+00** exactly
* kappa_F = 2 analytic/shipped - 1: **0.000e+00** exactly -- the "nothing else
  moves" property is EXACT, as designed, not a small number
* arm separation at x2 = 0.35: 8.2e-04, so the arms did separate and the null on
  the other 36 directions is a real null, not a shared cached result

**36 of 39 directions ratio 1.00 to every digit printed**: all 8 NP lambda, all
10 TNPs, kappa_R both legs, muF both legs, both joint muF x kappa_R, both alphaS.
The shipped arm reproduces every published number of
`260825_transition_muf_coordinate_fix/after` (transitions 2.847e-03 / 1.124e-03 /
3.133e-03, mufup 1.398e-02, kappa_R 7.456e-03 / 4.518e-03, alphaS 2.152e-03 /
2.293e-03), which is the control that this build IS the shipped model at mode 0.

**The three transition directions:**

| direction | shipped max&#124;dev&#124; | mode 1 | ratio | shipped yield-wtd mean | mode 1 | ratio |
|---|---|---|---|---|---|---|
| x2 = 0.35 | 2.847e-03 | 2.273e-03 | **0.80** | 2.205e-04 | 2.043e-04 | 0.93 |
| x2 = 0.75 | 1.124e-03 | 1.657e-03 | 1.47 | 8.587e-05 | 7.749e-05 | **0.90** |
| x1,x3 | 3.133e-03 | 2.812e-03 | **0.90** | 2.143e-04 | 1.633e-04 | **0.76** |

**Honest reading.** The yield-weighted mean -- the stable statistic, and the one
that matters for a fit -- improves on ALL THREE (7%, 10%, 24%). `max|dev|` is a
single-cell statistic and improves on two of three. This is a REAL but MODEST
sigma-level gain, far smaller than the 2-14x the conv-level measurement shows,
and the reason is that the template-closure residual is not only our
interpolation error: the same cache carries the `node_cval` floor (measured
1-2e-04 per bin, response to x1..x3 identically zero, no clean fix in the
present rule format) and an instance systematic of up to 1.1e-03 between model
instances at rel 1e-3 vs 1e-4. The clean attribution is the runcard comparison.

**Do not oversell this.** Mode 1 is the WEAKEST tier, chosen precisely because it
runs on an existing cache; mode 3 is 2-3x better at the conv level and cannot be
tested this way without rebuilding the nodes.

---

## Response-matrix gen binning (agent, 2026-08-26)


---

## PDF62 cache validation (agent, 2026-08-26)


---

## Parallelism routes: frozen node set vs in-process interleave (agent, 2026-08-26)

NOTE: this agent numbered its entries D-044..D-054, colliding with the
D-044..D-048 already in this file. Renumbered here as **I-044..I-054** ("I" for
interleave); its own webdir keeps the original numbers. Cross-references INSIDE
the block below still use the agent's own D-0xx numbering -- read those as I-0xx.

HEADLINE: route 2 (single-process interleave) is NOT worth it -- it targets a
barrier worth ~7%, not the ~27% I inferred, and needs a C++ redesign of the node
cache. The real loss is the NODE-SET stage's per-bin tail. Route 1 works and is
proven byte-identical with a frozen node set; the first thing to fix is the
transitive TensorFlow import, worth 804 MB and ~1530 threads per process with no
physics risk.

# Decisions — freezing the node set and splitting the member loop across processes

Session 2026-08-26, agent workstream "nodeset-split". Staged for folding into
`studies/scetlib-ad-param-model/DECISIONS.md`. Numbering continues from D-043.
Scripts: `studies/scetlib-ad-param-model/nodeset_split/`.
Run tree (scratch, not durable):
`/home/submit/lavezzo/.claude/jobs/140d052c/tmp/nodeset/{run,run2,lowqt,bar,bar2}`.

---

## I-044 — The OUTER node set is ALREADY persisted, in the fixed-order blob — SETTLED

The cache's `fo` blob is not just "the frozen O(alphas^2) grid": each `_Fo_node`
it writes carries `(Q, Y, qT, weight)` as raw doubles, and in the PAIRED
configuration the analysis uses (`fo_node_target_rel > 0`, taken from
`target_precision_rel` on a matched calculation — the "Sharing one outer node set"
line in every build log) `_ad_bin_grid` **never adapts a grid at all**:

```cpp
if (_matched_partner) {
   const auto shared = _matched_partner->shared_outer_grid(Q, Y, qT);
   grid->assign(shared->begin(), shared->end());   // ... and cache it
   return grid;
}
```
and `shared_outer_grid` is a straight copy of `_fo_bin_grid(Q, Y, qT)`.

So the outer (Q, Y, qT) node set of every bin is an INPUT the moment
`load_fo_cache` has run, bit for bit. This is the fact the whole proposal turns
on and it was not known: the knowledge note says the node set is a byproduct.

**Caveat that must travel with this.** It holds only PAIRED. Unpaired
(`fo_node_target_rel = 0`) `_ad_bin_grid` runs its own adaptive cubature, that
grid is not serialized, and none of D-045..D-047 applies.

## I-045 — A loaded rules blob is NOT sufficient on its own; one rewarm is — SETTLED

`build_pdf_variations` needs more than `_bin_rules`. It sums over the FULL node
pool of each retained outer point (`b[0] = sum_j W0[j]`, `var.c_val` likewise
over all `ns` sites) and indexes that pool by the rule's own site record
(`flat[si] = off[fi] + (pass ? n_incl[fi] : 0) + st.node`). The blob stores only
the COMPACTED grid and the SELECTED sites, so the pool is not in it. Run
against loaded rules with nothing else, the library refuses by name:

```
py::qT::DrellYan::set_pdf_keep_nodes: neither cache is populated, so there is
no geometry to keep. Evaluate once at the reference member first.
```

The missing piece is only the per-point bT node set (`_Ad_node_cache::Entry`),
and regenerating it is deterministic: the bT integrator's single mutable member
`_store` is a double-exponential abscissa table that `_init()` derives from
`_precision` alone, not accumulated history. So the working recipe is

1. `nons.load_fo_cache_bytes(...)`  — FIRST, so the outer grid is the file's
2. `sigma.prepare(bins, p0)`        — the "rewarm": repopulates the bT nodes
3. `sing.load_bin_rules_bytes(...)` — LAST, so the frozen site selection is final
4. `build_pdf_variations` / `build_fo_pdf_variations` on the member slice

## I-046 — D-013 is SUPERSEDED: members MAY be split across processes, if every
## process LOADS the same frozen node set — SETTLED (byte-identical)

260820 Z card, `--subset 0,1/19,20` (4 bins, qT [33,44] and [44,100] x |Y|
[0,0.15] and [0.15,0.3]), `target_precision_rel = 1e-3`, `n_train 9`,
`--pdf-eig 2` (8 members = 2 eig pairs + alphaS pair + muF pair, 4 atomic pairs),
P = 26, `SCETLIB_BUILD = scetlib-cms/build-fix`. `compare_caches.py --bytes`:

| test | verdict |
|---|---|
| separate process, loaded node set, all 8 members **vs** the originating process's own serial member loop | **IDENTICAL** |
| merge(members 0:4, members 4:8 — two processes) **vs** one process, same frozen node set, all 8 | **IDENTICAL** |
| members 0:4 at `--threads 8` **vs** members 0:4 at `--threads 16` | **IDENTICAL** |

"IDENTICAL" is the full structural comparison: header, rule-blob fingerprint,
opts, meta, anchor, 0 of 4 bins differing in the nominal rule, 0 of 32
(bin, member) records, frozen fixed-order grid 0 of 4 bin keys, 0 of 8 member
delta sets, both muF grids, `var_bins`.

**The control is what makes this a result.** Three INDEPENDENT full builds of the
same configuration at the same `--threads 8` gave retained sites/bin
`[363, 368, 400, 399]` / `[363, 365, 400, 400]` / `[363, 365, 400, 400]` — two
agreed and one did not. So the D-013 hazard is real AND intermittent, which is
the worst kind: an independent-shard merge would sometimes coincide and be
silently accepted. Freezing the node set removes the coin flip by construction
rather than by luck.

**What D-013 should become:** never split PDF members across processes that each
BUILD their own node set. Splitting them across processes that each LOAD one
frozen node set is exact.

## D-046b — WHY independent builds diverge: the NNLS site selection and the
## node STORAGE ORDER, not the node set's content — SETTLED (decoded)

Decoded the `fo` blobs of three independent builds node by node (297 nodes/bin,
`Q, Y, qT, weight, C[3][3], mu_ref, err, rule, n_orders, muR_resolved`):

* every build has the **same node count** in every bin;
* the raw bytes differ in 3 of 4 bins, with O(1) relative differences in `Q`,
  `weight`, `mu_ref`, `err` and the `C[n][k]`;
* **sorted, all three grids are bit-identical in every bin.** The difference is
  purely the ORDER the nodes are stored in — the grid is filled by a parallel
  loop over subregions — not their content.

So the outer node set is deterministic *content* in a nondeterministic *order*,
and the rule's `Site::point` / `Site::node` index into that order. Combined with
the genuinely nondeterministic NNLS site selection in `build_bin_rules`
(363/368/400/399 against 363/365/400/400), that is the whole of the D-013
hazard, and freezing pins both.

**Two documentation corrections that should go upstream.** The `fork_member_build`
docstring and the class docs blame "the integrator objects it hands out keep
internal buffers". That is not the mechanism: `integrator_de_oscillatory`'s only
mutable member is `_store`, a double-exponential abscissa table that `_init()`
derives from `_precision` alone. The real causes are the two above.

**And a gap in our own validation tool.** `compare_caches.py --bytes` already
knows that `_Fo_cache::bins` is an `unordered_map` and compares per bin key, but
it compares each bin's grid as a byte range — so a node PERMUTATION inside a bin
reads as "frozen grid differs in 3 of 4 bins", a false positive. It should sort
the nodes before comparing. (It did not affect any conclusion here: every
IDENTICAL verdict in D-046 came out identical including the raw grids.)

## I-047 — A member shard's prologue collapses by ~150-200x — SETTLED (measured)

The expensive half of `prepare` is the fixed-order node ladder (the source puts a
fixed-order point at ~130x a resummed one) and that half is what the fo blob
holds; `build_bin_rules` is not needed at all.

| | full build | member shard |
|---|---|---|
| 4 bins, qT 33-100, threads 8: `prepare` | 31 s | — |
| load the fo blob | — | 0.05 s |
| rewarm (`prepare` on the LOADED outer grid) | — | **1.2-1.8 s** |
| `build_bin_rules` | 163 s | 0 (loaded) |
| **prologue** | **194 s** | **1.3-1.9 s (150x)** |
| 2 bins, qT [1,2], threads 16: `prepare` / rules | 34 s / 89 s | — |
| rewarm | — | **0.6 s** |
| **prologue** | **123 s** | **0.6 s (205x)** |

The rewarm/`prepare` ratio is 3.9 % at qT 33-100 and **1.8 %** at qT [1,2], i.e.
it gets BETTER where the node set is expensive, which is the mechanism (the
fixed-order ladder is a larger share of `prepare` at low qT and it is the part
that comes from the file). Matched bin sums reproduce exactly across the round
trip: 14.92940684 pb and 2.411335343 pb, freeze and member process alike.

## I-048 — The member barrier is REAL and it costs 5-8 %, not 27 % — SETTLED (instrumented)

The claim under test was "the ~55 missing cores of the 200-thread 210-bin build
are threads idling at the member barrier". Instrumented directly rather than
inferred: 1 Hz sampling of running-thread count and CPU rate
(`nodeset_split/sample_threads.py`) on two 50-bin builds at `--threads 48` —
bins:threads = 1.04, the same ratio as the production 210:200 — 20 members,
P = 32. Trace plot: `~/public_html/alphaS/260826_nodeset_split_barrier/`.

**A: 50 bins, qT 20-100 x all 10 |Y| (uniform cost).**

| stage | wall | busy cores of 48 | core-s lost | drains below 90 % of pool |
|---|---|---|---|---|
| outer node set | 1.18 min | 47.4 (99 %) | 1 % | 0 |
| bin rules | 8.54 min | 46.5 (97 %) | 3 % | 1 |
| resummed members (20) | 4.6 min | 32.8 (68 %) | **32 %** | **exactly 20**, 8.1 s each |
| fixed-order members (20) | 14.9 min | 46.0 (96 %) | **5.3 %** | **20-24**, 1.9-2.5 s each |

**B: 50 bins, qT [1,2] / [5,6] / [10,11] / [16,18] / [44,100] x 10 |Y| (3.3x cost spread).**

| stage | wall | busy cores of 48 | core-s lost | drains below 90 % |
|---|---|---|---|---|
| outer node set | 3.52 min | 42.0 (**87 %**) | **12.9 %** | one 23 s tail at the end |
| bin rules | 11.1 min | 47.2 (98 %) | 2.5 % | 1 |
| resummed members (20) | 4.8 min | 33.6 (70 %) | 30.7 % | **exactly 20**, 8.8 s each |
| fixed-order members (20) | 19.3 min | 45.8 (**95 %**) | 5.8 % | **18**, 3.3 s each |

**The barrier exists exactly as predicted — one pool drain per member, 20 of them
for 20 members, in BOTH member stages and in both builds. What was wrong is its
size.** The drain is ~8 s of a ~14 s resummed member step (59 % of its duration,
32 % of its core-seconds) but only 1.9-3.3 s of a ~45-60 s fixed-order member step
(4-6 %). Since the fixed-order half carries ~95 % of the member cost at 210 bins
(7.6 min/member against 0.40), the barrier's weighted cost over the member work
is **0.32 x 5 % + 0.053 x 95 % = ~7 %**, and over the whole build A it is
6533 of 84 144 core-s = **7.8 %**. It cannot be the 27.5 % (145 of 200).

**Where the rest of the cores went.** Build B's node-set stage runs at 87 %
against build A's 99 %, purely from a 3.3x bin-cost spread, and the loss is one
long tail at the end rather than periodic drains. That is D-036's mechanism (the
node set carries only ~3-4 cores per bin, so a spread leaves a tail), and at 210
bins the qT [0,1] bins are >27 min against 0.2-1.0 min for every other ptV shard
— a ~30x spread against B's 3.3x. **The node-set tail, not the member loop, is
where the missing cores are.**

**Consequence for the proposal.** It stands, but the barrier argument is worth
~7 %, not ~28 %. Its real value is D-047's 150x cheaper shard prologue and the
scheduling freedom in D-049.

## I-049 — What it buys, honestly: nothing on one saturated node at 210 bins;
## the win is the critical path and the fan-out — PROPOSED (needs Luca)

Anchored on the measured production numbers (knowledge note: 210 bins at 200
threads, `prepare` 21.9 min, rules 4.4 min, resummed members 0.40 min/member;
monolith 8.7 h for 62 members, so fixed-order members ~7.6 min/member) the
210-bin member work is ~72 000 core-min. On this node (768 cores) at the 96 %
packing measured in D-048 that is **~1.6 h — exactly the wall clock the existing
21-way bin split already achieves.** The 8.7 h monolith was not
barrier-limited; it was limited to `--threads 200` on a 768-core machine.

So on one node, at 210 bins, the frozen node set buys **no wall clock**. What it
buys is:

1. **The critical path of a bin-sharded partition.** Today the shard that owns
   qT [0,1] must run its ~27 min prologue AND then all 62 members over its bins,
   serially, and it sets the partition's wall time (D-032, D-036). With the
   member axis its 62 members fan out over up to 31 processes, so its critical
   path is prologue + one pair. On the 781-bin grid this matters more, because
   that grid SPLITS both expensive fixed-order qT cells (D-041).
2. **A second, orthogonal work axis**, so tiles can be sized to the cores
   available (bins x members, up to 21 x 31 = 651 tiles at 210 bins) instead of
   being forced to whole bin groups whose node-set stage saturates at ~3-4
   cores/bin.
3. **Members as partial results.** Today a shard's bins are unusable until all
   62 members are done; with the member axis the whole grid is available at
   reduced member coverage early.
4. **A legal multi-machine fan-out for the member loop**, at a per-worker
   prologue of ~4 min (rewarm at 781 bins, extrapolated from D-047) instead of
   ~1.6-2 h.

**On the 781-bin grid.** The D-041 bracket of 55-80 h was quoted "at 210
threads". Scaling the 210-bin member work by the same 3.7-4.5x and packing it at
96 % on 768 cores gives **~5.6-7.3 h of member work plus a ~1.6-2 h freeze**,
i.e. **~7-9 h on one saturated node** — so most of the 55-80 h is the 210-thread
choice, not the architecture. Divided over C nodes the member half goes as 1/C;
on 4 nodes ~3.5-4 h all in. **These are projections from measured per-stage
costs, not measurements; the 781-bin runcard has never been built.**

## I-050 — Do NOT switch production yet; three things to check first — PROPOSED

The existing shard-and-merge path stays the production route (unchanged). Before
the frozen-node-set route replaces anything:

1. **Re-run the byte-identity chain at production scale** — 210 bins, 62 members,
   P = 53, and on the production library `build-nak` (D-031), not
   `build-fix` (which lacks 92f1299 and was used here only because it is the
   tree that has the CT18ZNNLO beamfunc grids). Nothing structural should
   change, but D-046 was proven at 4 bins / 8 members / P = 26.
2. **Mark the node-set-only cache.** It is a perfectly valid `.npz` with zero
   member records (1.0 MB at 4 bins). A loader accepts it and only fails later
   with "PDF variations were not built" — loud, but it should carry a sidecar
   the way `--members` shards do so it can never be mistaken for a cache.
3. **Confirm the paired assumption in the runcard** (D-044) rather than assuming
   it: refuse to write a node-set-only cache when `fo_node_target_rel = 0`.

---

# Addendum, same session: the coordinator's three narrowed questions

## I-051 — Item 3 ANSWERED, and it is a third option: the member OUTPUT is written
## straight through; the member INPUT is one shared, in-place-mutated node cache — SETTLED

Neither branch of the question as posed. Reading `build_pdf_variations` and
`set_pdf_keep_nodes`:

**Outputs: straight through.** Inside `_ad_parallel_run` over bins, everything a
bin produces goes directly into its own per-member record — `var.w[si]` (via
`rule_min_norm_update`), `var.nd[si]`, `var.c_val`, `var.c_grad`, and on the
fixed-order side `_fo_var_d[mi][n]`. The per-bin working set (`W0`, `V0`, `G0`,
`A`, `b`, `flat`, `gmap`) is local to the lambda and dies with the work item.
Nothing accumulates across the member step. So the live cost per in-flight item
is genuinely scratch, and *by that criterion* a queue over (bin, member) items
would be cheap.

**But the input is the blocker.** `set_pdf_keep_nodes` is called once per member,
OUTSIDE the parallel loop, and it:

1. calls `set_pdf(...)`, a **whole-object reset** ("resets, including the
   caches"), then puts the saved geometry back;
2. for the fixed-order side, **replaces every bin's grid with a fresh copy**
   (`std::make_shared<_Fo_bin_grid>(*kv.second)`) and refills each node's
   coefficients in it;
3. for the resummed side, builds a **complete new copy of every node-cache
   `Entry`** into a `std::vector out(keys.size())`, refills the convolutions in
   each copy, and only after the parallel region swaps them into `keep->map`.

So the convolutions every member reads live in ONE shared structure that holds
exactly one PDF member at a time, and switching it **transiently holds two full
copies of the node cache**. Convolutions are ~96 % of that cache.

**Consequence for route 2 (single-process queue over (bin, member)).** It is not
a scheduling change; it is a C++ redesign. K members in flight need K
independent convolution stores, and the API cannot express that — the node cache
is one per `DrellYan` object and `set_pdf` resets the whole object. The
"bounded two-member double buffer" would need two node caches, i.e. 2x the
dominant memory object, with no way to ask for it. **The barrier is a STATE
barrier, not an accumulation barrier.**

**Consequence for route 1 (frozen node set, one member per process).** Separate
address spaces give each member its own convolution store for free, which is
precisely the thing route 2 would have to build. Route 1 is available today and
is proven byte-identical (D-046).

Also confirmed as the coordinator said: kernel state is `thread_local`
(`src/qT/ad/ad_state.cpp`: `ad_g`, `ad_h`, `ad_nd`, `ad_beta`, `ad_p0`,
`ad_conv_var`, `ad_fo`, `ad_fom`, all `thread_local`), so `s_ad_mutex` is an
API re-entrancy guard and never needs changing.

## I-052 — Item 4: 804 MB of every build process is TensorFlow the builder never
## calls — the memory twin of D-030 — SETTLED (measured)

In-container, one import at a time (`--threads 16`, 260820 Z card, rel 1e-3):

| | VmRSS |
|---|---|
| bare python | 12 MB |
| + numpy, h5py | 48 MB |
| + `scetlib_qT` | 54 MB |
| **+ tensorflow** | **858 MB** |
| after `configure` (LHAPDF central set, beamfunc grids, runcard) | **930 MB** |

**TensorFlow costs 804 MB per build process and `prepare_cache_for_card.py`
never uses it** — it arrives transitively through `wremnants`, exactly as the
~1530 wasted OS threads of D-030 do. Today's 21-process bin split therefore
carries **~17 GB of resident TensorFlow that nothing calls.** That is a bigger,
cheaper win than any architecture change and it is the same one-line-of-imports
fix as D-030.

Everything else, measured (VmHWM in brackets):

| build | after `configure` | after `prepare` | after rules | after members |
|---|---|---|---|---|
| 4 bins qT 33-100, 8 members | 930 | 1020 | 1189 [1355] | 946 [1355] |
| 20 bins qT 33-100 | 930 | 1229 | 1596 [1717] | — |
| 50 bins qT 1-100 mix, 20 members | 930 | — | — | 5382 [**6818**] |

Fitting the two same-qT builds: the frozen node cache is **13 MB/bin** and node
cache + nominal rules together **25 MB/bin** at qT 33-100, on a fixed intercept
of ~1.09 GB. Extrapolated at that (cheap-bin) rate a 210-bin build needs
~6.3 GB before any member and a 781-bin one ~21 GB; adding members at the note's
~1.14 MB/bin/member puts a 210-bin 62-member monolith at ~21 GB (consistent with
the note's "~15 GB uncompressed" rules blob) and a 781-bin one at ~75 GB. Memory
is a real constraint on the bin axis, which is the other reason a member split
must not be "one process per member over ALL bins". Denser bins cost more — the 50-bin mixed build
peaks at 6.8 GB, i.e. ~120 MB/bin including its 20 member records (the knowledge
note's ~240 MB/member at 210 bins is ~1.14 MB/bin/member). The rules stage's
transient NNLS working set is the peak: +335 MB over `prepare` on 4 bins, and it
is released afterwards (RSS falls back to 946 MB).

**So the accounting is:** ~930 MB duplicated per process of which 86 % is dead
TensorFlow; the node cache and rules are the part that is genuinely per-process,
and they are bounded by that process's BIN count, not by members. The duplication
is a real cost today (17 GB of it is waste) and it is fixable without touching
the architecture.

## I-053 — Item 5: the barrier measurement — see D-048

Done and reported above. The instrumentation is a 1 Hz sample of running threads
and CPU rate rather than a per-bin finish-time log, because the bin loop is
inside C++ and the session is read-only; but it measures the same thing, since a
pool that drains over 8 s IS bins finishing at spread times. Result: **exactly
one drain per member, in both member stages, in both builds** — 8.1-8.8 s per
member in the resummed stage (32 % of its core-seconds) and 1.9-2.5 s in the
fixed-order stage (5 %). Weighted by where the cost is, **~7 %**, not the
inferred 27.5 %. The rest is the node-set stage's per-bin tail (87 % on a 3.3x
cost spread against 99 % on a uniform one).

## I-054 — RECOMMENDATION: route 1, as a 2-D tile, and fix the TF import first — PROPOSED

**Do not pursue route 2** (single-process queue over (bin, member) work items).
It needs the convolution store to be per-member, and today it is one per object,
reset wholesale by `set_pdf` and transiently doubled at every switch (D-051).
That is a C++ redesign of the node cache for a barrier worth ~7 % (D-048).

**Pursue route 1**, but as a two-dimensional tile rather than "one member per
process over all bins":

* **freeze** the node set once per bin group (the existing `--subset` +
  `--merge-bins` machinery already splits and merges the bin axis);
* run **(bin group x member group)** tiles, each loading its bin group's frozen
  node set — prologue ~1 s instead of ~200 s (D-047), and its node-cache
  footprint bounded by its BIN count, not by the full grid;
* merge on both axes with `build_cache_parallel.py`, which already does members
  from `.shard.json` and bins from `--merge-bins`.

Sizing it is now arithmetic rather than guesswork: memory per tile is
930 MB (or **126 MB once TF is gone**) + ~13-120 MB/bin + ~1.14 MB/bin/member.

**Order of work, by value per unit of risk:**
1. **Drop the transitive TensorFlow import from the build path.** ~804 MB and
   ~1530 threads per process, no physics risk, no architecture change.
2. Re-run the D-046 byte-identity chain at production scale on `build-nak`.
3. Only then add `--nodeset` / `--freeze-only` to the driver.

The existing shard-and-merge path stays production throughout.
