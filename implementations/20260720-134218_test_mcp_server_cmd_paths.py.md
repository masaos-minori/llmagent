# Implementation procedure: `tests/test_mcp_server_cmd_paths.py` (new file — cmd-path regression guard)

Source plan: `plans/20260720-073534_plan.md`, Implementation step Phase 2 (resolves UNK-01).

## Goal

Resolve the plan's UNK-01 (standalone new test file vs. extending an existing config test file) and
add a regression test asserting every `startup_mode="subprocess"` MCP server's `cmd` script path
actually exists on disk — the exact invariant the `server.py`→`<name>_server.py` bug violated.

## Scope

**In scope**
- UNK-01 resolution: read `tests/test_mcp_config_validation.py` (171 lines) and
  `tests/test_agent_cmd_config.py` (579 lines) in full, per the plan's own instruction, before deciding.
- New file `tests/test_mcp_server_cmd_paths.py`, built against the REAL `config/agent.toml` via
  `scripts/agent/config_builders.py::build_agent_config()` (not a hand-built/synthetic config), per the
  plan's Design §2 preference.

**Out of scope**
- No change to `tests/test_mcp_config_validation.py` or `tests/test_agent_cmd_config.py` themselves.
- No change to `scripts/shared/mcp_config.py`, `scripts/agent/config_builders.py`, or
  `scripts/agent/http_lifecycle.py` — all already correct; this is test-only.

## Assumptions

1. **UNK-01 resolved: neither existing candidate file fits; create a new dedicated file.**
   - `tests/test_mcp_config_validation.py` (verified, read in full): every test builds a synthetic
     `McpServerConfig` via local `_http_cfg()`/`_subprocess_cfg()` helpers with fake values (e.g.
     `cmd=["./run.sh"]`) — it never loads the real `config/agent.toml`. Adding a real-file-parsing test
     here would break the file's established synthetic-fixture convention.
   - `tests/test_agent_cmd_config.py` (verified, read in full): despite the name, this file tests the
     REPL's `/config` slash-command (`_ConfigMixin._cmd_stats`, SSE hot-reload) — "cmd" here means
     "CLI command," an unrelated meaning from the `McpServerConfig.cmd` subprocess-argv field. Wrong
     file entirely, not a naming coincidence to build on.
   - Per the plan's own UNK-01 default ("a new dedicated file is a safe default if neither existing
     file fits"), create `tests/test_mcp_server_cmd_paths.py`.
2. **Real-config construction path, verified by reading source**: `scripts/agent/config_builders.py`'s
   `build_agent_config(cfg_override=None)` calls `load_config()` (→ `ConfigLoader().load_all()`) when no
   override is given; `ConfigLoader()`'s default `config_dir` is `repo_root / "config"`
   (`scripts/shared/config_loader.py:53`, `repo_root = Path(__file__).resolve().parent.parent.parent`)
   — i.e. the actual repo `config/` directory, not a fixture. `build_agent_config()` then calls
   `_build_mcp_servers(cfg)` (`scripts/shared/mcp_config.py:129`), which returns
   `dict[str, McpServerConfig]` with `startup_mode` already coerced to the `StartupMode` enum and `cmd`
   as the literal `list[str]` from the TOML (`_build_single_server`, verified: no path transformation is
   applied to `cmd` — it is stored as read, e.g. `.../opt/llm/scripts/mcp_servers/web_search/web_search_server.py`).
   No existing test currently calls `build_agent_config()` with no override against the real config —
   this is a novel but straightforward use of an existing, unmodified function.
3. **Path-mapping is unavoidable and must be explicit**: `cmd`'s last element is always an absolute
   deploy-target path under `/opt/llm/scripts/...` (per `deploy/deploy.sh`'s `DEPLOY_SCRIPTS=/opt/llm/scripts`
   convention), not a repo-relative path — there is no existing ConfigLoader helper that maps this back to
   the repo's own `scripts/` directory (verified: `_build_single_server` does no such transformation).
   The test must do this mapping itself: replace the literal `/opt/llm/scripts/` prefix with this repo's
   own `scripts/` directory path (computed the same way `config_loader.py` computes `repo_root`, i.e.
   `Path(__file__).resolve().parent.parent`, since the test file lives directly under `tests/`).
4. `file_delete`/`file_write`/`file_read` (`mcp_servers.file_delete` etc., keys per `config/agent.toml`)
   also use `startup_mode="subprocess"` with `cmd` paths like `.../file/delete_server.py` — these already
   exist on disk (unaffected by the rename) and will simply pass the new assertion; no special-casing
   needed to exclude them.

