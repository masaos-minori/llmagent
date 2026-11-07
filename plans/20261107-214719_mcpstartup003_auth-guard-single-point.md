## Goal
Consolidate the "refuse to start an MCP server with an empty `auth_token`" rule into one enforcement point that every server uses, so a new or edited server cannot silently omit it. Route the six inline `if not <token>: raise RuntimeError(...)` guards through the shared enforcement point, add a structural test or checker that fails when a `*_server.py` module attaches the middleware without going through that point, and make the test-only accept-all intent of `attach_auth_middleware()` explicit in its API rather than in a docstring only — while keeping the import-time refusal behavior and the earlier Plan decision to keep the posture check at WARNING.

## Priority
Medium

## Scope
- **In-Scope**:
  - `scripts/mcp_servers/server.py` — `require_auth_token` and `attach_auth_middleware` so there is one enforcement point and the test-only accept-all intent is explicit in the signature.
  - `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/github/github_server.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/file/read_server.py`, `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/file/delete_server.py` — replace the inline `if not <token>: raise RuntimeError(...)` with a call through the shared enforcement point, keeping each server's variable name in the error message.
  - `tests/mcp_servers/test_require_auth_token.py` and the per-server auth tests — assert the shared enforcement point and preserve the empty-token refusal for all ten servers.
- **Out-of-Scope**:
  - Changing the posture severity of the empty-token check (kept at WARNING by the earlier Plan decision).
  - Agent-side startup validation in `scripts/agent/startup_validation.py`.
  - Token sourcing, rotation, or storage.
  - Changing the Bearer comparison (`hmac.compare_digest`) or the `X-Request-Id` behavior.
  - Changing authentication semantics, the header comparison, or whether an empty token is refused at import time.
- **Dependencies**: Sibling issue `issues/20261107-132004_mcpstartup001_python-m-double-execution.md` also edits `scripts/mcp_servers/server.py`; no required order, but plan them together to avoid conflicting edits in that file. Follows archived `issues/done/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md` (the shared-check preference is only partly implemented; re-verified against current source). No `Depends on` entries.

## Background
Archived issue `issues/done/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md` asked to apply one fail-closed rule to all ten servers and said to "prefer a single shared check (in `attach_auth_middleware` or the posture flow) over four more copies of the import-time `RuntimeError`". Its recorded Plan decision kept the posture check at WARNING and enforced by import-time refusal. Current source verified against HEAD `47b837eb8`; `scripts/mcp_servers/server.py` is unchanged since the review head `59dbae624`.

Evidence (label: `Explicit in code`):
- `require_auth_token()` in `scripts/mcp_servers/server.py` is used by `git_server.py`, `cicd_server.py`, `rag_pipeline_server.py`, and `web_search_server.py`.
- `shell_server.py`, `github_server.py`, `mdq_server.py`, `file/read_server.py`, `file/write_server.py`, and `file/delete_server.py` each carry their own inline `if not _cfg.auth_token: raise RuntimeError(...)` immediately before `attach_auth_middleware(...)`. The message text differs per file; `mdq_server.py` reads the token through its own `_load_auth_token()`.
- `attach_auth_middleware()` returns `True` from `_is_authorized` when the token is empty (L116-119); its docstring (L106-110) states this accept-all fallback exists only for standalone testability and relies on Agent startup validation.
- Tests: `tests/mcp_servers/test_require_auth_token.py` covers the helper and the four servers; the inline copies are covered per server (`tests/mcp_servers/shell/test_shell_server_auth.py`, `tests/mcp_servers/mdq/test_mdq_authentication.py`, and others). No test or checker asserts that every server module routes its token through one enforcement point (evidence label: `Strongly implied by code`).

## Problem
The intent of the archived issue (one shared check, so a new server cannot forget it) is only partly met. A future eleventh server, or an edit that removes an inline guard, would start accepting unauthenticated requests without any failing test, because the middleware default is accept-all and enforcement is a per-file convention. The six inline guards also drift independently (message wording, environment-variable name text, and the token source).

## Reason for Change
Authentication on loopback servers is the defense against other local processes. The current arrangement keeps today's ten servers safe but depends on each author remembering a local pattern. No incident is reported; this is a hardening and maintainability change, so it is Medium rather than High.

