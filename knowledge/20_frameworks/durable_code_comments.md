# Comments must be written for the merged tree, not for the branch

Convention enforced by review on WMass/rabbit (davidwalter2, 2026-09-14; he
traces it to a review on #154). It cost a pass over three PRs to retrofit, so
write them this way the first time.

## The rule

**Strip the development history, keep the reasoning.**

A comment that positions itself relative to work-in-progress stops being true
the moment it merges. The information is usually worth keeping; it is the
framing that expires.

## What expires

| pattern | why it breaks |
|---|---|
| "a property of the two commits below this one in the stack" | after merge there is no stack — and "not of main" **inverts**, becoming false |
| "this assertion used to read …" | refers to a version of the file nobody can see |
| "the blocker: this construction used to raise" | which blocker? |
| "covered now that the reframing below this in the stack handles it" | unresolvable |
| "that is the 2026-09-09 alpha_s bug" | dates the reasoning to an incident a future reader cannot look up |
| "which is the whole argument of this PR" | which PR? |

The worst case in our stack was attached to the one line where getting the
ordering wrong silently unblinds a fit — a statement that was both
unresolvable *and* false, exactly where a reader most needs to trust it.

## What does not expire

- **Runtime state**: "whichever offsets are currently armed" — "currently"
  means at the time of the call, not during development. Fine.
- **A pointer to a test**: "Pinned by `tests/test_saturated_blinding.py`" reads
  just as well in a year, and is the durable way to say "this is load bearing".
- **The mechanism**: say what goes wrong, not when it went wrong. Instead of
  "that is the 2026-09-09 alpha_s bug", write "for a POI fed into a calculation
  with a restricted domain this is an evaluation error".

## Rewrite recipe

Ask: *would this sentence still be true, and still resolvable, if someone read
it a year from now with no knowledge of the branch?* If not, state the property
directly and drop the provenance. Commit messages are the right home for
provenance — they are a historical record and are read as one.
