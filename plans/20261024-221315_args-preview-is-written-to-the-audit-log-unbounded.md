# Plan: `tool_audit.py` — bound `args_preview` written to the audit log

## Goal
- Implement one documented size cap for the `args_preview` field written by both agent-side audit
  writers in `scripts/agent/tool_audit.py`, with an explicit truncation marker that cannot be
  confused with masking output, so no tool call can grow the audit log through unbounded argument
  payloads.

## Priority
Medium

## Scope
- **In-Scope**: a shared private bound helper in `scripts/agent/tool_audit.py` applied to the
  `args_preview` value of both writers (`audit_approval()` and `audit_tool_exec()`); a module
  constant for the cap; regression tests in `tests/agent/test_tool_audit.py`; a documentation
  statement in `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`.
- **Out-of-Scope**: which keys are masked and the default `masked_fields` value (separate issue
  `issues/20261024-124138_tool005_default-masked-fields-names-match-no-real-tool-argument.md`);
  approval-preview behavior (unmasked by decision in `plans/20261023-072425_plan.md`); audit-log
  retention/rotation (`docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`); MCP-side
  audit records (`mcp_servers/audit.py`); the plan-mode blocked notice output (verified to be a UI
  write, not an audit sink — see Design).
- **Dependencies**: `plans/20261023-072425_plan.md` — closed (located at
  `plans/done/20261023-072425_plan.md`). No blocking dependency: masking and bounding are ordered
  (mask first, then bound) so its `AC-2` stays satisfiable. Note: its `REQ-002` recursive masking
  has already landed (`mask_args` now masks at any depth, verified 2026-10-24).

## Background
Found while converting `plans/20261023-072425_plan.md` into implementation procedures on 2026-10-24.
Re-verified on 2026-10-24 against current source: both writers pass the entire masked container
(`args_preview=masked` at `scripts/agent/tool_audit.py:58` and `:169`); the event fields are
unbounded `dict[str, object]` (`scripts/agent/shared/models.py:23`, `:55`); `grep -rn
"args_preview" scripts/` returns only the two writers, the two model fields, and
`scripts/agent/tool_approval.py:221-222`; `grep -rn "args_preview" docs/` is empty.

## Problem
Every audit row embeds the full masked argument container. `mask_args()` never removes keys and
never shortens unmasked values (verified in `scripts/agent/tool_result_formatter.py` `_mask_value`:
keys are preserved, unmasked values are recursed unchanged), so a call carrying a large unmasked
value (e.g. a file body passed to a write tool) is persisted in full. The concrete sink was
identified during this pass (the Issue marked it `Needs confirmation`): `_build_audit_logger()` in
`scripts/agent/factory.py:73-78` constructs `shared.logger.Logger("audit",
ctx.cfg.obs.audit_log_file, structured_log=True)` (default `/opt/llm/logs/audit.log`,
`scripts/agent/config_builders.py:146-147`), and neither `Logger` nor `_JsonFormatter` truncates
(`scripts/shared/logger.py:139-230`, `:116-138`; `_RedactionFilter` only replaces registered secret
strings, it does not bound size). Production measurement 2026-10-24: `/opt/llm/logs/audit.log`
123,795 bytes with every line exactly 134 chars — no truncation evidence, and no large-argument
row has appeared yet.

## Reason for Change
Audit rows are written on every tool call. An unbounded field in a durability-critical shared log
is a disk-usage concern; the behavior must either be capped or explicitly documented. The Issue
accepts either outcome; this Plan chooses the cap because the sink chain was verified to contain no
bound anywhere.

## Implementation Intent
Add one private helper in `scripts/agent/tool_audit.py` that both writers already share as their
single pass-through point: bound the masked container before it is stored in the event. Common-size
payloads (all rows measured today are 134 chars) pass through byte-for-byte unchanged; only
oversized payloads are replaced by a self-describing envelope carrying a truncated prefix of the
serialized preview. Document the cap in the chapter that owns agent-side audit events.

## Requirements
- `REQ-001`: `scripts/agent/tool_audit.py` gains a module constant `AUDIT_ARGS_PREVIEW_MAX_CHARS`
  (value 1500, owner-revisable) and a private `_bounded_preview(masked: dict) -> dict` helper:
  serialize `masked` with `_json_dumps`; if the serialized length is at most the cap, return the
  container unchanged; otherwise return the envelope `{"preview": <serialized prefix capped at
  AUDIT_ARGS_PREVIEW_MAX_CHARS>, "truncated": True}`.
