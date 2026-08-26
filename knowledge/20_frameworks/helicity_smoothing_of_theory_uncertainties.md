# Smoothing theory uncertainties via the helicity cross sections — why it works

Source: worked out from the code + AN in session 2026-07-28; every quantitative
claim below is reproduced by the toys in
`../../studies/helicity-smoothing-mechanism/`.
Last updated: 2026-07-28.

## Topic

Why `make_uncertainty_helper_by_helicity()` reduces the statistical noise of the
PDF / α_s / quark-mass nuisance templates, what it assumes, and what it does
*not* do. Complements `theory_weights_and_corrections.md` §2.8–2.11, which gives
the weight formulas; this note gives the mechanism and the validity conditions.

AN reference: `uncerts.tex` §`sec:smooth-by-helicity`, `theory.tex`
§`subsec:theory:alphas`. **The AN's stated reason ("quantizes the CS angles into
just nine helicity cross sections, largely reducing the dimensionality of the
histogram") names the wrong cause** — see "Corrections to the AN wording" below.

## Code map

| piece | where |
|---|---|
| builds the helper from the gen hists | `WRemnants/wremnants/production/theory_corrections.py:1349` `make_uncertainty_helper_by_helicity` |
| per-event weight evaluation | `WRemnants/wremnants/production/include/theory_corrections.hpp:157` `CentralCorrByHelicityHelper` |
| moment fill weights M_i | `WRemnants/wremnants/production/include/theoryTools.hpp:148` `csAngularMoments` |
| harmonics A_i | `WRemnants/wremnants/production/include/theoryTools.hpp:124` `csAngularFactors` |
| gen inputs (`--addHelicityAxis`) | `WRemnants/scripts/histmakers/w_z_gen_dists.py:396`, driven by `scripts/corrections/corrs_by_helicity/make_alphaS_gen_hists.py` |
| reco-level filling | `WRemnants/wremnants/production/systematics.py:626` `add_pdfAlphaSByHelicity_hist` (and `:588` for PDFs) |

## Notation

```
w_e   nominal MC weight of event e
r_e   variation ratio w_e^var / w_e^nom  (for α_s: PDF-member ratio × the σ_UL corr)
x_e   the 6 gen boson variables (Q, |y_V|, p_T^V, q_V, cosθ*, φ*), pre-FSR
g     gen cell = one (Q, |y_V|, p_T^V, q) bin of the by-helicity histogram
b     reco template bin (Z: 40×20×8×8 = 51,200; W: (p_T^μ, η^μ, charge))
ρ(x)  = E[r | x]      the physics: smooth, ρ−1 ~ 0.5%
s²(x) = Var(r | x)    the MiNNLO weight tail: no physics content
```

## 1. Mechanics — the bin values are sums of weights; the mean is the ratio

`--addHelicityAxis` fills **every event into all 9 helicity slots** with weight
`w_e · M_i(Ω_e)`. Since `scales_0 = 0, offsets_0 = 1` we have `M_0 ≡ 1`, so

```
h_{-1} = Σ_e w_e                 <- the i=-1 slot IS the plain sum of weights
h_i    = Σ_e w_e M_i(Ω_e)        <- same events, signed harmonic factor
h_i / h_{-1} = <M_i> = A_i       <- the mean; the division is implicit
Σ_i h_i A_i(Ω) = W · [(1+cos²θ*) + Σ_j A_j P_j]   = W × angular density
```

The last line is the *exact algebraic inverse* of the fill, not a fit. The helper
divides two such reconstructions, so W and all normalization cancel and what comes
out is the ratio of the varied to the nominal angular density.

Reordering the double sum (pure algebra, verified to 9 digits) gives the form that
answers "a mean over which events?":

```
R(Ω) = Σ_e w_e r_e K(Ω,Ω_e) / Σ_e w_e K(Ω,Ω_e),   K(Ω,Ω') = Σ_i A_i(Ω) M_i(Ω')
```

So it **is** a mean weight ratio per bin — a kernel-weighted one over every event
in the gen cell. `K` is signed (measured range −2.4 … +12) and global: at a given
Ω the events in the *opposite* hemisphere are 50% of the sample and carry 31% of
the total |kernel weight|. A histogram in the angles is the special case where K
is the indicator function of one bin. Measured at one Ω, 400k events in the cell:

| estimator | events used | accuracy |
|---|---|---|
| mean ratio in 8 cosθ* bins | 12.5% | 1.5e-3 |
| mean ratio in 64 cosθ* bins | 1.6% | 2.1e-3 |
| 9 harmonic moments | 100% | 1e-4 |

