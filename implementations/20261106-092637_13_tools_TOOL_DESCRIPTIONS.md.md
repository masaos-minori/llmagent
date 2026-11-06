## Goal
Update the gate scope text for `check_module_size.py` and add rows for the three new private modules (`REQ-004`, `REQ-005`, `REQ-006`; Plan phases 1-3).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the two `check_module_size.py` descriptions (Index and "Module Size Gate") and three Index rows.
- Out of scope: the other Plans' rows and sections.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the Index row and the "Module Size Gate" section describe `scripts/` only and name `tools/check_module_size_baseline.txt`.
- Sequencing: this Plan lands last among the `tools/` Plans; the procedures of `toolcommon001` and `toolwrite001` (archived with their procedures generated) are expected to have executed first, because they edit `run_validation_gates.py` and `manage_workitem_stage.py` before this Plan moves code from them.
- Execution is split: the gate scope text belongs to phase 1 (with the hook, CI, and gate), the `_workitem_status_table.py` and `_workitem_stage_parser.py` rows to phase 2, and the `_validation_gate_defs.py` row to phase 3.
- Needs confirmation (non-blocking): the archived `toolcli001` Plan's convention section may not exist; do not cross-reference it.
- Overlap judgment: earlier Plans add other rows and sections in this file; this Plan edits the module-size lines and adds three rows, so they are compatible; this Plan lands last.

## Design decisions
- Describe both invocations and both baselines in the gate text; name the three private modules and their one-line responsibility; no counts.

## Alternatives considered
N/A: single-purpose edit.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. (Phase 1) Update the two `check_module_size.py` descriptions to cover `scripts/` and `tools/` with separate baselines (`check_module_size_baseline.txt`, `check_module_size_tools_baseline.txt`) and the second invocation.
2. (Phase 2) Add Index rows for `_workitem_status_table.py` and `_workitem_stage_parser.py` (`Shared base`).
3. (Phase 3) Add the Index row for `_validation_gate_defs.py` (`Shared base`).

### Method
- Backtick every `*.py` name exactly; keep the table order (private modules first, alphabetical).

### Details
- Facts only; the behavior is in the tool procedures.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no secrets, hosts, or ports are written.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — expected `No issues found.` once the three modules exist and are documented.
- Final verification after all procedures: `uv run python tools/check_skills_references.py`, both module-size invocations, `uv run python tools/run_validation_gates.py`, and the per-file checks of `routing.md` "Adding a new tool" on every changed Python file.
- No deploy step: only `tools/`, `tests/`, CI, and documentation change.

## Completion criteria
- The gate text covers both scopes and baselines, three rows exist, the sync check passes, and the final verification list has been run and recorded.

## Out of Scope
- Other rows and sections, deploying.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: update the gate scope text | Pending | — | — | |
| 2 | Phase 2: add the two manage_workitem_stage module rows | Pending | — | — | |
| 3 | Phase 3: add the gate definitions row | Pending | — | — | |
| 4 | Run `check_tool_descriptions_sync.py` and the final verification list | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (gate scope text), `REQ-005`, `REQ-006` (new modules documented)
- **Source issue**: issues/20261104-152002_toolsizegate001_apply-size-gate-to-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110406_toolsizegate001_apply-size-gate-to-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092637
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
