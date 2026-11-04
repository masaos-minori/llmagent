## Goal

Update the "Turn Persistence Boundary" compensation description in the state-and-persistence
state-model document so it states the compensation guarantee after a turn that compressed:
the session's rows return to their turn-start content (same `message_id` and `created_at`)
and the `/undo` boundary resets, instead of only removing rows above the marker. Keep the
existing append-only description and the fail-safe description.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The document is the canonical persistence-model reference for the agent subsystem; its
  "Turn Persistence Boundary" section is the single place the compensation rule is stated
  (checked in Step 2 and via `docs/00_index.md` "Document References by Task").
- REQ-006 forbids copying concrete values into the documentation, so the update describes the
  guarantee in general terms (which rows are restored, what is preserved) without specific
  `message_id` numbers or counts (AC-7).
- The existing append-only compensation rule and the dedicated-error-type bullet remain true;
  only the Compensation bullet is widened to cover the rewrite case.

## Design decisions

- Extend the existing "Compensation" bullet rather than adding a new one, so the two
  compensation cases (append-only vs. after-rewrite) read as one coherent rule and the section
  keeps its current structure.
- State both the success path (restore turn-start rows + reset boundary) and the fail-safe path
  (a failing restore leaves rows untouched and still raises), matching REQ-002 and REQ-003.

## Alternatives considered

- Adding a separate paragraph under a new heading: rejected; the compensation rule is a single
  concept with two branches, so one expanded bullet keeps the two cases comparable.

## Implementation
### Target file
`docs/23_agent/agent_04_01_state-and-persistence-state-model.md`

### Procedure
1. In the "Turn Persistence Boundary" section, expand the "**Compensation.**" bullet:
   - Add the after-rewrite case: on a turn that compressed, compensation restores the
     turn-start rows with their original `message_id` and `created_at`, at or below the marker,
     and resets the `/undo` boundary, instead of deleting above the marker.
   - Note that compensation returns the persisted session to its turn-start content rather than
     leaving it empty.
   - Extend the memory-restore clause to include `ctx.conv.undo_floor` alongside
     `ctx.conv.history`.
   - Add the fail-safe clause: a failing restore leaves the rows present, logs the failure, and
     still raises the persistence error (never falling back to deleting above the marker).
2. Leave the "Dedicated error type." bullet and the surrounding paragraphs unchanged.

### Method
- The bullet now opens with the append-only case exactly as before, then adds "On a turn that
  also compressed its history, the compression rewrite had replaced the session's rows, so
  compensation instead restores the turn-start rows — with their original `message_id` and
  `created_at`, at or below the marker — and resets the `/undo` boundary, rather than deleting
  above the marker; this returns the persisted session to its turn-start content instead of
  leaving it empty."
- The memory clause becomes "the in-memory `ctx.conv.history` and `ctx.conv.undo_floor` are
  restored element-wise to the snapshot captured at turn start."
- A final sentence adds the fail-safe behaviour.

### Details
- No concrete values (specific `message_id` numbers, counts, timestamps) are introduced, per
  AC-7.
- Stale-reference marks: none created; the update references existing symbols
  (`ctx.conv.history`, `ctx.conv.undo_floor`, `/undo`) already present in the document.

## Compatibility considerations

- The change is prose-only; no code, schema, or public API changes. It stays consistent with
  the append-only rule and the dedicated-error-type bullet it sits beside.

## Security considerations

- N/A: documentation-only change; no data or policy change.

## Rollback considerations

- Revert the bullet to its previous wording.

## Validation plan

- Run the docs checkers listed in the plan's validation table:
  `uv run python tools/check_docs_quality.py`,
  `uv run python tools/check_docs_structure.py`,
  `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain agent`.
- Confirm no findings and that no concrete values were copied (AC-7).

## Completion criteria

- The "Compensation" bullet states that after a turn that compressed, the rows return to their
  turn-start content (ids and `created_at` preserved) and the `/undo` boundary resets, and that
  a failing restore leaves rows untouched and still raises.
- All four docs checkers report no findings; no concrete values were copied.

## Out of Scope

- The repository capture/restore implementation (Row 01).
- The boundary compensation wiring (Row 02).
- Any other document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the compensation guarantee and run the docs checkers | Completed | 20261105-085500 | 20261105-090500 | Compensation bullet updated in-place: append-only path kept, compression-rewrite restore path and fail-safe added, no concrete ids/counts (AC-7) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261105-090500 | N/A: no tests for a doc change docs/ grep confirmed the state-model doc is the only non-generated doc stating the compensation rule; agent_13 is generated reference (no edit needed) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-090500 | check_docs_quality/structure/content_policy pass; check_docs_consistency --domain agent clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-090500 | this row Done by Step 1: this row IS the documentation update; no other docs in scope |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-006` (document the compensation guarantee), `AC-7` (no concrete values)
- **Source issue**: issues/20261031-180341_compresscomp001_compression-compensation-wipes-session.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-114113_compresscomp001_compression-compensation-wipes-session.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-224326
- **Related target files**: docs/23_agent/agent_04_01_state-and-persistence-state-model.md