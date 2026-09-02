## Goal

Correct three stale references (Requirement REQ-003) in
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md` that describe the
empty-`branch` protected-branch bypass (and `MCP-003`) as unresolved, converting each to
a `Resolved`-format entry citing commit `800aea33e` and its verifying tests.

## Scope

Modify exactly three locations in
`docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`: the Manual Review bullet
(current line 190), the unlabeled Known Deviations "Known Issue" bullet describing the
empty-`branch` bypass (current lines 205-209), and the `MCP-003` Known Deviations bullet
(current line 210). No other line in this file — including its Decision, Rationale, or
Invariants sections — is touched.

## Assumptions

- Re-verified 2026-09-02, directly against current source:
  - `scripts/mcp_servers/git/git_service.py::_validate_protected()` (lines 130-136)
    confirms `if not branch: return False, "[DENIED] branch must not be empty"` — the
    bypass no longer exists.
  - Commit `800aea33e` ("fix: reject empty branch in `_validate_protected` to prevent
    protected-branch bypass") confirmed present in `git log`.
  - `tests/mcp_servers/git/test_git_security_compliance.py` confirms
    `test_git_push_with_empty_branch_returns_denied` (line 311),
    `test_git_pull_with_empty_branch_returns_denied` (line 327),
    `test_check_protected_branch` (line 28), and `test_is_safe_ref` (line 22) all exist.
  - The Manual Review bullet (line 190), the unlabeled Known Deviations bullet (lines
    205-209), and the `MCP-003` bullet (line 210) all match the Plan's evidence
    verbatim.
  - The `Resolved: MCP-005` precedent bullet exists at line 212:
    `- **Resolved**: MCP-005 — audit \`target\` field key-name mismatch fixed (see
    Resolution Notes).` — used as the exact format template for this row's three edits.

## Design decisions

Convert all three references to `Resolved`-prefixed bullets matching the existing
`Resolved: MCP-005` bullet's exact format (Plan `Implementation intent`) — do not invent
a new resolved-item format. Merge the two Known Deviations bullets (the unlabeled one
and `MCP-003`) into a single `Resolved` entry where they describe the same underlying
gap, since both name the empty-`branch` protected-branch bypass as their core scope.

## Alternatives considered

Deleting the three stale references outright instead of converting them to `Resolved`
entries — rejected: `rules/coding.md` Documentation notes classification and this ADR's
own Known Deviations convention (see the existing `Resolved: MCP-005` bullet) record
resolved issues as `Resolved` entries, preserving the historical record of what was
fixed and how, rather than silently deleting them.

## Implementation

### Target file

docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md

### Procedure

Reword the Manual Review bullet to `COMPLETED`, and replace the two Known Deviations
bullets describing the empty-`branch` bypass with one `Resolved`-prefixed bullet
matching the `Resolved: MCP-005` format.

### Method

1. Locate the Manual Review bullet (current line 190):
   ```
   - The protected-branch check (`_validate_protected()`) short-circuits on an empty
     `branch` argument, skipping the check entirely for that one input shape. This is a
     known, narrow gap against INV-03 (see Known Deviations) that has not been fixed;
     review before relying on protected-branch enforcement for callers that might supply
     an empty `branch`.
   ```
   Replace with:
   ```
   - The protected-branch check (`_validate_protected()`) previously short-circuited on
     an empty `branch` argument, skipping the check entirely for that one input shape —
     COMPLETED: fixed by commit `800aea33e`; `_validate_protected()` now returns
     `(False, "[DENIED] branch must not be empty")` for a falsy `branch`, verified by
     `test_git_push_with_empty_branch_returns_denied` and
     `test_git_pull_with_empty_branch_returns_denied`.
   ```
