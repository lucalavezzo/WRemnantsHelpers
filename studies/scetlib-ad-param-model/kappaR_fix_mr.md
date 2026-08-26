qT/ad: the live kappa_R must scale the minimum-scale compensation

Scale_provider compensates the muB/muS/nuS floors by w_fo = mu_FO/Q when
compensate_fo is set,

    muB = fo.mu * pB * f_run(qT/Q, mu_star(muT, muB_min/(pB * _2_wFO))/Q)
    _2_wFO = fo.mu/Q

so that a fixed-order scale variation leaves the large-bT floor exactly where it
was: at large bT the two factors of fo.mu cancel and muB -> muB_min.

The live-profile branch scales fo_mu by the live kappa_R but passed
ad_g.prof_w_fo, which prepare_point fixes once at configure time as _muFO_mu/Q.
The floor therefore landed at muB_min * kappa_R instead of muB_min: at
kappa_R = 0.5 the deep-IR floor halves, the large-bT tail moves, and the low-qT
bins move with it.

Measured on the CMS analysis runcard (mu0_min = muB_min = muS_min = 1.,
muf_min = 1.40, compensate_fo = yes; Q in [60,120], |Y| in [0,0.15]), as the
ratio to the central prediction for the same physical change made two ways --
kappaFO = 0.5 with kappaf = 2. in the RUNCARD with set_diff_scales off, against
scale_kappa_R = 0.5 as a live parameter with it on:

                  runcard      live (before)   live (after)
    qT [ 0, 1]    0.940886      0.910108        0.940888
    qT [ 1, 2]    0.945501      0.925919        0.945507
    qT [ 2, 3]    0.951370      0.945731        0.951370
    qT [ 4, 5]    0.967427      0.975811        0.967435
    qT [ 8, 9]    0.995254      0.994576        0.995254
    qT [33,44]    1.015613      1.015610        1.015613

    max |live/runcard - 1|:      3.3e-02        9.1e-06

The error is low-qT only -- 3e-06 by qT = 33 -- and changes sign between 2 and 5
GeV, which is why it survived every check made at high qT. It is also ten times
larger in the down direction than the up one, since that is the direction that
lowers the floor.

Confirmed independently before touching any code, by supplying the missing
factor by hand: doubling muB_min and muS_min in the varied runcard (so that the
uncompensated formula lands on the same floor the compensated one would) brings
the live route to 5.4e-06 of the runcard route in every bin, with nothing else
changed.

Why the existing validation did not catch it. 1bab661 established that the value
path is exact -- "the live kappa_R = 1.5 evaluation of the resummed piece
reproduces a genuinely reconfigured calculation (kappaFO = 1.5, kappaf = 1/1.5)
bit for bit" -- and that still holds: it was run on examples/matched_ad/
matched.conf, which sets no mu0_min/muB_min/muS_min/muf_min (SCETlib defaults
them to 0) and no compensate_fo (Scale_provider defaults it to false). With
floors of zero the compensation term is 0/anything, and with compensation off
w_fo is 1: the bug is invisible twice over. It needs a runcard that sets both.
Same class as b919b61, whose comment records "exactly 0 with the floors
removed".

compensate_fo is carried into ad::GlobalData rather than inferred from
prof_w_fo, because prof_w_fo is exactly 1.0 for the usual central runcard
(muFO_fixed unset, kappaFO = 1) whether compensation is on or off, and the live
kappa_R must scale it only in the first case. The arithmetic is written
straight-line at both sites rather than factored into a helper: b7f5eb9 found a
call boundary implicated in a lost adjoint in this exact function, and this
expression is on the tape.

This changes sizeof(ad::GlobalData) and the kappa_R response the bin rules are
trained on, so existing caches must be rebuilt.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01CnJ9YKK8c1q1sCDouM6y1c


---
MR: https://gitlab.cern.ch/scetlib/contrib/scetlib-cms/-/merge_requests/3
(opened 2026-08-21 from branch fix-kappaR-floor-compensation; GitLab took the
description from the commit message above. Offered upstream: a regression test
shaped as runcard-vs-parameter on a card that DOES set the floors, which is
exactly the check that was missing.)
