## Goal
Pin the new COMPAT semantics with regression tests in the checker's own test file: capitalized/lowercase/uppercase fixture pairs match, `_MCP_TOOLS` matches only the token form and not longer identifiers, and the 84-entry pattern inventory is pinned (`REQ-001`/`REQ-003`/`REQ-005`).

## Scope
**Release unit**: wfaudit012-full

- Covers Plan `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md` row 2 only: `tests/tools/test_check_compat_shims.py`.

## Assumptions
- Procedure 01 (`implementations/20261108-190836_01_tools_check_compat_shims.py.md`) lands in the same change unit: the new fixtures assert the `re.IGNORECASE` semantics and the `\b_MCP_TOOLS\b` pattern string, both of which exist only after that edit.
- Procedures 03-09 and `wfaudit008` land in the same change unit: the existing `TestProductionCategoryZero::test_real_repo_manifest_passes` runs the checker against the live repository and asserts exit code 0, so the file's suite is red while any census finding is open (verified 2026-11-08: 19 findings with the flip alone).
- Fixture text quoting removed names stays invisible to repository scans because `tests/tools/test_check_compat_shims.py` is a `fixture`-category exemption (`check-compat-shims-test-data` in `tools/compat_exceptions.toml`).

## Design decisions
- New COMPAT-semantics tests go in the existing `TestPatternDetection` class (L48-132) and call `check_compat_patterns(...)` on synthetic content, the way `test_clean_file_has_no_matches` (L122-126) does. Tests that call `re.search(pattern, text)` directly — `test_mdq_command_pattern_matches_command_form_only` (L81-85), `test_approval_gate_patterns_match_removed_names_only` (L111-120) — stay case-sensitive by construction and must not be reused for case semantics: they would assert the regex, not the checker's matching path.
- Case-semantics fixtures use both a capitalized and a lowercase spelling of the same pattern in one parametrized case list, so a future flip back to case-sensitive matching fails with a named case rather than a silent drop.
- The inventory pin asserts `len(COMPAT_PATTERNS) == 84` plus the `_MCP_TOOLS` entry's anchored pattern string, rather than snapshotting all 84 names: the count catches accidental add/remove, the pinned string pins the anchor, and a full-name snapshot would make every deliberate future pattern change a two-file edit (the removal path in `plans/20261107-064415_plan.md` adds names in one file).

## Alternatives considered
- One new top-level test class for case semantics: rejected — `TestPatternDetection` is the existing home for pattern-detection fixtures and keeps the file's per-stage class layout (the file already has 18 stage-scoped classes).
- Assert findings by exact message text: rejected — message text is not part of the contract (the procedure 01 edit leaves it unchanged by choice); assertions count findings and check the pattern name.
- Adding a fixture file under `tmp_path` and running `main()`: rejected for these tests — `TestDocSymbolStage` and `TestProductionCategoryZero` already cover stage wiring, and `main()`-level tests would not isolate the matching semantics.

## Implementation
### Target file
`tests/tools/test_check_compat_shims.py`

### Procedure
Add four test methods to `TestPatternDetection` after `test_allowlisted_file_skipped` (L128-132): `test_case_variant_forms_flagged` (new), `test_mcp_tools_token_form_flagged` (new), `test_mcp_tools_identifier_substrings_not_flagged` (new), `test_compat_pattern_inventory_pinned` (new). No existing test is edited.

### Method
- `test_case_variant_forms_flagged` (new): parametrized over `(line, pattern_name)` pairs — `Backward-compatible alias for _notify_threshold_breach.` and `backward-compatible alias` and `BACKWARD-COMPATIBLE` against `backward-compatible keyword`; `Re-export stub for models.` and `RE-EXPORT STUB` against `re-export stub phrase`; `Backward Compatibility Layer` against `backward compatibility layer`; `Workflow MODE=disabled` against `Workflow mode=disabled log`. Each case builds `content = line + "\n"`, calls `check_compat_patterns(content, Path("scripts/sample.py"), set())`, and asserts one finding whose message contains the expected pattern name.
- `test_mcp_tools_token_form_flagged` (new): fixture lines `_MCP_TOOLS = []`, `hasattr(m, "_MCP_TOOLS")`, `assert not hasattr(mod, "_MCP_TOOLS")`, and the lowercase quoted token `"_mcp_tools"`; each must produce a `backward compatibility leftover` finding naming `_MCP_TOOLS`.
- `test_mcp_tools_identifier_substrings_not_flagged` (new): fixture lines `async def _cmd_mcp_tools(self) -> None:`, `await self._cmd_mcp_tools()`, `"_cmd_mcp_tools",`, `See also tests/test_mcp_tools_validation.py (requirement 14) for a broader-server,` and `def test_empty_mcp_tools_attribute_missing_returns_empty_list(self) -> None:` — the real HEAD lines that produced false positives in the 2026-11-08 census; each must return no finding.
- `test_compat_pattern_inventory_pinned` (new): asserts `len(COMPAT_PATTERNS) == 84` and `COMPAT_PATTERNS["_MCP_TOOLS"] == r"\b_MCP_TOOLS\b"`.

