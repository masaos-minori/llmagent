## Goal
Record the consumer audit of the four tools' output formats, then document the shared reporting module, the `--format` convention, and the JSON schema once in `tools/TOOL_DESCRIPTIONS.md` (`REQ-001`, `REQ-007`; Plan phases 1 and 5).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: an audit record section, a module row (Index and detail), and a `--format` convention and JSON schema subsection in this file.
- Out of scope: the other Plans' rows and sections, any tool change, follow-up batches for the other ten tools.

## Assumptions
- Execution order is split: the audit record (Plan step 1) MUST be written before any tool migration of this Plan starts; the module row, convention, and schema (Plan step 5) are written after the migration procedures land. The Execution Status below lists both parts. This document has `seq` 09 because the Plan's `Implementation Target Files` table is ordered by implementation, and this file's second part is last.
- Audit facts verified on 2026-11-06 (Step 3a): pre-commit runs `uv run python -m tools.check_adr_invariant_matrix`, `-m tools.check_adr_reference`, and `-m tools.check_workitem_traceability --active-only`; `.github/workflows/ci.yml` runs `uv run python tools/check_adr_authority.py`; no pre-commit hook, CI workflow, `tools/run_validation_gates.py`, `skills/`, `rules/`, `routing.md`, `prompts/`, or `docs/` passes `--format json` or `--format csv` to the four tools (`rg` found only the `generate_mcp_inventory` gate token comment in `run_validation_gates.py`); importers are tests and, for `check_adr_invariant_matrix.py`, a lazy import in `tools/generate_reference_table.py` (`ADR_INDEX`, `_matrix_rows`, `_read_lines`, `_split_row`); readers outside the repository cannot be searched (Plan UNK-01, non-blocking).
- Current key sets and orders to record: `file`, `line_no`, `severity`, `message` sorted by `(file, line_no)` (the two ADR matrix and reference checkers); `code`, `location`, `message` sorted by `(code, location, message)` (`check_adr_authority.py`); `category`, `file`, `detail` in finding order with sorted keys, plus CSV with that header (`check_workitem_traceability.py`).
- Needs confirmation (non-blocking): the archived `toolcli001` Plan would add a CLI and exit-code convention section, but its procedures were archived with every step `Pending`; do not cross-reference a convention section unless it exists when this runs.
- Overlap judgment: three open Plans target this file (`toolwrite001`, `toolsizegate001`, and this one; `toolcommon001` was archived with its procedures generated). This Plan adds an audit record, one module row, and a subsection; the others add atomic-write and size-gate content, so they are compatible, with this Plan landing first.

## Design decisions
- Name tools and fields instead of counting them; keep the schema as a short table of keys per tool plus the `--format` rules (choices a tool offers, default stays text).

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. (Plan step 1, before any migration) Add an audit subsection recording the readers per output format, the current key sets and sort orders above, and the finding that no repository caller requests JSON or CSV; state UNK-01 (external readers unknown).
2. (Plan step 5) Add the Index row for `_report.py` (`Shared base`) and a detail row marked "(shared base; cannot run standalone)" describing the record, profiles, renderers, and option helper.
3. (Plan step 5) Add the `--format` convention (a tool offers only formats it already supports, the default stays human-readable text) and the JSON schema table once.
4. Run the checks in the Validation plan.

### Method
- Keep table columns and sentence style of the neighboring rows; backtick every `*.py` name exactly (`tools/check_tool_descriptions_sync.py` cross-checks them).

### Details
- Write the audit as facts with their source, not as a decision; the owner handles any later JSON key change.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: no secrets, hosts, or ports are written.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — expected `No issues found.` once `tools/_report.py` exists and is documented.
- After the migration procedures: `uv run pytest tests/tools -q`, `uv run python tools/run_validation_gates.py`, and the live-data comparison of each tool recorded in its own procedure.

## Completion criteria
- The audit record names every reader of the four tools' outputs or states that none was found; the module row, convention, and schema appear once; the sync check passes.

## Out of Scope
- Follow-up batches, any behavior change, deploying (no deploy step: only `tools/` and `tests/` change).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the audit record (before any tool migration of this Plan) | Pending | — | — | |
| 2 | Write the module row, `--format` convention, and JSON schema (after the migrations land) | Pending | — | — | |
| 3 | Run `check_tool_descriptions_sync.py` and the final verification list | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (consumer audit), `REQ-007` (module, convention, schema documented once)
- **Source issue**: issues/20261104-152906_toolreport001_share-report-model-and-renderers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110046_toolreport001_share-report-model-and-renderers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-091630
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
