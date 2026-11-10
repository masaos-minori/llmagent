## Goal
- Remove the wrong pointer to `eventbus_08_reference_api.md` for the `/admin/topics/authorization` contract (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the ADMIN row of the token table (line 46).
- Not in scope: the rest of the document.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (document 09) first, then Phase 2 (documents 02, 03, 04, 05, 08, then 01 and 10 for the Phase 2 share), then Phase 3 (documents 06, 07, then 01, 10, 15 for the Phase 3 share), then Phase 4 (documents 11-14). Phase 4.

## Assumptions
- The row already states the contract inline (optimistic concurrency, 409 `generation_conflict`, `previous_generation`/`new_generation`, optional `ttl_seconds`); `eventbus_08` holds only a symbol row, and the TTL bound is in `eventbus_07_configuration-and-operations.md`. Falsifiable by reading both.

## Design decisions
- Replace "see `eventbus_08_reference_api.md`" with a pointer to `eventbus_07_configuration-and-operations.md` for the TTL bound (`authz_max_ttl_seconds`), or drop the pointer.

## Alternatives considered
N/A: one-clause correction.

## Implementation
### Target file
`docs/24_eventbus/eventbus_02_api-reference-index.md`

### Procedure
1. In the ADMIN row, replace `; see `eventbus_08_reference_api.md`` with `; the TTL bound is described in `eventbus_07_configuration-and-operations.md``.
2. Keep the `related:` front matter consistent (add `eventbus_07_configuration-and-operations.md` only if the structure checker requires it).

### Method
- Edit in place.

### Details
- Do not copy the contract into another document (docs content policy).

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_consistency.py --domain eventbus`, `uv run python tools/check_docs_content_policy.py --strict`.

## Completion criteria
- The ADMIN row no longer points to `eventbus_08`; the checkers pass.

## Out of Scope
- Other rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `docs/24_eventbus/eventbus_02_api-reference-index.md` as described in Procedure | Completed | 20261110-113335 | 20261110-113335 |  |
| 2 | Run the documentation checkers listed in Validation plan | Completed | 20261110-113335 | 20261110-113335 |  |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20261109-112504_adrrev001_eventbus-route-handlers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-090758_adrrev001_eventbus-route-handlers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-100805
- **Related target files**: `docs/24_eventbus/eventbus_02_api-reference-index.md`