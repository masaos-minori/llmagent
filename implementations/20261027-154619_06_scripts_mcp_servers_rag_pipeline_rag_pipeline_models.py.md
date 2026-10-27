# Implementation Procedure: Rename the anti-loop pin keyword in `build_rag_cfg_adapter()`

## Goal

Rename the `rag_service_url=""` pin keyword in `scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`
so the HTTP-loop guard binds to the renamed config field with identical behavior (REQ-002,
REQ-006).

## Scope

- One keyword rename at the verified site (L171: `rag_service_url="",  # prevent HTTP loop
  when augment() is called in-process`), comment preserved.
- No other adapter field changes.

## Assumptions

- Part of the single mass rename of this Plan; the keyword must match the renamed
  `RagConfigImpl` field from `scripts/rag/models_config.py` (sibling row) in the same
  implementation sequence — a keyword mismatch would be a `TypeError` at construction.
- Anti-loop semantics preserved: the MCP adapter still pins the value to `""` (REQ-006, AC-3).

## Design decisions

- Keyword-only rename keeps the existing anti-loop comment verbatim (Plan Design: mechanical
  propagation).

## Alternatives considered

- N/A: reader rename fixed by REQ-002.

## Implementation
### Target file

`scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py`

### Procedure

1. Rename the `rag_service_url=""` keyword in `build_rag_cfg_adapter()` (L171, verified) to
   the new spelling `rag_query_service_url` (new), keeping the empty-string value and the
   trailing comment.

### Method

Single keyword rename inside the `RagConfigImpl(...)` construction call.

### Details

- The anti-loop contract ("augment() called in the MCP process must not re-delegate") is
  asserted by `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`, whose rename
  row lands in the same sequence (AC-3).

## Compatibility considerations

- N/A: keyword argument to the renamed dataclass field; behavior identical.

## Security considerations

- N/A: guard behavior unchanged.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` — anti-loop
  assertions green after the test rename row lands.
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: no standalone old-spelling occurrence remains in this file; AC-3: adapter pin still
  yields `""`.

## Out of Scope

- `rag_pipeline_server.py` docstring rename (own procedure document) and the test rename row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: regression tests only |
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
- **Requirement ID**: REQ-002, REQ-006
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154619
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_models.py
