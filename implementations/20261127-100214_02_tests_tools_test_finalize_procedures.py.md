## Goal
- Create `tests/tools/test_finalize_procedures.py` to verify `tools/finalize_procedures.py` with synthetic procedures covering each classification (`REQ-001`..`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new test module; it is its own document (not a companion) because `tools/TOOL_DESCRIPTIONS.md` also names it in `Related Tests`.
- Out of scope: the live-Plan comparison (`REQ-005`), recorded in the implementation report.

## Assumptions
- Run after the seq 01 procedure.
- The pure functions (`classify_symbol`, `parse_missing_symbols`, `apply_actions`, `find_procedures`) are tested directly; `run_check` is replaced by a stub for the orchestration tests so no checker needs a temporary repository. A final smoke test runs the real `tools/check_workitem_structure.py` on a synthetic procedure written under `tmp_path` (the structure checker takes `--file`).

## Design decisions
- Import as `import tools.finalize_procedures as fp` (the pattern of `tests/tools/test_amend_plan.py`); build procedure text with a small helper that fills the template headings.

## Alternatives considered
- Running the real stale detector in tests: rejected, it resolves paths against the real repository.

## Implementation
### Target file
`tests/tools/test_finalize_procedures.py` (new)

### Procedure
1. Helper `_procedure(implementation_body: str, source_plan: str = "plans/p.md") -> str` returning a full document with every template heading.
2. Classification (parametrized): `` `HIGH_SHARE = 0.70` `` and ``"`name: type`"`` give `created here`; "Add a function `deploy_impact(path, change, deploy_text)`" gives `created here` for `deploy_text` (signature rule) and for `deploy_impact`; "create the field `dedup_key`" gives `created here`; `` `result.is_stale` `` gives `not a code symbol` for `is_stale`; `"value_name"` inside a quoted literal and `key=value_name` give `not a code symbol`; a bare mention of a name with no rule gives `ambiguous`.
3. `parse_missing_symbols`: a sample stale output with a `symbol_missing` line, a `line_ref` line, and the `new_target_exists` line yields only the symbol names and returns the other lines as unclassified.
4. `apply_actions`: `created here` gets `(new)` once (idempotent on a second call); `not a code symbol` loses its backticks only on exact backticked occurrences; `ambiguous` text is byte-identical; a name inside a longer backticked span is unchanged.
5. Orchestration with a stubbed `run_check`: all pass gives exactly one `OK:` line, counts equal the fixtures, and exit 0; a failing structure result gives a row with the document, tool, and exit code and exit 1 while the other checks still ran (assert the stub's call list); no procedures gives exit 1 and the message; `--apply` without `--dry-run` writes, `--dry-run` writes nothing, no flag writes nothing.
6. Discovery: documents with a different `Source plan` are ignored; `plans/` and `plans/done/` spellings of the same Plan match by base name; `done/` documents are included only with `--include-done`.
7. A pinned-format test: the `Symbol '<name>' not found in source` pattern matches the detector's real line format by calling `tools.stale_detector.StaleResult` summary on a constructed result.

### Method
- Use `tmp_path` for all files and pass `--root tmp_path`; no network, no global state.

### Details
- `rules/coding.md`: line length 88, English comments, annotated helpers.

## Compatibility considerations
- Test-only; `tests/` is rsynced by `deploy/deploy.sh`, which is harmless.

## Security considerations
- N/A: temporary files only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_finalize_procedures.py -q`
- `uv run ruff format`, `uv run ruff check`, `uv run mypy` on the file.

## Completion criteria
- Each Plan acceptance criterion AC-1 to AC-6 is covered by a passing test and the file passes ruff and mypy.

## Out of Scope
- Changes to `tools/finalize_procedures.py` beyond what a failing test proves necessary (that is an amendment of the seq 01 procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/tools/test_finalize_procedures.py` with the helpers and tests of Procedure | Pending | — | — | Needs seq 01 first |
| 2 | Run the tests and fix failures in the test or report a tool defect | Pending | — | — | |
| 3 | Run ruff and mypy on the file | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`..`REQ-005` (behaviors under test)
- **Source issue**: issues/20261126-151441_wfeff006_finalize-procedure-checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-095609_wfeff006_finalize-procedure-checks.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-100214
- **Related target files**: `tests/tools/test_finalize_procedures.py`
