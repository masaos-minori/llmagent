# Implementation: Enforce fail-closed path authorization on MDQ path-accepting tools

## Goal

Enforce fail-closed path authorization on all MDQ path-accepting tools (`index_paths`, `refresh_index`, `outline`) so that paths outside `allowed_dirs` are rejected, `..` traversal is blocked, and symlink escapes are prevented.

## Scope

- **In-Scope**:
  - Harden `index_paths` in `scripts/mcp/mdq/indexer.py` to raise `MdqAuthorizationError` instead of logging a warning and continuing
  - Harden `refresh_index` path validation in `scripts/mcp/mdq/service.py` (`_validate_paths`) to raise `MdqAuthorizationError` instead of logging and continuing
  - Verify `outline` already raises `MdqAuthorizationError` (confirmed in `service.py:471-475`); no change needed
  - Verify `config/mdq_mcp_server.toml` already has `allowed_dirs = []` (confirmed); add inline production example comment
  - Add `tests/test_mdq_path_jail.py` covering: allowed path, denied path, `..` traversal, symlink escape, and empty-allowlist cases
  - Update `docs/04_mcp_04_server_catalog.md` to add path control spec for mdq-mcp
  - Update `docs/04_mcp_05_security_and_safety_model.md` to add mdq-mcp to the access control table

- **Out-of-Scope**:
  - Changing `auth.py` logic (already correct — uses `Path.resolve()`, empty list → False)
  - Adding `allowed_dirs` to `grep_docs` (grep operates on already-indexed chunks in DB, not filesystem paths)
  - Hybrid search / embedding changes
  - DB schema changes
  - `search_docs` / `get_chunk` / `stats` / `fts_consistency_check` / `fts_rebuild` (no filesystem path input)

## Verification Results

### 1. Current state: `index_paths` silently skips denied paths

**File**: `scripts/mcp/mdq/indexer.py`
- Line 115-117: `logger.warning + continue` pattern — denied paths are silently skipped
- Server returns "Indexing complete" even when all paths were denied
- Caller cannot tell if denial occurred

### 2. Current state: `_validate_paths` logs warning only

**File**: `scripts/mcp/mdq/service.py`
- `_validate_paths()` (lines ~564-573): logs warning for denied paths, does not raise
- `refresh_index()` caller will continue with partial indexing (some paths allowed, some denied)
- Inconsistent with `outline` which raises `MdqAuthorizationError`

### 3. `outline` already enforces authorization

**File**: `scripts/mcp/mdq/service.py:471-475`
- Confirmed: raises `MdqAuthorizationError` for denied paths
- No change needed — serves as regression guard

### 4. Config already has `allowed_dirs = []`

**File**: `config/mdq_mcp_server.toml`
- `allowed_dirs = []` already exists (deny-all default)
- Needs production example comment added

## Implementation

### Target file: `scripts/mcp/mdq/indexer.py`

#### Procedure

Replace `logger.warning + continue` with `raise MdqAuthorizationError` in `index_paths()`.

#### Details

**In `index_paths()` — replace lines ~115-117:**
```python
# Before:
if not authorize_path(path, _cfg.allowed_dirs):
    logger.warning(f"Skipping {path_str}: outside allowed directories")
    continue

# After:
if not authorize_path(path, _cfg.allowed_dirs):
    raise MdqAuthorizationError(
        f"Access denied: {path_str} is outside allowed directories"
    )
```

**Add import:**
```python
from mcp.mdq.models import (
    ...
    MdqAuthorizationError,  # NEW
    ...
)
```

### Target file: `scripts/mcp/mdq/service.py`

#### Procedure

Replace `logger.warning` with `raise MdqAuthorizationError` in `_validate_paths()`.

#### Details

**In `_validate_paths()` — replace warning with raise:**
```python
# Before:
if not authorize_path(p, self._cfg.allowed_dirs):
    logger.warning(f"Path outside allowed directories: {p}")
    continue  # or: return False depending on current implementation

# After:
if not authorize_path(p, self._cfg.allowed_dirs):
    raise MdqAuthorizationError(
        f"Access denied: {p} is outside allowed directories"
    )
```

**Note**: `refresh_index()` calls `_validate_paths(req.paths)` inside the lock — exception will propagate naturally to caller.

### Target file: `config/mdq_mcp_server.toml`

#### Procedure

Add production example comment for `allowed_dirs`.

#### Details

**Expand the comment on `allowed_dirs`:**
```toml
# Directories that mdq-mcp is allowed to read from.
# Default: [] (deny-all — no paths are allowed).
# Production example: allowed_dirs = ["/opt/llm/docs"]
allowed_dirs = []
```

### Target file: `tests/test_mdq_path_jail.py` (NEW)

#### Procedure

Create new test file with path jail authorization tests.

#### Details

