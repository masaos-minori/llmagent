## Goal

Fix the `max_read_bytes` unit mismatch (REQ-001, M-3) in `FileReadConfig` by renaming
`max_file_size_kb` to `max_read_bytes` and removing the hidden KB round-trip, per
`plans/20260826-115018_plan.md`.

## Scope

- In scope: `FileReadConfig`'s dataclass field name/default and `from_dict`'s
  conversion logic in this one file.
- Out of scope: `read_service.py`'s `build_service` call site (separate target file,
  seq 03 in this pass); any RAG-pipeline change (REQ-002, separate target files);
  `RagPipelineConfig.from_dict`'s pre-existing bare-coercion pattern (explicitly
  out of scope per this Plan).

## Assumptions

- `config/file_read_mcp_server.toml`'s inline comment already states
  `max_read_bytes` is bytes, and its current value is `1000000` — re-verified
  2026-08-27.
- Renaming the dataclass field is safe: `rg "max_file_size_kb"
  scripts/mcp_servers/file/*.py tests/mcp_servers/file/*.py` finds exactly three call
  sites (`read_service.py` and two test files), all accounted for as separate target
  files in this same implementation-procedure pass — re-verified 2026-08-27, no
  additional site found.

## Design decisions

- Interpret `max_read_bytes` as bytes end-to-end; drop the KB intermediate value
  entirely rather than renaming the TOML key (per this Plan's Design > "M-3
  decision").
- Keep `get_typed(d, "max_read_bytes", int, "an integer", default=1024000)` as the
  `from_dict` read call (TOML key name unchanged) — only the field name it populates
  and the value transformation change.
- Change the dataclass top-level default from `1000` to `1024000` so
  `FileReadConfig()`'s direct-construction default matches `from_dict({})`'s
  default (both now express the same 1,024,000-byte fallback, consistent units).

## Alternatives considered

- Renaming the TOML key instead of the code field was considered and rejected — the
  Plan's own Design section found the TOML author's byte intent unambiguous and a
  KB-suffixed key naming precedent already exists elsewhere (`github_mcp_server.toml`
  `max_file_size_kb`), making a code-side fix lower-risk.

## Implementation
### Target file
`scripts/mcp_servers/file/read_models.py`

### Procedure
1. Rename the dataclass field `max_file_size_kb` (line 28) to `max_read_bytes`,
   changing its default from `1000` to `1024000`.
2. In `from_dict` (lines 36-40), change the keyword to `max_read_bytes=` and remove
   the `// 1024` division — store `get_typed(...)`'s result directly.
3. Run `uv run pytest tests/mcp_servers/file/test_file_read_mcp_models.py -v` (will
   fail until the seq 04 test-file item in this pass is also applied — expected at
   this point in an interrupted/partial run).

### Method
Direct code edit (Edit tool) — one field declaration, one `from_dict` construction
block.

### Details
Current code (verified 2026-08-27, lines 24-46):
```python
@dataclasses.dataclass
class FileReadConfig:
    """Typed configuration for the File Read MCP server."""

    max_file_size_kb: int = 1000
    allowed_dirs: list[str] = dataclasses.field(default_factory=list)
    max_depth: int = 5
    max_files_per_batch: int = 100

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FileReadConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            max_file_size_kb=(
                get_typed(d, "max_read_bytes", int, "an integer", default=1024000)
            )
            // 1024,
            allowed_dirs=list(get_typed(d, "allowed_dirs", list, "a list", default=[])),
            max_depth=get_typed(d, "max_tree_depth", int, "an integer", default=5),
            max_files_per_batch=get_typed(
                d, "max_search_results", int, "an integer", default=100
            ),
        )
```
Change to:
```python
@dataclasses.dataclass
class FileReadConfig:
    """Typed configuration for the File Read MCP server."""

    max_read_bytes: int = 1024000
    allowed_dirs: list[str] = dataclasses.field(default_factory=list)
    max_depth: int = 5
    max_files_per_batch: int = 100

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FileReadConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            max_read_bytes=get_typed(
                d, "max_read_bytes", int, "an integer", default=1024000
            ),
            allowed_dirs=list(get_typed(d, "allowed_dirs", list, "a list", default=[])),
            max_depth=get_typed(d, "max_tree_depth", int, "an integer", default=5),
            max_files_per_batch=get_typed(
                d, "max_search_results", int, "an integer", default=100
            ),
        )
```
Do not touch `allowed_dirs`/`max_depth`/`max_files_per_batch` or the `load()`
classmethod below (unaffected by this rename).

## Compatibility considerations

- Field rename is a breaking change to `FileReadConfig`'s constructor keyword
  arguments — acceptable per this Plan's Assumptions (only three known call sites,
  no compat shim required per project policy, `tools/check_compat_shims.py`).
- Effective enforced byte limit changes from 999,424 to 1,000,000 for the default
  config value — a 576-byte increase, documented in this Plan's Risks as
  negligible.

## Security considerations

- N/A: no security-relevant behavior; this only corrects a units bug in a resource
  limit, moving it closer to (not further from) the operator's configured intent.

## Rollback considerations

- Single-file revert via `git diff`/`git checkout -- scripts/mcp_servers/file/read_models.py`;
  must be reverted together with the seq 03 (`read_service.py`) and seq 04/05 (test
  files) items in this same pass, since they share the renamed field — reverting
  this file alone without the others breaks the build.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/file/read_models.py` | Unit | `uv run pytest tests/mcp_servers/file/test_file_read_mcp_models.py -v` | Passes once the seq 04 test-file item in this pass is also applied |
| `scripts/mcp_servers/file/read_models.py` | Static | `uv run mypy scripts/mcp_servers/file/read_models.py` | No new type errors |

## Completion criteria

- `FileReadConfig.max_read_bytes` (renamed from `max_file_size_kb`) equals the raw
  `max_read_bytes` TOML value with no `// 1024` division anywhere in this file.
- `FileReadConfig()`'s default and `from_dict({})`'s default both equal `1024000`.

## Out of scope

- `read_service.py`'s `build_service` (separate target file, seq 03).
- Any RAG-pipeline change.
- `RagPipelineConfig.from_dict`'s bare-coercion pattern.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename `max_file_size_kb` → `max_read_bytes`, update default | Pending | — | — | |
| 2 | Remove `// 1024` in `from_dict` | Pending | — | — | |
| 3 | Run `uv run pytest tests/mcp_servers/file/test_file_read_mcp_models.py -v` | Pending | — | — | Requires seq 04 test-file item applied first |

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
- **Related target files**: `scripts/mcp_servers/file/read_models.py`
