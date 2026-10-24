# Audit `args_preview` cap implementation procedure (writers)

**Stage:** Implementation Procedure
**Created:** 2026-10-25 00:28 UTC
**Status:** Draft for execution
**Owning Plan:** `plans/done/20261024-221315_args-preview-is-written-to-the-audit-log-unbounded.md` (`Frozen`)
**Owning Requirement:** `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`
**Issue:** `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`
**Target file (row 1 of 3):** `scripts/agent/tool_audit.py`

## Goal

- Bound the `args_preview` field written by both agent-side audit writers in `scripts/agent/tool_audit.py`
  with one module constant and one private helper, so no tool call can grow `/opt/llm/logs/audit.log`
  through unbounded argument payloads (REQ-001, REQ-002).
- Keep the truncation marker structurally distinct from masking output (`"truncated": true` boolean vs
  the string value `"***"`) (REQ-004).
- Keep the event shape contract intact: `args_preview` stays a dict, one JSON line per event,
  `scripts/agent/shared/models.py` unchanged (REQ-003).

## Scope

- Module constant `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new) (value 1500) in `scripts/agent/tool_audit.py`.
- Private helper `_bounded_preview` (new) implementing the REQ-001 contract.
- Two call-site changes: `args_preview=masked` at `:58` (`audit_approval`) and `:169` (`audit_tool_exec`)
  become `args_preview=_bounded_preview(masked)`.
- Execution-order coupling: this row runs **after** row 2 (`tests/agent/test_tool_audit.py`) has landed its
  failing tests, per the plan's `Implementation steps` Phase 1 -> Phase 2 (TDD-first).

## Assumptions

- Character count of the serialized preview string produced by `_json_dumps` is the governed quantity
  (Plan `Assumptions`; `_json_dumps` returns `str`). Envelope keys sit outside the cap and add only a
  small fixed overhead.
- Cap value 1500 is frozen plan policy (owner-revisable by editing the constant); it is not a config key.
- All measured production rows are 134 chars, so every observed row stays on the pass-through path;
  the envelope only affects hypothetical oversized payloads.
- `_json_dumps(masked)` raising `TypeError` on a non-JSON-serializable value mirrors the failure that
  already exists at `_json_dumps(dataclasses.asdict(evt))` in the same writers; the helper adds no new
  failure mode and REQ-001 specifies no fallback, so none is added.

## Design decisions

- `DR-101`: One private helper called at both `args_preview=` assignment sites, not per-writer inline
  logic. The plan's `Design` (Choke-point choice) fixes this: both writers already compute
  `masked = mask_args(...)` and then pass it through unchanged; wrapping that single site is "the one
  place all audit writers share".
- `DR-102`: Oversized payloads are replaced **wholesale** by the envelope
  `{"preview": <serialized prefix>, "truncated": True}`; the prefix is the first
  `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new) chars of `_json_dumps(masked)`. No key-preserving trimming —
  REQ-001 fixes the envelope shape.
- `DR-103`: Pass-through is `len(serialized) <= AUDIT_ARGS_PREVIEW_MAX_CHARS` (truncation triggers
  strictly above the cap), so the exactly-at-cap case stores the container unchanged. This is the
  boundary the row-2 tests pin.
- `DR-104`: Mask-before-bound ordering is preserved (Plan `Design`, Order): the helper only ever sees
  the already-masked container, and a truncated prefix may therefore contain `"***"` values. This is
  an accepted consequence, not a defect.

## Alternatives considered

- Enforce the bound in the shared sink `scripts/shared/logger.py` — **rejected**: the sink is shared
  with MCP-side and gateway logging where a bound would be wrong (Plan `Design`, Architecture;
  `scripts/shared/logger.py` is a Reference File verified to add no size bound).
- Make the cap a `[tool]` config key — **rejected**: Plan `Assumptions` choose a module constant to keep
  `/opt/llm/config/agent.toml` (shared production config) out of scope; the Issue allows either.
- Keep keys and truncate individual values instead of an envelope — **rejected**: REQ-001 fixes the
  envelope shape; partial values would make the truncation state ambiguous against REQ-004.

## Implementation

### Target file

`scripts/agent/tool_audit.py`

Modify (constant + helper + 2 call-site wraps). Public function signatures unchanged.

### Procedure

