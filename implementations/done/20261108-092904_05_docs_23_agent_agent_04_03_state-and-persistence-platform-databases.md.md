# Implementation procedure: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` — state `execution_snapshots` retirement

## Goal
Remove the stale claims that `execution_snapshots` is written by the tool-call lifecycle, and record the retirement decision in the workflow lifecycle table section (`REQ-004`).

## Scope
**Release unit**: wfaudit010-full

- Two prose edits: the `StateStore` responsibility sentence (L72) and the Workflow Lifecycle Tables map (L79 row).

## Assumptions
- The doc edit lands after the code retirement (Plan Phase 3 order) so the doc describes implemented behavior.

## Design decisions
- State the retirement in one sentence rather than deleting every trace: readers of old databases need to know why the table/column may exist locally while fresh databases never create it (DESIGN Docs content policy: state boundaries and failure behavior, not history prose).

## Alternatives considered
- N/A: docs-only edit.

## Implementation
### Target file
`docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

### Procedure
1. In the `StateStore` paragraph (L72), change "the tool-call lifecycle (the `tool_call_state` / `execution_snapshots` tables, written through `agent/workflow/tool_call_state_ops.py`)" to name only the `tool_call_state` table.
2. In the "Workflow Lifecycle Tables (toolexec001)" table, delete the `execution_snapshots` row (L79: "Deployment fingerprints ... recorded at call time ... replay equality").
3. Add one sentence after the table: `execution_snapshots` is retired (wfaudit010) — it was never written by any code path, fresh databases no longer create it or the `tool_call_state.snapshot_id` FK, and legacy databases may still carry the empty table and NULL column with no effect.

### Method
- Sentence-level edits; the `tool_call_state` row and the idempotency-key prose around L72 stay verbatim.

### Details
- Current claims (verified at HEAD `367e583d2`): L72 "written through `agent/workflow/tool_call_state_ops.py`" and the L79 "recorded at call time" row are both false — no code inserts a snapshot row (issue `## Adversarial Validation`).
- The paragraph after the table cites the "migration path (`workflow.sqlite` ledger `1 -> 2`)" in its link sentence; the migration framework itself was removed earlier (compatrm001) and re-checking that claim belongs to a separate docs task, not this retirement edit (Out of Scope).

## Compatibility considerations
- N/A: docs-only.

## Security considerations
- N/A: docs-only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| edited doc | structure/quality gates | `uv run python tools/check_docs_structure.py docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain agent` | No findings |

## Completion criteria
- The doc no longer describes `execution_snapshots` as written, and states the retirement once (`Acceptance Criteria REQ-004`); docs checkers pass.

## Out of Scope
- The ledger `1 -> 2` migration-path claim in the link sentence (separate docs task; Plan Reference Files confirmed `db_02` and deployment docs carry no `execution_snapshots` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the edits described in Implementation > Procedure/Method/Details | Completed | 20261108-120435 | 20261108-120435 | Land after the code retirement (Plan Phase 3 order) |
| 2 | Run the docs checkers named in the Validation plan | Completed | 20261108-120435 | 20261108-120435 | ruff/format/mypy/lint-imports/bandit pass; full suite with coverage 11829 passed, 3 failed: 1 environmental (mdq allowed_dir_invalid, unrelated) and 2 fixed afterwards (citation count pinned to 55 after the adrver001 index edit; execution_snapshots inventory entry removed from tools/check_db_separation.py as fallout, plan archived so amend_plan refused); both re-run green; diff-cover N/A (deletions only); new tests fail pre-change |

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
- **Requirement ID**: `REQ-004` (retirement stated; stale claims removed)
- **Source issue**: `issues/20261107-203223_wfaudit010_snapshots-never-written.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084001_wfaudit010_snapshots-never-written.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-092904
- **Related target files**: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`
