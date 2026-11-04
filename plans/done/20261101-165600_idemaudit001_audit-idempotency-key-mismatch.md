## Goal
- Correct the documentation of the agent-side tool-execution idempotency key so the `tool_exec` audit event's `idempotency_key` field and the MCP dispatch doc accurately describe the two-key model established by `plans/done/20261101-105136_toolstate001_tool-call-state-producer.md`: the audit event records the workflow-scoped logical-call identity (`workflow_id:task_id:turn_id:call_id`), which is distinct from the deterministic transport `X-Idempotency-Key` used for server-side deduplication.

## Priority
Medium

## Scope
- **In-Scope**:
  - Correct the `ToolExecEvent.idempotency_key` field comment in `scripts/agent/shared/models.py` to state that it is the workflow-scoped logical-call identity recorded for the audit log, not the transport deduplication key, and that it differs from the `X-Idempotency-Key` header.
  - Extend `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` ("Idempotency and retry") with a sentence naming the agent-audit logical key and distinguishing it from the transport `X-Idempotency-Key`, so a reader cannot conflate the two.
  - Correct `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` ("Idempotency and Dedup Fields in the Audit Trace"): the audit record's `idempotency_key` is described there as the key the call was dispatched under and as matchable against the durable store and `tool_call_state` rows, and its synthetic example shows a transport-style hash. Added by amendment on 2026-11-04 with owner approval (scope class), after `plan-to-implementation-procedure` Step 3a found the claim.
- **Out-of-Scope**:
  - Changing which key the audit event records (the audit key stays `workflow_id:task_id:turn_id:call_id` per `toolstate001` REQ-009).
  - Changing the transport `derive_idempotency_key`/`X-Idempotency-Key` derivation, the `tool_call_state.idempotency_key`, or the dispatcher dedup cache (`scripts/shared/http_transport.py`, `scripts/agent/workflow/tool_call_state_ops.py`, `scripts/mcp_servers/dispatch.py`).
  - Any other audit field.
- **Dependencies**:
  - `plans/done/20261101-105136_toolstate001_tool-call-state-producer.md` (done): its REQ-009/D3 owner decision establishes the two-key model this Plan documents. This Plan must not contradict it — the audit key stays separate from the transport/state key. Non-blocking; it is the reference the Plan corrects toward.

## Background
The agent derives two distinct idempotency keys for a single tool call. `scripts/agent/tool_runner.py::_idempotency_key` composes `{workflow_id}:{task_id}:{turn_id}:{call_id}` and passes it to `audit_tool_exec`, so it lands in the `tool_exec` audit event's `idempotency_key` field. `scripts/shared/http_transport.py::HttpTransport.call` derives `derive_idempotency_key("call_tool", name, args, uid)` and sends it as the `X-Idempotency-Key` header, where `uid` is the transport session id (or an auth-token hash); the dispatcher's `_duplicate_cache` in `scripts/mcp_servers/dispatch.py` keys on that header. `plans/done/20261101-105136_toolstate001_tool-call-state-producer.md` resolved the ownership question (Issue `idemaudit001`) by deciding the audit key stays the workflow-scoped logical-call identity and the `tool_call_state` row uses the transport-identical key (REQ-003/D3, REQ-009) — two keys, distinct owners.

Verified against current source:
- `tool_runner._idempotency_key` builds `{workflow_id}:{task_id}:{turn_id}:{call_id}`; `execute_one_tool_call` passes it to `audit_tool_exec(..., idempotency_key=...)`. No caller reads `ToolExecEvent.idempotency_key` back (the `tool_call_state` recorder uses `tool_runner._state_key`, a different key).
- `HttpTransport.call` derives the transport key with `derive_idempotency_key("call_tool", name, args, uid)`, a deterministic hash of the method, the tool name, the canonical arguments, and `uid = _session_id or sha256(auth_token)`, and sends it as `X-Idempotency-Key`; the dispatcher's duplicate check in `dispatch.py` keys on that header value.
- `ToolExecEvent.idempotency_key` in `scripts/agent/shared/models.py` is documented as `# stable, retry-invariant key for deduplication`.
- `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` ("Idempotency and retry") documents the transport key's ownership and cache keying but names only the `X-Idempotency-Key`; it does not mention the agent-audit logical key.
- `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` ("Idempotency and Dedup Fields in the Audit Trace") says the audit record's `idempotency_key` is "the key the call was dispatched under" and can be matched against the durable store row and the `tool_call_state` row, and its synthetic example line carries a 64-character hex value. Both are wrong under the two-key model: the audit value is the workflow-scoped identity, which is neither the dispatched transport key nor the stored key (added by the 2026-11-04 amendment, `REQ-003`).

