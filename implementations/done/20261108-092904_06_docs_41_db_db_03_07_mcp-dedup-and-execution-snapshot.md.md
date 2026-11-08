# Implementation procedure: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` — retitle the snapshot section to retirement status

## Goal
Update the execution-snapshot tables section so it states the retirement of `execution_snapshots` and the `tool_call_state.snapshot_id` FK, with a pointer to the decision (`REQ-004`).

## Scope
**Release unit**: wfaudit010-full

- Intro sentence (L28), section heading and column listing (L73-88), timestamps line (L96), retirement pointer paragraph.

## Assumptions
- The doc edit lands after the code retirement (Plan Phase 3 order).
- The Replay Decision Table's `snapshot` vocabulary (L116-117) belongs to the separate `mcp_dedup.sqlite` dispatcher store and is NOT touched by this retirement (verified: `scripts/mcp_servers/dispatch.py` semantics, unrelated to the workflow table).

## Design decisions
- Keep the section (retitled) rather than delete it: the page is the canonical operational reference for both durable stores, and the retirement rationale + legacy-database behavior is the information a reader needs (Plan Documentation Impact: "retitle ... with a pointer to this decision").

## Alternatives considered
- Delete the whole execution-snapshot section: rejected — legacy databases still carry the artifacts and the mcp_dedup store's replay semantics stay live; deletion would orphan the cross-links from `docs/23_agent/agent_04_03` (its link sentence points here).

## Implementation
### Target file
`docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`

### Procedure
1. Intro (L26-28): change "the `tool_call_state` / `execution_snapshots` tables inside `workflow.sqlite`" to name `tool_call_state` and mark `execution_snapshots` as retired (see section).
2. Section heading (L73): retitle to "`tool_call_state` (workflow.sqlite); `execution_snapshots` retired".
3. Column listing: delete the `execution_snapshots` bullet (L82-83); delete the "`snapshot_id` (TEXT, FK to `execution_snapshots.snapshot_id`)" fragment from the `tool_call_state` bullet (L86).
4. Add a short retirement paragraph at the top of the section: the table and FK were never written by any code path; retired by wfaudit010 (`plans/done/20261108-084001_wfaudit010_snapshots-never-written.md`); fresh databases no longer create them; legacy databases may still contain the empty table and NULL column, and no migration drops them.
5. Timestamps note (L96-97): drop `recorded_at` from "`created_at`/`updated_at`/`recorded_at` are REAL epoch seconds" — it was the retired table's column.

### Method
- In-place edits; the historical note about the removed per-database migration step (L75-78), the index line, operational notes, and the Replay Decision Table stay verbatim.

### Details
- Current claims (verified at HEAD `367e583d2`): the section presents both tables as created at database creation and lists both column sets; the frontmatter keyword list (L10 `execution-snapshots`, L154 `execution_snapshots`) is kept — keywords aid discovery of the retirement statement and assert no behavior.

## Compatibility considerations
- N/A: docs-only; the sibling doc `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` (sibling procedure seq 05) is updated in the same batch so cross-links stay consistent.

## Security considerations
- N/A: docs-only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| edited doc | structure/quality gates | `uv run python tools/check_docs_structure.py docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain db` | No findings |

## Completion criteria
- The doc no longer describes `execution_snapshots` as created-and-written, states the retirement with the plan pointer, and its `tool_call_state` column listing matches the post-retirement DDL (`Acceptance Criteria REQ-004`); docs checkers pass.

## Out of Scope
- The Replay Decision Table and all `mcp_dedup.sqlite` dispatcher semantics (separate store).
- The `docs/23_agent/agent_04_03` edits (sibling procedure seq 05).

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
- **Requirement ID**: `REQ-004` (retirement stated in the canonical operational doc)
- **Source issue**: `issues/20261107-203223_wfaudit010_snapshots-never-written.md`
- **Source requirement**: N/A: the issue is the requirement source
- **Source plan**: `plans/20261108-084001_wfaudit010_snapshots-never-written.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-092904
- **Related target files**: `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`
