## Goal

Land the pinned `REQ-008` gated follow-on from `implementations/done/20261117-020145_02_docs_41_db_db_02_architecture_and_schema-schema-reference_md.md`: state in `db_02` §7 that the workflow lease columns are schema-enforced `NOT NULL` and that `owner_id` carries `CHECK(length(owner_id) > 0)`. The gate is released: `compat002` implemented (commit `3bc1efd58`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The gate is genuinely open (verified 20261117): the shipped DDL now reads `owner_id TEXT NOT NULL CHECK (length(owner_id) > 0)` and `lease_expires_at TEXT NOT NULL` (`scripts/db/schema_sql.py:192-193`), and `idempotency_ops::begin_stage_if_new()` takes `lease_duration_sec: int` as a required parameter with `_validate_lease_duration()` rejecting non-int/non-positive values (`scripts/agent/workflow/idempotency_ops.py:13-25,40-60`). `compat002`'s code procedures `20261117-011632_01`–`_04` are still active in `implementations/` but their code landed in `3bc1efd58`; this row documents the shipped DDL, not the procedure lifecycle.
- The exact wording is the one pinned in the `Details` section of the archived procedure `20261117-020145_02`: "`owner_id` and `lease_expires_at` are `NOT NULL`; `owner_id` also carries `CHECK(length(owner_id) > 0)`".
- §7 already carries the lease-contract paragraph landed by `20261117-020145_02` (verified 20261117); this row extends that paragraph rather than adding a second one.

## Design decisions
- **Extend the existing §7 lease-contract paragraph with one schema-enforcement sentence**, matching the pinned wording, instead of a new paragraph. Keep the responsibility/consequence style; the sentence names the schema-level guarantee, which is §7's subject (schema reference).

## Alternatives considered
- **Waiting until the `compat002` procedure batch (011632_01–_04) is archived.** Rejected per owner decision 20261117: the gate was defined on the schema/code contract, which has landed and is verified in the shipped DDL; the batch's remaining rows are validation bookkeeping and touch no docs.
- **Rewriting the whole lease paragraph to lead with `NOT NULL`.** Rejected: the existing paragraph is accurate and already reviewed; a one-sentence extension is the minimal in-scope edit.

## Implementation
### Target file
`docs/41_db/db_02_architecture_and_schema-schema-reference.md`

### Procedure
1. **REQ-008** — In the §7 lease-contract paragraph, after the sentence about the lease duration supplied by the production caller, add: the lease duration is required on every attempt-start call and the schema enforces `owner_id` and `lease_expires_at` as `NOT NULL`; `owner_id` also carries `CHECK(length(owner_id) > 0)`.

### Method
One sentence appended to the existing §7 lease-contract paragraph.

### Details
- Current paragraph ends with "...an old `started_at` alone never makes an attempt stale — and `agent/workflow/state_store.py::recover_stale_attempts()` recovers only lease-expired rows; the recovery narrative is in [db_07 section 9.7]...". Insert the enforcement sentence before the recovery link sentence so the schema facts stay grouped with the stamping facts.

## Compatibility considerations
Doc-only; no runtime blast radius. The statement matches the shipped DDL of `3bc1efd58`; databases created before that commit still have nullable columns but are refused by the startup fingerprint gate and recreated (already documented in §7).

## Security considerations
N/A: documentation only.

## Rollback considerations
Revert the doc edit; no operational dependency.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain db`, `check_docs_structure.py`, `check_docs_japanese.py`.
- `uv run python tools/check_workitem_structure.py --file <this file>`.

## Completion criteria
- §7 states the `NOT NULL` enforcement and the `owner_id` length `CHECK` for both lease columns (`REQ-008`).
- The pinned follow-on from `20261117-020145_02` is no longer outstanding.

## Out of Scope
`db_07` §11 direct lease-constraint check (`REQ-008`, row 123746_06); code changes; the `compat002` procedure batch lifecycle.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-124003 | 20261117-124023 | Schema-enforcement sentence landed in db_02 section 7 lease paragraph: lease duration required, NOT NULL columns, owner_id CHECK(length>0). |
| 2 | Add or update tests per Validation plan | Completed | — | 20261117-124024 | N/A: documentation-only row. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261117-124024 | doc checkers all exit 0; check_workitem_structure clean. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261117-124024 | N/A: documentation-only row. |

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
- **Source issue**: N/A: follow-on to `implementations/done/20261117-020145_02_docs_41_db_db_02_architecture_and_schema-schema-reference_md.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261116-224307_compat003_workflow-lease-docs-runbook.md
- **Source implementation procedure**: implementations/done/20261117-020145_02_docs_41_db_db_02_architecture_and_schema-schema-reference_md.md
- **Generated at**: 20261117-123746
- **Related target files**: docs/41_db/db_02_architecture_and_schema-schema-reference.md