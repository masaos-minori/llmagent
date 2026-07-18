# Implementation procedure: full validation pass — `/mcp tools` diagnostics

Source plan: `plans/done/20260717-130901_plan.md` (requirement `requires/20260717_11_require.md`),
Implementation step 6.

## Goal

Run the standard validation sequence (`rules/toolchain.md`) scoped to the files touched by this
requirement's three implementation docs — `scripts/agent/commands/cmd_mcp.py`, `tests/test_cmd_mcp.py`,
`tests/test_command_def_sync.py` — then the full suite, to confirm the new `/mcp tools` diagnostic
subcommand introduces zero regressions and satisfies its own acceptance criteria (7 fields shown,
disabled/policy-filtered tools visible, no schema/raw-definition leakage).

This doc is intentionally scoped to *this* requirement only — per the batch-wide note that the generic
`full_validation_pass` slug has been reused by multiple unrelated plans in this migration batch (confirmed
by direct read of both existing `implementations/*full_validation_pass*.md` docs:
`20260717-202631_full_validation_pass.md` covers the plugin-subsystem-removal plan;
`20260718-032349_full_validation_pass.md` covers a documentation/comment-only requirement — neither names
`/mcp tools` or `RuntimeToolRegistry` diagnostics anywhere in its Goal). Neither is reusable for this
plan's validation step; this doc is the scoped, disambiguated equivalent for requirement 11.

## Scope

**In scope**
- Format/lint/type-check/import-boundary/security checks on the 3 touched files.
- `uv run pytest tests/test_cmd_mcp.py tests/test_command_def_sync.py -v` (targeted), then
  `uv run pytest -v` (full suite).
- `uv run pre-commit run --all-files`.
- Manual confirmation of output conciseness (no `input_schema`/`raw_definition` in the default table).

**Out of scope**
- Validating `scripts/shared/runtime_tool.py` / `scripts/shared/runtime_tool_registry.py` /
  `scripts/agent/context.py`'s `AppServices.runtime_tools` wiring themselves — those are other
  requirements' own validation responsibility (see this batch's per-file docs, e.g.
  `implementations/20260717-203121_runtime_tool.py.md`, `implementations/20260717-203200_runtime_tool_registry.py.md`).
  This doc only validates that *this requirement's* consumer code, once those prerequisites exist, is
  correct and non-regressive.
- `diff-cover` gating on unrelated pre-existing coverage gaps elsewhere in the repo.

## Assumptions

1. This validation step cannot be executed as a live pass-through run **until** the blocking prerequisite
   identified in `implementations/20260718-032912_cmd_mcp.py.md`'s Assumption 1 lands
   (`AppServices.runtime_tools: RuntimeToolRegistry | None` must exist in real `scripts/agent/context.py`,
   and `scripts/shared/runtime_tool_registry.py` must exist) — otherwise `mypy`/`pytest` on `cmd_mcp.py`
   and its tests will fail on a genuinely missing import/attribute, not on a defect in this requirement's
   own logic. This doc documents the validation *procedure*; actually running it to a real pass/fail
   result is deferred until that prerequisite is confirmed landed.
2. Per `rules/toolchain.md`, the standard sequence order is: `ruff format` → `ruff check` → `mypy` →
   `lint-imports` → `ast-grep` (bare-except constraint) → `bandit` → `pytest` → `diff-cover` →
   `pre-commit run --all-files`.

## Implementation

### Target file

N/A — this is a validation/verification artifact, not a source-file change. It consumes the outputs of
`implementations/20260718-032912_cmd_mcp.py.md`, `implementations/20260718-032956_test_cmd_mcp.py.md`, and
`implementations/20260718-033035_test_command_def_sync.py.md`.

### Procedure

1. Confirm the blocking prerequisite (Assumption 1) is landed: `grep -n "runtime_tools" scripts/agent/context.py`
   returns a match, and `scripts/shared/runtime_tool_registry.py` exists.
2. Run format/lint/type/import/security checks scoped to the 3 touched files (see Details).
3. Run `uv run pytest tests/test_cmd_mcp.py tests/test_command_def_sync.py -v` — targeted pass.
4. Run `uv run pytest -v` — full suite, confirm no new failures anywhere else (e.g. no other test imports
   `_cmd_mcp`'s old 2-tuple `UnknownSubcommandError` allowed-set literally).
5. Run `uv run pre-commit run --all-files`.
6. Manually invoke `/mcp tools` in a REPL session (or an equivalent scripted harness) against a context with
   a populated `RuntimeToolRegistry` containing at least one disabled/policy-filtered tool; visually confirm
   all 7 fields render and no `input_schema`/`raw_definition` JSON appears.

### Method

Command-line validation sequence, no code produced by this item.

### Details

```
uv run ruff format scripts/agent/commands/cmd_mcp.py tests/test_cmd_mcp.py tests/test_command_def_sync.py
uv run ruff check   scripts/agent/commands/cmd_mcp.py tests/test_cmd_mcp.py tests/test_command_def_sync.py
uv run mypy scripts/agent/commands/cmd_mcp.py
PYTHONPATH=scripts uv run lint-imports
uv run bandit -r scripts/agent/commands/cmd_mcp.py -c pyproject.toml
ast-grep --pattern 'except: $$$' --lang python scripts/agent/commands/cmd_mcp.py
uv run pytest tests/test_cmd_mcp.py tests/test_command_def_sync.py -v
uv run pytest -v
uv run pre-commit run --all-files
```

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Prerequisite landed | `grep -n "runtime_tools" scripts/agent/context.py` | at least one match before running the rest of this doc |
| Lint/format | `uv run ruff format`/`ruff check` (scoped files) | 0 errors |
| Type check | `uv run mypy scripts/agent/commands/cmd_mcp.py` | 0 errors |
| Import boundary | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Security | `uv run bandit -r scripts/agent/commands/cmd_mcp.py -c pyproject.toml` | 0 high/medium |
| Targeted tests | `uv run pytest tests/test_cmd_mcp.py tests/test_command_def_sync.py -v` | all pass |
| Full suite | `uv run pytest -v` | no new failures |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
| Manual output review | run `/mcp tools` | 7 fields shown, disabled tools visible, no raw schema/definition leakage |
