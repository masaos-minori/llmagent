## Goal
Remove the two obsolete `_check_semantic_cache_threshold`/`_check_semantic_cache_max_size`
check tests, update tests whose behavior changes under the new removed-key check, and
add tests asserting `RagConfigValidator.validate()` returns an error containing a
migration message for each/all of the three removed keys
(`tests/shared/test_config_validator.py`) (`REQ-003`, `REQ-009`).

## Scope
- **In-Scope**:
  - Delete `test_semantic_cache_threshold_low_warning` (lines 32-39) and
    `test_semantic_cache_threshold_normal_no_warning` (lines 41-47) in their entirety —
    both test the removed `_check_semantic_cache_threshold()` warning behavior, which
    no longer exists (replaced by a hard error on mere key presence, not a
    value-dependent warning).
  - Rewrite `test_multiple_errors` (lines 49-60): the `"semantic_cache_threshold":
    0.2` case now produces an *error* (key presence), not a warning (value
    threshold) — update the fixture's expectation to `result.ok is False`, `len(result.errors)
    == 1`, `len(result.warnings) == 1` (only the `use_rrf=False` warning remains).
  - Rewrite `test_flat_shape_uses_root_dict` (lines 66-75): same fixture, same
    corrected expectation as `test_multiple_errors`, applied to the flat-shape input.
  - Rewrite `test_flat_config_negative_max_size_error` (lines 77-87): the removed-key
    check fires on *presence*, not on the value being negative — rename to reflect
    this (e.g. `test_flat_config_semantic_cache_max_size_present_error`) and update
    the value to a non-negative one (e.g. `100`) to prove the check does not depend on
    the value's sign, only the key's presence; update the expected error message to
    match the new migration-message wording (procedure document `05`'s Design
    decisions).
  - Delete `test_flat_config_max_size_zero_no_error` (lines 89-96) in its entirety —
    its entire premise ("zero is not negative, so no error") is inverted by the new
    check (any presence is an error, regardless of value); no adapted version of this
    test is meaningful.
  - Rewrite `test_nested_config_negative_max_size_error` (lines 107-117): same
    correction as `test_flat_config_negative_max_size_error`, applied to the nested
    (`{"rag": {...}}`) input shape.
  - Add new tests: `test_use_semantic_cache_present_error` (key alone, any value,
    produces an error naming it); `test_semantic_cache_threshold_present_error` (same,
    for that key alone); `test_all_three_removed_keys_produce_one_combined_error`
    (all three keys present together produce exactly one error entry naming all
    three, not three separate error entries — per procedure document `05`'s Design
    decisions choosing a single combined message).
- **Out-of-Scope**: `test_ok_no_errors`, `test_use_rrf_false_warning`,
  `test_use_rrf_true_no_warning`, `test_no_rag_key`,
  `test_flat_config_use_rrf_false_warning` — confirmed unrelated to the three removed
  keys by reading each; `setup_method` — confirmed unrelated.

## Assumptions
- `RagConfigValidator._check_removed_semantic_cache_keys()` (procedure document `05`)
  returns a single combined error message naming every removed key found, appended
  once to `result.errors` — this document's new
  `test_all_three_removed_keys_produce_one_combined_error` test directly depends on
  that design choice; if procedure document `05`'s implementer instead chooses a
  per-key error list, this test's `len(result.errors) == 1` assertion must become
  `== 3` and its message-content assertions adjusted accordingly — flagged here as a
  dependency on that document's exact implementation choice, not assumed silently.
- The exact migration-message wording (procedure document `05`'s Design decisions:
  `"Configuration key(s) {keys} are no longer supported — the semantic cache feature
  was removed ...; remove {keys} from your configuration."`) is used verbatim in this
  document's new/rewritten tests' message-content assertions (e.g. `assert
  "no longer supported" in result.errors[0]` and `assert "use_semantic_cache" in
  result.errors[0]`, checking substrings rather than the full message, so a minor
  wording change during procedure document `05`'s implementation does not require
  re-deriving this document's assertions from scratch).

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Prefer substring assertions (`"use_semantic_cache" in result.errors[0]`) over exact
  full-message equality in both rewritten and new tests — the message's exact
  wording is an implementation detail of procedure document `05`, not a contract this
  test file should over-specify; the *presence* of the key name and a
  human-readable "no longer supported"/"removed" signal is what matters for `AC-7`.
- Retain the negative-value framing in `test_flat_config_negative_max_size_error`'s
  renamed successor by using a non-negative substitute value, rather than deleting it
  outright — the test still meaningfully proves the check does not accidentally
  depend on the value's sign (a plausible implementation bug: e.g. reusing the old
  `_check_semantic_cache_max_size()`'s `< 0` condition by mistake instead of a
  presence check).

