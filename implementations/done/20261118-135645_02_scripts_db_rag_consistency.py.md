## Goal
Give each silent consistency rule a finding (`REQ-003`: no rule makes `is_consistent` false without a finding) so startup records a non-ok `rag_consistency` entry for it (`REQ-004`), keeping the single-rule `_CHECKS` design.

## Scope
**Release unit**: N/A: not part of a release unit
- In scope: five issue builders, their wiring into `_CHECKS`, and making `_ConsistencyCheck.issue` required.
- Companion test file: `tests/db/test_rag_consistency.py`.

## Assumptions
- The five rules without a builder today are `diagnostic_errors`, `read_smoke_test_ok`, `fk_unverified`, `embedding_unverified`, `schema_unverified` (checked in Step 3a against `_CHECKS`).
- Severity is DEGRADED with the `[WARNING]` prefix, aligned with ADR-004 Decision Group 2 item 7 (pending, AAL-019); decided by the maintainer for this Plan.
- UNK-01 resolution: the `repair_action` value is `rerun_check` (new) for all five; it is documented in `rag_05_07` by procedure 03.
- `scripts/db/models.py` needs no change: `ConsistencyFinding` already carries severity, message, and `repair_action` as free strings.

## Design decisions
- One builder per rule, in the style of `_fk_inconsistency_issue`, each returning a DEGRADED `ConsistencyFinding` whose message states what could not be verified and ends with "Re-run the consistency check after the cause is resolved."
- Because every rule then has a builder, `issue` becomes a required field and the `is not None` guards disappear; there is no second condition list.

## Alternatives considered
- FATAL severity (the Issue's interim value): rejected by the maintainer in favor of the ADR-004 item 7 classification.
- Keeping `issue: ... | None = None`: rejected; a rule without a builder is exactly the silent-pass defect.

## Implementation
### Target file
`scripts/db/rag_consistency.py`

### Procedure
1. Add after `_unknown_schema_issue` five builders: `_diagnostic_errors_issue` (new), `_read_smoke_test_issue` (new), `_fk_unverified_issue` (new), `_embedding_unverified_issue` (new), `_schema_unverified_issue` (new).
2. In `_CHECKS`, pass the matching builder as the second argument of the five entries that currently have none; keep their order and the fail-closed comment.
3. In `_ConsistencyCheck`, make `issue` a required `Callable[[RagConsistencyReport], ConsistencyFinding]` (no default) and rewrite its docstring: it no longer says two rules have no builder.
4. Remove the now-dead `check.issue is not None` condition in `check_rag_consistency` and the `check.issue is None or` condition in `summarize_issues`.

### Method
- `_diagnostic_errors_issue` (new): `[WARNING] Consistency diagnostics failed (count=N). First: <first diagnostic>.` plus the re-run sentence; `report.diagnostic_errors` is a tuple or None, so guard with `or ()`.
- `_read_smoke_test_issue` (new): `[WARNING] Read smoke test failed: a required RAG table could not be read.` plus the re-run sentence.
- `_fk_unverified_issue` (new), `_embedding_unverified_issue` (new), `_schema_unverified_issue` (new): `[WARNING] FK consistency could not be verified (probe failed).` and the matching texts for embedding dimension and schema recognition, plus the re-run sentence.
- All five use `severity=FindingSeverity.DEGRADED` and `repair_action="rerun_check"` (new value).

### Details
- Keep the file within its module-size baseline (`tools/check_module_size.py` baseline-gated): five short builders only.
- `check_rag_consistency` has radon complexity C (18); removing the `is not None` condition does not raise it.

### Companion test files
- `tests/db/test_rag_consistency.py`
  - Procedure: add `rerun_check` (new) with phrase `Re-run the consistency check` to `_REPAIR_PHRASE`; make `_all_unclean_report` also set `diagnostic_errors=("probe failed",)`, `read_smoke_test_ok=False`, `fk_unverified=True`, `embedding_unverified=True`, `schema_unverified=True`; drop `check.issue is not None` from `TestFindingConsistency._findings` and compare against `len(_CHECKS)` in `test_every_rule_with_an_issue_builder_yields_a_finding`; add `test_each_silent_rule_yields_one_degraded_finding` (new) (new, parametrized over the five fields, single-rule reports) and `test_findings_are_empty_exactly_when_the_report_is_consistent` (new) (new, parametrized over the same reports plus a clean one, comparing `is_consistent(report)` with `check_rag_consistency`-style `findings`); add `test_unverified_fk_with_zero_counts_yields_a_finding` (new) (new, the acceptance case: `fk_unverified=True`, all counts zero).
  - Validation: `uv run pytest tests/db/test_rag_consistency.py`.

## Compatibility considerations
- New findings appear for databases whose probes fail; startup treats them as warnings (DEGRADED), so no start is blocked.
- `_ConsistencyCheck.issue` becoming required is internal to this module (the only other reader is the test file).

## Security considerations
N/A: read-only diagnostics; no new input is parsed.

## Rollback considerations
N/A: revert the commit; no persisted data or schema is touched.

## Validation plan
- `uv run pytest tests/db/test_rag_consistency.py tests/agent/services/test_rag_index_integrity.py`.
- Validation sequence of `rules/toolchain.md` (ruff, mypy, diff-cover 100%); `uv run python tools/check_module_size.py`.

## Completion criteria
- Each of the five rules yields exactly one DEGRADED finding with `repair_action="rerun_check"`.
- For every tested report, `is_consistent` is false iff `findings` is non-empty.
- `_ConsistencyCheck.issue` has no default and no `None` check remains in the module.

## Out of Scope
- Startup routing (procedure 04), the documentation table (procedure 03), `scripts/db/models.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the five builders, wire them into `_CHECKS`, make `issue` required (Implementation > Procedure) | Completed | 20261118-140956 | 20261118-140956 | Changed: scripts/db/rag_consistency.py, tests/db/test_rag_consistency.py. Full suite 12780 passed, diff-cover 100%. |
| 2 | Update and add tests in `tests/db/test_rag_consistency.py` (Companion test files) | Completed | 20261118-140956 | 20261118-140956 | — |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-140956 | 20261118-140956 | — |

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20261117-123005_adrchk005_startup-fail-closed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-134945_adrchk005_startup-fail-closed.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-135645
- **Related target files**: `scripts/db/rag_consistency.py`, `tests/db/test_rag_consistency.py`
