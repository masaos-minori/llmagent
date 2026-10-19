## Goal
Make ADR-008 state that sqlite-vec is loaded by default for the databases that own a vec0 table (`rag.sqlite`, `session.sqlite`) and for no other, replacing the rule "only into `rag.sqlite`" (`REQ-001`).

## Scope
- Amend, in this one file: the Constraints bullet, Decision Details item 9, the scope sentence in Positive Consequences, INV-08, the INV-08 row of Automated Tests, the Implementation Notes bullet, the Review Triggers bullet, and the Approval Record `Current Decision Approval` sentence.
- Leave the four-database decision, table ownership, recovery matrix, and cross-database rules unchanged.

## Assumptions
- The owner's instruction of 2026-10-19 (adopt Session Vector by amending ADR-008) is the task-level approval ADR-008's Approval Record accepts (Plan Assumptions).
- The INV-08 Verification row cites tests created by the procedures for `tests/db/test_sqlite_helper.py` and `tests/tools/test_check_db_separation.py`; edit that row only after those tests exist, because a pre-commit hook rejects citations of missing tests.

## Design decisions
- Reword INV-08 and Decision 9 to name the two databases that own a vec0 table instead of adding a session exception; the invariant keeps its meaning (extension scope follows vec0 table ownership).
- Keep the Review Triggers bullet as a trigger, widened to "a database other than `rag.sqlite` and `session.sqlite`", since the trigger that justified this amendment has now been consumed.

## Alternatives considered
A new ADR superseding ADR-008 was rejected: the change is one scope sentence inside an unchanged decision. Keeping INV-08 and recording `session` as an exception was rejected: it would leave an invariant that the implemented schema ownership already contradicts.

## Implementation
### Target file
`docs/10_adr/adr_02_008_sqlite-4db-separation.md`

### Procedure
1. Edit the Constraints bullet and Decision Details item 9 to the new scope wording.
2. Edit the Positive Consequences scope sentence, INV-08, the Implementation Notes bullet, and the Review Triggers bullet.
3. After the helper and check-tool tests exist, replace the INV-08 row of Automated Tests with rows citing them.
4. Update the Approval Record `Current Decision Approval` sentence to cover the amended scope.

### Method
- Use Edit with exact old strings; each passage appears once (Constraints: "sqlite-vec extension loaded only into `rag.sqlite`"; item 9 and INV-08: "sqlite-vec is loaded only into `rag.sqlite`"; Implementation Notes: "loads the sqlite-vec extension by default only for `rag`").
- Do not touch any other `INV-` line, the Failure Policy, or the Decision text outside item 9.

### Details
- New INV-08: "sqlite-vec is loaded by default only into the databases that own a vec0 table: `rag.sqlite` and `session.sqlite`; it is not loaded into `workflow.sqlite` or `eventbus.sqlite`."
- New Implementation Notes bullet: `SQLiteHelper` loads sqlite-vec by default for `rag` and `session`, never for `workflow` or `eventbus`; an explicit `load_vec` overrides the default.
- New Verification row: test column "sqlite-vec is loaded by default only for `rag` and `session`, never for `workflow` or `eventbus`"; implementation column cites `TestSQLiteHelperVecDefault.test_default_load_vec_per_target` in `tests/db/test_sqlite_helper.py` and the three `test_default_load_vec_rule_*` tests in `tests/tools/test_check_db_separation.py` (names are fixed by their own procedures; copy them from there).
- New approval sentence: the task-level approval (repository owner instruction) covers the current decision text as of 2026-10-19, including the sqlite-vec scope amendment; individual reviewer names are not recorded.

## Compatibility considerations
Widens a normative rule. `docs/10_adr/adr_01_index.md` has no ADR-008 INV-08 row (checked), so no Index edit is needed. Other documents restating the scope are separate procedures.

## Security considerations
No new load path: the extension is still loaded only through the helper's configured-path loader, which disables extension loading right after. The amendment widens which connection uses it, not how.

## Rollback considerations
N/A: revert the commit together with the `SQLiteHelper` default change.

## Validation plan
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`
- `uv run python tools/check_docs_content_policy.py --strict`
- `uv run python tools/check_docs_japanese.py`
- `uv run python tools/check_adr_preservation.py` — an ERROR for the intentional INV-08 text change and the changed test citations is expected (Plan UNK-03); record it in the commit message and report if the pre-commit hook blocks the commit.
- `uv run python tools/check_docs_consistency.py --domain overview`

## Completion criteria
- All seven passages state the same scope (`rag`, `session`).
- The INV-08 Verification row cites only tests that exist.
- The Approval Record covers the amendment.

## Out of scope
- Any file other than the target file
- Code, tests, or configuration changes
- A new ADR or an ADR status change

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit Constraints, Decision 9, Consequences, INV-08, Implementation Notes, Review Triggers | Pending | — | — | |
| 2 | Replace the INV-08 Verification row after the cited tests exist | Pending | — | — | |
| 3 | Update the Approval Record sentence | Pending | — | — | |
| 4 | Run the documentation checkers and `tools/check_adr_preservation.py` (INV-08 error expected) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (amend the sqlite-vec scope rule)
- **Source issue**: issues/20261019-092704_mem001_session-sqlite-vec-not-loaded-at-runtime.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-094625_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-095521
- **Related target files**: docs/10_adr/adr_02_008_sqlite-4db-separation.md