`K` is the reproducing kernel of the ℓ≤2 space under the **flat** measure on the
sphere — which is why the by-helicity hists must be filled over the **full**
lepton phase space. Restrict the sphere and the harmonics stop being orthogonal,
the moments mix, and K stops reproducing.

## 2. Why the noise drops (the only mechanism)

`r = ρ(x) + [r − ρ(x)]` is an identity. Within a reco bin,

```
Var(δ_b) = Var_b(r)/N_b,   Var_b(r) = Var_b[ρ(x)] + E_b[s²(x)]
                                      └ ~(1e-4)² ┘   └ ~(0.05)² = V ┘
```

so essentially *all* of the raw template's noise comes from the part of r that is
unrelated to the physics. Replacing `r_e → ρ̂(x_e)` deletes that term. The price is
the error on ρ̂, estimated from all `N_g` events of the cell with p = 9 parameters:

```
Var(smoothed η_b)/Var(raw η_b) ≈ p/M
```

with **M = the number of reco template bins that one gen cell's events populate**.
At the fit level, with `n_b` data counts and κ = N_MC/N_data, template noise adds
fake likelihood curvature

```
ΔI = Σ_b n_b Var(η_b) = N_bins · V / κ        (raw)
```

Three consequences, all confirmed numerically:
- ΔI does **not** depend on MC-per-bin — only on the *number of bins* and κ. Fine
  binning is what breaks you (Z: 51,200 bins).
- The prior gives I = 1, so the postfit width is 1/√(1+ΔI): ΔI ≈ 5 already means a
  nuisance constrained to 0.4σ out of pure noise.
- Halving the MC doubles ΔI — **this is the half-vs-full-MC test, derived.**
- Smoothing divides ΔI by M/p.

## 3. Why the A_i basis, and why the CS angles are not the point

The leptons come from a spin-1 current, so the squared amplitude is bilinear in the
polarization: the angular distribution at fixed boson 4-momentum is a *quadratic*
polynomial in the lepton direction, i.e. lives entirely in the ℓ ≤ 2 spherical
harmonics — 1+3+5 = **9** functions, with ℓ≥3 identically zero at any order in QCD.
So 9 is the dimension of the physically allowed function space, not a smoothing
hyperparameter, and the projection is lossless. A production-side variation (PDF,
α_s, m_q) cannot change the decay, so it moves only {σ_UL, A_0..A_7}: the ratio of
two 9-term expansions **is** ρ(x), not a model of it. Unlike a kernel or spline
there is no bias-variance tradeoff in the angular direction.

At fixed gen boson 4-momentum the lepton momenta are a deterministic function of
(cosθ*, φ*). Hence (boson kinematics ⊗ 9 harmonics) is a **sufficient statistic**
for any lepton-level template — which is why the same machinery worked in mW over
(p_T^μ, η^μ, q) with no angular binning in the fit. M is large there because one
gen cell's events spread over many muon-kinematics bins.

Measured bias/noise frontier (true variation has 3 harmonics; fit resolves 64
angular bins; `dogfood_meanweight.py`):

```
estimator      #params/cell   dI_noise    dI_bias  noise gain  pred M/p
raw                      64      3.191      0.040         1.0       1.0
meanwgt K= 1              1      0.045      1.385        70.5      64.0
meanwgt K= 4              4      0.194      0.205        16.4      16.0
meanwgt K=16             16      0.796      0.024         4.0       4.0
meanwgt K=64             64      3.191      0.040         1.0       1.0
moments p=1               1      0.045      1.385        70.5      64.0
moments p=3               3      0.144      0.002        22.1      21.3
moments p=9               9      0.440      0.006         7.3       7.1
```

Read off:
- "mean weight ratio per gen cell, no angles" **is** the i=−1 term alone
  (`meanwgt K=1` ≡ `moments p=1`, identical numbers). Best noise, worst bias.
  **The A_i terms are exactly the minimal correction that removes that bias.**
- A mean-weight histogram at the fit's own angular resolution (`K=64`) reproduces
  the raw template exactly — gain 1.0. Any gain requires being coarser, and for a
  histogram coarser means biased.
- The projection dominates the histogram on **both** axes at every K (e.g. p=3 vs
  K=16: 5.5× less noise *and* 12× less bias). The h_i are a sufficient statistic,
  so slicing in the angles can only lose.
- Bias-column floor is dI_noise/N_exp; 0.040 (raw) and 0.006 (p=9) are consistent
  with exactly zero.

## 4. It is NOT clipping — the tail is kept

Common misconception: that the smoothing "throws away the weight tail". It does
not. Clipping (`theory_weight_truncate` / `clamp_tensor_safe`) is the operation
that throws the tail away, and it is badly biased. Toy with a one-sided tail whose
contribution to the mean (+0.0040) is 2/3 of the physical shift (+0.0060),
300 pseudo-experiments (`dogfood_tail.py`):

