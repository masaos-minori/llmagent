## Goal

- Add removed-name patterns for `_TOKEN_PRINCIPAL_MAP`, `principal_map`, and `_populate_token_maps` to `tools/check_compat_shims.py` `COMPAT_PATTERNS` so reintroduction fails CI (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- Checker-config extension only; the final checker-configuration consolidation stays with compatrm004 (Plan Out-of-Scope). Part of the Plan's single atomic Phase 1 cutover so the first checker run after the commit is clean.

## Assumptions

- Mechanism verified 2026-11-07 at HEAD `1a13653e8`: `COMPAT_PATTERNS` dict at line 39, closing brace at line 115, with the approval-stage precedent entries at 62-70 (`r"\bapproval_ops\b"` style); `tests/tools/test_check_compat_shims.py` iterates `COMPAT_PATTERNS` generically (line 550 region) and pins only the approval-stage subset (sample data lines 88-93) — adding entries needs no test-file edit (Plan Background).
- Scan corpus: `scripts/`, `docs/`, `tests/`, `tools/` `.py`+`.md` (checker main, lines 665-679). Exceptions manifest already covers the two unavoidable literal homes: `check-compat-shims-source` (`tools/check_compat_shims.py`) and `check-compat-shims-test-data` (`tests/tools/test_check_compat_shims.py`) in `tools/compat_exceptions.toml` — no new exception entry is required (Plan Design "Removed-name protection").

## Design decisions

- Three new entries appended after the approval-stage block, same naming convention `<name> (reason)`:
  - `"_TOKEN_PRINCIPAL_MAP (eventbus auth compat state removed)": r"\b_TOKEN_PRINCIPAL_MAP\b"`
  - `"principal_map (eventbus auth compat state removed)": r"\bprincipal_map\b"`
  - `"_populate_token_maps (eventbus auth compat state removed)": r"\b_populate_token_maps\b"`
- Word-boundary semantics verified against the codebase: `\bprincipal_map\b` does not match `_build_principal_map` (underscore is a word character, so no boundary between `_` and `p`) and does not match the new helpers `current_principals` (new)/`publish_derived_generation` (new); `auth._TOKEN_PRINCIPAL_MAP` does match (dot boundary).

## Alternatives considered

- Exception allowlist entries for the checker and its test data: rejected — both files already carry manifest exceptions (Assumptions), and the Plan forbids new entries once all references are deleted.

## Implementation
### Target file
`tools/check_compat_shims.py`

### Procedure
1. Insert the three entries (above) into `COMPAT_PATTERNS`, appended at the end of the dict just before its closing brace (line 115), keeping the approval-stage block (62-70) contiguous.
2. No change to `tools/compat_exceptions.toml`.
3. No change to `tests/tools/test_check_compat_shims.py` (generic iteration verified; approval-subset pins at 88-93 untouched).

### Method
- After Phase 1 lands, the only remaining literals of the three names in the scan corpus are the pattern strings in this file and this procedure's validation text in test data — both already exempted (Assumptions).

### Details
- Entries are plain regex strings; no code-path changes in the checker.

## Compatibility considerations

- Overlap with plan003 (recorded compatible in the Plan Assumptions): both plans only append `COMPAT_PATTERNS` entries; non-contradictory appends, consolidated by compatrm004. Plan002 appends its three; plan003 will append its own later.
- Ordering constraint: this file's new patterns only stay clean once every reference deletion (documents 01-14, 18) is in the same commit — enforced by the atomic Phase 1 rule.

## Security considerations

- N/A: static CI check.

## Rollback considerations

- Revert of the single atomic commit removes the three entries (Plan Design "Atomicity").

## Validation plan

- `uv run python tools/check_compat_shims.py` — clean after Phase 1 (AC-007); reintroducing any name makes it fail.
- `uv run pytest tests/tools/test_check_compat_shims.py` green with the added entries (Plan Validation row 3).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- The compatibility checker rejects reintroduction of the three removed names (AC-007) with zero findings on the post-cutover tree (AC-001).

## Out of Scope

- Checker-configuration consolidation — compatrm004 (Plan Out-of-Scope).
- Any new `tools/compat_exceptions.toml` entry — none needed (Design).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the three `COMPAT_PATTERNS` entries — Plan Phase 1 | Pending | — | — | clean only with all reference deletions in the same commit |
| 2 | Run the validation sequence (`rules/toolchain.md`) in the Plan Phase 3 pass | Pending | — | — | |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063003_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-083645
- **Related target files**: `tools/check_compat_shims.py`
