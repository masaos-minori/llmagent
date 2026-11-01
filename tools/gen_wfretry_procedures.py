"""Generate the wfretry001 implementation-procedure documents (batch 20261101-165312)
in the canonical 14-section format used by batches 20261101-140834, 20261101-145309,
and 20261101-163219.

Skeletons were created by `tools/generate_workitem.py --kind implementation-procedure
--all-rows` (shared pass timestamp recorded in the Plan). This script rewrites each
body from the verified content below.
Run: `uv run python tools/gen_wfretry_procedures.py`.
"""

from __future__ import annotations

from pathlib import Path

BATCH = "20261101-165312"
PLAN = "plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md"
ISSUE = "issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md"
GENERATED_AT = "20261101-165312"

COMMON_ASSUMPTIONS = [
    f"Plan `{PLAN}` is Frozen; its 12-row `Implementation Target Files` table is the canonical scope and every target of this procedure is a row of that table (re-verified 2026-11-01: all 12 paths exist on `master`, no row replaced).",
    "All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record'); drifted citations carry `(re-verified 2026-11-01)` markers.",
    "Canonical semantics come from the Plan REQs (Plan `:38-48`): `retry_policy.retry_on` list drawn from `exception`/`timeout`/`llm_failure` with default `[\"exception\"]` (REQ-001); deadline-versus-inner timeout classification via the deadline's `expired()` state (REQ-002); every failed attempt consumes one budget unit and ineligible kinds are terminal at once (REQ-003); typed outward kinds `workflow_halted` / `workflow_timeout` on the `(answer, error_kind, is_partial)` tuple (REQ-004); LLM-level failure results enter the engine as stage failures of kind `llm_failure` (REQ-005); per-attempt side-effect flag on `TurnState` set by `tool_runner` (REQ-006); attempt kinds `timeout`/`exception`/`llm_failure` distinct from outward kinds (REQ-007); no turn ends with empty answer, `error_kind` `None`, and a `halted`/`failed` task (REQ-008).",
    "Owner decisions (Plan UNK-01, UNK-02, 2026-10-30): timeouts and LLM-failure results are not retried by default; the shipped `retry_on` pins this, and the landed engine already treats timeouts as terminal (`workflow_engine.py:208-209`, re-verified 2026-11-01).",
    "Landing order (Plan Assumptions 'Re-verification record'): this batch lands after the pending procedure batches in plan order — wftaskapi001 `20261101-140834`, wfrecovery001 `20261101-145309`, wflease001 `20261101-163219` — so shared-file edits (`workflow_engine.py`, `models.py`, `workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `docs/23_agent/agent_03_03_...md`) rebase predictably. The wfrecovery001 Phase 4 attempt/budget contract itself is already landed on `master` (per-attempt event ids `{task_id}:{stage_id}:{attempt}`, `begin_stage_if_new` at `workflow_engine.py:264`, `finish_attempt` kinds at `:280-298`), so the Phase 2 gate is open.",
    "Side-effect rule (Plan Assumptions, UNK-06): every non-READ operation, including `classify_operation_type` results of `UNKNOWN`, counts as a side effect (conservative) until the owner decides a relaxation on top of the landed toolexec001 replay protocol.",
    "This Plan touches no schema, migration, or migration-registry file: the workflow migration ledger (`scripts/db/migrations_workflow.py`, HEAD code 2 / \"1.2.0\") is not a target row and needs no change here.",
]

TOOLCHAIN = "Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports` (baseline 6 kept, 0 broken), `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`."

EXEC_TABLE = """### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |"""

BLOCKER_PLACEHOLDER = """| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |"""

WORK_ITEMS_PLACEHOLDER = """| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |"""

DEFAULT_SECURITY = [
    "No new SQL surface: attempt persistence stays on the existing parameter-bound `finish_attempt` path; the new `error_kind` values are engine-produced literals, never caller- or user-supplied strings.",
]


TARGETS = {
    "01": "scripts/agent/workflow/workflow_engine.py",
    "02": "scripts/agent/workflow/models.py",
    "03": "scripts/agent/workflow/workflow_loader.py",
    "04": "config/workflows/default.json",
    "05": "scripts/agent/workflow_engine_adapter.py",
    "06": "scripts/agent/context.py",
    "07": "scripts/agent/tool_runner.py",
    "08": "tests/agent/workflow/test_workflow_engine.py",
    "09": "tests/agent/workflow/test_workflow_loader.py",
    "10": "tests/agent/test_orchestrator.py",
    "11": "tests/agent/test_tool_runner.py",
    "12": "docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md",
}


def doc(
    path: Path,
    *,
    seq: str,
    goal: str,
    scope: list[str],
    assumptions: list[str],
    design: list[str],
    alternatives: list[str],
    procedure: list[str],
    method: str,
    details: list[str],
    compatibility: list[str],
    security: list[str],
    rollback: list[str],
    validation: list[str],
    completion: list[str],
    out_of_scope: list[str],
    reqs: str,
    phase: str,
    related: str,
    blockers: str = BLOCKER_PLACEHOLDER,
) -> None:
    body = f"""## Goal

{goal}

## Scope

{chr(10).join(f"- {s}" for s in scope)}

## Assumptions

{chr(10).join(f"- {s}" for s in COMMON_ASSUMPTIONS + assumptions)}

## Design decisions

{chr(10).join(f"- {s}" for s in design)}

## Alternatives considered

{chr(10).join(f"- {s}" for s in alternatives)}

## Implementation
### Target file
`{TARGETS[seq]}`

### Procedure
{chr(10).join(f"{i}. {s}" for i, s in enumerate(procedure, 1))}

### Method
{method}

### Details
{chr(10).join(f"- {s}" for s in details)}

## Compatibility considerations

{chr(10).join(f"- {s}" for s in compatibility)}

## Security considerations

{chr(10).join(f"- {s}" for s in DEFAULT_SECURITY + security)}

## Rollback considerations

{chr(10).join(f"- {s}" for s in rollback)}

## Validation plan

{chr(10).join(f"- {s}" for s in validation)}

## Completion criteria

{chr(10).join(f"- {s}" for s in completion)}

## Out of Scope

{chr(10).join(f"- {s}" for s in out_of_scope)}

## Execution Status

{EXEC_TABLE}

### Blocker Log
{blockers}

### Work Items Created
{WORK_ITEMS_PLACEHOLDER}

## Traceability
- **Workflow phase**: {phase}
- **Requirement ID**: {reqs}
- **Source issue**: {ISSUE}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: {PLAN}
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {GENERATED_AT}
- **Related target files**: `{TARGETS[seq]}`{', ' if related else ''}{related}
"""
    path.write_text(body, encoding="utf-8")
    print(f"generated {path.name}")


