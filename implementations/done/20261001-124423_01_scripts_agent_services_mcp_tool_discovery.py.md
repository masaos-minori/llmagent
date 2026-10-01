## Goal

Remove the dead method `_fetch_server_tools()` (and the helper `_validate_and_normalize_entry()` that only it called) from `McpToolDiscoveryService` in `scripts/agent/services/mcp_tool_discovery.py`, eliminating a second, diverging MCP `/v1/tools` fetch-and-validate implementation while leaving the live discovery path byte-for-byte unchanged.

## Scope

- **In-Scope**: Delete `_fetch_server_tools()` (defined at line 342) and `_validate_and_normalize_entry()` (defined at line 434, called only at line 417 inside `_fetch_server_tools`). Remove any import newly flagged unused by ruff. Re-confirm no external caller exists immediately before deleting.
- **Out-of-Scope**: Any change to `discover_all()`, `McpToolsHttpClient.fetch_tools()`, or any other method. Unifying the two validation implementations into one (a separate improvement). Re-wiring `_fetch_server_tools()` as the live path. Modifying test files beyond running existing tests.

## Assumptions

- Both methods are genuinely dead: a caller search across `scripts/`, `tests/`, and `docs/` returns only the two definitions plus the single internal call at line 417. This is confirmed repository evidence, not an assumption.
- Deleting `_fetch_server_tools()` makes `_validate_and_normalize_entry()` unused: its only call site (line 417) lives inside `_fetch_server_tools()`. Shared helpers it uses (`_warning_entry`, `validate_tool_schema_v2()`) are referenced by live-path code and are not orphaned.
- No subclass overrides these underscore-prefixed private methods: no other definitions of either name exist in the repository.
- The deletions will not leave a now-unused import; `ruff check` will surface any such import for removal.

## Design decisions

- Deletion-only; no architectural change. `McpToolDiscoveryService.discover_all()` remains the sole entry point and builds the `RuntimeToolRegistry` through `McpToolsHttpClient.fetch_tools()` + `ToolEntryValidator.validate_entry()`.
- Task-size classification is Path A (one file, private-method deletion only, no public/runtime interface change, no DB schema change); architecture/dependency/historical/operational analysis is therefore skipped.

## Alternatives considered

