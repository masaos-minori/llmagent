# Implementation Procedure: Rename the 15 fixture occurrences in `tests/rag/test_augment_integration.py`

## Goal

Rename every key occurrence in the augment-integration suite so HTTP-delegation integration
tests construct the renamed config field with identical logic (REQ-004, AC-6).

## Scope

- Fifteen occurrences on fourteen lines (verified 2026-10-27): the `_make_cfg` fixture kwarg at
  L42; `_make_cfg(rag_service_url="http://example.com/api")` call sites at L181, L212, L237,
  L268, L297, L326, L425, L454, L483, L502, L538; the token-pairing lines L352
  (`rag_service_url="http://example.com/api", rag_auth_token="secret-token"`), L377, and L401.
- No assertion or logic edits; `rag_auth_token` stays unchanged (Plan Assumptions).

## Assumptions

- Phase 3 row: land after the scripts renames (rows 01-07).
- L401 carries a `# type: ignore[arg-type]` comment; the rename must not disturb the comment
  text.

## Design decisions

- Mechanical rename only (Plan Design "mechanical propagation").

## Alternatives considered

- N/A: name-only rename per AC-6.

## Implementation
### Target file

`tests/rag/test_augment_integration.py`

### Procedure

1. Rename the fixture kwarg `rag_service_url=None` at L42 (verified) to the new spelling
   `rag_query_service_url` (new).
2. Rename every `rag_service_url="http://example.com/api"` call-site keyword at L181, L212,
   L237, L268, L297, L326, L352, L377, L401, L425, L454, L483, L502, L538 (verified) to the
   new spelling.

### Method

Mechanical keyword rename (a single search-replace of the exact keyword token is safe here:
no other identifier contains the old token; `rag_pipeline_service_url` does not occur in this
file).

### Details

- Verify after the edits: `grep -n "rag_service_url" tests/rag/test_augment_integration.py`
  returns nothing (AC-1 for this file).

## Compatibility considerations

- Test-only change; delegation-integration behavior identical.

## Security considerations

- N/A: token-pairing tests keep asserting `rag_auth_token` semantics unchanged.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_augment_integration.py` — green after Phase 2 rows land.
- `uv run pytest tests/` — full suite green; test edits are name-only (AC-6).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: zero old-spelling occurrences remain in this file.

## Out of Scope

- The near-identical `tests/rag/test_augment_refiner.py` rename (own procedure document) and
  all other rename rows.

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
- **Related target files**: tests/rag/test_augment_integration.py
