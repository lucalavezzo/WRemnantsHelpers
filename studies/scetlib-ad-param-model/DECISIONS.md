# scetlib_ad — decision record

One line per decision, newest block first. Every entry says WHAT was decided,
WHY, WHAT EVIDENCE backed it, and WHAT WOULD OVERTURN it. This exists so a
review can check the reasoning, not just the outcome. Narrative lives in
`LOGBOOK.md`; this file is only decisions.

Status key: **SETTLED** (evidence in hand) / **PROVISIONAL** (acting on it, could
flip) / **OPEN** (needs Luca) / **SUPERSEDED** (kept for the audit trail).

---

## 2026-08-25 overnight session (autonomous, ~21:30 -> 08:00)

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