## Implementation Intent
Provide one enforcement point that every server uses, either by making the helper the only way servers attach the middleware or by adding a structural check or test that every `*_server.py` module routes its token through it. Keep the import-time refusal behavior and the Plan decision to keep the posture check at WARNING unless the plan explicitly revisits it. Preserve an explicit, test-only way to attach the middleware without a token. Decide the mechanism in the plan; do not change authentication semantics.

## Requirements
- `REQ-001`: All ten servers obtain their middleware token through one shared enforcement point, verified by a test or checker that scans the server modules.
- `REQ-002`: Adding a server module that calls `attach_auth_middleware` with an unvalidated token fails that test or checker.
- `REQ-003`: For each of the ten servers, importing the module with an empty token still raises `RuntimeError` naming the server and the environment variable.
- `REQ-004`: Existing auth tests pass, or are updated only where they relied on the accept-all default.

## Implementation Target Files
**Freeze status**: Draft

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/mcp_servers/server.py` | Modify | `require_auth_token` is the shared enforcement point used by four servers; `attach_auth_middleware()` accept-all default (L116-119) is documented as test-only. Consolidate so every server routes through one point and make the test-only intent explicit in the API. | `REQ-001`/`REQ-002`/`REQ-003` | `require_auth_token` used by git/cicd/rag/web_search; `_is_authorized` returns True on empty token L119 (checked in Step 2) | `test_require_auth_token.py` | `Verified` |
| `scripts/mcp_servers/shell/shell_server.py` | Modify | Inline `if not _cfg.auth_token: raise RuntimeError(...)` (L120-121) duplicates the shared rule; route through the shared enforcement point. | `REQ-001`/`REQ-003` | inline guard L120-121 (checked in Step 2) | `tests/mcp_servers/shell/test_shell_server_auth.py` | `Verified` |
| `scripts/mcp_servers/github/github_server.py` | Modify | Inline guard (L140-141) duplicates the shared rule; route through the shared enforcement point. | `REQ-001`/`REQ-003` | inline guard L140-141 (checked in Step 2) | per-server auth test | `Verified` |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | Inline guard (L484) duplicates the shared rule; route through the shared enforcement point while preserving `_load_auth_token()`. | `REQ-001`/`REQ-003` | inline guard L484 (checked in Step 2) | `tests/mcp_servers/mdq/test_mdq_authentication.py` | `Verified` |
| `scripts/mcp_servers/file/read_server.py` | Modify | Inline guard (L126-127) duplicates the shared rule; route through the shared enforcement point. | `REQ-001`/`REQ-003` | inline guard L126-127 (checked in Step 2) | per-server auth test | `Verified` |
| `scripts/mcp_servers/file/write_server.py` | Modify | Inline guard (L116-117) duplicates the shared rule; route through the shared enforcement point. | `REQ-001`/`REQ-003` | inline guard L116-117 (checked in Step 2) | per-server auth test | `Verified` |
| `scripts/mcp_servers/file/delete_server.py` | Modify | Inline guard (L118-119) duplicates the shared rule; route through the shared enforcement point. | `REQ-001`/`REQ-003` | inline guard L118-119 (checked in Step 2) | per-server auth test | `Verified` |
| `tests/mcp_servers/test_require_auth_token.py` | Modify | Assert the shared enforcement point is used by all ten servers and that adding an unvalidated call fails (`REQ-001`/`REQ-002`). | `REQ-001`/`REQ-002` | existing helper + four-server tests (checked in Step 2) | `test_require_auth_token.py` | `Verified` |
| `tests/mcp_servers/shell/test_shell_server_auth.py` | Modify | Preserve the empty-token refusal after routing through the shared point. | `REQ-003` | existing shell auth test (checked in Step 2) | `test_shell_server_auth.py` | `Verified` |
| `tests/mcp_servers/mdq/test_mdq_authentication.py` | Modify | Preserve the empty-token refusal after routing through the shared point. | `REQ-003` | existing mdq auth test (checked in Step 2) | `test_mdq_authentication.py` | `Verified` |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file group, or vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as its own row when it requires modification — do not fold it into the row for the source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same one-file-per-row discipline as `Implementation Target Files` above — no directories, glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/mcp_servers/server.py` | Read in full to understand `require_auth_token`, `attach_auth_middleware`, and the posture-gate interaction before consolidating. | `scripts/mcp_servers/server.py` (`REQ-001`/`REQ-002`) |
| `tests/mcp_servers/shell/test_shell_server_auth.py` | Existing per-server auth assertions to preserve when routing through the shared point. | `scripts/mcp_servers/shell/shell_server.py` (`REQ-003`) |
| `tests/mcp_servers/mdq/test_mdq_authentication.py` | Existing mdq auth assertions including `_load_auth_token()` usage. | `scripts/mcp_servers/mdq/mdq_server.py` (`REQ-003`) |

