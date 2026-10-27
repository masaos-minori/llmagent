# Implementation Procedure: Rename the key references in the rag_pipeline server module docstring

## Goal

Rename the key named in the module docstring of
`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` so the server's activation
condition is documented under the new spelling (REQ-002).

## Scope

- Two docstring occurrences (verified at L7-8: "Replaces the in-process augment() call when
  rag_service_url is configured in rag.toml (rag_service_url).").
- No executable code in this file references the key (grep verified: exactly two standalone
  occurrences, both docstring).

## Assumptions

- Part of the single mass rename of this Plan (documentation-only row within scripts/).

## Design decisions

- N/A: docstring token substitution.

## Alternatives considered

- N/A: no design space.

## Implementation
### Target file

`scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`

### Procedure

1. Rename both key occurrences in the module docstring (L7, L8, verified) to the new spelling
   `rag_query_service_url` (new).

### Method

Two docstring token renames.

### Details

- The `rag.toml` parenthetical at L8 documents the config file where the key would appear;
  it stays, only the key name changes.

## Compatibility considerations

- N/A: docstring only.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/rag_pipeline/` — suite green (regression only).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: no standalone old-spelling occurrence remains in this file.

## Out of Scope

- The `build_rag_cfg_adapter()` pin rename (own procedure document).

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154619
- **Related target files**: scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py
