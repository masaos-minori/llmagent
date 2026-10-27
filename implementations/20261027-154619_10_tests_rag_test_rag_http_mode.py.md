# Implementation Procedure: Rename the HTTP-mode fixture helper in `tests/rag/test_rag_http_mode.py`

## Goal

Rename the key spellings in the `_make_pipeline` fixture helper so HTTP-mode delegation
regression runs against the renamed field with identical logic (REQ-004, AC-6).

## Scope

- Two lines / three token occurrences (verified 2026-10-27): the helper signature parameter
  `rag_service_url: str = "http://rag.local"` at L20 and the assignment
  `cfg.rag_service_url = rag_service_url` at L23.
- No assertion or logic edits.

## Assumptions

- Phase 3 row: land after the scripts renames (rows 01-07); `cfg` is a MagicMock-style config
  consumed by `RagPipeline`, so the Plan's MagicMock risk applies here — the rename must match
  the renamed protocol attribute for the delegation check in `pipeline.py` to read it.
- The Plan Validation node IDs ("after rename" test names) refer to these files' existing
  HTTP-mode tests after the rename; no new tests are added here (Plan Scope adds only one new
  test, in `test_config_resolution.py`).

## Design decisions

- The helper parameter is renamed alongside the attribute so local naming stays consistent
  (single-token substitution throughout the helper).

## Alternatives considered

- Keeping the local helper parameter name unchanged — rejected: leaves a standalone
  old-spelling token in `tests/`, violating AC-1.

## Implementation
### Target file

`tests/rag/test_rag_http_mode.py`

### Procedure

1. Rename the helper parameter `rag_service_url` (L20, verified) to the new spelling
   `rag_query_service_url` (new), default `"http://rag.local"` unchanged.
2. Rename both tokens on L23 (verified): `cfg.rag_service_url = rag_service_url` to the new
   spelling on both sides.
3. Rename every call-site keyword use of the helper parameter in the file if present (grep
   the file after steps 1-2 to confirm zero standalone occurrences remain).

### Method

Mechanical token rename inside one helper plus its call sites; defaults unchanged.

### Details

- N/A beyond the verified occurrences.

## Compatibility considerations

- Test-only change; HTTP-mode behavior identical (AC-3).

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_rag_http_mode.py` — green after Phase 2 rows land (HTTP-mode
  delegation regression).
- `uv run pytest tests/` — full suite green; test edits are name-only (AC-6).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: zero standalone old-spelling tokens remain in this file; AC-3: HTTP-mode delegation
  regression passes with the renamed key.

## Out of Scope

- `pipeline.py` delegation-check rename (own procedure document) and result-kind test renames.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 3 row; land after Phase 2 rows 01-07 |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: rename only |
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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261027-071953_rag003_rag-url-key-ambiguity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110727_rag003_rag-url-key-ambiguity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-154619
- **Related target files**: tests/rag/test_rag_http_mode.py
