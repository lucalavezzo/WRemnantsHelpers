---
title: Varied-anchor cache — separating displacement error from cache-construction error
slug: scetlib-ad-varied-anchor
status: done
created: 2026-08-26
updated: 2026-08-26
---

# Varied-anchor cache — logbook

**Goal:** run the one experiment four previous rounds could not: build a second
SCETlib AD cache whose **anchor is at a varied transition point**, and use it to
split the published transition-point error into (a) pure displacement/replay
error and (b) cache-construction error. Done when the three-way comparison is
reported as differences, with the in-situ two-build floor measured alongside.

---

## START HERE (status as of 2026-08-26) — DONE, and the answer is decisive

> **The cache-construction term is EXACTLY ZERO. The confound this round was
> built to remove does not exist, the published numbers were never confounded,
> and the whole error is pure displacement.** A cache anchored at a varied
> transition point reproduces the live runcard at its own anchor to
> **4e-15 .. 2e-14**, so `cache_varied @ its own anchor` and
> `direct @ the varied point` are the same number. The displacement error
> therefore survives at **full size** — `(C-B)/dS` equals `(C-A)/dS` to four
> decimal places in every bin of both legs.
>
> **Per the decision rule this round was given: the assembly is EXONERATED and
> the cause is in the displacement handling.**
>
> **Read the floor before quoting any bin but [20,24].** Two independent builds
> of the *same* runcard agree bit-level at the anchor and disagree by up to
> **1.9e-03 in sigma** at the displaced point — 2 to 41 percentage points of the
> response. Only qT [20,24] clears it (14.7x on the x2 leg, 30.4x on x1,x3).
> At [24,28] and above the published per-bin *levels* (+10.8%, +11.6%, +2.3%,
> +1.2%) are **within a rebuild of the same cache** and should not be read as
> measurements. This does not touch T-036's A/B *differences* from ONE cache,
> which reproduce to 0.1 pp; it sharpens T-037's "quote differences, not levels".

- **Next action:** nothing here. The next move belongs to D-051 / D-T8 (make
  `r'(0) = 0` true by construction: mode 3, or store `d(conv)/dlnmuF` as two
  extra conv kinds at cache-build time). This round removes the last competing
  explanation for the low-qT residual.
- **Blocking on:** nothing.

---

## The design

Per bin, all sigma in pb, `|Y| [0, 0.15]`, qT bins `[20,24] [24,28] [28,33]
[33,44] [44,100]`. `[18,20]` is deliberately excluded — its true response is
below the reference's own node-ladder target (T-038 closed it as a diagnostic
bin, with a factor 13 between two builds of the same card).

| symbol | what |
|---|---|
| `A0` | direct runcard refill at the NOMINAL point (live, no cache) |
| `A`  | direct runcard refill at the VARIED point (live, no cache) |
| `C0` | cache built at NOMINAL, evaluated at its OWN anchor |
| `C`  | cache built at NOMINAL, evaluated at the VARIED point — **displaced** |
| `B`  | cache built at VARIED, evaluated at its OWN anchor — **the new reference** |
| `D`  | cache built at VARIED, evaluated at the NOMINAL point — displaced, reverse |
| `Cb` | a SECOND independent build of the NOMINAL runcard — the in-situ floor |

with `dS = A - A0` the true finite shift, and the exact decomposition

```
(C - A)/dS   =   (C - B)/dS   +   (B - A)/dS
what every       PURE            CACHE
previous round   DISPLACEMENT    CONSTRUCTION
measured         error           error
```

Four processes, one cache each: `nomA` (nominal anchor + live reference),
`nomB` (same runcard, second build, seed 9999 — the floor), `varA`
(x2 = 0.35 anchor + live reference), `x13A` (x1,x3 = 0.3,0.9 anchor + live
reference). ~11 min wall each, all four in parallel.

### Two implementation choices, and why