```
estimator                bias        as % of phys shift   per-bin noise
raw                   -0.000014 ± 0.000012      -0.2%       0.000567
clipped               -0.003805 ± 0.000001     -63.4%       0.000028
smooth                -0.000014 ± 0.000012      -0.2%       0.000352
smooth, tail deleted  -0.004000                -66.7%       0.000006
```

Clipping destroys 63% of the physical variation. The smoothed template has the same
(zero) bias as the raw one, and the last row proves the tail events are genuinely
*used*: deleting them from the moment sums reproduces the clipping bias exactly.

## 5. What is actually assumed

```
E[raw_b]      = Σ_x n(x,b) · E[r | x, b]
E[smoothed_b] = Σ_x n(x,b) · E[r | x]
```

equal **iff `E[r|x,b] = E[r|x]`**, i.e. r ⫫ (reco bin) | x. Nothing about the
tail's size, shape or heaviness enters unbiasedness; heavy tails affect only the
variance, which the conditional mean reduces regardless. So validity splits into:

| claim | status |
|---|---|
| the 9 harmonics span the angular dependence | **exact** for pre-FSR, LO EW (ℓ≥3 vanish) |
| ρ constant inside a gen (Q,\|y\|,p_T^V,q) cell | **approximation** — not yet tested |
| r ⫫ reco bin \| x | **the real assumption** — not yet tested |

## 6. How to establish validity (ranked by power)

The AN's angle-integrated raw-vs-smoothed comparison is a *weak* test: it checks
the total well but per-bin can only confirm agreement to the raw template's own
noise — the very thing that is noisy. The structural tests do not have that limit.

1. **Basis adequacy, nominal only** — reconstruct the nominal angular density from
   the 9 moments per gen cell, compare to the directly histogrammed angular
   distribution at full stats. Catches FSR/EW/acceptance breaking ℓ≤2. No
   variations needed, so no noise limitation. *Not done.*
2. **Cell-size convergence** (decisive for row 2) — remake the by-helicity hists
   with 2× finer (Q, |y_V|, p_T^V) cells, rebuild the templates, compare. Cheapest
   real test. *Not done.*
3. **Independence in slices** (tests the actual assumption) — compare raw vs
   smoothed in slices of variables *not* in the conditioning set: m_T, recoil u_T,
   n-jets. A systematic drift in a slice is a direct detection of the failure.
   *Not done.*
4. **Closure fit** — Asimov from raw templates, fitted with smoothed ones.
   End-to-end but power limited by the raw noise.
5. **Half-vs-full MC** — measures leftover spurious constraint, not validity. Done
   in the AN: clean for Z; W improved but not clean, hence the 1.26 MC-stat
   inflation in the single-muon channel.

**Direction of risk:** if the smoothing is valid its only effect is to remove a
*fake* constraint, so the reported uncertainty gets **larger** — more conservative.
The residual danger is bias in the central value / nuisance shape, which is what
tests 2–4 target.

**Where to look first if something is wrong: the W.** Its selection involves an m_T
cut and the recoil, which depend on hadronic activity, which correlates with parton
x/flavour at fixed boson kinematics — precisely the row-3 failure mode. It is also
the channel that kept leftover spurious constraints.

## 7. Corrections to the AN wording

- `uncerts.tex:39` — "quantizes the CS angles into just nine helicity cross
  sections, largely reducing the dimensionality of the histogram" is not the
  mechanism. The dimensionality that matters is *template bins per conditioning
  cell (M) vs parameters per cell (p)*, and the reduction works identically with no
  angular binning in the fit (as in mW). The angles are conditioned on for
  **unbiasedness**, not for variance.
- `theory.tex:96` — the moment formula for A_1 reads `5⟨sin²θ* cosφ*⟩`; it should be
  `sin2θ*`. That is what the code uses, what 1606.00689 Eq. 5 has, and what the
  AN's own P_1 in Eq. `harmonic-polynomials` says. Cosmetic typo.

## Evidence

`../../studies/helicity-smoothing-mechanism/`:

| script | what it shows |
|---|---|
| `smoothing_toy.py` | ΔI_raw = N_bins·V; gain = M/p over a decade in M and p; independent of cell/bin overlap; bias appears only when conditional independence is violated |
| `dogfood_meanweight.py` | the bias/noise frontier table in §3 |
| `dogfood_mechanics.py` | h_0 = Σw; h_i/h_0 = A_i; Σ_i h_i A_i = W·density; the kernel identity to 9 digits; kernel range and reach; events-used comparison |
| `dogfood_tail.py` | the clipping-vs-smoothing table in §4 |