- `REQ-002`: Both writers (`audit_approval()` and `audit_tool_exec()`) store
  `args_preview=_bounded_preview(masked)`; masking stays before bounding. `grep -rn "args_preview"
  scripts/` shows every writer going through the helper.
- `REQ-003`: Event shape is preserved: `args_preview` remains a dict (the envelope is a dict), the
  event is still emitted as one JSON line via `dataclasses.asdict(evt)`, and every field of
  `scripts/agent/shared/models.py` is unchanged (the field stays unbounded-typed; bounding happens
  at the writers, the shared choke point).
- `REQ-004`: The truncation marker is the JSON boolean key `"truncated"` plus the restructured
  envelope — structurally distinct from the masked value `"***"` (a string), so truncation can
  never be mistaken for masking.
- `REQ-005`: Regression tests measure the decided behavior: a multi-kilobyte argument value, one
  case at exactly the cap, one char over it, for both writers, asserting the recorded preview
  length and marker per REQ-001.
- `REQ-006`: `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md` states the
  cap value, the envelope shape, and that truncation applies after masking.

## Implementation Target Files
**Freeze status**: Frozen (validated 2026-10-24 per `rules/workflow-lifecycle.md` Implementation
Target Files Validation (Plan Freeze) — all rows `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/tool_audit.py` | Add `AUDIT_ARGS_PREVIEW_MAX_CHARS` and `_bounded_preview()`; call it at both `args_preview=` sites | The only two sinks that persist `args_preview` live in this file; one helper covers both writers | REQ-001, REQ-002, REQ-003, REQ-004; AC-1, AC-2 | `args_preview=masked` measured at `:58` and `:169` (2026-10-24); `_json_dumps` already imported/used in this module | `tests/agent/test_tool_audit.py` | Verified |
| `tests/agent/test_tool_audit.py` | Add cap regression tests for both writers incl. exactly-at-cap and cap+1 boundary cases | Existing tests assert event fields but never payload size; the decided behavior needs measured coverage | REQ-005; AC-3 | File exists with `MagicMock` audit-sink pattern (`test_logs_structured_event` etc., read 2026-10-24); `tests/agent/test_tool_approval_preflight.py` `TestAuditApproval` (`:394+`) provides the pattern the Issue cites | this file | Verified |
| `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md` | Document the cap and envelope in the audit-event contract | The Issue's "no docs chapter names auditing" hint is disconfirmed: this is the agent-side audit chapter (`audit-and-otel`), and it already documents the JSON-lines event format and `tool_approval`/`tool_exec` events | REQ-006; AC-5 | Chapter exists; `:48` states JSON-lines format, `:50` references `tool_approval`/`tool_exec` writers (read 2026-10-24); `grep -rn "args_preview" docs/` empty | docs gates in Validation plan | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/factory.py` (`:73-78`) | Identifies the concrete `ctx.services_required.audit_logger` (the Issue's `Needs confirmation` item): `shared.logger.Logger("audit", cfg.obs.audit_log_file, structured_log=True)`; unmodified | `scripts/agent/tool_audit.py`; REQ-001 |
| `scripts/shared/logger.py` | `Logger`/`_JsonFormatter`/`_RedactionFilter` verified to add no size bound (the cap belongs in the writers, not the sink); unmodified | `scripts/agent/tool_audit.py`; REQ-001 |
| `scripts/agent/shared/models.py` | `args_preview: dict[str, object]` (`:23`, `:55`) stays unchanged by design; envelope is still a dict | REQ-003 |
| `scripts/agent/tool_approval.py` (`:221-222`) | Plan-mode blocked notice: `masked_preview` goes to `emit_plan_blocked` → `OutputPort` UI write (`scripts/agent/tool_output.py:49-55`), not the audit logger — verified non-sink, stays unmodified | Scope exclusion, recorded in Design |
| `scripts/agent/repository_gateway.py` (`:109-110`), `scripts/agent/tool_audit.py` `write_round_exec` (`:182-215`), `scripts/agent/audit_event_emitter.py`, `scripts/agent/commands/cmd_memory.py` | All other `audit_logger.info` call sites enumerated 2026-10-24; none persists `args_preview` — sink enumeration complete per the Issue's Required Changes | REQ-002 |
| `tests/agent/test_audit_log_format.py` | Contract test asserting required fields of agent-side JSON-lines events; must stay green with the envelope shape | REQ-003 |
| `docs/22_mcp/mcp_06_05_reading-audit-logs.md` | Documents the shared `audit.log` including agent-side `tool_exec` example rows; its jq/grep usage examples filter on `event`/`tool`, not on `args_preview` sub-keys, so the envelope breaks no documented usage; unmodified unless the docs gate requires a cross-reference | REQ-006 |
| `plans/done/20261023-072425_plan.md` (`AC-2`, `Assumptions`) | Source of the ordering constraint (masking before bounding) and the recursive-masking dependency that has already landed | REQ-002 |

