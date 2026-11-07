## Goal

- docs/41_db/db_04 — rewrite section 1a import rules (AC-005, REQ-007)

## Scope
**Release unit**: N/A: outside the facade-cutover unit

- Phase 3 documentation only; it follows the Phase 1-2 unit and changes no code. Checker-config consolidation stays with compatrm004 (Plan Release unit row).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- Keep the section 1a heading so the inbound anchor link from db_01 stays valid.

## Alternatives considered

- Delete the rules paragraph: rejected — section 1a is the canonical import-boundary reference linked from db_01.

## Implementation
### Target file
`docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`
### Procedure
1. Line 19: replace "the protocol groups and implementations in `db/store.py`" with
   "the protocol groups and implementations in `db/store_protocols.py` and
   `db/store_impl.py`".
2. Replace the paragraph at line 25 (the whole "The DB store layer is split ...
   intentional protocol/implementation development." paragraph) with:
   ```markdown
   The DB store layer is split into modules with clear import boundaries. `db/store_protocols.py` holds the protocol definitions for storage contracts and the embedding helpers (`get_embedding_dims`, `get_embedding_bytes`, `validate_embedding_blob`) — import contracts and helpers from here. `db/store_impl.py` provides the concrete SQLite implementations — import implementations from here. **Rule:** Contracts and helpers come from `db.store_protocols`; SQLite implementations come from `db.store_impl`. The `db/store.py` re-export facade was deleted (2026-11-07) and must not be reintroduced.
   ```
3. Line 29: replace with:
   ```markdown
   Add the `Protocol` to `db/store_protocols.py` and implement it in `db/store_impl.py`. Caller code imports contracts and helpers from `db.store_protocols` and implementations from `db.store_impl`.
   ```
4. Keep the `## 1a. DB Store Module Boundaries` heading (line 23) and the "### How to
   extend the DB store" heading (line 27) unchanged.
### Method
REQ-007 / AC-005. Three places assert the facade: line 19 names "the protocol groups
and implementations in `db/store.py`"; the section 1a rules paragraph (line 25) calls
it "the public API surface" and mandates "Callers must always import from `db.store`";
the "How to extend" paragraph (line 29) ends with "export it from `db/store.py`". The
heading `## 1a. DB Store Module Boundaries` and its anchor must stay so `db_01`'s link
resolves.
### Details
Two paragraph replacements plus one phrase in the purpose line.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: sibling documents 01 (the facade the current rules name is deleted).
  - Blocks: none (db_01's link sentence to this section's anchor stays valid — the
  heading is unchanged).

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Revert the documentation commit.

## Validation plan

- Command: `grep -n "db/store\.py\|db\.store\b" docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md | grep -v deleted`
  Expected: only the historical deletion sentence in the new paragraph.
- Command: `grep -n "public API surface\|must always import from" docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`
  Expected: no matches.
- Command: `python3 tools/check_docs_links.py`
  Expected: no broken links (the anchor `#1a-db-store-module-boundaries` from `db_01`
  still resolves).

## Completion criteria

- the section names the two real modules as the import surface. (AC-005, REQ-007)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the db_04 section 1a rules — Plan Phase 3 | Pending | — | — | facade-cutover unit: suite green only with all unit documents landed |
| 2 | Run this document's Validation plan commands | Pending | — | — | |
| 3 | Full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Pending | — | — | |

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
- **Requirement ID**: REQ-007 / AC-005
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-091221
- **Related target files**: `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md`
