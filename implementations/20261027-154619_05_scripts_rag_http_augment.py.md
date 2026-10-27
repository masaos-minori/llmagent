# Implementation Procedure: Rename the trigger-key reference in `HttpAugment` docstrings

## Goal

Rename the key named in the `HttpAugment` docstring in `scripts/rag/http_augment.py` so the
delegation trigger is documented under the new spelling (REQ-002).

## Scope

- One docstring occurrence (verified at L73: "When rag_service_url is configured, delegates
  augment to an external ..."). Grep across the file found exactly one standalone old-spelling
  occurrence (2026-10-27 verification); the Plan row's "docstrings" plural is satisfied by
  this single reference plus its surrounding module/class documentation context.
- No executable code in this file references the key (verified by the same grep) — the
  delegation decision lives in `RagPipeline`.

## Assumptions

- Part of the single mass rename of this Plan (documentation-only row within scripts/).

## Design decisions

- N/A: docstring token substitution.

## Alternatives considered

- N/A: no design space.

## Implementation
### Target file

`scripts/rag/http_augment.py`

### Procedure

1. Rename the key named in the L73 docstring to the new spelling `rag_query_service_url` (new).

### Method

Single docstring token rename.

### Details

- N/A.

## Compatibility considerations

- N/A: docstring only.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_augment_integration.py` — suite green after its rename row
  lands (regression only).
- `grep -rn "rag_service_url" scripts/ tests/ | grep -v "rag_pipeline_service_url"` — clean
  after all rows land (AC-1).

## Completion criteria

- AC-1: no standalone old-spelling occurrence remains in this file.

## Out of Scope

- `RagPipeline` delegation-check rename (own procedure document) and test fixture renames.

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
- **Related target files**: scripts/rag/http_augment.py