## Acceptance Criteria
- AC-1 (REQ-001): With a large argument value, the audit row's `args_preview` is the envelope
  (`preview` string of at most 1500 chars + `"truncated": true`); no cap-free container is written.
- AC-2 (REQ-002): `grep -rn "args_preview" scripts/` shows both writers storing
  `_bounded_preview(...)`; no writer bypasses the helper.
- AC-3 (REQ-005): A regression test writes an audit event with a multi-kilobyte argument value and
  asserts the recorded preview matches the decided behavior, including exactly-at-cap and cap+1
  cases for both writers.
- AC-4: `uv run pytest tests/agent -q` and `uv run pytest tests/integration -q` pass with no new
  failure (`tests/integration` verified 2026-10-24 to contain no `args_preview` references).
- AC-5 (REQ-006): The cap is stated in `agent_10_02` and the docs gates report no findings.

## Tests
- Unit (REQ-005): `audit_approval()` with a >1500-char serialized argument container → envelope:
  `len(preview) <= 1500`, `"truncated": True`, original keys not present at top level.
- Unit (REQ-005): serialized length exactly at the cap → container stored unchanged, no
  `"truncated"` key; cap+1 → envelope. (Boundary pair per the Issue's Testing Expectations.)
- Unit (REQ-004/REQ-005): large container containing a masked key → payload contains `"***"` before
  the cut, contains no raw secret, and carries the boolean marker — demonstrating truncation is
  distinguishable from masking.
- Unit (REQ-005): same three cases through `audit_tool_exec()` (the second writer).
- Regression (REQ-003): existing `tests/agent/test_tool_audit.py`,
  `tests/agent/test_tool_approval_preflight.py` (`TestAuditApproval`), and
  `tests/agent/test_audit_log_format.py` pass unchanged.
- Lint (REQ-001): `ruff`/`mypy` clean on the changed files.

## Documentation Impact
Required, one entry, driven by REQ-006:
- `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`: state the cap value
  (`AUDIT_ARGS_PREVIEW_MAX_CHARS = 1500` chars of serialized preview JSON), the envelope shape
  (`{"preview": ..., "truncated": true}`), and the mask-before-bound ordering. The Issue's pointer
  at `docs/41_db/` or `docs/40_shared/` is corrected by verification: `agent_10_02` is the agent-side
  audit-event chapter (`audit-and-otel`); `41_db/db_06` covers only retention/rotation (out of scope).
- `docs/22_mcp/mcp_06_05_reading-audit-logs.md` is the shared-log reader doc; no edit planned —
  its usage examples do not consume `args_preview` sub-keys (verified 2026-10-24).

## Assumptions
- Cap policy decided (Issue open question "character or byte?"): character count of the serialized
  preview string produced by `_json_dumps`. Rationale: `_json_dumps` returns `str`; the cap governs
  the `preview` field content; envelope keys add a small fixed overhead outside the cap, documented
  in `agent_10_02`. Owner may switch to bytes later without changing writer structure.
- Cap value 1500 is this Plan's decision (module constant, owner-revisable per the Issue's own
  constraint that the value live in a constant or config). Measured rows are 134 chars today, so the
  pass-through path is unchanged for all observed traffic.
- A module constant (not `[tool]` config) is the correct boundary: the Issue allows either, and
  avoiding a `/opt/llm/config/agent.toml` edit keeps shared production config out of scope.
- `args_preview`'s type and the one-JSON-line format stay compatible with existing readers; no repo
  consumer parses `args_preview` sub-keys (verified: only `tool_audit.py` writers and tests).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | None open. The Issue's two unresolved questions were closed by this pass: the `audit_logger` implementation is identified (`factory.py:73-78` → `shared.logger.Logger`, verified to add no truncation), and the char-vs-byte question is decided in Assumptions. | — | — | — |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_audit.py` | Modify (helper + 2 call sites; public function signatures unchanged) | Medium — imported by `tool_runner.py`, `tool_approval.py`, `workflow_engine_adapter.py`, `tool_run_recorder.py`; none can observe the internal helper or envelope unless payloads exceed the cap | 1 | High (single author) | rsynced (deployed) — deployed file must be synced |
| `tests/agent/test_tool_audit.py` | Modify (add tests) | Low | 2 | High | rsynced |
| `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md` | Modify (one subsection) | Low | 13 | High | rsynced |