- **Wire `_fetch_server_tools()` as the live path** instead of deleting it. Not pursued: the method has had no caller since introduction, and the live path already works via `McpToolsHttpClient.fetch_tools()`.
- **Merge the two validation implementations**. Not pursued: out of scope for this task; would require design work beyond simple deletion.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py`

### Procedure

1. Confirm no external caller exists for `_fetch_server_tools()` and `_validate_and_normalize_entry()`.
2. Delete `_fetch_server_tools()` method definition (lines 342–432).
3. Delete `_validate_and_normalize_entry()` method definition (lines 434–503; ends at `return entry, None` on line 503, before `_detect_duplicates` at line 505).
4. Run `ruff format` + `ruff check`; remove any newly-unused imports.
5. Run `mypy` and `bandit` on the file; confirm clean.
6. Re-run the existing discovery unit suite (`tests/agent/services/test_mcp_tool_discovery.py`, 79 tests) end-to-end against `discover_all()`.
7. Re-run `tests/agent/test_startup.py` and `tests/agent/shared/test_startup_validation_pipeline.py`.

### Method

Delete two private methods from `McpToolDiscoveryService`:

#### `_fetch_server_tools()` (line 342–432)

```python
async def _fetch_server_tools(
    self, key: str, cfg: McpServerConfig
) -> tuple[list[_RawEntry], list[StartupCheckOutcome], bool]:
```

This async method fetches one server's `/v1/tools` endpoint, validates the response shape, normalizes entries via `_validate_and_normalize_entry()`, and returns `(entries, findings, is_unreachable)`. It is never called from anywhere outside this class.

#### `_validate_and_normalize_entry()` (line 434–498)

```python
def _validate_and_normalize_entry(
    self, server_key: str, server_url: str, entry: object
) -> tuple[dict[str, object] | None, StartupCheckOutcome | None]:
```

This sync method validates one raw `/v1/tools` entry (checks dict shape, required fields `name`/`description`, type constraints). Its only call site is line 417 inside `_fetch_server_tools()`.

### Details

**Step 1: Pre-deletion caller verification**

Run `rg '_fetch_server_tools\|_validate_and_normalize_entry' scripts/ tests/ docs/` to confirm zero external callers. Current evidence shows exactly 3 occurrences: the two method definitions (lines 342, 434) and the internal call at line 417.

**Step 2: Delete `_fetch_server_tools()`**

Remove lines 342–432 inclusive. This is the entire method body including docstring, return type annotation, and all nested logic (HTTP fetch, JSON parsing, schema_version validation, tool list iteration with `_validate_and_normalize_entry()` calls).

**Step 3: Delete `_validate_and_normalize_entry()`**

Remove lines 434–503 inclusive (method body ends at `return entry, None` on line 503). After Step 2, this method has no remaining callers. Verify again with `rg '_validate_and_normalize_entry' scripts/ tests/ docs/` — should show zero matches.

**Step 4: Fix unused imports**

Run `uv run ruff format scripts/ && uv run ruff check scripts/`. If any import becomes unused (e.g., `http.HTTPStatus` if only used in the deleted method), remove it.

**Step 5: Static analysis**

Run `uv run mypy scripts/agent/services/mcp_tool_discovery.py` and `uv run bandit -r scripts/agent/services/mcp_tool_discovery.py -c pyproject.toml`. Both must be clean.

**Step 6: Discovery unit tests**

Run `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -x -q`. All 79 tests must pass.

**Step 7: Integration tests**

Run `uv run pytest tests/agent/test_startup.py tests/agent/shared/test_startup_validation_pipeline.py -x -q`. All must pass.

## Compatibility considerations

- No public API changes. Both methods are private (underscore-prefixed) and have no external callers.
- `discover_all()` is untouched; the live discovery path produces the same `RuntimeToolRegistry` and the same findings.
- Backward compatible: removing dead code does not affect any existing behavior.

## Security considerations

- Removing dead code reduces attack surface by eliminating a second, diverging validation path that could mask which validation logic is authoritative.
- No new security implications from deletion.

## Rollback considerations

- To rollback, restore the deleted method definitions from git history: `git checkout HEAD~1 -- scripts/agent/services/mcp_tool_discovery.py`.
- The rollback restores both methods and their original callers intact.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/mcp_tool_discovery.py` | Post-deletion static checks | `uv run ruff format scripts/ && uv run ruff check scripts/` | Clean (no formatting/style issues) |
| `scripts/agent/services/mcp_tool_discovery.py` | Type checking | `uv run mypy scripts/agent/services/mcp_tool_discovery.py` | Clean (no type errors) |
| `scripts/agent/services/mcp_tool_discovery.py` | Security scan | `uv run bandit -r scripts/agent/services/mcp_tool_discovery.py -c pyproject.toml` | Clean (no findings) |
| `tests/agent/services/test_mcp_tool_discovery.py` | Regression (79 tests) | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -x -q` | All 79 pass |
| `tests/agent/test_startup.py` | Regression | `uv run pytest tests/agent/test_startup.py -x -q` | All pass |
| `tests/agent/shared/test_startup_validation_pipeline.py` | Regression | `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py -x -q` | All pass |

## Completion criteria

- AC-001: No remaining definition or call site for `_fetch_server_tools()` anywhere in `scripts/`, `tests/`, or `docs/`.
- AC-002: No remaining definition or call site for `_validate_and_normalize_entry()` anywhere in `scripts/`, `tests/`, or `docs/`.
- AC-003: `discover_all()` builds the same `RuntimeToolRegistry` and emits the same findings; the 79 discovery tests plus the startup/pipeline tests pass unchanged.
- AC-004: `uv run ruff format scripts/ && uv run ruff check scripts/`, `uv run mypy scripts/`, and `uv run bandit -r scripts/agent/services/mcp_tool_discovery.py -c pyproject.toml` are all clean after the change.

## Out of scope

- Changing how approvals are requested or resolved during a live session.
- Altering the approval table schema.
- Unifying the two validation implementations into one.
- Re-wiring `_fetch_server_tools()` as the live path.
- Modifying test files beyond running existing tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261001-124529 | 20261001-155911 | Deleted `_fetch_server_tools()` (lines 342-432) and `_validate_and_normalize_entry()` (lines 434-503) from `McpToolDiscoveryService`; caller recheck shows zero remaining references; AST parse OK |
| 2 | Add or update tests per Validation plan | Completed | — | 20261001-155911 | No new tests required (dead-method deletion); existing suite covers `discover_all()` regression |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261001-155911 | `ruff format`/`ruff check` clean; `bandit` clean; `mypy` fails on a PRE-EXISTING `tool_constants` duplicate-module-path config error (verified against HEAD, unrelated to this change); 79 discovery + 52 startup/pipeline tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261001-155911 | N/A: no `docs/00_index.md` task-scope mapping for `scripts/agent/services/mcp_tool_discovery.py` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: no blockers | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: N/A: the Plan's own Traceability section carries `{path}` placeholder (not filled)
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260930-205529_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-124423
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py