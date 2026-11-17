## Goal

Land the pinned `REQ-008` gated follow-on from `implementations/done/20261117-020145_03_docs_41_db_db_07_api_and_operations-recovery-and-reference_md.md`: add the optional direct lease-constraint check to `db_07` §11. The gate is released: `compat002` implemented (commit `3bc1efd58`) and the shipped DDL enforces the columns.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The gate is genuinely open (verified 20261117): `scripts/db/schema_sql.py:192-193` ships `owner_id TEXT NOT NULL CHECK (length(owner_id) > 0)` and `lease_expires_at TEXT NOT NULL`, so a post-recreation direct check can reference real constraints. `compat002`'s code procedures `20261117-011632_01`–`_04` are still active in `implementations/` but their code landed in `3bc1efd58`.
- The exact wording is the one pinned in the `Details` section of the archived procedure `20261117-020145_03`: an optional direct lease-constraint check verifying `attempts.owner_id` and `lease_expires_at` are `NOT NULL` (with `CHECK(length(owner_id) > 0)`).
- §11 "Important notes" already carries the workflow verification / no-migration / rollback bullets landed by `20261117-020145_03` (verified 20261117); the new bullet joins that list.
- `db_07` sits at its recorded size ceiling (`check_docs_structure.py` `SIZE_EXCEPTIONS`, 27995 recorded 20261117); the added bullet will require the ceiling to be re-recorded to the accepted size, per the established precedent comments in that file.

## Design decisions
- **One "Important notes" bullet in §11**, phrased as an optional operator check after recreation (verify the lease columns' `NOT NULL` and the `owner_id` length `CHECK` via `PRAGMA table_info(attempts)` / the DDL), not a new procedure step: the fingerprint gate already refuses a shape mismatch, so the direct check is supplementary verification, matching the pinned "optional" framing.

## Alternatives considered
- **Waiting until the `compat002` procedure batch (011632_01–_04) is archived.** Rejected per owner decision 20261117: the gate was defined on the schema/code contract, which has landed and is verified in the shipped DDL.
- **Making the check a mandatory §11 step.** Rejected: it duplicates what `check_workflow_schema()` enforces automatically at startup; the pinned wording says "optional".

## Implementation
### Target file
`docs/41_db/db_07_api_and_operations-recovery-and-reference.md`

### Procedure
1. **REQ-008** — In §11 "Important notes", after the **Workflow verification** bullet, add an **Optional lease-constraint check** bullet: after recreating `workflow.sqlite`, an operator can verify directly that `attempts.owner_id` and `lease_expires_at` are `NOT NULL` and that `owner_id` carries `CHECK(length(owner_id) > 0)`.

### Method
One bullet appended to the §11 "Important notes" list.

### Details
- Keep the bullet operational and short; it names the column constraints, not a specific sqlite3 command line, consistent with the file's existing bullet style.

## Compatibility considerations
Doc-only; no runtime blast radius. `tools/check_docs_structure.py`: `db_07` grows past its recorded 27995 ceiling; re-record the ceiling to the accepted new size with the usual dated precedent comment, and re-baseline the tool's module size in `tools/check_module_size_tools_baseline.txt` if the added comment pushes the tool past its recorded size.

## Security considerations
N/A: documentation only.

## Rollback considerations
Revert the doc edit and the ceiling re-record together; no operational dependency.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain db`, `check_docs_structure.py` (after the ceiling re-record), `check_docs_japanese.py`.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` if `check_docs_structure.py` changed.
- `uv run python tools/check_workitem_structure.py --file <this file>`.

## Completion criteria
- §11 carries the optional direct lease-constraint check naming both `NOT NULL` columns and the `owner_id` length `CHECK` (`REQ-008`).
- The pinned follow-on from `20261117-020145_03` is no longer outstanding.

## Out of Scope
`db_02` §7 schema-enforcement sentence (`REQ-008`, row 123746_05); code changes; the `compat002` procedure batch lifecycle.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-124037 | 20261117-124142 | Optional lease-constraint check bullet landed in 11 Important notes; db_07 ceiling re-recorded 27995->28371; tool module baseline re-recorded 33655->33665. |
| 2 | Add or update tests per Validation plan | Completed | — | 20261117-124150 | N/A: documentation-only row. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261117-124150 | doc checkers all exit 0 after ceiling re-record; tools validation ruff/mypy/bandit/tool_descriptions_sync/module_size clean; test_check_docs_structure 82 passed. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261117-124150 | N/A: documentation-only row. |

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
- **Requirement ID**: REQ-008
- **Source issue**: N/A: follow-on to `implementations/done/20261117-020145_03_docs_41_db_db_07_api_and_operations-recovery-and-reference_md.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261116-224307_compat003_workflow-lease-docs-runbook.md
- **Source implementation procedure**: implementations/done/20261117-020145_03_docs_41_db_db_07_api_and_operations-recovery-and-reference_md.md
- **Generated at**: 20261117-123746
- **Related target files**: docs/41_db/db_07_api_and_operations-recovery-and-reference.md