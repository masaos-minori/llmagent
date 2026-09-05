## Goal
Document `allowed_remote_urls` in `config/git_mcp_server.toml` with a commented
example, consistent with the file's existing `allowed_repo_paths`/
`protected_branches` documentation style (`REQ-002`).

## Scope
- In scope: a new commented key block for `allowed_remote_urls` in this file only.
- Out of scope: `GitConfig`'s field definition/parsing (`git_models.py`, a separate
  row); any enforcement logic (`format_output.py`, a separate row).

## Assumptions
- None beyond the Plan's own fail-closed-when-empty convention (Assumptions,
  `git_models.py`'s row).

## Design decisions
- Mirror `allowed_repo_paths`'s exact three-line comment shape (purpose, fail-closed
  note, example), placed immediately after `allowed_repo_paths` (line 6) since both
  are allowlist-of-strings configs with the same fail-closed default — keeping
  related config together.

## Alternatives considered
- Placing the new key near `protected_branches` (line 26-29) instead was considered;
  rejected because `allowed_remote_urls` is an allowlist with the same fail-closed
  shape and purpose family as `allowed_repo_paths`, not a branch-protection concern.

## Implementation
### Target file
`config/git_mcp_server.toml`

### Procedure
1. Insert a new commented block immediately after line 6 (`allowed_repo_paths = []`)
   and its blank-line separator, before line 8's `read_only` comment.

### Method
Copy `allowed_repo_paths`'s comment structure (lines 3-6) verbatim in shape, only
substituting the key name, purpose sentence, and example values.

### Details
```toml
# allowed_remote_urls: normalized remote URLs authorized for git_pull/git_push.
# Empty list = deny all (fail-closed). Add authorized remote URLs explicitly.
# Example: allowed_remote_urls = ["https://github.com/org/repo.git"]
allowed_remote_urls = []
```

## Compatibility considerations
- Additive, commented-and-defaulted-empty key — no existing deployment's config file
  is invalidated; `GitConfig.from_dict()`'s `default=[]` (separate row) makes the key
  optional.

## Security considerations
- The example must not include real credentials or a real internal URL — use a
  generic public-looking placeholder (`https://github.com/org/repo.git`), consistent
  with `allowed_repo_paths`'s placeholder-style example.

## Rollback considerations
- Removing this comment block alone has no behavioral effect (it is documentation
  only) as long as `GitConfig`'s `default=[]` fallback remains in place.

## Validation plan
- Manual read-through: confirm the new block's key name matches `GitConfig`'s field
  name exactly (`allowed_remote_urls`), since a mismatch would silently fall back to
  the default with no error.
- No automated test targets a config file's comments directly; covered indirectly by
  `git_models.py`'s row test asserting `GitConfig.from_dict()` parses the key.

## Completion criteria
- `config/git_mcp_server.toml` documents `allowed_remote_urls` with a working,
  correctly-keyed example, in the same style as `allowed_repo_paths`.

## Out of scope
- `GitConfig`'s field definition/parsing and any enforcement logic — separate rows.

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260902-144912_gitremote_define_remote_authorization_and_concurrency_control.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192131_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-204502
- **Related target files**: config/git_mcp_server.toml
