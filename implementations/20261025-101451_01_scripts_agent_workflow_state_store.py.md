# Procedure: `scripts/agent/workflow/state_store.py`

Stage-2 output for Issue 20261024-105743 / Plan 20261025-090841. Source plan: `plans/20261025-090841_workflow001_state-store-create-task-duplicates-the-composite-idempotency-key.md`. Frozen decisions are copied from the plan; this procedure does not re-decide any of them.

**Row:** 1 of 2, Type `Code`, Path `scripts/agent/workflow/state_store.py`, Action `Modify`, Size `S`, Depends on `tests/agent/workflow/test_workflow_state_store.py` (Phase 1 red test lands first, per the plan's Implementation steps)

## File Scope

- One method body (`StateStore.create_task`, `:48-93`) replaced by a delegation; one import line added.
- No other method, import, or line in the file changes. `task_ops.py`, `schema_sql.py`, `workflow_engine_adapter.py`, and the resume path are out of scope (plan Out-of-Scope; REQ-005 requires their diffs to be empty).

## Pre-Change State

Verified 2026-10-25 (Step 3a re-verification; all plan claims held):
- `state_store.py:48` `def create_task(self, session_id: str | None, turn_number: int | None, workflow_version: str, workflow_id: str) -> TaskRecord:` — synchronous, first docstring line `Create a new task record.` (`:55`).
- Composite branch `:56-59`: `if session_id is not None and turn_number is not None: idempotency_key = f"{session_id}:{turn_number}"` (`:57`) else `str(uuid.uuid4())`. Duplicated `INSERT INTO tasks` `:63-79` + `commit` `:80` + manual `TaskRecord(...)` return `:81-92`.
- `rg 'f"{session_id}' scripts/agent/workflow/` matches only `state_store.py:57` (re-run confirmed).
- `task_ops.py:13-19` module-level `create_task(db, session_id, turn_number, workflow_version, workflow_id) -> TaskRecord`; `:30` sets `idempotency_key = str(uuid.uuid4())` unconditionally; docstring `:20-29` states the key is never derived from caller fields. Body writes the same columns, same `TaskRecord` fields, same commit (diff-by-read confirmed).
- No callers of `store.create_task` exist: `rg -n '\.create_task\(' scripts tests` minus `loop.`/`asyncio.` hits returns nothing (exit 1, re-run confirmed).
- Imports `:12` `uuid` and `:15` `now_iso as _now` are also used at `:98` (`update_task_status`) and `:161` (`start_attempt`), so removing the body's usage leaves no unused import.
- `.importlinter` contains only `forbidden` cross-package contracts (`agent` → `mcp_servers.*` models etc.); no contract constrains `agent.workflow.state_store` → `agent.workflow.task_ops`. `task_ops` imports only `db.helper`, `shared.json_utils`, `agent.workflow.models` — no cycle.

## Frozen Decisions (from the plan, copied not re-decided)

| ID | Decision |
|---|---|
| REQ-001 | Body becomes `return create_task(self._db, session_id, turn_number, workflow_version, workflow_id)`; first docstring line unchanged |
| REQ-002 | Signature, return type (`TaskRecord`), and `__init__.py` export unchanged |
| REQ-003 | Repo-wide guard: `rg 'f"{session_id}' scripts/agent/workflow/` must return no match after the change |
| REQ-005 | `task_ops.py` and `schema_sql.py` diffs stay empty |
| REQ-006 | `PYTHONPATH=scripts uv run lint-imports` stays green |
| Design | Delegation over inline patch; import form `from agent.workflow.task_ops import create_task` added to the `agent.workflow` import block (`:17` area, alongside `from agent.workflow.models import ...`) |
| Design | Name resolution is safe: a method name is not in module scope, so the bare `create_task` call inside the method resolves to the imported function |

## Implementation Procedure

Order: this file is edited only **after** the Phase 1 red test from doc0002 is committed (plan Implementation steps Phase 1 → Phase 2).

1. Add import (after `:17` `from agent.workflow.models import AttemptRecord, TaskRecord`):
   ```python
   from agent.workflow.task_ops import create_task
   ```
2. Replace lines 56-93 (the `if session_id ...` branch through the `TaskRecord(...)` return) with:
   ```python
   return create_task(self._db, session_id, turn_number, workflow_version, workflow_id)
   ```
   Keep `def create_task(`, the parameter list (`:49-53`), the `-> TaskRecord` annotation, and the docstring line `Create a new task record.` byte-identical (reference-table guard, plan Risk 3).
3. Do not touch `uuid`/`_now` imports or any other method.

## Validation Commands

```bash
rg 'f"{session_id}' scripts/agent/workflow/                       # REQ-003/AC-1: exit 1, no match (after edit)
grep -n "INSERT" scripts/agent/workflow/state_store.py           # AC-1: no INSERT inside create_task (other methods keep theirs — out of scope)
uv run pytest tests/agent/workflow/test_workflow_state_store.py -q   # doc0002's test green after this edit
uv run ruff format scripts/ && uv run ruff check scripts/ && uv run mypy --no-namespace-packages scripts/ && uv run bandit -r scripts/ -c pyproject.toml -ll
PYTHONPATH=scripts uv run lint-imports                            # REQ-006
uv run vulture scripts/ --min-confidence 80                       # no unused-import finding for uuid/_now
uv run python tools/check_module_size.py                          # size gate (12174 B → shrinks, < 20480 B)
uv run radon cc scripts/agent/workflow/state_store.py -s -n C    # create_task drops from A(3) to A(1); no C+
uv run python tools/generate_reference_table.py --check           # docstring-first-line guard
git diff --stat -- scripts/agent/workflow/task_ops.py scripts/db/schema_sql.py   # REQ-005: empty
```

Mutation check (AC-3, paired with doc0002): in a scratch copy under /tmp/opencode, restore the composite branch and confirm the new wrapper test fails with `sqlite3.IntegrityError`; then discard the scratch copy.

## Risk & Impact

- Blast radius: `StateStore` is constructed by `orchestrator.py`, `session_persister.py`, `workflow_engine_adapter.py`; none calls `create_task` on it (verified). No signature change → zero caller-visible effect.
- Cycle risk: none — `task_ops` imports nothing from `state_store`; lint-imports is the hard gate.
- Reference-table coupling: `generate_reference_table.py --check` keys off the first docstring line; keeping it byte-identical is mandatory.
- Deploy coupling: `scripts/` change → deploy hand-off belongs to the plan's Phase 3 step (user approval gate), not to this document.

## Scope Decisions

- In: import line + method body replacement only. Out: other inline-SQL copies in `StateStore` (plan Out-of-Scope), wrapper deletion (needs its own decision), any docs edit (plan Documentation Impact: `N/A`).

## Definition of Done

- Red wrapper test (doc0002) turns green; guard grep exit 1; empty diffs on `task_ops.py`/`schema_sql.py`; lint-imports, ruff, mypy, bandit, vulture, size, radon, reference-table checks all green; mutation check performed once; `tests/agent/workflow` reports 92 passed.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `from agent.workflow.task_ops import create_task` and replace `create_task` body with the delegation, docstring byte-identical | Completed | 2026-10-25 | 2026-10-25 | landed after doc0002 Phase 1 red (plan order honored); ruff reformatted the delegation line wrap only |
| 2 | Run all Validation Commands and the mutation check | Completed | 2026-10-25 | 2026-10-25 | guard rg exit 1 (required `rg -F`: literal braces trip the regex engine); no INSERT left in create_task (only attempts at :131, out of scope); 92 passed; ruff/mypy/bandit(0 issues)/lint-imports(6 kept)/vulture(no uuid/_now hit)/size/radon(no C+)/reference-table(--check: no drift) all green; task_ops/schema_sql diffs empty; mutation check performed once: composite branch restored via `git checkout --` on the target path (fixed file saved at /tmp/opencode/state_store_fixed.py) -> wrapper test FAILED with IntegrityError -> restored -> passed; whole suite 10082 passed 9 skipped |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | None | — | — |

### Work Items Created
- None
