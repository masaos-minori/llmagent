# Implementation procedure: scripts/agent/repository_gateway.py

## Goal

Remove the redundant, provably-unreachable-without-prior-approval second
`run_approval_checks()` call from `RepositoryGateway._gate_write()`, so
`tool_runner._run_approval_gate()` becomes the sole authoritative
interactive approval gate, and correct the module/method docstrings that
currently describe the old "policy → approval → execution → audit" model.

## Scope

- In scope:
  - `scripts/agent/repository_gateway.py::_gate_write()` — delete the
    `risk = classify_risk(...)` / `if risk != RiskLevel.NONE:` block, the
    local `run_approval_checks` import, and the `tool_call_dict` it builds.
  - Remove the now-unused `RiskLevel` (from `agent.tool_enums`) and
    `classify_risk` (from `agent.tool_policy`) imports at module top.
  - Update the module docstring (lines 1-11) and `_gate_write()`'s
    docstring (line 88) to describe the single-gate model.
  - Add a code comment on `RepositoryGateway` documenting the load-bearing
    precondition: callers must route write/risky tool calls through
    `tool_runner.execute_all_tool_calls()` (or otherwise call
    `tool_approval.run_approval_checks()` themselves) before invoking
    `RepositoryGateway.execute()`.
  - `tests/test_repository_gateway.py`: delete
    `TestWritePolicy::test_write_tool_denied_by_user`; drop the
    `agent.repository_gateway.classify_risk` patch from
    `test_write_tool_approved_and_executed` and `TestAudit::test_audit_emitted_on_write`.
- Out of scope:
  - `tool_policy.check_preflight()` / `classify_operation_type()` — unchanged,
    kept as non-interactive defense-in-depth (line 90).
  - `check_approval()`, `_prompt_user_approval()`, risk-classification rules
    in `tool_approval.py` / `tool_policy.py`.
  - `tool_approval.run_approval_checks()`'s `skip_in_workflow_mode` removal
    — covered by a separate doc for `tool_approval.py`.
  - `tool_runner._run_approval_gate()`'s docstring fix and the new
    regression test in `tests/test_tool_runner.py` — covered by a separate
    doc for `tool_runner.py`.
  - `docs/*.md` updates (document-only phase; not permitted in this cycle).

## Assumptions

1. No production code path invokes `RepositoryGateway.execute()` /
   `_gate_write()` for a write/risky tool call without first passing
   through `tool_runner.execute_all_tool_calls()`'s `_run_approval_gate()`
   (verified in the source plan via repo-wide grep of `RepositoryGateway`
   call sites: only `factory.py`, `context.py`, and `tool_runner.py`
   reference it in production code; `tool_runner.py`'s only call to
   `gateway.execute()` is strictly after the batch approval gate has
   filtered `tool_calls` into `approved_calls`).
2. `check_preflight()` remains safe to call twice per write tool call
   (once inside `check_approval()`, once directly in `_gate_write()`)
   since it is non-interactive and idempotent; not addressed by this change.

## Design decisions

- Delete the redundant call site rather than thread an "already-approved
  call id" signal through `RepositoryGateway.execute()`'s signature: the
  current call graph makes deletion provably safe today, and threading a
  new id/state mechanism is materially more invasive for a benefit
  (defense-in-depth against a hypothetical future direct caller) that a
  documented precondition + regression test also covers.
- Keep `check_preflight()` in `_gate_write()` untouched — it is a cheap,
  non-interactive policy check with no user-facing side effect, so
  removing it is not required to fix the double-prompt defect.
- Encode the new precondition (approval must happen upstream) as both a
  docstring update and an inline code comment, so it is visible to future
  authors who might add a new `RepositoryGateway.execute()` call site.

## Alternatives considered

- **Thread an approved-call-id/set through `AgentContext` or
  `RepositoryGateway.execute()`'s signature** (Option (a) in the source
  plan): rejected — requires changing the public `execute()` signature,
  updating every call site and test that constructs/calls it directly,
  and adding new mutable lifecycle state to clear per turn/round. Larger
  surface area than the defect warrants.
- **Leave both approval calls in place and rely on idempotent
  double-prompting**: rejected — this is the exact defect being fixed
  (the user sees two prompts for one logical tool call).

## Implementation

### Target file

`scripts/agent/repository_gateway.py` (plus `tests/test_repository_gateway.py`)

### Procedure

1. In `_gate_write()` (currently lines 81-123), delete the block:
   - `risk = classify_risk(self._cfg, tool_name, args)`
   - `if risk != RiskLevel.NONE:` and its body (the local
     `from agent.tool_approval import run_approval_checks` import, the
     `tool_call_dict` construction, the `await run_approval_checks(...)`
     call, and the `if tool_name in denied_ids or not approved_calls:`
     denial branch).
   - Leave `check_preflight()` (line 90) and the
     execute/audit tail (lines 114-123) untouched.