### Details
- The file already imports `COMPAT_PATTERNS` and `check_compat_patterns` (L16-30), and `Path` (L11) — no new imports.
- Fixtures in `test_case_variant_forms_flagged` (new) are single-line so the historical-context and section-scope logic of other stages cannot interfere.
- The lowercase quoted-token case is intentional: after the flip, a lowercase spelling of the retired name is a finding, matching `REQ-001`.

## Compatibility considerations
- This test file is the gate that keeps the strict semantics from drifting back to case-sensitive matching, so it must land with procedure 01 (a passing test suite is what makes the strict gate safe for every future commit).
- No existing fixture or class is renamed, so other suites that import nothing from this file are unaffected.

## Security considerations
- Tests write only under pytest's `tmp_path` or use in-memory strings; no repository file is written and no subprocess is added beyond the existing repo-run tests.

## Rollback considerations
- Revert the commit: the four new methods disappear with no state to unwind. Rolling back only this file while keeping procedure 01 leaves the checker strict but unpinned — acceptable short-term, and recorded as a rollback ordering note in procedure 01.

## Validation plan
- Red-on-HEAD gate: run `uv run pytest tests/tools/test_check_compat_shims.py -q` on HEAD first — `test_case_variant_forms_flagged` (new), `test_mcp_tools_token_form_flagged` (new) (its quoted lowercase-token case), and `test_compat_pattern_inventory_pinned` (new) (its anchored-pattern assertion) must fail (`REQ-005`). `test_mcp_tools_identifier_substrings_not_flagged` (new) is green on HEAD by design: it is the guard that keeps the false-positive suppression in place after the flip, and its mutation gate is the anchor removal below.
- After procedure 01 lands: the same command shows those three green; the whole file stays green only after procedures 03-09 and `wfaudit008` land, because `TestProductionCategoryZero::test_real_repo_manifest_passes` requires a clean strict run.
- Mutation spot checks: temporarily remove `re.IGNORECASE` at `tools/check_compat_shims.py` L631, or remove the `\b` anchors at L79, and confirm the named tests fail; restore the file (`git checkout -- tools/check_compat_shims.py`) and re-run to confirm green.
- `uv run ruff check tests/tools/test_check_compat_shims.py` and `uv run pytest tests/tools/ -q`, then full `uv run pytest tests/ -q` per `rules/toolchain.md`.

## Completion criteria
- Four new tests present in `TestPatternDetection`, all green with procedure 01 applied; the three case/inventory tests demonstrably red on HEAD; no existing test modified.

## Out of Scope
- Tests for the removed-names stage, the ADR stage, and the doc-symbol stage (unchanged behavior).
- Tests for any exemption mechanism (`REQ-002`: none is added).
- Editing existing fixtures, including the case-sensitive `re.search`-based parametrizations.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-090314 | 20261109-090314 | four new methods in `TestPatternDetection` |
| 2 | Add or update tests per Validation plan | Completed | 20261109-090314 | 20261109-090314 | this document is the test procedure |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-101318 | 20261109-101318 | green only with procedures 03-09 and `wfaudit008` landed STEP 3: per-member validators + targeted tests pass; diff-cover 100%; census 0 findings. End-of-unit full suite has 28 pre-existing eventbus failures (verified on clean HEAD, unrelated to unit); user approved proceeding. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-090314 | 20261109-090314 | no doc edit in scope; `tools/TOOL_DESCRIPTIONS.md` is procedure 01 N/A: no doc edit in scope |

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
- **Requirement ID**: `REQ-001`, `REQ-003`, `REQ-005`
- **Source issue**: `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-190836
- **Related target files**: `tests/tools/test_check_compat_shims.py`; companion `tools/check_compat_shims.py` (procedure 01, `implementations/20261108-190836_01_tools_check_compat_shims.py.md`)