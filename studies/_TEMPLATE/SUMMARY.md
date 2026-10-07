---
title: <study name>
slug: <study slug>            # for a task summary: <YYMMDD>-<task>, and add `study: <parent slug>`
status: active                # copy of the logbook's status at the time of writing
period: YYYY-MM-DD – YYYY-MM-DD   # first to last logbook entry covered ("– ongoing" if active)
updated: YYYY-MM-DD           # when this summary was written
covers: YYYY-MM-DD            # the newest logbook entry this summary accounts for
---

# <study name>

<!-- READ BEFORE WRITING (delete these comments in the real summary).
     Audience: a member of the analysis who knows the analysis, the framework and the AN,
     but was not in this study and has not read its logbook. They should come away knowing
     why it was done, what was done, what came out, what changed, and what's still open,
     without opening anything else.
     Length: one to two printed pages (~600-900 words plus 2-4 figures or tables). Go over
     only if the study really needs it.
     Every number must trace to a logbook entry; cite the task in brackets, e.g. [260826-b-scan].
     This page is published on the web without authentication: no unblinded numbers. -->

> **<The answer in one or two sentences: what we now know, or where it stands.>**

## Why

<2-4 sentences: what prompted the study, and the driving question(s) as they were posed at
the start. If the question changed along the way, say what it became and why.>

## What we did

<A short paragraph on the approach: the setup (card, PDF set, cache, data or Asimov) and the
method. Explain any study-internal name the first time it appears. Leave out the dead ends
unless they taught us something.>

| Task | Question | Answer |
|---|---|---|
| [YYMMDD-task](https://submit.mit.edu/~lavezzo/alphaS/studies/#<slug>/YYMMDD-task) | <one line> | <one line> |

<!-- Links: full viewer URLs, as above, so they also work in the PDF. Images: relative paths. -->

## Findings

<!-- Numbered and ordered by importance, not by date. Put the comparability caveat
     (blinding family, Asimov vs data, PDF/order swap, card, freeze list, warm vs cold)
     BEFORE the number. Embed a figure wherever it is the evidence, reusing the task's
     own plot by relative path: ![alt](YYMMDD-task/plot.png). -->

1. **<finding>.** <one-to-three-sentence physics read>. [YYMMDD-task]

   ![<what the figure shows>](YYMMDD-task/plot.png)

   *<caption: what to look at, and its caveat>*

## What changed

<!-- Whatever outlives the study, or "nothing; diagnostic only". -->

- **Code:** <PR / commit and what it does>
- **Analysis defaults / cards:** <e.g. "λ4_ν frozen to 0 in the nominal fit">
- **knowledge/:** <notes written or corrected>

## Conclusions and open items

<What this means for the α_s / m_W measurement. Then what's still open and whether anyone is
working on it. For an active study, the next step.>

---

<small>Full record: [logbook](https://submit.mit.edu/~lavezzo/alphaS/studies/#<slug>:logbook)
· plots in each task directory · bulk outputs: `<ceph path>`</small>
