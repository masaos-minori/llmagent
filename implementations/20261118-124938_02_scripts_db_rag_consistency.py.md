## Goal
Make every finding's prefix match its severity and its message and repair action name the same repair, which can fix the state (REQ-001, REQ-002).

## Scope
**Release unit**: rag-diagnostics
- The finding builders of `scripts/db/rag_consistency.py`; severities and check predicates are unchanged.
- Release unit: the failing-first tests stay red until procedure 02 lands, so the full suite and diff-cover run once at the end of the unit.

## Assumptions
- Gate: the owner confirms UNK-02 (the mapping and the new `reingest` repair action) of the Source plan before the first edit; stop and ask when it is not confirmed.
- Procedure 01 is done, so its tests are red for the reasons recorded there.
- `repair_action` is a plain `str` field of `ConsistencyFinding` and its only production consumer prints it in the startup message, so a new value needs no type change.

## Design decisions
- A prefix follows the severity (`[CRITICAL]` for FATAL, `[WARNING]` for DEGRADED); a severity is policy and stays.
- A repair action is chosen by what can fix the state: `rebuild_vec` now only removes orphan vector rows, so only the orphan-vector finding keeps it; findings that need ingestion to run again use `reingest`.

## Alternatives considered
Raising the three findings to FATAL was rejected: it changes which findings abort startup, a policy decision.

## Implementation
### Target file
`scripts/db/rag_consistency.py`
### Procedure
1. Gate: confirm UNK-02.
2. FTS orphan builder: `[CRITICAL]` becomes `[WARNING]`; the rest of the message and `rebuild_fts` stay.
3. Orphan vector builder: `[WARNING]`; replace the re-run-ingestion sentence with `Run '/session rag-rebuild-vec' to remove the orphan rows.`; `rebuild_vec` stays.
4. Vector mismatch builder: repair action `reingest` (new); the message keeps its `ingester.py --force` sentence.
5. Documents-without-chunks builder: repair action `reingest`; the sentence becomes `Re-run ingestion with 'ingester.py --force' for affected documents.`
6. Chunks-without-vector builder: `[WARNING]`; repair action `reingest`; the message keeps its sentence.
7. URL-level builder: repair action `reingest`; the sentence becomes `Re-run ingestion with 'ingester.py --force' for affected URLs.`
8. FATAL builders: the duplicate chunk index message ends with `Restore from a verified backup or re-ingest; duplicate chunk indices indicate data corruption.` and the FK, embedding dimension, and unknown schema messages each end with `Restore from a verified backup.`; `restore_from_backup` stays.
9. Run the tests of procedure 01 and fix only what they show.
### Method
Edit the f-strings of the builders in place; do not touch `_CHECKS`, the predicates, or the severities.
### Details
- After this change no builder uses `reconcile_url` as a repair action; the method still exists in the maintenance service.
- Keep the message wording short and in English; the startup message appends `Repair action: <value>`.

## Compatibility considerations
The set of `repair_action` strings changes (`reingest` is new; `reconcile_url` is no longer produced) and three prefixes change; the startup message prints the new strings. The guide table is updated by procedure 03.

## Security considerations
N/A: message and label changes only.

## Rollback considerations
Revert only this procedure's own changes with `git checkout -- <path>` on each changed path (single-path revert; no bulk form). Apply the procedure's Rollback considerations after a failed full-suite run.

## Validation plan
- `uv run pytest tests/db/test_rag_consistency.py tests/agent/test_startup.py tests/agent/test_startup_validation.py`
- `uv run ruff format <changed files>`, `uv run ruff check <changed files>`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`
- End of the release unit: `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`

## Completion criteria
- Every finding's prefix matches its severity and its message names the repair its action stands for (AC-1, AC-2).
- The tests of procedure 01 pass and diff-cover is at least 90% on the changed lines.

## Out of Scope
- Changing a severity, a check predicate, or the startup routing.
- Editing the maintenance service.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the owner decision UNK-02 | Pending | — | — | Stop and ask if not confirmed |
| 2 | Implement the changes in Implementation > Procedure | Pending | — | — |  |
| 3 | Run the tests of procedure 01 and the startup tests | Pending | — | — |  |
| 4 | Run the validation sequence (`rules/toolchain.md`) and the end-of-unit full suite | Pending | — | — | Stays In Progress until the end-of-unit run passes |

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
- **Requirement ID**: `REQ-001`, `REQ-002`: prefix matches severity; message and repair action agree
- **Source issue**: issues/20261117-123006_adrchk006_rag-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-124317_adrchk006_rag-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-124938
- **Related target files**: `scripts/db/rag_consistency.py`
