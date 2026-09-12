# Narrow check_docs_content_policy.py's "full file tree" check to avoid false-positive on non-tree diagrams

## Priority
Medium

## Summary
`tools/check_docs_content_policy.py`'s `full file tree` check flags
`docs/04_mcp_03_03_transport-and-health.md` lines 52-56 — a `McpServerHealthRegistry`
state-transition diagram, not a directory tree — because it only tests for the
presence of `├`/`│`/`└` characters rather than directory-tree structure. Narrow the
check so it stops matching non-tree ASCII diagrams that happen to reuse the same
Unicode box-drawing glyphs.

## Background
Discovered as `UNK-03` while executing
`implementations/20260909-194838_03_docs_04_mcp_03_03_transport-and-health_md.md`
(part of `plans/done/20260908-211017_plan.md`, which covered literal-port-number
removal only). `plans/done/20260908-211017_plan.md`'s `REQ-001` covers literal port
numbers only, so this finding was not in that Plan's scope. A related, unrelated-area
finding in the same file (`implementation-location mapping`, line 24) is tracked
separately in `dcp007`.

## Problem
`uv run python tools/check_docs_content_policy.py` reports 5 `full file tree`
findings for `docs/04_mcp_03_03_transport-and-health.md`, one per line of:
```
HEALTHY ──(failure × threshold)──→ UNAVAILABLE
   ↑                                    │
   │                            (cooldown 30s elapsed)
   │                                    ↓
   └──(record_success)────────── HALF_OPEN (trial probe)
                                         │
                               (failure)─┘ → UNAVAILABLE (cooldown reset)
```
This is a state-transition diagram for `McpServerHealthRegistry`'s health states
(`HEALTHY`/`DEGRADED`/`UNAVAILABLE`/`HALF_OPEN`), not a directory listing. Per
`skills/DESIGN.md` Docs content policy — remove, the `full file tree` category is
defined as "a literal ASCII directory tree ... Example: a '## File Structure' section
drawing out an entire directory listing" — this diagram matches neither the
definition nor the example. It is exactly the kind of content Docs content policy —
retain calls out as worth keeping ("Component responsibility", state ownership), not
implementation-detail duplication.

## Reason for Change
The check currently keys off the mere presence of `├`/`│`/`└` characters (per
`tools/check_docs_content_policy.py`'s docstring/behavior for this category), so any
non-tree ASCII diagram reusing the same Unicode box-drawing glyphs (state machines,
sequence diagrams, wiring diagrams) is misclassified as a violation. Left uncorrected,
this either produces a permanent false-positive finding for this file, or invites
authors to redraw legitimate diagrams without box-drawing characters purely to satisfy
the checker — degrading diagram readability for no policy benefit.

## Implementation Intent
Narrow `check_docs_content_policy.py`'s `full file tree` detection so it requires
actual directory-tree shape (e.g. a nearby "File Structure"/"Directory" heading, or a
line pattern resembling `path/to/file.ext` alongside the box-drawing character) rather
than the box-drawing characters alone. Prefer the narrowest change that keeps existing
true-positive detections (e.g. `01_overview-files-*.md`'s real file trees) working
unchanged.

## Target Files or Areas
- `tools/check_docs_content_policy.py`
- `tests/tools/test_check_docs_content_policy.py`

## Required Changes
1. Adjust the `full file tree` check (see `check_docs_content_policy.py`'s handling of
   this category, analogous to the recent auto-generated-block exemption added for the
   `literal port number` check) so a box-drawing character alone, without accompanying
   directory-tree structure, does not match.
2. Add a regression test in `tests/tools/test_check_docs_content_policy.py` using a
   non-tree diagram (e.g. a state-transition diagram like this issue's example) to
   confirm it is no longer flagged, alongside a real file-tree fixture that must still
   be flagged.
3. Re-run `uv run python tools/check_docs_content_policy.py` and confirm the 5 findings
   for `docs/04_mcp_03_03_transport-and-health.md` lines 52-56 are gone, with no
   change to true-positive findings elsewhere (e.g. `01_overview-files-*.md`).

## Constraints
- Do not weaken the check so an actual directory tree stops being flagged — verify
  against at least one existing true-positive file (e.g. `01_overview-files-01-build.md`)
  before and after the change.
- Do not edit `docs/04_mcp_03_03_transport-and-health.md` as part of this issue — the
  diagram itself is not the problem; see `dcp007` for that file's unrelated,
  legitimate finding.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero `full file tree`
  findings for `docs/04_mcp_03_03_transport-and-health.md`.
- Existing true-positive `full file tree` findings (e.g. in `01_overview-files-*.md`)
  are unchanged.
- A new regression test in `tests/tools/test_check_docs_content_policy.py` covers a
  non-tree box-drawing diagram.

## Testing Expectations
- `uv run pytest tests/tools/test_check_docs_content_policy.py -v`
- `uv run python tools/check_docs_content_policy.py` (manual smoke test against live
  `docs/` content, per `routing.md` "Adding a new tool" step 4)
- `uv run ruff format tools/check_docs_content_policy.py` and
  `uv run ruff check tools/check_docs_content_policy.py`
- `uv run mypy tools/check_docs_content_policy.py`
- `uv run bandit tools/check_docs_content_policy.py`

## Documentation Impact
N/A: no `docs/*.md` content changes as part of this issue — `tools/` behavior only.

## Out of Scope
- `docs/04_mcp_03_03_transport-and-health.md`'s `implementation-location mapping`
  finding (line 24) — tracked in `dcp007`.
- Any other `check_docs_content_policy.py` category (literal port number,
  implementation-location mapping, class/function-index, per-file description).

## Dependencies
N/A: independent of `dcp007` (same file, different finding category) — either can be
done without the other.

## Unresolved Questions
- Whether other `docs/*.md` files contain similar non-tree box-drawing diagrams that
  are also being misclassified — not verified during this investigation; worth a
  repository-wide `check_docs_content_policy.py` re-run once the fix lands to confirm
  no other false positives surface or disappear unexpectedly.

## AI Implementation Instruction
Change only the `full file tree` detection logic in `tools/check_docs_content_policy.py`
and its regression test. Do not touch the `literal port number`,
`implementation-location mapping`, or other category checks. Do not edit any
`docs/*.md` file. Run the full `tests/tools/test_check_docs_content_policy.py` suite,
not just the new test, before considering this done.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20260908-211017_plan.md (`UNK-03`)
- **Source implementation procedure**: implementations/20260909-194838_03_docs_04_mcp_03_03_transport-and-health_md.md
- **Generated at**: 20260909-200213
- **Related target files**: tools/check_docs_content_policy.py, tests/tools/test_check_docs_content_policy.py
