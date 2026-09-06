## Goal
Add `tests/tools/test_check_canonical_source_registry.py`: unit tests for
`tools/check_canonical_source_registry.py` (seq 02) covering REQ-008's six cases,
built against seq 02's actual schema decision, not this Plan's originally-proposed
one (REQ-008).

## Scope
- In scope: new file `tests/tools/test_check_canonical_source_registry.py` only,
  covering: valid-registry pass; missing-source-path failure;
  `source_paths`-length-violation-on-a-single-source-claim-type failure (REQ-008's
  "`sources`-on-a-single-source-claim-type failure", reinterpreted per seq 02's
  schema); non-Accepted-ADR failure; unrecognized-claim-type failure;
  schema-version-mismatch handling.
- Out of scope: `tools/check_canonical_source_registry.py`'s own implementation
  (seq 02); `tools/check_canonical_source_conflicts.py` and its own test file
  (`tests/tools/test_check_canonical_source_conflicts_routing.py`, pre-existing,
  unrelated to this row).

## Assumptions
- **Schema decision inherited from seq 02** (`implementations/20260906-150039_02_tools_check_canonical_source_registry.py.md`):
  tests target `RegistryEntry(decision_target, claim_type, source_paths: list[str],
  area, notes=None)` and `CanonicalSourceRegistry(version, entries: list[RegistryEntry])`,
  not the Plan's originally-proposed nested `source`/`sources`-split schema. The
  "`sources`-on-a-single-source-claim-type failure" case (REQ-008) is tested as:
  a `source_paths` list with 2+ entries on a claim type other than
  `runtime-behavior` must fail; the same list with 2+ entries on
  `claim_type="runtime-behavior"` must pass.
- **Schema-version-mismatch case**: since the actual registry file has no `version`
  field until seq 01 lands (adding `version = "1"`), this test constructs a registry
  fixture with an unsupported/missing version value directly (in-memory, not reading
  the real file) and asserts `load_registry()`/`validate_registry_schema()` reports
  an error rather than silently accepting an unversioned or wrong-version registry.
- Tests use in-memory `CanonicalSourceRegistry`/`RegistryEntry` fixtures constructed
  directly in Python, plus `tmp_path`-based temporary TOML files only where exercising
  `load_registry()`'s file-parsing path itself (matching this file's sibling
  `tests/tools/test_check_canonical_source_conflicts_routing.py`'s in-memory-fixture
  convention, which does not touch the filesystem, and `test_check_docs_structure.py`'s
  convention for tests that do need a real file — confirm the latter's exact pattern
  at implementation time since it was not re-read this cycle).
- The ADR-status-check test needs a real (or `tmp_path`-constructed) file with a
  `## Status` section — reuse the confirmed format from
  `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` (`## Status` heading,
  blank line, then the status word) rather than inventing a different ADR-file shape.

