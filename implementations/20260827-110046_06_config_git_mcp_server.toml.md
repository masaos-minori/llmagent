## Goal

Activate the existing, tested `protected_branches` guard for the real repository by
setting it in `config/git_mcp_server.toml` (REQ-006), per
`plans/20260826-113056_plan.md`.

## Scope

- In scope: adding one `protected_branches` key to `config/git_mcp_server.toml`.
- Out of scope: `allowed_repo_paths` (currently `[]`, independently denies all
  git-mcp access — not this Plan's concern); `read_only`; any other key; any code
  change (`GitConfig.from_dict()` already parses `protected_branches`, no loader
  change needed).

## Assumptions

- `GitConfig.from_dict()` (`git_models.py:37-58`) already parses `protected_branches`
  via `get_typed(d, "protected_branches", list, "a list", default=[])` — re-verified
  2026-08-27; no schema or loader change is required.
- The three branch names mirror `config/agent.toml::approval_high_risk_branches`
  (`["main", "master", "release"]`, re-verified 2026-08-27 at lines 120-124) — this
  Plan's own Assumptions section states this parity target needs no separate
  owner sign-off, since `protected_branches`'s mechanism was already designed and
  wired in a prior Plan.

## Design decisions

- Additive single-key change to an existing TOML file — no schema change, no new
  field, following the same shape `GitConfig` already accepts.
- Value: `protected_branches = ["main", "master", "release"]`.

## Alternatives considered

- N/A: the value and mechanism were already decided in the prior Plan that
  implemented `protected_branches` — this item only activates it for the shipped
  config, per this Plan's Assumptions.

## Implementation
### Target file
`config/git_mcp_server.toml`

### Procedure
1. Add `protected_branches = ["main", "master", "release"]` to
   `config/git_mcp_server.toml`, near the `allowed_repo_paths`/`read_only` keys for
   discoverability, with a short comment mirroring the file's existing comment style.
2. Confirm `GitConfig.load()` parses the new value (covered by the REQ-006 test items
   in `test_git_models.py`/`test_git_security_compliance.py`, see the other two
   implementation procedures in this same pass).
3. Deploy per `skills/deploy/SKILL.md` and restart the git-mcp service — confirm via
   its health endpoint that the new value is loaded (mandatory deployment
   validation, not part of this document-only workflow phase — to be executed at
   `code-implementation` time).

### Method
Direct TOML edit (Edit tool) — one new key, one new comment block.

### Details
Current file content (verified 2026-08-27) has no `protected_branches` key. Add,
after the `read_only` key's comment block and before `max_log_entries`:
```toml
# protected_branches: branch names rejected for git_checkout/git_pull/git_push.
# Empty list = none protected. Mirrors config/agent.toml::approval_high_risk_branches.
protected_branches = ["main", "master", "release"]
```
This is a git-mcp-server-process-only config (`GitConfig.load()` consumers); it
requires a git-mcp process restart, not covered by `/reload`
(`scripts/agent/services/config_reload.py` has no reference to
`git_mcp_server.toml`, confirmed via `grep -rln "git_mcp_server" scripts/ config/`
during this Plan's own verification).

## Compatibility considerations

- `allowed_repo_paths` is currently `[]`, which already denies all git-mcp access
  independently of this change — no live caller is affected today.
- Once an operator later populates `allowed_repo_paths` and sets `read_only=false`,
  `git_checkout`/`git_pull`/`git_push` targeting `main`/`master`/`release` will be
  rejected — this is the intended activation, matching the operator-declared intent
  already recorded in `config/agent.toml::approval_high_risk_branches`.
- `deploy/deploy.sh` already covers copying this config file (`cp` to
  `${DEPLOY_CONFIG}/`) — no `deploy.sh` change needed for this key addition.

## Security considerations

- This change is additive-restrictive (adds a rejection, does not remove one) — no
  new attack surface is introduced.

## Rollback considerations

- Single-key revert via `git diff`/`git checkout -- config/git_mcp_server.toml`; if
  already deployed, remove the key and restart the git-mcp service to restore the
  empty-list (no branches protected) behavior.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `config/git_mcp_server.toml`, `scripts/mcp_servers/git/git_models.py` | Unit | `uv run pytest tests/mcp_servers/git/test_git_models.py -v` | `GitConfig.load()`-sourced assertion (added by the REQ-006 test item) confirms `protected_branches == ["main", "master", "release"]` |
| `scripts/mcp_servers/git/git_service.py` | Unit | `uv run pytest tests/mcp_servers/git/test_git_security_compliance.py -v` | Three-branch rejection case (added by the REQ-006 test item) passes |
| Deployment | Manual | `skills/deploy/SKILL.md` deploy + git-mcp service restart + health check | git-mcp reports the new `protected_branches` value active |

## Completion criteria

- `config/git_mcp_server.toml`'s `GitConfig.protected_branches` (as loaded by
  `GitConfig.load()`) equals `["main", "master", "release"]`.
- A test demonstrates that `git_checkout`/`git_pull`/`git_push` targeting any of
  those three branch names is rejected when the service is constructed from the
  shipped config file.

## Out of scope

- `allowed_repo_paths`, `read_only`, and any other key in this file.
- Any code/schema change to `GitConfig`.
- Actual deployment execution (belongs to `code-implementation` phase, not this
  document-only workflow phase).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `protected_branches` key to `config/git_mcp_server.toml` | Pending | — | — | |
| 2 | Run `uv run pytest tests/mcp_servers/git/ -v` (after test items land) | Pending | — | — | |
| 3 | Deploy and restart git-mcp service; verify via health endpoint | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: `issues/20260821_02_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-113056_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-110046
- **Related target files**: `config/git_mcp_server.toml`
