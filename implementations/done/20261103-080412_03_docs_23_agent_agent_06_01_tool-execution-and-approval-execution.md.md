## Goal
Document the new duplicate-call-id preparation check and its reporting behavior in the tool
execution and approval doc (REQ-001, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md` row (seq 03) of
`plans/20261101-142610_dupcallid001_duplicate-call-id-misexecution.md`. Executed last, after the
seq 01/02 code changes and the seq 06 test are in place, so the doc describes shipped behavior.

## Assumptions
- The overlap with `plans/20261101-144325_inflightcancel001_cancelled-call-reported-unexecuted.md`
  on this file is compatible: that Plan edits the synthesized-row semantics section, this change
  edits the preparation checklist and scheduling invariant (Plan A5 judgment).

## Design decisions
- Intent-only documentation: add the uniqueness check to the preparation checklist (doc:59-64) and
  one sentence to the scheduling invariant (doc:49) about the scheduler guard; no code snippets.

## Alternatives considered
- A new dedicated section for duplicate ids: rejected — the checklist and invariant already host
  per-call rules; a uniqueness bullet fits the existing structure.

## Implementation
### Target file
`docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`

### Procedure
1. Add a uniqueness item to the preparation checklist: duplicated call ids in one round are
   rejected at preparation with failure kind `duplicate_id` (new), every occurrence, before the
   approval gate.
2. Extend the scheduling invariant sentence (call_id keying, doc:49) with the defense-in-depth
   note: `build_execution_groups` raises on duplicate ids.

### Method
Two targeted edits to existing lists/sentences.

### Details
- Match the checklist's existing phrasing style (one rule per numbered item, failure kind named).
- Keep the failure-kind list consistent with `tool_preparation.py` docstrings after seq 01 lands.
- Verification 20261103: the checklist is the five-item bullet list in the "Argument Validation"
  section (existence, JSON parse, registry resolution, schema validation, metadata construction);
  the new uniqueness rule is its sixth bullet. The invariant sentence is the
  `build_execution_groups()`/`call_id`-key paragraph in the scheduling section (doc:49).

## Compatibility considerations
- `docs/00_index.md` mapping already lists this doc for agent tool-execution tasks; no index
  change needed.

## Security considerations
- N/A for a documentation change; it records the safety behavior.

## Rollback considerations
- Revert the doc edits; no dependency on code ordering.

## Validation plan
1. `uv run python tools/stale_detector.py` plus the doc checker sequence per `rules/toolchain.md`
   (docs edited under `docs/` require the routing checkers).

## Completion criteria
- The checklist names the `duplicate_id` (new) rejection and the scheduler guard, matching shipped
  code.

## Out of Scope
- Any code or test change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the two targeted doc edits (Procedure 1-2) | Completed | 20261103-104234 | 20261103-104234 | Sixth preparation-checklist bullet added (uniqueness post-pass, `duplicate_id`, per-occurrence tool rows); scheduling invariant sentence extended with the `DuplicateToolCallIdError` guard (doc:49). |
| 2 | Run the doc checker sequence (`rules/toolchain.md`) | Completed | 20261103-104234 | 20261103-104234 | check_docs_consistency --domain agent: no issues; stale_detector: not stale. |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20261101-073525_dupcallid001_duplicate-call-id-misexecution.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-142610_dupcallid001_duplicate-call-id-misexecution.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-080412
- **Related target files**: `docs/23_agent/agent_06_01_tool-execution-and-approval-execution.md`