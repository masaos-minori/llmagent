## Goal

- Replace the stale "ADR-02.05 REQ-004" comment at `tools/generate_reference_table.py` line 559 with a citation of the current normative source per the Plan (`REQ-021`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the comment-only edit in the `_db_schema_version_entries` function (line 559).
- Out of scope: the function's logic and any generated manifest content (`REQ-022`: generated artifacts must not change from a comment edit).

## Assumptions

- Verified 2026-11-19: line 559 of `tools/generate_reference_table.py` reads `# No PRAGMA user_version stamp required (ADR-02.05 REQ-004): stamp-less` — a stale citation.
- Line 53 of `docs/10_adr/adr_01_index.md` numbers this ADR as `ADR-008` ("Separating SQLite into Six Databases"), and the ADR body contains no "REQ-004" stamp requirement.
- The current normative statement for the stamp-less rule is the no-migration/no-version-stamping policy in `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` line 117 ("Automatic migration and version stamping are not supported for any domain").

## Design decisions

- New comment text cites `ADR-008` and the db_07 no-version-stamping policy (the current specification), matching the citation style already used in the file's comments. Comment wording only; the code path (`_PRAGMA_USER_VERSION_RE` search, "unversioned" fallback) is untouched.

## Alternatives considered

- Delete the citation entirely and keep a plain comment — rejected: `REQ-021` requires citing the current normative ADR/requirement, not removing traceability.

## Implementation
### Target file
`tools/generate_reference_table.py`
### Procedure
1. Rewrite the line 559 comment to: "No PRAGMA user_version stamp required (ADR-008 no-migration policy; see docs/41_db/db_07_api_and_operations-recovery-and-reference.md): stamp-less" (final wording may wrap; content must cite ADR-008 and the current db_07 policy).
2. Confirm the diff is comment lines only.
3. Run the drift gate and the tool's tests.

### Method
- Comment-only change; validated by the `--check` drift gate passing with unchanged manifests (`AC-16`, `T14`).

### Details
- No other comment in the file references the stale `ADR-02.05 REQ-004` anchor (grep `ADR-02.05` verified 2026-11-19: this is the only occurrence in `tools/`).

## Compatibility considerations

- Generated artifacts (`registry/manifests/*.yaml`) must be byte-identical after the edit; the `--check` gate enforces this (`REQ-022`).
- Consumers: `tools/test_generate_reference_table.py` (`tests/tools/test_generate_reference_table.py`) covers the tool's behavior; no behavior change, so no test changes.

## Security considerations

- N/A: comment-only change.

## Rollback considerations

- Single-commit revert of the comment.

## Validation plan

- `uv run python tools/generate_reference_table.py --check` — exit 0 (`AC-16`, `T14`).
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — green.
- `git diff` shows comment lines only.
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- `AC-15`/`AC-16` hold: the file contains no stale reference comment, the citation names ADR-008 and the current db_07 policy, and the drift gate passes.

## Out of Scope

- The registry rows (seq 03) and adr_authority changes (seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the stale comment at line 559 (`REQ-021`) | Pending | — | — | |
| 2 | Run `generate_reference_table.py --check` and its tests | Pending | — | — | |

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
- **Requirement ID**: `REQ-021` (stale ADR reference comment), `REQ-022` (generated artifacts untouched, drift gates pass)
- **Source issue**: issues/20261117-123010_adrchk010_canonical-registry-checkers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-115842_adrchk010_canonical-registry-checkers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-19 13:48:55
- **Related target files**: `tools/generate_reference_table.py`
