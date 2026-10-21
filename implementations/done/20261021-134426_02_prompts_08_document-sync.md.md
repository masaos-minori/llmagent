## Goal
Add an enumeration-generalization manual review step to the docs-cleanup procedure in `prompts/08_document-sync.md`, with an owner, so dropped-requirement risk from non-universal-word enumerations is covered manually when no mechanical check is adopted.

## Scope
- Modify only `prompts/08_document-sync.md`: append one manual review bullet to the cleanup procedure covering enumeration generalizations that omit a universal word (`each`/`every`).
- Do not change any other prompt, checker logic, or docs content.

## Assumptions
- The owner's decision is recorded before this executes (Plan REQ-001); this procedure documents the "manual step" branch so it can be applied once decided.
- Wording stays present-tense per the Current-Specification-Only Policy.

## Design decisions
- Add a single, clearly-scoped manual-review bullet to the cleanup procedure rather than restructuring the prompt.
- Attach an explicit owner so the accepted limit has accountability (REQ-004).

## Alternatives considered
- Building a mechanical check instead: out of scope for this row — that is the `tools/<existing-docs-check>.py` row (REQ-002/REQ-003).
- Inferring the owner's decision: rejected, REQ-001 makes the recorded decision a hard gate.

## Implementation
### Target file
`prompts/08_document-sync.md`

### Procedure
1. Confirm the owner's decision is recorded (REQ-001). If absent, stop and report; do not infer.
2. If the "manual step" branch is chosen, append a bullet to the cleanup procedure such as: "When a docs compression replaces an explicit list with a general statement, manually verify no concrete requirement was dropped — especially generalizations that omit a universal word (`each`/`every`)."
3. Attach an owner to the step (e.g. "reviewed by <owner-id>").

### Method
- Locate the docs-cleanup procedure section in `prompts/08_document-sync.md` (confirmed to currently have no such step).
- Append the new bullet at the end of the cleanup procedure, preserving the existing prompt structure.

### Details
- Verified at planning time: `prompts/08_document-sync.md` contains zero matches for enumeration/generalization/universal-word/compression/removed-list review steps. The gap is real and uncovered.
- This row is the manual-branch target only. If the owner chooses the mechanical branch, leave this file unchanged and record the accepted limit under `docs/00_governance/governance_04_documentation-checks.md`.

## Compatibility considerations
- Downstream plans reference `prompts/08_document-sync.md` as the cleanup contract; keeping the manual step accurate maintains a self-consistent contract.

## Security considerations
N/A: documentation-only update of a prompt; no code, secrets, or access changes.

## Rollback considerations
N/A: revert the commit that edits `prompts/08_document-sync.md`.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `prompts/08_document-sync.md` | Manual review | Manual review | Manual step present with owner; matches REQ-001 decision |

## Completion criteria
- The enumeration-generalization manual review step is present in `prompts/08_document-sync.md` with an owner.
- No other prompt or procedure text changed.

## Out of Scope
- Implementing a mechanical check (that is the `tools/<existing-docs-check>.py` row).
- Editing any `docs/` content.
- Restructuring the rest of the prompt.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the enumeration-generalization manual review step + owner to the cleanup procedure | Pending | — | — | Branch selected by owner decision (REQ-001) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Owner decision (mechanical / manual / record-limit) not available to the planning agent | N/A: pending external governance decision | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` — add the enumeration-generalization manual review step with owner to the cleanup procedure
- **Source issue**: `issues/20261021-100336_compressverify_detect-enumeration-generalization-without-universal-wording-after-docs-compression.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261021-124107_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-134426
- **Related target files**: `prompts/08_document-sync.md`
