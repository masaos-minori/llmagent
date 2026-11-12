## Goal

Remove the `corpus_identity` wire field from the rag-pipeline MCP response model so the
model no longer declares a corpus identity (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The field lives on `RagRunResponse` (`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`,
  seq 04), which `RagDebugResponse` subclasses; deleting it from the parent removes it from
  both.
- No other module reads this field (`UNK-03`): the server sets it only via the deleted
  `_identity_payload()`.

## Design decisions
- Delete the `corpus_identity: dict[str, Any] = Field(...)` attribute from `RagRunResponse`
  and its description line; the frozen dataclass keeps its other fields.

## Alternatives considered
N/A: removal is the decided Option B; a present-but-empty field would keep dead wire state.

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`
### Procedure
- Delete the `corpus_identity: dict[str, Any] = Field(default_factory=dict, ...)` attribute
  and its description from `RagRunResponse` (`rag_pipeline_models.py`, around line 259).
### Method
Single attribute deletion in a frozen dataclass; confirm no other module references the name.
### Details
- Leave the rest of the DTO untouched; the field was additive and documented as such.

## Compatibility considerations
N/A: additive wire field removal recorded in the ADR; no alias kept.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_identity|_identity_payload" scripts/mcp_servers` returns nothing.
- `uv run pytest tests/mcp_servers/rag_pipeline` passes.

## Completion criteria
`RagRunResponse` has no `corpus_identity` field; no remaining reference exists.

## Out of Scope
The server's `_identity_payload()` and its call sites (`REQ-003`, seq 04).

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
- **Requirement ID**: `REQ-003`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`
