## Goal
Give `StateStore` two thin facade methods (`StateStore.begin_stage_if_new` (new) and `StateStore.record_artifact` (new)) that call the ops functions with `self._db`, and make `recover_stale_attempts` take no db argument (the method binds `db = self._db` internally), so callers no longer pass the store's own connection back into the store.

## Scope
**Release unit**: wfaudit015-full (all-or-nothing: the signature change and the 31 test call-site retargets in procedure documents 04-06 must land in the same unit, or the suite breaks mid-unit).

**Plan row implemented**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md` Implementation Target Files row 1 (`scripts/agent/workflow/state_store.py`, `REQ-001`/`REQ-002`; plan step 1).

**In scope**:
- Import extensions in `scripts/agent/workflow/state_store.py`.
- New facade methods `begin_stage_if_new` and `record_artifact` (pure delegation, no logic movement).
- `recover_stale_attempts(self, db: SQLiteHelper) -> int` becomes `recover_stale_attempts(self) -> int` with a `db = self._db` binding as the first statement of the body.

**Out of scope**:
- Changing `idempotency_ops.begin_stage_if_new` or `artifact_ops.record_artifact` signatures (both confirmed no-change).
- Deleting `get_connection()` (kept; `UNK-01` follow-up).
- Call-site conversions (`workflow_engine.py`, `orchestrator.py`) and test retargets — procedure documents 02-06.

**Dependencies (landing order)**: This document's edits are symbol-anchored and land after `implementations/20261108-134201_01_scripts_agent_workflow_state_store.py.md` (wfaudit001), `implementations/20261108-135741_01_scripts_agent_workflow_state_store.py.md` (wfaudit007), and `implementations/20261108-170505_02_scripts_agent_workflow_state_store.py.md` (wfaudit009). Those procedures extend the `recover_stale_attempts` body and delete `find_stale_running_attempts`/`pending_tool_calls`; the `db = self._db` binding added here absorbs their `db`-referencing statements unchanged.

## Assumptions
| ID | Assumption | Validation |
|---|---|---|
| A-001 | Every current caller of `recover_stale_attempts` passes the store's own connection (verified at `ad48bfa28`: orchestrator L92 + 31 test sites), so dropping the argument is behavior-preserving. | Verified (grep census) |
| A-002 | The ops functions take `SQLiteHelper` and manage their own begin/commit patterns, so passing `self._db` preserves transaction semantics exactly. | Verified (`idempotency_ops.py` begin_immediate, no explicit commit; `artifact_ops.py` commit after insert) |
| A-003 | At execution time the `recover_stale_attempts` body may already contain statements added by `134201_01`/`135741_01`; they reference `db` locally and keep working after the binding. | Design contract (plan Notes reconciliation) |
| A-004 | `SQLiteHelper` stays imported: `get_connection()` still returns it and body type hints keep using it. | Verified (L13 import, L58-65) |

## Design decisions
| ID | Decision | Rationale |
|---|---|---|
| D-001 | Drop the db argument entirely (no `db: SQLiteHelper \| None = None` optional form). | An optional argument keeps the bypass route open; the plan requires a single auditable entry (REQ-002). No caller owns a foreign connection today. |
| D-002 | Bind `db = self._db` as the first body statement of `recover_stale_attempts` instead of renaming every `db` use. | Symbol-anchored edit that cannot collide with statements siblings add to the body; zero churn inside the recovery logic (REQ-004). |
| D-003 | Facade methods call the ops functions module-qualified (`idempotency_ops.begin_stage_if_new(...)`, `artifact_ops.record_artifact(...)`), importing the modules rather than the functions. | Avoids shadowing: the method names are identical to the ops function names, and state_store.py already imports `attempt_ops`/`tool_call_state_ops` in module form. |
| D-004 | `begin_stage_if_new` goes in the Attempt section after `finish_attempt`; `record_artifact` goes in a new `# ── Artifact ──` section inserted before `# ── Diagnostic Queries ──`. | Matches the file's section-per-domain layout; keeps the Startup Recovery section untouched. |

## Alternatives considered
| Alternative | Reason rejected |
|---|---|
| Keep `recover_stale_attempts(db)` and add a no-arg overload via default | Two call shapes keep the raw-connection route alive; REQ-003 audit becomes ambiguous. |
| Move the SQL from ops modules into the facade methods | Plan Design is explicit: thin delegation, no logic movement; ops modules remain the SQL owner. |
| Import ops functions directly (`from agent.workflow.idempotency_ops import begin_stage_if_new`) | Name collision with the new method names inside the class module; module-qualified imports match the file's existing style. |

## Implementation
### Target file
`scripts/agent/workflow/state_store.py` (plan target row 1).

### Procedure
Step 1: extend imports. Step 2: add facade `begin_stage_if_new`. Step 3: add Artifact section with facade `record_artifact`. Step 4: re-signature `recover_stale_attempts` and add the `db = self._db` binding.

### Method
Symbol-anchored edits on the file as it exists after `134201_01`, `135741_01`, `170505_02` land. HEAD `ad48bfa28` anchors are given as reference points; the edits anchor on symbols, not line numbers.