**Test cases:**
```python
#!/usr/bin/env python3
"""Tests for MDQ path authorization enforcement (fail-closed)."""

import pytest
from pathlib import Path

from mcp.mdq.models import MdqAuthorizationError


class TestPathJail:
    """Verify fail-closed path authorization on all path-accepting tools."""

    def test_allowed_path_accepted(self) -> None:
        """Path within allowed_dirs is indexed without error."""
        # Requires mock or fixture with configured allowed_dirs
        ...

    def test_denied_path_raises(self) -> None:
        """Path outside allowed_dirs raises MdqAuthorizationError in index_paths."""
        ...

    def test_dotdot_traversal_denied(self) -> None:
        """../secret path raises MdqAuthorizationError."""
        ...

    def test_symlink_escape_denied(self) -> None:
        """Symlink pointing outside allowed_dirs raises MdqAuthorizationError."""
        ...

    def test_empty_allowlist_denies_all(self) -> None:
        """Empty allowed_dirs denies all paths."""
        ...

    def test_refresh_index_denied_path_raises(self) -> None:
        """refresh_index raises MdqAuthorizationError for denied path."""
        ...

    def test_outline_denied_path_raises(self) -> None:
        """outline raises MdqAuthorizationError for denied path (regression guard)."""
        ...
```

### Target file: `docs/04_mcp_05_security_and_safety_model.md`

#### Procedure

Add mdq-mcp row to access control table.

#### Details

**Add mdq-mcp row to Fail-Open vs Fail-Closed summary:**
| MCP Server | Fail-Open / Fail-Closed | Notes |
|------------|------------------------|-------|
| mdq-mcp | Fail-Closed | `allowed_dirs = []` denies all paths by default; `authorize_path()` enforces at each file access |

### Target file: `docs/04_mcp_04_server_catalog.md`

#### Procedure

Add path control spec to mdq-mcp section.

#### Details

**Add to mdq-mcp section:**
```markdown
### Path Control

All path-accepting tools enforce fail-closed authorization via `allowed_dirs`:

| Tool | Path Input | Authorization |
|------|-----------|---------------|
| `index_paths` | Directories to index | `authorize_path()` — raises `MdqAuthorizationError` if outside allowed_dirs |
| `refresh_index` | Paths to refresh | `_validate_paths()` — raises `MdqAuthorizationError` if any path is denied |
| `outline` | File to outline | `authorize_path()` — raises `MdqAuthorizationError` if outside allowed_dirs |

- `..` traversal: blocked by `Path.resolve()` in `authorize_path()`
- Symlink escapes: blocked by `Path.resolve()` in `authorize_path()`
- Empty `allowed_dirs = []`: denies all paths (fail-closed default)
```

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `indexer.py::index_paths` | Unit test denied path raises | `uv run pytest tests/test_mdq_path_jail.py::test_denied_path_raises` | `MdqAuthorizationError` raised |
| `indexer.py::index_paths` | Unit test `..` traversal blocked | `uv run pytest tests/test_mdq_path_jail.py::test_dotdot_traversal_denied` | `MdqAuthorizationError` raised |
| `indexer.py::index_paths` | Unit test symlink escape blocked | `uv run pytest tests/test_mdq_path_jail.py::test_symlink_escape_denied` | `MdqAuthorizationError` raised |
| `indexer.py::index_paths` | Unit test empty allowlist | `uv run pytest tests/test_mdq_path_jail.py::test_empty_allowlist_denies_all` | `MdqAuthorizationError` raised |
| `service.py::refresh_index` | Unit test denied path raises | `uv run pytest tests/test_mdq_path_jail.py::test_refresh_index_denied_path_raises` | `MdqAuthorizationError` raised |
| `service.py::outline` | Regression — still raises on denied | `uv run pytest tests/test_mdq_path_jail.py::test_outline_denied_path_raises` | `MdqAuthorizationError` raised |
| Regression suite | Existing mdq tests unbroken | `uv run pytest tests/test_mdq_service.py tests/test_mdq_incremental_refresh.py -v` | All pass |
| Lint / type | No new errors | `uv run ruff check scripts/mcp/mdq/ && uv run mypy scripts/mcp/mdq/ --ignore-missing-imports` | No errors |
| Import contract | Layer contract holds | `uv run lint-imports` | No violations |

## Risks & Mitigations

- **Risk**: Production deployments with `allowed_dirs = []` (default) will now get `MdqAuthorizationError` from `index_paths`/`refresh_index` where they previously got silent success with no indexing done. → **Mitigation**: Document the behavioral change clearly in config comment and deployment notes. Operators must configure `allowed_dirs` before using indexing tools.

- **Risk**: `_validate_paths` in `service.py` currently checks all paths before starting the lock — changing it to raise on first denied path means partial validation. If the first two paths are allowed but the third is denied, nothing is indexed. → **Mitigation**: Validate all paths before any indexing begins (pre-flight check pattern), or raise immediately on first violation (simpler, fail-fast). Choose fail-fast for security clarity.

- **Risk**: `_index_directory` recursively walks subdirectories. If a directory is authorized but contains a symlink to an external path, `_index_single_file` could follow it. → **Mitigation**: `authorize_path` resolves the symlink target via `Path.resolve()`. Each file indexed via `_index_single_file` must also pass `authorize_path`. Add explicit per-file authorization check in `_index_single_file` as defense-in-depth.
