## Goal

Regenerate `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS` golden-snapshot constant against the current `docs/` tree, per that file's own documented regeneration procedure (REQ-003), fixing `TestRegressionFullDocsTree::test_cross_file_duplication_detected_on_full_docs_tree`.

## Scope

In scope: regenerate the contents of the `EXPECTED_WITHIN_FILE_PAIRS: frozenset[str]` constant (starting at line 27) in `tests/tools/test_check_docs_quality.py`, replacing stale pre-docs-reorg keys with the current tree's actual within-file content-similarity pairs. Out of scope: `tools/check_docs_quality.py`'s own duplication-detection logic (unchanged, already correct); any other file in this Plan (each has its own implementation procedure document).

## Assumptions

- `EXPECTED_WITHIN_FILE_PAIRS`'s regeneration is purely mechanical (re-run the tool, capture its actual output, replace the constant) — the test's own header comment (lines 17-26) documents this exact procedure and states the set is designed to tolerate content changing over time.
- The docs reorg's path renames (governance/eventbus/rag/agent/db domains) are complete and correct — this Plan does not re-verify the reorg's own correctness, only that this constant reflects the current tree.

## Design decisions

- Regenerate the constant's full contents via the tool's own documented procedure rather than hand-editing individual keys — avoids missing a stale entry or introducing a typo, and matches the test file's own stated maintenance expectation.

## Alternatives considered

- Hand-editing only the entries visibly mentioned in this session's earlier investigation (governance/eventbus/rag path-prefix changes): rejected — risks missing other stale entries (e.g. agent/db domains also confirmed affected) that only a full regeneration run would surface completely.

## Implementation

### Target file

`tests/tools/test_check_docs_quality.py`

### Procedure

1. Run `uv run python -m tools.check_docs_quality | grep 'between sections' > /tmp/pairs.txt` (or an equivalent capture) against the current repository tree.
2. Parse `/tmp/pairs.txt`'s output lines (format: `[WARNING] {file_path}:{line} — Content similarity detected between sections '{a}' and '{b}'`) into the `"{file_path}:'{a}' <-> '{b}'"` string format `EXPECTED_WITHIN_FILE_PAIRS` uses.
3. Replace the entire contents of the `EXPECTED_WITHIN_FILE_PAIRS: frozenset[str] = frozenset([...])` literal (lines 27 onward) with the newly-captured set of pairs.
4. Update the header comment's "updated {date}" note (line 17) to reflect this regeneration's date, consistent with the file's own existing convention (e.g. "updated 2026-09-23 after...").

### Method

Mechanical regeneration via the tool's own documented procedure, then a full literal replacement of the constant's contents — not a line-by-line hand edit.

### Details

- Regeneration command: `uv run python -m tools.check_docs_quality | grep 'between sections' > /tmp/pairs.txt`, per the test file's own header comment (lines 24-26).
- After regenerating, diff the new constant's domain coverage against this session's earlier-confirmed `Added`/`Removed` sets (governance/eventbus/rag/agent/db path-prefix renames only) — if the regenerated set includes an unexpected new pair outside those known-renamed domains, flag it for separate review before accepting it into the snapshot, per this Plan's own Risk mitigation.
- Confirm the cross-file-duplication assertion (`test_cross_file_duplication_detected_on_full_docs_tree`'s second assertion, checking for the known governance_01/governance_04 cross-file finding) still passes after the within-file snapshot is regenerated — the two assertions in the same test method must both hold.

## Compatibility considerations

- No production code changes; this is a test-fixture (golden snapshot) regeneration only.

## Security considerations

N/A: a test-fixture data regeneration; no security-relevant behavior change.

## Rollback considerations

- To rollback: `git revert` the commit containing this change, restoring the prior (stale) `EXPECTED_WITHIN_FILE_PAIRS` contents. No data migration or state involved.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/tools/test_check_docs_quality.py` | Integration: golden-snapshot regression against full docs tree | `uv run pytest tests/tools/test_check_docs_quality.py -q` | All tests pass, including `TestRegressionFullDocsTree::test_cross_file_duplication_detected_on_full_docs_tree` |

## Completion criteria

- `uv run pytest tests/tools/test_check_docs_quality.py -q` passes with no failures.
- The regenerated `EXPECTED_WITHIN_FILE_PAIRS`'s domain coverage has been diffed against the known-renamed domains (governance/eventbus/rag/agent/db) with no unexplained new pair silently accepted.

## Out of scope

- Any further `docs/` file renames or restructuring.
- `tools/check_dependency_graph_cycles.py` and `tools/check_issue_inventory_conformance.py` (covered by their own implementation procedure documents from this same Plan).
- Any of the other 96 full-suite test failures tracked under separate issues/plans.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Regenerated EXPECTED_WITHIN_FILE_PAIRS with 242 pairs; also updated cross-file assertion paths from old to new names |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: regenerating the existing golden-snapshot constant is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 18 tests pass, 2 skipped |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no docs/00_index.md task-scope mapping for this tests/tools/ file |

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
- **Requirement ID**: REQ-003: regenerate `EXPECTED_WITHIN_FILE_PAIRS` golden snapshot
- **Source issue**: issues/20260927-075236_docs001_stale-pre-reorg-governance-doc-paths-in-checker-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-080744_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091010
- **Related target files**: tests/tools/test_check_docs_quality.py