### Details
Step 1 — imports. Current (L20-21):
```python
from agent.workflow import attempt_ops, tool_call_state_ops
from agent.workflow.models import TaskRecord
```
Change to:
```python
from agent.workflow import artifact_ops, attempt_ops, idempotency_ops, tool_call_state_ops
from agent.workflow.models import ArtifactRef, AttemptRecord, TaskRecord
```

Step 2 — facade `begin_stage_if_new`, inserted in the Attempt section immediately after `finish_attempt` (HEAD L91-103). Contract mirrors `idempotency_ops.begin_stage_if_new` exactly:
```python
    def begin_stage_if_new(
        self,
        event_id: str,
        task_id: str,
        stage_id: str,
        workflow_id: str | None = None,
        lease_duration_sec: int | None = None,
    ) -> AttemptRecord | None:
        """Start an attempt for the event if it has not been processed yet.

        Delegates to idempotency_ops.begin_stage_if_new with the store's own
        connection. Returns AttemptRecord if the stage should run, None if the
        event was already processed. begin_immediate handles the transaction;
        no explicit commit here.
        """
        return idempotency_ops.begin_stage_if_new(
            self._db,
            event_id,
            task_id,
            stage_id,
            workflow_id=workflow_id,
            lease_duration_sec=lease_duration_sec,
        )
```

Step 3 — new Artifact section (section comment matching the file's `# ── <Name> ──` style) before `# ── Diagnostic Queries ──` (HEAD L134):
```python
    # ── Artifact ─────────────────────────────────────────────────────────────

    def record_artifact(
        self,
        task_id: str,
        stage_id: str,
        uri: str,
        workflow_id: str | None = None,
        attempt_number: int | None = None,
    ) -> ArtifactRef:
        """Insert an artifact reference using the store's own connection.

        Delegates to artifact_ops.record_artifact; that function commits.
        """
        return artifact_ops.record_artifact(
            self._db,
            task_id,
            stage_id,
            uri,
            workflow_id=workflow_id,
            attempt_number=attempt_number,
        )
```

Step 4 — recovery signature. Replace the definition line (HEAD L189):
```python
    def recover_stale_attempts(self, db: SQLiteHelper) -> int:
```
with:
```python
    def recover_stale_attempts(self) -> int:
```
and make the first statement of the body:
```python
        db = self._db
```
Add one sentence to the docstring: the method always operates on the store's own connection; callers pass no arguments. Do not touch any other statement in the body (the compare-and-swap loop, commit gate `if stale: db.commit()`, and `last_recovery_report` bookkeeping stay byte-identical, REQ-004).

## Compatibility considerations
- External API break by design: every call site of `recover_stale_attempts` with an argument breaks at the same commit; procedure documents 02-06 retarget all known call sites, and the full-suite gate catches any site this census missed.
- `get_connection()` and its identity test (`test_workflow_state_store.py` L274-275) stay untouched.
- The new facade methods are additive; existing direct ops-module imports elsewhere (tests, sibling-procedure call sites) keep working.

## Security considerations
No new SQL, no new inputs, no transaction-semantics change. The change strengthens auditability: all workflow.sqlite writes from these paths now enumerate through `StateStore`.

## Rollback considerations
Revert this file plus documents 02-06 together (single release unit). The change is pure routing; no schema or data migration exists to unwind.

## Validation plan
Run after documents 01-08 of the unit have landed (the unit gate is evaluated on the whole unit):
| Gate | Command | Expectation |
|---|---|---|
| Recovery regression | `uv run pytest tests/agent/workflow/test_state_store.py tests/agent/workflow/test_workflow_state_store.py tests/agent/workflow/test_stale_recovery_lease.py -q` | all green |
| Delegation tests | `uv run pytest tests/agent/workflow/test_workflow_state_store.py -q -k facade` (procedures 01-05 test names) | green |
| Lint | `uv run ruff check scripts/agent/workflow/state_store.py` | clean |
| Type check | `uv run pyright scripts/agent/workflow/state_store.py` | clean |
| Docstrings | `uv run python tools/check_docstrings.py` | clean for the touched module |
| Module size | `uv run python tools/check_module_size.py` | state_store.py stays under its gate |

## Completion criteria
- `StateStore.begin_stage_if_new` and `StateStore.record_artifact` exist as one-call delegations with `AttemptRecord | None` / `ArtifactRef` return semantics (REQ-001).
- `recover_stale_attempts()` callable with no arguments; recovery counts identical for the same fixture database (REQ-002).
- No other statement in `recover_stale_attempts` differs from its post-siblings form (REQ-004).

## Out of Scope
- Engine/orchestrator call-site conversion (documents 02-03).
- Test call-site retargets and new routing tests (documents 04-08).
- Docs update (document 09).
- `get_connection()` deletion (`UNK-01`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend imports; add facade `begin_stage_if_new` and Artifact section `record_artifact` | Pending | — | — | |
| 2 | Re-signature `recover_stale_attempts` with `db = self._db` binding | Pending | — | — | |
| 3 | Run the unit validation gates (valid only after documents 01-08 land) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261107-203228_wfaudit015_state-store-facade-bypass.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084011_wfaudit015_state-store-facade-bypass.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-175155
- **Related target files**: `scripts/agent/workflow/state_store.py`

<!-- tools/generate_workitem.py implementation-procedure timestamp: 20261108-175155 -->
