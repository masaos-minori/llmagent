# Config dataclass field validators do not re-run on /reload

## Priority
High

## Summary
Config dataclass validators (`scripts/agent/services/config_validators.py`) only run inside `__post_init__`. `ConfigReloadService` mutates already-constructed dataclass instances via direct `setattr` (confirmed: 26 `setattr(cfg....)` call sites in `scripts/agent/services/config_reload.py`), so no validation runs when a value changes via `/reload`. Out-of-range values (e.g. a negative `llm_retry_base_delay`, an `llm_temperature` above its max) can be silently applied, producing a state where the running config violates invariants that are enforced at startup.

## Background
N/A: covered by Summary.

## Problem
Verified: `scripts/agent/config_dataclasses.py` defines `__post_init__` on multiple config dataclasses (`LLMConfig`, `ToolConfig`, etc.), each calling the `validate_*` functions from `config_validators.py`. `scripts/agent/services/config_reload.py` updates fields on the already-constructed `ctx.cfg.*` instances directly via `setattr(...)` (26 occurrences confirmed by grep), which does not re-trigger `__post_init__` or any validator.

## Reason for Change
This creates an inconsistency between startup-time and reload-time invariants: a value that would be rejected at process start can be silently accepted via `/reload`, with no operator-visible error.

## Implementation Intent
Choose one of the following and apply it consistently across `config_reload.py`:
- **Option A (targeted):** after diff-applying a field, call the relevant `validate_*` function for that sub-config.
- **Option B (rebuild):** reconstruct the affected sub-config via `dataclasses.replace(...)` so `__post_init__` re-validates, then swap it into `ctx.cfg`.

Surface validation failures as a reload-specific error (e.g. `ConfigReloadValidationError`, which already exists and is raised elsewhere in this file for a different check) and keep the previous value on failure — do not partially apply a change that fails validation partway through.

## Target Files or Areas
- `scripts/agent/services/config_reload.py`
- `scripts/agent/config_dataclasses.py`
- `scripts/agent/services/config_validators.py`
- `scripts/agent/services/typed_validators.py`

## Required Changes
- Decide between Option A and Option B (see Unresolved Questions) and apply it to every `setattr(cfg...., ...)` call site in `config_reload.py` that mutates a field with an existing validator.
- Ensure a validation failure raises `ConfigReloadValidationError` (or an equivalent, already-used error type) and leaves `ctx.cfg` unchanged for that field.

## Constraints
- Must not change the validation rules or thresholds themselves — only ensure they run on reload as they do on startup.
- Must not weaken startup-time validation while adding reload-time validation.

## Acceptance Criteria
- [ ] Reloading an out-of-range value (e.g. `llm_temperature = 5.0`) is rejected and the running value is left unchanged.
- [ ] A clear, operator-visible error is reported on rejection (no silent acceptance).
- [ ] Valid reloads continue to apply exactly as before.

## Testing Expectations
- Unit test: reload `llm_temperature = 5.0` (or another out-of-range value already covered by an existing validator) is rejected, and `ctx.cfg.llm.llm_temperature` is unchanged.
- Unit test: reload a valid change continues to apply successfully (regression).

## Documentation Impact
If `docs/05_agent_07_06_cli-and-commands-hot-reload.md` (or the equivalent hot-reload scope doc) states or implies that reload values are validated, no change needed; if it is silent on this point, add a short note that reload now enforces the same field-level invariants as startup.

## Out of Scope
- Adding new validation rules beyond what already exists in `config_validators.py`.
- Refactoring the validators themselves (tracked separately, see Dependencies).

## Dependencies
- Coordinate with the separate validator-deduplication issue (`issues/20260825_config_validators_duplicate_range_checks_issue.md`) if both land in the same window — that issue changes the internal structure of `config_validators.py` but not the public `validate_*` names/signatures this issue calls.

## Unresolved Questions
- Option A vs. Option B: Option A is more surgical but requires identifying, per field, which `validate_*` function covers it and calling it correctly with the right sub-config object. Option B is more uniform but requires confirming `dataclasses.replace(...)` is safe for every sub-config touched by `config_reload.py` (e.g. no non-init fields or mutable shared state that would be lost on reconstruction). Resolve this during Plan generation by inspecting each affected dataclass.

## AI Implementation Instruction
Do not guess which option is safer without inspecting each affected dataclass's `__post_init__` and field set — `dataclasses.replace(...)` on a dataclass with non-trivial `__post_init__` side effects (e.g. derived caches, opened resources) could reintroduce a different class of bug. Keep the change scoped to fields that already have a `validate_*` counterpart; do not invent new validation for previously-unvalidated fields.
