## Goal
Write, before the fix, the tests that pin each finding's prefix to its severity and its message to its repair action, and update the existing assertions that pin the old prefixes and guidance (REQ-001, REQ-002).

## Scope
**Release unit**: rag-diagnostics
- `tests/db/test_rag_consistency.py` only; no production file changes.
- Release unit: the failing-first tests stay red until procedure 02 lands, so the full suite and diff-cover run once at the end of the unit.

## Assumptions
- The repair action mapping is the Source plan default (UNK-02): `rebuild_fts` for the FTS findings, `rebuild_vec` for orphan vector rows, a new `reingest` value for vector mismatch, chunks without vector rows, documents without chunks, and URL-level inconsistency, `restore_from_backup` for the FATAL findings. The owner confirms it before procedure 02; a different mapping changes these tests.
- Severities do not change; only the three DEGRADED findings that carry `[CRITICAL]` change their prefix.
- Expected pre-fix result: the new consistency tests fail on the three prefixes, on the repair actions that cannot fix their state, and on the FATAL messages that name no repair; the updated old assertions fail for the same reasons. Record the failing output in the Execution Status Notes.

## Design decisions
- One report with every rule unclean exercises every issue builder; the test iterates the `_CHECKS` pairs instead of repeating each finding.
- The phrase table maps a repair action to the command or wording a user can act on, so a mismatch between a message and its action fails.

## Alternatives considered
Per-finding tests were rejected: they repeat the same assertion eleven times and miss a new finding.

## Implementation
### Target file
`tests/db/test_rag_consistency.py`
### Procedure
1. Update the existing assertions that pin the old behavior: the FTS orphan tests (the one searching `[CRITICAL]` with `FTS index has more entries`, the one that finds `fts_orphan_issue`, and the exact-text tests of `TestFtsOrphanIssueDetail`-style cases) expect `[WARNING]`; the orphan vector prefix test (`test_summarize_issues_orphan_vec_has_critical_prefix`) is renamed to say warning and expects `[WARNING]`; the orphan vector guidance test expects `/session rag-rebuild-vec` instead of `ingester.py --force`; the chunks-without-vector assertion expects `[WARNING]`.
2. Add helper `_all_unclean_report` (new): a `_report(...)` call that makes every rule unclean (FTS gap and FTS orphan, orphan vector rows, vec different from chunks, documents without chunks, chunks without vector rows, duplicate chunk index, URL-level mismatches, FK inconsistency, dimension mismatch, unknown schema).
3. Add class `TestFindingConsistency` (new) with: every finding's prefix is `[CRITICAL]` if and only if it is FATAL and `[WARNING]` otherwise; every finding's message contains the phrase `_REPAIR_PHRASE` (new) assigns to its repair action; every repair action is a key of `_REPAIR_PHRASE` (new); the report yields one finding for each rule that has an issue builder.
4. Run the file and record the failures.
### Method
Build findings with `[check.issue(report) for check in _CHECKS if check.issue is not None and not check.clean(report)]`, importing `_CHECKS` from `db.rag_consistency`. `_REPAIR_PHRASE` (new) maps `rebuild_fts` to `/session rag-rebuild-fts`, `rebuild_vec` to `/session rag-rebuild-vec`, `reingest` to `ingester.py --force`, and `restore_from_backup` to `verified backup`. Import `FindingSeverity` from `db.models`.
### Details
- The existing tests with `ingester.py --force` for the vector mismatch and the URL-level mismatch stay as they are; the new messages keep that phrase.
- Do not change any test that does not pin a prefix, a guidance phrase, or a repair action.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: in-memory databases and report objects only.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/db/test_rag_consistency.py` (expected red before procedure 02, green after)
- `uv run ruff format <changed files>`, `uv run ruff check <changed files>`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run python tools/check_mock_patch_targets.py`

## Completion criteria
- The new tests exist and fail before the fix for the stated reasons; the updated assertions encode the new prefixes and guidance.
- After procedure 02 the whole file passes.

## Out of Scope
- Editing `scripts/` files.
- Changing a severity or a test that does not pin a prefix, phrase, or repair action.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the repair action mapping (UNK-02) with the owner | Pending | — | — | Stop and ask if not confirmed |
| 2 | Update the pinned assertions and add the consistency tests | Pending | — | — |  |
| 3 | Run the file and record the expected failures | Pending | — | — | Record the failing output here |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Stays In Progress until the end-of-unit run |

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
- **Requirement ID**: `REQ-001`, `REQ-002`: prefix matches severity; message and repair action agree
- **Source issue**: issues/20261117-123006_adrchk006_rag-failure-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-124317_adrchk006_rag-failure-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-124938
- **Related target files**: `tests/db/test_rag_consistency.py`
