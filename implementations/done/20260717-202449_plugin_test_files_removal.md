# Implementation: remove/trim plugin-referencing test files

Source plan: `plans/20260717-123416_plan.md` ("Remove plugin subsystem completely"), Implementation
step 6.

Cross-cutting slug used because this item spans 22 test files (the plan's own prose says "21" but the
literal enumerated list totals 22 — see Assumptions #1) with two different dispositions (outright
delete vs. partial trim), not one target file.

## Goal

Remove test coverage for the deleted plugin subsystem: delete test files that are plugin-only outright,
and remove only the plugin-related test cases/fixtures from files that also test unrelated (surviving)
behavior — without losing any real non-plugin coverage.

## Scope

**In scope** — all 22 files below, confirmed to exist at the listed paths (verified via `find tests/`):

**Delete outright** (7 files, plugin-only per the plan's own Implementation step 6 text):
| File | Current size |
|---|---|
| `tests/test_plugin_registry.py` | 1011 lines |
| `tests/test_cmd_plugins.py` | 76 lines |
| `tests/test_plugin_contract.py` | 239 lines |
| `tests/test_plugin_ci_strict.py` | 77 lines |
| `tests/shared/test_plugin_tool_invoker.py` | 95 lines |
| `tests/shared/test_plugin_tool_registration.py` | 78 lines |
| `tests/test_dispatch_plugin_boundary.py` | 103 lines |

**Trim** (15 files — remove only plugin-specific cases/fixtures, keep the rest; plugin-mention line
counts below are from `grep -inc "plugin"` on each file, gathered during this doc's investigation, and
mark the *upper bound* of lines needing inspection, not necessarily all requiring deletion — some
matches may be in comments/docstrings only):
| File | plugin-matching lines (grep count) |
|---|---|
| `tests/test_config_dataclasses.py` | 7 |
| `tests/test_config_builders.py` | 1 |
| `tests/test_config_reload.py` | 13 |
| `tests/test_config_reload_classification.py` | 7 |
| `tests/test_tool_executor.py` | 24 |
| `tests/test_tool_executor_routing.py` | 13 |
| `tests/test_tool_executor_order.py` | 13 |
| `tests/test_agent_factory.py` | 3 |
| `tests/test_command_registry_dispatch.py` | 7 |
| `tests/test_cmd_audit.py` | 1 |
| `tests/test_tool_audit.py` | 3 |
| `tests/test_repl_health.py` | 8 |
| `tests/test_production_config_validator.py` | 9 |
| `tests/docs/test_command_docs_sync.py` | 4 |
| `tests/integration/test_agent_mcp_integration.py` | 8 |

**Out of scope**
- Any test file not in the two lists above.
- Non-plugin test cases within the 15 "trim" files — must be preserved exactly.

## Assumptions

1. The plan's prose says "21 plugin-referencing test files" but its own enumerated list (Affected
   areas table + Implementation step 6) contains 22 distinct paths. This doc uses the full 22-file list
   from direct enumeration; the discrepancy is a minor miscount in the plan's prose and does not change
   scope.
2. Per the plan's own Unknown #1: "Only import-level grep was run during planning; full file contents
   not read for all 21 [22]" — this doc's grep-count table above is itself still only an import/mention
   survey (not full-file reads), consistent with the plan's own acknowledged gap. The actual
   delete-vs-trim decision for each of the 15 "trim" files requires reading each file in full at
   implementation time, per the plan's own Risk mitigation ("Implementation Step 6 requires reading
   each file in full before deciding delete-vs-trim, not deleting based on filename/grep-hit alone").
   This doc records the starting point (which files, how many candidate lines) but explicitly defers
   the line-level edit decision to implementation time, as instructed by the plan itself.
3. `tests/test_plugin_registry.py` at 1011 lines is unusually large for a "delete outright" candidate —
   confirmed plugin-only disposition per the plan's own explicit categorization in Implementation step
   6; no further verification performed here beyond trusting the plan's categorization, since re-reading
   1011 lines is deferred to implementation time (this doc is a procedure document, not the edit
   itself).