1. Confirm `tests/agent/test_tool_audit.py` cap tests from row 2 exist and fail against the current
   code (plan Phase 1). Do not start this row otherwise.
2. Add the module constant `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new) with value `1500` after the import
   block (imports end at `:20`; `TYPE_CHECKING` block `:22-23`), before `_extract_resource_scope`
   (`:26`).
3. Add the private helper `_bounded_preview` (new) between `_extract_resource_scope` (`:26-30`) and
   `audit_approval` (`:33`).
4. In `audit_approval`, replace `args_preview=masked` (`:58`) with `args_preview=_bounded_preview(masked)`.
5. In `audit_tool_exec`, replace `args_preview=masked` (`:169`) with `args_preview=_bounded_preview(masked)`.
6. No change at `write_round_exec` (`:182`): its `round_exec` dict carries no `args_preview` key
   (revalidated 2026-10-25); REQ-003's "behavior unchanged" is satisfied by leaving it untouched.
7. Run the targeted test command from the plan Phase 2 (see Validation plan) — row-2 tests must turn
   green, existing tests must stay green.
8. Run the AC-2 grep: `grep -rn "args_preview" scripts/` — both writers must show
   `_bounded_preview` (new), no writer may bypass it.

### Method

Constant and helper, exact final form:

```python
AUDIT_ARGS_PREVIEW_MAX_CHARS = 1500


def _bounded_preview(masked: dict[str, object]) -> dict[str, object]:
    """Cap the serialized audit preview; oversized containers become a truncated envelope."""
    if not masked:
        return masked
    serialized = _json_dumps(masked)
    if len(serialized) <= AUDIT_ARGS_PREVIEW_MAX_CHARS:
        return masked
    return {
        "preview": serialized[:AUDIT_ARGS_PREVIEW_MAX_CHARS],
        "truncated": True,
    }
```

Call-site diffs (each is a single-line change):

```python
# audit_approval, was: args_preview=masked,
        args_preview=_bounded_preview(masked),
```

```python
# audit_tool_exec, was: args_preview=masked,
        args_preview=_bounded_preview(masked),
```

No new imports are required: `_json_dumps` is already imported at `:14`, and the helper stays inside
the module, so no `importlinter` layer is crossed.

### Details

- The governed quantity is `len(_json_dumps(masked))` — chars of the serialized string, not bytes and
  not per-value lengths. `preview` is the serialized prefix cut at exactly
  `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new) chars, and its own length equals the cap in every truncated case
  (row 2 asserts this).
- `args_preview`'s declared type in `scripts/agent/shared/models.py` (`:23`, `:55`) stays
  `dict[str, object]`; the envelope is a dict, so `dataclasses.asdict` + one-line JSON emission are
  unchanged.
- Empty containers return unchanged without serializing (fast path; `DR-103` pass-through would apply
  to `"{}"` anyway).
- `resource_scope` extraction (`_extract_resource_scope`, `audit_approval` `:47`) runs on `masked`
  **before** bounding and is unaffected by the envelope.
- Constant placement is module-level (not class/config) so the value is greppable and satisfies the
  Issue's "value must live in a constant or config" constraint.

## Compatibility considerations

- No signature changes: `audit_approval()`, `audit_tool_exec()`, `write_round_exec()` keep their
  parameters and return behavior. Importers listed in the plan `Affected areas` (`tool_runner.py`,
  `tool_approval.py`, `workflow_engine_adapter.py`, `tool_run_recorder.py`) cannot observe the private
  helper.
- Existing audit tests use small payloads (all under 1500 serialized chars), so the envelope never
  triggers in them: `tests/agent/test_tool_audit.py` (12 tests, revalidated 2026-10-25),
  `tests/agent/test_tool_approval_preflight.py` `TestAuditApproval` (`:394-443`), and
  `tests/agent/test_audit_log_format.py` (MCP-side format gate) must pass unchanged.
- Log readers: no repo code or documented usage parses `args_preview` sub-keys (plan Risks, verified
  2026-10-24; `docs/22_mcp/mcp_06_05_reading-audit-logs.md` examples filter on `event`/`tool` only).
- Deployed runtime: the file is rsynced by `deploy.sh`; the plan Validation plan requires a post-deploy
  `tail` smoke confirming sub-cap rows stay byte-identical (134-char rows today).

## Security considerations