2. Locate the two Known Deviations bullets (current lines 205-210):
   ```
   - **Known Issue**: `_validate_protected()` skips the protected-branch check entirely
     when the `branch` argument is an empty string, so a call that omits `branch`
     bypasses INV-03 for that input shape.
     - **Type**: Design Gap
     - **Summary**: Protected-branch enforcement has a narrow bypass via an empty
       `branch` argument
     - **Impact**: A caller supplying an empty `branch` value is not evaluated against
       the protected-branch list
     - **Resolution Target**: Fix `_validate_protected()` to treat an empty `branch` as
       subject to the same check, or document why an empty value is always safe to
       allow
   - **Known Issue**: MCP-003 — no protected-branch/Force-Push guard; confirmed
     option-injection exploit via `branch`/`remote`.
   ```
   Replace with a single merged bullet, matching the `Resolved: MCP-005` format:
   ```
   - **Resolved**: MCP-003 / empty-`branch` protected-branch bypass — `_validate_protected()`
     previously skipped the protected-branch check entirely when `branch` was an empty
     string; fixed by commit `800aea33e`, which makes an empty `branch` return
     `(False, "[DENIED] branch must not be empty")`. Verified by
     `test_git_push_with_empty_branch_returns_denied`,
     `test_git_pull_with_empty_branch_returns_denied`, `test_check_protected_branch`,
     and `test_is_safe_ref`.
   ```

### Details

Only the three named references are reworded — the ADR's Decision, Rationale, and
Invariants sections are not modified (Plan `Implementation intent`). The `MCP-004`
Known Deviations bullet (line 211, unrelated to the empty-`branch` bypass) and the
`Resolved: MCP-005` bullet (line 212, already correct) are left untouched.

## Compatibility considerations

Documentation-only change; no code, schema, Decision, or Invariant content affected.

## Security considerations

N/A: rewording a resolved security-relevant deviation to reflect its fix has no new
security-relevant content of its own — the underlying fix (commit `800aea33e`) is
independently verified by the four cited regression tests, re-run as part of this row's
Validation plan before finalizing the wording.

## Rollback considerations

Trivially revertable via `git revert`/`git checkout` of this single file.

## Validation plan

- `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -k "empty_branch or protected_branch or safe_ref" -q`
  — all four cited tests pass, confirming the `Resolved` wording is accurate.
- `uv run python tools/check_docs_quality.py` and
  `uv run python tools/check_docs_structure.py` — no new issues for this file (AC-005).

## Completion criteria

The Manual Review bullet, the unlabeled Known Deviations bullet, and the `MCP-003`
Known Deviations bullet no longer describe the empty-`branch` bypass or `MCP-003`'s
protected-branch/option-injection scope as open; each is reworded as `Resolved` (or
`COMPLETED` for the Manual Review bullet), matching the existing `Resolved: MCP-005`
bullet's format and citing commit `800aea33e` and its verifying tests (AC-003).

## Out of scope

The `MCP-004` Known Deviations bullet (unrelated scope). Any change to
`scripts/mcp_servers/git/` or `tests/mcp_servers/git/` — the underlying fix is already
implemented and tested; this row only corrects documentation (Plan Out-of-Scope).
`docs/04_mcp_90_inconsistencies_and_known_issues.md`'s own `MCP-003` Status field —
covered by the companion plan `plans/20260901-223706_plan.md`, not this row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm `_validate_protected()` and cited test names unchanged | Pending | — | — | |
| 2 | Reword Manual Review bullet and merge the two Known Deviations bullets per Method | Pending | — | — | |
| 3 | Run cited regression tests + doc validation (`check_docs_quality.py`, `check_docs_structure.py`) | Pending | — | — | |
| 4 | N/A: no `docs/00_index.md` task-scope mapping row further requires updating beyond this file itself | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-003 (correct 3 stale empty-`branch`-bypass/`MCP-003` references to `Resolved`)
- **Source issue**: `issues/20260902-094746_h01_git_mcp_write_protection_status_contradiction.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260902-095910_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-183225
- **Related target files**: `docs/adr/ADR-012-git-mcp-server-side-write-enforcement.md`
