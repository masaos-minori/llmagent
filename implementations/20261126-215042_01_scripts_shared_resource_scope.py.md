## Goal

Extend the resource-scope vocabulary and the conflict predicate so a `github_repo:` scope
conflicts with the finer GitHub scopes of the same repository (REQ-002, AC-3: repository-wide
operations conflict with all relevant finer scopes).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Plan's row evidence was re-verified on 20261126: `_KNOWN_SCOPE_KINDS` is at
  `scripts/shared/resource_scope.py:41-52` (not 40-49), `_COMPOSED_KIND_SEPARATORS` at 66-69,
  `_scopes_conflict()` at 117.
- The three finer kinds must also be registered in `_COMPOSED_KIND_SEPARATORS` with separator
  `/`; without it `resolve_resource_scopes()` emits one scope string per key instead of the
  single composed `github_branch:<owner>/<repo>/<branch>` string the Plan's Design decisions
  state (Plan correction, 20261126).
- The finer kinds are NOT added to `_FILESYSTEM_LIKE_KINDS` (56): GitHub identities are not
  paths, so `PurePosixPath` normalization must not apply to them.
- The scheduler consumes `_scopes_conflict()` as a black box (`scripts/agent/tool_scheduler.py:37`)
  and is a reference row, not a target row.

## Design decisions
- The change is confined to the predicate plus the kind vocabulary; the scheduler grouping, the
  synthetic `global:write` scope, and the fail-closed fallback stay untouched, so existing safety
  properties hold by construction (REQ-005).
- Ancestor semantics are added as an additional conflict source only — the predicate never
  removes a conflict, so existing serialization results are preserved monotonically (Plan Risk).
- `github_repo:` is the ancestor kind; `github_branch:`, `github_issue:`,
  `github_pull_request:` are the descendant kinds. Ancestor identity is `<owner>/<repo>`;
  descendant identity must begin with that identity followed by `/`.

## Alternatives considered
- Normalize GitHub identities through `PurePosixPath` and reuse the existing filesystem ancestor
  branch: rejected — it would change identity normalization for non-path values and couple the
  GitHub kinds to the filesystem vocabulary.
- Handle the ancestor rule in the scheduler instead of the predicate: rejected — the scheduler is
  a consumer of the predicate and is out of scope for this Plan.

## Implementation
### Target file
`scripts/shared/resource_scope.py`

### Procedure
1. Add `github_branch` (new), `github_issue`, `github_pull_request` (new) to `_KNOWN_SCOPE_KINDS` (41-52).
2. Add the same three kinds to `_COMPOSED_KIND_SEPARATORS` (66-69) with separator `/`.
3. Add a module-level constant `_GITHUB_FINE_KINDS` (new) holding the three descendant kinds,
   placed next to `_COMPOSED_KIND_SEPARATORS`.
4. Extend `_scopes_conflict()` (117) with the GitHub ancestor branch after the exact-equality
   check, and update its docstring to state the new rule.

### Method
In `_scopes_conflict()`, after `if a == b`, resolve the pair's kind prefixes; when one side is
`github_repo:` and the other is a member of `_GITHUB_FINE_KINDS` (new), compare the identity part
after `:` — conflict when the descendant identity starts with the ancestor identity plus `/`.
Keep the existing `filesystem:` branch unchanged.

### Details
- Kind prefix extraction: split at the first `:`; a scope string is always
  `f"{kind}:{identity}"` per `resolve_resource_scopes()` (76-114).
- The rule is directional in effect but must be checked in both orders, mirroring the existing
  filesystem ancestor check (130-133).
- `_scopes_conflict()` is currently radon grade A (3); the added branch keeps it under B per the
  Plan's Validation quality baseline.

## Compatibility considerations
- `_scopes_conflict()` is consumed by `scripts/agent/tool_scheduler.py` and pinned by
  `tests/shared/test_resource_scope.py` (target row 6) and `tests/agent/test_tool_scheduler.py`
  (target row 7); reference tests `tests/mcp_servers/test_tool_schema_contract.py`,
  `tests/shared/test_runtime_tool_registry.py`, `tests/shared/test_tool_routing_validation.py`
  execute the module but pin no scope-kind set, so they are not affected.
- Adding the three kinds to `_KNOWN_SCOPE_KINDS` only widens the accepted vocabulary of
  `validate_tool_schema_v2()`; no existing declaration is rejected.

## Security considerations
- Fail-closed behavior is unchanged: a write tool whose keys do not resolve still returns
  `_FALLBACK_WRITE_SCOPE` (62). The change adds conflicts, never removes one, so it cannot make a
  write look more parallelizable.

## Rollback considerations
- Single-commit change; revert the commit. Tests land before the implementation per the Plan's
  Bus Factor mitigation.

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Unit | `uv run pytest tests/shared/test_resource_scope.py -v` | Ancestor conflict for repository-versus-finer; independent resources non-conflicting (tests added by procedure 06) |
| Static | `uv run ruff format --check scripts/shared/resource_scope.py`, `uv run ruff check scripts/shared/resource_scope.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | No new findings |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | `shared-is-leaf` kept |
| Security | `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |
| Coverage | `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Completion criteria
- A `github_repo:<owner>/<repo>` scope conflicts with `github_branch:`, `github_issue:`, and
  `github_pull_request:` scopes whose identity begins with `<owner>/<repo>/` (AC-3).
- The three finer kinds resolve to one composed scope string each (AC-2).
- The `filesystem:` ancestor behavior and the fail-closed fallback are unchanged (REQ-005).

## Out of Scope
- The scheduler (`scripts/agent/tool_scheduler.py`) — reference row, no modification.
- Test files — covered by procedure 06 (`tests/shared/test_resource_scope.py`).
- Key-kind vocabulary — procedure 02 (`scripts/shared/tool_metadata.py`).

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
| — | N/A: no blocker recorded at procedure creation | N/A: no blocker recorded | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (repository-wide scopes conflict with all relevant finer scopes)
- **Source issue**: issues/20261119-140520_mcpai013_github-resource-scope-refine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-073010_mcpai013_github-resource-scope-refine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-215042
- **Related target files**: `scripts/shared/resource_scope.py`
