# Talking to CERN GitLab from this machine (API, MRs, issues)

`glab` is not installed and there is no ambient API token, so for a long time
everything on gitlab.cern.ch was "write a draft, ask Luca to paste it". It is
not: there is a personal access token at

    ~/.cern_gitlab_pat        (mode 600, one line, `glpat-…`)

Read it into a variable, never echo it, never put it in a log, a commit, a
logbook or anything under `~/public_html` (which is world-readable and is where
study directories are published):

    TOK=$(tr -d '\r\n' < ~/.cern_gitlab_pat)
    API=https://gitlab.cern.ch/api/v4
    PROJ=scetlib%2Fcontrib%2Fscetlib-cms      # path, URL-encoded

Read an MR, set its description from a file, comment, open an issue:

    curl -s --header "PRIVATE-TOKEN: $TOK" "$API/projects/$PROJ/merge_requests/13"

    python3 -c "import json;json.dump({'description':open('MR_BODY.md').read()},open('/tmp/p.json','w'))"
    curl -s --request PUT --header "PRIVATE-TOKEN: $TOK" \
         --header "Content-Type: application/json" --data @/tmp/p.json \
         "$API/projects/$PROJ/merge_requests/13"

    curl -s --request POST --header "PRIVATE-TOKEN: $TOK" \
         --form "body=<comment.md" "$API/projects/$PROJ/merge_requests/13/notes"

    curl -s --request POST --header "PRIVATE-TOKEN: $TOK" \
         --form "title=..." --form "description=<ISSUE.md" "$API/projects/$PROJ/issues"

Always build JSON with python rather than shell interpolation: MR bodies contain
backticks, quotes and newlines, and a hand-rolled `--data "{...}"` will mangle
them or, worse, execute them.

## What needs kinit and what does not

* The **API token** is self-contained — no Kerberos needed.
* **SSH push** (`ssh://git@gitlab.cern.ch:7999/...`) uses the ssh key, also no
  Kerberos.
* `kinit` is for AFS/EOS and for web SSO; ask Luca to run it when a step needs
  those, since it is interactive.

## Opening an MR without the API at all

`git push` accepts GitLab push options, which is how MR !13 was opened before
the token turned up:

    git push -u origin <branch> \
      -o merge_request.create \
      -o merge_request.target=autodiff-sigmaul \
      -o merge_request.title="..."

The push prints the MR URL. GitLab prefills the description from the commit
body when the branch has one commit, so a thorough commit message is worth
writing even when you intend to replace the description afterwards.

## `git fetch` BEFORE you claim anything about upstream

Our sibling checkouts (`scetlib-cms` in particular) are long-lived working trees
that nobody pulls unless a build needs it, and `origin/<branch>` in them is a
**cached** ref: it is whatever the last fetch saw, not the branch tip. Reading it
as HEAD is silent — there is no warning, the log looks complete, and `git log
origin/<branch>` prints a plausible history.

Cost, measured 2026-09-22: a local `scetlib-cms` checkout **72 commits behind**
`origin/autodiff-sigmaul` led `studies/alphas-scan-discontinuity/` to report two
upstream defects as unfixed when both were already fixed upstream — one of them
deliberately, by a commit that diagnoses the problem in the same terms we had.
The error survived a task worker and an orchestrator and was caught only because
a collaborator said "I think I added that".

**So: `git fetch --all` (or `git fetch origin <branch>`) before quoting a commit,
before saying "upstream has not fixed this", and before opening an issue or an
MR.** Name the SHA you actually read, and say when you fetched it — a claim about
a branch tip is only as fresh as the fetch behind it.

Related: [[scetlib_cache_format_versions_and_pins]] for which branch a cache
build must be pinned to.
