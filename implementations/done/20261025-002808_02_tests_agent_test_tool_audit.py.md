# Audit `args_preview` cap implementation procedure (regression tests)

**Stage:** Implementation Procedure
**Created:** 2026-10-25 00:28 UTC
**Status:** Draft for execution
**Owning Plan:** `plans/done/20261024-221315_args-preview-is-written-to-the-audit-log-unbounded.md` (`Frozen`)
**Owning Requirement:** `REQ-005` (regression coverage; supports `REQ-004` marker distinction)
**Issue:** `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`
**Target file (row 2 of 3):** `tests/agent/test_tool_audit.py`

## Goal

- Add the cap regression suite for both audit writers **before** the implementation lands (plan
  `Implementation steps` Phase 1): multi-kilobyte value, exactly-at-cap case, cap+1 case for
  `audit_approval()` and `audit_tool_exec()`, plus the mask-then-truncate case (REQ-005, `AC-3`).
- Make the tests measure the persisted event (parse the logged JSON line), not an in-memory value.
- Derive every boundary from the shipped constant `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new) so the suite
  cannot drift from the documented cap.

## Scope

- New module-level helpers `_payload_with_serialized_len` (new) and `_logged_event` (new) in
  `tests/agent/test_tool_audit.py`.
- Two new test classes `TestApprovalPreviewCap` (new) and `TestToolExecPreviewCap` (new) with the seven
  tests listed under Implementation.
- Import additions: extend the existing `agent.tool_audit` import with
  `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new); add `from shared.json_utils import dumps as _json_dumps`.
- Execution-order coupling: this row is plan Phase 1 and must be committed **first**; the tests are
  expected to fail (`ImportError` on the not-yet-existing constant) until row 1
  (`scripts/agent/tool_audit.py`) lands.

## Assumptions

- The helper name, cap value, and envelope shape are frozen by the plan's `REQ-001`; tests may import
  the constant but must hardcode no cap number (boundary drift prevention, plan Revalidation record
  note).
- `_make_cfg` (`:28`) and `_make_ctx` (`:60`) fixtures and the `MagicMock` audit-sink pattern
  (`TestAuditToolExec`, `:132-183`) are sufficient for the new tests; no new fixtures are needed.
- The existing 12 tests stay untouched; the new classes are appended after `TestWriteRoundExec`
  (file currently ends at `:238`).
- `shared.json_utils.dumps` is the exact serializer the writers use (`tool_audit.py:14`), so serialized
  lengths computed in tests match the lengths bounded in code.

## Design decisions

- `DR-101`: Boundary pair derived from `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new) (`n` and `n + 1`), following
  the existing precedent pair `scripts/mcp_servers/git/format_output.py` `GIT_SHOW_OUTPUT_MAX_CHARS` +
  `tests/mcp_servers/git/test_format_output.py:253-258` (`cap + 500` payload, `len(result) == cap`).
  Hardcoding 1500 — rejected: the cap is owner-revisable, and a hardcoded test would silently enforce a
  stale value.
- `DR-102`: Exact-length payloads are built from the serialized result, not from raw string length:
  `_payload_with_serialized_len` (new) pads a `{"q": ...}` container until `len(_json_dumps(payload))`
  equals the requested length, then asserts it. JSON overhead (`{"q":""}`) is measured, not assumed.
- `DR-103`: Assertions run on `json.loads` of the string passed to `audit_logger.info` (the exact
  persisted line), reusing the file's existing pattern (`test_writes_to_audit_logger_when_conditions_met`,
  `:142-147`; `TestWriteRoundExec`, `:202-207`).
- `DR-104`: The mask-then-truncate case asserts the REQ-004 distinction structurally: the boolean
  `"truncated"` key and the retained `"***"` string value coexist in one envelope — masking is a value
  substitution, truncation is a container replacement.

## Alternatives considered

- Monkeypatch the cap to a tiny value for cheaper tests — **rejected**: the plan freezes 1500 as the
  documented contract and `AC-3` measures the shipped configuration; monkeypatching would also break
  `DR-101`'s "measure the cap that ships" property.
- Parametrize the seven cases into one data-driven test — **rejected**: the plan `Tests` section names
  distinct cases per writer and per boundary; separate named tests keep failure localization exact.
- Assert on the `ToolApprovalEvent` dataclass via `args_preview` type only — **rejected**: `REQ-005`
  requires measuring "the recorded preview length and marker", i.e. the serialized output.

## Implementation

### Target file

`tests/agent/test_tool_audit.py`

Modify (append helpers, imports, two test classes). Existing tests unchanged.

### Procedure

1. Confirm `scripts/agent/tool_audit.py` does **not** yet define `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new)
   (plan Phase 1 precondition: tests-first order).
