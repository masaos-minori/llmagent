# docs/adr-index.md's ADR List omits the live ADR-013 and its "deleted" note is stale

## Priority
Medium

## Summary
`docs/adr-index.md`'s ADR List table lists ADR-001 through ADR-010, then jumps to
ADR-012 and ADR-014 — skipping ADR-013 — and a note below the table states "ADR-013
（MCP Tool Availability Model）はADR-003へ統合され、削除された。" (ADR-013 was merged into
ADR-003 and deleted). `docs/adr/ADR-013-eventbus-authentication-authorization.md`
currently exists, is `Status: Accepted`, and covers EventBus authentication/
authorization — an unrelated, live topic, not "MCP Tool Availability Model". Confirmed
still present as of 20260919 (not fixed by any later change to `docs/adr-index.md`).

## Background
Originally surfaced as a risk follow-up
(`issues/done/20260919-104524_risks.md` — since deleted per this issue's creation) filed
while planning `issues/20260918-130115_adrref01_decide-reference-class-fate-via-adr.md`
(which itself needed to register a new ADR in `docs/adr-index.md` and, while doing so,
read the ADR List to determine the next available number). Not fixed inline at the time
because doing so would have edited content outside that Plan's own scope.

## Problem
`docs/adr-index.md` is the canonical ADR list, dependency graph, and invariant
verification matrix per `docs/00_governance_01_documentation-policy.md`'s ADR Section
Header Standardization ("The ADR list, dependency graph, and invariant verification
matrix are maintained in `adr-index.md`"). A reader relying on this index believes
ADR-013 does not exist / was deleted, when it is in fact a currently `Accepted` ADR
governing EventBus authentication and authorization.

## Reason for Change
This gap could cause a future ADR author to accidentally reuse the ADR-013 number for a
new, unrelated decision (the index's own gap makes it look "available"), or cause a
reviewer checking ADR dependency/coverage via the index to overlook ADR-013 entirely,
since it is absent from both the ADR List table and the ADR Dependency Graph.

## Implementation Intent
Add an ADR List row for ADR-013 in the same format as the existing rows (ID, Japanese
title, Status, file path), sourced from `docs/adr/ADR-013-eventbus-authentication-authorization.md`'s
own front matter/Status section (`Status: Accepted`). Correct or remove the stale
"ADR-013 was merged into ADR-003 and deleted" note — investigate whether that description
was ever accurate for a different, no-longer-present ADR number rather than simply
deleting it without checking (`docs/adr-index.md`'s existing "ADR-011...統合され、削除された"
line for a genuinely-merged ADR shows the correct form such a note should take when
accurate). Add ADR-013 to the ADR Dependency Graph, consistent with the existing entries'
`ADR-X → ADR-Y, ADR-Z` format — its own front matter already declares
`related: [ADR-002, ADR-006]`, which is the strongest available evidence for this edge,
but confirm by reading ADR-013's body (Context/Rationale) before asserting the direction
of the dependency, not only its front matter.

## Target Files or Areas
- `docs/adr-index.md` (ADR List table, the stale note below it, ADR Dependency Graph)

## Required Changes
- Add a row: `| ADR-013 | <Japanese title, e.g. Event Bus認証・認可> | Accepted |
  \`adr/ADR-013-eventbus-authentication-authorization.md\` |` in correct numeric position
  between ADR-010 and ADR-012.
- Remove or correct the "ADR-013（MCP Tool Availability Model）はADR-003へ統合され、削除された。"
  note — do not leave a stale claim about a live ADR number.
- Add an ADR-013 edge (or edges) to the ADR Dependency Graph if investigation of ADR-013's
  own Context/Rationale confirms a real dependency on ADR-002 and/or ADR-006 (its front
  matter's `related` list is a starting hint, not confirmation by itself).

## Constraints
Do not modify `docs/adr/ADR-013-eventbus-authentication-authorization.md` itself — this
issue is scoped to correcting the index, not the ADR it indexes. Do not renumber or
reassign any other ADR ID while fixing this.

## Acceptance Criteria
- `docs/adr-index.md`'s ADR List table includes a row for ADR-013 matching its real
  title/status/path.
- The stale "ADR-013 was merged into ADR-003 and deleted" note no longer appears
  unchanged; it is either removed or corrected to accurately describe whatever it was
  actually meant to reference.
- If ADR-013 has a genuine dependency per its own Context/Rationale, the ADR Dependency
  Graph reflects it.
- `uv run python tools/check_docs_quality.py` and
  `uv run python tools/check_docs_structure.py docs/adr-index.md` report no new findings.

## Testing Expectations
Not required for behavior — this is a documentation-only correction. Run the two checker
commands listed in Acceptance Criteria to confirm no structural regression.

## Documentation Impact
This issue's entire scope is a documentation correction to `docs/adr-index.md` — no
further Documentation Impact beyond the change itself.

## Out of Scope
Re-evaluating any other ADR's status, title, or dependency edges in `docs/adr-index.md`
beyond ADR-013's own row and the stale note referencing it.

## Dependencies
N/A: none.

## Unresolved Questions
Whether the stale "ADR-013（MCP Tool Availability Model）はADR-003へ統合され、削除された。"
note was ever accurate for some other, now-renumbered or since-removed ADR is not
investigated here — left for the implementer to check (e.g. via `git log -p
docs/adr-index.md`) before deciding whether to simply delete the note or correct it to
reference a different ID.

## AI Implementation Instruction
Change only `docs/adr-index.md`. Verify ADR-013's title/status directly from
`docs/adr/ADR-013-eventbus-authentication-authorization.md` before writing the new row —
do not guess the Japanese title wording beyond what's reasonable from the file's own
English title. Investigate `git log -p docs/adr-index.md` for the stale note's origin
before deciding whether to delete or correct it. Keep the diff minimal and scoped to the
ADR List table, the stale note, and (if warranted) the Dependency Graph.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-104524_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-165929
- **Related target files**: docs/adr-index.md
