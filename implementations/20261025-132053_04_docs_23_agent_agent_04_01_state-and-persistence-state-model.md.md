# Implementation Procedure — docs/23_agent/agent_04_01_state-and-persistence-state-model.md

## Goal

Document the state-model consequence required by REQ-005 (state model documentation):
`session_id` is mutable on restore, and persistence attribution follows the current
value.

## Scope

- Update the `### Session Persistence Design Intent` section (line 32) of
  `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`.

## Assumptions

- Invariant/prose update only; the doc's `Key Constraints` section stays unless a
  checker requires a cross-reference.

## Design decisions

- State that `/session load` (`restore_session()`) reassigns the live session's
  `session_id` and that the message repository rebuilds to the new id on next use, so
  post-restore turns are attributed to the restored session; skipped-save counters
  belong to the live repository instance.

## Alternatives considered

N/A: docs-only row.

## Implementation
### Target file
`docs/23_agent/agent_04_01_state-and-persistence-state-model.md`

### Procedure
Add 2-4 sentences to `### Session Persistence Design Intent` stating the
`session_id` mutability and attribution semantics above.

### Method
Insert after the existing design-intent paragraph; do not restate repository method
signatures.

### Details
English only (enforced by `check_docs_japanese.py`).

## Compatibility considerations

N/A: prose-only change; complements procedure 03's data-layer wording.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_04_01_state-and-persistence-state-model.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

The state-model doc states `session_id` mutability across restore and its persistence
attribution effect (AC-006), and all docs checkers pass.

## Out of Scope

Other sections of this document; the data-layer wording (procedure 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update `### Session Persistence Design Intent` with the mutability/attribution semantics | Pending | — | — | |
| 2 | Run the docs checkers listed in Validation plan | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (documentation of the state model change)
- **Source issue**: `issues/done/20261025-115501_sess001_repo-staleness-after-restore.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-121815_sess001_repo-staleness-after-restore.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-132053
- **Related target files**: docs/23_agent/agent_04_01_state-and-persistence-state-model.md
