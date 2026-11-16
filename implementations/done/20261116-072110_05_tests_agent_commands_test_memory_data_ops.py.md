## Goal
- Verify that `tests/agent/commands/test_memory_data_ops.py` prune-event tests do not depend on `maintenance.prune_old_memories` calling `collect_prunable_ids` (removed by REQ-005); edit only if the regression run proves a dependence (row: "Verify, edit only if needed").

## Scope
**Release unit**: N/A: not part of a release unit (verify-only row; maps to no plan phase step — plan Phase 3 runs this file as the UNK-01 regression confirmation).

- In scope: regression run of this file after `_01`/`_03` land; conditional adjustment of patch targets.
- Out of scope: everything else in `tests/agent/commands/`; the production `memory_data_ops.py` itself (no change planned — its own `collect_prunable_ids` call at `memory_data_ops.py:372-374` is the dry-run/confirm count and stays).

## Assumptions
- UNK-01 resolved statically (re-verified 2026-11-16 against HEAD `206e36a3f`; originally `8fc337615`): the prune-event tests — `TestMemoryPruneEvents`, `:369-424` — patch `db.store_impl.SQLiteMemoryDeleteStore.collect_prunable_ids` (`:386-389`, `:418-421`), which the agent `memory_prune` path itself calls (`memory_data_ops.py:374`, passing `days`) — independent of the removed `maintenance.py:400` call. Expected outcome: green as-is, no edit.
- The `data["pruned_ids"]` shape consumed at `memory_data_ops.py:402-403` stays `list[str]` (procedure `20261116-072110_01` step 5), so the event-emission assertions are unaffected.

## Design decisions
- Keep this as a standalone verify-only procedure instead of folding it into the tests procedure: the plan's frozen target table has it as its own row with a distinct change responsibility ("Verify, edit only if needed"), and its run command differs (`tests/agent/commands`, not `tests/db`).

## Alternatives considered
- No document at all (run it inside procedure `_04` step 2): rejected — the frozen target-file table requires one procedure per row, and traceability (`check_workitem_traceability.py --plan-coverage`) must find a work item for every row.

## Implementation
### Target file
`tests/agent/commands/test_memory_data_ops.py`

### Procedure
1. After `_01` (step 5) and `_03` land, run `uv run pytest tests/agent/commands -v`.
2. Expected: green with no edits (UNK-01 static resolution). Only if a prune-event test fails due to `maintenance` no longer calling `collect_prunable_ids`, adjust the patch targets at `:386-389`/`:418-421` to match the landed call graph — no other edit is authorized by this row.

### Method
- No edit anticipated; the "procedure" is a gated regression run recorded against this row.

### Details
- Do not pre-emptively change patch targets: the static check says the dependence does not exist, and speculative edits would break the agent-path coverage of `memory_data_ops.py:373`.

## Compatibility considerations
- If step 2 ever fires, the change is confined to patch-target strings; assertions on emitted delete events and their id lists stay semantically identical.

## Security considerations
- Test-only; no change expected.

## Rollback considerations
- No change expected; if an edit was needed, `git checkout` revert of the unit commit restores the file.

## Validation plan
- `uv run pytest tests/agent/commands -v` → green as-is (expected outcome per plan Validation plan row "Regression run for UNK-01").
- Covered by the full-suite run in procedure `_01`/`_04` validation (`uv run pytest tests/ -n auto`).

## Completion criteria
- `uv run pytest tests/agent/commands -v` is green against the landed REQ-005 shape, with either zero edits (expected) or a minimal patch-target adjustment plus a note in this document's Execution Status explaining it.

## Out of Scope
- `scripts/agent/commands/memory_data_ops.py` production code (not a plan target).
- All other tests under `tests/agent/commands/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regression run after `_01` step 5 and `_03` land; edit only on failure (plan Phase 3 UNK-01 check) | Completed | 2026-11-16 | 2026-11-16 | UNK-01 resolved statically; no edit expected regression green with zero edits; 5 prune-event tests passed incl. TestMemoryPruneRealLoader; UNK-01 confirmed dynamically; full-suite waived per user instruction, covered by scoped tests/db+tests/agent/commands run (878 passed) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | N/A | — | — | no edit expected; covered by full-suite run |

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
- **Requirement ID**: REQ-005 (regression verification of the `pruned_ids` consumer tests)
- **Source issue**: issues/20261114-092854_dbreview006_maintenance-error-semantics.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-050112_dbreview006_maintenance-error-semantics.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-072110
- **Related target files**: tests/agent/commands/test_memory_data_ops.py