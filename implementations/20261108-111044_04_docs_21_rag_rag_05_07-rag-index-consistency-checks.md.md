## Goal
Correct the statement that the augment gate refuses fallback while the identity is unverified, and state identity sources (REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit
Edits the failed-or-timed-out-check bullet of `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` and adds the identity-source statement.

## Assumptions
- `_identity_gate()` proceeds when either identity is missing; `rag_01_system_overview.md` already states this.

## Design decisions
- Align the sentence with the code and rag_01 wording.

## Alternatives considered
N/A: wording correction

## Implementation
### Target file
`docs/21_rag/rag_05_07-rag-index-consistency-checks.md`

### Procedure
1. Replace "the augment gate then refuses fallback while the identity is unverified" with the approved semantics: the gate rejects or degrades only when both identities are present and unequal; otherwise it proceeds and records the unverifiable state.
2. Add one sentence on identity sources, per-request freshness, and the self-reported remote value.

### Method
Documentation edit.

### Details
- Do not alter the Fatal findings list.

## Compatibility considerations
Documentation only.

## Security considerations
N/A: documentation-only change; no secret, permission, or input-handling behavior changes

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_japanese.py`: no findings
- `uv run python tools/check_docs_consistency.py --domain rag`: no findings
- `uv run pytest tests/rag/test_identity_gate.py`: pass

## Completion criteria
- No sentence in the file says an unverifiable identity refuses fallback.

## Out of Scope
- Startup check behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document as described in Implementation > Procedure | Pending | — | — |  |
| 2 | Run the documentation checkers named in the Validation plan | Pending | — | — |  |

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
- **Requirement ID**: `REQ-002`, `REQ-003` (identity semantics; identity sources)
- **Source issue**: issues/20261107-050701_adrrag001_rag-fallback-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-091446_adrrag001_rag-fallback-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-111044
- **Related target files**: `docs/21_rag/rag_05_07-rag-index-consistency-checks.md`
