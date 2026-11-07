## Goal

- docs/41_db/db_05 — retarget section 3 from the facade to store_protocols (AC-005, REQ-007)

## Scope
**Release unit**: N/A: outside the facade-cutover unit

- Phase 3 documentation only; it follows the Phase 1-2 unit and changes no code. Checker-config consolidation stays with compatrm004 (Plan Release unit row).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- Rename the heading rather than repurpose it: no inbound anchor links to this heading exist.

## Alternatives considered

- Leave the heading and only edit the helpers sentence: rejected — the heading itself names the deleted module.

## Implementation
### Target file
`docs/41_db/db_05_api_and_operations-protocol-and-backend.md`
### Procedure
1. Replace the heading at line 18 with:
   ```markdown
   ## 3. Storage Protocol Groups (`db.store_protocols`)
   ```
2. In line 20, replace "are exported from `db.store`" with "are defined in
   `db/store_protocols.py` and imported from there".
3. Leave the rest of section 3 (runtime_checkability, `VectorStore`/`DocumentStore`
   coverage paragraph, `SQLiteDocumentStore` defensive check) unchanged.
### Method
REQ-007 / AC-005. Section 3 (heading at line 18: "## 3. `db/store.py` Protocol
Groups") opens with line 20 claiming the embedding helpers "are exported from
`db.store`". The helpers (`get_embedding_dims`, `get_embedding_bytes`,
`validate_embedding_blob`) are defined in `scripts/db/store_protocols.py` (lines 27,
32, 37), which is already the named home at line 22 ("Method signatures:
`db/store_protocols.py`"). No other document links to this section's heading anchor,
so the heading rename is safe.
### Details
Heading and one phrase.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: sibling documents 01 (facade deleted), sibling documents 03 (helper ownership is stated post-cutover).
  - Blocks: none.

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Revert the documentation commit.

## Validation plan

- Command: `grep -n "db/store\.py\|exported from \`db.store\`" docs/41_db/db_05_api_and_operations-protocol-and-backend.md`
  Expected: no matches.
- Command: `python3 tools/check_docs_links.py`
  Expected: no broken links.

## Completion criteria

- section 3 attributes protocols and helpers to `db.store_protocols`. (AC-005, REQ-007)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Retarget db_05 section 3 to `db.store_protocols` — Plan Phase 3 | Pending | — | — | facade-cutover unit: suite green only with all unit documents landed |
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
- **Related target files**: `docs/41_db/db_05_api_and_operations-protocol-and-backend.md`