## Design
- **Task size**: Path A. Verified target count is 3 files; the Issue's 4-area list narrowed during
  verification (`models.py` unchanged by design; `tool_approval.py:221-222` proven to be a UI output
  write, not an audit sink) and gained one docs chapter.
- **Architecture**: `scripts/agent` stays within its `importlinter` contracts — the change is
  internal to `tool_audit.py`; no new imports cross layers (helper uses the module's existing
  `_json_dumps`). The sink (`shared/logger.py`) is deliberately not modified: it is shared with
  MCP-side and gateway logging where a bound would be wrong.
- **Choke-point choice**: both writers already compute `masked = mask_args(...)` and then set
  `args_preview=masked`; wrapping that single assignment site with `_bounded_preview(masked)` is the
  "one place all audit writers share" the Issue asks for, without changing event models or the
  `Logger` sink.
- **Order**: mask first, bound second. Consequence: the retained prefix of a truncated preview
  contains the masking output produced by `mask_args` (closed-plan `AC-2` shows `"***"` at masked
  paths whenever the payload fits under the cap; oversized payloads are replaced wholesale).
- **Sink enumeration (Issue Required Changes, completed 2026-10-24)**: `args_preview` sinks =
  `tool_audit.py:58` (`tool_approval` event) and `tool_audit.py:169` (`tool_exec` event). Verified
  non-sinks: `tool_approval.py:221-222` (UI `emit_plan_blocked`), `repository_gateway.py:109-110`
  (fixed-format `gateway.write` line, no args — matches the uniform 134-char production rows),
  `write_round_exec` (`round_exec` event, no args), `audit_event_emitter.py` and `cmd_memory.py`
  (no args fields). Today's row-size measurement: min = max = 134 chars over the whole
  `/opt/llm/logs/audit.log`.
- **Truncation marker (constraint: not confusable with masking)**: masking emits the string value
  `"***"`; truncation emits a structural change — the top-level container is replaced by
  `{"preview": <string>, "truncated": true}`. A reader distinguishes them by the presence of the
  boolean key, never by string content.

## Implementation steps
1. **Phase 1: Failing regression tests first**
   - [ ] Add to `tests/agent/test_tool_audit.py`: envelope case for `audit_approval()` with a
     multi-kilobyte value, exactly-at-cap case, cap+1 case, mask-plus-truncation case, and the same
     three cases for `audit_tool_exec()` (REQ-005; `tests/agent/test_tool_audit.py`). Expect these
     tests to fail against the current tool.
2. **Phase 2: Bounded preview in the writers**
   - [ ] In `scripts/agent/tool_audit.py`, add `AUDIT_ARGS_PREVIEW_MAX_CHARS = 1500` and
     `_bounded_preview()` per REQ-001; change both `args_preview=masked` sites to
     `args_preview=_bounded_preview(masked)` (REQ-001, REQ-002, REQ-003, REQ-004;
     `scripts/agent/tool_audit.py`).
   - [ ] Run `uv run pytest tests/agent/test_tool_audit.py
     tests/agent/test_tool_approval_preflight.py tests/agent/test_audit_log_format.py -q` — all
     pass (REQ-003, REQ-005).
3. **Phase 3: Documentation and full validation**
   - [ ] Add the cap/envelope/ordering statement to `agent_10_02`'s audit-event section (REQ-006;
     `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`).
   - [ ] Verification pass: AC-2 grep; docs gates required by `routing.md` for a `docs/*.md` edit
     (`check_docs_quality.py`, `check_docs_structure.py "docs/**/*.md"`,
     `check_docs_content_policy.py`); `rules/toolchain.md` sequence (`ruff format`/`check`,
     `mypy --no-namespace-packages scripts/`, `bandit -r scripts/ -c pyproject.toml -ll`,
     `PYTHONPATH=scripts uv run lint-imports`, `uv run pytest tests/agent -q`,
     `uv run pytest tests/integration -q`, coverage + diff-cover ≥ 90% on changed lines,
     `uv run pre-commit run --all-files`). Deploy step: the change touches a deployed `scripts/`
     file — `deploy.sh` sync applies, then confirm the running agent services pick up the new file
     on their next restart per `skills/deploy/SKILL.md`.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_audit.py` | Unit (new tests) + manual grep | `uv run pytest tests/agent/test_tool_audit.py -q`; `grep -rn "args_preview" scripts/` | New cap tests pass; both writers show `_bounded_preview(masked)` |
| `scripts/agent/tool_audit.py` | Lint/type | `uv run ruff format --check scripts/agent/tool_audit.py`; `uv run ruff check scripts/agent/tool_audit.py`; `uv run mypy --no-namespace-packages scripts/` | Clean |
| `tests/agent/test_tool_audit.py` | Regression | `uv run pytest tests/agent -q` incl. `test_tool_approval_preflight.py` and `test_audit_log_format.py` | All existing audit tests pass unchanged |
| Whole change | Integration | `uv run pytest tests/integration -q` | No new failure |
| `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md` | Docs gates | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py "docs/**/*.md"`; `uv run python tools/check_docs_content_policy.py` | No findings |
| Whole change | Full sequence | `rules/toolchain.md` sequence incl. coverage + `diff-cover` ≥ 90% on changed lines, `uv run pre-commit run --all-files` | No new failures; diff coverage ≥ 90% |
| Deployed runtime | Operational | `deploy.sh` sync + service restart + `tail <audit.log>` smoke: one normal tool call keeps a plain `args_preview` | Row unchanged for sub-cap payloads |