## Alternatives considered
- Deleting `test_flat_config_negative_max_size_error`/`test_nested_config_negative_max_size_error`
  outright instead of rewriting with a non-negative value — rejected: rewriting
  preserves a meaningful regression guard (presence-not-value-triggered) that a
  simple deletion would lose.

## Implementation
### Target file
`tests/shared/test_config_validator.py`

### Procedure
1. Delete `test_semantic_cache_threshold_low_warning` (lines 32-39) and
   `test_semantic_cache_threshold_normal_no_warning` (lines 41-47).
2. Rewrite `test_multiple_errors`: keep the same input fixture; change the
   assertions to `assert result.ok is False`, `assert len(result.errors) == 1`,
   `assert len(result.warnings) == 1`; add `assert "semantic_cache_threshold" in
   result.errors[0]` and `assert "use_rrf" in result.warnings[0]` (or equivalent
   content checks).
3. Rewrite `test_flat_shape_uses_root_dict` the same way as step 2, applied to its
   flat-shape input.
4. Rewrite `test_flat_config_negative_max_size_error` → rename to
   `test_flat_config_semantic_cache_max_size_present_error`; change the fixture value
   from `-1` to `100` (non-negative); change assertions to `assert result.ok is
   False`, `assert len(result.errors) == 1`, `assert "semantic_cache_max_size" in
   result.errors[0]`.
5. Delete `test_flat_config_max_size_zero_no_error` (lines 89-96) in its entirety.
6. Rewrite `test_nested_config_negative_max_size_error` the same way as step 4,
   applied to its nested-shape input.
7. Add `test_use_semantic_cache_present_error`: `self.validator.validate({"rag":
   {"use_semantic_cache": True}})` → `assert result.ok is False`; `assert
   "use_semantic_cache" in result.errors[0]`.
8. Add `test_semantic_cache_threshold_present_error`: `self.validator.validate({"rag":
   {"semantic_cache_threshold": 0.92}})` (a value that would have produced no
   warning under the old check) → `assert result.ok is False`; `assert
   "semantic_cache_threshold" in result.errors[0]` — proves the new check fires
   regardless of the old check's now-irrelevant "unusually low" threshold logic.
9. Add `test_all_three_removed_keys_produce_one_combined_error`:
   `self.validator.validate({"rag": {"use_semantic_cache": True,
   "semantic_cache_threshold": 0.92, "semantic_cache_max_size": 100}})` → `assert
   result.ok is False`; `assert len(result.errors) == 1`; `assert
   "use_semantic_cache" in result.errors[0]`; `assert "semantic_cache_threshold" in
   result.errors[0]`; `assert "semantic_cache_max_size" in result.errors[0]` (per
   Assumptions — adjust count/structure if procedure document `05` implements
   per-key errors instead of one combined message).

### Method
Direct `Edit`: two whole-test deletions, four test rewrites (rename + fixture +
assertion changes), three new test additions.

### Details
- Confirm `RagConfigValidator._check_removed_semantic_cache_keys()`'s actual return
  shape (single combined string vs. list) by reading procedure document `05`'s
  landed implementation before writing steps 7-9's assertions — do not assume the
  combined-message design holds without checking the actual code, per this document's
  own Assumptions caveat.
- Confirm after editing: `rg -n "semantic_cache"
  tests/shared/test_config_validator.py` still matches — this file's remaining
  content deliberately references the removed key names as the *subject* of the
  rejection tests (per Out of Scope discipline, these matches are expected and
  correct, unlike other procedure documents in this Plan where a zero-match result is
  the goal).

## Compatibility considerations
N/A: test-only file; no production caller depends on it.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure document `05` (`RagConfigValidator`).

## Validation plan
- `uv run pytest tests/shared/test_config_validator.py -v` — all tests pass,
  including the three new tests and four rewritten tests.
- Manually confirm the rewritten/new tests' assertions match procedure document `05`'s
  actual implemented message format (see Details).

## Completion criteria
- `RagConfigValidator`'s two removed checks (`_check_semantic_cache_threshold`,
  `_check_semantic_cache_max_size`) have no remaining test asserting their old
  value-dependent behavior (Plan `AC-5`).
- `RagConfigValidator().validate()` is proven, by test, to return an error containing
  a migration message for each of the three removed keys individually and in
  combination (Plan `AC-7`).

## Out of scope
- `scripts/shared/config_validator.py`'s implementation itself (procedure document
  `05`).
- `test_ok_no_errors`, `test_use_rrf_*`, `test_no_rag_key` — unrelated,
  untouched.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document's Implementation IS the test rewrite/addition |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-003` (remove the two obsolete check tests; add rejection-message tests)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/shared/test_config_validator.py
