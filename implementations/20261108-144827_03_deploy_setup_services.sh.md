## Goal
Extend the second hardcoded `REQUIRED_WORKFLOW_TABLES` list in `deploy/setup_services.sh` to
include `tool_call_state`, keeping both deploy pre-flights identical to the Python gate list
(`REQ-002`), and extend the test fixture that seeds the workflow DB for the script's integration
test.

## Scope
**Release unit**: wfaudit003-full (Phase 1)

- Covers Plan `plans/20261108-084006_wfaudit003_schema-gate-table-gap.md` row 6 (amendment
  2026-11-08): `deploy/setup_services.sh` (L55), plus `tests/deploy/test_setup_services_eventbus.py`.
- This mirror was discovered during the procedure pass: the same list string exists in
  `deploy/init_db.sh` (procedure `144827_02`) and in this script.

## Assumptions
- Procedures `144827_01` (Python gate) and `144827_02` (init_db.sh mirror + parity test) land in
  the same unit; the parity test owned by `144827_02` also pins this script's constant.
- `tests/deploy/test_setup_services_eventbus.py` runs the real `setup_services.sh` against a
  sandbox root; its `_seed_workflow_db` fixture must satisfy the extended gate or the test's
  happy-path case aborts with the `[FATAL]` missing-table exit.

## Design decisions
- Change only the constant line, same as `144827_02`: the script's presence loop (L57-63) and
  messages stay untouched; column-level enforcement remains in the Python gate (procedure 01).
- Fixture DDL stays minimal (`CREATE TABLE tool_call_state (idempotency_key TEXT PRIMARY KEY);`)
  matching the existing one-column-per-table seed style of `_seed_workflow_db` — the script's gate
  checks table presence only, not columns.

## Alternatives considered
- Replacing the shell loop with a Python `check_workflow_schema()` call (single source): rejected
  for the same reason as in procedure 02 — it couples the pre-flight to the venv and rewrites the
  script's established shape.
- Deleting the duplicate loop from `setup_services.sh` and delegating to `init_db.sh`: rejected —
  the two scripts run in different deploy phases and must each gate independently.

## Implementation
### Target file
`deploy/setup_services.sh` — `REQUIRED_WORKFLOW_TABLES` assignment (L55).

### Procedure
Append `tool_call_state` to the space-separated list. No loop or message changes.

### Method
Change L55 from:

```bash
REQUIRED_WORKFLOW_TABLES="tasks attempts processed_events artifacts"
```

to:

```bash
REQUIRED_WORKFLOW_TABLES="tasks attempts processed_events artifacts tool_call_state"
```

### Details
- The loop (L57-63) and `[FATAL] Workflow database schema is missing or incomplete.` block then
  cover `tool_call_state`; the file-existence guard above (L48-52) is untouched.
- Test fixture update in `tests/deploy/test_setup_services_eventbus.py`: add one
  `CREATE TABLE tool_call_state (idempotency_key TEXT PRIMARY KEY);` line to the
  `executescript` block inside `_seed_workflow_db` (L120-131).

## Compatibility considerations
- Current production workflow databases already carry `tool_call_state`; the extended pre-flight
  passes them unchanged (plan `UNK-01` probe gates rollout).
- The script stays read-only against the DB (SELECT-only queries).

## Security considerations
- No new attack surface; identical query shape to existing entries.

## Rollback considerations
- Revert L55 and the fixture line together with procedures 01/02; partial revert trips the parity
  test from `144827_02` by design.

## Validation plan
- Update `tests/deploy/test_setup_services_eventbus.py` `_seed_workflow_db` (fixture seeding, not a
  new test case): add the `tool_call_state` CREATE line so the happy-path case keeps passing.
- Confirm both failure-mode cases in that file (missing DB, malformed eventbus) remain green.
- Targeted: `uv run pytest tests/deploy/test_setup_services_eventbus.py tests/deploy/test_required_workflow_tables_parity.py -q`
  (parity file from `144827_02`); full `uv run pytest tests/ -q` and shell lint per
  `rules/toolchain.md`.

## Completion criteria
- `deploy/setup_services.sh` list equals the Python `REQUIRED_WORKFLOW_TABLES` keys (five entries).
- `test_setup_services_eventbus.py` green with the extended fixture; parity test green.

## Out of Scope
- `deploy/init_db.sh` and the parity test file (procedure `144827_02`).
- Docs describing this pre-flight (procedure `144827_07` covers the deployment doc rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Fixture extension in test_setup_services_eventbus.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs are covered by procedures 04-07 |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261107-203216_wfaudit003_schema-gate-table-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084006_wfaudit003_schema-gate-table-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-144827
- **Related target files**: `deploy/setup_services.sh`, `tests/deploy/test_setup_services_eventbus.py`
