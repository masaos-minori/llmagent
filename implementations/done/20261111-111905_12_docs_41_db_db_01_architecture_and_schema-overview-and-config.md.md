## Goal

Add `mcp_dedup.sqlite` to the `db/` layer schema/dependency overview so the fifth store (a disposable cache outside the original four domains, owned by the shared MCP dispatcher) is named alongside the four canonical databases (`REQ-005`).

## Scope
**Release unit**: N/A: documentation alignment (Plan Implementation steps, Phase 5).

## Assumptions
- `mcp_dedup.sqlite` is a disposable cache outside the four domains (ADR-008, classified in seq 10); it is owned by the dispatcher (`scripts/shared/mcp_dedup.py` `DedupStore`) and is NOT managed by the `db/` layer's `SQLiteHelper` (which serves only `rag`/`session`/`workflow`, and the EventBus service owns `eventbus.sqlite`).
- Open (flag, do not fabricate): exact current wording at implementation time (UNK-04); re-read in Step 2.

## Design decisions
- **Extend, do not reframe.** The overview (L34) is framed around the four canonical databases. Add ONE sentence naming `mcp_dedup.sqlite` as a fifth, dispatcher-owned disposable cache outside those four — do not rewrite the four-DB framing or imply the `db/` layer manages it.
- **Consistent classification.** The one-line mention must match the fuller classification in ADR-008 (seq 10), `db_03_07` (seq 13), and `db_08` (seq 14): disposable cache, recovered by recreation, no backup.

## Alternatives considered
- **Give `mcp_dedup.sqlite` a full subsection here.** Rejected: this doc covers the `db/` layer's four stores and `DbConfig`/`SQLiteHelper`; `mcp_dedup.sqlite` is outside that layer. A single overview sentence plus the dedicated `db_03_07`/`db_08` treatment is the correct depth.

## Implementation
### Target file
`docs/41_db/db_01_architecture_and_schema-overview-and-config.md`

### Procedure
1. In section 2 "DB Layer Overall Structure", extend the paragraph at L34 (which lists the four DB files and their contents) by appending one sentence after the "separation avoids WAL contention." clause:

   > A fifth store, `mcp_dedup.sqlite` (the dispatcher's `tool_call_state` dedup ledger, `scripts/shared/mcp_dedup.py` `DedupStore`), lives outside these four domains: it is a disposable cache owned by the shared MCP dispatcher, recreated after loss or corruption, and not backed up or served by `SQLiteHelper`. Its schema/dependency overview and lifecycle are in `db_03_07` and `db_08`.

2. Do NOT alter the four-DB framing, the `DbConfig`/`SQLiteHelper` descriptions (L42, L48-50), or the import-boundaries note (L36). Keep the four databases as the `db/` layer's scope.

### Method
- Edit-only: append one sentence to the existing L34 paragraph. No new sections, no structural change.

### Details
- Keep the classification terse and identical to ADR-008/`db_03_07`/`db_08` (disposable cache, recreate, no backup).
- Do not introduce "system of record" wording anywhere in this doc (the plan removes that phrasing from `db_03_07`; keep this doc consistent).

## Compatibility considerations
- `check_docs_consistency.py --domain db` cross-checks the db domain; the one-line mention must match the `db_03_07`/`db_08`/ADR-008 classification.
- This doc does not manage `mcp_dedup.sqlite`; point readers to `db_03_07`/`db_08` for detail.

## Security considerations
- Low: documentation only. Naming the store and its disposable-cache status keeps its recovery behavior explicit.

## Rollback considerations
Revert the commit. No state or schema changes.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db`: pass; `mcp_dedup.sqlite` classified consistently as a disposable cache across the db domain.
- `uv run python tools/stale_detector.py` on this procedure.
- Full validation sequence.

## Completion criteria
- `mcp_dedup.sqlite` is named in the `db/` layer overview as a fifth, dispatcher-owned disposable cache outside the four domains.
- Classification matches ADR-008, `db_03_07`, `db_08`.
- `check_docs_consistency.py --domain db` passes.

## Out of Scope
- The fuller classification/lifecycle (seq 10 ADR-008, seq 13 `db_03_07`, seq 14 `db_08`).
- Implementing the fail-closed rejection (`dispatch.py`, seq 02) or out-of-band detection (`mcp_dedup.py`, seq 01).
- Config isolation (seq 03-06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `mcp_dedup.sqlite` to the `db/` layer overview (L34) | Pending | — | — | One sentence; disposable-cache classification |
| 2 | Add or update tests per Validation plan | Pending | — | — | none (doc) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` — `mcp_dedup.sqlite` added to the schema/dependency overview
- **Source issue**: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-111905
- **Related target files**: `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`

### Companion test files
- none (documentation change; verified by `check_docs_consistency.py --domain db`).
- Validation: db-domain consistency check passes.