## Acceptance Criteria
- `REQ-001`: All ten servers obtain their middleware token through one shared enforcement point, verified by a test or checker that scans the server modules.
- `REQ-002`: Adding a server module that calls `attach_auth_middleware` with an unvalidated token fails that test or checker.
- `REQ-003`: For each of the ten servers, importing the module with an empty token still raises `RuntimeError` naming the server and the environment variable.
- `REQ-004`: Existing auth tests pass, or are updated only where they relied on the accept-all default.

## Tests
- Parametrized test over all ten server modules for the empty-token refusal and for the use of the shared enforcement point (`REQ-001`/`REQ-003`).
- Structural checker or parametrized test asserting that a server calling `attach_auth_middleware` with an unvalidated token fails (`REQ-002`).
- Preserve existing per-server auth assertions (`REQ-004`).

## Documentation Impact
Update the MCP authentication documentation only if it names the per-server guard or the accept-all fallback as a supported behavior. State the boundary and failure behavior, not implementation details. Run the `docs/` checkers from `routing.md` for any edited doc.

## Assumptions
- `require_auth_token()` can serve as the single shared enforcement point for both the import-time refusal and the middleware attachment, or a thin wrapper around it can.
- Each server's error message must keep naming its own server and environment variable; the consolidation preserves per-server identity in the message.
- The earlier Plan decision to keep the posture check at WARNING stands; this issue does not revisit it.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| `UNK-01` | whether the owner wants `attach_auth_middleware()` to keep the accept-all default for tests, or an explicit opt-in argument | not decided in the issue | record the chosen approach in the implementation procedure; confirm with owner | `False` |
| `UNK-02` | whether `mdq_server.py`'s separate `_load_auth_token()` must stay separate for a reason not visible in the code | not stated in code or docs | confirm with owner; affects how mdq routes through the shared point | `False` |
| `UNK-03` | whether a structural scan of server modules is better than a parametrized import test for `REQ-002` | both approaches viable | choose the lower-maintenance option in the implementation procedure | `False` |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows — this table analyzes change-impact risk for those same files; it is not a separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/mcp_servers/server.py` | Modify | all ten servers' auth attachment path | 7 | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/shell/shell_server.py` | Modify | that server's import-time auth guard only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/github/github_server.py` | Modify | that server's import-time auth guard only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/mdq/mdq_server.py` | Modify | that server's import-time auth guard only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/file/read_server.py` | Modify | that server's import-time auth guard only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/file/write_server.py` | Modify | that server's import-time auth guard only | N/A | N/A | not applicable (rsynced) |
| `scripts/mcp_servers/file/delete_server.py` | Modify | that server's import-time auth guard only | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/test_require_auth_token.py` | Modify | that test file only | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/shell/test_shell_server_auth.py` | Modify | that test file only | N/A | N/A | not applicable (rsynced) |
| `tests/mcp_servers/mdq/test_mdq_authentication.py` | Modify | that test file only | N/A | N/A | not applicable (rsynced) |

## Design
**Open decision — consolidation mechanism (drives `REQ-001`/`REQ-002`):**
- **Approach (a) make the helper the only attachment path.** Change the six servers to call the shared enforcement point (e.g. `require_auth_token(...)` or a thin `attach_auth_middleware` wrapper that refuses an empty token) instead of the inline `if not <token>: raise RuntimeError(...)`. Then add a structural test/checker (`REQ-002`) that fails when a `*_server.py` module attaches the middleware without going through the point. Lowest message drift; one behavioral source.
- **Approach (b) structural gate only.** Keep the inline guards but add a test/checker that scans every `*_server.py` and asserts each routes its token through the shared point (for example by asserting the guard text or a call site). Less invasive but does not remove the duplication.
- Recommend approach (a): it removes the drift the issue flags and gives one enforcement point. Record the choice and blast-radius trade-off in the implementation procedure.

