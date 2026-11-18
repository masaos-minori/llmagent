# Adversarial Review — `scripts/mcp_servers/git` (11 modules)

Reviewed head: `de26cfcadb4bd7a0502c3ecd05ce1e4c09072ed9` (working tree matched HEAD, no uncommitted edits).

## Review Scope

- Reviewed (service/dispatch): `git_service.py`, `git_server.py`.
- Reviewed (security guards): `git_security.py`, `git_ref_validation.py`, `write_protection_pipeline.py`.
- Reviewed (mutation site): `format_output.py`.
- Reviewed (state/config): `repository_state.py`, `git_models.py`.
- Reviewed (supporting): `git_tools.py`, `errors.py`, `format_output.py`.
- Reviewed (shared backbone): `mcp_servers/dispatch.py`, `mcp_servers/server.py` (auth middleware + REQ-004 idempotency boundary), `mcp_servers/audit.py`, `scripts/shared/tool_constants.py`.
- Not reviewed: non-Python assets, shell/TOML, tests (no test-run phase beyond the existing suite), other `scripts/mcp_servers/*` servers.

Working tree vs reviewed head: matched at `de26cfcadb4bd7a0502c3ecd05ce1e4c09072ed9`.

## Commands run

| Tool | Scope | Result |
|---|---|---|
| `ruff check` | `scripts/mcp_servers/git/` | All checks passed |
| `mypy --no-namespace-packages` | `scripts/mcp_servers/git/` | Success: no issues found (11 files) |
| `bandit -ll` | `scripts/mcp_servers/git/` | 0 Medium/High; 8 Low (all B101 `assert`) |
| `pytest tests/mcp_servers/git/` | full git suite | 418 passed |

## Summary

- Overall assessment: **Clean.** No correctness, concurrency, resource-lifecycle, error-handling, configuration, or security defect survives adversarial scrutiny across the repo-path allowlist, remote-URL allowlist, protected-branch, read-only, and write-protection layers. The code is defensively structured: GitPython is invoked without a shell (so no command injection regardless of ref content), the repo-path allowlist is enforced twice (server + service) on a canonicalized path with component-aware containment, the remote URL is checked against an allowlist before any network write, the protected-branch rule fails closed and is enforced non-empty at load, `read_only` is triple-checked, and every mutation runs through a serialized 9-stage pipeline that re-checks HEAD identity immediately before the mutating call.
- Highest-risk area: **the write-protection pipeline and the remote-URL authorization boundary** (`format_pull`/`format_push` + `_authorize_remote` + `WriteProtectionPipeline`). Scrutinized for ref-injection, remote hijack, protected-branch bypass, and read-only escape; none found.
- Recommended next step: **proceed.** No fix required. The items below are all Low/Informational; each is either by-design audit behavior, a defensive-assert artifact, or a stale-precondition edge that is mitigated by the serialization lock. None warrants a tracked issue.

## Adversarial scenarios exercised

| Scenario | Path examined | Outcome |
|---|---|---|
| `git_checkout`/`git_pull`/`git_push` with a CLI-option ref (`-f`, `--force`) | `validate_ref` leading-dash guard | Denied; never reaches GitPython. |
| Ref with structural tokens (`+`, `..`, `@{`, `*`) | `_is_simple_ref_name` / `validate_ref_allowlist` | Denied; not a valid simple branch name. |
| `git checkout <branch>` where branch starts with `-` | `git.checkout(req.branch, "--")` `--` guard | `--` terminates option parsing; no injection. |
| Any GitPython call with a hostile ref | `repo.git.*` / `repo.index.*` subprocess | No shell is used (list-based subprocess); refs passed as literal args. |
| `git_pull`/`git_push` to a remote whose URL is not configured | `_authorize_remote` allowlist membership | `GitPolicyError` before the network call; fail-closed empty. |
| `git_pull` leaving merge conflicts | `format_pull` + `verify_postcondition` `unmerged_blobs()` | Rejected; conflict state surfaced. |
| Write tool while `read_only=true` | `_git_tool_availability` + `_validate_repo` + posture | Denied at all three layers. |
| Repo path outside allowlist (`/allowed-repo-evil`) | `is_within_allowed_paths` `relative_to` | Denied (component-aware; sibling rejected). |
| Concurrent writes to the same canonical repo | `_get_repo_lock` + Stage 5b HEAD re-check | Serialized; HEAD drift rejected. |
| Request without matching Bearer token | `_auth_middleware` `hmac.compare_digest` | 401 (outermost middleware). |
| Empty `protected_branches` at startup | `GitConfig.load()` | `ValueError` → server refuses to start (fail-closed). |
| Detached HEAD write without `allow_detached_head` | `verify_preconditions` | Denied. |

## Findings

No Medium-or-higher finding survived adversarial scrutiny. The four items below are all Low/Informational; each is either by-design audit behavior, a defensive-assert artifact, or a stale-precondition edge mitigated by the serialization lock. None warrants a tracked issue.

### F-001 — Audit pre/post state snapshots in `call_tool` run outside the per-repo lock

