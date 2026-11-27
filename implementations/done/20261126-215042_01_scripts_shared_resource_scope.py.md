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
- `_scopes_conflict()` was radon grade A (5) before the change, not A (3) as the Plan's Validation
  quality baseline stated (stale claim, corrected 20261126). With the ancestor branch the function
  scores B (9): the boolean conditions inside the loop add the complexity, so "keeps it under B"
  does not hold. The repository gate is grade C or worse (`rules/toolchain.md`), so B (9) passes;
  no helper extraction was added to chase the baseline number because that would be a design change
  outside this procedure.
- Amendment (user decision 20261127, from procedure 03's verification): the fail-closed fallback is
  extended to composed GitHub identities. `resolve_resource_scopes()` composes only the keys present
  in `args`, so an omitted discriminating key produced a partial identity
  (`github_branch:<owner>/<repo>`) that conflicts with neither the `github_repo:` ancestor nor the
  complete identity of the same resource. A write tool whose composed GitHub identity
  (`_GITHUB_FINE_KINDS`) is missing any declared key now returns `_FALLBACK_WRITE_SCOPE`. The
  `github_repo:` kind and non-write tools keep their existing behavior; `cicd_workflow` is not
  affected. This supersedes the earlier statement in Design decisions that the fail-closed fallback
  stays untouched. Note on the resulting semantics: `global:write` conflicts only by exact equality
  (`tool_scheduler.py` builds the conflict graph through `_scopes_conflict()`), so a default-branch
  write now serializes with other unknown-resource writes but still not with a repository-wide
  `github_repo:` scope — that is the existing fallback semantics, unchanged by this amendment.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261127-092247 | 20261127-092247 | Verified against current source: _KNOWN_SCOPE_KINDS 41-52, _COMPOSED_KIND_SEPARATORS 66-69, _scopes_conflict() 117 all confirmed; _FILESYSTEM_LIKE_KINDS left untouched. Applied the four edits (three kinds added to the vocabulary, three entries with separator / added to the separators map, new _GITHUB_FINE_KINDS next to it, GitHub ancestor branch after the exact-equality check plus docstring). Baseline: file clean at cycle start. Finding: radon baseline claim stale - A (5) before, B (9) after; passes the C-or-worse gate. Changed file: scripts/shared/resource_scope.py. Amendment applied (user decision 20261127, from procedure 03's verification): resolve_resource_scopes() now returns _FALLBACK_WRITE_SCOPE for a write tool whose composed GitHub identity (_GITHUB_FINE_KINDS) is missing any declared key, instead of a partial identity. github_repo and non-write tools unchanged. Docstring updated. Ad-hoc check: github_branch:acme/app/main when branch present, global:write when branch omitted, github_repo partial identity unchanged. |
| 2 | Add or update tests per Validation plan | Completed | 20261127-092247 | 20261127-092247 | No tests added in this cycle: the Validation plan's unit expectations are delivered by procedure 06 (tests/shared/test_resource_scope.py), this procedure's Out of Scope. Existing 47 tests in that file pass unchanged. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-092247 | 20261127-092247 | ruff format --check and ruff check: pass. mypy: no issues in scripts/shared/resource_scope.py (7 pre-existing errors in scripts/agent/services/mcp_health.py, untouched by this cycle). lint-imports: 6 kept / 0 broken, shared-is-leaf kept. bandit -r scripts/ -ll: no new findings (0 on the changed file; Medium 7 / High 38 pre-existing elsewhere). radon: B (9), under the C gate. check_module_size.py: OK, no new violations. Targeted tests: 47 passed tests/shared/test_resource_scope.py. Full suite and diff-cover deferred to the end of batch 3 per Batch mode (plan batch). Re-run after the amendment: ruff format --check and ruff check pass, mypy on the changed file no issues, bandit on the changed file no findings, lint-imports 6 kept / 0 broken, check_module_size.py OK, targeted tests 55 passed. radon: resolve_resource_scopes C (14) (was C (11)), _scopes_conflict B (9); both under the C-or-worse gate. The fail-closed case needs a test in procedure 06. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261127-092247 | 20261127-092247 | No documentation in scope: Compatibility considerations cite no docs and docs/00_index.md maps resource_scope only to the shared infra spec, which is procedure 08's target scope. No docs change made, so the docs checkers were not run for this cycle. |

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