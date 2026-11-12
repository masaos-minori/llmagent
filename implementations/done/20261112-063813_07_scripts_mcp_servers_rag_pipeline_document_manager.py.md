## Goal

Route `DocumentManager.delete_document()` through the shared `delete_document_chain()` helper and add a test that fails if the MCP path stops using it (`REQ-004`, `REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `self._make_helper().open(write_mode=True)` yields a `SQLiteHelper` matching the helper's `db` parameter type (`scripts/rag/ingestion/document_manager.py` line 18 signature).
- The helper issues the two `DELETE` statements in the same order (`chunks_vec` before `documents`), so ADR-005 INV-02/INV-05 hold unchanged.
- An `mcp_servers → rag` import is allowed and verified 2026-11-12: the `.importlinter` contract list (`shared-is-leaf`, `db-only-uses-shared`, `rag-no-agent-or-mcp_servers`, `mcp_servers-no-agent`, `eventbus-is-isolated`, `agent-mcp-config-models`) forbids no such edge, and `rag_pipeline_server.py` / `rag_pipeline_service.py` already import `rag.*` (`UNK-03` resolved; `lint-imports` rerun in validation).
- Gate resolved 2026-11-12: the identity-gate removal landed (`b217f999b`); the frozen rmcompat001 Plan (`plans/20261112-115458_rmcompat001_rag-delegation-leftovers.md`) lists `rag_05_07` as a reference file only, not a target; `tools/plan_dependency_order.py` reports this Plan Ready with no gate.

## Design decisions
- Replace the two inline `db.execute("DELETE ...")` calls with one `delete_document_chain(db, doc_id)` call inside the existing `with ... as db:` block; keep the `SELECT doc_id` lookup and the final `db.commit()` untouched.
- Add the module-level import `from rag.ingestion.document_manager import delete_document_chain` (new).

## Alternatives considered
- Moving `delete_document_chain()` to the `db` layer: wider blast radius across ingestion and Agent callers; rejected unless `lint-imports` fails or the maintainer objects (`UNK-03` fallback via plan amendment).

## Implementation
### Target file
`scripts/mcp_servers/rag_pipeline/document_manager.py`

### Procedure
1. Add the `delete_document_chain` import at the top of the module.
2. In `delete_document()`, replace the two inline `DELETE` statements with a single `delete_document_chain(db, doc_id)` call.
3. Leave the `SELECT doc_id` lookup, the `with self._make_helper().open(write_mode=True) as db:` context, and the trailing `db.commit()` as-is.
4. Write the companion test first and confirm it fails before the replacement.
5. Update the module docstring `Dependency direction` line to include `rag.ingestion.document_manager`.

### Method
`delete_document` spans lines 66-81: the `if row is None: return False` guard, then `db.execute("DELETE FROM chunks_vec WHERE chunk_id IN (...)")` followed by `db.execute("DELETE FROM documents WHERE doc_id = ?")`, then `db.commit()`. Substitute the two `execute` calls with one helper call passing the same `db` handle and the resolved `doc_id`.

### Details
- Helper signature (new reference): `delete_document_chain(db: SQLiteHelper, doc_id: int) -> None` — `scripts/rag/ingestion/document_manager.py` line 18.
- Deletion order is unchanged; the `chunks_vec_ad` orphan backstop triggers identically, so no orphan vectors are introduced.
- The caller `rag_pipeline_service.py` needs no change.

## Compatibility considerations
- Behavior is identical (same two statements, same order, same commit); no persisted schema, public API, or shared constant changes.

## Security considerations
- Delete effect is unchanged; the orphan-vector backstop behaves as before.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline tests/rag/ingestion/test_delete_chain.py -v` — pass.
- `uv run python tools/check_mock_patch_targets.py` — pass (patch `delete_document_chain` where `DocumentManager` imports it).
- `uv run ruff format` / `ruff check` / `uv run mypy` / `bandit -r scripts/mcp_servers/rag_pipeline -c pyproject.toml` — clean.
- `uv run lint-imports` — pass (`UNK-03`).

## Completion criteria
- `delete_document()` contains no `DELETE` SQL and calls `delete_document_chain()` once; the companion test asserts exactly one call with the doc id on a hit and none on a miss; the existing no-orphan and other-documents-untouched cases still pass.

## Out of Scope
- Any change to the shared helper itself, the ingester delete path, or the deletion order.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-12 | 2026-11-12 | Gate resolved 2026-11-12 (see Blocker Log); `delete_document()` now calls `delete_document_chain()`; docstring dependency line updated |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-12 | 2026-11-12 | 2 tests added (`test_delete_document_calls_shared_helper`, `test_delete_document_missing_url_skips_shared_helper`); red first, then green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-12 | 2026-11-12 | ruff format/check, mypy, bandit, mock-patch-targets, `lint-imports` (6 contracts kept), rag_pipeline + delete-chain tests green |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | rmcompat001 phase-all gate (`rag_05_07` startup-paragraph rewrite) | Yes | 2026-11-12 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

### Companion test files
- `tests/mcp_servers/rag_pipeline/test_document_manager.py`
  - Procedure: in `TestDeleteDocument`, patch `delete_document_chain` where `DocumentManager` imports it; assert it is called once with the doc id on a hit and not called on a miss.
  - Validation: `uv run python tools/check_mock_patch_targets.py` then `uv run pytest tests/mcp_servers/rag_pipeline -v`.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` (route MCP deletion through the shared helper, no inline `DELETE`) and `REQ-005` (test that the helper is used)
- **Source issue**: issues/20261109-113123_adrrev013_rag-consistency-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-102935_adrrev013_rag-consistency-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-063813
- **Related target files**: `scripts/mcp_servers/rag_pipeline/document_manager.py`, `tests/mcp_servers/rag_pipeline/test_document_manager.py`
