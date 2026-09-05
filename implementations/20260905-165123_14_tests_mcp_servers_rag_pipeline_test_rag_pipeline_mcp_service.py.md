## Goal
Remove `svc.invalidate_cache()` tests and `fmt_delete_document`'s cache-invalidation
assertions from `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`, since
the API and behavior they assert no longer exist once procedure documents `01`/`06`
land (`REQ-002`, `REQ-006`).

## Scope
- **In-Scope**: remove the `# ── invalidate_cache ──` comment header and the
  `class TestInvalidateCache:` block in its entirety (lines 432-445: both
  `test_delegates_to_pipeline` and `test_raises_when_not_started`); remove
  `test_found_invalidates_cache` (lines 642-648) and
  `test_not_found_does_not_invalidate_cache` (lines 657-662) from
  `class TestFmtDeleteDocument`.
- **Out-of-Scope**: `TestFmtDeleteDocument`'s other test methods
  (`test_found_returns_deleted`, `test_not_found_returns_not_found`,
  `test_missing_url_returns_error`, and any other method in that class not named
  above) — confirmed unrelated to cache invalidation by reading their bodies; every
  other test class in this file (e.g. `test_raises_when_not_started` at line 425,
  belonging to a different class than the one removed here — verify class membership
  before editing, see Details).

## Assumptions
- `RagPipelineMCPService.invalidate_cache()` (procedure document `06`) and
  `RagPipeline.invalidate_cache()` (procedure document `01`) are both removed in the
  same implementation pass — these tests would otherwise still pass against
  unremoved production code, masking an incomplete Plan execution.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove `TestInvalidateCache` as a whole class (it exists solely to test the removed
  `svc.invalidate_cache()` method) but remove only the two named methods from
  `TestFmtDeleteDocument` (the class itself continues to test valid,
  non-cache-related `fmt_delete_document()` behavior — deleting/found/not-found
  paths — which this Plan does not remove).

## Alternatives considered
- Keeping `test_not_found_does_not_invalidate_cache` as a negative assertion that
  nothing cache-related happens — rejected: once `invalidate_cache()` does not exist
  on the pipeline mock, asserting `pipeline.invalidate_cache.assert_not_called()`
  against a `MagicMock()` attribute that no real object will ever expose is a
  vacuous/misleading assertion, not a meaningful regression guard.

## Implementation
### Target file
`tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`

### Procedure
1. Remove the `# ── invalidate_cache ──────────────────────────────────────────────────────────`
   comment header (line 432) and the following `class TestInvalidateCache:` block in
   full (lines 434-445: `test_delegates_to_pipeline`, `test_raises_when_not_started`).
2. Confirm the blank-line spacing between the preceding class (ending at line 429) and
   the following `# ── MCP tool formatters ──` section comment (line 447) is left at a
   single blank line, matching this file's existing convention.
3. Within `class TestFmtDeleteDocument:`, remove `test_found_invalidates_cache` (lines
   642-648, immediately after `test_found_returns_deleted`).
4. Within the same class, remove `test_not_found_does_not_invalidate_cache` (lines
   657-662, immediately after `test_not_found_returns_not_found`).

### Method
Direct removal via `Edit`, applied as two separate edits within the same file (one for
`TestInvalidateCache`, one each for the two `TestFmtDeleteDocument` methods) since they
are not contiguous.

### Details
- Re-read the file's current class boundaries immediately before editing (per Step 3a
  Adversarial Verification) — line numbers are approximate and may have shifted if this
  file was touched by an unrelated change since this Plan's Step 3 evidence was
  gathered; match on the method/class names given above, not on line numbers alone.
- After steps 3-4, `TestFmtDeleteDocument` must retain exactly: `test_found_returns_deleted`,
  `test_not_found_returns_not_found`, `test_missing_url_returns_error`, and any other
  method already confirmed unrelated to caching.
- Confirm after editing: `rg -n "invalidate_cache" tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`
  returns zero matches.

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; independent of other test files, but
  functionally coupled to procedure documents `01` and `06` (reverting only this test
  file while `01`/`06` remain applied would leave tests referencing a removed method).

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py -v` —
  all remaining tests pass; `TestFmtDeleteDocument`'s non-cache tests confirm deletion
  behavior is otherwise unchanged.
- `rg -n "invalidate_cache" tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py`
  — zero matches.

## Completion criteria
- `TestInvalidateCache` no longer exists in this file (Plan `AC-9`).
- `TestFmtDeleteDocument` no longer contains cache-invalidation assertions, but its
  other tests (found/not-found/missing-url) remain intact and pass (Plan `AC-4`,
  `AC-9`).

## Out of scope
- `RagPipelineMCPService.invalidate_cache()` itself (procedure document `06`).
- `TestFmtDeleteDocument`'s non-cache-related test methods.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-06 | 2026-09-06 | All invalidate_cache references removed; rg returns zero matches |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-06 | 2026-09-06 | N/A: this document itself is a test-removal change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-06 | 2026-09-06 | pytest passes with zero regressions |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-06 | 2026-09-06 | N/A |

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
- **Requirement ID**: `REQ-002` (assert `invalidate_cache()` absent from protocol/service); `REQ-006` (remove tests referencing the removed API)
- **Source issue**: issues/20260902-150339_semcacherm_remove_semanticcache_implementation_and_invalidation_paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-140151_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-165123
- **Related target files**: tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py
