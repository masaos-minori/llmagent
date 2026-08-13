## Goal

Add a new module, `scripts/agent/tool_preparation.py`, that runs a fail-closed
"preparation" phase for every raw LLM tool call *before* `_run_approval_gate()` in
`execute_all_tool_calls()`. For each call it must: parse `id`/`function.name`, parse
`arguments` JSON exactly once, require the parsed result to be a `dict`, resolve the
tool through `RuntimeToolRegistry` only (no `ctx.cfg.tool.tool_definitions` fallback),
validate args against the live `RuntimeTool.input_schema`, and build a `PreparedToolCall`
carrying a per-call `ToolSpec`. Any failure at any step becomes a synthetic tool-error
result tuple, never a `PreparedToolCall`.

## Scope

In scope: creating `scripts/agent/tool_preparation.py` with:
- `PreparedToolCall` (frozen dataclass): `call_id`, `name`, `args`, `spec: ToolSpec`,
  `original_call: dict`.
- `prepare_tool_calls(ctx, tool_calls) -> tuple[list[PreparedToolCall], list[tuple]]`,
  where the second list holds synthetic-error tuples in the same 6-tuple shape
  `execute_one_tool_call()` currently returns (`tc_id, name, args, full_text, is_error,
  llm_text`), tagged so `execute_all_tool_calls()` can reinsert them at their original
  index.
- A small internal helper per preparation step (id/name check, JSON decode, dict-type
  check, registry lookup, schema validation, spec build), each mapped to one of five
  error kinds: `configuration`, `unknown_tool`, `validation`, `schema`, `metadata`.

Out of scope: any change to `scripts/agent/tool_runner.py`,
`scripts/agent/tool_approval.py`, or `scripts/agent/config_dataclasses.py` (each has its
own doc in this set); reimplementing `validate_tool_arguments()` or
`RuntimeToolRegistry.tool_spec_for_call()` (both reused verbatim).

## Assumptions

- `ctx.services_required.runtime_tools` (a `RuntimeToolRegistry`) is populated before
  `execute_all_tool_calls()` runs in normal operation; a `None` registry is a defensive
  `configuration`-kind rejection, not the expected steady-state path (per the plan's
  Assumptions).
- `RuntimeToolRegistry.tool_spec_for_call(call_id, name, args)` (confirmed present at
  `scripts/shared/runtime_tool_registry.py:156-164`, reading: `tool = self.get(name)` then
  `RuntimeToolRegistry._build_tool_spec(call_id, name, tool, args)`) already raises
  `KeyError` for an unregistered tool name — reused directly rather than re-implemented.
- `validate_tool_arguments(tool_name, args, input_schema, allow_extra_fields=False) ->
  ValidationResult` (confirmed at `scripts/agent/tool_arg_validator.py:54`) is safe to call
  with `runtime_tool.input_schema` / `runtime_tool.allow_extra_fields` taken from the
  registry entry, matching today's `_validate_tool_args()` call shape
  (`scripts/agent/tool_runner.py:144-150`).
- `ToolSpec` (confirmed at `scripts/shared/tool_spec.py`) is `frozen`, with fields
  `call_id, name, args, resource_scope, requires_serial, is_write` — the version in the
  current tree (singular `resource_scope`); this doc grounds against that shape as it
  exists today, not a hypothetical future rename.

## Design decisions

- **One parse, one validation, one registry lookup per call, all in this module.** Today
  `orjson.loads()` runs once in `execute_one_tool_call()`
  (`scripts/agent/tool_runner.py:195`) and again, independently, in
  `run_approval_checks()` (`scripts/agent/tool_approval.py:202`) with a different (lenient)
  error-handling policy. Centralizing the parse here and having both downstream call sites
  consume `PreparedToolCall.args` removes the second, inconsistent path.
- **Reuse `RuntimeToolRegistry.tool_spec_for_call()` instead of hand-building a
  `ToolSpec`.** It already folds in `resource_scope`/`requires_serial`/`is_write` from the
  live `RuntimeTool`, replacing both `_build_tool_meta()`'s per-name construction and
  `_validate_tool_args()`'s registry lookup in one call.
