# Implementation Procedure: Remove the MCP Watchdog Feature (Health Polling + Auto-Restart Loop)

Source plan: `plans/20260716-144940_plan.md`
Source requirement: `requires/20260716_20_require.md`

## Goal

Remove the MCP watchdog (background health-poll + auto-restart loop) and every config key, display line, test, and doc that exists solely to support it, while leaving the independent `/health` endpoint / `HealthRegistry` / `/mcp status` probing path fully intact.

## Scope

**In scope**
- Delete watchdog loop/check/classify functions from `scripts/agent/repl_health.py` and their start/stop/call-site wrappers in `scripts/agent/repl.py`.
- Delete the two `MCPConfig.mcp_watchdog_*` fields, their builder resolution, their `/reload` application, their `/config` display lines, and their `/mcp status` display block.
- Delete `McpServerHealthRegistry.record_restart_exhausted()` (watchdog-only production caller).
- Delete the two `mcp_watchdog_*` keys from `config/agent.toml`.
- Delete the `check_watchdog_restarts_on_dependency_failure()` doc-consistency check, its regex constant, its `--skip watchdogrestart` flag, and its call site in `tools/check_mcp_docs_consistency.py`.
- Delete/trim watchdog-specific tests across 13 test files (see Implementation → Details for the exact list).
- Rewrite or trim watchdog content across 25 documentation files: one full removal-note rewrite (`04_mcp_06_12`), two targeted partial edits (`04_mcp_06_13` part1/part2), one section removal (`04_mcp_03_04`), and 21 incidental-mention cleanups.

**Out of scope**
- `/health` endpoint, `McpServerHealthRegistry` state machine (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN), `McpStatusService.probe_all()` — unchanged, independent of the watchdog.
- `record_success()` / `record_failure()` / `record_degraded()` / `get_degraded_reason()` on `McpServerHealthRegistry` — used by the transport-error path too, not watchdog-only.
- Subprocess lifecycle management (`start_http_subprocess()`, `ensure_ready()`, manual `/mcp restart`) — only the watchdog's automatic trigger of `lifecycle.restart()` is removed.
- Any change to production process-supervision (systemd, container healthcheck) — explicitly out of scope; see Risks.

## Assumptions

1. No module besides `scripts/agent/repl.py` and its own tests imports `watchdog_loop`, `_watchdog_check_http`, or `_classify_health_failure` (confirmed via `grep -rn "_classify_health_failure\|watchdog_loop\|_watchdog_check_http" scripts/`).
2. `record_restart_exhausted()` has exactly one production caller (`repl_health.py`, inside `_watchdog_check_http`); once the watchdog is removed it becomes dead code and is deleted along with its 3 dedicated tests.
3. `tests/test_config_reload.py` and `tests/test_config_reload_classification.py` do not reference `mcp_watchdog_*` — no change needed there.
4. `deploy/deploy.sh` has no watchdog-specific logic — no copy-list change needed; this is a same-file-set removal.
5. This repo's established convention for a fully-removed feature is a short, dated resolution note (as in `implementations/done/20260629-185000_mdq_stub_language_removal.md`) rather than silent deletion of all doc trace — applied only to `04_mcp_06_12` (confirmed 100% watchdog content); the other 24 doc files get targeted edits, not removal notes, since they carry substantial non-watchdog content.

## Implementation

### Target file

Multiple files across `scripts/agent/`, `scripts/shared/`, `config/`, `tools/`, `tests/`, and `docs/` — grouped below by phase. This is a single cohesive subtractive change; no new module is created.

### Procedure

**Phase 1 — Core removal (agent/shared layer)**
1. Delete `watchdog_loop()`, `_watchdog_check_http()`, `_classify_health_failure()` from `scripts/agent/repl_health.py`.
2. Delete `_watchdog_loop()`, `_start_watchdog()`, `_stop_watchdog()`, the `watchdog_loop` import, and their call sites in `_run_repl_loop()` in `scripts/agent/repl.py`.
3. Delete `record_restart_exhausted()` from `scripts/shared/mcp_health.py`.
4. Run `PYTHONPATH=scripts uv run lint-imports` to confirm no boundary regressions.

**Phase 2 — Configuration surface**
1. Delete `mcp_watchdog_interval` / `mcp_watchdog_max_restarts` fields from `MCPConfig` in `scripts/agent/config_dataclasses.py`; update the class/module docstring (no longer "watchdog settings").
2. Delete `watchdog_interval_default` resolution and the two kwargs passed into `MCPConfig(...)` in `scripts/agent/config_builders.py`.
3. Delete `_apply_mcp_watchdog_params()` and its call site in `scripts/agent/services/config_reload.py`; update `_apply_rag_tool_params()`'s docstring.
4. Delete `mcp_watchdog_interval` / `mcp_watchdog_max_restarts` from `config/agent.toml`.

**Phase 3 — Display / status surface**
1. Delete the 2 watchdog lines from `_print_mcp_settings()` in `scripts/agent/commands/cmd_config_display.py`.
2. Delete the `Watchdog` status line and `wd_interval`/`wd_max`/`wd_status` block from `scripts/agent/commands/cmd_mcp.py`.

**Phase 4 — Doc-consistency tooling**
1. Delete `check_watchdog_restarts_on_dependency_failure()`, its regex constant, the `watchdogrestart` skip-flag registration, its call site, and the `--skip watchdogrestart` help line from `tools/check_mcp_docs_consistency.py`.