2. Extend the existing `from agent.tool_audit import ...` line with `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new); add
   `from shared.json_utils import dumps as _json_dumps` to the import block (after `:20`).
3. Append module-level helpers `_payload_with_serialized_len` (new) and `_logged_event` (new) after
   `_make_ctx` (`:60-68`) or immediately before the new classes.
4. Append class `TestApprovalPreviewCap` (new) with four tests and class `TestToolExecPreviewCap` (new)
   with three tests at the end of the file (after `TestWriteRoundExec`).
5. Run the file: `uv run pytest tests/agent/test_tool_audit.py -q` — the seven new tests must fail
   (`ImportError`), the twelve existing tests must pass. Record this RED state; it is the Phase 1 exit
   condition.
6. After row 1 lands, re-run the same command — all tests green (plan Phase 2 gate).

### Method

Helpers, exact final form:

```python
def _payload_with_serialized_len(n: int) -> dict[str, str]:
    """Build a {"q": ...} container whose serialized length is exactly n chars."""
    payload = {"q": ""}
    overhead = len(_json_dumps(payload))
    payload["q"] = "x" * (n - overhead)
    assert len(_json_dumps(payload)) == n
    return payload


def _logged_event(logger: MagicMock) -> dict:
    """Parse the single line the audit logger received."""
    logger.info.assert_called_once()
    return json.loads(logger.info.call_args[0][0])
