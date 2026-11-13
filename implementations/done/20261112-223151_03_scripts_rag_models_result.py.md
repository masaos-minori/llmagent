## Goal

Remove the `corpus_generation` field from the RAG result DTO so the diagnostics model no
longer carries a corpus generation (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Verified against current source: no `SearchDiagnostics(...)` construction anywhere passes
  `corpus_generation` (dataclass field at `scripts/rag/models_result.py` ~lines 90-91 has no
  writer); the only same-named writer is the diagnostics **dict** key appended in
  `pipeline.py` `get_diagnostics()` (sibling document, seq 02), and the MCP server reads
  that dict key, not the DTO field. Deleting both removes all uses.

## Design decisions
- Delete the dataclass field and its comment; the frozen dataclass keeps its other fields.

## Alternatives considered
N/A: removal is the decided Option B; a nullable default would keep dead state.

## Implementation
### Target file
`scripts/rag/models_result.py`
### Procedure
- Delete the `corpus_generation: int | None = None` field and its comment from
  `SearchDiagnostics`.
### Method
Single field deletion in a frozen dataclass; confirm no other module references the name.
### Details
- Leave the rest of the DTO untouched; the field was additive.

## Compatibility considerations
N/A: additive wire field removal recorded in the ADR; no alias kept.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_generation" scripts/rag/models_result.py` returns nothing.
  (Scoped to this file: `scripts/rag/identity_gate.py` docstring legitimately still mentions
  the name until the release-unit documents remove it in phase 6.)
- `uv run pytest tests/rag` passes. Verified: no test under `tests/rag` asserts the
  `corpus_generation` key or the DTO field.

## Completion criteria
`SearchDiagnostics` has no `corpus_generation` field; no remaining reference exists.

## Out of Scope
The pipeline diagnostics append (`REQ-002`, seq 02) and the MCP wire field (`REQ-003`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-095937 | 20261113-100523 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113-100523 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113-100523 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113-100523 |  |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `scripts/rag/models_result.py`