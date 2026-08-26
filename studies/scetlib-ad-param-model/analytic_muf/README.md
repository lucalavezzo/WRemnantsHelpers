# Analytic d(conv)/d(ln muF) for the transition points

The route the two knot rounds pointed at: give the beam convolutions their
DGLAP muF derivative analytically instead of interpolating three frozen muF
samples. Results and the full write-up:
`~/public_html/alphaS/260826_analytic_muf_dglap/00_README.txt`.

SCETlib side: worktree `/work/submit/lavezzo/alphaS/scetlib-anlmuf`, build dir
`build-anlmuf`, branch `muf-analytic-dglap` off `eb60a04` (the same base the
five-knot round used). `DrellYan.set_muf_analytic(mode)`; 0 = off, 1 = the terms
the production `fo_lvl = 2` conv prefix already holds (no new grids, no cache
change, runs on existing caches), 3 = the full alphaS^3 set (four extra conv
kinds, 16 more beamfunc grid families, needs the nodes rebuilt).

## The gate, which needed no prototype at all

`DrellYan.conv_probe(x, muf, pid, side)` returns the node's beam convolutions at
ANY muF, so the exact muF dependence is sampleable directly.

| script | what it answers |
|---|---|
| `dconv_dlnmuf.py` | is a first-order model enough at D ~ 1.15 ln f? (the question D-022 asked) |
| `dconv_gate2.py` | does the analytic derivative need the P2 (NNLO splitting) term? |
| `dconv_gate3.py` | the four candidate constructions at the REAL member geometry |
| `dconv_gate4.py` | endpoint CLOSED FORMS for the evolution integrals -- measured bad |
| `dconv_gate5.py` | the quadratic-alphaS model that replaced them; whose alphaS |
| `dconv_gate6.py` | what each tier of extra conv kinds costs and buys |
| `gate6b.py`, `gate7.py` | the same across flavour, beam and rapidity, with a response-size guard |

## The prototype, and its two A/Bs

| script | what it measures |
|---|---|
| `anlmuf_closure.py` | 39-direction closure against the CorrZ templates, mode ON vs OFF, BOTH ARMS FROM ONE CACHE |
| `anlmuf_interp_error.py` | the model against an EXACT runcard refill, modes 0/1/3 in one process |
| `anlmuf_plots.py` | the figures, from the gate JSON |
| `run_closure.sh`, `run_interp_queue.sh` | the drivers |
| `configure_anlmuf.sh`, `incontainer_anlmuf.sh` | cmake + container entry for the worktree |

Both A/B scripts REFUSE to report a null unless the arms are proven to separate:
`ScetlibCachedXsecTF.values_and_jacobian` memoises on the parameter vector
alone, and this study has already been burnt by a perfect and completely wrong
null.
