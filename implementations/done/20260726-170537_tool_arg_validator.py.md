## Goal

Add a per-tool custom-validation-hook interface to `scripts/agent/tool_arg_validator.py` so
that additional, tool-specific validation rules can be plugged into the schema-based
`validate_tool_arguments()` pipeline, satisfying plan Phase 3 ("Define interface for MCP
servers to register custom validation rules per tool").

## Scope

**In-Scope:**
- A module-level registry + decorator (`register_custom_validator`) in
  `tool_arg_validator.py`, mirroring the existing pattern in
  `scripts/mcp_servers/tool_validators.py`.
- Wiring the hook lookup into `validate_tool_arguments()` so a registered hook runs after
  the existing required/extra-field/type checks pass.
- Module docstring update documenting the hook mechanism.

**Out-of-Scope:**
- `allow_extra_fields` per-MCP-server default (already implemented on `RuntimeTool` /
  `runtime_tool_registry.py` — see "Out of scope" below).
- Modifying `scripts/mcp_servers/tool_validators.py` or its existing registered validators.
- Changing `scripts/agent/tool_runner.py`'s `_validate_tool_args()` call signature.
- Adding new MCP servers or modifying MCP server implementations.

## Assumptions

- Custom validators are process-local, registered via decorator at import time — same
  pattern as `mcp_servers/tool_validators.py`'s `register_validator`.
- Custom hooks run only after the built-in checks (required fields, extra fields, type
  validation) already pass; they add stricter/business-specific checks, they do not replace
  schema checks.
- No persistence of hook registration; ephemeral per-process registry, consistent with the
  existing `tool_validators.py` pattern.

## Design decisions

- Reuse the established registry+decorator pattern already proven in
  `mcp_servers/tool_validators.py` for consistency and minimal new abstraction (no
  `Protocol`/`ABC` needed for a single-callable contract).
- Hooks return the existing `ValidationResult` frozen dataclass rather than raising
  exceptions, keeping `validate_tool_arguments()`'s "never raises for validation failures"
  contract uniform.
- Keep the registry as a plain module-level `dict`, matching the file's existing
  function-based (non-class) style for `_check_*` helpers.

## Alternatives considered

- **Reuse `mcp_servers/tool_validators.py`'s `_VALIDATORS` registry directly** instead of a
  new registry in `agent/tool_arg_validator.py`. The import-layer contract (`agent` may
  import all layers) would technically allow this, but that registry's hooks raise
  `ValueError` and serve a different validation moment (MCP server-side raw arg checks in
  `mcp_servers/models.py`) — reusing it would conflate two contracts. Rejected in favor of a
  separate, `ValidationResult`-returning registry local to this module.
- **Pass a validator callable explicitly into `validate_tool_arguments()` on each call
  site** instead of a global registry. Rejected: would require threading a lookup through
  `tool_runner.py`'s `_validate_tool_args()`, adding coupling; a registry decorator keeps
  registration co-located with hook definitions, consistent with `tool_validators.py`.

## Implementation

### Target file

`scripts/agent/tool_arg_validator.py`

### Procedure

1. Add `CustomValidator = Callable[[dict], ValidationResult]` type alias and
   `_CUSTOM_VALIDATORS: dict[str, CustomValidator] = {}` module-level registry after the
   `logger = logging.getLogger(__name__)` line (current line 18).
2. Add `register_custom_validator(tool_name: str) -> Callable[[CustomValidator],
   CustomValidator]` decorator function, mirroring `mcp_servers/tool_validators.py`'s
   `register_validator` signature/docstring style.
3. Add `_run_custom_validator(tool_name: str, args: dict) -> ValidationResult` helper:
   looks up `_CUSTOM_VALIDATORS.get(tool_name)`; if none, return
   `ValidationResult(success=True)`; if present, call it inside try/except, converting any
   raised exception into `ValidationResult(success=False, reason=f"Custom validation error
   for {tool_name}: {exc}")` (never propagate).
4. In `validate_tool_arguments()` (current lines 34-76), after the existing
   `_check_type_validation` call succeeds and before the final
   `return ValidationResult(success=True)`, call `_run_custom_validator(tool_name, args)`
   and return its result if it fails.
5. Update the module docstring (current lines 1-9) to document the custom-hook mechanism
   and usage pattern, mirroring the `mcp_servers/tool_validators.py` docstring style
   (current lines 1-13).

### Method

Direct source edit to `scripts/agent/tool_arg_validator.py` only; no new files. Use plain
functions and a module-level dict, consistent with the file's existing style — no new
classes.

### Details

- Current file state (verified by reading `scripts/agent/tool_arg_validator.py`, 129
  lines): `ValidationResult` frozen dataclass (lines 21-31); `validate_tool_arguments()`
  (lines 34-76) already runs `_check_required_fields` -> (conditionally)
  `_check_extra_fields` -> `_check_type_validation` -> returns success. No custom-hook
  concept exists yet.
- `scripts/agent/tool_runner.py`'s `_validate_tool_args()` (lines 115-143) already calls
  `validate_tool_arguments(tool_name=name, args=args, input_schema=..., allow_extra_fields=
  runtime_tool.allow_extra_fields)` — no change needed there since the hook lookup is
  internal to `tool_arg_validator.py` by `tool_name`.
- `scripts/mcp_servers/tool_validators.py` (129 lines) already implements an unrelated,
  proven `register_validator`/`_VALIDATORS` pattern (used by
  `scripts/mcp_servers/models.py`) — used here only as a style reference, not imported.

## Compatibility considerations

- Hook lookup only activates for tool names with a registered hook; tools without one
  behave exactly as before (`_run_custom_validator` returns `success=True`) — fully
  backward compatible.
- No change to `validate_tool_arguments()`'s public parameter list, so
  `tool_runner._validate_tool_args()`'s call site is unaffected.

## Security considerations

- Custom hooks execute arbitrary in-repo Python code on every call for their registered
  tool name; only trust hooks defined in this codebase (no dynamic/plugin loading from
  external sources).
- Hook failures must return `ValidationResult(success=False, reason=...)` with a
  human-readable reason only — never leak raw exception tracebacks to the LLM-facing
  message.
- Hook exceptions must not crash `execute_one_tool_call()` — caught in
  `_run_custom_validator()` and converted to a failed `ValidationResult`, consistent with
  the plan's Assumption 3 ("validation failures are errors returned to the LLM, not fatal
  crashes").

## Rollback considerations

- Purely additive to `tool_arg_validator.py`; since no hooks are registered by default,
  rollback is a straight revert of this one file — no impact on `runtime_tool.py`,
  `runtime_tool_registry.py`, or `tool_runner.py`.
- No schema/data migration involved; no `deploy/deploy.sh` change needed (no new file
  added).

## Validation plan

| Target File/Module | Testing Strategy | Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_arg_validator.py` | Unit: hook registered + passes; hook registered + fails; no hook registered (no-op); hook raises exception (converted, not propagated) | `uv run pytest tests/test_tool_arg_validator.py -v` | All four cases behave as specified |
| `scripts/agent/tool_runner.py` (regression) | Confirm existing integration point unaffected | `uv run pytest tests/test_tool_runner.py -v` | No regression |
| Full validation sequence | Format/lint/type/arch/security/tests per `rules/toolchain.md` | `uv run ruff check scripts/`, `uv run mypy scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`, `uv run pytest` | All pass, no new failures |

## Out of scope

- `allow_extra_fields` per-MCP-server default (tracked under `runtime_tool.py` /
  `runtime_tool_registry.py`, already implemented per existing implementation docs).
- Modifying `scripts/mcp_servers/tool_validators.py`.
- Adding new MCP servers or changing existing MCP server implementations.
- Changing DAG scheduling logic or tool result formatting/history.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-153505_plan.md
- Source implementation procedure: N/A
- Generated at: 20260726-170537
- Related target files: tool_arg_validator.py
