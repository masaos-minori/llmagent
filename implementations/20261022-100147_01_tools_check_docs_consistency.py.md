## Goal
Register the `eventbus`, `shared`, and `db` domains in the docs consistency checker so that `--domain <name>` runs the existing generic checks against their docs folders (REQ-001: register the three domains; REQ-002: Warning-only, exit 0 on the live corpus).

## Scope
- Add three keys to the three domain tables, update the module usage docstring and the `--domain` help text.
- No new check, no new `elif` branch in `main()`, no behavior change for the five existing domains.

## Assumptions
- `main()` already runs the five generic checks (links, removed files, command drift, file refs, function refs) for any domain and branches by domain only for domain-specific checks, so new domains need table entries only (verified in `main()`: the generic block precedes the `if args.domain == ...` chain).
- `report_and_exit` returns 1 only for ERROR findings; the dry measurement on live docs showed 0 errors and 4 warnings across the three folders.
- `DOMAIN_GENERIC_CHECKS` is not read by `main()`; entries are added only to keep the tables consistent.

## Design decisions
- Keep the registration data-only: the `choices` list is derived from `DOMAIN_PREFIXES` keys, so adding keys there is what makes the CLI accept the new values.
- Use the same generic check set as `mcp` and `rag` for `DOMAIN_GENERIC_CHECKS`, matching what `main()` actually runs.

## Alternatives considered
- Adding a new `elif` branch per domain: rejected, there is no domain-specific check to run and `main()` complexity is already grade D.
- A single `docs` domain covering all folders: rejected, it changes how the existing CI workflows scope their runs (out of scope).

## Implementation
### Target file
`tools/check_docs_consistency.py`

### Procedure
1. Add `"eventbus": "eventbus_"`, `"shared": "shared_"`, `"db": "db_"` to `DOMAIN_PREFIXES` (only the keys are used by the CLI).
2. Add `"eventbus": "24_eventbus"`, `"shared": "40_shared"`, `"db": "41_db"` to `DOMAIN_SUBFOLDERS`.
3. Add the three keys to `DOMAIN_GENERIC_CHECKS` with `frozenset({"links", "removedfiles", "commanddrift", "filerefs", "funcrefs"})`.
4. Add three usage lines to the module docstring and extend the `--domain` help text with the new names.

### Method
- Edit only the dictionary literals, the docstring, and the help string; leave `main()` logic, `ALL_SKIP_OPTIONS`, and the entry-point wrappers untouched.
- Keep line length at 88 and the existing alignment style of the docstring usage block.

### Details
- After the edit, `uv run python tools/check_docs_consistency.py --domain eventbus` (and `shared`, `db`) must exit 0 and report only Warnings; expected live findings: one `funcrefs` warning each for `to_thread()` (eventbus), `isinstance()` (shared), and two for `_insert_chunk()` and `copy2()` (db).
- Triage (REQ-006): the stdlib names are accepted best-effort false positives; the `_insert_chunk()` reference in `docs/41_db/db_05_api_and_operations-protocol-and-backend.md` has no matching `def` under `scripts/` (the live method is `_insert_chunks_batch`), so file a follow-up issue instead of editing docs in this change.

## Compatibility considerations
The five existing domains are unchanged; the only CLI change is three additional accepted values. CI workflows call the existing five domains and are not edited.

## Security considerations
N/A: read-only docs checker, no secrets or external I/O.

## Rollback considerations
Revert the commit; no data or configuration state is involved.

## Validation plan
- `uv run ruff format tools/check_docs_consistency.py`, `uv run ruff check tools/check_docs_consistency.py`, `uv run mypy tools/check_docs_consistency.py`, `uv run bandit tools/check_docs_consistency.py`.
- `uv run python tools/check_docs_consistency.py --domain eventbus|shared|db` (exit 0, Warning only) and each existing domain (output unchanged).
- `uv run pytest tests/tools/test_check_docs_consistency_checks.py tests/tools/test_check_agent_docs_consistency.py tests/tools/test_check_docs_consistency_port.py -q`.

## Completion criteria
- The three domains are accepted by `--domain` and map to their docs folders.
- Exit code is 0 for the three new domains on live docs and the existing domains produce the same output as before.
- The four measured findings are classified and the follow-up issue for `_insert_chunk()` is filed or the doc fixed.

## Out of Scope
- Domain-specific drift checks, per-domain CI workflows, fixing every finding, editing any docs content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the domain keys and update docstring/help in `tools/check_docs_consistency.py` | Pending | — | — | |
| 2 | Tests are covered by the procedure for `tests/tools/test_check_docs_consistency_checks.py` | Pending | — | — | |
| 3 | Run the tool validation sequence and live domain runs | Pending | — | — | |
| 4 | Triage findings (REQ-006); docs updates are handled by the docs procedures of this Plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (register the three domains), `REQ-002` (Warning-only, exit 0), `REQ-006` (triage the measured findings)
- **Source issue**: `issues/20261021-101756_domaincov_decide-consistency-check-coverage-for-the-eventbus-and-shared-db-docs-domains.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-093304_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100147
- **Related target files**: tools/check_docs_consistency.py