**Test-only accept-all intent (`REQ-004`):** If `attach_auth_middleware()` keeps accepting an empty token by default, make the test-only intent explicit in the API (an explicit opt-in argument) rather than a docstring only, and update any test that relied on the implicit default. Decide in the plan (`UNK-01`).

**Baseline (Step 5):** radon rates `attach_auth_middleware` A(1) and `require_auth_token` A(2); `bandit -ll` reports no high/medium findings; `lint-imports` 6 kept / 0 broken; `server.py` churn 7 commits in 30 days (high-churn file — scope the edit tightly).

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows of `Implementation Target Files` above — do not restate file-level detail independently of that frozen table. A step is a top-level numbered item (a Phase); its checklist items are sub-tasks, and the Execution Status table has one row per step. Declare a release unit (see `### Release units` below) when a phase breaks existing callers or tests until another phase lands (for example a `NOT NULL` column added before its write path): one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be validated alone}`.

1. **Phase 1: Choose the consolidation mechanism and document it.** Decide approach (a) vs (b) (Requirements `REQ-001`/`REQ-002`); record the blast-radius trade-off in the implementation procedure. No file change yet.
2. **Phase 2: Consolidate the six inline guards.** Replace the inline `if not <token>: raise RuntimeError(...)` in `shell`, `github`, `mdq`, `read`, `write`, `delete` with a call through the shared enforcement point, keeping each server's variable name in the error message and never echoing the token (`REQ-001`/`REQ-003`).
3. **Phase 3: Make the test-only accept-all intent explicit.** If keeping the accept-all default, add an explicit opt-in argument to `attach_auth_middleware()` and update tests that relied on the implicit default (`REQ-004`/`UNK-01`).
4. **Phase 4: Add the structural enforcement test.** Add the test/checker that fails when a `*_server.py` module attaches the middleware without the shared point (`REQ-002`).
5. **Phase 5: Repair per-server auth tests.** Preserve existing empty-token refusals after consolidation (`REQ-003`/`REQ-004`).
6. **Phase 6: Deployment & verification.** Run the validation commands below.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/server.py` | Unit / integration | `uv run pytest tests/mcp_servers` | new and existing tests pass |
| All ten servers | Integration (parametrized) | empty-token import + shared-point scan | all refuse empty token; all route through one point |
| `scripts/mcp_servers/server.py` | Static | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | clean |
| `scripts/mcp_servers/` | Static security | `uv run bandit -r scripts/ -c pyproject.toml -ll` | no new high/medium findings |
| Reference table | Static | `uv run python tools/generate_reference_table.py --check` | no drift |

## Risks
- **Risk:** consolidating the six guards changes the exact `RuntimeError` message wording some tests assert. → **Mitigation:** preserve each server's server-name and env-var name in the message; update only the assertions that match exact wording.
- **Risk:** high 30-day churn (7 commits) on `server.py` means the file may have moved during planning. → **Mitigation:** re-verify the target sections at Step 8 freeze against current content.
- **Risk:** making the accept-all intent explicit in the API could break tests that call `attach_auth_middleware()` without the new opt-in. → **Mitigation:** keep the default behavior unchanged unless the owner opts into an explicit argument (`UNK-01`).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Choose the consolidation mechanism (a helper-only / b structural gate) | Pending | — | — | Open design decision in Design section |
| 2 | Consolidate the six inline guards | Pending | — | — | shell/github/mdq/read/write/delete |
| 3 | Make the test-only accept-all intent explicit | Pending | — | — | `attach_auth_middleware` API |
| 4 | Add the structural enforcement test | Pending | — | — | `test_require_auth_token.py` |
| 5 | Repair per-server auth tests | Pending | — | — | shell/mdq per-server tests |
| 6 | Deployment & verification | Pending | — | — | run validation commands |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-132052_mcpstartup003_auth-guard-single-point.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-214719
- **Related target files**: `scripts/mcp_servers/server.py`, `scripts/mcp_servers/shell/shell_server.py`, `scripts/mcp_servers/github/github_server.py`, `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/file/read_server.py`, `scripts/mcp_servers/file/write_server.py`, `scripts/mcp_servers/file/delete_server.py`, `tests/mcp_servers/test_require_auth_token.py`, `tests/mcp_servers/shell/test_shell_server_auth.py`, `tests/mcp_servers/mdq/test_mdq_authentication.py`

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.