- **No `tool_definitions` fallback anywhere in this module.** The current
  `_validate_tool_args()` gateway-fallback loop over `ctx.cfg.tool.tool_definitions`
  (`scripts/agent/tool_runner.py:157-172`) is exactly the silent-acceptance path this
  requirement removes; `prepare_tool_calls()` must reject via `unknown_tool` on a registry
  `KeyError`, full stop.
- **Synthetic errors keep the same 6-tuple shape as today's results**, so
  `_collect_tool_result_msgs()` (`scripts/agent/tool_runner.py:234-263`) needs no shape
  change; only `execute_all_tool_calls()`'s merge/ordering logic changes (handled in the
  `tool_runner.py` doc in this set).

## Alternatives considered

- Making preparation raise exceptions instead of returning synthetic error tuples.
  Rejected: the plan requires each failed call to surface as a normal tool-error message
  in original order, not to abort the whole batch; the existing `_reject_validation()`
  pattern (`scripts/agent/tool_runner.py:115-125`) already returns a `ToolCallResult`
  rather than raising, and this module should produce the equivalent result shape, not a
  new exception type.
- Building `ToolSpec` by hand inside this module (mirroring `_build_tool_meta()`).
  Rejected: `RuntimeToolRegistry.tool_spec_for_call()` already exists and is the plan's
  designated single source for per-call `ToolSpec` construction; duplicating its logic
  here would reintroduce the multiple-sources-of-truth problem the plan is fixing.

## Implementation

### Target file

`scripts/agent/tool_preparation.py` (new file)

### Procedure

1. Module docstring stating its role: the fail-closed preparation phase that runs before
   approval, per `scripts/agent/tool_runner.py`'s `execute_all_tool_calls()`.
