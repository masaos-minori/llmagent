## Goal

Make the consistency report's repair guidance name the renamed RAG vector command and the job commands, so guidance points at commands that exist and at the operation the command actually performs (REQ-007: name matches behavior).

## Scope
**Release unit**: R6-rag-vector-contract (Phase 6)

- In scope: the repair-guidance string in the consistency check.
- Out of scope: the checks themselves, the report structure.

## Assumptions

- The rename decision is `/session rag-prune-vec` (plan decision OD-01, 2026-11-24); the retired name is not an alias.

## Design decisions

- The guidance names the job command for the outcome view (`/jobs status <id>`) in addition to the repair command, because the operator needs the job record to see whether the run was verified.

## Alternatives considered

- Keeping the old name as an alias in the guidance — rejected: `tests/agent/commands/test_removed_commands.py` (row 50) requires the retired name to stay unregistered.

## Implementation
### Target file
`scripts/db/rag_consistency.py`

### Procedure
1. Change the guidance text at `scripts/db/rag_consistency.py:247` from `Run '/session rag-rebuild-vec' to remove the orphan rows.` to the renamed form.
2. Add the job-command reference to the same guidance sentence, without changing the check that produces it (`_ConsistencyCheck` at `:437`).

### Method

- No change to `orphan_vec_count` computation.

### Details

- The wording must match the operation: the command removes orphan `chunks_vec` rows; it does not rebuild the vector table from `chunks`.

### Companion test files
- `tests/db/test_rag_consistency.py`
  - Procedure: assert the repair guidance names the renamed command.
  - Validation: `uv run pytest tests/db/test_rag_consistency.py -q` (REQ-007; AC-8, AC-9).

## Compatibility considerations

- The doc-quality rule that sanctions the command name is updated in the same release unit (row 35); a half-applied rename fails `tools/check_docs_quality.py`.

## Security considerations

- N/A: guidance text only.

## Rollback considerations

- N/A: revert the Phase 6 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/db/rag_consistency.py` | Unit | `uv run pytest tests/db/test_rag_consistency.py -q` | Guidance names the chosen command |
| Same file | Quality gates | `uv run ruff check scripts/db/rag_consistency.py`, `uv run mypy scripts/db/rag_consistency.py` | No finding |

## Completion criteria

- The consistency report names only registered commands, and the vector guidance names the prune operation.

## Out of Scope

- The service method rename (row 22), the documents, the doc-quality rule.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the repair guidance string | Completed | 20261125-002740 | 20261125-002740 | Phase 6 Phase 6 (R6) done: the guidance names /session rag-prune-vec and adds the job-record reference (/jobs status <id>); repair_action is prune_orphan_vectors. The check itself is unchanged. |
| 2 | Update the companion test per Validation plan | Completed | 20261125-002740 | 20261125-002740 | Covered by this document Companion test: the guidance assertion, the three exact-message assertions, the _REPAIR_PHRASE mapping, and a new assertion that the vector finding names the service method and the job record. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-002740 | 20261125-002740 | Phase 6 part: ruff, ruff format, mypy pass; docs checkers clean; tests/db/test_rag_consistency.py 79 passed. |

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
- **Requirement ID**: REQ-007 (command name matches behavior)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/db/rag_consistency.py`, `tests/db/test_rag_consistency.py`