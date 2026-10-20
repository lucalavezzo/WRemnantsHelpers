## Validation beyond CI (head 8b3f180)

Each row lists a claim, how it was tested, and the result. The real-data checks use a blinded fit, so only uncertainties and impacts are quoted, in rabbit's POI units.

| Claim | Test | Result |
|---|---|---|
| **Problem solved:** traditional impacts exist at an active face (linear face) | Post-fit of a real fit (3720 params, SCETlib NP param model + lattice term, one weakly binding linear NP face) rerun from its minimum with `--doImpacts --globalImpacts` | Grouped and ungrouped impacts are present and finite. The recomputed face-held `cov` equals the stored one exactly (0 difference), with the same EDM and multiplier. |
| **Problem solved:** curved face + bound face together | Post-fit of a second real fit with two active faces: the bound `lambda2_nu >= 0` (mu 32.4) and a cubic NP face (mu 4.10) | Grouped and ungrouped impacts are finite; the held parameter's `cov` row is exactly 0. |
| **Exactness on real data:** holding a bound face == freezing the parameter | The same post-fit at the same point with `--freezeParameters lambda2_nu`; the cubic face stays held in both | `cov` (excluding lambda2_nu), traditional impacts (3720 ungrouped + 63 grouped) and global impacts (ungrouped + grouped): **max difference 0, bit-identical**. |
| Curved-face algebra | `tests/test_face_held_impacts.py`: disk face vs the fit with the face *eliminated*; frozen-group refits; Newton-polished finite differences | Agreement to 1e-8 (impacts), 1e-6 (groups) and 1e-6 (FD, whose error is measured as -0.051 delta^2) |
| Consistency with an earlier build of this change (older branch) | Same real post-fit, two code versions | Agreement to 1e-13 everywhere except the global grouped `stat`. That column differs by exactly the `diag(C Hc C)` = 7.8e-5 correction that 8b3f180 removed; the global sources now add up to sigma^2 exactly (0.295342). |
| **No new problems:** fits without an active face are bit-identical to `main` | `rabbit_fit` with main 2d9f380 vs this branch on the test tensors, with `--doImpacts --globalImpacts --gaussianGlobalImpacts --saveHists --computeHistErrors --computeHistImpacts`. Configs: bbstat lite / full / off, sparse, inactive constraint (with and without bbstat) | Every output (all hists incl. variances, every dict leaf) is identical. `--chisqFit` is not run-to-run deterministic on `main` itself (two `main` runs differ in the output key set); its impact hists were identical in this run. |
| Sharding path | `--constraints` is refused with `--nDevices > 1`, so the face path cannot be reached sharded. The no-face path is the unchanged graph (`test_sharded_fit.py`, 43 passed) | Not affected |
| Plot tools on a face-held result | `rabbit_plot_pulls_and_impacts.py` (traditional + global, grouped + ungrouped) on both real post-fits | rc 0, plots produced |
| CI + review | Full suite (476 passed locally), CI green on 8b3f180; review bot re-run on the head | "No issues found" |

**Caveats / open (unchanged, not in this PR).**
- The global grouped `stat` remainder can still be negative (NaN after the sqrt) when the non-prior part of the Hessian is indefinite. On the linear-face fit it is -0.022 even though `C H C = C` holds to 1e-12, so faces do not cause it. `--gaussianGlobalImpacts` gives a data stat that is never negative.
- `--gaussianGlobalImpacts` at a face was validated on the test tensors only (exact against frozen and eliminated fits), not on the 3720-parameter real fits.
- Pre-existing on `main` and not touched here: a sparse tensor with JVP global impacts crashes (`SparseMatrixMatMul` InternalError).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