2. Imports: `orjson`; `from shared.tool_spec import ToolSpec`; `from shared.transport_dto
   import ToolCallResult` (for the error-tuple text, matching
   `_reject_validation()`'s shape); `from agent.tool_arg_validator import
   validate_tool_arguments`; `TYPE_CHECKING` guard for `from agent.context import
   AgentContext`.
3. Define `PreparedToolCall`:
   ```python
   @dataclass(frozen=True)
   class PreparedToolCall:
       call_id: str
       name: str
       args: dict[str, Any]
       spec: ToolSpec
       original_call: dict
   ```
4. Define a module-level `_PrepFailure = tuple[str, str, dict, str, bool, str]` type
   alias matching `execute_one_tool_call()`'s return shape, for the failure list's element
   type.
5. Define one small helper per step, each returning either a partial result or raising
   internally to a single `try/except` in `prepare_tool_calls()`'s per-call loop —
   mirroring the existing style of `_reject_validation()` (build-and-return, not raise):
   - `_prepare_one(ctx, tc) -> PreparedToolCall | _PrepFailure`:
     a. `tc.get("id")` and `tc.get("function", {}).get("name")` must both be truthy;
        missing → `configuration` kind (id) or `validation` kind (name), via a local
        `_reject(name_or_placeholder, kind, reason)` builder that mirrors
        `_reject_validation()`'s `ToolCallResult` construction but tags `error_type` with
        the specific kind string instead of the single literal `"validation"`.
     b. `orjson.loads(func.get("arguments", "{}"))` inside `try/except
        orjson.JSONDecodeError` → `validation` kind on failure (reason includes the raw
        string, matching `ToolArgumentsDecodeError`'s current message shape at
        `scripts/agent/tool_runner.py:197-199`, but returned as a result tuple, not
        raised).
     c. `isinstance(args, dict)` — non-dict decoded JSON (e.g. a JSON array or scalar) →
        `validation` kind, reason `"arguments must decode to a JSON object"`.
     d. `ctx.services_required.runtime_tools is None` → `configuration` kind.
     e. `registry.get(name)` inside `try/except KeyError` → `unknown_tool` kind on miss.
     f. `validate_tool_arguments(tool_name=name, args=args,
        input_schema=runtime_tool.input_schema,
        allow_extra_fields=runtime_tool.allow_extra_fields)` → `schema` kind if
        `not result.success` (reason = `result.reason`).
     g. `registry.tool_spec_for_call(call_id, name, args)` inside `try/except KeyError` →
        `metadata` kind (defensive; step (e) already caught the common case).
     h. On success, return `PreparedToolCall(call_id=tc["id"], name=name, args=args,
        spec=spec, original_call=tc)`.
6. `prepare_tool_calls(ctx, tool_calls: list[dict]) -> tuple[list[PreparedToolCall],
   list[_PrepFailure]]`: loop over `tool_calls` in order, call `_prepare_one`, and append
   to the appropriate list, preserving relative order within each list (final
   interleaving back into original batch order is the caller's job, per the
   `tool_runner.py` doc in this set — this function does not need `tool_calls`' original
   indices itself, since each failure tuple already carries its own `tc_id`, which the
   caller can look up in a `call_order` map).
7. Log each rejection via `logger.warning("tool_preparation_rejected kind=%s
   tool=%r reason=%s", kind, name, reason)`, matching `_reject_validation()`'s existing
   log style (`scripts/agent/tool_runner.py:117`).

### Method

New file, written directly (not a codemod) — it has no prior version to diff against.
Ground every reused call (`validate_tool_arguments`, `tool_spec_for_call`) against the
current signatures read for this doc, not against the plan's paraphrase.

### Details

- `execute_one_tool_call()`'s current 6-tuple return
  (`scripts/agent/tool_runner.py:176-231`, `return tc["id"], name, args, text, is_error,
  llm_text`) is the shape a synthetic failure tuple must match, with `text == llm_text ==
  reason` (no separate "full" vs "truncated" text for a prep failure — there is no tool
  output to truncate).
- `_reject_validation()` (`scripts/agent/tool_runner.py:115-125`) returns a
  `ToolCallResult`, not a 6-tuple; preparation failures need the 6-tuple shape directly
  (matching what `_collect_tool_result_msgs()` iterates over at
  `scripts/agent/tool_runner.py:247`), so this module builds `(tc_id, name, args, reason,
  True, reason)` tuples locally rather than importing `_reject_validation()` from
  `tool_runner.py` (which would also invert the intended import direction — preparation
  should not depend on `tool_runner.py`; `tool_runner.py` depends on preparation).

## Compatibility considerations

- No existing caller imports from `scripts/agent/tool_preparation.py` yet (file does not
  exist); the only planned importer is `scripts/agent/tool_runner.py` (see its doc).
- `PreparedToolCall.spec`'s `ToolSpec.resource_scope` field is singular in the current
  tree; if a separate, unrelated effort renames it to `resource_scopes` (plural) before
  this lands, `_build_tool_spec()`'s call inside `tool_spec_for_call()` already reflects
  whichever shape is live, so this module needs no change either way — it never
  constructs a `ToolSpec` field-by-field itself.

## Security considerations

- This module is the enforcement point removing the silent-acceptance gap: an
  unregistered tool name can no longer reach approval or execution just because a stale
  `ctx.cfg.tool.tool_definitions` entry happens to match it by name — `unknown_tool` is a
  hard rejection with no fallback lookup.
- Non-dict decoded JSON (e.g. `arguments: "[1,2,3]"`) is explicitly rejected rather than
  passed through as-is to schema validation or execution, closing a type-confusion gap
  that a raw `orjson.loads()` result being silently used as `args: dict` in downstream
  code would otherwise allow.

## Rollback considerations

- Deleting this new file and reverting its single call site
  (`execute_all_tool_calls()`) restores the pre-change behavior exactly, since this doc
  introduces no other file changes. See the `tool_runner.py` doc's Rollback section for
  the paired revert.
- No persisted state or schema is touched; rollback is source-only.

## Validation plan

`uv run pytest tests/agent/test_tool_preparation.py -v` — covering the 8 requirement
scenarios (registry `None`, unregistered name despite a matching stale
`tool_definitions` entry, malformed JSON, non-dict decoded value, schema violation,
mixed valid/invalid batch preserving order, approval-mock never called for a
failed-prep call, and a fully-valid call producing a `PreparedToolCall`). See the paired
`tests/agent/test_tool_preparation.py` doc for the concrete test bodies.

## Out of scope

- Wiring into `execute_all_tool_calls()`, `_execute_with_dag()`, and
  `run_approval_checks()` — covered by the `tool_runner.py` and `tool_approval.py` docs
  in this set.
- `config_dataclasses.py`'s `tool_definitions` docstring update — separate doc.
- Any `docs/*.md` update — explicitly out of scope for this document-only phase.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-184037_plan.md
- Source implementation procedure: N/A
- Generated at: 20260813-235940
- Related target files: tool_preparation.py
