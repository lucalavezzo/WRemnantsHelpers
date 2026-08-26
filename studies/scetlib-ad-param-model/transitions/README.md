# The transition points, taken end to end

Follows `../analytic_muf/`. Results and the full write-up:
`~/public_html/alphaS/260826_transition_analytic_e2e/00_README.txt`.
Decisions: `../DECISIONS_transitions.md` (D-031 .. D-044).

SCETlib side: worktree `/work/submit/lavezzo/alphaS/scetlib-anltrans`, branch
`muf-analytic-trans` off `eb60a04`. Builds, in the order they were needed:

| build dir | what it adds |
|---|---|
| `build-anltrans`  | `set_muf_ablate` bits 1 / 2 / 16, `rule_cvals` c_grad |
| `build-anltrans2` | + the c_i1 evolution (then behind ablation bit 8) |
| `build-anltrans3` | + the clamped extrapolation (bit 32) |
| `build-anltrans4` | c_i1 promoted to `set_muf_analytic_i1`, default ON |
| `build-anltrans5` | + the quartic Hermite residual (bit 64) |

`scetlib-cms`, `build-fix`, `build-knots`, `build-trans`, `build-nak`,
`build-5knot` and `build-anlmuf` were NOT touched.

## Scripts

| script | what it answers |
|---|---|
| `trans_attribute.py` | the ablation attribution against an EXACT runcard refill; all arms in one process off one rule build and one reference. `--with-i1 / --with-mode3 / --with-clamp / --with-herm` select the arms a given build supports. |
| `trans_closure.py` | the 39-direction CorrZ closure A/B from ONE cache; `anlmuf_closure.py` with an ablation mask on the second arm |
| `stencil_conditioning.py` | the per-node muF member geometry and the Lagrange weights it implies; pure arithmetic, no SCETlib |
| `gate2_lowmuf.py` | `dconv_gate2.py` with the muF list extended down to `muf_min` = 1.40 GeV |
| `trans_plots.py`, `lowmuf_plot.py`, `summarize.py` | the figures and the absolute-sigma tables |

Drivers: `run_attr.sh` (the four variation points, matched), `run_attr_sing.sh`
(`calculation_piece = sing`, the frozen-nonsingular test), `run_attr_prec.sh`
(`target_precision_rel` 1e-5), `run_attr_i1.sh`, `run_attr_clamp.sh`,
`run_attr_m3.sh`, `run_attr_herm.sh`, `run_closure_trans.sh`.

## Two things to know before using these

1. Every A/B script REFUSES to report a null unless the arms are proven to
   differ on the varied point AND to agree exactly on the central one. A clean
   null between two arms is this study's known signature of a shared cached
   result.
2. **Quote A/B differences, not absolute levels.** Two independent runs of the
   same mode-0 measurement differ by 0.3-3.7 percentage points bin by bin, while
   the shipped -> mode 1 difference reproduces to 0.1 pp.

## The safe-interpolant round (2026-08-26, follows the above)

One bounded round on the question the round above left open, and the answer is a
STOP: **no residual interpolant form works at `ad_muf_anl = 1`, and the reason is
not conditioning.** Write-up:
`~/public_html/alphaS/260826_transition_safe_interp/00_README.txt`. Decisions and
narrative: `../DECISIONS_transfix.md`, `../LOGBOOK_ENTRY_transfix.md` (staged).

SCETlib side: worktree `/work/submit/lavezzo/alphaS/scetlib-safeint`, branch
`muf-safe-interp` off `a7392be` (MR !9), build `build-safeint`. It adds a
**residual-form field** in `ad_muf_abl` bits 7..9, `form = (abl >> 7) & 7`:
1 cubic, 2 quartic (= the existing bit 64), 3/4/5 conditioning-guarded blends of
quadratic and quartic, 6 the clipped quartic factor, 7 a guarded blend of
quadratic and cubic. No new `ad::GlobalData` field, so `sizeof` is unmoved and
existing caches load.

| script | what it answers |
|---|---|
| `form_conditioning.py` | the amplification factors `A1`, `A2`, `A1c` per node from SCETlib's scale formulas alone -- pure arithmetic, no SCETlib, no cache |
| `residual_forms.py` | the residual `r(D)` MEASURED with `conv_probe`, every candidate form scored on it exactly; `--mode3` switches delta to the full `alphas^3` evolution |
| `residual_kinds.py` | the same per conv KIND, so "is only `c_delta` interpolated well?" is answerable |
| `mechanism_check.py` | `(A1-1) e1 D + (A2-1) e2 D^2/2` predicted against measured, per node |
| `safe_summarize.py` | the absolute-sigma per-direction summary of the arms |
| `safeint_plots.py` | the four figures |

Drivers: `run_attr_safe.sh` (`trans_attribute.py --with-safe`, x1,x3 FIRST),
`run_closure_safe.sh` (staged, never needed -- no candidate reached the closure
gate), `configure_safeint.sh` / `build.sh` / `incontainer_safeint.sh`.

**The one-line result.** `r'(0)` is not zero: it is the analytic model's own
linear truncation error, measured at **13.8% of the node response at the
muf_min = 1.40 GeV floor** (2.05% at mode 3), which is exactly where the qT 18-24
bins get their transition response. Every candidate form exists only to impose
`r'(0) = 0`, and each one's price is `(A1 - 1) e1` with `A1` up to 8.02 from
stencil geometry alone. The quadratic is the unique three-point form with
`A1 = A2 = 1`.
