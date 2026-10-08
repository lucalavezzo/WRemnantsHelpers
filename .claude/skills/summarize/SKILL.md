---
name: summarize
description: Write or refresh the standalone LaTeX summary (SUMMARY.tex + PDF) of a study or a large task by dispatching the study-summarizer agent. Use when Luca types /summarize <slug>[/<task>], or asks to summarize / write up / digest a study.
---

# /summarize <slug>[/<YYMMDD>-<task>] [occasion]

A thin entry point. The `study-summarizer` agent does the work and holds the writing rules
(`.claude/agents/study-summarizer.md`). When and why summaries get written is in the
`study` skill, §4. This file only covers dispatching the agent.

## 1. Resolve the target

`studies/<slug>` or `studies/<slug>/<YYMMDD>-<task>`. If no slug was given, use the study
this session is working on; if there isn't one, ask. If the target has no `LOGBOOK.md`,
stop and say so: a summary is built from a logbook, never from scratch.

## 2. Brief the agent

Spawn `study-summarizer`. Its context starts empty, so the brief has to carry:

- the target, and whether a `SUMMARY.tex` already exists (a refresh), only an old
  `SUMMARY.md` (convert it to tex), or neither (first version);
- the **occasion**, if one was given ("for Thursday's meeting", "closing the study"), which
  sets what to emphasise;
- anything this session knows that the logbook doesn't record yet: a result that came in
  but isn't logged, or a conclusion you know has been superseded. Better still, log it
  first, because the summary must trace to the logbook;
- the layout, if it's unusual: a single-layer study with no task dirs (cite dated entries),
  figures that live outside the study dir (embed by full `https://submit.mit.edu/~lavezzo/...`
  URL, after checking the file exists);
- what not to do: no logbook edits, no web publishing.

## 3. When it returns

1. Read the summary yourself (the PDF) before reporting. Check that it is standalone,
   two to four pages, carries its results in figures, has units on its numbers, and puts
   caveats before numbers. If the agent returned `MISSING FIGURE`, decide with Luca whether
   to dispatch a task for it.
2. Give Luca: the web link (`https://submit.mit.edu/~lavezzo/alphaS/studies/#<slug>`, and
   `#<slug>:logbook`), the PDF path, the one-line answer, and the agent's
   `UNTRACED / INCONSISTENT` items. Those are logbook problems, so they go to Luca rather
   than being buried.
3. If the study isn't published (`ls ~/public_html/alphaS/studies/<slug>`), say so and offer
   `scripts/webpublish_study.sh <slug>`. Don't run it unasked: the page has no
   authentication.
4. If you are the study's orchestrator, log one dated line: "summary refreshed, covers
   through YYYY-MM-DD", and update the `Summary:` line in START HERE. Otherwise leave the
   logbook alone.
