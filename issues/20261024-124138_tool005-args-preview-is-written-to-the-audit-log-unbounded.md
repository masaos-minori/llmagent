# tool005: `args_preview` is written to the audit log unbounded, and nothing documents that it has no size cap

## Priority
Medium

## Summary
Bound (or explicitly document) the size of the tool-argument data written into audit events. Both
audit writers pass the entire masked argument container to the event field, the field type is an
unbounded `dict`, and no document states whether a cap exists.

## Background
Found while converting `plans/20261023-072425_plan.md` into implementation procedures on 2026-10-24.
That Plan makes masking recursive (`REQ-002`), which shrinks masked values but adds no bound for
anything else, and its `Assumptions` (`:172-173`) justify recursion cost by tool-argument parsing
limits — not any limit on what the audit log stores. `grep -rn "args_preview" docs/` returns no match,
so the field's size behavior is undocumented in either direction.

## Problem
- `scripts/agent/tool_audit.py:58` — `args_preview=masked` inside `audit_approval()`, serialized whole
  by `audit_logger.info(_json_dumps(dataclasses.asdict(evt)))` (`:63`).
- `scripts/agent/tool_audit.py:169` — the same pattern in the `tool_exec` writer.
- `scripts/agent/shared/models.py:23` and `:55` — `args_preview: dict[str, object]`, no size
  constraint.
- Repo-wide search for truncation of argument data finds none for this field: `grep -rn "args_preview"
  scripts/` yields only the two writers plus `tool_approval.py:221-222` (the plan-mode blocked notice),
  and `grep -rn "1500\|4000\|2000" scripts/ --include=*.py` finds only
  `scripts/mcp_servers/file/read_models.py:28` (`max_read_bytes`) and
  `scripts/agent/memory/extract.py:52` (`IMPORTANCE_LENGTH_DIVISOR`), both unrelated.

`mask_args()` never removes keys and never shortens unmasked values, so a call with many arguments, or
one large unmasked value, is persisted in full. The `[:200]` limits in `scripts/agent/tool_result_formatter.py`
(`:58`, `:66`) bound the *preview text*, not the audit payload.

## Reason for Change
Audit rows are written on every tool call, including calls whose arguments carry file bodies. A
growth or injection path in the audit log is a durability and disk-usage concern, and the plan cycle
that changes masking is the natural point to decide the bound rather than leave the behavior implicit.

## Implementation Intent
Measure what an audit row actually contains for a large argument, decide where a cap belongs (audit
writer, event model, or the injected audit logger sink), then implement one documented cap with an
explicit truncation marker — or state in documentation that no cap exists. Either outcome is
acceptable; an undocumented behavior is not.

## Target Files or Areas
- `scripts/agent/tool_audit.py` (`audit_approval` `:35-63`, the `tool_exec` writer at `:169`)
- `scripts/agent/shared/models.py` (`args_preview` `:23`, `:55`)
- the object behind `ctx.services_required.audit_logger` (Needs confirmation: the concrete
  implementation injected in production was not identified during this pass)
- `scripts/agent/tool_approval.py:221-222` (plan-mode blocked notice, which builds its own masked
  preview)

## Required Changes
- Enumerate every sink that persists `args_preview` and measure the row size it produces today.
- Decide a cap policy: a character or byte budget for the serialized preview plus a marker that
  distinguishes truncation from a masked value (`***`).
- Implement it in the one place all audit writers share, or document that no cap exists.
- Add a regression test for the decided behavior.

## Constraints
- Keep the event shape (`dataclasses.asdict(evt)` as one JSON line) so existing readers and
  `tests/agent/test_tool_audit.py` continue to work.
- A truncation marker must not be confusable with masking output.
- Put the cap value in configuration or a module constant rather than an inline literal, per
  `rules/coding.md` config boundaries.
- `plans/20261023-072425_plan.md` `AC-2` requires the serialized payload to show `***` at the masked
  path; a cap must not truncate before that assertion is satisfiable.

## Acceptance Criteria
1. The size behavior of `args_preview` is either an implemented cap that a test measures, or a
   documented statement that no cap exists.
2. `grep -rn "args_preview" scripts/` shows every writer going through the decided behavior.
3. A regression test writes an audit event with a multi-kilobyte argument value and asserts the
   recorded preview matches the decided behavior.
4. `uv run pytest tests/agent -q` and `uv run pytest tests/integration -q` pass with no new failure.

## Testing Expectations
- Unit test in `tests/agent/` for `audit_approval()` with a large argument value, asserting the size of
  the serialized audit JSON's preview field and the presence of the marker.
- Reuse the `MagicMock` audit-sink pattern already in `tests/agent/test_tool_approval_preflight.py`
  (`TestAuditApproval`, `:394-430`).
- If a cap is added: one case at exactly the cap and one byte over it.

## Documentation Impact
Required. The audit-event field is currently undocumented (`grep -rn "args_preview" docs/` is empty).
State the decided behavior in the chapter that describes audit events; confirm the correct `docs/41_db/`
or `docs/40_shared/` chapter before editing, because none of the current chapter titles names auditing.

## Out of Scope
- Which keys are masked, and the default `masked_fields` value
  ([issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md](20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md)).
- Approval-preview behavior (previews are unmasked by decision in
  `plans/20261023-072425_plan.md`).
- Audit-log retention, rotation, or pruning
  (`docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`).

## Dependencies
- No blocking dependency on `plans/20261023-072425_plan.md`; the two changes touch different behavior.
- Related: the default-key-names issue above, because masking more keys changes how much of the
  payload is redacted rather than truncated.

## Unresolved Questions
- Which object implements `ctx.services_required.audit_logger` in production, and whether it already
  truncates. Not confirmed in this pass.
- Cap by character count or by serialized byte count?

## AI Implementation Instruction
Do not assume any truncation exists; measure first. Keep `args_preview`'s type and the one-JSON-line
event format compatible with existing readers. Record the decision in documentation either way.

## Traceability
- **Workflow phase**: `plan-to-implementation-procedure` (latent gap found while verifying the Plan's claims)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-072425_plan.md` (`Assumptions`, `AC-2`)
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261024-124138
- **Related target files**: `scripts/agent/tool_audit.py`, `scripts/agent/shared/models.py`, `scripts/agent/tool_approval.py`
