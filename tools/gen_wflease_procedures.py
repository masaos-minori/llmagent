"""Generate the wflease001 implementation-procedure documents (batch 20261101-163219)
in the canonical 14-section format used by batches 20261101-140834 and 20261101-145309.

Skeletons were created by `tools/generate_workitem.py --kind implementation-procedure
--all-rows` (shared pass timestamp recorded in the Plan). This script keeps each
line-1 workitem marker and rewrites the body from the verified content below.
Run: `uv run python tools/gen_wflease_procedures.py`.
"""

from __future__ import annotations

from pathlib import Path

BATCH = "20261101-163219"
PLAN = "plans/20261030-114516_wflease001_stale-attempt-lease.md"
ISSUE = "issues/20261030-105723_wflease001_stale-attempt-lease.md"
GENERATED_AT = "20261101-163219"

COMMON_ASSUMPTIONS = [
    f"Plan `{PLAN}` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.",
    "All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').",
    "Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).",
    "Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.",
    "Ledger landing order (Plan UNK-06): `master` records code 2 / \"1.2.0\" (`migrations_workflow.py:42`); wftaskapi001 procedure 12 (`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) reserves the next slot. This Plan takes code 3 / \"1.3.0\" only if its step registers before wftaskapi001's, otherwise 4 / \"1.4.0\" (same rule as `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).",
    "Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).",
]

TOOLCHAIN = "Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`."

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
    "All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.",
]


