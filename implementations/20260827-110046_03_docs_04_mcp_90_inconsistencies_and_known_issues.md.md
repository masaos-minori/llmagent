## Goal

Narrow `MCP-003` in `docs/04_mcp_90_inconsistencies_and_known_issues.md` (REQ-003) to
its still-open scope, per `plans/20260826-113056_plan.md`.

## Scope

- In scope: the `MCP-003` entry (lines 70-90) only.
- Out of scope: `MCP-004` (already correctly `Status: resolved`), `GIT-001`, `GIT-002`,
  and any other entry in this document; any code change.

## Assumptions

- The protected-branch guard, ref-safety validation, and their test coverage are
  already implemented — re-verified 2026-08-27 (see this Plan's Problem section and
  the `04_mcp_04_05_git.md` implementation procedure in this same pass).
- `GIT-002` is the correct cross-reference for the postcondition-verification gap
  (resolves the Plan's UNK-01, confirmed 2026-08-27).

## Design decisions

- Mirror the sibling `MCP-004` entry's own resolution style (`Status`, `Resolution
  Notes` citing the fix and its test) rather than inventing a new format.
- `MCP-003`'s `Status` should move from `open` to a value reflecting partial
  resolution — decide between `resolved` (if scoping the entry down to
  Dirty-Worktree/Detached-HEAD/postcondition makes it a duplicate of `GIT-001`/
  `GIT-002`) or keep `open` with a narrowed `Summary`/`Current Description` that
  points to `GIT-001`/`GIT-002` for the remaining scope. This is a Needs confirmation
  item — see Assumptions/Out of scope below; default to narrowing the description and
  keeping `Status: open` with `Resolution Notes` explaining the narrowing, since
  `GIT-001`/`GIT-002` are the tracking entries for the remaining gap and `MCP-003`
  should not duplicate their `Status` independently.

## Alternatives considered

- Deleting `MCP-003` entirely (since its remaining scope is covered by `GIT-001`/
  `GIT-002`) was considered and rejected — the Plan's REQ-003 specifies narrowing, not
  removal, and removal is a scope decision beyond what this Plan's Implementation
  steps describe (would need to be reported as a Plan Gap if pursued).

## Implementation
### Target file
`docs/04_mcp_90_inconsistencies_and_known_issues.md`

### Procedure
1. Read the full current `MCP-003` entry (lines 70-90) before editing.
2. Rewrite `Summary`, `Current Description`, `Observed Implementation`, `Recommended
   Action`, and `Resolution Notes` per Method/Details below.
3. Decide `Status` per Design decisions above.
4. Run `uv run python tools/check_docs_consistency.py --domain mcp`.

### Method
Direct text edit (Edit tool) on the single `MCP-003` entry block.

### Details
Current entry (verified 2026-08-27, lines 70-90):
- `Summary`: "Git MCP enforces only repository-path allowlisting and `read_only`; no
  guard checks Dirty Worktree, Detached HEAD, protected branches, or Force Push.
  `branch`/`remote` are forwarded to GitPython unvalidated." — **false** for
  protected-branches and unvalidated `branch`/`remote`; still true for Dirty
  Worktree/Detached HEAD/Force Push (Force Push has no guard because it has nothing to
  guard — `GitPushRequest` exposes no `force` field).
- `Observed Implementation`: "Reproduced in a sandboxed test environment — passing
  `branch=\"--force\"` to `git_checkout` discards uncommitted worktree changes without
  warning..." — **false against current code**: `GitService._validate_ref()`
  (`git_service.py:112-118`) rejects any `branch`/`remote` starting with `-`, called
  before dispatch in `git_checkout` (239), `git_pull` (268, 274), `git_push` (298,
  304); tested by `test_is_safe_ref` and the `"remote": "-force"` / `"CLI option"`
  assertions in `tests/mcp_servers/git/test_git_security_compliance.py` (lines
  85-101). This bullet must be corrected, not only the `Summary`/`Current Description`
  fields.
- `Recommended Action`: "Validate `branch`/`remote` against a safe-ref pattern..." —
  already done; replace with a forward-looking action for the remaining gap only
  (Dirty-Worktree/Detached-HEAD/postcondition — cross-reference `GIT-001`/`GIT-002`
  instead of restating).
- `Resolution Notes`: currently "Open; confirmed exploitable, not merely a
  documentation gap." — must be replaced entirely; it directly asserts the
  now-disproven exploit.

Rewrite to state: protected-branch enforcement
(`GitSecurityGuards._check_protected_branch()`) and `branch`/`remote`
option-injection rejection (`_is_safe_ref()`/`_validate_ref()`) are implemented and
tested; Force-Push has no guard because `git_push`'s schema has no `force` field to
guard (not a gap); the remaining Dirty-Worktree/Detached-HEAD gap is tracked as
`GIT-001` and the postcondition-verification gap as `GIT-002` — do not restate their
details here, cross-reference by ID.

## Compatibility considerations

- Documentation-only; no runtime behavior, config schema, or public interface is
  affected.

## Security considerations

- The narrowed entry must not drop the still-open Dirty-Worktree/Detached-HEAD/
  postcondition gaps from tracking — they must remain visible via the `GIT-001`/
  `GIT-002` cross-references, not silently disappear when `MCP-003`'s exploit claim is
  removed.

## Rollback considerations

- Single-entry text revert via `git diff`/`git checkout -- <path>`; `MCP-004` (the
  sibling entry) and `GIT-001`/`GIT-002` are not modified by this item and need no
  coordinated rollback.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_90_inconsistencies_and_known_issues.md` | Doc consistency check | `uv run python tools/check_docs_consistency.py --domain mcp` | Passes; no new findings |

## Completion criteria

- `MCP-003`'s `Current Description`/`Observed Implementation`/`Recommended Action` no
  longer claim protected-branch enforcement or ref-safety validation are absent, and
  no longer claim the `branch="--force"` exploit is currently reproducible.
- `Resolution Notes` reflects the narrowed, still-open scope, citing `GIT-001` for
  Dirty-Worktree/Detached-HEAD and `GIT-002` for postcondition verification.

## Out of scope

- `MCP-004`, `GIT-001`, `GIT-002`, and any other entry in this document.
- Any code change.
- Deciding whether `MCP-003` should be deleted outright (see Alternatives considered)
  — out of this Plan's scope; a Plan Gap if pursued.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `MCP-003` per Implementation > Method/Details | Pending | — | — | |
| 2 | Run `uv run python tools/check_docs_consistency.py --domain mcp` | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/20260821_02_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-113056_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110046
- **Related target files**: `docs/04_mcp_90_inconsistencies_and_known_issues.md`
