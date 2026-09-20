# check_docs_content_policy.py: heading-window heuristic causes false positives after edits

## Priority
Medium

## Summary
`tools/check_docs_content_policy.py`'s `check_error_handling_table()` and
`check_config_file_inventory_table()` decide whether a table/bullet-list is
"error-handling"/"config-file-inventory" content by checking whether an
`_ERROR_HEADING_RE`/`_CONFIG_HEADING_RE`-matching heading appears within
`_HEADINGS_WINDOW` (10) lines above it — with no allowance for unrelated content that
happens to fall inside that window. Two confirmed cases on 2026-09-20 show that
removing a flagged table/list (the tool's own intended remediation) can shrink the
line-distance to an adjacent, unrelated section enough to pull it into the window,
producing a new false-positive finding purely as a side effect of fixing an earlier
one.

## Background
The window-based heuristic is documented in `check_error_handling_table()`'s own
docstring (`tools/check_docs_content_policy.py:666`) as "Flag a table under an
Error/Exception/Error Handling heading ... independent of a nearby heading" — i.e. it
is deliberately heading-proximity-based rather than requiring the table to be
structurally nested under the heading (e.g. via Markdown section boundaries). This
design was exercised extensively during a 2026-09-20 batch that removed
mechanically-derivable tables/lists across 22 `docs/*.md` files
(`implementations/done/20260920-16*.md`), two of which triggered this side effect.

## Problem
1. **`docs/05_agent_05_llm-and-streaming.md`** (implementation procedure
   `implementations/done/20260920-163055_01_docs_05_agent_05_llm-and-streaming.md.md`):
   removing the "Partial Completion Persistence Rules" and "Error Type Design" tables
   left the retained `### Error Type Design` heading directly above an unrelated
   `### Runtime Parameter Generation` table (a config-field/hot-reload mapping, not
   error-handling content). The removal shortened the line-distance between the two
   enough that `_ERROR_HEADING_RE` (matching the literal word "Error" at the start of
   a heading) now found `### Error Type Design` within `_HEADINGS_WINDOW` of the
   unrelated table, flagging it as a new `error-handling table` finding. Worked around
   by renaming the heading to `### LLMTransportError Kind Categories` (the first word
   no longer matches `_ERROR_HEADING_RE`, which anchors on the heading's first word
   after the `#` markers).
2. **`docs/06_eventbus_05_configuration-and-operations.md`** (implementation procedure
   `implementations/done/20260920-163249_02_docs_06_eventbus_05_configuration-and-operations.md.md`):
   replacing 8 of 20 `Configuration Fields` bullets with a one-sentence pointer pulled
   the 12 untouched bullets — including `publisher_token`/`consumer_token`, explicitly
   protected as security-relevant content by the source Plan
   (`plans/done/20260920-160505_plan.md`) — into the `_HEADINGS_WINDOW` of the
   `### Configuration Fields` heading, producing new `config-file inventory
   correspondence entry` findings for content that was correctly *not* flagged before
   the edit. Worked around by expanding the pointer paragraph with additional prose
   until the remaining bullets fell outside the 10-line window.

In both cases the newly-flagged content was not itself mechanically-derivable filler —
it required either an unrelated rewrite (case 1) or padding an otherwise-complete
sentence with extra clauses purely to manipulate line count (case 2), neither of which
is a content-quality improvement in its own right.

## Reason for Change
A checker whose own remediation can trigger a new, unrelated false positive creates a
whack-a-mole editing loop and forces workarounds (heading renames, padded prose) that
exist only to satisfy the tool rather than to improve document quality — the opposite
of `skills/DESIGN.md` Docs content policy's intent. This also means the *order* in
which findings are fixed within a file can change the total mechanical-content removed
depending on which sections end up within `_HEADINGS_WINDOW` of which heading, which is
not decidable from reading the flagged finding alone.

## Implementation Intent
Reduce the heuristic's sensitivity to incidental line-count changes, e.g.:
- Scope the heading-window check to the same Markdown section (bounded by the next
  heading of equal-or-higher level), not merely bounded by line-count — a table 6
  lines under `### Error Type Design` is far more likely to belong to that section
  than one 6 lines under a heading that is itself followed by a different `###`
  heading before the table.
- Alternatively (or additionally), narrow `_ERROR_HEADING_RE`/`_CONFIG_HEADING_RE`
  from a first-word match to require the heading's full topic to be about errors/config
  (e.g. exclude a heading that is itself about a *category* of error values, like
  "Error Type Categories", from being treated as introducing an error-handling table
  below it) — though this is a narrower, more heuristic-specific fix than the
  section-scoping approach above.
- At minimum, re-scan and re-run the checker after each edit within the same file
  during `code-implementation`'s own Step 3e loop is already required practice — this
  issue is about reducing how often that re-scan finds a *new*, unrelated finding
  rather than confirming the *fixed* one is gone.

## Target Files or Areas
- `tools/check_docs_content_policy.py`

## Required Changes
1. Change `check_error_handling_table()` (line 666) and
   `check_config_file_inventory_table()` (line 405) to scope their heading-proximity
   check to the same Markdown section (i.e. stop scanning backward for a matching
   heading once a different heading of equal-or-higher level is encountered), instead
   of relying solely on `_HEADINGS_WINDOW`'s fixed line count.
2. Add regression tests reproducing both confirmed cases: (a) an error-type-value
   heading directly above an unrelated table that is itself preceded by a different
   heading within 10 lines, and (b) a config-field heading whose untouched bullet list
   extends within 10 lines of the heading after an earlier bullet in the same list was
   replaced with a pointer sentence.
3. Re-run `uv run python tools/check_docs_content_policy.py` against the full `docs/`
   tree and confirm no findings appear for the two files cited in Problem beyond what
   is already recorded as pre-existing/intentional per their respective implementation
   procedures.

## Constraints
- Do not weaken the heuristic to the point it stops catching a table that is
  genuinely under a matching heading, including when other prose separates them within
  the same section.
- Do not change `_HEADINGS_WINDOW`'s value as a blunt fix (e.g. lowering it) without
  verifying it does not reintroduce missed detections on already-passing cases in the
  existing test suite.

## Acceptance Criteria
- A table 6 lines below a heading matching `_ERROR_HEADING_RE`, where a different
  `###` heading appears between the matching heading and the table, is not flagged.
- A table/bullet-list genuinely nested directly under a matching heading (no
  intervening heading) is still flagged, regardless of exact line distance up to the
  existing window bound.
- `uv run pytest tests/tools/test_check_docs_content_policy.py -v` passes, including
  the two new regression tests from Required Changes item 2.

## Testing Expectations
Extend `tests/tools/test_check_docs_content_policy.py` with the two regression cases
above. Run `uv run pytest tests/tools/test_check_docs_content_policy.py -v`,
`uv run ruff check tools/check_docs_content_policy.py`, and
`uv run mypy tools/check_docs_content_policy.py`. Also re-run
`uv run python tools/check_docs_content_policy.py` against the full `docs/` tree
before and after the fix to confirm no unrelated finding count regression (compare
against the current full-corpus baseline before starting).

## Documentation Impact
N/A: this is an internal tooling accuracy fix with no `docs/00_index.md` task-scope
mapping.

## Out of Scope
- The two already-applied workarounds in `docs/05_agent_05_llm-and-streaming.md` and
  `docs/06_eventbus_05_configuration-and-operations.md` — both are functioning,
  content-preserving fixes already landed; this issue is about preventing the
  underlying tool behavior from requiring such workarounds in future edits, not about
  reverting or redoing those two files.
- `check_docs_content_policy.py`'s other detection functions
  (`check_full_json_example`, `check_literal_port_number`, etc.) — only the two
  heading-window-based functions are in scope.
- The separate, already-tracked guard-comment-format exemption bug referenced in
  `docs/adr/ADR-015-reference-document-class-disposition.md`'s Consequences section
  (`GV-021`) — unrelated detection logic.

## Dependencies
N/A: none.

## Unresolved Questions
Whether section-scoping (bounded by the next equal-or-higher-level heading) fully
replaces `_HEADINGS_WINDOW` or should be combined with it (e.g. section-scoped *and*
within N lines) is an implementation-time design choice — resolve by checking whether
any currently-passing test in `tests/tools/test_check_docs_content_policy.py` relies on
cross-section detection before deciding.

## AI Implementation Instruction
Read `check_error_handling_table()` and `check_config_file_inventory_table()` in full,
including their shared use of `_HEADINGS_WINDOW`, before changing either. Implement
section-scoping per Implementation Intent, verify against the two concrete cases in
Problem (the pre-fix content is visible via `git log -p` on
`docs/05_agent_05_llm-and-streaming.md` and
`docs/06_eventbus_05_configuration-and-operations.md` around 2026-09-20), and confirm
the full existing test suite for this file still passes before considering the fix
complete.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-175121
- **Related target files**: tools/check_docs_content_policy.py
