## Goal
- Register `classify_changes.py` in `tools/TOOL_DESCRIPTIONS.md` so `check_tool_descriptions_sync.py` passes (`REQ-005`: tool registered).

## Scope
- In scope: one row in the Index table and one row in the Work Items table (and a short note for the options if the file's style adds one). Out of scope: the stale `Index (61 modules)` count, other tools' rows, and the routing and gate rows.

## Assumptions
- Step 3a verification: the file has an `## Index (61 modules)` table (File, Category, Purpose; actual `tools/*.py` count is 69, so the heading count is already stale and no checker verifies it) and a `## Work Items` table (File, Target, Description) holding `check_plan_target_overlaps.py`, `manage_workitem_stage.py`, and `run_validation_gates.py`; `tools/check_tool_descriptions_sync.py` cross-checks the backticked `*.py` names against `tools/*.py`.
- Row 03 creates the tool first (`seq` order), so the sync check sees the file.
- Overlap (Step 2): `tools/TOOL_DESCRIPTIONS.md` is also a target of `flowimp008`, `flowimp011`, and (per Plan A6) `flowimp001`, `flowimp003`, `flowimp004`, `flowimp005`. Judged compatible (Plan A6, A6b): each adds its own row; inserting beside the neighbors is row-additive, and a merge conflict is resolved by keeping every row.
- The description text states: read-only; `--group`, `--verify-pathspec`, `--status-file`; exit codes 0, 1, 2 (shared contract in row 03).

## Design decisions
- Index category `Git helper` (the tool serves commits, not the issue/plan lifecycle).
- Add a Work Items row as well (the tool classifies workflow artifacts too), following the same two-place pattern as `run_validation_gates.py`.

## Alternatives considered
N/A: two-place registration is the existing pattern.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Index table: add a row (File `classify_changes.py`, Category `Git helper`, Purpose per Method) next to the other `check_*` rows, matching the file's ordering at edit time; do not change the `Index (61 modules)` heading count (out of scope, already stale).
2. Work Items table: add a row (File `classify_changes.py`, Target `git status --porcelain=v1 -z` output of the current repository, Description per Method).

### Method
- Purpose text (one line): `Read-only classifier for splitting one working tree into per-group commits: groups changed paths (artifacts, code, tests, tools, docs, other), prints pathspec lists with both names of every rename, marks untracked and unstaged paths, flags partly staged paths. Options --status-file, --group, --verify-pathspec; exit 1 on partly staged or unmerged paths.`

### Details
- Use the exact backticked file name `classify_changes.py` so the sync checker finds it; keep table pipes escaped where the cell contains `|` (none expected).

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py`: passes (`AC-6`); `uv run python tools/check_docs_quality.py` is not required (not under `docs/`).

## Completion criteria
- Both rows exist and the sync checker passes with the tool file present.

## Out of Scope
- Fixing the stale module count; rows for other tools; `routing.md`; the gate mapping.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `tools/TOOL_DESCRIPTIONS.md`: Index row and Work Items row (Implementation > Procedure) | Completed | 20261102-141521 | 2026-11-02 | Added Index and Work Items rows; files: tools/TOOL_DESCRIPTIONS.md; no correction |
| 2 | Run `check_tool_descriptions_sync.py` | Completed | 2026-11-02 | 2026-11-02 | check_tool_descriptions_sync: pass; full suite deferred to plan end (docs only) |

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
- **Requirement ID**: `REQ-005`; acceptance `AC-6`
- **Source issue**: issues/20261030-191702_flowimp010_artifact-commit-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-081312_flowimp010_artifact-commit-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085619
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