## Implementation

### Target file

22 files across `tests/`, `tests/shared/`, `tests/docs/`, `tests/integration/` — see Scope tables
above for the full list and per-file disposition.

### Procedure

**Phase A — outright deletion (7 files):**
1. For each of the 7 "delete outright" files, confirm via `rg -c "def test_" <file>` that every test
   function in the file is plugin-related (spot-check function names for any non-plugin test that
   would need to be preserved elsewhere before deleting the file).
2. `git rm` each of the 7 files.

**Phase B — targeted trim (15 files):**
1. For each of the 15 files, read the file in full (not just the grep-matched lines) to identify exact
   test function boundaries, fixtures, and imports that are plugin-specific vs. shared with non-plugin
   tests.
2. Remove: (a) plugin-only test functions/classes in full, (b) plugin-only fixtures used by no
   surviving test, (c) plugin-only imports (e.g. `from shared.plugin_registry import ...`,
   `from shared.plugin_tool_invoker import ...`), (d) plugin-only parametrize cases within otherwise
   shared parametrized tests (edit the parameter list, not the whole test).
3. Re-run `rg -inc "plugin" <file>` after edits — expect 0 (or only incidental non-subsystem uses of
   the English word "plugin" that are genuinely unrelated, if any exist — none identified during this
   survey).

### Method

Straightforward removal/trim, no new logic introduced. Each trim is a subtraction: delete a test
function, its class if the class becomes empty, and any now-unused import/fixture. No production code
changes result from this step (test-only).

### Details

- `tests/test_tool_executor.py` has the highest trim burden (24 matching lines) — this correlates with
  `scripts/shared/tool_executor.py` being the file whose `PluginToolInvoker` import/instantiation/call
  site is removed by the separate, already-covered `tool_executor.py` implementation item; the test
  file's plugin-specific assertions (e.g. asserting the plugin short-circuit runs before MCP dispatch)
  must be removed in lockstep with that production change, or the test suite will fail against the new
  `ToolExecutor` behavior (MCP-only, no plugin short-circuit).
- `tests/docs/test_command_docs_sync.py` and `tests/integration/test_agent_mcp_integration.py` are
  cross-cutting integration/doc-sync tests — their plugin mentions likely reference the `/plugin`
  command's presence in `_COMMANDS` (removed by the sibling `command_defs_list.py` item) or doc
  cross-references (removed by the sibling documentation-removal item in this batch); these two files
  warrant particular care per the plan's own Risk section about adjacent non-plugin coverage sharing
  fixtures/module scope.
- No new test file is created — this step only subtracts.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No remaining plugin test files | `find tests/ -iname "*plugin*"` | 0 files (after Phase A) |
| No remaining plugin mentions in trimmed files | `rg -inc "plugin" tests/test_config_dataclasses.py tests/test_config_builders.py tests/test_config_reload.py tests/test_config_reload_classification.py tests/test_tool_executor.py tests/test_tool_executor_routing.py tests/test_tool_executor_order.py tests/test_agent_factory.py tests/test_command_registry_dispatch.py tests/test_cmd_audit.py tests/test_tool_audit.py tests/test_repl_health.py tests/test_production_config_validator.py tests/docs/test_command_docs_sync.py tests/integration/test_agent_mcp_integration.py` | 0 matches per file (or only genuinely unrelated non-subsystem uses, if any) |
| Targeted tests | `uv run pytest tests/test_command_registry_dispatch.py tests/test_tool_executor.py tests/test_agent_factory.py tests/test_config_builders.py tests/test_config_reload.py -v` | all pass, no plugin-specific tests remain |
| Full suite | `uv run pytest -v` | all pass, no new failures, coverage not meaningfully reduced for surviving (non-plugin) code paths |
| Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | >= 90% on changed lines |