## Problem
The audit event's `idempotency_key` field is documented as a "key for deduplication", but the value written there (`workflow_id:task_id:turn_id:call_id`) is never used for deduplication — the transport `X-Idempotency-Key` is. No consumer reads the audit field, so the mislabel is invisible in code, yet a reviewer infers the audit record participates in deduplication when it only records a logical-call identity. The MCP dispatch doc describes only the transport key, so a reader of the docs has no record that the agent also emits a separate audit-side logical key and may assume the `X-Idempotency-Key` is the only idempotency key the agent produces.

## Reason for Change
The two-key model is now the implemented design (`toolstate001`), but the field description and the dispatch doc still describe a single-key world. Correcting them is cheap and prevents a future change from relying on or re-deriving the wrong key's semantics.

## Implementation Intent
Update the two documentation sites to describe the existing two-key model without changing any key's derivation or ownership: correct the `ToolExecEvent.idempotency_key` field comment to state it is the workflow-scoped logical-call identity recorded for the audit log and distinct from the transport dedup key; extend the dispatch doc's "Idempotency and retry" section to name the agent-audit logical key and distinguish it from the `X-Idempotency-Key`.

## Requirements
- `REQ-001`: The `idempotency_key` field comment in `scripts/agent/shared/models.py` states that the value is the workflow-scoped logical-call identity (`workflow_id:task_id:turn_id:call_id`) recorded for the audit log and is distinct from the transport `X-Idempotency-Key` used for server-side deduplication. (`scripts/agent/shared/models.py`; checked in Step 3)
- `REQ-002`: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` names the agent-audit logical key and states how it differs from the transport `X-Idempotency-Key`, without altering the existing transport-key description. (`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`; checked in Step 3)

- `REQ-003`: `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` describes the audit record's `idempotency_key` as the workflow-scoped logical-call identity (`workflow_id:task_id:turn_id:call_id`), states that it is not the key the call was dispatched under (the transport `X-Idempotency-Key`) and is not the key stored in the durable dedup store or the `tool_call_state` row, and its synthetic example line shows a value of that workflow-scoped shape. (`docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`; checked in Step 3a of `plan-to-implementation-procedure`)

## Implementation Target Files
**Freeze status**: `Frozen` (validated at `issue-to-plan` Step 8 on 20261101-165600:
`check_workitem_structure.py` clean; both rows `Verified`; `check_plan_target_overlaps.py`
reports no cross-plan overlap for either target file — `scripts/agent/shared/models.py`
and `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` appear in zero overlap findings).
Amended 2026-11-04 (scope): added docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md — The Idempotency and Dedup Fields section says the audit idempotency_key is the key the call was dispatched under and can be matched against the durable store and tool_call_state rows, and the example shows a transport-style hash; the audit key is the workflow-scoped logical-call identity, distinct from the transport key

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/shared/models.py` | Correct the `ToolExecEvent.idempotency_key` field comment to state it is the workflow-scoped logical-call identity recorded for the audit log and distinct from the transport dedup key | The field currently reads `# stable, retry-invariant key for deduplication`, which attributes dedup ownership to a value no consumer reads; the transport `X-Idempotency-Key` (and the `tool_call_state` key) owns dedup | REQ-001 / AC-1 | `ToolExecEvent.idempotency_key` field comment in `scripts/agent/shared/models.py`; `tool_runner._idempotency_key` composition (checked in Step 3a) | none (comment only) | Verified |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Add a sentence in "Idempotency and retry" naming the agent-audit logical key and distinguishing it from the `X-Idempotency-Key` | The section documents only the transport key's ownership and cache keying; the audit-side logical key is unnamed, so readers may conflate the two | REQ-002 / AC-2 | `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` section "Idempotency and retry" (checked in Step 3a) | docs checkers | Verified |
| `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Correct the audit-trace description of the tool_exec idempotency_key field and its example line | The Idempotency and Dedup Fields section says the audit idempotency_key is the key the call was dispatched under and can be matched against the durable store and tool_call_state rows, and the example shows a transport-style hash; the audit key is the workflow-scoped logical-call identity, distinct from the transport key | REQ-003 / AC-3 | docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md section 'Idempotency and Dedup Fields in the Audit Trace' (the sentence 'The record also carries idempotency_key (the key the call was dispatched under)' and the synthetic tool_exec example line); the audit value is built by tool_runner._idempotency_key (checked in Step 3a) | docs checkers | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `plans/done/20261101-105136_toolstate001_tool-call-state-producer.md` | The owner decision (REQ-003/D3 key identity, REQ-009 audit key stays separate) that defines the two-key model this Plan documents | `scripts/agent/shared/models.py` / `REQ-001` |
| `scripts/agent/tool_runner.py` | `_idempotency_key`, `_state_key`, and the `audit_tool_exec` call in `execute_one_tool_call` — the exact value the corrected field comment must describe | `scripts/agent/shared/models.py` / `REQ-001` |
| `scripts/shared/http_transport.py` | `derive_idempotency_key` and the `X-Idempotency-Key` emission in `HttpTransport.call` — the transport key the audit key is distinct from | `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` / `REQ-002` |

## Acceptance Criteria
- `AC-1` (`REQ-001`): `scripts/agent/shared/models.py` no longer labels the audit `idempotency_key` as a dedup key; the comment states it is the workflow-scoped logical-call identity recorded for the audit log and distinct from the transport `X-Idempotency-Key`.
- `AC-2` (`REQ-002`): `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` names the agent-audit logical key and states how it differs from the `X-Idempotency-Key`; the existing transport-key description is unchanged.

- `AC-3` (`REQ-003`): `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` no longer says the audit `idempotency_key` is the key the call was dispatched under or that it matches the durable store or `tool_call_state` row; it names the workflow-scoped logical-call identity, and the example line's `idempotency_key` has that shape.

## Tests
`N/A: documentation-only change; no code behavior changes.` Validation is via the doc checkers in the Validation plan.

## Documentation Impact
`docs/22_mcp/mcp_03_01_dispatch-and-routing.md` ("Idempotency and retry") — name the agent-audit logical key and distinguish it from the transport `X-Idempotency-Key` (`REQ-002`). Mapped via `routing.md` Docs → task mapping for the MCP domain; exact heading edits are decided at implementation. `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` ("Idempotency and Dedup Fields in the Audit Trace") — correct the audit-key description and the example line (`REQ-003`).

## Assumptions
- **A1**: The audit key's composition (`workflow_id:task_id:turn_id:call_id`) is intentionally kept separate from the transport key per `toolstate001` REQ-009; this Plan documents that decision and does not reopen it. Derived from the archived `toolstate001` plan, not an owner decision in this cycle.
- **A2**: Correcting a field comment cannot regress behavior (no consumer reads `ToolExecEvent.idempotency_key`), so the change is safe without a functional test. Derived from the caller inspection in Step 2.
- **A3**: `git-fame`/`pydeps`/`grimp` are unavailable in this environment; `Churn (30d)` and `Bus Factor` are judged from `git log` churn and marked where the tool is missing.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any external operator tooling (outside `scripts/`) reads the audit `idempotency_key` and depends on its current label | Not searched in operational tooling outside the repository | Non-blocking; the correction only removes a misleading label and adds clarity | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/shared/models.py` | Modify | Low (comment only; no behavior) | 2 | N/A (`git-fame` unavailable) | not applicable (rsynced) |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Modify | Low (doc only) | 4 | N/A (`git-fame` unavailable) | not applicable (rsynced) |
| `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Modify | Low (doc only) | 6 | N/A (`git-fame` unavailable) | not applicable (rsynced) |

## Design
This Plan makes one labeling decision:

**DD-1 — How far the correction goes.** Two options:
- **Option A — correct both sites to state the two-key model explicitly** (field comment names the logical-call identity + distinct-from-transport; doc adds the audit-key sentence). Selected.
- **Option B — minimal: fix only the clearly-wrong "for deduplication" label in `models.py` and leave the doc as-is.** Rejected: the doc's single-key framing is the more visible source of conflation and is what the Issue's AC-2 targeted.

Rationale: Option A fully resolves the Issue's AC-2 (the doc states who generates which key and what each identifies) while Option B leaves the primary conflation surface unaddressed.

## Implementation steps
1. **Phase 1: Documentation correction**
   - [ ] Correct the `ToolExecEvent.idempotency_key` field comment in `scripts/agent/shared/models.py` to state it is the workflow-scoped logical-call identity recorded for the audit log and distinct from the transport `X-Idempotency-Key` (`REQ-001`; `scripts/agent/shared/models.py`).
   - [ ] Extend "Idempotency and retry" in `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` to name the agent-audit logical key and distinguish it from the `X-Idempotency-Key`, leaving the transport-key description intact (`REQ-002`; `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`).
   - [ ] Correct the audit-trace description of the tool_exec idempotency_key field and its example line (REQ-003; `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md`) — amendment 2026-11-04
2. **Phase 2: Verification**
   - [ ] Run the doc checkers on the edited doc (`check_docs_quality.py`, `check_docs_structure.py`, `check_docs_consistency.py --domain mcp`) and confirm clean; confirm the `models.py` edit is comment-only and the existing audit tests stay green. (`REQ-001`, `REQ-002`, `AC-1`, `AC-2`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/shared/models.py` | Comment-only; no behavior | `uv run pytest tests/agent/test_tool_audit.py tests/agent/test_audit_log_format.py tests/agent/test_tool_runner.py` (audit event fields and the audit call in the runner) | existing tests pass unchanged |