## Risks
- **Risk**: downstream readers parsing `args_preview` sub-keys would break when the envelope
  replaces the container. → **Mitigation**: verified 2026-10-24 that no repo code or documented
  usage reads sub-keys (`mcp_06_05` examples filter on `event`/`tool` only); envelope is applied
  only above 1500 chars, which no measured production row has approached (max 134).
- **Risk**: truncation could hide a masked path making a security review think a secret was absent
  rather than masked. → **Mitigation**: mask-before-bound ordering plus the explicit `truncated`
  boolean; the docs section states oversized rows must be treated as structurally reduced.
- **Risk**: cap too small for real approval-audit forensics. → **Mitigation**: constant is a single
  module-level value (owner-revisable); decision recorded in `agent_10_02` so the number is
  discoverable, satisfying the Issue's "undocumented behavior is not acceptable" in either case.
- **Risk**: shared `audit.log` is also written by MCP servers whose records are not bounded by this
  change. → **Mitigation**: explicitly out of scope (Issue's Out of Scope + this Plan's Scope);
  documented boundary in `agent_10_02` wording refers to agent-side events only.
- **Risk**: `agent_10_02` is high-churn (13 commits/30d). → **Mitigation**: single subsection edit;
  `plan-to-implementation-procedure` Step 2 revalidates the row before procedure generation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: add cap regression tests (`tests/agent/test_tool_audit.py`) | Pending | — | — | REQ-005 |
| 2 | Phase 2: `AUDIT_ARGS_PREVIEW_MAX_CHARS` + `_bounded_preview()` at both writers (`scripts/agent/tool_audit.py`) | Pending | — | — | REQ-001, REQ-002, REQ-003, REQ-004 |
| 3 | Phase 3: docs update (`agent_10_02`) + full validation + deploy sync | Pending | — | — | REQ-006 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at plan generation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261024-124138_tool005-args-preview-is-written-to-the-audit-log-unbounded.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261023-072425_plan.md` (`Assumptions`, `AC-2` ordering constraint)
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261024-221315
- **Related target files**: `scripts/agent/tool_audit.py`, `tests/agent/test_tool_audit.py`, `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem + Required Changes (cap policy, marker, constant); sink chain read 2026-10-24 | `scripts/agent/tool_audit.py` | Phase 2 | AC-1 | unit tests: envelope, boundary pair | Confirmed by repository evidence |
| REQ-002 | Problem `:58`/`:169` reproduced 2026-10-24; Required Changes "one place all audit writers share" | `scripts/agent/tool_audit.py` | Phase 2 | AC-2 | grep check + unit tests for both writers | Confirmed by repository evidence |
| REQ-003 | Constraints (event shape, `models.py` fields read 2026-10-24) | `scripts/agent/tool_audit.py` | Phase 2 | AC-4 | `test_audit_log_format.py`, existing audit tests | Confirmed by repository evidence |
| REQ-004 | Constraints (marker not confusable with `***`) | `scripts/agent/tool_audit.py` | Phase 2 | AC-1 | unit test: mask-plus-truncation case | Explicit in issue |
| REQ-005 | Testing Expectations (multi-KB value, exactly-at-cap, cap+1) | `tests/agent/test_tool_audit.py` | Phase 1, Phase 2 | AC-3 | `uv run pytest tests/agent/test_tool_audit.py -q` | Explicit in issue |
| REQ-006 | Documentation Impact; chapter ownership corrected by verification (`agent_10_02` exists) | `docs/23_agent/agent_10_02_operations-and-observability-audit-and-otel.md` | Phase 3 | AC-5 | docs gates in Validation plan | Confirmed by repository evidence |
