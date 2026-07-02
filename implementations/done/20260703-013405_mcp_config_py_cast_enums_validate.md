# Implementation: scripts/shared/mcp_config.py — Resolve UNK-03 and Remove _cast_enums

**Plan source:** `plans/20260702-202739_plan.md` (Phase 1 + Phase 5)
**Target file:** `scripts/shared/mcp_config.py`

---

## Goal

Verify that no test directly exercises `_cast_enums` with raw strings (Phase 1 UNK-03 resolution), then remove `McpServerConfig._cast_enums()` from the shared module (Phase 5).

---

## Scope

**In:**
- Phase 1: grep for `McpServerConfig(` calls with raw string arguments in `tests/` and `scripts/`
- Phase 1: Run `uv run pytest tests/ -k mcp_config -v` to confirm which tests exercise `_cast_enums`
- Phase 5: Remove `_cast_enums` method body and `self._cast_enums()` call from `__post_init__()`

**Out:**
- Adding `_validate_enum_types()` (that is handled in plan 202756)
- Changing `_build_single_server()` enum conversion logic
- Changes to TOML config file format

---

## Assumptions

1. Raw-string callers in tests are updated before removing `_cast_enums` (see plan 202756 for the full removal plan).
2. `TransportType`, `StartupMode`, `HealthcheckMode` are `StrEnum`; `isinstance` check suffices.
3. No production script under `scripts/` constructs `McpServerConfig(...)` with raw strings.

---

## Implementation

### Target file

`scripts/shared/mcp_config.py`

### Procedure

1. Run `grep -rn "McpServerConfig(" tests/ scripts/ | grep -v ".venv"` — identify all construction sites.
2. Run `uv run pytest tests/ -k mcp_config -v` — confirm test behavior.
3. If raw-string callers exist: update them to pass enum values before proceeding.
4. Remove `_cast_enums()` method body and definition from `McpServerConfig`.
5. Remove `self._cast_enums()` call from `__post_init__()`.
6. Run `ruff check scripts/shared/mcp_config.py`.

### Method

Bash for grep/pytest checks. Edit tool for method removal.

### Details

After removal, `McpServerConfig.__post_init__()` should call only `_validate_cross_fields()` (or the new `_validate_enum_types()` if plan 202756 has been applied first).

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Caller check | `grep -R "_cast_enums" scripts tests docs` | 0 matches after removal |
| Lint | `ruff check scripts/shared/mcp_config.py` | 0 errors |
| Type check | `mypy scripts/shared/` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Tests | `uv run pytest tests/ -k mcp_config -v` | All pass |
| Full suite | `uv run pytest` | All pass |
