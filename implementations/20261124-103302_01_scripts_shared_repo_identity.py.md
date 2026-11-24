## Goal

Provide the single definition of repository identity required by REQ-002 (one canonical `owner/repo` key used by the guard, the API slug, the error text, and the audit record) and REQ-010 (one definition in `scripts/shared/`, not re-implemented per server).

## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 1 is validated on its own)

## Assumptions

- The canonical form is the lowercase form of `owner` and `repo` (Plan Assumptions, resolved as UNK-02); GitHub accepts a lowercase slug, so normalization at the entry is safe.
- Non-canonical input is accepted and normalized, never rejected (REQ-002).
- The module stays stdlib-only so the `shared must not import from agent, mcp_servers, rag, or db` contract stays kept (`uv run lint-imports`: 6 contracts kept, 0 broken).

## Design decisions

- The module owns policy only: two pure functions, no I/O, no GitHub types, no exceptions other than `ValueError` for a non-string argument (Plan D-1).
- An allowlist entry is validated by shape (`owner/repo` with no case difference), so a non-canonical entry in config is detected at the guard rather than silently matching nothing.

## Alternatives considered

- Placing both helpers in `scripts/mcp_servers/github/github_service_security.py` — rejected by the Plan (D-1): the guard module's responsibility is enforcement, and sibling items (mcpai003, mcpci001, mdqmcp001) consume the shared definition.
- Rejecting mixed-case input with `GitHubValidationError` — rejected (Plan D-3): GitHub accepts it, and rejection would break callers for no security gain.

## Implementation
### Target file
`scripts/shared/repo_identity.py` (new)

### Procedure
1. Module docstring in the repository style (`scripts/shared/<file>.py — <purpose>`, usage example).
2. Add `normalize_repo_key` (new) — returns the canonical lowercase `owner/repo` key from two string parts.
3. Add `is_canonical_repo_key` (new) — the allowlist-entry shape check: reports whether a stored entry is already in canonical form.

### Method
- `normalize_repo_key` (new), signature `(owner, repo) -> str`: rejects a non-string argument with `ValueError`, joins with `/`, lowercases both parts, and returns the key. Input that is already canonical is returned unchanged.
- `is_canonical_repo_key` (new), signature `(entry) -> bool`: one argument, one claim per branch — shape (`owner/repo`, both parts non-empty) and case (equal to its own lowercase form). It does not modify the allowlist.

### Details
- No logging, no config access, no dependency on `shared.config_utils`; the guard and the config builder call these functions, they do not call back.
- Keep the module under the repository module-size gate (`tools/check_module_size.py`, 24576 B); this module is a few dozen lines.

### Companion test files
- `tests/shared/test_repo_identity.py` (new)
  - Procedure: mixed-case input, already-canonical input, and non-string input for `normalize_repo_key` (new); shape and case cases for `is_canonical_repo_key` (new) (REQ-002, REQ-010).
  - Validation: `uv run pytest tests/shared/test_repo_identity.py`; AC-2 is satisfied only by the mixed-case and already-canonical cases.

## Compatibility considerations

- New file: no existing caller. The first callers are `github_models_config.py`, `github_service_security.py`, and `github_server.py` (Plan Affected areas, Medium blast radius).
- Existing tests use lowercase keys, so no existing assertion changes (Plan Assumptions).

## Security considerations

- Repository identity is the key the guard, the audit record, and the Agent's approval decision use; a single definition removes the case-dependent divergence reported in the Plan's Problem section.
- The module performs no authorization decision of its own — enforcement stays in `github_service_security.py`.

## Rollback considerations

- High: removing the module and its callers restores the current state with no data or config change (Plan D-1).

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/shared/repo_identity.py` | Unit (pure function) | `uv run pytest tests/shared/test_repo_identity.py` | Mixed-case input yields the canonical key; already-canonical input is unchanged; non-string input is rejected |
| Import contract | Static shape | `uv run lint-imports` | 6 contracts kept, 0 broken — `shared` stays a leaf |

## Completion criteria

- `normalize_repo_key` (new) and `is_canonical_repo_key` (new) exist only in this file, and the GitHub package contains no second definition (AC-10 of this Plan is satisfied by that single definition).
- The new tests pass and the import contract stays kept.

## Out of Scope

- Adoption by GitHub schema generation, CI/CD, Web Search, and MDQ (mcpai003, mcpci001, mdqmcp001).
- Any change to `scripts/mcp_servers/cicd/cicd_service_business.py:_parse_repo`, listed as a Reference File only.
- Calling the helpers from the guard, the config builder, or the audit path: those are their own target rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion `tests/shared/test_repo_identity.py`) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) plus `uv run lint-imports` | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (one canonical `owner/repo` key), REQ-010 (single shared definition)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `scripts/shared/repo_identity.py`, `tests/shared/test_repo_identity.py`
