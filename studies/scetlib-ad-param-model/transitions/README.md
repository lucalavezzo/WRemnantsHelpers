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