- Title: Concurrent writes can produce mismatched audit pre/post states.
- Severity: Low
- Confidence: Medium
- Evidence label: Observed
- Evidence: `scripts/mcp_servers/git/git_server.py::call_tool` takes `pre_state` (line 325) and `post_state` (line 346) around `dispatch_tool(...)`, but the per-repo serialization lock is acquired inside the pipeline (Stage 5b, `write_protection_pipeline.py`). The audit snapshots are not taken under that lock.
- Current behavior: Under two concurrent writes to the same canonical repo, the first writer's audited `post_state` reflects the second writer's completed mutation, so its audit record's pre→post does not correspond to a single logical operation.
- Impact: Real but low — this degrades audit-trail accuracy under concurrency. It is not a security bypass: the enforcement-critical Stage 5b HEAD re-check runs inside the lock, so correctness of the write guard is unaffected.
- Recommended action: None unless concurrent same-repo writes are a common operational pattern requiring a precise audit trail. If so, snapshot `post_state` inside the lock (or derive post-state from the pipeline result).

### F-002 — `allowed_remote_urls` has no startup/posture guard; empty ⇒ silent deny-all

- Title: Remote-URL allowlist not validated at startup.
- Severity: Informational
- Confidence: High
- Evidence label: Observed
- Evidence: `git_models.GitConfig.load()` rejects an empty `protected_branches` (fail-closed, ADR-004) but places no constraint on `allowed_remote_urls`; `validate_git_security()` checks `allowed_repo_paths` but not `allowed_remote_urls`. `_authorize_remote` denies when `url not in cfg.allowed_remote_urls`, so an empty list denies every pull/push.
- Current behavior: An operator who enables writes but omits `allowed_remote_urls` gets a server that starts cleanly and silently rejects every `git_pull`/`git_push` at runtime rather than failing at startup.
- Impact: Fail-closed behavior is correct; the gap is detectability — misconfiguration surfaces as repeated runtime denials instead of a clear startup rejection.
- Recommended action: None required. Optionally add a posture WARNING when write tools are enabled but `allowed_remote_urls` is empty, mirroring the `protected_branches` load-time gate.

### F-003 — `assert state._repo is not None` guards are stripped under `python -O`

- Title: bandit B101 asserts are not runtime guarantees under optimization.
- Severity: Informational
- Confidence: High
- Evidence label: Verified (bandit: 8× B101, all `assert`, 7 in `format_output.py`, 1 in `git_server.py`)
- Evidence: `format_output.py` asserts `state._repo is not None` before every mutating GitPython call; `git_server.py` asserts `result is not None` before returning.
- Current behavior: These asserts double as null guards but are removed when the interpreter runs with `-O` (optimized bytecode), so the guard vanishes under optimization.
- Impact: Low — the real security comes from the pipeline stages and argument validation, not these asserts, and the repo's ruff config permits asserts. No correctness or security boundary depends on them.
- Recommended action: None. If asserts must survive `-O`, convert the `_repo` guards to explicit `if ... is None: raise` checks; otherwise leave as documentation.

### F-004 — Dirty-worktree precondition (Stage 5) runs outside the serialization lock

- Title: Stale dirty-worktree check under concurrency.
- Severity: Informational
- Confidence: Medium
- Evidence label: Observed
- Evidence: `write_protection_pipeline.run()` runs Stage 5 (`verify_preconditions`, including the dirty-worktree guard) before acquiring `_get_repo_lock`; only Stage 5b re-checks HEAD identity inside the lock. Dirty state is not re-verified post-lock.
- Current behavior: Between the dirty check and the mutating call, a concurrent writer could change the worktree. The per-repo lock serializes MCP writers and Stage 5b re-checks HEAD identity, so an MCP-writer race cannot corrupt the guard; only an external concurrent `git` CLI write (documented out-of-scope in `write_protection_pipeline.py`) could observe a stale dirty flag.
- Impact: Low; mitigated by the serialization lock and the documented out-of-scope for external writers.
- Recommended action: None unless external concurrent writers against the same repo become an operational concern.

## Open Questions

- Question: Is F-001's concurrent-same-repo audit gap operationally relevant?
- Why it matters: The audit `pre_condition`/`post_condition` snapshots bracket the operation but not the serialization lock, so their fidelity degrades only when multiple writes target the same canonical repo concurrently.
- Required confirmation: Confirm whether concurrent writes to the same repo are expected. If rare, current behavior is acceptable; if common, snapshot post-state inside the lock for an accurate trail.

## Suggested Tests

- Test target: `git_server.call_tool` with two concurrent writes to the same canonical repo.
- Behavior to verify: Both operations are correctly serialized and each enforces its own Stage 5b HEAD re-check; note whether the audited pre/post states bracket each individual operation.
- Failure mode: A future refactor that moves the pipeline lock outside `call_tool`'s snapshots, or drops Stage 5b, would let a concurrent write bypass the HEAD-identity re-check.

## Documentation Notes

- Target document: the `validate_git_security` posture contract (four check ids, always present) and the `GitConfig.load()` fail-closed contract.
- Required update: none. The numeric/allowlist/protected-branch/read-only posture checks match the runtime guards; the remote-URL allowlist is intentionally unguarded at startup (see F-002).

## Final Recommendation

**Proceed.** No Medium-or-higher finding survives adversarial scrutiny. The toolchain is green (ruff, mypy clean over 11 files; bandit only B101 `assert` notes; 418 git tests pass). The four Low/Informational items are by-design audit behavior, defensive-assert artifacts, or stale-precondition edges mitigated by the serialization lock; none is actionable enough to warrant a tracked issue. The single Open Question (F-001 concurrent audit fidelity) is confirmable without code change and does not block.