- Masking still runs before bounding (REQ-002), so a raw secret can never enter `preview`: the prefix is
  cut from the already-masked serialization.
- Truncated rows must be treated as structurally reduced during security review; the boolean `truncated`
  marker makes this detectable, and the row-3 doc states it in the event contract (plan Risks mitigation).
- No new secret material, no new file paths, no config changes.

## Rollback considerations

- Revert is self-contained: delete the constant and helper, restore the two `args_preview=masked`
  lines (`:58`, `:169`). No data migration is needed — no oversized envelope rows exist in the live
  `audit.log` (all 123,795 bytes of measured rows are 134 chars, re-measured 2026-10-25), so rolling
  back leaves no log artifacts to interpret.
- Row 2's tests are designed to fail without this row (TDD pairing); a rollback of this row alone must
  be accompanied by disabling or reverting the row-2 cap tests to keep CI green.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Targeted tests | `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_tool_approval_preflight.py tests/agent/test_audit_log_format.py -q` | New cap tests green; all pre-existing tests unchanged |
| AC-2 grep | `grep -rn "args_preview" scripts/` | Both writers store `_bounded_preview` (new); no bypass |
| Lint/type | `uv run ruff format --check scripts/agent/tool_audit.py`; `uv run ruff check scripts/agent/tool_audit.py`; `uv run mypy --no-namespace-packages scripts/` | Clean |
| Architecture/security | `PYTHONPATH=scripts uv run lint-imports`; `uv run bandit -r scripts/ -c pyproject.toml -ll` | No contract violation (change is module-internal); no findings at `-ll` |
| Full gate | `uv run pytest tests/agent -q`; `uv run pytest tests/integration -q`; `rules/toolchain.md` sequence incl. diff-cover >= 90% on changed lines | No new failures |

## Completion criteria

- REQ-001: constant and helper present with the exact REQ-001 contract (serialize, pass at `<=` cap,
  envelope above it).
- REQ-002: both writers call the helper; AC-2 grep shows no bypass.
- REQ-003: event shape unchanged; `scripts/agent/shared/models.py` untouched; `write_round_exec` untouched.
- REQ-004: truncation expressed only via the `truncated` boolean envelope (no string marker).
- AC-1/AC-2 satisfied; the row-2 boundary tests (exactly-at-cap and cap+1 for both writers) pass; the
  full `rules/toolchain.md` sequence reports no new failures.

## Out of Scope

- Masked-key selection and the default `masked_fields` value (separate issue
  `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`).
- `mask_args` semantics, `scripts/agent/shared/models.py` fields, the shared `Logger` sink, MCP-side
  audit records, plan-mode blocked notice UI output, audit-log retention/rotation, and any config file.
- Making the cap value configurable (module constant only, per frozen Plan `Assumptions`).

## Execution Status

| Block | Status | Notes |
|---|---|---|
| 1. Constant + helper (`DR-101`..`DR-104`) | Pending | After row 2 lands its failing tests |
| 2. Two call-site wraps (`REQ-002`) | Pending | `:58`, `:169` |
| 3. Targeted + full validation (`AC-1`, `AC-2`, `AC-4`) | Pending | Plan Phase 2 gate |

## Traceability

- **Owning plan**: `plans/done/20261024-221315_args-preview-is-written-to-the-audit-log-unbounded.md` —
  row 1 of the `Implementation Target Files` table.
- **Source issue**: `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`.
- **Plan requirements covered**: `REQ-001` (`AC-1`), `REQ-002` (`AC-2`), `REQ-003` (`AC-4` regression half),
  `REQ-004` (`AC-1` marker half).
- **Local design decisions**: `DR-101`..`DR-104` extend the plan's frozen `Design` bullets (choke point,
  envelope, ordering) with procedure-level specifics only.
- **Cross-row dependencies**:
  - Row 2 (`tests/agent/test_tool_audit.py`) must be written and confirmed failing **before** this row
    (plan Phase 1); this row turns those tests green.
  - Row 3 (`docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`) documents the
    names and value introduced here; it must run after this row so the doc claims match landed code.
- **Revalidation record**: plan `Revalidation record (2026-10-25, HEAD 9331b337a)` rows 1-3 and 7-8
  carry the fresh evidence for the anchors cited here (`:14`, `:26-30`, `:58`, `:169`, `:182`).
