## Goal

Update `tests/mcp_servers/file/test_file_read_mcp_models.py` to reflect the
`max_file_size_kb` → `max_read_bytes` rename and dropped KB conversion (REQ-001,
REQ-003, T-1), per `plans/20260826-115018_plan.md`.

## Scope

- In scope: `TestFileReadConfig::test_from_dict_defaults`,
  `test_from_dict_custom_values`, `test_dataclass_fields`, plus one new test case
  for a non-1024-aligned value.
- Out of scope: `TestReadModelsImport` (unrelated to this rename); any RAG-pipeline
  test file.

## Assumptions

- `scripts/mcp_servers/file/read_models.py`'s `FileReadConfig` field has been (or is
  being, in this same pass, seq 02) renamed to `max_read_bytes` with its `from_dict`
  KB division removed — this file's assertions depend on that change landing
  together.

## Design decisions

- Update the three existing tests' field-name references and expected values to the
  corrected byte semantics, rather than deleting and rewriting them wholesale —
  preserves this file's existing test-case structure and intent (defaults case,
  custom-values case, field-introspection case).
- Add one new test case asserting a non-1024-aligned value (e.g. `999999`)
  round-trips unchanged — this is the specific regression guard REQ-003 requires
  (proves no hidden `// 1024`/`* 1024` conversion remains anywhere in the load path).

## Alternatives considered

- N/A: mechanical test update following directly from the seq 02 source-code
  change; the one substantive addition (non-aligned-value test) is explicitly
  specified by this Plan's own `T-1`.

## Implementation
### Target file
`tests/mcp_servers/file/test_file_read_mcp_models.py`

### Procedure
1. In `test_from_dict_defaults` (lines 26-31): change `cfg.max_file_size_kb == 1000`
   to `cfg.max_read_bytes == 1024000`.
2. In `test_from_dict_custom_values` (lines 33-45): change `cfg.max_file_size_kb ==
   2048` to `cfg.max_read_bytes == 2097152` (exact pass-through of the input
   `"max_read_bytes": 2097152`, not `// 1024`).
3. In `test_dataclass_fields` (lines 47-54): change the expected field-name set's
   `"max_file_size_kb"` to `"max_read_bytes"`.
4. Add a new test method (e.g. `test_from_dict_non_aligned_value_survives_unchanged`)
   asserting `FileReadConfig.from_dict({"max_read_bytes": 999999}).max_read_bytes ==
   999999`.
5. Run `uv run pytest tests/mcp_servers/file/test_file_read_mcp_models.py -v`.

### Method
Direct test-file edits (Edit tool) — three assertion/value updates, one new test
method; no changes to `TestReadModelsImport`.

### Details
Current file content (verified 2026-08-27, reproduced in full above in this
procedure's context) uses `cfg.max_file_size_kb` in three places (lines 28, 42, 50).
After the edits, no reference to `max_file_size_kb` should remain in this file —
confirm with `rg -n "max_file_size_kb" tests/mcp_servers/file/test_file_read_mcp_models.py`
returning nothing.

New test method body:
```python
def test_from_dict_non_aligned_value_survives_unchanged(self) -> None:
    cfg = FileReadConfig.from_dict({"max_read_bytes": 999999})
    assert cfg.max_read_bytes == 999999
```
Place it within `TestFileReadConfig`, adjacent to the other `from_dict`-focused
tests.

## Compatibility considerations

- Test-only change; no production code path is affected.
- Depends on seq 02 (`read_models.py`) landing in the same change — without it,
  these updated assertions fail against the still-old field name/semantics.

## Security considerations

- N/A: test-only change, no security-relevant code path.

## Rollback considerations

- Revert via `git diff`/`git checkout -- <path>`; must be reverted together with
  seq 02 (`read_models.py`) and seq 03 (`read_service.py`) in this same pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/file/test_file_read_mcp_models.py` | Unit | `uv run pytest tests/mcp_servers/file/test_file_read_mcp_models.py -v` | All tests pass once seq 02 (`read_models.py`) has also landed |

## Completion criteria

- No reference to `max_file_size_kb` remains in this file.
- `test_from_dict_defaults` expects `1024000`; `test_from_dict_custom_values`
  expects `2097152` (exact pass-through); `test_dataclass_fields` expects
  `max_read_bytes` in the field-name set.
- A new test proves a non-1024-aligned value round-trips unchanged.

## Out of scope

- `TestReadModelsImport`.
- Any RAG-pipeline test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update `test_from_dict_defaults` | Pending | — | — | |
| 2 | Update `test_from_dict_custom_values` | Pending | — | — | |
| 3 | Update `test_dataclass_fields` | Pending | — | — | |
| 4 | Add `test_from_dict_non_aligned_value_survives_unchanged` | Pending | — | — | |
| 5 | Run `uv run pytest tests/mcp_servers/file/test_file_read_mcp_models.py -v` | Pending | — | — | Requires seq 02 (`read_models.py`) applied first |

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
- **Related target files**: `tests/mcp_servers/file/test_file_read_mcp_models.py`