def main() -> None:
    root = Path("implementations")
    files = sorted(root.glob(f"{BATCH}_*.md"))
    by_seq = {f.name.split("_")[1]: f for f in files}
    if len(files) != 12:
        raise SystemExit(f"expected 12 batch files, found {len(files)}: {files}")

    doc(
        by_seq["01"],
        seq="01",
        goal="Implement kind-based retry semantics in `scripts/agent/workflow/workflow_engine.py`: distinguish stage-deadline expiry from an inner `TimeoutError` using `asyncio.timeout()`'s `expired()` state, gate retry eligibility on `retry_policy.retry_on`, make every failed attempt consume one budget unit, route terminal kinds, add the `llm_failure` attempt kind, and treat side-effect-wrapped and callback-raised halts as terminal (REQ-002, REQ-003, REQ-005, REQ-006, REQ-007 / AC-2, AC-3, AC-5, AC-6, AC-7).",
        scope=[
            "Deadline-versus-inner timeout (REQ-002 / AC-2): replace `asyncio.wait_for(fn(), timeout=timeout)` (`workflow_engine.py:278`) with `async with asyncio.timeout(timeout)` around the stage callback; in the `except TimeoutError` branch, decide by the deadline context's `expired()` state — deadline expiry keeps today's path (kind `timeout`, `WorkflowTimeoutError` raise at `:279-289`), an inner `TimeoutError` from the callback is classified kind `exception` (persisted with `_ERROR_KIND_EXCEPTION` at `:291-298`) and the original exception propagates instead of being relabeled `WorkflowTimeoutError`.",
            "Retry eligibility by kind (REQ-003 / AC-3): in `_run_stage_with_retry` (`:188-240`) classify each failure (kind `timeout` for deadline expiry, `exception` otherwise, `llm_failure` for the new stage-failure error, terminal for callback-raised `WorkflowHaltError`); when the kind is not in `self._wdef.retry_policy.retry_on`, re-raise the original exception at once — the engine writes `failed` via the existing catch in `run()` (`:183-185`) and no backoff sleep or extra attempt occurs; eligible kinds keep the current consume-budget-then-halt loop (`:211-221`).",
            "`except WorkflowTimeoutError: raise` at `:208-209` stays for the shipped default (timeout is not in `retry_on`), but becomes a consequence of the kind gate rather than a hardcoded bypass, so `retry_on: [\"exception\", \"timeout\"]` retries a deadline timeout identically to an exception (AC-3 second half).",
            "Stage-failure error (REQ-005 / AC-5, REQ-007 / AC-7): define `WorkflowStageFailure(Exception)` in this module next to `WorkflowHaltError`/`WorkflowTimeoutError` (`:75-81`) carrying `kind` (`\"llm_failure\"`), `answer`, `error_kind`, `is_partial`; add `_ERROR_KIND_LLM_FAILURE = \"llm_failure\"` beside `_ERROR_KIND_TIMEOUT`/`_ERROR_KIND_EXCEPTION` (`:27-28`); the engine persists it through `finish_attempt` with that kind and applies the `retry_on` gate; a terminal stage failure writes task `failed` exactly once via `run()` and propagates the typed error for the adapter (procedure 05) to convert back to the tuple.",
            "Terminal halts from callbacks (REQ-006 / AC-6): a `WorkflowHaltError` raised by the stage callback itself (the adapter wraps side-effect-flagged failures with it, procedure 05) is re-raised without retry — add `WorkflowHaltError` to the terminal re-raise branch beside `WorkflowTimeoutError` at `:208-209`; halts synthesized by budget exhaustion (`:219-221`) remain the engine's own and stay distinguishable from callback halts by their message.",
            "Outward kinds (`workflow_timeout`, `workflow_halted`) are turn-level and are NOT written to `attempts.error_kind` (REQ-007 / AC-7): the persisted kinds stay `timeout`, `exception`, `llm_failure`.",
        ],
        assumptions=[
            "`asyncio.timeout()` is the chosen mechanism (Plan Design 'Timeout classification'); the Plan's own verification record (2026-10-30) tested on Python 3.13.5 that `expired()` is false for an inner `TimeoutError` and true when the deadline fires.",
            "Every engine-started attempt already consumes one idempotency/ledger record (`begin_stage_if_new` at `:264-270`, event id `{task_id}:{stage_id}:{attempt}` at `:262`), so 'every failed attempt consumes one budget unit' holds on the landed wfrecovery001 Phase 4 contract without new attempt bookkeeping.",
        ],
        design=[
            "Exception routing inside the engine, typed tuple only at the adapter boundary (Plan Design 'Failure mechanism', UNK-04 default): retry logic and status writes stay in `run()`/`_run_stage_with_retry`.",
            "Terminal exceptions not in `retry_on` take today's non-retryable-stage path (original exception propagates, engine writes `failed`, orchestrator records the exception class name as `error_kind`); `workflow_halted` is reserved for budget exhaustion and the side-effect rule (Plan Design).",
            "Failure-mapping helpers live here, not in the adapter (Plan Risk mitigation: adapter is at 15702 B of the 20480 B `check_module_size` limit).",
        ],
        alternatives=[
            "Keep `wait_for` and compare elapsed time — rejected (Plan Design): `asyncio.timeout().expired()` answers the deadline question directly without clocks.",
            "Return-value failure routing for LLM-level failures — rejected (UNK-04 default): it would split retry/status logic across engine and adapter.",
        ],
        procedure=[
            "Add `_ERROR_KIND_LLM_FAILURE` (`:27-28` region) and `WorkflowStageFailure` (`:75-81` region).",
            "Rewrite the `_run_stage` timeout block (`:277-298`): `async with asyncio.timeout(timeout)`; classify by `expired()`; persist kind `timeout` only for deadline expiry, kind `exception` for inner `TimeoutError`; keep `finish_attempt` calls parameter-bound.",
            "Rewrite `_run_stage_with_retry` (`:203-240`): after a failure, compute its kind (timeout / exception / llm_failure / halt), consult `self._wdef.retry_policy.retry_on`, re-raise terminal kinds immediately, keep the existing budget/backoff/`workflow.retry` span path for eligible kinds, and re-raise callback-raised `WorkflowHaltError` without retry.",
            "Persist `WorkflowStageFailure` in `_run_stage`'s failure branch with kind `llm_failure` and re-raise it unchanged.",
            "Do not change `run()`'s status writes (`:180-186`): `halted` for halt/timeout, `failed` for terminal exceptions, `completed` on success — REQ-008 depends on exactly one status write per turn.",
        ],
        method="In-place edits of `_run_stage_with_retry` and `_run_stage` plus two module-level additions; no agent-layer imports (Plan Design 'Layering': the engine stays free of agent-layer imports).",
        details=[
            "HEAD anchors (re-verified 2026-11-01): `run()` `:162-186`; retry loop `:188-240` (`retryable` gate `:196-199`, timeout bypass `:208-209`, halt-after-max `:210-221`, backoff and retry span `:222-240`); stage body `:242-309` (`timeout` computed `:261`, event id `:262`, `begin_stage_if_new` `:264-270`, `wait_for` `:278`, kind persistence `:279-298`, artifact record `:300-308`).",
            "`WorkflowStageFailure` lives in `workflow_engine.py` and is exported through `agent.workflow.__init__` exactly like `WorkflowHaltError` (the adapter imports it from `agent.workflow`); the pending wfrecovery001 errors-module procedure (`implementations/20261101-145309_02_scripts_agent_workflow_errors.py.md`) is the place where all three move together if it lands first — coordinate at implementation time.",
            "The `workflow.retry` span attributes (`retry.attempt`, `retry.max_attempts`, `retry.error_type` at `:231-239`) gain the kind value as `retry.error_type` stays the exception class name; no new span is required.",
        ],
        compatibility=[
            "`retry_policy.retry_on` must exist before this procedure compiles: Blocked until procedures 02-04 land (see Blocker Log).",
            "Blast radius per Plan Risks: `WorkflowEngine` 54 test references in 3 files, `WorkflowHaltError` 28, `WorkflowTimeoutError` 16 — defaults preserve behavior and exception class names are kept; each commit leaves the suite green.",
            "Rebases on the pending wfrecovery001 engine procedure (`implementations/20261101-145309_07_scripts_agent_workflow_workflow_engine.py.md`) and the pending wflease001 engine procedure (`implementations/20261101-163219_05_scripts_agent_workflow_workflow_engine.py.md`): the lease margin and conditional-finish edits touch the same functions; this batch lands last in plan order.",
        ],
        security=[
            "Classification is derived from the deadline context, never from exception strings or user input.",
        ],
        rollback=[
            "Single-commit revert restores today's behavior: timeouts terminal via the hardcoded bypass, inner `TimeoutError` relabeled as `WorkflowTimeoutError`, no `llm_failure` rows.",
        ],
        validation=[
            "`uv run pytest tests/agent/workflow/ -v` — procedure 08's new tests fail against pre-change `master` and pass after this procedure (Plan Validation plan).",
            TOOLCHAIN,
        ],
        completion=[
            "AC-2: a callback raising `TimeoutError` records kind `exception`; a callback exceeding `timeout_sec` records kind `timeout`.",
            "AC-3: with shipped config a timed-out execute stage is not retried and an exception is retried up to `max_attempts`; with `retry_on` including `timeout` the timeout consumes the budget identically.",
            "AC-5/AC-7 hold for stage failures persisted with kind `llm_failure`; no outward kind is ever written to `attempts.error_kind`.",
        ],
        out_of_scope=[
            "The adapter tuple/status contract (procedure 05), the `TurnState` flag (procedure 06), and the tool_runner side-effect setter (procedure 07).",
            "`retry_on` parsing/validation (procedure 03) and config (procedure 04).",
        ],
        reqs="`REQ-002`, `REQ-003`, `REQ-005`, `REQ-006`, `REQ-007`",
        phase="Phase 2 (Engine semantics; after wfrecovery001 Phase 4 — gate open)",
        related="`scripts/agent/workflow/models.py`, `scripts/agent/workflow/workflow_loader.py`, `config/workflows/default.json`, `scripts/agent/workflow_engine_adapter.py`, `tests/agent/workflow/test_workflow_engine.py`",
        blockers="""| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Blocked until procedures 02-04 land (`RetryPolicy.retry_on` must exist before the engine consults it) | No | — |
| 1 | Landing order: rebase on pending wfrecovery001 procedures 04/07 and wflease001 procedure 05 for the same functions (plan-order landing, Plan Assumptions) | No | — |""",
    )

    doc(
        by_seq["02"],
        seq="02",
        goal="Add the `retry_on` field to `RetryPolicy` in `scripts/agent/workflow/models.py` with the shipped default that preserves today's behavior (REQ-001 / AC-1).",
        scope=[
            "Extend `RetryPolicy` (`models.py:61-66`, fields `max_attempts`, `backoff_sec`) with `retry_on: tuple[str, ...] = (\"exception\",)`.",
            "Kind names are the literals `\"exception\"`, `\"timeout\"`, `\"llm_failure\"`; the field is a tuple so the dataclass stays hashable/immutable like its siblings.",
            "No other model changes: `StageDefinition` (`:54-56`) and `WorkflowDef` (`:69+`) are untouched; the stage-level `retryable` flag remains the outer gate.",
        ],
        assumptions=[
            "Default `(\"exception\",)` reproduces the owner-decided behavior (Plan UNK-01/UNK-02); `RetryPolicy` is constructed only by `workflow_loader.py` (`:128-131`) and test fixtures (`tests/agent/workflow/*`), so a defaulted field breaks nothing.",
        ],
        design=[
            "Per-kind list instead of a boolean `retry_timeouts` (Plan Design 'Retry policy' alternative (a)): it also covers `llm_failure` and future kinds without more booleans.",
        ],
        alternatives=[
            "`list[str]` field — rejected: mutable default is illegal on a dataclass and the value is read-only after load.",
            "A new `RetryKind` enum — rejected by Plan scope: the loader validates literal strings against a module-level set; no shared enum file is a target row.",
        ],
        procedure=[
            "Add the field after `backoff_sec` (`models.py:65`).",
            "Note the allowed kinds in the class docstring (`exception`, `timeout`, `llm_failure`) so the contract is visible at the dataclass.",
        ],
        method="One dataclass field addition.",
        details=[
            "HEAD anchor (re-verified 2026-11-01): `class RetryPolicy` at `models.py:61-66`.",
            "`lint-imports` unaffected: `models.py` imports nothing new.",
        ],
        compatibility=[
            "The pending wftaskapi001 (`20261101-140834_03`) and wfrecovery001 (`20261101-145309_01`) procedures edit the same file earlier in plan order; Plan Assumptions record the overlap as non-contradicting (distinct dataclasses/fields).",
        ],
        security=[],
        rollback=["Delete the field; loader and config rows revert with it."],
        validation=[
            "`uv run pytest tests/agent/workflow/ -v` (procedures 08, 09 exercise the field).",
            TOOLCHAIN,
        ],
        completion=["AC-1 (model half): `RetryPolicy` carries `retry_on` with default `[\"exception\"]` semantics."],
        out_of_scope=["Validation and parsing of the key (procedure 03); the shipped config (procedure 04)."],
        reqs="`REQ-001`",
        phase="Phase 1 (Policy schema and loader; independent)",
        related="`scripts/agent/workflow/workflow_loader.py`, `config/workflows/default.json`, `tests/agent/workflow/test_workflow_loader.py`, `scripts/agent/workflow/workflow_engine.py`",
    )

    doc(
        by_seq["03"],
        seq="03",
        goal="Parse and validate `retry_policy.retry_on` in `scripts/agent/workflow/workflow_loader.py` inside a separate helper, rejecting unknown kinds with `WorkflowLoadError` and defaulting an absent key (REQ-001, REQ-011 / AC-1, AC-9).",
        scope=[
            "Add `_validate_retry_on(policy: dict) -> tuple[str, ...]` (module level, next to `_validate` at `workflow_loader.py:56`): absent key returns the default `(\"exception\",)`; present key must be a list of strings drawn from `{\"exception\", \"timeout\", \"llm_failure\"}`, otherwise `WorkflowLoadError` naming the offending kind.",
            "Call it from `_validate` (`:56-96`, after the `max_attempts`/`backoff_sec` checks at `:86-91`) and pass the result into the `RetryPolicy(...)` construction (`:128-131`).",
            "`_REQUIRED_POLICY_KEYS` (`:48`) stays `{max_attempts, backoff_sec}` — `retry_on` is optional by REQ-001 and must NOT be added to it.",
        ],
        assumptions=[
            "Complexity guard (Plan Risks): `_validate` is radon grade C (18) at the recorded baseline (2026-10-30); keeping the new validation in a separate helper keeps `_validate` at or below C (18). The Validation plan re-runs `uv run radon cc scripts/agent/workflow/workflow_loader.py -s -n C`.",
            "Older deployed loaders ignore unknown policy keys (Plan Assumptions verification record: `_validate` ignores unknown keys), so the config may ship before or with the code (Plan Design 'Compatibility').",
        ],
        design=[
            "Validation lives in a dedicated helper rather than inline (Plan REQ-001 explicit wording: 'validation in a separate helper').",
            "The allowed-kind set is a module-level frozenset `_RETRY_KINDS` so the engine doc (procedure 01) and tests share one vocabulary; the helper returns a tuple (procedure 02 field type).",
        ],
        alternatives=[
            "Reject the key entirely on unknown kinds only at engine start — rejected: AC-1 requires a `WorkflowLoadError` at load time, and the deploy pre-flight (`python -m agent.workflow.validate`) is the earliest gate.",
        ],
        procedure=[
            "Add `_RETRY_KINDS` and `_validate_retry_on`.",
            "Wire the call in `_validate` and thread the parsed tuple into `RetryPolicy(...)` at `:128-131`.",
            "Confirm `validate.py` (`scripts/agent/workflow/validate.py`) needs no change: it calls the loader, which now validates (Plan Reference Files).",
        ],
        method="One helper function plus two call-site edits.",
        details=[
            "Error message shape: `retry_policy.retry_on contains unknown kind 'X' (allowed: exception, timeout, llm_failure)` — matches the existing message style (`:87-91`, `:92-96`).",
            "`require_approval` rejection (`:92-96`) stays as is.",
        ],
        compatibility=[
            "Deploy pre-flight: `deploy/setup_services.sh` runs `python -m agent.workflow.validate` before start (Plan Reference Files); an invalid shipped `retry_on` therefore blocks startup, which is the intended gate (AC-9).",
        ],
        security=[],
        rollback=["Remove the helper and the call; the config key from procedure 04 is ignored by the reverted loader (forward-compatible), so config and code can be reverted independently."],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_loader.py -v` (procedure 09).",
            "`PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json` (AC-9).",
            "`uv run radon cc scripts/agent/workflow/workflow_loader.py -s -n C` — grade not above the recorded C (18).",
            TOOLCHAIN,
        ],
        completion=["AC-1: a definition without `retry_on` loads with the default; an unknown kind raises `WorkflowLoadError`.", "AC-9: the pre-flight passes on the shipped file and on an older-format file without the key."],
        out_of_scope=["Engine consumption of the parsed value (procedure 01)."],
        reqs="`REQ-001`, `REQ-011`",
        phase="Phase 1 (Policy schema and loader)",
        related="`scripts/agent/workflow/models.py`, `config/workflows/default.json`, `tests/agent/workflow/test_workflow_loader.py`",
    )

    doc(
        by_seq["04"],
        seq="04",
        goal="Add the explicit shipped `retry_on` to `config/workflows/default.json` so shipped behavior is readable from configuration (REQ-001, REQ-003, REQ-011 / AC-1, AC-3, AC-9).",
        scope=[
            "Extend the `retry_policy` block (`default.json:19-22`, currently `max_attempts: 3`, `backoff_sec: 1`) with `\"retry_on\": [\"exception\"]`.",
            "No stage changes: `plan`/`verify` stay `retryable: false`, `execute` stays `retryable: true` with 30/120/10 s timeouts (`:4-18`).",
            "`config/defaults/default_settings.json` is NOT a target — it no longer exists on `master` (re-verified 2026-11-01); workflow configuration lives only in `config/workflows/*.json`.",
        ],
        assumptions=[
            "The explicit value pins the owner decisions (Plan UNK-01/UNK-02): timeout and LLM failure are terminal under the shipped config.",
        ],
        design=[
            "Explicit-in-config instead of relying on the loader default (Plan row 4 'Shipped behavior must be readable from configuration').",
        ],
        alternatives=[
            "Leave the key absent (loader default) — rejected by the frozen table row: AC-1 asserts the shipped file carries the key.",
        ],
        procedure=[
            "Add the key to the `retry_policy` object.",
            "Run the pre-flight validation on the edited file.",
        ],
        method="One JSON key addition.",
        details=[
            "Rolling-deploy safety (Plan Risks): an older deployed loader ignores the unknown key (Plan Assumptions verification record), so config and code order does not matter for startup.",
            "Deployment sync: the deployed `/opt/llm/config/workflows/default.json` updates through the normal config sync in the deploy skill (REQ-011); deploying is the user's decision (Plan Phase 6 approval gate).",
        ],
        compatibility=[
            "`tests/agent/workflow/test_workflow_loader.py` gains a shipped-file assertion (procedure 09) so the pinned value cannot drift.",
        ],
        security=[],
        rollback=["Remove the key; the loader default reproduces the same behavior (AC-1)."],
        validation=[
            "`PYTHONPATH=scripts uv run python -m agent.workflow.validate config/workflows/default.json` (AC-9).",
            "`uv run pytest tests/agent/workflow/test_workflow_loader.py -v` (procedure 09).",
        ],
        completion=["AC-1: the shipped `default.json` carries `retry_on`. AC-3 is pinned by procedure 08/09 tests against this file."],
        out_of_scope=["Any stage timeout or `retryable` change."],
        reqs="`REQ-001`, `REQ-003`, `REQ-011`",
        phase="Phase 1 (Policy schema and loader)",
        related="`scripts/agent/workflow/workflow_loader.py`, `scripts/agent/workflow/models.py`, `tests/agent/workflow/test_workflow_loader.py`",
    )

    doc(
        by_seq["05"],
        seq="05",
        goal="Make the turn boundary typed in `scripts/agent/workflow_engine_adapter.py`: return `error_kind` `workflow_halted` / `workflow_timeout` on halted/timed-out turns, route LLM-level failure results through the engine as `WorkflowStageFailure`, wrap side-effect-flagged attempt failures as terminal, clear the flag at each attempt start, and limit adapter status writes to cancellation (REQ-004, REQ-005, REQ-006, REQ-008 / AC-4, AC-5, AC-6, AC-8).",
        scope=[
            "Typed halt/timeout kinds (REQ-004 / AC-4): in the `except (WorkflowHaltError, WorkflowTimeoutError)` branch (`workflow_engine_adapter.py:210-212`) set `error_kind` to `\"workflow_halted\"` or `\"workflow_timeout\"` (split the catch into two branches) before the return at `:222`, so `execute_turn` no longer returns `(\"\", None, False)` for a halted turn and the orchestrator's turn-end audit (`orchestrator.py:166-200` → `audit_event_emitter`) carries the kind; `on_error` stays observational (called once via `_handle_workflow_halt` `:307-313`, never the sole signal).",
            "LLM-failure routing (REQ-005 / AC-5): in `execute_fn` (`:180-186`), when `_run_execute_stage` (`:331-383`) returns a failure result (`result.action != \"continue\"` classification at `:359-365`), raise `WorkflowStageFailure(kind=\"llm_failure\", answer=..., error_kind=..., is_partial=...)` instead of returning the tuple; the engine applies the `retry_on` gate (procedure 01); under the shipped config the failure is terminal: the engine writes task `failed` once (`workflow_engine.py:183-185`) and the adapter's halt/exception handling converts the typed error back to the outward `(answer, error_kind, is_partial)` with the same outward `error_kind` value as today.",
            "Remove the completed-then-failed overwrite (REQ-008): `_status_for_exit` (`:49-60`) drops the `exit_reason == \"completed\" and error_kind is not None` branch (`:58-59`); the engine already wrote `failed` for the terminal stage failure, so the adapter writes status only for cancellation (`:56-57`) (Plan 'The task status is written once, by the engine; the adapter writes only what the engine cannot observe').",
            "Side-effect terminal wrap (REQ-006 / AC-6): in `execute_fn`, clear `ctx.turn.attempt_side_effect` (procedure 06's field) at attempt start; if `_run_execute_stage` raises and the flag is set, raise `WorkflowHaltError(\"stage execute halted: side effect attempted\")` from it — the engine re-raises halts without retry (procedure 01); the outward kind is `workflow_halted` regardless of `retry_on`.",
            "`audit_stage_completed` stays emitted before a stage failure is raised (Plan Design): keep the emission at `_run_execute_stage:374-382` before raising `WorkflowStageFailure`.",
        ],
        assumptions=[
            "Outward `error_kind` values `workflow_halted` / `workflow_timeout` are turn-level literals (REQ-007); they are never written to `attempts.error_kind`.",
            "LLM-level failure keeps today's outward `error_kind` (the `result.error_kind or result.reason or result.action` value at `:360`) so existing REPL behavior is unchanged (Plan Risk mitigation).",
        ],
        design=[
            "Boundary contract stays the existing typed tuple (Plan Design 'Failure mechanism', UNK-04 default); no new caller contract is invented — `Orchestrator._execute_turn` already forwards `error_kind` to `emit_turn_end` (`orchestrator.py:166-200`).",
            "The flag check lives here (the agent layer) because `workflow_engine.py` stays free of agent-layer imports (Plan Design 'Layering').",
        ],
        alternatives=[
            "Keep returning failure tuples from `execute_fn` and let the engine infer failure — rejected (REQ-005): the engine could not apply retry policy or write `failed` once for LLM-level failures.",
        ],
        procedure=[
            "Split the halt catch (`:210-212`) into `except WorkflowTimeoutError` (kind `workflow_timeout`) and `except WorkflowHaltError` (kind `workflow_halted`), plus a `WorkflowStageFailure` branch that restores the outward tuple fields from the error attributes.",
            "Raise `WorkflowStageFailure` from `execute_fn` on LLM-level failure results; keep the persistence and partial-flag classification logic in `_run_execute_stage` (`:356-372`).",
            "Clear and check `ctx.turn.attempt_side_effect` in `execute_fn` as described; import nothing from `agent.workflow` beyond the shared `WorkflowStageFailure` export.",
            "Drop the completed-then-failed branch in `_status_for_exit` (`:58-59`).",
        ],
        method="Edits across `execute_turn`, `execute_fn`, and `_status_for_exit`; failure-mapping helpers stay in `workflow_engine.py` (module-size mitigation).",
        details=[
            "HEAD anchors (re-verified 2026-11-01): `execute_turn` `:149-222` (tuple init `:157-159`, halt catch `:210-212`, return `:222`), `_status_for_exit` `:49-60`, `_handle_workflow_halt` `:307-313`, `_run_execute_stage` `:331-383` (LLM-failure classification `:359-365`, audit `:374-382`).",
            "Module size gate (Plan Risks): the file is 15702 B at baseline of the 20480 B limit; this procedure adds branches, not helpers — `check_module_size` in the Validation plan.",
            "Cancellation path (`:213-215`) and `finally` block (`:216-220`) keep their current shape.",
        ],
        compatibility=[
            "Blocked until procedures 01 and 06 land (`WorkflowStageFailure` and the `TurnState` field must exist; see Blocker Log).",
            "Rebases on the pending wfrecovery001 adapter procedure (`implementations/20261101-145309_08_scripts_agent_workflow_engine_adapter.py.md`) and wflease001 landing order; Plan Assumptions record the overlap as different methods, non-contradicting.",
            "`orchestrator.py`, `startup_component_init.py`, `cli_view.py` need no change (Plan Assumptions).",
        ],
        security=[
            "The new outward kinds are fixed literals; no error text from the engine or LLM is copied into `error_kind` for halt/timeout (the LLM-failure branch keeps today's classification only).",
        ],
        rollback=["Single-commit revert restores the silent halt tuple, the completed-then-failed overwrite, and tuple-returning `execute_fn`."],
        validation=[
            "`uv run pytest tests/agent/test_orchestrator.py tests/integration/test_orchestrator_integration.py -v` (procedure 10 pins AC-4/AC-5/AC-8).",
            TOOLCHAIN,
        ],
        completion=[
            "AC-4: halted and timed-out turns return `workflow_halted` / `workflow_timeout` with and without `on_error`, and the turn-end audit carries it.",
            "AC-5: LLM-failure turns write `failed` once (no `completed` write) with the same outward kind as before.",
            "AC-6: a flag-set failed attempt is terminal with `workflow_halted` even when its kind is in `retry_on`.",
            "AC-8: the invariant test (procedure 10) passes for halt, timeout, LLM failure, and cancellation.",
        ],
        out_of_scope=["Engine kind logic (procedure 01); the `TurnState` field itself (procedure 06); tool_runner flag setter (procedure 07)."],
        reqs="`REQ-004`, `REQ-005`, `REQ-006`, `REQ-008`",
        phase="Phase 4 (Boundary contract)",
        related="`scripts/agent/workflow/workflow_engine.py`, `scripts/agent/context.py`, `scripts/agent/tool_runner.py`, `tests/agent/test_orchestrator.py`",
        blockers="""| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Blocked until procedure 01 (`WorkflowStageFailure`, terminal halt re-raise) and procedure 06 (`TurnState` field) land | No | — |
| 1 | Landing order: rebase on the pending wfrecovery001 adapter procedure `20261101-145309_08` (plan-order landing, Plan Assumptions) | No | — |""",
    )

    doc(
        by_seq["06"],
        seq="06",
        goal="Add the per-attempt side-effect flag to `TurnState` in `scripts/agent/context.py` (REQ-006 / AC-6).",
        scope=[
            "Extend `TurnState` (`context.py:213-226`, fields `current_turn_id`, `background_tasks`, `persistence_boundary`) with `attempt_side_effect: bool = False` (name chosen here; the Plan calls it 'a per-attempt side-effect flag' and freezes no field name).",
            "The flag is transient process state: no DB column, no persistence boundary write, no cross-process visibility.",
            "Reset is owned by the adapter's attempt start (procedure 05), not by this dataclass.",
        ],
        assumptions=[
            "`TurnState` is constructed once with `AgentContext` (`context.py:320` region, re-verified 2026-11-01 per the file's own comment at `:218-220`) and is not recreated per turn — so 'cleared at each attempt start' must be an explicit write at attempt start (procedure 05), which is why the default alone is not the reset mechanism.",
        ],
        design=[
            "Boolean flag instead of a per-attempt tool-call id set (Plan Design 'Side effects': the heavier tracking is unnecessary for a yes/no rule).",
        ],
        alternatives=[
            "Reuse `ctx.workflow` state instead of `TurnState` — rejected (REQ-006 names `TurnState`, the per-turn transient owner).",
        ],
        procedure=[
            "Add the field after `persistence_boundary` (`:226`) with a comment stating: set by `tool_runner` before a non-READ call (procedure 07), cleared at each attempt start by the adapter (procedure 05), read by the adapter's failure wrap.",
        ],
        method="One dataclass field addition.",
        details=[
            "HEAD anchor (re-verified 2026-11-01): `class TurnState` at `context.py:213-226`.",
            "Blast radius per Plan Affected areas: `context.py` 12 commits in 30 days; the additive defaulted field breaks no construction site.",
        ],
        compatibility=["No serialization: `TurnState` is not persisted, so no schema or migration interaction exists for this Plan."],
        security=[],
        rollback=["Delete the field; procedures 05 and 07 revert with it."],
        validation=[
            "`uv run pytest tests/agent/test_tool_runner.py tests/agent/test_orchestrator.py -v` (procedures 11, 10).",
            TOOLCHAIN,
        ],
        completion=["AC-6 (state half): a defaulted boolean exists on `TurnState` that procedures 05/07 write and read."],
        out_of_scope=["Who sets/clears the flag (procedures 05, 07)."],
        reqs="`REQ-006`",
        phase="Phase 3 (Side-effect rule)",
        related="`scripts/agent/tool_runner.py`, `scripts/agent/workflow_engine_adapter.py`, `tests/agent/test_tool_runner.py`",
    )

    doc(
        by_seq["07"],
        seq="07",
        goal="Set the side-effect flag before non-READ tool calls in `scripts/agent/tool_runner.py` by hoisting the operation classification above the gateway branch (REQ-006 / AC-6).",
        scope=[
            "In `_execute_prepared_call` (`tool_runner.py:194-221`, re-verified 2026-11-01), move `classify_operation_type(name, ctx.services_required.runtime_tools)` (`currently at :215`) above the gateway branch (`gateway is not None` return at `:211-213`), and set `ctx.turn.attempt_side_effect = True` whenever the classification is not `OperationType.READ` — before `gateway.execute(...)` (`:212`) or `tools.execute(...)` (`:221`).",
            "The no-gateway preflight path (`:214-219`) consumes the same classification result (no second call); `check_preflight` behavior is unchanged.",
            "Unclassified tools (`OperationType.UNKNOWN`) set the flag (conservative rule, Plan Assumptions/UNK-06).",
        ],
        assumptions=[
            "Production always has a gateway (`factory.py:652` creates `RepositoryGateway` unconditionally; module docstring at `tool_runner.py:207-209`) — without the hoist the flag would never be set in production, which is exactly the defect REQ-006 names.",
            "`classify_operation_type` and `OperationType` are already imported (`tool_runner.py:37` region); `tool_policy.py` is a Reference File, not a target (no change there).",
        ],
        design=[
            "Set-before-execute (not after success): the flag records that a side effect was attempted, so a crashed or timed-out non-READ call also blocks retry (Plan Intent 'A retry never follows a completed non-READ tool call' — 'completed' means the call ran, not that it succeeded).",
            "One classification per call: hoisting reuses the value for both the flag and the preflight gate.",
        ],
        alternatives=[
            "Set the flag inside `RepositoryGateway.execute` — rejected: the gateway is not a target row (frozen table), and the no-gateway path would miss the flag.",
        ],
        procedure=[
            "Hoist the classification line above the gateway branch.",
            "Add the flag assignment in the non-READ case, keeping the existing preflight `try/except PolicyViolationError` block (`:216-219`).",
        ],
        method="Reordering plus one attribute write; no signature changes.",
        details=[
            "Flag writes go through `ctx.turn` (`AgentContext.turn`, `context.py:320` region) — the same object the adapter reads per attempt (procedure 05).",
            "`_record_transport_failure` (`:223+`) and the recorder path above `_execute_prepared_call` (`:274`) are untouched.",
        ],
        compatibility=[
            "Blocked until procedure 06 lands (the field must exist).",
            "Blast radius per Plan Affected areas: `tool_runner.py` 9 commits in 30 days; behavior change is confined to setting a new flag no existing consumer reads until procedure 05 lands.",
        ],
        security=[
            "Hoisting does not weaken the preflight gate: non-READ calls still hit `check_preflight` in the no-gateway branch, and the gateway path keeps its own enforcement (module docstring `:197-210`).",
        ],
        rollback=["Restore the original branch order and delete the flag write; preflight behavior is byte-identical to today."],
        validation=[
            "`uv run pytest tests/agent/test_tool_runner.py -v` (procedure 11).",
            TOOLCHAIN,
        ],
        completion=["AC-6 (setter half): after any non-READ call the flag is true; READ-only attempts leave it false; unclassified tools set it."],
        out_of_scope=["Retry suppression itself (procedures 01/05).", "`tool_policy.py` classification changes (Plan Out-of-Scope)."],
        reqs="`REQ-006`",
        phase="Phase 3 (Side-effect rule)",
        related="`scripts/agent/context.py`, `scripts/agent/workflow_engine_adapter.py`, `tests/agent/test_tool_runner.py`",
        blockers="""| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Blocked until procedure 06 adds the `TurnState.attempt_side_effect` field | No | — |""",
    )

    doc(
        by_seq["08"],
        seq="08",
        goal="Rewrite the timeout test and add the engine kind/retry/budget/side-effect tests in `tests/agent/workflow/test_workflow_engine.py` (REQ-002, REQ-003, REQ-005, REQ-006, REQ-009 / AC-2, AC-3, AC-5, AC-6).",
        scope=[
            "Rewrite `test_timeout_raises_workflow_timeout_error` (`:163-181`, re-verified 2026-11-01: currently accepts `pytest.raises((WorkflowHaltError, WorkflowTimeoutError))`) to assert exactly `WorkflowTimeoutError` and that the attempt row persisted kind `timeout`.",
            "New cases (Plan REQ-009 list): inner `TimeoutError` from the callback records kind `exception` and is retried when `exception` is in `retry_on`; timeout retried when `retry_on` includes `timeout` (timeout then success); timeout exhaustion halts with the shipped config; exception exhaustion halts after consuming the full budget (attempt-row count equals `max_attempts`); non-retryable kind is terminal at once (no backoff sleep, one attempt row); LLM-failure stage failure via `WorkflowStageFailure` persisted with kind `llm_failure` and terminal under the shipped config; side-effect suppression — a callback that raises `WorkflowHaltError` is not retried even when `retry_on` includes `exception`.",
            "Shipped-configuration pin (REQ-003 / AC-3): one test loads the real `config/workflows/default.json` through the loader and asserts the shipped policy pins timeout-not-retried / exception-retried behavior.",
        ],
        assumptions=[
            "Existing fixtures (per-test store/engine, `StageDefinition(timeout_sec=...)`) are reused; retry/timeout tests at `:113`, `:133`, `:165`, `:212`, `:242`, `:263`, `:303` stay green where their behavior is unchanged.",
        ],
        design=[
            "Assertions read persisted attempt rows through the store (kind column), locking the REQ-007 contract, not engine internals.",
        ],
        alternatives=[
            "Spying on `finish_attempt` call arguments — rejected: the ACs are about persisted kinds and attempt counts.",
        ],
        procedure=[
            "Rewrite the named timeout test first (it is the Plan's designated rewrite).",
            "Add a `TestWorkflowEngineRetryKinds` class with the seven cases above, parametrizing `retry_on` through `WorkflowDef(retry_policy=RetryPolicy(..., retry_on=(...)))` fixtures.",
            "Add the shipped-config test using `WorkflowLoader().load(\"default\")`.",
        ],
        method="Test-only edits in the existing file layout (one rewritten case, one new class).",
        details=[
            "The side-effect case raises `WorkflowHaltError` from the stage callback directly — at engine level this is the contract procedure 01 implements and procedure 05 triggers in production.",
            "Inner-`TimeoutError` fixtures raise `TimeoutError` from the callback well before its `timeout_sec` so classification cannot be time-ambiguous.",
        ],
        compatibility=[
            "File is shared with pending wftaskapi001/wfrecovery001/wflease001 test procedures (`20261101-140834_06`, `20261101-145309_14/15`, `20261101-163219_11`); Plan Assumptions classify the overlap as compatible (additive tests in different classes) — this batch lands last and rebases.",
        ],
        security=[],
        rollback=["Delete the new class; restore the rewritten test."],
        validation=["`uv run pytest tests/agent/workflow/test_workflow_engine.py -v` — new cases fail on pre-change `master` and pass after procedures 01-05."],
        completion=["AC-2, AC-3, AC-5, AC-6 (engine half), AC-7 covered by this file."],
        out_of_scope=["Adapter/orchestrator tuple tests (procedure 10)."],
        reqs="`REQ-002`, `REQ-003`, `REQ-005`, `REQ-006`, `REQ-009`",
        phase="Phase 2 (Engine semantics)",
        related="`scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/models.py`, `config/workflows/default.json`",
    )

    doc(
        by_seq["09"],
        seq="09",
        goal="Add `retry_on` loader tests to `tests/agent/workflow/test_workflow_loader.py` (REQ-001, REQ-009, REQ-011 / AC-1, AC-9).",
        scope=[
            "New cases: valid `retry_on` list parses to the tuple; absent key loads the default `(\"exception\",)`; unknown kind (`\"halt\"`) raises `WorkflowLoadError`; non-list or non-string values raise `WorkflowLoadError`; a definition without `retry_on` (older format) still loads (AC-9 compatibility).",
            "Shipped-file case: `WorkflowLoader().load(\"default\")` produces `retry_on == (\"exception\",)` from `config/workflows/default.json` (pins procedure 04).",
            "Pre-flight parity: one case runs the same validation `python -m agent.workflow.validate` performs (REQ-011 / AC-9).",
        ],
        assumptions=[
            "The file's existing tmp-path definition fixtures (file is 248 lines, required-keys coverage only, re-verified 2026-11-01) are reused for each variant.",
        ],
        design=["Each AC-1 clause (present/absent/unknown) gets its own case so failures localize to the loader helper."],
        alternatives=["Parametrized single test — rejected: the file's existing style is explicit named cases."],
        procedure=[
            "Append `TestRetryOn` with the cases above.",
        ],
        method="Test-only additions in the existing class-per-topic layout.",
        details=[
            "`WorkflowLoadError` import already used in this file for the existing key tests.",
        ],
        compatibility=["No changes to the existing required-keys tests."],
        security=[],
        rollback=["Delete the class."],
        validation=["`uv run pytest tests/agent/workflow/test_workflow_loader.py -v` — new cases fail against pre-change `master`."],
        completion=["AC-1 and AC-9 fully covered in this file."],
        out_of_scope=["Engine consumption tests (procedure 08)."],
        reqs="`REQ-001`, `REQ-009`, `REQ-011`",
        phase="Phase 1 (Policy schema and loader)",
        related="`scripts/agent/workflow/workflow_loader.py`, `scripts/agent/workflow/models.py`, `config/workflows/default.json`",
    )

    doc(
        by_seq["10"],
        seq="10",
        goal="Add halt/timeout outcome, LLM-failure, callback, and invariant tests to `tests/agent/test_orchestrator.py` (REQ-004, REQ-005, REQ-008, REQ-009 / AC-4, AC-5, AC-8).",
        scope=[
            "Typed outcomes (REQ-004 / AC-4): a halted turn and a timed-out turn return `error_kind` `workflow_halted` / `workflow_timeout` from the turn path, with and without `on_error`; with a callback it is called exactly once with the typed exception; the turn-end audit event (`emit_turn_end`) carries the same `error_kind` (assert through the mocked emitter the file already uses).",
            "The existing halt tests (`:663-667` region, re-verified 2026-11-01: they assert task status and `on_error`'s `WorkflowHaltError`) are extended — not replaced — with the returned-tuple assertion.",
            "LLM failure (REQ-005 / AC-5): the fake-adapter/fake-result pattern already in this file drives a `result.action != \"continue\"` turn; assert task status written once as `failed` (no `completed` row state) and the outward `error_kind` equals today's value.",
            "Invariant (REQ-008 / AC-8): one parametrized test over halt, timeout, LLM failure, and cancellation asserts no turn has empty answer + `error_kind=None` + task status `halted`/`failed` simultaneously.",
        ],
        assumptions=[
            "The file's `_temp_workflow_store` / fake `WorkflowEngine` fixtures (`:670+` region) are the existing pattern for driving real engine paths; reuse them.",
        ],
        design=["Assert the boundary tuple plus the persisted status plus the audit argument triple in one place per scenario (Plan Design: audit already consumes the tuple)."],
        alternatives=["New integration file — rejected: the frozen table names this file and its fixtures already cover the turn path."],
        procedure=[
            "Extend the halt tests with the returned-tuple and audit assertions.",
            "Add `TestTurnFailureKinds` with the AC-4 (with/without callback), AC-5, and AC-8 invariant cases.",
        ],
        method="Test-only additions plus two assertion extensions in existing tests.",
        details=[
            "Cancellation scenario drives the adapter's `asyncio.CancelledError` path (`workflow_engine_adapter.py:213-215`) and expects outward kind handling per procedure 05 plus `halted` status (the adapter-owned write).",
            "No change to the bg-failure tests around `:2627-2765` (re-verified 2026-11-01: that region is bg-task failure handling, not workflow halt); the Plan's `:764` cite maps to the recorder tests, untouched here.",
        ],
        compatibility=[
            "File shared with pending wfrecovery001 (`20261101-145309_19`) and turnadr001 regions; Plan Assumptions: compatible (different regions).",
        ],
        security=[],
        rollback=["Delete the new class; revert the two extended assertions."],
        validation=["`uv run pytest tests/agent/test_orchestrator.py -v`, plus `uv run pytest tests/integration/test_orchestrator_integration.py -v` (Plan Validation plan)."],
        completion=["AC-4, AC-5, AC-8 covered by this file."],
        out_of_scope=["Engine-level kind tests (procedure 08)."],
        reqs="`REQ-004`, `REQ-005`, `REQ-008`, `REQ-009`",
        phase="Phase 4 (Boundary contract)",
        related="`scripts/agent/workflow_engine_adapter.py`, `scripts/agent/orchestrator.py`",
    )

    doc(
        by_seq["11"],
        seq="11",
        goal="Add side-effect-flag tests to `tests/agent/test_tool_runner.py` (REQ-006, REQ-009 / AC-6).",
        scope=[
            "New cases through the file's existing `_execute_prepared_call` test pattern (file is 2265 lines, re-verified 2026-11-01): a non-READ call through a mocked gateway sets `ctx.turn.attempt_side_effect` true before the gateway executes; a READ call leaves it false; an unclassified (UNKNOWN) tool sets it; the no-gateway branch sets it and still runs `check_preflight` unchanged.",
            "Flag ordering: a case where the mocked gateway raises asserts the flag was already set before the exception (set-before-execute contract).",
        ],
        assumptions=[
            "`TurnState` in test fixtures is the real dataclass (the file's `_make_ctx`-style helpers construct it); no new fixture layer.",
        ],
        design=["Read the flag on the context object (the adapter-visible contract), not the classification call log."],
        alternatives=["Assert classification hoisting via call-order mocks only — rejected: AC-6 is about the flag state."],
        procedure=[
            "Append `TestAttemptSideEffectFlag` with the four ordering/state cases.",
        ],
        method="Test-only additions.",
        details=[
            "Gateway mocks: reuse the file's existing fake-gateway fixtures so both branches are exercised.",
        ],
        compatibility=["Existing 2265-line file's cases stay untouched."],
        security=[],
        rollback=["Delete the class."],
        validation=["`uv run pytest tests/agent/test_tool_runner.py -v` — new cases fail against pre-change `master`."],
        completion=["AC-6 (flag half) covered by this file."],
        out_of_scope=["Retry suppression behavior (procedure 10)."],
        reqs="`REQ-006`, `REQ-009`",
        phase="Phase 3 (Side-effect rule)",
        related="`scripts/agent/tool_runner.py`, `scripts/agent/context.py`",
    )

    doc(
        by_seq["12"],
        seq="12",
        goal="Update `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`: Task Status Transitions table, Retry Mechanism, and Operational Notes to describe the configured retry kinds, the timeout classification, the typed failure contract, and the side-effect rule (REQ-010 / AC-10).",
        scope=[
            "Task Status Transitions table (`:74-94` region, re-verified 2026-11-01): the `halted` rows stay, with the halt now described as 'kind not in `retry_on`, budget exhausted, or side-effect-flagged failure'; add the turn-level `error_kind` values `workflow_halted` / `workflow_timeout` to the turn-outcome description.",
            "Retry Mechanism section (`:119-129` region): state that retry eligibility is `retry_policy.retry_on` (`exception` / `timeout` / `llm_failure`, shipped default `[\"exception\"]`), every failed attempt consumes one `max_attempts` unit, and deadline expiry is distinguished from a callback-raised `TimeoutError`.",
            "Operational Notes (`:149-150` region): keep the `halted` terminal-state bullets; add the side-effect rule sentence (a retry never follows an attempted non-READ tool call) and the LLM-failure status path (`failed` written once).",
            "Intent and failure behavior only; no code restatement (Plan Documentation Impact). UNK-01/UNK-02 are settled owner decisions, so no Needs-Confirmation marker is required; the conservative side-effect rule is described as current behavior, with relaxation deferred to a future owner decision (UNK-06).",
        ],
        assumptions=[
            "The table is shared with wfrecovery001 (`20261101-145309_24`) and wflease001 (`20261101-163219_15`) procedures that land earlier; Plan Assumptions: different sections, and the later change reconciles the transitions rows — this document reconciles last.",
        ],
        design=["Docs describe the configuration-driven policy (readable from `config/workflows/default.json`) instead of restating code."],
        alternatives=["A new docs page — rejected: REQ-010 names the three passages of this file."],
        procedure=[
            "Edit the three passages listed in Scope.",
            "Run the docs checkers (Plan Validation plan).",
        ],
        method="Markdown section edits.",
        details=[
            "Docs language policy: English file content (repo convention), verified by `check_docs_japanese`.",
            "`docs/10_adr/adr_02_02_001...md` decision 6 stays true under the shipped configuration and is not a target (Plan Documentation Impact).",
        ],
        compatibility=["`docs/00_index.md` task-scope mapping applies (file is located through 'Document References by Task', Plan Documentation Impact)."],
        security=[],
        rollback=["Revert the document edits; code and docs land as one chain but each doc edit is independently revertable."],
        validation=[
            "`uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py` (Plan Validation plan).",
        ],
        completion=["AC-10: the passages describe the implemented policy and contract and pass the docs checkers."],
        out_of_scope=["ADR amendment (Plan Documentation Impact; only if the owner changes the outcome).", "Startup Recovery section (`:143+`, owned by wfrecovery001/wflease001 rows)."],
        reqs="`REQ-010`",
        phase="Phase 5 (Documentation)",
        related="`scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow_engine_adapter.py`, `config/workflows/default.json`",
    )


if __name__ == "__main__":
    main()
