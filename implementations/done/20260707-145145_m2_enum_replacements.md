# Implementation: M-2 — Replace string literals with enum comparisons (4 files)

## Goal

Replace all `cfg.transport == "http"` and `cfg.startup_mode == "subprocess"` string
literal comparisons with `TransportType.HTTP` and `StartupMode.SUBPROCESS` enum members
across `factory.py`, `startup.py`, `repl_health.py`, and `mcp_status.py`.
No behavior change — `TransportType` and `StartupMode` are `StrEnum` so equality holds.

## Scope

**Targets** (all 4 files in one pass):
- `scripts/agent/factory.py`
- `scripts/agent/startup.py`
- `scripts/agent/repl_health.py`
- `scripts/agent/services/mcp_status.py`

**Steps covered**: Plan M-2 steps 1–4.

**Out of scope**: `mcp_config.py` (no change), test files (StrEnum equality preserved).

## Assumptions

1. `TransportType` and `StartupMode` are `StrEnum` (confirmed: `mcp_config.py` lines
   23–34). Runtime equality is unchanged.
2. All import lines for `shared.mcp_config` exist in the 4 files; only extend the
   `import from` clause.
3. Negative comparisons (`!= "subprocess"`) use `!= StartupMode.SUBPROCESS`.

## Implementation

### Target files

All 4 source files; one logical change per file.

### Procedure

#### File 1: `scripts/agent/factory.py`

**Import change**: extend existing `from shared.mcp_config import McpServerConfig` to:
```python
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
```

**Line ~60** (`ensure_ready()`):
```python
# Before
if cfg.transport == "http" and cfg.startup_mode == "subprocess":
# After
if cfg.transport == TransportType.HTTP and cfg.startup_mode == StartupMode.SUBPROCESS:
```

**Line ~75** (`restart()`):
```python
# Before
if cfg is None or cfg.startup_mode != "subprocess":
# After
if cfg is None or cfg.startup_mode != StartupMode.SUBPROCESS:
```

Verify with `grep -n '"http"\|"subprocess"' scripts/agent/factory.py` — should return 0.

#### File 2: `scripts/agent/startup.py`

**Import change**: add to existing imports:
```python
from shared.mcp_config import StartupMode, TransportType
```

**Line ~109** (`_start_servers()`):
```python
# Before
if cfg.startup_mode == "subprocess" and cfg.transport == "http":
# After
if cfg.startup_mode == StartupMode.SUBPROCESS and cfg.transport == TransportType.HTTP:
```

Verify with `grep -n '"subprocess"\|"http"' scripts/agent/startup.py` — should return 0.

#### File 3: `scripts/agent/repl_health.py`

**Import change**: extend existing `shared.mcp_config` import to include `TransportType, StartupMode`.

**Lines ~188, 235, 642, 682** (all `== "http"` comparisons):
```python
# Before
cfg.transport == "http"
# After
cfg.transport == TransportType.HTTP
```

**Line ~600** (`== "subprocess"` comparison):
```python
# Before
cfg.startup_mode == "subprocess"
# After
cfg.startup_mode == StartupMode.SUBPROCESS
```

Verify: `grep -n '"http"\|"subprocess"' scripts/agent/repl_health.py` — should return 0.

#### File 4: `scripts/agent/services/mcp_status.py`

**Import change**: add `from shared.mcp_config import TransportType` (or extend existing).

**Line ~100**:
```python
# Before
if cfg.transport == "http":
# After
if cfg.transport == TransportType.HTTP:
```

Verify: `grep -n '"http"' scripts/agent/services/mcp_status.py` — should return 0 for transport comparisons.

### Method

- Run `grep -rn 'cfg\.transport == "http"\|cfg\.startup_mode == "subprocess"' scripts/`
  after all edits to confirm zero remaining string comparisons.
- Each edit is a surgical token swap; no structural changes.

### Details

- The exact line numbers (60, 75, 109, 188, 235, 600, 642, 682) are approximate;
  verify by reading each file before editing in case prior plans (H-4, H-9) shifted lines.
- After H-4 (`ensure_ready()` update), the `"http"`/`"subprocess"` comparisons in
  `factory.py` may already have been replaced. Check before editing.
- `mcp_status.py` may have multiple `"http"` occurrences as URL scheme strings (e.g.
  `url.startswith("http")`); only replace `cfg.transport == "http"` comparisons.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check scripts/` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Architecture | `lint-imports` | 0 violations |
| Grep audit | `grep -rn 'cfg\.transport == "http"\|cfg\.startup_mode == "subprocess"' scripts/` | 0 matches |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
