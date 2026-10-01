## Goal
- Update only the `10_adr/` entries of `EXPECTED_WITHIN_FILE_PAIRS` in `tests/tools/test_check_docs_quality.py` so that, after the ADR translation, `test_cross_file_duplication_detected_on_full_docs_tree` reports no `10_adr/` entry in its Added/Removed diff (REQ-004: reconcile ADR snapshot rows).

## Scope
- In: the `"10_adr/..."` string entries inside the `EXPECTED_WITHIN_FILE_PAIRS` frozenset literal, and the snapshot comment line above it (update date and source).
- Out: every non-`10_adr/` entry (including the stale `23_agent/05_agent_*` entries that make the test already fail), every test function, helpers, fixtures, and `tools/check_docs_quality.py`.

## Assumptions
- Current state (2026-10-01, re-verified in Step 3a): 70 `10_adr/` entries for ADR-001 (3), ADR-002 (11), ADR-003 (12), ADR-004 (3), ADR-005 (2), ADR-006 (1), ADR-007 (2), ADR-008 (10), ADR-009 (6), ADR-010 (18), and ADR-014 (2); 16 of them contain Japanese section names (e.g. `'3. 第3の採用理由 — Operability'`).
- The test compares sets (`current_pairs == EXPECTED_WITHIN_FILE_PAIRS`), so duplicate literal entries collapse; preserve the existing literal style but ordering/duplicates do not affect the result.
- The test already fails before this work, only because of `23_agent/05_agent_*` entries in the "Removed" set (commit `3d7a2c4fc` message records this as pre-existing).
- Translation changes section bodies, so similarity pairs can be added or removed even for sections whose names were already English.

## Design decisions
- Regenerate the `10_adr/` subset from the checker's actual post-translation output rather than hand-translating section names — the snapshot must reflect what `check_docs_quality.py` reports, not what the names were expected to become.
- Keep the non-`10_adr/` subset byte-identical; fixing the pre-existing `05_agent_*` drift is out of scope (`rules/ai-execution.md` Step-Level Failure Triage: record, do not fix).

## Alternatives considered
- Replace the whole snapshot with the current output: rejected — would silently absorb the unrelated, pre-existing `05_agent_*` drift outside this Plan's scope.
- Remove `10_adr/` from the snapshot comparison: rejected — changes test behavior instead of updating its baseline.

## Implementation
### Target file
- `tests/tools/test_check_docs_quality.py`

### Procedure
1. Confirm Plan Steps 2-16 are Completed (all ADR translations landed).
2. Run `uv run python tools/check_docs_quality.py` and extract the within-file pairs for `10_adr/` using the same regex the test uses (`\[WARNING\] ([^:]+):\d+ — Content similarity detected between sections '([^']+)' and '([^']+)'`), formatted as `"{file}:{repr(a)} <-> {repr(b)}"`.
3. Replace exactly the `"10_adr/..."` entries in `EXPECTED_WITHIN_FILE_PAIRS` with the extracted set, keeping them at the same position in the literal.
4. Update the comment above the frozenset to state the update date and this procedure's path.
5. Run the Validation plan.

### Method
- Edit only the literal's `10_adr/` lines; verify with `git diff -U0 tests/tools/test_check_docs_quality.py` that every changed line starts with `"10_adr/` (plus the comment line).

### Details
- Expected outcome after the update: running the test yields either a pass or a failure whose Added/Removed sets contain only the pre-existing `23_agent/05_agent_*` entries — no `10_adr/` entry.
- Keep line length ≤ 88 where the existing entries comply; follow the existing (exceeding) style for long pair strings rather than reformatting unrelated lines.

## Compatibility considerations
- No change to test logic or to `tools/check_docs_quality.py`; other tests in the module are unaffected.

## Security considerations
- N/A: test fixture data only.

## Rollback considerations
- Revert with `git checkout -- tests/tools/test_check_docs_quality.py`; independent of the ADR edits (reverting ADRs would require regenerating this subset again).

## Validation plan
- `uv run pytest tests/tools/test_check_docs_quality.py` — passes, or fails with no `10_adr/` entry in Added/Removed.
- `uv run ruff format --check tests/tools/test_check_docs_quality.py` and `uv run ruff check tests/tools/test_check_docs_quality.py` — clean.
- `uv run mypy tests/tools/test_check_docs_quality.py` — no new error versus baseline.
- `uv run pytest tests/tools` — no new failures versus the Plan Step 1 baseline.

## Completion criteria
- Every `10_adr/` entry in `EXPECTED_WITHIN_FILE_PAIRS` matches the post-translation checker output, and no `10_adr/` entry appears in the test's Added/Removed diff.
- Non-`10_adr/` entries are byte-identical to before.
- Lint/format checks are clean.

## Out of scope
- Fixing `23_agent/05_agent_*` snapshot drift; modifying any other test or tool; any ADR text change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm Plan Steps 2-16 Completed | Completed | 20261001-132152 | 20261001-132152 | Plan Steps 2-16 Completed; stale_detector clean |
| 2 | Extract post-translation 10_adr pairs from check_docs_quality output | Completed | 20261001-132323 | 20261001-132323 |  |
| 3 | Replace only 10_adr entries and update the snapshot comment | Completed | 20261001-132323 | 20261001-132323 |  |
| 4 | Run pytest, ruff, mypy and compare with baseline | Completed | 20261001-132323 | 20261001-132323 | Replaced the 70 10_adr/ snapshot entries with the 6 pairs the checker reports after translation (extracted with the test's own regex); comment updated; non-10_adr entries byte-identical (git diff -U0 checked); snapshot diff for 10_adr/: Added 0 / Removed 0; test still fails only on the 30 pre-existing 23_agent/05_agent_* entries (out of scope); governance_01/04 cross-file finding still present; ruff format/check clean; mypy no issues (same as before); full suite deferred to batch end per user decision; docs step N/A |

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
- **Requirement ID**: REQ-004 (reconcile 10_adr snapshot rows) — Plan Implementation steps Step 17
- **Source issue**: issues/20261001-104551_langadr001_translate-japanese-adr-content-to-english.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-105822_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-115707
- **Related target files**: tests/tools/test_check_docs_quality.py