```

Writer-side fixture setup for the new tests mirrors the existing pattern:
`ctx = _make_ctx()`, `ctx.services_required.audit_logger = MagicMock()`,
`ctx.cfg.tool.masked_fields = []`, `ctx.cfg.approval.approval_resource_keys = {}`
(the last two prevent `MagicMock` attribute fall-through from reaching
`_extract_resource_scope`, matching `TestAuditToolExec` `:136-138`).

Approval class, exact final form:

```python
class TestApprovalPreviewCap:
    def test_multi_kb_value_truncated(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        audit_approval(
            ctx, "write_file", "medium", _payload_with_serialized_len(4096), "approved"
        )
        event = _logged_event(ctx.services_required.audit_logger)
        preview = event["args_preview"]
        assert preview["truncated"] is True
        assert isinstance(preview["preview"], str)
        assert len(preview["preview"]) == AUDIT_ARGS_PREVIEW_MAX_CHARS
        assert set(preview.keys()) == {"preview", "truncated"}

    def test_exact_cap_unchanged(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        payload = _payload_with_serialized_len(AUDIT_ARGS_PREVIEW_MAX_CHARS)
        audit_approval(ctx, "write_file", "medium", payload, "approved")
        event = _logged_event(ctx.services_required.audit_logger)
        assert event["args_preview"] == payload
        assert "truncated" not in event["args_preview"]

    def test_cap_plus_one_truncated(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        payload = _payload_with_serialized_len(AUDIT_ARGS_PREVIEW_MAX_CHARS + 1)
        audit_approval(ctx, "write_file", "medium", payload, "approved")
        event = _logged_event(ctx.services_required.audit_logger)
        preview = event["args_preview"]
        assert preview["truncated"] is True
        assert preview["preview"] == _json_dumps(payload)[:AUDIT_ARGS_PREVIEW_MAX_CHARS]

    def test_mask_then_truncate_marker(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = ["secret"]
        ctx.cfg.approval.approval_resource_keys = {}
        payload = {"secret": "s3cr3t", **_payload_with_serialized_len(4096)}
        audit_approval(ctx, "write_file", "high", payload, "approved")
        logged = ctx.services_required.audit_logger.info.call_args[0][0]
        event = json.loads(logged)
        preview = event["args_preview"]
        assert "s3cr3t" not in logged
        assert preview["truncated"] is True
        assert '"secret"' in preview["preview"]
        assert isinstance(preview["truncated"], bool)
```

Tool-exec class, exact final form (same boundary pair through the second writer; call shape mirrors
`:140`, `request_id` non-empty so the writer does not skip the event):

```python
class TestToolExecPreviewCap:
    def test_multi_kb_value_truncated(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        audit_tool_exec(
            ctx, "read_text_file", _payload_with_serialized_len(4096), False, "req-cap-1"
        )
        event = _logged_event(ctx.services_required.audit_logger)
        preview = event["args_preview"]
        assert preview["truncated"] is True
        assert len(preview["preview"]) == AUDIT_ARGS_PREVIEW_MAX_CHARS

    def test_exact_cap_unchanged(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        payload = _payload_with_serialized_len(AUDIT_ARGS_PREVIEW_MAX_CHARS)
        audit_tool_exec(ctx, "read_text_file", payload, False, "req-cap-2")
        event = _logged_event(ctx.services_required.audit_logger)
        assert event["args_preview"] == payload
        assert "truncated" not in event["args_preview"]

    def test_cap_plus_one_truncated(self) -> None:
        ctx = _make_ctx()
        ctx.services_required.audit_logger = MagicMock()
        ctx.cfg.tool.masked_fields = []
        ctx.cfg.approval.approval_resource_keys = {}
        payload = _payload_with_serialized_len(AUDIT_ARGS_PREVIEW_MAX_CHARS + 1)
        audit_tool_exec(ctx, "read_text_file", payload, False, "req-cap-3")
        event = _logged_event(ctx.services_required.audit_logger)
        preview = event["args_preview"]
        assert preview["truncated"] is True
        assert preview["preview"] == _json_dumps(payload)[:AUDIT_ARGS_PREVIEW_MAX_CHARS]
```

### Details

- The seven tests map 1:1 to the plan `Tests` section: envelope (multi-KB), exactly-at-cap, cap+1 for
  both writers, and the mask-plus-truncation case (approval writer, where masking applies).
- `test_exact_cap_unchanged` (new) pins `DR-103` of row 1 (`<=` pass-through, not `<`);
  `test_cap_plus_one_truncated` (new) pins the envelope prefix equality contract.
- `set(preview.keys()) == {"preview", "truncated"}` pins the multi-KB case's "original keys not present
  at top level" requirement (plan `Tests`, first bullet) and rules out a hybrid container.
- `"s3cr3t" not in logged` plus `'"secret"' in preview["preview"]` demonstrates the mask-before-bound
  ordering: the masked key survives inside the retained prefix, the raw value appears nowhere.
- Boundary virtualization is safe here: no pre-existing test measures serialized length and no existing
  payload approaches 1500 chars (plan Revalidation record rows 4-5), so these tests create a new
  boundary without altering any existing behavior.

## Compatibility considerations

- Imports resolve only after row 1 lands; the intermediate RED state is the planned Phase 1 outcome, not
  a CI-fatal condition, provided rows 1-2 are merged in the same work item (plan Execution status step
  1 -> step 2).
- Existing classes (`TestLogApprovalDecision`, `TestMaskArgs`, `TestAuditApproval`, `TestAuditToolExec`,
  `TestWriteRoundExec`) and module helpers (`_make_cfg`, `_make_ctx`) are untouched; new names do not
  collide with them.
- `tests/agent/test_tool_approval_preflight.py` (`TestAuditApproval`, `:394-443`) and
  `tests/agent/test_audit_log_format.py` stay untouched; they are regression gates (plan Phase 2 command).
- Test count grows from 12 to 19; coverage contribution for `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new) and
  `_bounded_preview` (new) lines supports the plan's diff-cover >= 90% gate.

## Security considerations

- The mask-then-truncate test is itself the security regression: it fails if bounding ever runs before
  masking or if a truncated row ever contains a raw secret value.
- Test payloads are synthetic (`"x" * n`, `"s3cr3t"`); no production data or real secret strings are
  introduced into the test corpus.

## Rollback considerations

- Removing this row is a pure deletion of the two new classes, two helpers, and two import additions; no
  existing test depends on them.
- If row 1 is reverted while these tests remain, the suite fails with `ImportError` — the rollback note
  in the row-1 procedure applies: revert both rows together.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Phase 1 RED check | `uv run pytest tests/agent/test_tool_audit.py -q` (before row 1) | 7 new tests fail on `ImportError`; 12 existing tests pass |
| Phase 2 gate | `uv run pytest tests/agent/test_tool_audit.py -q` (after row 1) | 19/19 pass |
| Plan Phase 2 trio | `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_tool_approval_preflight.py tests/agent/test_audit_log_format.py -q` | All pass unchanged |
| Lint | `uv run ruff format --check tests/agent/test_tool_audit.py`; `uv run ruff check tests/agent/test_tool_audit.py` | Clean |
| Full gate | `uv run pytest tests/agent -q`; `uv run pytest tests/integration -q` (plan `AC-4`) | No new failures |

## Completion criteria

- REQ-005 / `AC-3`: multi-kilobyte case, exactly-at-cap case, and cap+1 case exist for **both** writers
  and pass, asserting recorded preview length and marker.
- REQ-004 distinction is demonstrated by `test_mask_then_truncate_marker` (new): boolean marker present,
  masked `"***"` content retained, raw value absent.
- The 12 pre-existing tests pass unchanged in Phase 1 and Phase 2.
- `uv run pytest tests/agent -q` and `uv run pytest tests/integration -q` report no new failure.

## Out of Scope

- Implementation in `scripts/agent/tool_audit.py` (row 1) and the docs statement (row 3).
- Non-serializable-`args` handling (no fallback exists in the frozen REQ-001 contract; row-1 procedure
  records the failure-mode equivalence instead).
- `write_round_exec` events (they carry no `args_preview` key; plan `Design` sink enumeration).
- MCP-side audit records and retention/rotation (plan `Scope`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Imports + helpers (`DR-101`, `DR-102`) | Completed | 20261024-233411 | 20261024-233411 | Helpers appended after `_make_ctx`; `shared.json_utils.dumps` import added per Method |
| 2 | `TestApprovalPreviewCap` (new) (4 tests) | Completed | 20261024-233411 | 20261024-233411 | REQ-005 approval half; appended after `TestWriteRoundExec` |
| 3 | `TestToolExecPreviewCap` (new) (3 tests) | Completed | 20261024-233411 | 20261024-233411 | REQ-005 tool-exec half |
| 4 | RED -> GREEN runs (Phase 1 -> Phase 2) | Completed | 20261024-233411 | 20261024-233411 | RED: collection-level `ImportError` (module-wide, not 7-of-19 as the procedure text expected — pytest cannot run existing tests when a module import fails); GREEN: 19/19 in target file, trio 119 passed, `tests/agent` 3691 passed, `tests/integration` 117 passed |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 4 | `test_mask_then_truncate_marker` failed: procedure test code assumed insertion-order serialization, but the writers' serializer (`shared.json_utils.dumps`, default `orjson.OPT_SORT_KEYS` — the same function this row's Assumptions name) sorts keys, so padding key `"q"` filled the retained prefix before `"secret"` | Yes: helper padding key renamed `"q"` -> `"z"` (sorts after `"secret"`); all four contract assertions of `DR-104` now hold; deviation from the procedure's "exact final form" helper text recorded | 20261024-233411 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | N/A |

**Reconcile note (2026-10-25):** the source fixes for this procedure landed on `origin/master` from a separate session (fix commit `73d714609`, archive commit `e6c0d6eef`). A second session independently re-executed and fully validated the same procedure on the pre-reset tree; `origin/master` was then adopted as canonical and the source state re-confirmed there with targeted tests.

## Traceability

- **Owning plan**: `plans/done/20261024-221315_args-preview-is-written-to-the-audit-log-unbounded.md` —
  row 2 of the `Implementation Target Files` table; plan `Implementation steps` Phase 1.
- **Source issue**: `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`
  (Testing Expectations: multi-KB value, exactly-at-cap, cap+1).
- **Plan requirements covered**: `REQ-005` (`AC-3`); measures the contracts of `REQ-001`, `REQ-002`,
  `REQ-004`.
- **Local design decisions**: `DR-101`..`DR-104` implement the plan Revalidation record's boundary rule
  ("derive both sides from `AUDIT_ARGS_PREVIEW_MAX_CHARS` (new) and pad from the serialized length")
  using the `GIT_SHOW_OUTPUT_MAX_CHARS` / `test_format_output.py` precedent.
- **Cross-row dependencies**: this row runs **before** row 1 (TDD-first, plan Phase 1 -> Phase 2);
  row 1 turning these tests green is the shared completion gate; row 3 documents the cap only after
  rows 1-2 land.
