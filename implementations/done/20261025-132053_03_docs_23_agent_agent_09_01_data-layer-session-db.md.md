# Implementation Procedure — docs/23_agent/agent_09_01_data-layer-session-db.md

## Goal

Document the session persistence attribution semantics required by REQ-005
(document persistence binding semantics): the `SessionMessageRepository` used by
`AgentSession` always follows the facade's current `session_id`.

## Scope

- Update the `### Session Message Persistence` section (line 36) of
  `docs/23_agent/agent_09_01_data-layer-session-db.md`.

## Assumptions

- Invariant statement only — no code snippets, per `skills/DESIGN.md` docs content
  policy (implementation detail belongs to canonical sources).

## Design decisions

- State the invariant and the failure behavior only: "the message repository is
  (re)bound lazily to the current `session_id`; a `session_id` change invalidates the
  cached repository, so persistence never attributes writes to a superseded session".
- Note that `session_persister.py` and `DiagnosticStore` read the id per call and need
  no rebind.

## Alternatives considered

N/A: docs-only row.

## Implementation
### Target file
`docs/23_agent/agent_09_01_data-layer-session-db.md`

### Procedure
Add 3-5 sentences to `### Session Message Persistence` describing the binding
invariant above.

### Method
Insert after the existing persistence description; keep the section's current bullets
intact.

### Details
English only (enforced by `check_docs_japanese.py`); do not touch Keywords/Front
Matter unless a checker demands it.

## Compatibility considerations

N/A: prose-only change; no claim elsewhere in the doc contradicts the invariant.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/23_agent/agent_09_01_data-layer-session-db.md`
- `uv run python tools/check_docs_content_policy.py` (no implementation-detail prose)
- `uv run python tools/check_docs_consistency.py --domain agent`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

The section states the current-`session_id` binding invariant and per-call-id
inheritance without duplicating code (AC-006), and all docs checkers pass.

## Out of Scope

Any other section of this document; the state-model wording (procedure 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update `### Session Message Persistence` with the binding invariant | Completed | 20261025-174142 | 20261025-174142 |  |
| 2 | Run the docs checkers listed in Validation plan | Completed | 20261025-174142 | 20261025-174142 |  |

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
- **Requirement ID**: REQ-005 (documentation of persistence binding semantics)
- **Source issue**: `issues/done/20261025-115501_sess001_repo-staleness-after-restore.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-121815_sess001_repo-staleness-after-restore.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-132053
- **Related target files**: docs/23_agent/agent_09_01_data-layer-session-db.md