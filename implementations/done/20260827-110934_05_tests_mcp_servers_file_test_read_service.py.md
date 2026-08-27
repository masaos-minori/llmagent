## Goal

Update `tests/mcp_servers/file/test_read_service.py::test_build_service_with_allowed_dirs`
to construct `FileReadConfig(max_read_bytes=500, ...)` and drop the `* 1024`
expectation (REQ-001, REQ-003, T-1), per `plans/20260826-115018_plan.md`.

## Scope

- In scope: `test_build_service_with_allowed_dirs` (verified at lines 1195-1208 as of
  2026-08-27).
- Out of scope: `test_build_service_...` tests that only use `allowed_dirs=[]` and do
  not reference `max_file_size_kb`/`max_read_bytes` (e.g. the test at line 1190,
  confirmed unaffected — it asserts only `caplog` output and `_allowed_dirs`); any
  RAG-pipeline test file.

## Assumptions

- `scripts/mcp_servers/file/read_models.py`'s `FileReadConfig` field has been (or is
  being, in this same pass, seq 02) renamed to `max_read_bytes`, and
  `read_service.py`'s `build_service` (seq 03) now passes it through directly
  without `* 1024` — this test's construction and assertion depend on both landing
  together.

## Design decisions

- Keep the test's semantic intent (construct with a small custom limit, verify
  `build_service` propagates it to the service instance) — only the keyword
  argument name and the expected value's arithmetic change, since the field now
  means bytes directly rather than KB.

## Alternatives considered

- N/A: mechanical test update following directly from the seq 02/03 source-code
  changes.

## Implementation
### Target file
`tests/mcp_servers/file/test_read_service.py`

### Procedure
1. In `test_build_service_with_allowed_dirs` (verified at lines 1195-1208 as of
   2026-08-27), change the `FileReadConfig(...)` construction's `max_file_size_kb=500`
   keyword to `max_read_bytes=500`.
2. Change the assertion `assert svc.max_read_bytes == 500 * 1024` to
   `assert svc.max_read_bytes == 500`.
3. Run `uv run pytest tests/mcp_servers/file/test_read_service.py -v`.

### Method
Direct test-file edit (Edit tool) — one constructor keyword, one assertion value.

### Details
Current code (verified 2026-08-27, lines 1195-1208):
```python
    def test_build_service_with_allowed_dirs(self, tmp_path: Path) -> None:
        from mcp_servers.file.read_models import FileReadConfig
        from mcp_servers.file.read_service import build_service

        cfg = FileReadConfig(
            allowed_dirs=[str(tmp_path)],
            max_file_size_kb=500,
            max_depth=4,
            max_files_per_batch=25,
        )
        svc = build_service(cfg)
        assert svc._allowed_dirs == [Path(str(tmp_path))]
        assert svc.max_read_bytes == 500 * 1024
        assert svc.max_tree_depth == 4
        assert svc._max_search_results == 25
```
Change to:
```python
    def test_build_service_with_allowed_dirs(self, tmp_path: Path) -> None:
        from mcp_servers.file.read_models import FileReadConfig
        from mcp_servers.file.read_service import build_service

        cfg = FileReadConfig(
            allowed_dirs=[str(tmp_path)],
            max_read_bytes=500,
            max_depth=4,
            max_files_per_batch=25,
        )
        svc = build_service(cfg)
        assert svc._allowed_dirs == [Path(str(tmp_path))]
        assert svc.max_read_bytes == 500
        assert svc.max_tree_depth == 4
        assert svc._max_search_results == 25
```
Confirm no other reference to `max_file_size_kb` remains in this file via
`rg -n "max_file_size_kb" tests/mcp_servers/file/test_read_service.py` — the other
`FileReadConfig(allowed_dirs=[])` construction at line 1190 does not set this field
and is unaffected.

## Compatibility considerations

- Test-only change; no production code path is affected.
- Depends on seq 02 (`read_models.py`) and seq 03 (`read_service.py`) landing in the
  same change.

## Security considerations

- N/A: test-only change, no security-relevant code path.

## Rollback considerations

- Revert via `git diff`/`git checkout -- <path>`; must be reverted together with
  seq 02 and seq 03 in this same pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/file/test_read_service.py` | Unit | `uv run pytest tests/mcp_servers/file/test_read_service.py -v` | `test_build_service_with_allowed_dirs` passes once seq 02/03 have also landed; all other tests unaffected |

## Completion criteria

- `test_build_service_with_allowed_dirs` constructs `FileReadConfig` with
  `max_read_bytes=500` and asserts `svc.max_read_bytes == 500` (no `* 1024`).

## Out of scope

- `test_build_service_...` tests unrelated to `max_file_size_kb`/`max_read_bytes`.
- Any RAG-pipeline test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update `test_build_service_with_allowed_dirs`'s construction and assertion | Completed | 2026-08-28 | 2026-08-28 | Adversarial verification confirmed: lines 1202-1208 show `max_read_bytes=512000` and `assert svc.max_read_bytes == 512000` — no `max_file_size_kb` or `* 1024`. REQ-001 completed by `plans/done/20260826-115018_plan.md`. No code changes needed. |
| 2 | Run `uv run pytest tests/mcp_servers/file/test_read_service.py -v` | Completed | 2026-08-28 | 2026-08-28 | Validated below. |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: `issues/20260821_05_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-115018_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110934
- **Related target files**: `tests/mcp_servers/file/test_read_service.py`
