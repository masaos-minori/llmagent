# Resolve NC-038: Memory reference-class migration target and wiring

## Priority
Medium

## Summary
Confirm the target document(s) for the Memory-layer Reference-class migration
(`UNK-01`/`NC-038`) and finish wiring `generate_memory_reference_table()` into
`tools/generate_reference_table.py`'s `--type` dispatch, completing Step 4 of
`plans/done/20260919-105034_plan.md`, which has stood `In Progress` since 2026-09-19.

## Background
`docs/adr/ADR-015-reference-document-class-disposition.md` (Accepted, 2026-09-19)
adopted Option B: Reference-class documents are generated artifacts. Agent
(`docs/05_agent_13_reference-api.md` + companion `05_agent_14_reference-api-generated.md`)
and EventBus (`docs/06_eventbus_06_reference-api.md`) have both completed this
migration. Memory is the one domain ADR-015's own Implementation Notes leave
unresolved, tracked as `NC-038` in
`docs/00_governance_03_issue-and-uncertainty-management.md` and as `UNK-01`/Step 4 in
`plans/done/20260919-105034_plan.md`.

## Problem
- `tools/generate_reference_table.py::generate_memory_reference_table()` (line 279) is
  already implemented (returns `_generate_class_function_reference_table(MEMORY_DIR)`,
  same pattern as `generate_agent_reference_table()`/`generate_eventbus_reference_table()`),
  but `DOMAIN_GENERATORS`, `DOMAIN_DOCS`, `DOMAIN_GUARDS`, `DOMAIN_WELCOME_LINES`, and
  `DOMAIN_HEADING` have no `"memory"` entry — `--type memory` is not a usable CLI option.
- No `docs/*.md` file has an `<!-- AUTO-GENERATED: ... memory ... -->` guarded block yet.
- `UNK-01`'s open question is still unresolved: 6 candidate files carry a "Memory Layer"
  title (`docs/05_agent_12_01_memory-overview-and-modes.md` through
  `docs/05_agent_12_06_memory-module-ref-ops-and-scoring.md`, confirmed via each file's
  own front-matter `title` on 2026-09-20). Of these, 4 are titled "Module Reference"
  (`12_03`-`12_06`) and 2 are titled "Overview and Modes"/"Activation Gate, Data Model,
  and Search" (`12_01`, `12_02`) — the Plan's own wording leaves open whether the latter
  two are in scope for generated-artifact migration at all.
- `plans/done/20260919-105034_plan.md`'s Execution Status table still shows Step 4
  `In Progress` with no Completed date, and its own Risk note says `UNK-01` should be
  resolved "by reading the [Reference-class] ADR's Implementation Notes section ... before
  choosing the memory target document" — ADR-015 is now Accepted, so that gating
  condition is satisfied and this work is unblocked.

## Reason for Change
Until this is resolved, Memory-layer API/class reference material in
`docs/05_agent_12_03`-`06` remains hand-maintained Reference-class content — exactly the
drift-prone pattern ADR-015 was adopted to eliminate for Agent/EventBus. Leaving it open
also leaves `plans/done/20260919-105034_plan.md` permanently `In Progress`, which
`tools/manage_workitem_stage.py detect-stale` would flag as a stale in-progress
workitem.

## Implementation Intent
Follow the Agent precedent recorded in that same Plan's Blocker Log (entry for Step 2):
when a domain's reference content does not fit cleanly into one existing hand-curated
document, add a dedicated `*-generated.md` companion file rather than overloading an
existing hand-curated one. Decide `UNK-01` first (target document(s) and whether
`12_01`/`12_02` are in scope), then extend `generate_reference_table.py`'s five
`DOMAIN_*` dictionaries with a `"memory"` entry mirroring the existing `"agent"`/
`"eventbus"` entries, then run the generator to populate the guarded block(s).

## Target Files or Areas
- `tools/generate_reference_table.py` (DOMAIN_* dictionaries)
- `docs/05_agent_12_03_memory-module-ref-core-and-store.md` through
  `docs/05_agent_12_06_memory-module-ref-ops-and-scoring.md` (primary migration
  candidates)
- `docs/05_agent_12_01_memory-overview-and-modes.md`,
  `docs/05_agent_12_02_memory-gate-data-model-search.md` (in-scope status: Unknown —
  resolve as part of this issue)
- Possibly a new `docs/05_agent_12_XX_memory-module-reference-generated.md` companion
  file, if the target-document decision follows the Agent precedent
- `docs/00_governance_03_issue-and-uncertainty-management.md` (`NC-038` status update)
- `plans/done/20260919-105034_plan.md` (Step 4 Execution Status update)

