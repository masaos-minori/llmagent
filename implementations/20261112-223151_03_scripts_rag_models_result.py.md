## Goal

Remove the `corpus_generation` field from the RAG result DTO so the diagnostics model no
longer carries a corpus generation (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `SearchDiagnostics.corpus_generation` is written only by `pipeline.py` (sibling document,
  seq 02); deleting the field there removes the only writer.
- No serializer or caller reads this field outside the diagnostics dict already covered by
  seq 02.

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
- `rg -n "corpus_generation" scripts/rag` returns nothing.
- `uv run pytest tests/rag` passes.

## Completion criteria
`SearchDiagnostics` has no `corpus_generation` field; no remaining reference exists.

## Out of Scope
The pipeline diagnostics append (`REQ-002`, seq 02) and the MCP wire field (`REQ-003`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `scripts/rag/models_result.py`
