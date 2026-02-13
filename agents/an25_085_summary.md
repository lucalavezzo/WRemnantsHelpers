# AN-25-085 Summary (Working Digest)

This is a practical high-level digest of the CMS analysis note at:
- `/home/submit/lavezzo/alphaS/AN-25-085`

Main source file:
- `/home/submit/lavezzo/alphaS/AN-25-085/AN-25-085.tex`

Status note:
- The analysis is blinded; multiple numerical results in the note are placeholders (`XXXX`, `YYYY`) or Asimov-only.
- `simFit.tex` is explicitly marked early-stage/in progress.

## 1) Analysis Goal
- Primary goal: measure `alphaS(mZ)` from Drell-Yan dimuon events using the low-`pT` Z spectrum at 13 TeV (2016 post-VFP).
- Main extraction: detector-level 4D fit in `(ptll, yll, cosTheta*, phi*)`.
- Additional extraction: unfold to pre-FSR generator level and fit unfolded Z/W cross sections.
- Combined fits can also include W single-muon channel and simultaneously fit `mW` (internal-use context, not intended as competitive `mW` measurement).

## 2) Data and Channels
- Data: 2016 post-VFP UL NanoAOD, `SingleMuon`, triggers `HLT_IsoMu24` or `HLT_IsoTkMu24`.
- Luminosity quoted in note macro: `16.8 fb^-1`.
- Z (dimuon) channel:
  - Exactly two opposite-sign good muons.
  - `60 < mll < 120 GeV`.
  - Detector-level fit variables: `ptll`, `yll`, `cosTheta*`, `phi*`.
- W (single-muon) channel:
  - Exactly one good muon plus one veto muon.
  - `mT > 40 GeV`.
  - Detector-level fit variables: `pt`, `eta`, `charge`.

## 3) Core Theoretical Setup
- Baseline MC: Powheg-MiNNLO + Pythia (+ Photos++).
- Central high-order correction model: SCETlib + DYTurbo at `N^3LL + NNLO`.
- Event reweighting/corrections are applied in `(ptVGen, absYVGen, qVGen)`.
- Baseline central PDF: `CT18Z`.
- Alternative theory comparisons discussed: higher resummation/FO orders (including NNLOjet-based alternatives where available).

## 4) Key Physics/Method Ingredients
- Angular decomposition is central:
  - Cross section split into unpolarized term (`sigmaUL`) plus 8 angular coefficients (`A0..A7`) in Collins-Soper variables.
- Detector-level extraction:
  - Profile likelihood fit with `rabbit`.
  - Z-only fit and combined W+Z fit variants.
- Unfolding:
  - Simultaneous unfolding of Z and W channels.
  - Z uses helicity-template method to unfold to full lepton phase space.
  - W unfolded to pre-FSR fiducial phase space (direct detector-to-generator response).
- Generator-level extraction:
  - Fit unfolded Z-only or W+Z cross sections to theory predictions.

## 5) Binning Snapshot (Most Important Operational Numbers)
- Z detector level:
  - `ptll`: 40 bins up to 100 GeV.
  - `yll`: 20 bins from -2.5 to 2.5.
  - `cosTheta* x phi*`: `8 x 8` quantiles per `(ptll, yll)` bin.
  - Total bins: `40 x 20 x 8 x 8 = 51,200`.
- W detector level:
  - `pt`: 30 bins (26-56 GeV, 1 GeV width).
  - `eta`: 48 bins (-2.4 to 2.4, 0.1 width).
  - `charge`: 2 bins.
  - Total bins: `2,880`.
- Z generator-level unfolding (helicity):
  - `ptVGen x absYVGen x 9 helicities` = `20 x 10 x 9 = 1,800`.
- W generator-level unfolding:
  - `ptGen x absEtaGen x qGen` = `34 x 22 x 2 = 1,224`.

## 6) Uncertainty Model (What Matters for Automation)
- Categories: statistical, experimental, theory.
- Statistical handling:
  - BB-lite/full methods compared.
  - Spurious-constraint issue from large MC weight variance identified.
  - Smoothing strategy for theory variations (`PDF`, `alphaS`, heavy-quark mass) via helicity decomposition is a key mitigation.
- Experimental uncertainties:
  - Inherited from W-mass framework (muon efficiencies/scales, prefire, lumi, etc.).
- Theory uncertainties include:
  - PDF uncertainties (multiple sets; inflation/coverage studies documented),
  - Resummation via theory nuisance parameters (TNPs),
  - Matching/scale uncertainties,
  - Nonperturbative model uncertainties (`npgamma`, `npf`),
  - Heavy-quark mass effects (partly still under development).
- Important correlation choices:
  - Several theory + experimental nuisances correlated between W and Z.
  - Some NP and channel-specific effects intentionally uncorrelated.

## 7) Practical Interpretation for Codex Work
- Good automation targets:
  - Reproducible detector-level fit workflows (Z-only and W+Z),
  - Unfolding + downstream generator-level extraction chains,
  - Validation plots for pulls/impacts and response diagnostics,
  - Systematic variation bookkeeping (especially smoothing and correlation configs).
- High-risk areas where checks are essential:
  - Correct correlation scheme across channels,
  - Consistency of pre-FSR definitions and phase-space selections,
  - Correct propagation of unfolded covariance into generator-level fits,
  - Avoiding spurious constraints from noisy shape variations.

## 8) Section Map (Where to Read in AN)
- Introduction and analysis strategy:
  - `/home/submit/lavezzo/alphaS/AN-25-085/introduction.tex`
- Input samples/selections/backgrounds:
  - `/home/submit/lavezzo/alphaS/AN-25-085/input.tex`
- Theory model and NP setup:
  - `/home/submit/lavezzo/alphaS/AN-25-085/theory.tex`
- Uncertainties and correlation scheme:
  - `/home/submit/lavezzo/alphaS/AN-25-085/uncerts.tex`
- Detector-level extraction:
  - `/home/submit/lavezzo/alphaS/AN-25-085/detector_extraction.tex`
- Unfolding:
  - `/home/submit/lavezzo/alphaS/AN-25-085/unfolding.tex`
- Generator-level extraction:
  - `/home/submit/lavezzo/alphaS/AN-25-085/gen_extraction.tex`
- Simultaneous PDF+alphaS fit (in progress):
  - `/home/submit/lavezzo/alphaS/AN-25-085/simFit.tex`

## 9) Open Items / Caveats to Revisit With You
- Final unblinded `alphaS(mZ)` values are not yet in this digest.
- `mW` numbers in the AN text appear placeholder-like in some sections.
- Some theory updates are tagged TODO in-source (for example NNLOjet/PDF handling and heavy-quark effects).
- If you want, we can annotate this file with "analysis-frozen" vs "work-in-progress" choices used in your current production workflow.