1. **The cache is the in-process one** (`build_bin_rules` +
   `build_pdf_variations(n_eig=0, as_cen=0, as_step=0, muf_lo=1/2, muf_hi=2)`),
   not a `prepare_cache_for_card.py` npz. Same machinery, same rule format, and
   it is the machinery every previous transition number came from, so the new
   numbers are directly comparable to T-036 / T-037 / D-T7. It also keeps the
   live runcard reference in the same process. **Control that it worked:** the
   true responses come out `-3.075e-03 / -7.840e-03 / -1.822e-02 / -3.301e-02`,
   the published T-038 values to every digit.
2. **`--no-pdf` was NOT used, and must not be for this question.** In
   `prepare_cache_for_card.py`, `--no-pdf` sets `plan = None` (line 436) and so
   skips `build_pdf_variations` **entirely** — no PDF eigenvectors, no alphaS
   pair, **and no muF pair**. The muF member pair is the whole route the
   transition points travel on (moving x1/x2/x3 shifts muF per node, and muF is
   member-served), so a literal `--no-pdf` cache would have had no transition
   response to measure. The intended saving — dropping the PDF eigenvector
   member loop, D-C1's 68% — is `--pdf-eig 0 --as-pair off`, i.e. exactly
   `n_eig = 0, as_cen = 0, as_step = 0` here.

### Arms proven separated

Three arms, three different sums over the five bins (pb):

```
A0  direct @ nominal         14.4414154890     C0  cache_nom @ own anchor  14.4414143278
--- x2 = 0.35
A   direct @ varied          14.1721170244     B   cache_var @ own anchor  14.1721132981
C   cache_nom @ varied       14.1650098725     Cb  cache_nomB @ varied     14.1675014503
--- x1,x3 = 0.3,0.9
A   direct @ varied          14.5052576982     B   cache_var @ own anchor  14.5052576982
C   cache_nom @ varied       14.5125757020     Cb  cache_nomB @ varied     14.5079251040
```

plus the script's own guard: it refuses to report if two eval points of one
cache agree to better than 1e-13. Measured separations 3.38e-02 / 1.25e-02
(nomA), 3.31e-02 / 1.20e-02 (nomB), 3.47e-02 (varA), 1.28e-02 (x13A).

---

## Results

Full tables: `RESULTS.txt`. Raw: `nomA.json`, `nomB.json`, `varA.json`,
`x13A.json`; logs alongside.

### 1. Validation — a cache anchored at a varied transition point IS exact there

`cache @ its own anchor / live runcard at the same point − 1`:

| qT | nominal anchor | x2 = 0.35 anchor | x1,x3 = 0.3,0.9 anchor |
|---|---|---|---|
| [20,24] | −4.4e−15 | −7.7e−15 | −6.8e−15 |
| [24,28] | −9.5e−15 | −4.0e−15 | +2.9e−15 |
| [28,33] | −6.8e−15 | +1.9e−07 | −1.8e−14 |
| [33,44] | +2.2e−16 | −6.1e−15 | −1.3e−15 |
| [44,100] | −2.6e−07 | −9.6e−07 | −4.0e−15 |

The 1e−07 entries are the **direct integrator's own** reproducibility, not the
cache's: two independent direct runs of the nominal card differ by `+2.6e−07` in
[44,100] and by `0.000e+00` in the other four bins.

Splitting the same thing two ways (`RESULTS.txt` block 1b): `rule/live − 1`
*inside one object* at the anchor is `≤ 1e−14` in every bin of every arm, and
`live/direct − 1` *across two configures* is `≤ 2.2e−16` except the same
[44,100] 1e−07. **So at fixed tolerance, "the cache" and "live" are the same
number to machine precision.** The 1.1e−03 "instance systematic" that motivated
this round (DECISIONS.md:3448) is a *tolerance* effect — it was measured
between model instances at `rel 1e-3` vs `1e-4` — not a cache-vs-live effect.

### 2. The measurement — the error survives at full size

Errors as a fraction of the true shift `dS`, `|Y| [0, 0.15]`, FINITE variation:

**x2: 0.6 → 0.35**

