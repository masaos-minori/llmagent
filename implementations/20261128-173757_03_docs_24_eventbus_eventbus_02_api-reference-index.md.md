## Goal
- State the check order and the metadata-only 422 of `POST /admin/topics/authorization` in the ADMIN row of the roles table (`REQ-005` documentation sync).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the ADMIN row of the roles table in `docs/24_eventbus/eventbus_02_api-reference-index.md`.

## Assumptions
- The code change of procedure 01 defines the behavior being documented: 401/403 first, then body validation and TTL validation (422), then the generation conflict (409); a body without `consumer_authorization` is 422.
- The row currently describes `expected_generation`, HTTP 409 `generation_conflict`, the response fields, optional `ttl_seconds`, and points to `eventbus_07_configuration-and-operations.md` for the TTL bound (checked at the Plan's evidence revision).
- This file is hand-written (not a generated block); no generator rewrites it.

## Design decisions
- Extend the existing ADMIN row in place; do not add a new section.

## Alternatives considered
N/A: single-row wording change.

## Implementation
### Target file
`docs/24_eventbus/eventbus_02_api-reference-index.md`

### Procedure
1. In the ADMIN row, state that `consumer_authorization` is required (a body without it returns HTTP 422), that an invalid `ttl_seconds` returns HTTP 422 before the `expected_generation` comparison, and that HTTP 409 `generation_conflict` is returned only for a structurally valid request with a stale `expected_generation`.

### Method
- Keep the row to one table row, English, using normative terms; keep the existing pointer to `eventbus_07_configuration-and-operations.md`.

### Details
- Do not change any other row or section.

## Compatibility considerations
N/A: documentation wording only.

## Security considerations
N/A: no credential or trust-boundary content.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/run_validation_gates.py` (selects the documentation checkers for a `docs/` change per `rules/tool-gates.md`).
- `uv run python tools/generate_reference_table.py --check` and `uv run python tools/check_adr_structure.py`.

## Completion criteria
- The ADMIN row states the check order and the metadata-only 422 consistently with the shipped code (`REQ-005`), and the checkers above report no findings.

## Out of Scope
- ADR-013 wording (procedure 04); any code change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the ADMIN row of `docs/24_eventbus/eventbus_02_api-reference-index.md` | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (API reference states the check order and the metadata-only rejection)
- **Source issue**: issues/20261125-103307_adrr001_admin-ttl-precedence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-172318_adrr001_admin-ttl-precedence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-173757
- **Related target files**: `docs/24_eventbus/eventbus_02_api-reference-index.md`
