## Goal

Document the write gate in the db architecture reference: the db layer gains a refusal state that every write entry point consults, and the architecture document must state what a refused write means for callers (REQ-004: writes stop when shutdown starts).

## Scope
**Release unit**: R7-reporting-and-docs (Phase 7)

- In scope: section 4 of this document and its Keywords list.
- Out of scope: the gate module (row 2), the write-path checks (row 3), and the package export (row 4).

## Assumptions

- Section 4 (`docs/41_db/db_01_architecture_and_schema-overview-and-config.md:48-52`) describes `SQLiteHelper` connection lifecycle and the `open(write_mode=True)` behavior, `### 4b` (`:58-64`) lists the additional `open()` options and the connect-failure contract, and `### 4c` (`:66-68`) describes `begin_immediate()` / `begin_exclusive()`.
- The gate is created by the agent layer and consulted by the helper (Plan Design, and the import-linter contract verified in the Plan's Step 5), so `db` describes the gate as an input it honors, not as a component it owns.
- The refusal is an exception at the write entry point, not a silent no-op: a caller that does not handle it fails the same way any other write failure fails.

## Design decisions

- Add one subsection `### 4d. Write gate` rather than editing each existing bullet: the gate is a new cross-cutting property of the write paths, and scattering it across 4, 4b and 4c would make it invisible as a contract.
- State the three states and the authorized context as behavior, and leave the type names to the generated reference (row 54), so this document stays at the architecture level the content policy requires.
- State explicitly that reads are unaffected in every state, because that is the property that lets the checkpoint and snapshot steps keep working after the gate closes.
- Compatibility impact: documentation only.

## Alternatives considered

- Document the gate only in the generated API reference — rejected: the generated table lists symbols, not the rule that every write entry point consults the gate, which is the claim a db-layer contributor needs.

## Implementation
### Target file
`docs/41_db/db_01_architecture_and_schema-overview-and-config.md`

### Procedure
1. Add `### 4d. Write gate` after `### 4c` (`docs/41_db/db_01_architecture_and_schema-overview-and-config.md:66-68`) stating: the gate has an open, closing, and closed state; a write attempted in `closing` without authorization, or in `closed`, raises `WriteGateClosed` (new) and is counted as a refused write.
2. State that the shutdown-owned writes run inside the authorized context the gate provides, that the authorization does not outlive the block, and that reads succeed in every state.
3. Add one sentence to section 4 (`docs/41_db/db_01_architecture_and_schema-overview-and-config.md:48-52`) and one to `### 4c` naming `open(write_mode=True)`, `execute`, `commit`, and the transaction helpers as guarded write entry points.
4. Add `write-gate` to the Keywords list (`docs/41_db/db_01_architecture_and_schema-overview-and-config.md:72-78`).

### Method

- One new subsection plus two cross-referencing sentences; the existing bullets keep their meaning.

### Details

- The refusal count is reported by the shutdown report (row 5); this document states only that refusals are counted, not where the count is printed.

## Compatibility considerations

- Runs after rows 2, 3 and 4: the gate it describes must exist before the document claims it guards the write paths.
- `docs/00_index.md` maps db-layer claims to this file; the generated subpackage reference (row 54) carries the symbol list.

## Security considerations

- N/A: no path or credential is documented; the refusal exception carries no path (REQ-013).

## Rollback considerations

- Revert this row's commit with the Phase 7 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Docs | `uv run python tools/check_docs_quality.py` | No finding |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Docs | `uv run python tools/check_docs_structure.py docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | No finding |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Docs | `uv run python tools/check_docs_content_policy.py` | No warning for the new subsection |
| `docs/41_db/db_01_architecture_and_schema-overview-and-config.md` | Consistency | `uv run python tools/check_docs_consistency.py --domain db` | Documented db behavior matches `scripts/` |

## Completion criteria

- The document states the gate states, the refusal exception, the authorized context, and that reads are unaffected, and the consistency checker reports no mismatch.

## Out of Scope

- The gate implementation and exports, the shutdown sequence, and the generated API tables (rows 53-55).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the write-gate subsection and cross-references | Pending | — | — | Phase 7 |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (writes stop when shutdown starts)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`
