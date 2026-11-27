## Goal

State the compensation statuses and the degraded-session behavior in the agent state-and-persistence documentation.

## Scope
**Release unit**: N/A: not part of a release unit

Requirement implemented: REQ-006 (documentation of the turn-persistence contract). Acceptance criteria: none directly; documents AC-1 through AC-4 behavior.

## Assumptions
- Documentation-only change; no source file is modified by this document.
- The clearing criteria for the degraded state are undecided (UNK-01 seam), so the text states that clearing is not defined yet rather than naming a command.

## Design decisions
- The statuses are described by name in prose, not by citing the enum symbol, per `skills/DESIGN.md` Docs content policy (implementation detail belongs to the canonical source).

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/23_agent/agent_04_01_state-and-persistence-state-model.md`

### Procedure
- In the Turn Persistence Boundary section, add the compensation statuses recorded on the error and on the turn result.
- Add the degraded-session behavior: a session whose compensation failed is marked, and the next turn is refused while it stays degraded.

### Method
- Extend the existing compensation bullet list (lines 56-60) with the status outcomes and the safe public error format.
- Add one short paragraph for the degraded state under the same section; keep the existing compensation semantics unchanged.

### Details
- The inserted-count rule is documented in `docs/23_agent/agent_09_01_data-layer-session-db.md`, not here.

## Compatibility considerations
- N/A: prose only; no generated block in this file.

## Security considerations
- N/A: no security-sensitive content.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Documentation gates per `rules/tool-gates.md`: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria
- The document states the three compensation statuses and the degraded-session refusal.

## Out of Scope
- The count contract and strict-mode scope (the data-layer document's row).
- The generated reference table (its own row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-115210 | compensation statuses + masked public error string + degraded-session refusal added |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` | Completed | — | 20261127-115210 | check_docs_quality/structure/content_policy/japanese passed; consistency --domain agent: 1 pre-existing warning in agent_14 (file not touched by this procedure) |

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
- **Requirement ID**: REQ-006 (documentation of the turn-persistence contract)
- **Source issue**: `issues/20261119-145308_cliplc010_strict-turn-persistence.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-211240_cliplc010_strict-turn-persistence.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-103439
- **Related target files**: `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`