# Implementation: delete the `plugins/` directory

Source plan: `plans/20260717-123416_plan.md` ("Remove plugin subsystem completely"), Implementation
step 5.

Cross-cutting slug used because this item deletes a directory (not a single Python module under
`scripts/`) and also touches `deploy/deploy.sh`'s copy-list.

## Goal

Delete the top-level `plugins/` directory, which today contains only `example.py` (an inert template,
2026 bytes, dated 2026-07-06) and a `__pycache__/` directory — no production plugin exists in this
codebase (plan Assumption 1).

## Scope

**In scope**
- Delete `plugins/example.py` and `plugins/__pycache__/` (and the now-empty `plugins/` directory
  itself).
- Confirm `deploy/deploy.sh`'s `plugins/` copy-list block (lines 76-79, see Affected/Deploy impact in
  the plan) is updated or removed to match — this sub-step is cross-referenced here but the actual
  `deploy.sh` edit is covered by the separate, already-covered `deploy.sh` implementation item (matches
  existing `implementations/done/*deploy_sh*` docs); this doc only records what that edit must account
  for regarding the `plugins/` directory specifically.

**Out of scope**
- Any change to how MCP servers or `RuntimeToolRegistry` provide tools going forward (requirement 02).

## Assumptions

1. Per plan Assumption 1: `plugins/` contains only `example.py` (a template, explicitly documented in
   its own docstring as inactive unless manually placed there and the agent restarted — "To activate:
   place the file in plugins/ and restart the agent. To deactivate: remove or rename the file") and
   `__pycache__/`. Confirmed by direct listing: `plugins/` has exactly two entries, `example.py` and
   `__pycache__/`.
2. `example.py` imports `from shared.plugin_registry import (register_command, register_pipeline_stage,
   register_tool)` — since `plugin_registry.py` is deleted by a sibling (already covered/skipped) item
   in this same plan, `example.py` would be left with a dangling import if not deleted in the same
   batch; deleting the whole directory (rather than leaving `example.py` in place) avoids this.
3. `deploy/deploy.sh` currently has, at lines 76-79: a `echo "--- plugins/ → /opt/llm/plugins/ ---"`
   line, `mkdir -p /opt/llm/plugins`, and `cp -n "${REPO_ROOT}/plugins/"*.py /opt/llm/plugins/ 2>/dev/null
   || true` — confirmed by direct read. Whether `plugins/` remains a deployed directory (per the plan's
   "Deploy impact" note asking to "confirm during implementation whether `plugins/` itself is a
   deployed directory") is resolved: yes, it is copied today, so this deploy block must be removed
   entirely once `plugins/` no longer exists in the repo, not merely left pointing at an empty source
   directory.

## Implementation

### Target file

`plugins/` (directory: `plugins/example.py`, `plugins/__pycache__/`) — delete in full.

### Procedure

1. Delete the directory: `git rm -r plugins/` (this removes `example.py`; `__pycache__/` is typically
   already untracked/gitignored — confirm via `git status plugins/` before deleting and clean up any
   untracked `__pycache__/` remnants with a plain `rm -rf plugins/__pycache__` if `git rm -r` does not
   remove it because it was never tracked).
2. Confirm the directory no longer exists: `test -d plugins/ && echo STILL_EXISTS || echo REMOVED`.
3. Cross-check `deploy/deploy.sh` lines 76-79 (the `plugins/` copy block) — this specific removal is
   performed by the separate `deploy.sh` implementation item, but must not be skipped: after this
   directory deletion, `deploy.sh`'s `cp -n "${REPO_ROOT}/plugins/"*.py ...` line would silently no-op
   (source directory doesn't exist) rather than fail loudly, so the dead deploy step should still be
   removed for cleanliness per the plan's "Deploy impact" note.
4. Re-run `rg -rn "plugins/" scripts/ deploy/ docs/` (excluding this plan's own text) to confirm no
   remaining references to the deleted directory as a runtime path.

### Method

Pure directory/file deletion — no code transformation. The only "logic" is the pre/post-deletion
verification in steps 2-4.

### Details

- `example.py`'s docstring documents the plugin activation contract being removed: "Copy this file and
  rename it ... to create a new plugin. Each `@register_*` decorator runs at import time when
  `load_plugins()` loads the file." This is the last artifact describing that contract in the
  filesystem (dedicated docs describing it in `docs/` are handled by the separate documentation-removal
  item in this batch).
- No config key (`config/agent.toml`'s `plugin_tool_override`/`plugin_strict`, removed by a sibling
  already-covered item) points at this directory by path — the plugin directory path itself is
  hardcoded as `plugins/` at the `load_plugins()` call site in `factory.py` (removed by the sibling
  `factory.py` item), not read from config.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Directory removed | `test -d plugins/ && echo FAIL || echo OK` | `OK` |
| No remaining path references | `rg -rn "plugins/" scripts/ deploy/ docs/` | 0 matches (aside from this plan's own artifacts) |
| Deploy script consistency | manual review of `deploy/deploy.sh` after the sibling `deploy.sh` item lands | no `plugins/` copy block remains |
| Full suite | `uv run pytest -v` | all pass |