| `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Doc structure/consistency | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_consistency.py --domain mcp` | clean; no findings |

## Risks
- **Risk**: Rewording the transport-key description and accidentally changing its meaning. → **Mitigation**: REQ-002 requires the transport-key description to stay unchanged; only an audit-key sentence is added; AC-2 checks the transport description is intact.
- **Risk**: The `models.py` comment correction is seen as cosmetic and out of scope. → **Mitigation**: the current label ("for deduplication") is factually wrong for a value no consumer reads; correcting it prevents a future change from relying on the wrong semantics (Reason for Change).
- **Risk**: `git-fame`/`pydeps`/`grimp` unavailable for Churn/Bus Factor. → **Mitigation**: judge from `git log` churn and mark `N/A` (Assumption A3).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Documentation correction in `scripts/agent/shared/models.py`, `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, and `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` | Completed | — | 20261104-130610 |  |
| 2 | Verification: doc checkers clean, `models.py` edit comment-only, existing audit tests pass | Completed | — | 20261104-130617 | Carried out by code-implementation: doc checkers clean for both docs, models.py AST-equal to HEAD (comment only), audit tests pass (targeted 164, full suite 11445 passed) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261104-124615_01_scripts_agent_shared_models.py.md | 1 | Procedure | Completed | — | — |
| implementations/20261104-124615_02_docs_22_mcp_mcp_03_01_dispatch-and-routing.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261104-124615_03_docs_22_mcp_mcp_06_06_end-to-end-tool-call-tracing.md.md | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261101-073823_idemaudit001_audit-idempotency-key-mismatch.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-165600
- **Related target files**: `scripts/agent/shared/models.py`, `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`, `docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md` — the full list of `File Path` values from `Implementation Target Files` above, once `Frozen`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem; Documentation Impact; Background (field comment in `models.py`) | `scripts/agent/shared/models.py` | Phase 1 | AC-1 | doc checker / comment review | Confirmed by repository evidence |
| REQ-002 | Problem; Testing Expectations; Background (doc section "Idempotency and retry") | `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` | Phase 1 | AC-2 | doc checker | Confirmed by repository evidence |
| REQ-003 | Amendment 2026-11-04: The Idempotency and Dedup Fields section says the audit idempotency_key is the key the call was dispatched under and can be matched against the durable store and tool_call_state rows, and the example shows a transport-style hash; the audit key is the workflow-scoped logical-call identity, distinct from the transport key | docs/22_mcp/mcp_06_06_end-to-end-tool-call-tracing.md | Phase 1 | AC-3 | doc checker | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261104-124615 -->