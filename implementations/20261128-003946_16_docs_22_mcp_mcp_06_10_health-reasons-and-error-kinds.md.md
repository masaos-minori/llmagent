# Implementation Procedure — docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md

## Goal

Record the mdq readiness conditions as the documented mapping onto the closed capability vocabulary,
with no new vocabulary added (REQ-006, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-006 (the readiness conditions map onto the closed vocabulary). Acceptance criterion:
AC-4.

Lightweight fill: documentation-only row.

## Assumptions
- This doc owns the closed reason-code vocabulary that `scripts/shared/mcp_health_contract.py` (lines
  30-39) references, so the mapping is recorded here and nowhere else.
- No code is added: the readiness conditions are internal condition names, and each one reports through
  an existing code, so the closed set stays closed (plan default for UNK-02).
- The mapping is recorded as a mapping, not as a new producer rule: the doc already states that producers
  may emit only these codes.

## Design decisions
- The mapping is one subsection under `#### Degraded Reason-Code Vocabulary` (line 45), which is the
  section that owns the vocabulary.
- The readiness condition names are listed with the capability state and the reason code each one reports,
  so a reader can see that no name became a state or a code.

## Alternatives considered
- N/A: documentation-only change.

## Implementation
### Target file
`docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`

### Procedure
- Add a subsection after the vocabulary table (line 47) that lists the mdq readiness conditions and the
  existing capability state each one reports through: healthy reports the `ok` state, rebuild in progress
  and degraded report `degraded`, inconsistent reports `degraded`, failed reports `unavailable`, each with
  an existing reason code from the table above.
- State that the condition names are neither capability states nor reason codes and that both closed sets
  are unchanged.

### Method
- Prose only; no generated block in this file.

### Details
- The condition names come from `scripts/mcp_servers/mdq/health_check.py` (row 4), which publishes them as
  a `details` entry rather than as a capability reason.

## Compatibility considerations
- `uv run python tools/check_docs_content_policy.py --strict` must stay clean: the doc records the mapping
  and points to the code, it does not restate the constants.

## Security considerations
- N/A: documentation only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`
- `uv run python tools/check_docs_consistency.py --domain mcp`

## Completion criteria
- The doc records the readiness-condition mapping onto the existing codes and states that no code was
  added (AC-4); the docs checkers pass.

## Out of Scope
- The mdq server spec row, owned by row 15; the readiness implementation, owned by row 4.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the doc changes described in Procedure/Method/Details | Pending | — | — | Phase 4 |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (the readiness conditions map onto the closed capability vocabulary)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `docs/22_mcp/mcp_06_10_health-reasons-and-error-kinds.md`
