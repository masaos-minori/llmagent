# Implementation Procedure: Rename the `RagConfig` protocol attribute

## Goal

Rename the cross-package protocol attribute consumed by all RAG query-path readers in
`scripts/shared/types.py` to the new spelling (REQ-001).

## Scope

- One protocol attribute rename at the verified declaration (L97: `rag_service_url: str`).
- No other protocol member changes.

## Assumptions

- Part of the single mass rename of this Plan; `RagConfig` is the protocol contract consumed
  across packages (`rag/`, `mcp_servers/`, `agent/`), so mypy is the primary cross-check.
- Structural typing means any class satisfying the old protocol (including test stubs such as
  the local dataclass in `tests/rag/test_rag_pipeline_stage.py`) must carry the new name —
  those files are sibling rename rows.

## Design decisions

- Protocol rename mirrors the dataclass rename exactly so the structural conformance edge
  stays one-to-one (Plan Design: mechanical propagation verified by mypy + grep).

## Alternatives considered

- N/A: identifier rename; no design space beyond the Plan's naming decision (query key only).

## Implementation
### Target file

`scripts/shared/types.py`

### Procedure

1. Rename the `RagConfig` protocol attribute `rag_service_url: str` (L97, verified) to the
   new spelling `rag_query_service_url` (new).

### Method

Single identifier rename; annotation unchanged.

### Details

- The shared→rag direction of this contract is unchanged; the import-linter contract is not
  affected by an attribute rename.

## Compatibility considerations

- N/A: internal protocol; consumers are this Plan's reader rename rows.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run mypy --no-namespace-packages scripts/` — protocol rename type-checks across
  packages (Plan Tests).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: no standalone `rag_service_url` occurrence remains in this file; mypy clean.

## Out of Scope

- All reader renames (`pipeline.py`, `http_augment.py`, the rag_pipeline MCP files — own
  procedure documents) and the dataclass rename.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: no test change from this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154619
- **Related target files**: scripts/shared/types.py
