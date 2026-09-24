## Goal
Update `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS`
frozenset so its 12 governance-file keys carry the `00_governance/` directory prefix
that `tools/check_docs_quality.py`'s `discover_md_files()` (already
`docs_dir.rglob("*.md")`-based) will report once seq 01/03's `git mv` lands, implementing
`REQ-002`.

## Scope
In scope: editing exactly the 12 `EXPECTED_WITHIN_FILE_PAIRS` keys prefixed
`00_governance_01_documentation-policy.md:` (10 keys) and
`00_governance_03_issue-and-uncertainty-management.md:` (2 keys). Out of scope: any
other key in the same frozenset, any other assertion in this file, and any change to
`tools/check_docs_quality.py` itself (confirmed as not needing modification — see
Compatibility considerations).

## Assumptions
- The 12-key count (10 + 2) is directly confirmed against the current file content —
  not the source Issue's originally stated count of 13 (see the Plan's `REQ-002` and
  Design for the correction).
- `docs/00_governance_02_documentation-metadata.md`,
  `docs/00_governance_04_documentation-checks.md`, and `docs/00_index.md` have zero
  entries in this frozenset and require no key change.

## Design decisions
Prefix format mirrors the existing `eventbus/*.md` subfolder keys already present in
the same frozenset (e.g. `eventbus/ack-nack-endpoints.md:'Bad Request Responses' <->
'Bad Request Responses'`) — no new key format is introduced.

## Alternatives considered
- Rewriting the test to compute expected keys dynamically from `discover_md_files()`
  output instead of a static frozenset: rejected — out of scope for this row; the
  frozenset's purpose (per its own docstring/usage in this test) is to pin a known-good
  baseline and flag any content-similarity drift, which a dynamically computed
  expectation would not do.

## Implementation
### Target file
`tests/tools/test_check_docs_quality.py`

### Procedure
1. Locate the `EXPECTED_WITHIN_FILE_PAIRS: frozenset[str] = frozenset([...])` literal.
2. Replace each of the following 10 keys (prefixed `00_governance_01_documentation-policy.md:`):
   - `'Agent' <-> 'EventBus'`
   - `'Agent' <-> 'Shared/DB'`
   - `'EventBus' <-> 'Shared/DB'`
   - `'MCP' <-> 'Agent'`
   - `'MCP' <-> 'EventBus'`
   - `'MCP' <-> 'Shared/DB'`
   - `'RAG' <-> 'Agent'`
   - `'RAG' <-> 'EventBus'`
   - `'RAG' <-> 'MCP'`
   - `'RAG' <-> 'Shared/DB'`

   with the same suffix, prefixed `00_governance/00_governance_01_documentation-policy.md:`
   instead of `00_governance_01_documentation-policy.md:`.
3. Replace each of the following 2 keys (prefixed
   `00_governance_03_issue-and-uncertainty-management.md:`):
   - `'CI-009' <-> 'CI-012'`
   - `'Lifecycle' <-> 'Lifecycle'`

   with the same suffix, prefixed
   `00_governance/00_governance_03_issue-and-uncertainty-management.md:` instead of
   `00_governance_03_issue-and-uncertainty-management.md:`.
4. Leave every other key in the frozenset unchanged.

### Method
Direct text edit of the 12 string literals inside the `EXPECTED_WITHIN_FILE_PAIRS`
frozenset definition — no logic change to the test file's comparison assertion
(`assert current_pairs == EXPECTED_WITHIN_FILE_PAIRS`) or to any other test class in
this file.

### Details
- Preserve the existing inline `# 00_governance_01_documentation-policy.md` /
  `# 00_governance_03_issue-and-uncertainty-management.md` grouping comments above each
  key block — update their text to include the `00_governance/` prefix for consistency
  with the keys they annotate, but this is a comment-only change with no test-behavior
  effect.
- Do not reorder keys relative to the rest of the frozenset unless required to keep the
  file's existing alphabetical/grouped ordering convention.
- This row assumes seq 01 and seq 03 (the `git mv` of `00_governance_01_documentation-policy.md`
  and `00_governance_03_issue-and-uncertainty-management.md`) have landed before this
  test is run — the assertion at the end of this test class also checks that
  `"00_governance_01_documentation-policy.md"` and
  `"00_governance_04_documentation-checks.md"` appear as substrings in the tool's
  output; both remain valid substring matches of the folder-qualified path
  (`00_governance/00_governance_01_documentation-policy.md`), so no change is needed to
  that assertion.

## Compatibility considerations
`tools/check_docs_quality.py`'s `discover_md_files()` already builds `rel_path` via
`docs_dir.rglob("*.md")` and `str(p.relative_to(docs_dir))`, so it will report the new
folder-qualified `rel_path` values automatically once the governance files are moved —
no change to `tools/check_docs_quality.py` itself is required by this row.

## Security considerations
N/A: a test-fixture key rename carries no security-relevant surface.

## Rollback considerations
Revert the 12 key edits (and the 2 grouping-comment edits) via `git checkout --
tests/tools/test_check_docs_quality.py`, or `git revert` the commit containing this
change if already committed. A rollback of this row without also reverting seq 01/03's
moves would make `uv run pytest tests/tools/test_check_docs_quality.py -q` fail again
(keys would no longer match `discover_md_files()`'s post-move output) — coordinate any
rollback with seq 01/03.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_quality.py -q` passes with the updated
  `EXPECTED_WITHIN_FILE_PAIRS` (Plan `AC-2`).
- `uv run python -m tools.check_docs_quality` passes or reports only pre-existing,
  unrelated findings (Plan `AC-4`).

## Completion criteria
All 12 governance-file keys in `EXPECTED_WITHIN_FILE_PAIRS` carry the `00_governance/`
prefix; no other key in the frozenset is changed; the test module's own comparison
assertion and the governance-cross-file substring assertion both pass against the
moved repository tree.

## Out of scope
Any key referencing `00_governance_02_documentation-metadata.md`,
`00_governance_04_documentation-checks.md`, or `00_index.md` (zero existing entries,
none needed); any change to `tools/check_docs_quality.py`; any change to the 5 moved
docs files themselves (covered by seq 01-05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Prefix the 12 `EXPECTED_WITHIN_FILE_PAIRS` keys with `00_governance/` | Completed | 20260924-122641 | 20260924-122641 | Prefixed all 12 EXPECTED_WITHIN_FILE_PAIRS keys with 00_governance/. ruff format/check and mypy pass clean. |
| 2 | N/A: this row is itself a test-fixture update, not new test coverage | Completed | 20260924-122641 | 20260924-122641 | N/A: this row is itself a test-fixture update, not new test coverage. |
| 3 | Run `uv run pytest tests/tools/test_check_docs_quality.py -q` and `uv run python -m tools.check_docs_quality` | Completed | 20260924-122641 | 20260924-122641 | uv run pytest tests/tools/test_check_docs_quality.py -q: 20 passed. Confirms EXPECTED_WITHIN_FILE_PAIRS matches actual post-move discover_md_files() output exactly (12 keys, not 13 as the source Issue originally stated). |
| 4 | N/A: no documentation update beyond the test fixture itself | Completed | 20260924-122641 | 20260924-122641 | N/A: no docs/00_index.md task-scope mapping for a tests/tools/*.py fixture file. |

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
- **Requirement ID**: `REQ-002` (update `EXPECTED_WITHIN_FILE_PAIRS` keys for the
  folder-qualified path)
- **Source issue**: issues/20260923-140944_docsreorg05_move-governance-docs-into-new-governance-folder.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-115855_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121124
- **Related target files**: tests/tools/test_check_docs_quality.py