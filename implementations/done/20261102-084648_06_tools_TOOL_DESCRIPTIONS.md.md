## Goal
- Describe the extended `drift` behavior in both `run_validation_gates.py` entries (`REQ-005`: tool description matches behavior).

## Scope
- In scope: the two existing `run_validation_gates.py` rows (the Validation runner table and the input/behavior table). Out of scope: other tools' rows and the stale `--fast` / "stops on the first Fail" wording in those rows.

## Assumptions
- Step 3a: both rows end their description of `drift` with "fails when a `routing.md` checker has no mapping entry"; this is the text to extend.
- Step 3a observation (not changed here): the rows say `--fast`/`--full` and "stops non-zero on the first `Fail`", but the parser has `--full` only and `_run_gates` runs every selected gate; reported as a caveat, outside this Plan's scope.
- Overlap (Step 2, `tools/check_plan_target_overlaps.py`): `tools/TOOL_DESCRIPTIONS.md` is also targeted by the Plans filed from `flowimp001`, `flowimp003`, `flowimp008`, `flowimp010`, `flowimp011`, and `flowimp007`. Judged compatible: each adds its own row; this Plan updates the two existing `run_validation_gates.py` rows. Edits are row-additive, so whichever lands later rebases.

## Design decisions
- Edit only the `drift` clause in each row so concurrent row-additive edits by sibling Plans do not conflict.

## Alternatives considered
- N/A: documentation edit.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
- Replace the `drift` clause in both `run_validation_gates.py` rows with: `drift` subcommand fails when a `routing.md` checker has no mapping entry, or when a tool-backed `.pre-commit-config.yaml` hook has neither a gate mapping nor a reviewed allowlist entry (malformed or unreadable config also fails); it also runs as the `gates-hook-parity` pre-commit hook.

### Method
- Locate the two rows with `rg -n '^\| `run_validation_gates.py`' tools/TOOL_DESCRIPTIONS.md`. Keep each row on one line and keep the column count.

### Details
N/A: covered by Procedure and Method.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` passes.

## Completion criteria
- Both rows describe the hook comparison, the allowlist, and the hook, and the sync check passes (AC-5).

## Out of Scope
- Rows of other tools; correcting unrelated stale wording.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261102-092319 | 20261102-092319 | Edit two rows Changed: tools/TOOL_DESCRIPTIONS.md (both run_validation_gates.py rows). Docs N/A (tools overview row names TOOL_DESCRIPTIONS itself). Full suite deferred to plan end |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261102-092319 | 20261102-092319 | `check_tool_descriptions_sync.py` check_tool_descriptions_sync passed; drift OK |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261030-191302_flowimp005_gates-hook-parity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-075445_flowimp005_gates-hook-parity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-084648
- **Related target files**: tools/TOOL_DESCRIPTIONS.md