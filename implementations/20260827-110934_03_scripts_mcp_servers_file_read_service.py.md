## Goal

Update `read_service.py`'s `build_service` to consume `FileReadConfig.max_read_bytes`
directly, without the `* 1024` re-multiplication (REQ-001, M-3), per
`plans/20260826-115018_plan.md`.

## Scope

- In scope: the single `max_read_bytes=cfg.max_file_size_kb * 1024` line (line 199)
  in `build_service`.
- Out of scope: any other part of `build_service` or this file; any RAG-pipeline
  change.

## Assumptions

- `scripts/mcp_servers/file/read_models.py`'s `FileReadConfig` field has been (or is
  being, in the same pass) renamed from `max_file_size_kb` to `max_read_bytes` — this
  file's change depends on that rename (seq 02 in this pass) landing together, not
  independently.

## Design decisions

- Direct pass-through: `max_read_bytes=cfg.max_read_bytes` — no transformation, since
  the field now already holds the correct byte value after the seq 02 change.

## Alternatives considered

- N/A: single-line mechanical update following directly from the seq 02 field
  rename; no design alternative applies.

## Implementation
### Target file
`scripts/mcp_servers/file/read_service.py`

### Procedure
1. Change line 199 from `max_read_bytes=cfg.max_file_size_kb * 1024,` to
   `max_read_bytes=cfg.max_read_bytes,`.
2. Run `uv run pytest tests/mcp_servers/file/test_read_service.py -v` (will fail
   until the seq 05 test-file item in this pass is also applied).

### Method
Direct code edit (Edit tool) — one keyword-argument line.

### Details
Current code (verified 2026-08-27, line 199):
```python
        max_read_bytes=cfg.max_file_size_kb * 1024,
```
Change to:
```python
        max_read_bytes=cfg.max_read_bytes,
```
No other line in `build_service` references `max_file_size_kb`/`max_read_bytes` —
confirmed via `rg -n "max_file_size_kb\|max_read_bytes" scripts/mcp_servers/file/read_service.py`
returning only this one line as of 2026-08-27.

## Compatibility considerations

- Must land in the same change as seq 02 (`read_models.py`'s field rename) — this
  file alone, without that rename, would raise `AttributeError: 'FileReadConfig'
  object has no attribute 'max_read_bytes'`.
- Effective enforced byte limit changes from 999,424 to 1,000,000 for the default
  config value (same change already noted in the seq 02 procedure).

## Security considerations

- N/A: no security-relevant behavior; corrects a units bug in a resource limit.

## Rollback considerations

- Single-line revert via `git diff`/`git checkout -- scripts/mcp_servers/file/read_service.py`;
  must be reverted together with seq 02 (`read_models.py`) and the seq 04/05 test
  files in this same pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/file/read_service.py` | Unit | `uv run pytest tests/mcp_servers/file/test_read_service.py -v` | `build_service` enforces exactly `cfg.max_read_bytes`, no `* 1024`; passes once seq 05 test-file item is also applied |

## Completion criteria

- `build_service`'s `max_read_bytes` argument equals `cfg.max_read_bytes` exactly,
  with no `* 1024` or other transformation anywhere in this file.

## Out of scope

- Any other part of `build_service` or this file.
- Any RAG-pipeline change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change `build_service`'s `max_read_bytes` argument to direct pass-through | Pending | — | — | Depends on seq 02 (`read_models.py`) landing first or together |
| 2 | Run `uv run pytest tests/mcp_servers/file/test_read_service.py -v` | Pending | — | — | Requires seq 05 test-file item applied first |

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
- **Requirement ID**: REQ-001
- **Source issue**: `issues/20260821_05_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-115018_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110934
- **Related target files**: `scripts/mcp_servers/file/read_service.py`