## Design decisions
- Mirror `tests/tools/test_check_canonical_source_conflicts_routing.py`'s existing
  structure: one test class per concern (e.g. `TestLoadRegistry`,
  `TestPathExistence`, `TestSourcePathsEnforcement`, `TestAdrStatusCheck`,
  `TestClaimTypeValidation`, `TestSchemaVersion`), a small fixture-builder helper
  function (mirroring that file's `_entry()` helper) for constructing
  `RegistryEntry`/`CanonicalSourceRegistry` instances tersely per test.
- Use `tmp_path` (pytest's built-in fixture) for tests needing a real file on disk
  (path-existence checks, ADR-status checks reading a real `## Status` section,
  `load_registry()`'s TOML-parsing path) rather than mocking the filesystem —
  matches this repository's general test convention of using real temporary files
  for file-system-touching code (already observed in `tests/db/test_rag_consistency.py`'s
  in-memory-SQLite convention for a different kind of file-backed test).

## Alternatives considered
- Test only `validate_registry_schema()` with pre-built `CanonicalSourceRegistry`
  objects, skipping `load_registry()`'s own TOML-parsing correctness: rejected — the
  Plan's REQ-008 explicitly requires the six cases as end-to-end tool behavior
  (AC8/AC11 reference running the tool, not only its schema-checking internals);
  at least one test must exercise `load_registry()` against a real `tmp_path` TOML
  file to confirm the array-of-tables parsing itself works.

## Implementation
### Target file
`tests/tools/test_check_canonical_source_registry.py`

### Procedure
1. Re-confirm seq 02's actual landed function/dataclass names immediately before
   writing imports (this document assumes `RegistryEntry`, `CanonicalSourceRegistry`,
   `load_registry`, `validate_registry_schema` — adjust import names to match
   whatever seq 02 actually implements if it diverges from its own procedure
   document).
2. Add a `_entry(...)` fixture-builder helper (matching the sibling test file's
   `_entry()` pattern) with sensible defaults for `decision_target`, `claim_type`,
   `source_paths`, `area`.
3. `TestValidRegistryPass`: a registry with the actual 2 illustrative entries (or
   equivalent fixtures) and a supported `version` passes `validate_registry_schema()`
   with zero errors.
4. `TestMissingSourcePath`: an entry whose `source_paths` contains a path that does
   not exist on disk (a `tmp_path`-relative nonexistent file) fails with an error
   naming that path.
5. `TestSourcePathsEnforcement`: an entry with `claim_type != "runtime-behavior"` and
   `len(source_paths) > 1` fails; the same shape with
   `claim_type == "runtime-behavior"` passes.
6. `TestAdrStatusCheck`: an entry with `claim_type == "architecture-decision"`
   pointing to a `tmp_path`-constructed file with `## Status\n\nAccepted` passes; the
   same pointing to a file with `## Status\n\nDraft` (or any non-`Accepted` value)
   fails.
7. `TestClaimTypeValidation`: an entry with a claim type outside `M-01-01`'s 13
   defined types fails; each of the 13 valid types individually passes (or a
   representative subset, per this repository's existing parametrize convention).
8. `TestSchemaVersion`: a registry missing `version` entirely, and one with an
   unsupported version value, both fail; the currently-supported version value
   passes.

### Method
Confirmed this cycle (2026-09-06) via direct read of
`tests/tools/test_check_canonical_source_conflicts_routing.py` (full file, its
class-per-concern + `_entry()` helper + `pytest.mark.parametrize` conventions) and
`ls tests/tools/` (confirms `test_check_*.py` naming convention already followed by
19 sibling files). Confirmed via read of seq 01/seq 02's procedure documents
(`implementations/20260906-150039_01_...md`, `implementations/20260906-150039_02_...md`)
that this row must target seq 02's actual schema, not the Plan's original proposal.

### Details
No change to any existing test file.

## Compatibility considerations
N/A: new test file, no existing test affected.

## Security considerations
Test fixtures must not reference paths outside the test's own `tmp_path` sandbox
when constructing a "missing path" case, to avoid accidentally depending on
repository-external state.

## Rollback considerations
New file — revert via `git rm tests/tools/test_check_canonical_source_registry.py`
if seq 02's actual implementation diverges enough from this document's assumptions
to need a substantially different test structure.

## Validation plan
- `uv run pytest tests/tools/test_check_canonical_source_registry.py -v` — all 6
  REQ-008 cases pass.
- `uv run pytest tests/tools/test_check_canonical_source_conflicts_routing.py -v` —
  regression check, confirms this new file's additions did not disturb the sibling
  test file (no shared state expected, but verify).

## Completion criteria
- All six cases in REQ-008 have a corresponding passing test.
- Tests exercise both `load_registry()` (file-parsing) and
  `validate_registry_schema()` (schema/semantic checks), not only the latter.

## Out of scope
- `tools/check_canonical_source_registry.py`'s own implementation — tracked in
  seq 02.
- `tools/check_canonical_source_conflicts.py` and its existing test file — unrelated,
  pre-existing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20260903-103027_m0104_introduce-machine-readable-canonical-source-registry.md
- **Source plan**: plans/20260905-165405_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-150039
- **Related target files**: tests/tools/test_check_canonical_source_registry.py
