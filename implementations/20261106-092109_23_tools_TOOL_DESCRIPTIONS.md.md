## Goal
Document the `--dry-run` convention and the shared atomic-write helper in `tools/TOOL_DESCRIPTIONS.md` and run the Plan's final verification (`REQ-008`; Plan phase 5).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one Index row, one shared-base detail row, and a `--dry-run` convention note.
- Out of scope: the other Plans' rows and sections, changing any tool.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the Index lists private modules with category `Shared base`, a detail row `(shared base; cannot run standalone)` exists for existing private modules, and no `--dry-run` convention text exists.
- Facts for the note: the writers that gain `--dry-run` are `module_nodes.py` (`extract`), `set_execution_status.py`, `fix_docs_section_marks.py` (explicit flag for its existing default preview), `fix_procedure_new_markers.py`, `migrate_runtime_tool_calls.py`, and `generate_workitem.py`; the seven atomic-only writers are `manage_workitem_stage.py`, `manage_frontmatter.py`, `rename_doc.py`, `close_procedures_batch.py`, `fix_docstring_paths.py`, `fix_docstring_blank_line.py`, and `mark_procedure_new_symbols.py`; the dry-run output is a unified diff and writes nothing.
- Needs confirmation (non-blocking): the archived `toolcli001` Plan would add a CLI convention section; do not cross-reference it unless it exists when this runs.
- Overlap judgment: the open `toolsizegate001` Plan also targets this file (size-gate rows, a different section), compatible; this Plan lands first.

## Design decisions
- Name the tools instead of counting them; one short subsection for the convention.

## Alternatives considered
N/A: documentation-only row.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Add the Index row for `_atomic_write.py` (`Shared base`) and a detail row `(shared base; cannot run standalone)` listing the staged write, atomic write, diff preview, and option helper.
2. Add a `--dry-run` convention note: the flag prints a unified diff, writes nothing, returns the real run's exit code; list the tools above.
3. Run the checks in the Validation plan.

### Method
- Keep column order and sentence style of neighboring rows; backtick every `*.py` name exactly (`check_tool_descriptions_sync.py` cross-checks them).

### Details
- Write facts only; the behavior of each tool is in its own procedure.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no secrets, hosts, or ports are written.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — expected `No issues found.` once `tools/_atomic_write.py` exists and is documented.
- Final verification after all procedures of this Plan: `uv run pytest tests/tools -q`; `uv run python tools/run_validation_gates.py`; `rg -n "write_text"` over the thirteen migrated tools (no call on a repository file remains); the live-data comparison recorded per procedure.
- No deploy step: only `tools/` and `tests/` change.

## Completion criteria
- The helper row and the `--dry-run` convention appear once; the sync check passes; the final verification list has been run and recorded.

## Out of Scope
- Changing any tool, deploying.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the Index row, the detail row, and the convention note | Pending | — | — | |
| 2 | Run `check_tool_descriptions_sync.py` | Pending | — | — | |
| 3 | Run the Plan's final verification list (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: `REQ-008` (document the convention and helper)
- **Source issue**: issues/20261104-152906_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110212_toolwrite001_make-mutating-tools-dry-run-and-atomic.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092109
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