## Required Changes
1. Decide `UNK-01`: which document(s) receive the generated Memory reference block, and
   whether `12_01`/`12_02` are in scope. Record the decision and its rationale (this can
   go directly in the Plan's Blocker Log per its existing pattern, or in a short ADR
   addendum if the decision materially extends ADR-015's Implementation Notes).
2. Add a `"memory"` entry to `DOMAIN_GENERATORS`, `DOMAIN_DOCS`, `DOMAIN_GUARDS`,
   `DOMAIN_WELCOME_LINES`, and `DOMAIN_HEADING` in `tools/generate_reference_table.py`,
   mirroring the existing `"agent"`/`"eventbus"` entries exactly in structure.
3. Add the guard-comment block (`<!-- AUTO-GENERATED: ... -->` / `<!-- AUTO-GENERATED-END
   -->`) to the target document(s) chosen in Step 1.
4. Run `uv run python tools/generate_reference_table.py --type memory` (dry-run first,
   then live) and confirm the guarded block populates correctly.
5. Update `plans/done/20260919-105034_plan.md`'s Execution Status Step 4 row to
   `Completed` with a completion timestamp.
6. Update `NC-038` in `docs/00_governance_03_issue-and-uncertainty-management.md` to
   `Status: resolved`, per `tools/check_needs_confirmation_inventory.py`'s inventory
   convention.

## Constraints
- Follow the existing generator pattern exactly (`_generate_class_function_reference_table`
  already generalizes over a directory constant — no new generation logic should be
  needed beyond the `MEMORY_DIR` constant already defined at line 34).
- Do not hand-edit content between the new guard comments once generated — per ADR-015's
  Invariants.
- Do not modify the Agent/EventBus `DOMAIN_*` entries or their generated documents.

## Acceptance Criteria
- `uv run python tools/generate_reference_table.py --type memory --dry-run` succeeds and
  its output matches what a live run writes.
- The target document(s) decided in Step 1 contain a populated, guard-commented Memory
  reference block.
- `uv run python tools/manage_workitem_stage.py show plan plans/done/20260919-105034_plan.md`
  confirms Step 4 is `Completed`.
- `uv run python tools/check_needs_confirmation_inventory.py` shows `NC-038` as resolved.
- `uv run python tools/check_docs_structure.py` and `check_docs_content_policy.py` pass
  for the modified/new document(s) (the generated block is guard-exempt per `GV-021`'s
  intended exemption — confirm the guard format matches what `check_docs_content_policy.py`
  actually recognizes, since ADR-015's Consequences flag this exemption as
  currently mismatched for a *different* guard format bug; verify it is not also
  mismatched for the new `memory` guard strings before relying on the exemption).

## Testing Expectations
`uv run pytest tests/tools/test_generate_reference_table.py -v` (existing test file,
extend with a `memory` case per the `agent`/`eventbus` precedent). Also run
`uv run python tools/check_docs_content_policy.py`,
`uv run python tools/check_docs_structure.py`, and
`uv run python tools/check_docs_consistency.py --domain agent` (Memory is part of the
Agent area per front matter).

## Documentation Impact
Yes — this issue both adds new generated documentation content and updates two
governance tracking documents (`NC-038` entry, Plan Execution Status).

## Out of Scope
- Extending `generate_reference_table.py` to any domain other than `memory`.
- Re-opening the Agent/EventBus migration decisions already completed under this Plan.
- Fixing the unrelated guard-format exemption bug in `check_docs_content_policy.py`'s
  `GV-021` that ADR-015's Consequences section already tracks separately — only confirm
  during Acceptance Criteria that the new `memory` guard strings are not independently
  affected; do not fix the underlying bug here if it turns out to also apply.

## Dependencies
- **Source plan**: `plans/done/20260919-105034_plan.md` (this issue completes its
  outstanding Step 4 / resolves its `UNK-01`).
- Depends on `docs/adr/ADR-015-reference-document-class-disposition.md` remaining
  `Accepted` (already satisfied).

## Unresolved Questions
- Whether `docs/05_agent_12_01_memory-overview-and-modes.md` and
  `docs/05_agent_12_02_memory-gate-data-model-search.md` are in scope for generated-artifact
  migration, or only the four "Module Reference"-titled files (`12_03`-`12_06`) — this is
  `UNK-01` itself and must be resolved as Required Changes Step 1, not assumed here.
- Whether the target is one primary document with cross-references (the Agent pattern:
  hand-curated `05_agent_13_reference-api.md` + generated companion
  `05_agent_14_reference-api-generated.md`) or guarded blocks distributed across the
  existing 4-6 Memory chapter files — also part of `UNK-01`, to be decided during
  implementation per the Plan's own deferral ("Confirm during
  `plan-to-implementation-procedure`/`code-implementation`").

## AI Implementation Instruction
Resolve `UNK-01` first and record the decision before touching any code or doc file —
do not default to one option without stating the rationale, since the Plan explicitly
deferred this choice. Once decided, mirror the existing `agent`/`eventbus` wiring in
`tools/generate_reference_table.py` exactly (same dictionary shapes, same guard-comment
format). Do not hand-edit generated content after running the generator. Update the
Plan's Execution Status and the `NC-038` inventory entry as the final step, not before
the generation is verified working.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20260919-105034_plan.md`
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-154806
- **Related target files**: see Target Files or Areas above
