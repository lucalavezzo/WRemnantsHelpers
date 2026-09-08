# Slide material: three validations and two fits, from pushed scripts

Everything below runs from a plain `WRemnants` checkout on
**`scetlib-ad-param-model`** (PR #715), head `f479d015` or later. No script lives
outside the repo any more -- the one that did (`validate_variations_reco.py`) was
moved in on 2026-09-08 for exactly this reason.

## Paths

```bash
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CORRDIR=$WREM_BASE/wremnants-data/data/TheoryCorrections
BASE=scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO

# the 770-bin autodiff cache: 770 gen bins on the theory correction's own grid,
# 62 PDF members, 53 parameters
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full

# the reco card WITH the response auxiliary (3673 systs).  `adexcl` is the
# sibling that keeps the PDF templates (3731); use `adexclpdf` for a fit where
# the model owns the PDFs too.
CARD=$CEPH/260908_Z_2D_card_corrgrid770/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5

# the histmaker the card's response comes from
HM=$CEPH/260907_Z_histmaker_corrgrid/mz_dilepton_${BASE}_Corr_maxFiles_m1_corrgrid.hdf5

# theory corrections: main + alphaS + PDF eigenvectors
CORR_MAIN=$CORRDIR/${BASE}_CorrZ.pkl.lz4
CORR_AS=$CORRDIR/${BASE}_pdfas_CorrZ.pkl.lz4
CORR_PDF=$CORRDIR/${BASE}_pdfvars_CorrZ.pkl.lz4

# SCETlib: the frozen VALIDATED snapshot every number in this study was made
# against (b66f8de, libscet-qT.so md5 71b5e68a0cfed89326ff4ed521d37300)
LIB=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot

MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
```

Environment, once per shell (`incontainer.sh` in this directory does exactly this):

```bash
singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ \
  /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest bash
source /opt/venv/bin/activate
source $WREM_BASE/setup.sh
export SCETLIB_BUILD=$LIB/build && source $LIB/setup.sh
```

---

## Validation 1 -- sigma_gen vs the theory correction, on the correction's own binning

```bash
python3 scripts/rabbit/scetlib_ad/compare_to_scetlib_run.py \
    --conf $CACHE/cache.conf --cache $CACHE/cache.npz \
    --reference $CORR_MAIN --piece matched \
    --threads 48 --plot-dir <out>/gen_vs_corr --tag gen_vs_corr
```

Both sides are bin-integrated and get summed onto their **common** bin edges --
exact, no interpolation -- and the script refuses to run unless each side tiles
that grid exactly. Because the cache was built *on* the correction's grid, the
common grid **is** the correction's grid, which is what makes this the
"original theory-correction binning" comparison. Writes `..._qT` and
`..._absY` projections.

`--piece matched`, not `resummed`: this build carries `3a8db11`, where
`resummed_only()` returns the matched total, so `--piece resummed` would be
silently 34 % wrong.

**Measured, 2026-09-08** (11 x 70 = 770 common bins, |Y| 0..2.5, qT 0..100):

| | |
|---|---|
| total, ours/ref | **1.000089** |
| per-bin \|ours/ref - 1\|, median | **7.2e-05** |
| per-bin, max | 5.2e-02, in qT [0, 0.5] |

The max is confined to the lowest qT bins and falls monotonically
(5.2e-2, 3.1e-2, 2.8e-2, 1.2e-2, 7.0e-3, ... under 1e-3 by qT ~ 6 GeV, under
3e-4 everywhere above 15 GeV).

**Attribution, from `260908-ptll-residual` -- the same effect chased at reco
level.** Two distinct causes, not one:

1. **Dominant, qT < 1 GeV: the nonsingular qT-cutoff convention.** We vanish the
   nonsingular below **0.1 GeV**; the production template was made with
   `--qtCutoff 1.0`. Removing our nonsingular below the cut brings gen qT
   [0, 0.5] to model/template = **1.000063** and [0.5, 1] to **1.000009**, and
   two independent routes agree on the reco bin-0 prediction to **9e-06**.
2. **Smaller, above the cut: nonsingular accuracy.** The model is **+0.91 %**
   high at gen qT [1, 1.5] -- DYTurbo's fixed order vs SCETlib's analytic V+jet.
   No cutoff change touches this one.

The run prints `settings cross-check: OK`, and that does **not** cover this.
The cutoff is recorded in neither config -- ours is announced at runtime
("nonsingular to vanish below qT = 0.1 GeV"), the template's exists only in its
production command line -- and the whitelist the cross-check compares is 13
keys, none of them the cutoff. Do not read "OK" as "same nonsingular
convention".

## Validation 2 -- sigma_reco vs the histmaker nominal carrying the correction

```bash
python3 scripts/rabbit/scetlib_ad/validate_reco.py \
    --datacard $CARD --histmaker $HM \
    --cache $CACHE/cache.npz --conf $CACHE/cache.conf \
    --reference histmaker --threads 48 --tag card770 \
    --plot-dir <out> --plot-axes ptll yll
```

Model `= R @ sigma_gen(p_anchor)`, reference `=` the histmaker's reco `nominal`
(which carries the theory correction). **SHAPE only** -- one global scale is
applied first, by design; use `--no-match-norm` for the absolute comparison
instead.

## Validation 3 -- the variations, at reco level, vs the histmaker's own templates

This is the one a fit actually uses.

```bash
python3 scripts/rabbit/scetlib_ad/validate_variations_reco.py \
    --datacard $CARD --histmaker $HM \
    --cache $CACHE/cache.npz --conf $CACHE/cache.conf \
    --corr $CORR_MAIN $CORR_AS $CORR_PDF \
    --threads 64 --plot-dir <out>/reco_variations --csv <out>/reco_variations.csv
```

For every direction it compares the model's folded response
`[R @ sigma_gen(p_v)] / [R @ sigma_gen(p_anchor)]` against the histmaker's own
`H_v / H_central`, and splits the residual exactly three ways:

    r_mod / r_ref = (r_mod / r_A) x (r_A / r_B) x (r_B / r_ref)
                     \__ CALC __/   \__ WGT __/   \__ GRAIN __/

CALC is ours to fix (SCETlib / the cache); GRAIN is pure gen-binning
granularity and contains no model physics at all. That split is the reason for
the 770-bin grid: on the old 210-bin grid GRAIN beat CALC in 72 of 97
directions, and on this one it is 46 of 97.

The gen-level counterpart, if you want the response before the fold (no card
needed, and non-circular):

```bash
python3 scripts/rabbit/scetlib_ad/validate_variations.py \
    --corr $CORR_MAIN $CORR_AS $CORR_PDF \
    --cache $CACHE/cache.npz --conf $CACHE/cache.conf \
    --threads 48 --profile --plot-dir <out>/gen_variations
```

---

## Fit 1 -- Asimov

```bash
rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o <out> \
    --postfix AS770 \
    --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=48
```

An Asimov fit never runs the minimiser (`ifit = -1`), so **100 % of its runtime
is the postfit Hessian pass**. `--jitCompile off` is mandatory and enforced at
construction.

## Fit 2 -- one toy, all NPs frozen

```bash
rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o <out> \
    --postfix TOY770NP -t 1 --earlyStopping 100 \
    --freezeParameters lambda2 lambda4 delta_lambda2 lambda2_nu lambda4_nu \
    --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=256
```

All five lambda are named explicitly because rabbit matches with `re.fullmatch`
-- `lambda2` freezes `lambda2` and **not** `lambda2_nu`. `lambda_inf` and
`lambda_inf_nu` are already `DEFAULT_FROZEN`, so the whole NP function is then
pinned at the cache's own physical tune (`cache.conf`: lambda2 0.4, lambda4 0.4,
delta_lambda2 0.0, lambda2_nu 0.15, lambda4_nu 0.0).

Freezing rather than dropping them from `fit_params` keeps the fit vector at
47 + 3673 = 3720, so the toy's thrown constraint centres -- and therefore the
pseudodata -- stay bit-identical to the free-NP arm's, which is what makes the
two comparable.

Result of this configuration, 2026-09-08: converged, EDM 3.485e-05, 0 negative
yields of 3720.

**Blinding is on.** Neither fit passes `--unblind`, so an unknown shift is added
to the alphaS POI; uncertainties and pulls are meaningful, the central value is
not.

---

## The one thing not yet in a PR

Both fits need the two-line `hvp` zero-seed skip in
`scetlib-cms/py/scetlib_tf.py`, which is **SCETlib MR !11** (branch
`hvp-fast-covariance`, commit `8e92c14`) and is still **open**. Without it the
Asimov postfit Hessian costs ~77x more -- 7260 s versus 49 s, measured, bitwise
identical results. Until it merges, either build that branch or put the patched
file first on `PYTHONPATH`; `260908-fit-770/incontainer.sh` does the latter and
prints an md5 check that the fix is present.