| qT | true resp | OLD `(C−A)/dS` | PURE DISPL `(C−B)/dS` | CACHE CONSTR `(B−A)/dS` |
|---|---|---|---|---|
| [20,24] | −3.075e−03 | **−31.8%** | **−31.8%** | **+0.0000** |
| [24,28] | −7.840e−03 | +10.8% | +10.8% | +0.0000 |
| [28,33] | −1.822e−02 | +11.6% | +11.6% | −0.0000 |
| [33,44] | −3.301e−02 | +2.3% | +2.3% | +0.0000 |
| [44,100] | −2.377e−02 | +1.2% | +1.2% | +0.0000 |

**x1,x3: 0.2,1.0 → 0.3,0.9**

| qT | true resp | OLD | PURE DISPL | CACHE CONSTR |
|---|---|---|---|---|
| [20,24] | +1.784e−03 | −32.4% | −32.4% | −0.0000 |
| [24,28] | +5.752e−03 | −18.5% | −18.5% | +0.0000 |
| [28,33] | +7.537e−03 | +43.1% | +43.1% | −0.0000 |
| [33,44] | +1.157e−02 | +7.9% | +7.9% | −0.0000 |
| [44,100] | −1.033e−03 | −35.4% | −35.4% | +0.0000 |

The old and the pure-displacement columns are identical to four decimal places
because the cache-construction column is zero. `−31.9%` (T-037's `attr_x2_035`)
→ `−31.8%` here is the T-037 run-to-run scatter, 0.1 pp on that bin.

### 3. The floor, measured in situ — and it is the caveat that matters

Two independent builds of the **same** (nominal) runcard, `Cb/C − 1`:

| qT | at the anchor | at x2 = 0.35 | at x1,x3 | floor in response units (x2 / x1,x3) |
|---|---|---|---|---|
| [20,24] | +2.2e−16 | −6.7e−05 | −1.9e−05 | +2.2 pp / −1.1 pp |
| [24,28] | +1.6e−15 | −6.1e−04 | +1.7e−03 | +7.8 pp / +30.2 pp |
| [28,33] | −4.4e−16 | +1.9e−03 | −2.4e−03 | −10.3 pp / −32.4 pp |
| [33,44] | +6.7e−16 | +6.6e−04 | −4.4e−04 | −1.9 pp / −3.9 pp |
| [44,100] | −1.4e−06 | −4.3e−04 | −4.2e−04 | +1.8 pp / +40.8 pp |

`|signal| / |floor|`: x2 leg **14.7**, 1.4, 1.1, 1.2, 0.7; x1,x3 leg **30.4**,
0.6, 1.3, 2.0, 0.9. Summed over the five bins the ratio is 2.85 on the x2 leg.

Two things follow:

- **The floor is a purely DISPLACED-point phenomenon.** At the anchor the two
  builds agree bit-level; at a displaced transition point they part by up to
  1.9e−03. It is the rule compression that differs (different `n_train` seed,
  independent adaptive node sets), and that difference is invisible at the
  anchor by construction and visible only under displacement.
- **My in-situ floor is 60x the published two-build sigma floor** (3.1e−05) and
  lands at the published *Jacobian* floor (3.0e−03). A transition displacement
  of Δx2 = −0.25 is a large excursion; the published sigma floor was not
  measured at one and must not be used as the yardstick here. **This is why the
  round was told to measure it in situ, and it was the right instruction.**

### 4. The reverse leg, and the size of the cancellation behind it

`D` — the x2 = 0.35 cache displaced *back* to 0.6 — recovers **72.3%** of the
true shift at [20,24], against **68.2%** for the forward leg from the nominal
anchor and **67.6%** for the forward x1,x3 leg. Three different anchors, three
different stencil geometries, the same ~32% deficit: the effect is not an
accident of the nominal anchor. (In these units a linear-in-D error has the same
sign both ways, so this is *consistent with* D-049's `(A1−1)e1 D` and does not
discriminate against a multiplicative one.)

**Why a few-percent error lands at 32%, at the sigma level.** `live` at a
displaced point is *not* a live calculation here: `set_gradient_node_cache(True)`
caches the per-node profile scales and PDF/beam-grid convolutions, so it
re-sweeps the kernels over the NodeData frozen at the anchor — i.e. it is the
path *without* the muF member interpolation. The response it delivers, as a
fraction of `dS`:

| qT | frozen-node only | + members (the rule) |
|---|---|---|
| [20,24] | **−7.88** | +0.68 |
| [24,28] | −8.65 | +1.11 |
| [28,33] | −6.33 | +1.12 |
| [33,44] | −4.82 | +1.02 |
| [44,100] | −4.51 | +1.01 |
| x1,x3 [20,24] | −9.44 | +0.68 |

The two halves are `−7.9 dS` and `+8.6 dS` and the answer is `+0.68 dS`: a
**~9x cancellation, measured at the sigma level per bin**, which is T-033's
number arrived at from a different direction. A 4% error on either half is 32%
of the answer. That is the whole low-qT story in one line, and it is why
D-050/D-T7's "≤ 1.8% per node" and "−32% in sigma" were never in contradiction.

---

## Log

### 2026-08-26
- Read AGENTS.md, D-049..D-052, the T-0xx block, `00_README.txt` "THE ANSWER".
- Wrote `varied_anchor.py` (one cache at one anchor, evaluated at a list of
  points, recording `rule` = cache replay and `live` = same-object evaluation),
  `summarize_va.py`, `extra_va.py`. Driver `run_va.sh`.
- Found and avoided the `--no-pdf` trap (drops the muF member pair).
- Ran the four arms; results above. Total ~15 min wall, 4 x 8 threads.

---

## Findings

1. **A cache anchored at a varied transition point is exact at its own anchor**
   — 4e−15 to 2e−14 against the live runcard, on all three anchors tried
   (x2 = 0.6, x2 = 0.35, x1,x3 = 0.3,0.9). — (evidence: `RESULTS.txt` block 1)
2. **The cache-construction term is zero**, so every previous round's
   transition number was measuring pure displacement error all along. The
   feared confound does not exist. — (evidence: `RESULTS.txt` block 3)
3. **The assembly is exonerated; the cause is in the displacement handling.**
   The error survives at full size against a same-machinery reference.
   — (evidence: `RESULTS.txt` block 3, both legs)
4. **The cache-vs-live "1.1e−03" was a tolerance effect, not a cache effect.**
   At fixed tolerance `rule/live − 1 ≤ 1e−14` inside one object at the anchor.
   — (evidence: `RESULTS.txt` block 1b)
5. **Two independent builds of the same runcard agree bit-level at the anchor
   and by only 1.9e−03 at a displaced transition point** (2–41 pp of the
   response). Only qT [20,24] clears this floor; [24,28] and above do not.
   — (evidence: `RESULTS.txt` block 2)
6. **The ~9x muF cancellation, measured at the sigma level per bin**: the
   frozen-node half delivers −4.5 to −13 times the true response and the member
   half cancels it to +0.68..+1.12. — (evidence: `RESULTS.txt`, last block)
7. `prepare_cache_for_card.py --no-pdf` drops the **muF** member pair as well as
   the PDF ones, so it cannot be used for any transition-point measurement.
   — (evidence: `prepare_cache_for_card.py:436`)

---

## Open questions

- Nothing this round opened. The remaining question is D-051 / D-T8's, unchanged:
  make `r'(0) = 0` true by construction (mode 3, or store `d(conv)/dlnmuF` as
  two extra conv kinds at build time).
- Worth knowing but out of scope here: how much of the displaced-point two-build
  floor is the `n_train` seed and how much is the independent adaptive node set.
  One extra arm (same seed, second process) would separate them.

---

## Decisions

- 2026-08-26 — use the in-process rule build, not an npz cache — same machinery,
  comparable to every previous transition number, and it keeps the live
  reference in-process. Validated by reproducing the published true responses
  to every digit.
- 2026-08-26 — do NOT use the builder's `--no-pdf` for any transition question —
  it drops the muF member pair, which is the entire mechanism under test.
- 2026-08-26 — quote no transition-point per-bin *level* above qT [20,24]
  without the in-situ two-build floor beside it.
