# Implementation Procedure: Rename the `RagConfigImpl` dataclass field

## Goal

Rename the dataclass declaration of the query-path service-URL field in
`scripts/rag/models_config.py` to the new spelling (REQ-001).

## Scope

- One attribute rename at the verified declaration (L26: `rag_service_url: str`).
- No other field, default, or annotation changes.

## Assumptions

- Part of the single mass rename of this Plan (declaration rows land together with reader
  rows before tests run).
- `RagConfigImpl` is constructed only via keyword arguments in `resolve_rag_config` and test
  fixtures; all construction sites are rename targets in sibling procedure documents.

## Design decisions

- Field name follows the config-key name exactly (`resolve_rag_config` builds the dataclass
  from filtered config keys by name), so the dataclass field must carry the identical new
  spelling `rag_query_service_url` (new).

## Alternatives considered

- Keeping the old field name and mapping key→field in the resolver — rejected: re-introduces
  exactly the name ambiguity the Plan removes.

## Implementation
### Target file

`scripts/rag/models_config.py`

### Procedure

1. Rename the dataclass attribute `rag_service_url: str` (L26, verified) to the new spelling.

### Method

Single identifier rename; type annotation `str` unchanged.

### Details

- mypy validates the dataclass/protocol/consumer rename across packages (Plan Tests);
  runtime breakage surfaces immediately because construction uses keyword arguments.

## Compatibility considerations

- N/A: internal dataclass; callers are the rename rows of this Plan.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run mypy --no-namespace-packages scripts/` — protocol/dataclass rename type-checks.
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — no
  matches after all rows land (AC-1).
- `uv run pytest tests/rag/test_config_resolution.py` — green after Phase 3 rows.

## Completion criteria

- AC-1: no standalone `rag_service_url` occurrence remains in this file.

## Out of Scope

- `RagConfig` protocol rename (`scripts/shared/types.py`, own procedure document) and all
  reader/test/doc renames.

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
- **Related target files**: scripts/rag/models_config.py