TARGETS = {
    "01": "scripts/shared/json_utils.py",
    "02": "scripts/agent/workflow/state_store.py",
    "03": "scripts/agent/workflow/attempt_ops.py",
    "04": "scripts/agent/workflow/idempotency_ops.py",
    "05": "scripts/agent/workflow/workflow_engine.py",
    "06": "scripts/db/schema_sql.py",
    "07": "scripts/agent/services/workflow_schema.py",
    "08": "tests/shared/test_json_utils.py",
    "09": "tests/agent/workflow/test_workflow_state_store.py",
    "10": "tests/agent/workflow/test_state_store.py",
    "11": "tests/agent/workflow/test_workflow_engine.py",
    "12": "tests/agent/workflow/test_stale_recovery_lease.py",
    "13": "tests/db/test_create_schema.py",
    "14": "tests/agent/test_repl_health.py",
    "15": "docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md",
    "16": "docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md",
    "17": "scripts/db/migrations_workflow.py",
    "18": "tests/db/test_migrations_workflow.py",
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
    new_target: bool = False,
    blockers: str = BLOCKER_PLACEHOLDER,
) -> None:
    marker = path.read_text(encoding="utf-8").splitlines()[0]
    body = f"""{marker}

## Goal

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
`{TARGETS[seq]}`{" (new)" if new_target else ""}

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
    if len(files) != 18:
        raise SystemExit(f"expected 18 batch files, found {len(files)}: {files}")

    doc(
        by_seq["01"],
        seq="01",
        goal="Add the strict shared UTC ISO-8601 parser `parse_iso_utc(value)` to `scripts/shared/json_utils.py` that accepts exactly what `now_iso()` writes plus offsets and fractional seconds, and rejects naive strings (REQ-001 / AC-1).",
        scope=[
            "Add `parse_iso_utc(value: str) -> datetime` returning a timezone-aware UTC `datetime`.",
            "Accept `YYYY-MM-DDTHH:MM:SSZ` (the production `now_iso()` format, `json_utils.py:45-51`), explicit offsets (`+09:00`-style, converted to UTC), and optional fractional seconds.",
            "Raise `ValueError` for naive strings (no `Z`/offset), malformed strings, and non-`str` input.",
            "No change to `now_iso` or `now_iso_raw` (Plan Scope Out-of-Scope: changing the output of `now_iso()`).",
        ],
        assumptions=[
            "The workflow timestamp format stays `YYYY-MM-DDTHH:MM:SSZ`; recovery round-trips it through `parse_iso_utc` unchanged (AC-1 test uses `now_iso()` output).",
        ],
        design=[
            "Implementation via `datetime.fromisoformat` after a single normalization: a trailing `Z` becomes `+00:00`; the result is `.astimezone(timezone.utc)` so the return value is always aware UTC.",
            "Naive input is rejected by checking `dt.tzinfo is None` after parsing — `fromisoformat` accepts naive strings silently, so the check is explicit (Plan Design 'Parser': a malformed row cannot be silently read as a local time).",
            "`ValueError` messages include the offending value and the reason (`naive`, `malformed`) so the recovery report (procedure 02) can log them verbatim.",
        ],
        alternatives=[
            "(a) reuse the local `fromisoformat(...replace('Z','+00:00'))` in `scripts/agent/memory/scoring.py:25` — rejected: not reusable from `agent.workflow` without a cross-module import of an unrelated module, and it accepts naive input (Plan Design).",
            "(b) `dateutil`/third-party parser — rejected: stdlib-only project convention (`rules/coding.md`).",
        ],
        procedure=[
            "Add `parse_iso_utc` after `now_iso_raw` (`json_utils.py:54-61`).",
            "Normalize a trailing `Z` to `+00:00`, parse with `datetime.fromisoformat`, reject naive results, and return `.astimezone(timezone.utc)`.",
            "Document the contract in the function docstring: accepted forms, rejection of naive input, and that it is the only ISO parser the workflow package may use.",
        ],
        method="Pure stdlib function in the existing shared module; no new imports beyond `datetime`/`timezone` already imported at `json_utils.py:1-20` region.",
        details=[
            "Signature: `parse_iso_utc(value: str) -> datetime`.",
            "`json_utils` is layer `shared`; `agent.workflow` may import it — the import contract (`lint-imports`, baseline 6 kept) is unaffected.",
            "`fromisoformat` on Python 3.13 accepts `+00:00` offsets natively; the only normalization needed is the trailing-`Z` substitution.",
        ],
        compatibility=[
            "New function; no existing caller changes. `mcp_servers/file` consumers of `now_iso_raw` (`mtime` freshness code) are untouched.",
        ],
        security=[],
        rollback=[
            "Delete the function; no data or call-site to unwind because nothing imports it before procedures 02/09 land.",
        ],
        validation=[
            "`uv run pytest tests/shared/test_json_utils.py -v` — new `TestParseIsoUtc` class (procedure 08) passes; all existing tests unchanged.",
            TOOLCHAIN,
        ],
        completion=[
            "AC-1: `parse_iso_utc` returns the correct UTC instant for `Z`, `+09:00` offsets, and fractional seconds; raises `ValueError` for naive and malformed input; a test uses `now_iso()` output.",
        ],
        out_of_scope=[
            "Any change to `now_iso`/`now_iso_raw` output (Plan Out-of-Scope).",
            "The local `Z` parse in `scripts/agent/memory/scoring.py` (Plan Out-of-Scope; stays as is).",
        ],
        reqs="`REQ-001`",
        phase="Phase 1 (Timezone-safe parsing and conservative detection; independent)",
        related="`tests/shared/test_json_utils.py`, `scripts/agent/workflow/state_store.py`",
    )

    doc(
        by_seq["02"],
        seq="02",
        goal="Rewrite stale-attempt detection and takeover in `scripts/agent/workflow/state_store.py`: parse only with `parse_iso_utc`, report unparseable rows, decide staleness from the lease (legacy age for lease-less rows), remove `_STALE_GRACE_SEC`, and make takeover a one-row conditional update (REQ-002, REQ-003, REQ-006, REQ-007, REQ-008 / AC-2..AC-7).",
        scope=[
            "Phase 1 increment (independent): `find_stale_running_attempts` (`state_store.py:250-277`) parses `started_at` with `json_utils.parse_iso_utc`; `time.mktime(time.strptime(...))` at `:265` and the silent `continue` are deleted; `_STALE_GRACE_SEC` (`:25`) is removed and replaced for lease-less rows by the named constant `_LEGACY_STALE_AGE_SEC = 3600` (REQ-008, interim safety).",
            "Phase 3 increment (after procedures 03-06 and 17 land): staleness = `lease_expires_at` parsed and expired; an unexpired lease is never recovered, including by another process (REQ-006 / AC-4).",
            "`recover_stale_attempts` (`:279-316`) takeover becomes one conditional `UPDATE attempts SET status='failed', ended_at=?, error_msg=? WHERE attempt_id=? AND status='running' AND owner_id IS ? AND lease_expires_at IS ?` requiring `cursor.rowcount == 1`; zero rows means another recoverer took it and the row is skipped (REQ-007 / AC-6).",
            "Recovery report: frozen dataclass `RecoveryReport(recovered, still_live, legacy_recovered, unparseable)` stored as `last_recovery_report`; `recover_stale_attempts()` keeps returning the recovered count (18 test references in 2 files rely on it, Plan Design 'Report API').",
            "Unparseable `started_at` or `lease_expires_at`: `logger.warning` with attempt id and the raw value, counted in `unparseable`, row neither recovered nor silently skipped (REQ-003 / AC-3).",
        ],
        assumptions=[
            "The conditional update is compare-and-swap on the exact `owner_id`/`lease_expires_at` values listed by the preceding `find` — a live owner that re-started an attempt in the meantime changes those values and fences the takeover.",
            "`IS` comparisons (not `=`) are used for the expected values so a legacy `NULL` owner/lease matches correctly in the legacy branch.",
        ],
        design=[
            "One detection function returns classified rows (stale-lease / legacy-stale / live / unparseable) so `find_stale_running_attempts` and `recover_stale_attempts` share the same decision; `find_stale_running_attempts` keeps its `list[dict]` return shape (external callers unchanged), extended with `owner_id`/`lease_expires_at` keys.",
            "Detection compares aware datetimes (`parse_iso_utc(lease) < now_utc`); no host-local time anywhere (AC-2: `rg \"mktime|strptime\" scripts/agent/workflow` is empty after this procedure).",
            "Phase 1 lands first with only the legacy-age branch (no lease columns exist yet); Phase 3 adds the lease branch behind `lease_expires_at IS NOT NULL` so the same code works before and after procedure 17 migrates an existing database.",
        ],
        alternatives=[
            "Heartbeat renewal instead of deadline lease — rejected by the owner (Plan UNK-02): `asyncio.wait_for` already bounds a normal stage, and a heartbeat adds event-loop `BEGIN IMMEDIATE` writes that can wait up to the 30000 ms busy timeout.",
            "Deleting `find_stale_running_attempts` and inlining into recovery — rejected: the method is a public seam used by the orchestrator-adjacent tests and keeps the detection testable without mutation.",
        ],
        procedure=[
            "Import `parse_iso_utc` from `shared.json_utils` in `state_store.py`.",
            "Replace the parse block at `:263-271` with `parse_iso_utc` + classification; remove `_STALE_GRACE_SEC` (`:25`) and add `_LEGACY_STALE_AGE_SEC = 3600`.",
            "Add the `RecoveryReport` frozen dataclass (module level) and `last_recovery_report` attribute set by `recover_stale_attempts`.",
            "Rewrite `recover_stale_attempts` (`:279-316`): classify rows, then per stale row run the conditional takeover update via the existing helper cursor; on `rowcount == 1` count it recovered (and `legacy_recovered` when the row had no lease); on `rowcount == 0` count nothing and log at info.",
            "Phase 3: extend the conditional `WHERE` with the expected `owner_id`/`lease_expires_at` values captured by the classify step (compare-and-swap fencing).",
        ],
        method="In-place rewrite of two methods plus module-level constants and one dataclass; all SQL parameter-bound through the existing `SQLiteHelper`.",
        details=[
            "`state_store.py` is 11164 B at baseline and stays under the 20480 B `check_module_size` limit (Plan Validation plan).",
            "Warning log format: `unparseable workflow attempt timestamp: attempt_id=%s value=%s` — the same line satisfies REQ-003 and the docs manual-recovery path (procedure 15).",
            "The failing-row branch keeps the attempt `running` (never a partial recovery) — the documented manual path owns it.",
        ],
        compatibility=[
            "`recover_stale_attempts()` return type stays `int` (Plan Risk row: 18 references in 2 test files).",
            "`orchestrator.py:92` call site is unchanged (Plan Reference Files).",
            "Task-level transition after a takeover follows the wfrecovery001 atomic-recovery procedures (Pending); this procedure must land after `implementations/20261101-145309_06_scripts_agent_workflow_state_store.py.md` so attempt+task failure stays atomic.",
        ],
        security=[
            "The takeover `WHERE` clause pins status and expected ownership values, so a takeover can only ever transition the exact stale row it observed — a racing or live owner is fenced by `rowcount`.",
        ],
        rollback=[
            "Phase 1 and Phase 3 land as separate commits; each reverts independently. Reverting 02 restores the grace-period detection but the columns from 17 stay (nullable, harmless).",
        ],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_state_store.py tests/agent/workflow/test_state_store.py tests/agent/workflow/test_stale_recovery_lease.py -v` (procedures 09, 10, 12).",
            "AC-2 check: `rg \"mktime|strptime\" scripts/agent/workflow` returns empty.",
            TOOLCHAIN,
        ],
        completion=[
            "AC-2 through AC-7 pass with production-format timestamps under `TZ=UTC` and a non-UTC `TZ`.",
            "`recover_stale_attempts()` still returns the recovered count and `last_recovery_report` exposes all four counts.",
        ],
        out_of_scope=[
            "Attempt numbering, ledger semantics, task transitions (wfrecovery001, Plan Out-of-Scope).",
            "Retry policy and failure propagation (`issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md`, Plan Out-of-Scope).",
        ],
        reqs="`REQ-002`, `REQ-003`, `REQ-006`, `REQ-007`, `REQ-008`",
        phase="Phases 1 and 3 (interim detection; lease-based takeover)",
        related="`scripts/shared/json_utils.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_stale_recovery_lease.py`",
        blockers="""| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Phase 3 increment is Blocked until procedures 03-06 and 17 (lease columns) and the wfrecovery001 conditional-finish/atomic-recovery procedures (Pending) land | No | — |""",
    )

    doc(
        by_seq["03"],
        seq="03",
        goal="Stamp `owner_id` and `lease_expires_at` when an attempt starts in `scripts/agent/workflow/attempt_ops.py` (REQ-004, REQ-005 / AC-5).",
        scope=[
            "Add a per-process owner identity created once: module-level lazy `get_owner_id() -> str` built from `socket.gethostname()`, `os.getpid()`, and a `secrets.token_hex(4)` suffix (Plan Design 'Owner identity': a bare PID can be reused, so the random part is required).",
            "Extend `start_attempt` (`attempt_ops.py:12-31`) with `lease_duration_sec: int | None = None`; when set, the INSERT at `:19-22` also writes `owner_id=get_owner_id()` and `lease_expires_at = started_at + lease_duration_sec` in the same production format (`Z` string computed from the aware `started_at`); when `None`, both columns stay NULL (legacy-compatible unit callers).",
        ],
        assumptions=[
            "`started_at` stays the existing value the function already writes; the lease is derived from the same instant so the AC-5 equality test compares parsed values, not strings.",
        ],
        design=[
            "`get_owner_id()` lives here (the attempt writer) and `idempotency_ops.py` imports it — the two attempt-insert sites must write the identical identity string (procedure 04).",
            "Lease math uses the aware `datetime` from the same `_now()` call that produced `started_at` (`attempt_ops.py:44-45` region), formatted back with the `Z` suffix so stored values round-trip through `parse_iso_utc`.",
        ],
        alternatives=[
            "UUID stored per attempt as the owner — rejected: REQ-005 asks for host+pid+random so a dead process is identifiable in the manual recovery path (procedure 15 documents it).",
        ],
        procedure=[
            "Add `get_owner_id()` with a module-level cached value.",
            "Add the `lease_duration_sec` parameter to `start_attempt` and extend the INSERT columns/values.",
            "Keep `finish_attempt` (`:34-48`) unchanged here — its conditional fencing is the wfrecovery001 procedure 04 (Pending).",
        ],
        method="Two small edits in one module; parameter-bound SQL unchanged pattern.",
        details=[
            "`import secrets` and `import socket`/`os` are stdlib and bandit-clean (`token_hex` is not a password primitive; no bandit finding expected).",
            "`AttemptRecord` (`models.py`) is not extended: the lease fields are row-level detection data, not part of the record the engine consumes.",
        ],
        compatibility=[
            "`lease_duration_sec` defaults to `None`, so every existing caller and test compiles and behaves identically until procedure 05 starts passing it.",
            "Blocked until procedures 06 and 17 land: the columns must exist before the INSERT references them (Plan execution-order rule).",
        ],
        security=[],
        rollback=[
            "Remove the parameter and identity helper; no persisted data depends on it once 02's takeover is also reverted.",
        ],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_state_store.py tests/agent/workflow/test_workflow_engine.py -v` (procedures 09, 11 assert the stamp).",
            TOOLCHAIN,
        ],
        completion=[
            "AC-5: a started attempt has `owner_id` and `lease_expires_at` equal to start plus the stage `timeout_sec` plus the margin (margin value owned by procedure 05).",
        ],
        out_of_scope=[
            "Conditional `finish_attempt` fencing (wfrecovery001 procedure 04).",
            "Lease renewal/heartbeat (owner decision, Plan UNK-02).",
        ],
        reqs="`REQ-004`, `REQ-005`",
        phase="Phase 3 (Ownership and lease-based recovery)",
        related="`scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_engine.py`",
        blockers="""| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Blocked until procedures 06 and 17 add the `owner_id`/`lease_expires_at` columns (Plan execution-order rule) | No | — |""",
    )

    doc(
        by_seq["04"],
        seq="04",
        goal="Carry the lease duration into the attempt-start transaction in `scripts/agent/workflow/idempotency_ops.py` so the idempotent stage-start path stamps the same ownership fields (REQ-005 / AC-5).",
        scope=[
            "Extend `begin_stage_if_new` (`idempotency_ops.py:18-67`) with `lease_duration_sec: int | None = None`; the attempt INSERT at `:48-51` writes `owner_id` and `lease_expires_at` exactly as procedure 03 (import `get_owner_id` from `attempt_ops`), inside the same `BEGIN IMMEDIATE` transaction that inserts the `processed_events` row.",
        ],
        assumptions=[
            "Engine calls always pass a concrete `lease_duration_sec` (procedure 05); the `None` default exists only so direct unit callers stay compilable.",
        ],
        design=[
            "Reuse `attempt_ops.get_owner_id()` and a shared lease-formatting helper rather than duplicating the identity/lease math in the second insert site (Plan Design 'Owner identity': one identifier per process).",
        ],
        alternatives=[
            "Stamp the lease in the engine after `begin_stage_if_new` returns — rejected: a separate statement outside the transaction can observe a half-written attempt row and adds a second `BEGIN IMMEDIATE` round under the 30000 ms busy timeout.",
        ],
        procedure=[
            "Add the parameter and extend the INSERT at `:48-51`.",
            "Import the identity/lease helpers from `attempt_ops` (same package layer; `lint-imports` unaffected).",
        ],
        method="One signature extension plus one INSERT edit; transaction structure untouched.",
        details=[
            "`begin_stage_if_new` already receives `db`, `event_id`, `task_id`, `stage_id` at `:18-24`; the new keyword goes last.",
            "The processed-event dedup semantics (`is_event_processed`) are untouched (Plan: different methods, compatible overlap with wftaskapi001).",
        ],
        compatibility=[
            "Blocked until procedures 06 and 17 land (columns must exist).",
            "Existing callers that omit the parameter keep today's behavior.",
        ],
        security=[],
        rollback=[
            "Revert the parameter; the transaction shape never changed.",
        ],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_engine.py -v` (procedure 11 asserts the stamp through the engine path).",
            TOOLCHAIN,
        ],
        completion=[
            "AC-5 holds for attempts started through the idempotent path, with identical `owner_id` as the plain path.",
        ],
        out_of_scope=[
            "Event dedup and ledger semantics (wfrecovery001 / wftaskapi001 contracts).",
        ],
        reqs="`REQ-005`",
        phase="Phase 3 (Ownership and lease-based recovery)",
        related="`scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `tests/agent/workflow/test_workflow_engine.py`",
        blockers="""| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Blocked until procedures 06 and 17 add the lease columns (Plan execution-order rule) | No | — |""",
    )

    doc(
        by_seq["05"],
        seq="05",
        goal="Pass the stage timeout plus the lease margin from `scripts/agent/workflow/workflow_engine.py` at attempt start and define the margin constant (REQ-005 / AC-5).",
        scope=[
            "Define the named module constant `_LEASE_MARGIN_SEC = 30` (Plan Assumptions UNK-03: named constant, not configuration).",
            "In `_run_stage` (`workflow_engine.py:242` region), where the stage timeout is computed at `:261` (`stage_def.timeout_sec if stage_def else 60`), pass `timeout + _LEASE_MARGIN_SEC` as `lease_duration_sec` to the `begin_stage_if_new` call at `:264`.",
            "Any direct `start_attempt` call path the engine uses (`_run_stage_with_retry`, `:188` region) passes the same value.",
        ],
        assumptions=[
            "`timeout_sec` per stage comes from `config/workflows/default.json` (120 s for `execute`); the lease horizon is therefore 150 s for `execute` — longer than any normally running stage because `asyncio.wait_for` (`:278`) enforces the timeout (Plan Design 'Lease without heartbeat').",
        ],
        design=[
            "The engine owns the margin because it owns the timeout; ops modules receive only the finished duration (procedures 03-04), keeping the constant single-sourced.",
            "No renewal calls are added (Plan UNK-02: deadline lease).",
        ],
        alternatives=[
            "Margin as configuration — rejected by Plan UNK-03 default; promote later only if the owner asks.",
            "Deriving the lease inside ops modules from a stage lookup — rejected: the engine already resolved `stage_def` and duplicating the lookup would drift from the enforced `wait_for` timeout.",
        ],
        procedure=[
            "Add `_LEASE_MARGIN_SEC = 30` near the module constants.",
            "Pass `lease_duration_sec=timeout + _LEASE_MARGIN_SEC` at both attempt-start call sites.",
        ],
        method="Constant plus two call-site keyword additions; no control-flow change.",
        details=[
            "Timeout source at `:261` already falls back to 60 s for stages without a definition; the lease falls back with it (`60 + 30`), so no lease is ever unstamped on the engine path.",
            "The engine keeps using `begin_stage_if_new` (`:264`) — no new imports beyond the ops signatures from procedures 03-04.",
        ],
        compatibility=[
            "Blocked until procedures 03, 04, 06 and 17 land (parameter and columns must exist first) — Plan execution-order rule.",
        ],
        security=[],
        rollback=[
            "Single-commit revert; behavior returns to no-lease attempt starts.",
        ],
        validation=[
            "`uv run pytest tests/agent/workflow/test_workflow_engine.py -v` (procedure 11).",
            TOOLCHAIN,
        ],
        completion=[
            "AC-5: for every engine-started attempt, `parse_iso_utc(lease_expires_at) - parse_iso_utc(started_at) == stage timeout_sec + 30`.",
        ],
        out_of_scope=[
            "Retry policy and timeout-failure propagation (`wfretry001` issue, Plan Out-of-Scope).",
            "`_run_stage_with_retry` structure changes beyond the two keyword arguments.",
        ],
        reqs="`REQ-005`",
        phase="Phase 3 (Ownership and lease-based recovery)",
        related="`scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `tests/agent/workflow/test_workflow_engine.py`",
        blockers="""| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Blocked until procedures 03-04 (parameters) and 06/17 (columns) land | No | — |""",
    )

    doc(
        by_seq["06"],
        seq="06",
        goal="Add the `owner_id` and `lease_expires_at` columns to the canonical `attempts` DDL and set the workflow schema version string in `scripts/db/schema_sql.py` (REQ-004 / AC-8).",
        scope=[
            "Extend the `attempts` CREATE block (`schema_sql.py:197-206`) with `owner_id TEXT` and `lease_expires_at TEXT` (both nullable, no CHECK, no index).",
            "Bump `WORKFLOW_SCHEMA_VERSION` (`:27`) from the current `\"1.2.0\"` to the landing-order value: `\"1.3.0\"` if this Plan's migration step registers before wftaskapi001's pending step, else `\"1.4.0\"` (Plan Assumptions, ledger landing order).",
        ],
        assumptions=[
            "`schema_sql.py` is row 6 of the frozen table and must land before rows 3-5 and the lease part of row 2 even though its table position is later (Plan Assumptions execution-order item); this document states that rule.",
        ],
        design=[
            "Nullable columns with no defaults so an existing database migrates with all-null values (AC-8) and lease-less legacy rows keep flowing through the REQ-008 age rule.",
            "The version string is the shared single source consumed by `workflow_schema.py:114` and the registry fingerprint; it must equal the target version of the registered step in procedure 17 at landing time.",
        ],
        alternatives=[
            "Separate `workflow_attempt_lease` table — rejected: REQ-004 names columns on `attempts`, and takeover compare-and-swap needs them on the same row the `find` reads.",
        ],
        procedure=[
            "Add the two columns to the `attempts` CREATE text (`:197-206`).",
            "Update `WORKFLOW_SCHEMA_VERSION` (`:27`) to the agreed landing-order value at implementation time (coordinate with `implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md` and `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).",
        ],
        method="DDL string and constant edits in the canonical schema template.",
        details=[
            "The no-vec0 copy in `tests/db/test_create_schema.py` (`:392-421`) must be edited in the same commit (procedure 13) to keep the parity tests green.",
            "`tools/check_db_separation.py` ownership inventory is unaffected (same table, same domain file).",
        ],
        compatibility=[
            "High blast radius recorded in the Plan Risks: `schema_sql.py` had 12 commits in 30 days with sibling plans; only the `attempts` block is touched here.",
        ],
        security=[],
        rollback=[
            "Revert the DDL edit; if procedure 17 already registered, its step and the version constant revert in the same plan-internal order (17 before 06).",
        ],
        validation=[
            "`uv run pytest tests/db/test_create_schema.py -v` (procedure 13).",
            "`uv run python tools/check_db_separation.py`",
            TOOLCHAIN,
        ],
        completion=[
            "AC-8: the version constant differs from `\"1.2.0\"` and the new columns appear in the canonical DDL.",
        ],
        out_of_scope=[
            "The migration registration itself (procedure 17); required-column startup enforcement (procedure 07).",
        ],
        reqs="`REQ-004`",
        phase="Phase 2 (Schema)",
        related="`scripts/db/migrations_workflow.py`, `scripts/agent/services/workflow_schema.py`, `tests/db/test_create_schema.py`, `tests/agent/test_repl_health.py`",
    )

    doc(
        by_seq["07"],
        seq="07",
        goal="Require the two new attempt columns in the startup schema check in `scripts/agent/services/workflow_schema.py` (REQ-004 / AC-8).",
        scope=[
            "Extend `REQUIRED_WORKFLOW_TABLES[\"attempts\"]` (`workflow_schema.py:48`) from `attempt_id`, `task_id`, `stage_id`, `status` to include `owner_id` and `lease_expires_at`.",
            "No other change: the version comparison at `:114` already reads `WORKFLOW_SCHEMA_VERSION` from `scripts/db/schema_sql.py` and reports a mismatch automatically.",
        ],
        assumptions=[
            "This procedure lands after procedure 17: a database at the previous version without the columns must fail the startup check with the actionable error the check already emits (`:93` required-columns loop), which is the designed gate, not an accident.",
        ],
        design=[
            "Required-column enforcement is additive so a stale deployment (un-migrated `workflow.sqlite`) is caught at startup before any recovery query references the columns.",
        ],
        alternatives=[
            "Optional columns in the check — rejected: AC-8 requires `check_workflow_schema` to fail when a required new column is missing.",
        ],
        procedure=[
            "Edit the `attempts` list at `:48`.",
            "Confirm the error message path at `:93-100` already names the missing column (no change expected).",
        ],
        method="One list literal edit.",
        details=[
            "`_WORKFLOW_SCHEMA_READ_ONLY` (`:54`) and `SchemaCheckResult` semantics unchanged.",
            "Grade note from the Plan baselines: `check_workflow_schema` is radon grade C (12); this edit does not add a branch.",
        ],
        compatibility=[
            "Landing order with procedures 06 and 17 (schema, then migration, then this check) keeps `/opt/llm/db/workflow.sqlite` deployments gated correctly.",
        ],
        security=[],
        rollback=[
            "Remove the two entries; already-migrated databases are unaffected (extra columns are harmless).",
        ],
        validation=[
            "`uv run pytest tests/agent/test_repl_health.py tests/db/ -v` (procedures 14, 13).",
            TOOLCHAIN,
        ],
        completion=[
            "AC-8: `check_workflow_schema` fails (with the column named) when `owner_id` or `lease_expires_at` is missing from `attempts`.",
        ],
        out_of_scope=[
            "The `tasks`/`processed_events`/`artifacts` entries and `workflow_schema_version` (`workflow_schema.py:46-52`).",
        ],
        reqs="`REQ-004`",
        phase="Phase 2 (Schema)",
        related="`scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `tests/agent/test_repl_health.py`, `tests/db/test_create_schema.py`",
    )

    doc(
        by_seq["08"],
        seq="08",
        goal="Add parser tests for `parse_iso_utc` to `tests/shared/test_json_utils.py` (REQ-001, REQ-009 / AC-1).",
        scope=[
            "New `TestParseIsoUtc` class after `TestNowIsoRaw` (`:453-510`): `Z` format (including `now_iso()` output round-trip, `:45`), `+09:00` offset converted to the same instant, fractional seconds, naive string rejected (`ValueError`), malformed string rejected, non-string rejected, result is timezone-aware UTC.",
        ],
        assumptions=[
            "Test style follows the existing classes in this file (plain `unittest`-style classes with pytest-compatible asserts).",
        ],
        design=[
            "The `now_iso()` round-trip case is the AC-1 anchor: `parse_iso_utc(now_iso())` parses to the same wall second and the returned value carries `timezone.utc`.",
        ],
        alternatives=[
            "Hypothesis property tests — rejected: not used in this repo's shared test convention.",
        ],
        procedure=[
            "Append `TestParseIsoUtc` with the case list above.",
            "Import `parse_iso_utc` in the module import block at `:18-19`.",
        ],
        method="Test-only file; no fixtures needed.",
        details=[
            "Naive rejection is asserted with `pytest.raises(ValueError)` and a message-substring check (`naive`).",
            "Offset equality compares aware datetimes (`==`), never wall-clock strings.",
        ],
        compatibility=["Existing `TestNowIso` (`:382-451`) and `TestNowIsoRaw` (`:453-510`) tests stay untouched (out-of-scope functions)."],
        security=[],
        rollback=["Delete the class."],
        validation=["`uv run pytest tests/shared/test_json_utils.py -v` — new cases pass on procedure 01's implementation and fail against `master` without it."],
        completion=["AC-1 fully covered by the new class."],
        out_of_scope=["Any change to existing `now_iso`/`now_iso_raw` tests."],
        reqs="`REQ-001`, `REQ-009`",
        phase="Phase 1 (Timezone-safe parsing and conservative detection)",
        related="`scripts/shared/json_utils.py`",
    )

    doc(
        by_seq["09"],
        seq="09",
        goal="Replace naive-format seeds and grace-based expectations in `tests/agent/workflow/test_workflow_state_store.py` with production-format, lease-based recovery tests (REQ-002, REQ-006, REQ-007, REQ-009 / AC-2..AC-7).",
        scope=[
            "Replace the naive seeds `\"2026-01-01T00:00:00\"` at `:286`, `:336`, `:360` (and remaining seeds inside the recovery block `:274-452`) with the production format (`...Z`) produced by `json_utils.now_iso`-equivalent literals.",
            "Re-point the recovery tests (`test_stale_attempt_marked_failed` `:274`, `test_find_stale_returns_only_old_attempts` `:348`, `test_recovered_attempt_has_ended_at_set` `:375`, `test_recover_multiple_stale_attempts` `:399`, `test_recover_no_stale_attempts` `:452`) onto lease semantics: expired-lease seeds are stale; unexpired-lease seeds are live; legacy seeds (NULL lease) follow the 3600 s age rule.",
            "Add host-timezone independence: the same seed set recovers identically under `TZ=UTC` and a non-UTC `TZ` set via `monkeypatch` + `time.tzset()` (REQ-002 / AC-2).",
        ],
        assumptions=[
            "The seed helper that inserts attempt rows must also seed `owner_id`/`lease_expires_at` after procedures 06/17 land; before that, Phase 1 seeds exercise only the legacy-age branch.",
        ],
        design=[
            "Phase 1 rewrites land with the legacy branch only (no lease columns in the fixture DB yet); Phase 3 extends the same tests with lease fixtures — the file keeps one fixture helper so both phases reuse it.",
        ],
        alternatives=[
            "Rewriting the file from scratch — rejected: 84 blast-radius references are elsewhere, but this file's passing structure is reused; only seeds and expectations change.",
        ],
        procedure=[
            "Switch every seeded timestamp literal to the `Z` format.",
            "Convert grace-based expectations to lease/legacy expectations.",
            "Add the two `TZ` variants for the find/recover pair.",
            "Add an unparseable-seed case asserting the `RecoveryReport.unparseable` count and that the row stays `running`.",
        ],
        method="Seed-literal replacement plus expectation edits inside the existing test classes.",
        details=[
            "`time.tzset()` is POSIX-only; tests are skipped on non-POSIX platforms exactly like the Plan's Tests section prescribes `TZ` via `monkeypatch` and `tzset`.",
            "Assertions compare parsed instants (`parse_iso_utc`), not raw strings, except the format-literal seeds themselves.",
        ],
        compatibility=["Mock-free: these tests keep using the real fixture DB (`workflow_db` fixture) they already use."],
        security=[],
        rollback=["Characterize: pre-change tests pass on old code only with naive seeds; revert keeps them green on old code."],
        validation=["`uv run pytest tests/agent/workflow/test_workflow_state_store.py -v`"],
        completion=["AC-2, AC-4..AC-7 covered through the lease fixtures in this file."],
        out_of_scope=["Task-transition expectations (wfrecovery001 procedures, already landed or pending per `implementations/20261101-145309_*`)."],
        reqs="`REQ-002`, `REQ-006`, `REQ-007`, `REQ-009`",
        phase="Phases 1 and 3",
        related="`scripts/agent/workflow/state_store.py`, `scripts/shared/json_utils.py`, `tests/agent/workflow/test_stale_recovery_lease.py`",
    )

    doc(
        by_seq["10"],
        seq="10",
        goal="Replace the mocked detection/recovery tests in `tests/agent/workflow/test_state_store.py` with real-database report and race tests (REQ-003, REQ-009 / AC-2, AC-3).",
        scope=[
            "Replace the mock-based tests (`find_stale_running_attempts` lambdas at `:26-167`) with real-`StateStore` tests against the fixture DB: single stale recovery, non-stale untouched, mixed stale/live, multiple stale, no-running-attempts.",
            "Replace the `\"not-a-date\"` test (`:217`): an unparseable `started_at` (and a new unparseable `lease_expires_at` case) yields a warning log (captured with `caplog`), an `unparseable` count in `last_recovery_report`, and a row still `running` (REQ-003 / AC-3).",
            "Keep the concurrency-flavored test (`test_recover_concurrent_calls_only_one_succeeds`, `:74`) but re-express it against the conditional update: two sequential recover calls produce one takeover (`rowcount` path), deep two-connection racing belongs to procedure 12.",
        ],
        assumptions=[
            "This file imports the same fixture helpers as procedure 09's file so seeds stay in one style.",
        ],
        design=[
            "Mock removal is deliberate (REQ-009: the mock-only seeds are replaced): mocking `find_stale_running_attempts` hid the production parse defect (Plan Background).",
        ],
        alternatives=[
            "Keeping the mocks for speed — rejected: the fixture DB is an in-memory/temp SQLite and already used by sibling files.",
        ],
        procedure=[
            "Delete the lambda-mock blocks and rebuild each scenario with seeded rows (production-format timestamps, explicit lease values).",
            "Add the `caplog` warning assertion (`unparseable workflow attempt timestamp`).",
            "Assert the four-count report after each scenario.",
        ],
        method="Test rewrite in place; same test-class skeleton names.",
        details=[
            "Report assertions also lock `recover_stale_attempts()`'s int return (compatibility with the 18 existing references).",
        ],
        compatibility=["Any remaining test in this file that mocks `_db` internals is left alone unless it touches detection."],
        security=[],
        rollback=["File-level revert."],
        validation=["`uv run pytest tests/agent/workflow/test_state_store.py -v`"],
        completion=["AC-3 fully covered in this file; AC-2 partially with procedure 09."],
        out_of_scope=["Multi-connection race coverage (procedure 12)."],
        reqs="`REQ-003`, `REQ-009`",
        phase="Phase 1 (Timezone-safe parsing and conservative detection)",
        related="`scripts/agent/workflow/state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`",
    )

    doc(
        by_seq["11"],
        seq="11",
        goal="Assert in `tests/agent/workflow/test_workflow_engine.py` that every engine-started attempt carries the owner stamp and the timeout-plus-margin lease (REQ-005, REQ-009 / AC-5).",
        scope=[
            "Extend the existing retry/timeout tests (`test_retry_succeeds_on_second_attempt` `:113`, `test_timeout_raises_workflow_timeout_error` `:165-230`): after a stage runs, read the attempt row and assert `owner_id` is non-null and `parse_iso_utc(lease_expires_at) - parse_iso_utc(started_at) == stage timeout_sec + 30` (`StageDefinition(timeout_sec=5)` fixtures at `:41-43` make the expected 35 s).",
            "Add one case asserting the fallback horizon (no stage def / default 60 s path yields 90 s) if the fixture allows a stage-less run; otherwise assert with the 5 s stages only.",
        ],
        assumptions=[
            "Engine fixtures already build stores and engines per test (this file's existing style); no new fixture layer.",
        ],
        design=[
            "Assertions read the persisted row through the store (not the engine's in-memory objects) so the test locks the DB contract, per REQ-005.",
        ],
        alternatives=[
            "Asserting on `begin_stage_if_new` call arguments with spies — rejected: the Plan AC-5 is about the stored row, and spies would survive a write-side bug.",
        ],
        procedure=[
            "Add a shared helper `fetch_attempt(conn, attempt_id)` mirroring the file's existing row reads.",
            "Extend the two named tests and add `test_attempt_start_stamps_lease`.",
        ],
        method="Test-only edits inside existing classes.",
        details=[
            "No heartbeat/renewal assertion — Plan UNK-02 (deadline lease).",
        ],
        compatibility=["Existing assertions in these tests stay; this is additive unless a retry test's row expectations change."],
        security=[],
        rollback=["Delete the added helper and cases."],
        validation=["`uv run pytest tests/agent/workflow/test_workflow_engine.py -v`"],
        completion=["AC-5 covered end-to-end through the engine path."],
        out_of_scope=["Timeout/retry behavior changes themselves (`wfretry001` issue, Plan Out-of-Scope)."],
        reqs="`REQ-005`, `REQ-009`",
        phase="Phase 3 (Ownership and lease-based recovery)",
        related="`scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/shared/json_utils.py`",
    )

    doc(
        by_seq["12"],
        seq="12",
        goal="Create the multi-connection lease-recovery test module `tests/agent/workflow/test_stale_recovery_lease.py` covering live-lease protection, owner death, takeover races, fencing, and legacy rows (REQ-007, REQ-008, REQ-009 / AC-4..AC-7).",
        scope=[
            "New file with two independent SQLite connections on one temp `workflow.sqlite` (two `SQLiteHelper` instances standing in for two agent processes — no process lock exists, Plan Background).",
            "Cases: live attempt with unexpired lease is not recovered by the second process (AC-4); owner death with expired lease is recovered exactly once (AC-6); two concurrent recoverers produce exactly one takeover (AC-6, one `rowcount==1`, one `rowcount==0`); repeated recovery changes nothing (AC-6); legacy lease-less row older than 3600 s recovered once, younger or unparseable not recovered (AC-7); late `finish_attempt` by the fenced owner raises the typed error (AC-7 — gated on the wfrecovery001 conditional-finish procedure, see blockers).",
            "Timestamp literals in production `Z` format; the race case uses `lease_expires_at` values computed via `parse_iso_utc` so wall-clock arithmetic is explicit.",
        ],
        assumptions=[
            "Two connections use the same `begin_immediate()` path as production so SQLite busy handling is exercised the same way (`scripts/db/helper.py`, Plan Reference Files).",
        ],
        design=[
            "Race ordering is deterministic: process B calls `recover_stale_attempts` while process A's row is still mid-stage (lease unexpired) for AC-4, and after lease expiry for AC-6; no sleeps on timing thresholds, only on lease-boundary literals.",
        ],
        alternatives=[
            "True multiprocessing via `subprocess` — rejected: the fencing semantics are all in SQL compare-and-swap; two connections on one process reproduce the interleaving deterministically.",
        ],
        procedure=[
            "Create the module with a fixture that opens the temp DB and two helpers.",
            "Implement the six cases above; mark the AC-7 fencing case with `pytest.mark.xfail(strict=True)` referencing wfrecovery001 procedure 04 until its typed error exists, and remove the mark in the same PR chain once it lands (Plan UNK-06).",
        ],
        method="New pytest module, class-per-scenario layout like sibling files.",
        details=[
            "File name is frozen in the Plan table (`test_stale_recovery_lease.py`); directory `tests/agent/workflow/` exists.",
            "AC-4 note: the execute stage runs 120 s in production; the test uses short synthetic timeouts (1-2 s) with the same margin constant.",
        ],
        compatibility=["Pure addition; no existing test depends on it."],
        security=[],
        rollback=["Delete the file."],
        validation=["`uv run pytest tests/agent/workflow/test_stale_recovery_lease.py -v`; the new tests must fail against pre-change `master` (Plan Validation plan)."],
        completion=["AC-4..AC-7 demonstrated end-to-end."],
        out_of_scope=["`wfretry001` retry semantics; task-level resume paths."],
        reqs="`REQ-007`, `REQ-008`, `REQ-009`",
        phase="Phase 3 (Ownership and lease-based recovery)",
        related="`scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/db/helper.py`",
        new_target=True,
        blockers="""| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | The AC-7 fenced-late-finish case depends on the Pending wfrecovery001 conditional-finish procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`) | No | — |""",
    )

    doc(
        by_seq["13"],
        seq="13",
        goal="Update schema-parity and version assertions in `tests/db/test_create_schema.py` for the two new `attempts` columns (REQ-004, REQ-009 / AC-8).",
        scope=[
            "Extend the embedded no-vec0 `attempts` DDL copy (`:392-421`) with `owner_id TEXT` and `lease_expires_at TEXT` so the parity test keeps the template and the copy identical.",
            "Update the workflow version assertion (currently pinned to the landed `\"1.2.0\"` behavior via the `workflow_schema_version` assertions at `:662-728`) to the new landing-order version together with procedure 17's registry codes.",
            "Extend the attempts-column assertions (`INSERT` shape test around `:575-581`) to write and read back the two columns.",
        ],
        assumptions=[
            "The exact expected version string is filled at implementation time from the landing-order decision (procedure 06/17); this document does not fix it.",
        ],
        design=[
            "Column assertions use `PRAGMA table_info` on a fresh DB so a forgotten DDL edit breaks immediately rather than surfacing in the startup check only.",
        ],
        alternatives=["Rely on the startup-check tests alone — rejected: `tests/db/` is the canonical schema-parity home (Plan Tests section)."],
        procedure=[
            "Edit the DDL copy at `:392-421`.",
            "Add the column-presence assertions for `attempts`.",
            "Adjust the ledger/version assertions in sync with procedure 17.",
        ],
        method="Fixture-string and assertion edits in the existing test module.",
        details=[
            "`test_create_schema.py` had 15 commits in 30 days (Plan Affected areas) — keep the diff surgical: only the workflow `attempts` blocks and version pins.",
        ],
        compatibility=["Must land in the same commit as procedure 06 or the parity test breaks."],
        security=[],
        rollback=["Revert with procedure 06."],
        validation=["`uv run pytest tests/db/test_create_schema.py -v`"],
        completion=["AC-8: columns present in a freshly created DB; version differs from the previous value."],
        out_of_scope=["Non-workflow domain schema blocks."],
        reqs="`REQ-004`, `REQ-009`",
        phase="Phase 2 (Schema)",
        related="`scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `tests/db/test_migrations_workflow.py`",
    )

    doc(
        by_seq["14"],
        seq="14",
        goal="Extend the minimal workflow-table fixtures in `tests/agent/test_repl_health.py` so the startup health check exercises the new required columns (REQ-004 / AC-8).",
        scope=[
            "Add `owner_id TEXT` and `lease_expires_at TEXT` to the hand-written `CREATE TABLE attempts` fixture (`:538`, fixture block `:538-590`) so `check_workflow_schema` passes on the fixture once procedure 07 makes the columns required.",
            "Add one negative case: dropping `owner_id` from the fixture makes the startup check report the missing column (AC-8).",
        ],
        assumptions=[
            "These fixtures intentionally build minimal (un-migrated-shaped) tables; the new columns join the existing minimal vocabulary, not the full canonical DDL.",
        ],
        design=["The negative case locks the actionable error path the operational runbook (procedure 15) promises."],
        alternatives=["Reuse `create_workflow_tables` in the fixture — rejected: the point of this file is minimal hand-built tables to prove the check catches drift."],
        procedure=[
            "Edit the fixture DDL at `:538`.",
            "Add the missing-column negative test next to the existing health-check cases (`:523-554`, `:599` region).",
        ],
        method="Fixture string edit plus one test case.",
        details=["Fixture edits must land with procedure 07 in the same commit chain or these tests fail at startup-check time."],
        compatibility=["Other fixtures in the block (`tasks`, `processed_events`) are untouched."],
        security=[],
        rollback=["Revert with procedure 07."],
        validation=["`uv run pytest tests/agent/test_repl_health.py -v`"],
        completion=["AC-8 covered for the startup path."],
        out_of_scope=["Health checks outside the workflow-table section."],
        reqs="`REQ-004`",
        phase="Phase 2 (Schema)",
        related="`scripts/agent/services/workflow_schema.py`, `scripts/db/schema_sql.py`",
    )

    doc(
        by_seq["15"],
        seq="15",
        goal="Rewrite the \"Startup Recovery\" section of `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` with lease semantics, the timestamp format contract, and the manual recovery path (REQ-010 / AC-9).",
        scope=[
            "Rewrite the section starting at `:143` (currently describing elapsed-time recovery that never changes task status): staleness = expired `lease_expires_at` (stamped at attempt start from the stage `timeout_sec` plus the 30 s margin); legacy lease-less rows use the 3600 s age rule; unparseable timestamps are reported and left for the manual path.",
            "Document the timestamp contract: workflow timestamps are `YYYY-MM-DDTHH:MM:SSZ` written by the shared clock and parsed only by `scripts/shared/json_utils.parse_iso_utc`.",
            "Document the operational manual recovery for rows left `running` (unparseable or legacy-young): identify the owning process from `owner_id` (host:pid:suffix), inspect, and correct via the documented manual SQL path — no automated takeover.",
        ],
        assumptions=[
            "Baseline wording expectation at landing: wfrecovery001 procedure 24 (`implementations/20261101-145309_24_docs_23_agent_agent_03_03_turn-processing-flow-workflow-engine.md.md`, Pending) rewrites the same section to atomic attempt+task failure semantics first; this procedure amends that rewrite (the later plan reconciles the shared wording per Plan Assumptions).",
        ],
        design=[
            "Intent and ownership only — no DDL or code restatement (Plan Documentation Impact).",
        ],
        alternatives=["A new dedicated lease document — rejected: the Plan names this section as the home."],
        procedure=[
            "Apply this rewrite on top of the wfrecovery001 rewrite (or on the current text if wfrecovery001's lands second, in which case its document carries the reconciliation note).",
            "Run the docs checkers listed in the Validation plan after the edit.",
        ],
        method="Section-level documentation rewrite.",
        details=[
            "The Needs-Confirmation marker for UNK-01 (multi-process support) stays recorded if unresolved (Plan Documentation Impact).",
            "`docs/41_db/db_02` is not a target (names tables only, Plan Documentation Impact).",
        ],
        compatibility=["English content per `skills/DESIGN.md` Output language."],
        security=[],
        rollback=["Restore the section text from the pre-change commit."],
        validation=["`uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py`."],
        completion=["AC-9 for the docs half: the section describes lease semantics and the manual path."],
        out_of_scope=["Other sections of the same document."],
        reqs="`REQ-010`",
        phase="Phase 4 (Documentation and ADR)",
        related="`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `scripts/agent/workflow/state_store.py`",
    )

    doc(
        by_seq["16"],
        seq="16",
        goal="Amend ADR-001 INV-07 in `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` so \"interrupted Attempt\" means a lease-expired attempt (REQ-010 / AC-9).",
        scope=[
            "Amend INV-07 (`:171`) under the ADR change protocol: recovery targets attempts whose `lease_expires_at` has expired (or lease-less legacy rows past the conservative age), never an attempt with an unexpired lease; the test-evidence row (`:187`) gains `tests/agent/workflow/test_stale_recovery_lease.py`.",
        ],
        assumptions=[
            "wfrecovery001 procedure 23 amends the same INV-07 first (Pending); the landing order decides which amendment is applied to which baseline text — the later document reconciles (Plan Assumptions overlap record).",
        ],
        design=[
            "Accepted ADR: the change is an amendment note with rationale, not a silent rewrite; `check_adr_preservation.py` reports the change and this procedure supplies the explanation line the checker requires.",
        ],
        alternatives=["Supersede the ADR — rejected: INV-07's intent survives; only its definition of 'interrupted' is refined."],
        procedure=[
            "Apply the amendment on top of the wfrecovery001 amendment baseline.",
            "Add the change rationale (timezone defect + live-attempt theft) adjacent to the amended INV-07 line.",
        ],
        method="Single-invariant amendment plus test-table row update.",
        details=["Preserve the INV number and table structure (ADR checker contracts)."],
        compatibility=["English content."],
        security=[],
        rollback=["Restore from pre-change commit; the ADR checker compares against git history."],
        validation=["`uv run python tools/check_adr_preservation.py`"],
        completion=["AC-9 for the ADR half."],
        out_of_scope=["Other INVs and the decision log."],
        reqs="`REQ-010`",
        phase="Phase 4 (Documentation and ADR)",
        related="`docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `tests/agent/workflow/test_stale_recovery_lease.py`",
    )

    doc(
        by_seq["17"],
        seq="17",
        goal="Register the lease `ADD COLUMN` migration step and version codes in `scripts/db/migrations_workflow.py` (REQ-004 / AC-8).",
        scope=[
            "Append a `MigrationSpec` `workflow_attempt_lease` to `REGISTRY` (`:246-262`): `from_version=2`, `to_version=3` (or `4` if wftaskapi001's pending step registers first), `mutation_sql` = `ALTER TABLE attempts ADD COLUMN owner_id TEXT;` + `ALTER TABLE attempts ADD COLUMN lease_expires_at TEXT;`, precondition: attempts table exists and the prior workflow step is applied, postcondition: both columns present via `PRAGMA table_info`.",
            "Extend `WORKFLOW_VERSION_CODES` (`:42`, currently `{\"1.1.0\": 0, \"1.2.0\": 2}`) with the landing-order mapping (`\"1.3.0\": 3` or `\"1.4.0\": 4`) and raise `WORKFLOW_TARGET_VERSION` (`:48`) to match procedure 06's version string.",
        ],
        assumptions=[
            "Landing-order rule (Plan UNK-06, shared with `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md` and `implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`): the plan whose step registers first takes code 3 / \"1.3.0\"; the others shift up. The codes are fixed at implementation time, not in this document.",
            "dbmig001 registry semantics (forward-only, backup gate, per-step pre/post conditions) are already implemented in this module (`MigrationRunner`, stamped markers).",
        ],
        design=[
            "Two nullable `ADD COLUMN` statements in one step (Plan Design 'Migration'): an existing database with `running` rows migrates with null values, which is exactly the legacy-row population REQ-008 governs.",
            "The step runs before the code that writes the columns (procedures 03-05) and before the required-column check (procedure 07) — the plan-internal order 17 → 03/04/05 → 07.",
        ],
        alternatives=[
            "Table-rebuild migration — rejected: SQLite `ADD COLUMN` is in-place and the columns are nullable with no constraints.",
            "Un-registered ad-hoc ALTER — rejected: dbmig001 forward-only registry is the contract (Plan Reference Files).",
        ],
        procedure=[
            "Add the `MigrationSpec` entry after `workflow_tool_call_state`.",
            "Update `WORKFLOW_VERSION_CODES` and `WORKFLOW_TARGET_VERSION` with the landing-order values.",
            "Extend the fingerprint/validation path (`:159-163` version-code check) automatically through the codes map — verify no hardcoded list exists elsewhere in the module.",
        ],
        method="Registry data edit; runner code unchanged.",
        details=[
            "Mutation SQL follows the existing `_TOOL_STATE_MUTATION_SQL` pattern (module-level SQL constants near `:246`).",
            "Postcondition raises on missing columns exactly like `_postcondition_tool_state` (`:240-242` pattern).",
        ],
        compatibility=[
            "Shared file with wfrecovery001 (landed codes 0-2) and pending wftaskapi001 code 3 reservation — coordinate at landing (Blocker Log).",
            "Deploy prerequisite per Plan Phase 5: the `/opt/llm/db/workflow.sqlite` migration runs with the dbmig001 backup gate; deploying is the user's decision.",
        ],
        security=[],
        rollback=[
            "Forward-only registry: rollback is restoring the pre-migration backup taken by the dbmig001 gate (Plan Design 'Migration').",
        ],
        validation=[
            "`uv run pytest tests/db/test_migrations_workflow.py tests/db/test_create_schema.py -v` (procedure 18).",
            "`uv run python tools/check_db_separation.py`",
            TOOLCHAIN,
        ],
        completion=[
            "AC-8: a database at the previous version with existing `running` rows migrates with the new columns null.",
        ],
        out_of_scope=["Data backfill of `owner_id`/`lease_expires_at` for existing rows (they stay null by design)."],
        reqs="`REQ-004`",
        phase="Phase 2 (Schema)",
        related="`scripts/db/schema_sql.py`, `scripts/agent/services/workflow_schema.py`, `tests/db/test_migrations_workflow.py`, `tests/db/test_create_schema.py`",
        blockers="""| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Ledger code/version values are Blocked until the landing order against pending wftaskapi001 step (code 3 / "1.3.0" reservation) is fixed | No | — |""",
    )

    doc(
        by_seq["18"],
        seq="18",
        goal="Cover the lease migration step in `tests/db/test_migrations_workflow.py`: registration, row-preserving migration over `running` rows, resume/idempotence, and version codes (REQ-004, REQ-009 / AC-8).",
        scope=[
            "Extend `TestWorkflowRegistry` (`:106-121`) with `test_registry_holds_the_attempt_lease_step` (spec id, from/to codes, pre/post conditions present).",
            "Extend the migration-execution pattern (`TestWorkflowToolCallStateStep`, `:192-260`): seed an old-shape attempts table with `running` rows, apply the registry path, assert both columns exist and existing rows keep all values with the new ones null; re-applying is empty (resume); a forged stamp without the ledger row is refused (pattern at `:260`).",
            "Assert `WORKFLOW_VERSION_CODES`/`WORKFLOW_TARGET_VERSION` include the landing-order code together with procedure 17's edit.",
        ],
        assumptions=[
            "Expected version codes in assertions are written at implementation time from the landing-order decision (procedure 17).",
        ],
        design=["Reuse the file's existing tmp_path DB fixture helpers so the new step's tests mirror the landed step-by-step structure."],
        alternatives=["Parameterizing a step-matrix test — rejected: the file's per-step explicit style is the convention."],
        procedure=[
            "Add the registry case.",
            "Add a `TestWorkflowAttemptLeaseStep` class following the `:192-260` template.",
            "Extend version-code assertions.",
        ],
        method="Test-only additions in the existing module.",
        details=[
            "`running`-row preservation is the AC-8 anchor: seed with the exact production `Z` `started_at` format so the migrated rows also feed procedure 02's legacy branch.",
        ],
        compatibility=["Land with procedure 17 in the same commit chain."],
        security=[],
        rollback=["Revert with procedure 17."],
        validation=["`uv run pytest tests/db/test_migrations_workflow.py -v`"],
        completion=["AC-8 migration half covered."],
        out_of_scope=["Production `/opt/llm/db/workflow.sqlite` execution (deploy skill gate)."],
        reqs="`REQ-004`, `REQ-009`",
        phase="Phase 2 (Schema)",
        related="`scripts/db/migrations_workflow.py`, `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`",
    )


if __name__ == "__main__":
    main()