**Phase 5 — Tests**
1. Delete `tests/test_watchdog.py` entirely.
2. Delete `TestClassifyHealthFailure` from `tests/test_repl_health.py`.
3. Delete from `tests/test_mcp_health_degraded.py`: `test_classify_health_failure_all_five_cases`; `test_record_restart_exhausted_sets_reason`, `test_record_restart_exhausted_does_not_change_state`, `test_record_restart_exhausted_overwrites_prior_reason`; `test_watchdog_reachable_not_restart_calls_record_degraded`, `test_watchdog_reachable_restart_does_not_call_record_degraded`, `test_watchdog_unreachable_calls_record_failure`, `test_watchdog_no_registry_no_error`, `test_watchdog_malformed_json_calls_record_degraded_with_reason`, `test_watchdog_degraded_with_restart_recommended_true_no_record_degraded`.
4. Drop the `mcp_watchdog_*` fixture lines/assertions from `tests/test_cmd_mcp.py`, `test_config_builders.py`, `test_agent_cmd_config.py`, `test_cmd_config_char.py`, `test_llm_client.py`, `test_tool_approval_repos.py`, `test_tool_approval_paths.py`, `test_tool_approval_preflight.py`, `test_tool_approval_risk.py`, `test_tool_audit.py`, `test_cmd_registry_note_removal.py`.
5. Delete the `check_watchdog_restarts_on_dependency_failure` import and its 2 tests from `tests/test_check_mcp_docs_consistency.py`.
6. Run `uv run pytest -q`; confirm `grep -rn "watchdog" tests/` returns empty.

**Phase 6 — Documentation sweep**
1. Rewrite `docs/04_mcp_06_12_watchdog-configuration-monitoring.md` as a short dated removal note ("MCP watchdog was removed on 2026-07-16; see `requires/done/20260716_20_require.md`").
2. Edit `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part1.md`: remove only the "watchdogのロギング動作" subsection and the `restart_limit_reached` table row; keep the general `health_reason`/`HealthRegistry` content; retitle away from "Watchdog Behavior".
3. Edit `docs/04_mcp_06_13_watchdog-health-reasons-scheduling-part2.md`: remove/reword the 2 watchdog-referencing sentences in "ツールエラーの監視" and "ツールのスケジューリングと直列化"; keep the rest; retitle away from "Watchdog Behavior".
4. Remove the "## ウォッチドッグ" section from `docs/04_mcp_03_04_tool-call-tracing-and-watchdog.md`; keep transport-error-tracing content; reconsider filename/title.
5. Strip incidental watchdog mentions from the remaining 21 docs listed in the source plan's Affected areas table.
6. Update any `related:` front-matter lists / cross-links pointing at a renamed/edited doc.
7. Run `grep -rl watchdog docs/` and confirm only the intentional removal-note pages remain.

**Phase 7 — Full validation**
1. Run the standard sequence from `rules/toolchain.md` (ruff, mypy, lint-imports, ast-grep, bandit, full pytest, diff-cover, pre-commit).
2. Run `uv run check-mcp-docs` and confirm no dangling `watchdogrestart` skip-flag reference.

### Method

- Direct source/test/doc file edits and deletions (git-tracked removal, not soft-disable).
- Each phase is independently committable and leaves the tree in a fully testable state — no phase depends on a later phase to compile or pass tests.
- Documentation edits distinguish full removal-note rewrite (only for pages confirmed 100% watchdog content) from targeted partial edits (pages with substantial non-watchdog content) — do not apply a removal note where a partial edit is correct.

### Details

- Do not modify `McpServerHealthRegistry`'s state machine, `record_success`/`record_failure`/`record_degraded`/`get_degraded_reason`, the `/health` endpoint, or `McpStatusService.probe_all()` — these have callers independent of the watchdog.
- Do not touch `deploy/deploy.sh` — no file add/remove requiring a copy-list change.
- After Phase 1–5, run `grep -rn "watchdog\|_classify_health_failure\|record_restart_exhausted" tests/` and confirm it returns empty before proceeding to Phase 6.
- High-churn risk: `repl_health.py` (42 commits/30d) and `repl.py` (38 commits/30d) — rebase immediately before merging; do not bundle with unrelated edits to these files.
- Removing the watchdog removes the only automatic recovery path for a crashed subprocess-mode MCP server; document the new manual-recovery expectation (`/mcp restart` or process restart) in the Phase 6 doc sweep — do not silently drop this operational consequence.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| No remaining watchdog references in source/config/tools | `grep -rn "watchdog" scripts/ config/ tools/` | 0 matches |
| Lint | `uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors vs. pre-existing baseline |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| No bare except / dead patterns | `ast-grep --pattern 'except: $$$' --lang python scripts/` | 0 matches |
| Security | `uv run bandit -r scripts/ -c pyproject.toml` | no new HIGH/MEDIUM unaddressed |
| Dead code | `uv run vulture scripts/agent/repl_health.py scripts/agent/repl.py scripts/shared/mcp_health.py --min-confidence 60` | no new "unused" hits from leftover fragments |
| Targeted tests | `uv run pytest tests/test_repl_health.py tests/test_mcp_health_degraded.py tests/test_cmd_mcp.py tests/test_config_builders.py tests/test_check_mcp_docs_consistency.py -v` | all pass, watchdog-specific tests absent |
| Full suite | `uv run pytest -q` | all pass, no new failures |
| Doc consistency | `uv run check-mcp-docs` | passes, no `watchdogrestart` check remaining |
| Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
