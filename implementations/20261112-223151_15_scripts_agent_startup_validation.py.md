## Goal

Remove the `RAG identity-unverified:` prefix from the two startup consistency warnings so
the warning category no longer names the removed corpus identity (`REQ-009`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Both warnings live in `scripts/agent/startup_validation.py` around lines 246-261: one for
  the 30s timeout path and one for the exception path.
- Severity routing (`add_warning("rag_consistency", ...)`) and continue-startup behavior are
  unchanged; only the message text changes.

## Design decisions
- Strip the leading `RAG identity-unverified: ` token from both warning messages; keep the
  rest of each message and the surrounding error handling.

## Alternatives considered
N/A: removal is the decided Option B; keeping the prefix would name a removed concept.

## Implementation
### Target file
`scripts/agent/startup_validation.py`
### Procedure
- Change `"RAG identity-unverified: consistency check timed out after 30s; startup continues
  with the corpus identity unverified."` to drop the prefix (~line 249).
- Change `"RAG identity-unverified: " f"{category} ({type(exc).__name__}): {exc}; startup
  continues with the corpus identity unverified."` to drop the prefix (~line 259).
### Method
Two message-text edits; keep severity, category, and timeout text intact.
### Details
- This region overlaps `rmcompat001` (sequencing dependency): that Plan edits the same two
  warnings' prefix. Apply this edit to a re-read of the file.

## Compatibility considerations
N/A: warning-message text change only; the `rag_consistency` warning category is retained.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "identity-unverified" scripts tests docs` returns nothing.
- `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_startup.py tests/agent/test_startup_severity_classification.py` passes.

## Completion criteria
Neither warning carries the `identity-unverified` prefix; severity and continue-startup
behavior are unchanged.

### Companion test files
- `tests/agent/test_startup_validation.py`
  - Procedure: drop the `identity-unverified` assertions (lines 245-255, 281); keep every
    other assertion.
  - Validation: `uv run pytest tests/agent/test_startup_validation.py` passes.

## Out of Scope
The other two startup test files that assert the same prefix (standalone docs 34, 35).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covers companion `test_startup_validation.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-009`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `scripts/agent/startup_validation.py`, `tests/agent/test_startup_validation.py`
