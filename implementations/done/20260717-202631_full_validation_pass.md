# Implementation: full validation pass for plugin subsystem removal

Source plan: `plans/20260717-123416_plan.md` ("Remove plugin subsystem completely"), Implementation
step 9.

Cross-cutting slug used per this task's own instructions example — this step runs the repo's standard
validation sequence (`rules/toolchain.md`) plus a plugin-specific grep sweep; it is not tied to a
single source file, and it is the terminal step that depends on every other item in this plan (both
the already-covered items and the 8 sibling docs created alongside this one) having landed first.

## Goal

Run the standard validation sequence from `rules/toolchain.md` (ruff, mypy, lint-imports, ast-grep,
bandit, full pytest, diff-cover, pre-commit) plus a repo-wide `grep -rn "plugin"` sweep, to confirm the
plugin subsystem removal is complete and only intentional survivors remain (this plan's own commit
messages, or genuinely unrelated uses of the word "plugin" outside the subsystem, if any exist).

## Scope

**In scope**
- Execute every command in the plan's own Validation plan table (reproduced below) after all other
  Implementation steps (1-8) have landed.
- Triage any failure back to the specific implementation item (this doc's 8 siblings, or the
  already-covered/skipped items) whose change caused it.

**Out of scope**
- Fixing any *new* pre-existing failure unrelated to plugin removal (only regressions caused by this
  plan's changes are in scope to fix as part of this plan).

## Assumptions

1. This step is fully sequenced *after* every other item in the plan — Implementation steps 1-8,
   covering: consumer call-site removal (registry.py, tool_executor.py, factory.py, rag/pipeline.py,
   command_defs_list.py — already covered/skipped), subsystem file deletion (plugin_registry.py,
   plugin_tool_invoker.py, cmd_plugins.py — already covered/skipped; plugin_auto_discover.py,
   plugin_registries.py, plugin_result.py, plugin_conflicts.py — new docs in this batch), config
   surface removal (config_dataclasses.py, config_builders.py, config_reload.py,
   production_config_validator.py, config/agent.toml — already covered/skipped; config_validators.py —
   new doc in this batch), transport_dto.py doc-comment update (already covered/skipped), plugins/
   directory deletion (new doc in this batch), test file removal/trim (new doc in this batch),
   documentation removal/trim (new doc in this batch), and deploy.sh copy-list update (already
   covered/skipped).
2. "Already covered/skipped" items in this plan (per this task's filename-match rule against
   `implementations/` and `implementations/done/`) are assumed to have their own implementation
   procedures already on file from prior work; this validation pass does not re-derive them, only
   depends on their completion.
3. No new HIGH/MEDIUM bandit findings are expected from pure deletions and comment-only edits (the
   plan's own Validation plan table already states this expectation for the bandit check).

## Implementation

### Target file

None — this is a cross-cutting validation/CI step with no single target file. Its "inputs" are the
entire `scripts/`, `tests/`, `config/`, and `docs/` trees after all other items land.

### Procedure

Run, in order (per `rules/toolchain.md`'s standard validation sequence and the plan's own Validation
plan table):
1. `rg -n "plugin_registry\|plugin_auto_discover\|plugin_registries\|plugin_result\|plugin_tool_invoker\|plugin_conflicts\|PluginToolInvoker\|_PluginsMixin\|_dispatch_plugin" scripts/` → expect 0 matches.
2. `rg -n "\"/plugin\"" scripts/` → expect 0 matches.
3. `rg -n "plugin_strict\|plugin_tool_override" scripts/ config/` → expect 0 matches.
4. `uv run ruff format scripts/ tests/` then `uv run ruff check scripts/ tests/` → expect 0 errors.
5. `uv run mypy scripts/` → expect no new errors vs. pre-existing baseline.
6. `PYTHONPATH=scripts uv run lint-imports` → expect 0 violations (verify the import-layer contract in
   `.importlinter` is still satisfied: `shared` → external only; `db` → `shared`; `rag` → `db`,
   `shared`; `mcp_servers` → `db`, `shared`; `agent` → all layers — plugin removal should not have
   introduced any new cross-layer edge).
7. `uv run bandit -r scripts/ -c pyproject.toml` → expect no new HIGH/MEDIUM unaddressed findings.
8. `uv run vulture scripts/agent/commands/registry.py scripts/shared/tool_executor.py scripts/agent/factory.py --min-confidence 60` → expect no new "unused" hits from leftover fragments.
9. `uv run pytest tests/test_command_registry_dispatch.py tests/test_tool_executor.py tests/test_agent_factory.py tests/test_config_builders.py tests/test_config_reload.py -v` → expect all pass, no plugin-specific tests remain.
10. `uv run pytest -v` (full suite) → expect all pass, no new failures.
11. `uv run check-agent-docs` (if available per requirement 17) or manual review → expect no dangling
    plugin references in documentation.
12. `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` → expect >= 90% coverage
    on changed lines.
13. `uv run pre-commit run --all-files` → expect pass.
14. Final sweep: `grep -rn "plugin" scripts/ config/ tests/ docs/` → expect only intentional survivors
    (this plan's own commit messages/design docs, or genuinely unrelated non-subsystem uses of the
    word "plugin", if any exist).

### Method

Sequential command execution with a hard stop-and-fix-forward on any unexpected failure — each failure
should be triaged to the specific file/implementation item that caused it (see Assumptions #1 for the
full item list) rather than patched ad hoc in this validation step itself.

### Details

- This step has no code of its own; it is pure verification. If step 14's final grep sweep finds an
  unexpected survivor, the fix belongs in whichever sibling implementation item covers that file, not
  in this validation-pass step.
- `ast-grep` is listed in `rules/toolchain.md`'s standard sequence but has no plugin-specific
  invocation called out in the plan's own Validation plan table — run it per the toolchain's default
  ruleset as a standard part of the sequence; no plugin-specific `ast-grep` rule is defined by this
  plan.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| No remaining plugin imports | `rg -n "plugin_registry\|plugin_auto_discover\|plugin_registries\|plugin_result\|plugin_tool_invoker\|plugin_conflicts\|PluginToolInvoker\|_PluginsMixin\|_dispatch_plugin" scripts/` | 0 matches |
| No remaining `/plugin` command | `rg -n "\"/plugin\"" scripts/` | 0 matches |
| No remaining plugin config keys | `rg -n "plugin_strict\|plugin_tool_override" scripts/ config/` | 0 matches |
| Lint | `uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors vs. pre-existing baseline |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Security | `uv run bandit -r scripts/ -c pyproject.toml` | no new HIGH/MEDIUM unaddressed |
| Dead code | `uv run vulture scripts/agent/commands/registry.py scripts/shared/tool_executor.py scripts/agent/factory.py --min-confidence 60` | no new "unused" hits |
| Targeted tests | `uv run pytest tests/test_command_registry_dispatch.py tests/test_tool_executor.py tests/test_agent_factory.py tests/test_config_builders.py tests/test_config_reload.py -v` | all pass |
| Full suite | `uv run pytest -v` | all pass, no new failures |
| Doc consistency | `uv run check-agent-docs` or manual review | no dangling plugin references |
| Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | >= 90% on changed lines |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
| Final sweep | `grep -rn "plugin" scripts/ config/ tests/ docs/` | only intentional survivors |