## Implementation

### Target file

`tests/test_mcp_server_cmd_paths.py` (new)

### Procedure

1. Import `build_agent_config` from `agent.config_builders`.
2. Call `cfg = build_agent_config()` (no override — loads the real `config/agent.toml` + associated
   `*_mcp_server.toml` files).
3. Iterate `cfg.mcp_servers.items()`; filter to `server_cfg.startup_mode == StartupMode.SUBPROCESS`.
4. For each, take `server_cfg.cmd[-1]` (the script path argument), replace the `/opt/llm/scripts/`
   prefix with this repo's own `scripts/` directory (`Path(__file__).resolve().parent.parent / "scripts"`),
   and assert the resulting path exists via `Path.is_file()`.
5. Write the test so that failure names the offending server key and the missing path in the assertion
   message (e.g. `f"mcp_servers.{key}: cmd script {script_path} does not exist"`), so a future regression
   is immediately actionable, not a bare `assert False`.
6. Before finalizing, confirm the test would have failed against the pre-fix config: temporarily revert
   one `config/agent.toml` `cmd` entry (e.g. `git stash` the Phase-1 edit, or hand-edit one line back to
   bare `server.py`), re-run, confirm failure, then restore the fix and confirm the test passes. This
   proves the test is not vacuous, per the plan's own Design §2 instruction.

### Method

```python
"""tests/test_mcp_server_cmd_paths.py

Regression guard: every subprocess-mode MCP server's cmd script path must
exist on disk. Added after config/agent.toml's cmd entries silently pointed
at server.py files deleted by an earlier MCP-server rename cleanup.
"""

from __future__ import annotations

from pathlib import Path

from agent.config_builders import build_agent_config
from shared.mcp_config import StartupMode

_REPO_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
_DEPLOY_SCRIPTS_PREFIX = "/opt/llm/scripts/"


def _repo_relative_cmd_path(cmd: list[str]) -> Path:
    script_arg = cmd[-1]
    assert script_arg.startswith(_DEPLOY_SCRIPTS_PREFIX), (
        f"expected cmd's last element to start with {_DEPLOY_SCRIPTS_PREFIX!r}, got {script_arg!r}"
    )
    return _REPO_SCRIPTS_DIR / script_arg[len(_DEPLOY_SCRIPTS_PREFIX) :]


class TestSubprocessServerCmdPathsExist:
    def test_every_subprocess_cmd_script_exists(self) -> None:
        cfg = build_agent_config()
        subprocess_servers = {
            key: server_cfg
            for key, server_cfg in cfg.mcp_servers.items()
            if server_cfg.startup_mode == StartupMode.SUBPROCESS
        }
        assert subprocess_servers, "expected at least one subprocess-mode MCP server in config"

        missing = []
        for key, server_cfg in subprocess_servers.items():
            script_path = _repo_relative_cmd_path(server_cfg.cmd)
            if not script_path.is_file():
                missing.append(f"mcp_servers.{key}: cmd script {script_path} does not exist")

        assert not missing, "\n".join(missing)
```

(Pseudocode/sketch — verify exact `AgentConfig`/`McpServerConfig` attribute names against current source
at implementation time before finalizing.)

### Details

- Assumption 3's prefix-replace is intentionally explicit and asserted (not silently skipped) — if a
  future config ever uses a `cmd` path NOT under `/opt/llm/scripts/`, the test fails loudly rather than
  silently passing on an unchecked path, per the plan's Risk about the fragile path-mapping assumption.
- Do not special-case `file_delete`/`file_write`/`file_read` — they satisfy the same assertion without
  modification, keeping the test uniform across all subprocess-mode servers.
- No production code is touched — this document's file list is entirely test-only.

## Validation plan

| Check | Command | Target |
|---|---|---|
| New test (post-fix) | `uv run pytest tests/test_mcp_server_cmd_paths.py -v` | passes |
| New test (pre-fix, temporary) | revert one `config/agent.toml` cmd entry, re-run, then restore | fails with an actionable message naming the server key |
| Regression check | `uv run pytest tests/test_mcp_config_validation.py tests/test_agent_cmd_config.py tests/test_mcp_config.py -v` | unaffected, all pass |
| Format/lint | `uv run ruff format tests/test_mcp_server_cmd_paths.py && uv run ruff check tests/test_mcp_server_cmd_paths.py` | 0 errors |
| Type check | `uv run mypy scripts/` (tests/ covered by pre-commit's mypy run per `rules/coding.md`) | 0 new errors |
| Full suite | `uv run pytest -q` | no new failures |
