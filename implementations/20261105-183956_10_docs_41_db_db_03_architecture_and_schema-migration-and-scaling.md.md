## Goal

Update the EventBus migration passage of `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` from the single 3 -> 4 ledger step to the canonical version-6 three-step forward-only chain (`3 -> 4 -> 5 -> 6`), and reference the fingerprint identity contract, so the passage is not stale after this Plan registers the 4 -> 5 outbox and 5 -> 6 FK-dedup steps.

## Scope
**Release unit**: canonical-version-6

## Assumptions
- The doc is documentation-only; this Plan edits prose only. The corrected prose must stay consistent with `scripts/eventbus/migrations.py` (the three ordered registry steps), `scripts/eventbus/schema.sql` (version stamp 6), and `scripts/shared/eventbus_schema_fingerprint.py` (`assert_matches` / `validate_canonical`).
- `dbmigsafe001` already rewrote this passage for the two-step (3 -> 4) state; this Plan's added steps make it stale again, so the correction moves it to the three-step chain.
- The "Migration guarantees" paragraph (L58) describes the shared runner contract across the workflow and eventbus databases; "both" databases still each carry a migration, so that sentence is left unchanged.

## Design decisions
- Replace the "one registered forward-only migration ... 3 -> 4" clause (L52) with the three-step chain and name each step, and change the `PRAGMA user_version = N` placeholder to 6.
- Update the eventbus.sqlite table row (L76-L77) to describe the full `3 -> 4 -> 5 -> 6` chain and cite the fingerprint contract as the per-step postcondition, leaving the workflow.sqlite and mdq.sqlite rows untouched.

## Alternatives considered
- Editing only the table row and leaving L52: rejected — L52 is the primary narrative passage and would remain stale; both must move to the three-step chain together.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Edit the eventbus migration paragraph (L52): replace "There is one registered forward-only migration, the ledger bootstrap that bumps the baseline from `3` to `4` (`eventbus_ledger_baseline` in `eventbus/migrations.py`)" with the three-step chain — `eventbus_ledger_baseline` (3 -> 4, ledger bootstrap), `eventbus_dlq_outbox` (new) (4 -> 5, outbox baseline), and `eventbus_dlq_outbox_fk_dedup` (new) (5 -> 6, rebuilds `dlq_outbox` to a single inline foreign key) — and change `PRAGMA user_version = N;` to `PRAGMA user_version = 6;`.
2. In the same paragraph, add a clause that each step re-verifies the canonical fingerprint (`assert_matches` against `scripts/shared/eventbus_schema_fingerprint.py`) as its postcondition and that `validate_canonical` (new) gates the create path on version 6 plus shape before any mutation.
3. Edit the eventbus.sqlite row of the "Supported Upgrade Baseline" table (L77): change "Registered forward-only migration (`eventbus/migrations.py`) adds the ledger, bumps the baseline to `user_version 4`, and re-verifies the `schema.sql` fingerprint, preserving rows" to describe the full `3 -> 4 -> 5 -> 6` chain ending at version 6, re-verifying the fingerprint contract at each step, preserving rows. Leave the "Never — the ledger is the replayable migration history" removal condition and the EventBus service owner unchanged.

### Method
- Two in-place edits (the L52 paragraph and the L77 table cell); no other section or row is touched. The workflow.sqlite row (L76) and the mdq.sqlite row (L78) are left as-is.

### Details
- Pre-change anchors: L50-L52 (eventbus migration paragraph), L74-L78 (Supported Upgrade Baseline table), L58 (shared migration guarantees).
- The new step names `eventbus_dlq_outbox` and `eventbus_dlq_outbox_fk_dedup` must match `REGISTRY` keys in `eventbus/migrations.py` exactly.
- Layering unchanged: this doc references the migration modules as external documentation only; no code change.

### Companion test files
- None: this is a documentation correction; the migration behavior it now describes is covered by the code rows' tests.

## Compatibility considerations
- N/A: prose-only edit; no caller, import, or schema is affected.

## Security considerations
- N/A: no behavioral change; the corrected text only describes the existing fail-closed validate-before-write and per-step rollback contract.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Docs/ADR checkers: `uv run python tools/check_docs.py` and the ADR checkers named in `routing.md` Tools "When to run which tool"; expect zero findings.

## Completion criteria
- The eventbus migration passage states the `3 -> 4 -> 5 -> 6` three-step chain with each step named, `PRAGMA user_version = 6`, and the fingerprint contract as the per-step postcondition; the eventbus.sqlite table row reflects the full chain.
- `check_docs.py` / ADR checkers report no findings.

## Out of Scope
- The `schema.sql` version bump and FK removal (seq 02), the 5 -> 6 rebuild step (seq 03), the fingerprint contract code (seq 04), the `create_eventbus_schema` three-path rewrite (seq 01), the equivalence/convergence tests (the test row), and the eventbus_06 schema-passage correction (seq 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | docs-only row; no tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: issues/20261104-143443_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-234502_ebschema001_separate-eventbus-schema-create-validate-migrate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-183956
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