2. Remove `RiskLevel` from the `from agent.tool_enums import ...` line and
   `classify_risk` from the `from agent.tool_policy import ...` line at
   the top of the file — both become unused once step 1 lands.
3. Update the module docstring (lines 1-11): change step 2 of the
   4-step list from "Approval prompt (tool_approval.run_approval_checks
   per call)" to describe that approval is enforced upstream, once, by
   `tool_runner.execute_all_tool_calls()`'s batch-level gate, before any
   tool call reaches this executor.
4. Update `_gate_write()`'s docstring (line 88) from "Enforce policy,
   prompt for approval, execute, audit." to something like "Enforce
   policy, execute, audit. Approval is expected to have already been
   granted by the caller's batch-level gate; this method does not
   prompt."
5. Add an inline comment (e.g. above the class definition or above
   `_gate_write()`) stating the precondition: write/risky tool calls must
   be pre-approved by `tool_runner.execute_all_tool_calls()`'s
   `_run_approval_gate()` (or an equivalent caller-side
   `run_approval_checks()` call) before reaching `RepositoryGateway.execute()`.
6. In `tests/test_repository_gateway.py`:
   - Delete `TestWritePolicy::test_write_tool_denied_by_user` (lines
     104-131 as currently laid out) — the behavior it asserts
     (gateway independently denying via `run_approval_checks`) no longer
     exists at this layer. Equivalent denial coverage remains via
     `tests/test_tool_runner.py::test_denied_tool_call_is_returned_as_tool_message`
     and `test_execute_all_tool_calls_does_not_bypass_approval`.
   - In `test_write_tool_approved_and_executed` and
     `TestAudit::test_audit_emitted_on_write`, remove the
     `patch("agent.repository_gateway.classify_risk", return_value=RiskLevel.NONE)`
     context manager entry — `classify_risk` is no longer imported/called
     by the gateway, so patching it is now meaningless (and would error
     if the reference is removed from the module).
   - If `RiskLevel` becomes unused in the test module after this change,
     drop it from the `from agent.tool_enums import ...` import there too.

### Method

Direct, surgical deletion of the identified block plus docstring text
edits; no new abstractions, no behavior added. Test changes are deletions
and patch-list trims only — no new test infrastructure needed.

### Details

- Post-change `_gate_write()` shape: `check_preflight()` →
  `self._executor.execute(tool_name, args)` → audit emission → return
  `result`. No approval-related code remains in this method.
- Verify no other reference to `RiskLevel`/`classify_risk` remains in
  `repository_gateway.py` before removing the imports (confirmed by the
  source plan's U3: both symbols are used only in the block being deleted).

## Compatibility considerations

- `RepositoryGateway.execute()`'s public signature is unchanged — no
  caller-visible API break.
- Denied-write behavior surfaces one layer higher (at the
  `tool_runner.execute_all_tool_calls()` batch gate) instead of at the
  gateway; this is already the enforced order today (per Assumption 1),
  so no observable behavior change for any current caller.

## Security considerations

- The gateway no longer independently enforces interactive approval for
  write/risky tools; it now relies entirely on the caller having already
  run the batch-level gate. This is documented as a load-bearing
  precondition (docstring + inline comment) so a future direct caller of
  `RepositoryGateway.execute()` that skips `execute_all_tool_calls()`
  would silently lose interactive approval (only non-interactive
  `check_preflight()` would still run). Mitigated by: (1) the docstring/
  comment, (2) the regression test added in the `tool_runner.py` doc
  pinning the single-approval invariant end-to-end.
- No change to policy enforcement (`check_preflight()`), audit emission,
  or risk-classification rules themselves.

## Rollback considerations

- Revert is a single-file source change (plus its paired test-file edits):
  re-add the deleted `risk = classify_risk(...)` / approval block and
  restore the removed imports and docstrings; re-add the deleted/edited
  tests. No data migration, no config, no persisted state involved.

## Validation plan

- `ruff check scripts/agent/repository_gateway.py` — 0 errors, no
  unused-import (F401) findings after the `RiskLevel`/`classify_risk`
  import removal.
- `mypy scripts/agent/` — no new errors.
- `pytest tests/test_repository_gateway.py -q` — all pass after the
  rewrite (denial test removed, `classify_risk` patches dropped).
- `vulture scripts/agent/repository_gateway.py --min-confidence 80` — no
  new findings from the removed block.
- Full-suite run (`pytest -q`) is validated jointly with the
  `tool_approval.py` and `tool_runner.py` docs' changes, since all three
  files/tests must land together for the suite to pass (see those docs'
  Validation plans).

## Out of scope

- `scripts/agent/tool_approval.py`'s `skip_in_workflow_mode` removal.
- `scripts/agent/tool_runner.py`'s `_run_approval_gate()` docstring fix
  and the new end-to-end regression test.
- Any workflow-mode-specific wiring (confirmed dead / not applicable).
- `docs/*.md` updates.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-093740_plan.md
- Source implementation procedure: N/A
- Generated at: 20260726-101359
- Related target files: repository_gateway.py
