# Plan: web_search import-time refusal claim contradicts `require_auth_token` at import

## Goal
- Correct the `_build_security_posture()` docstring in `scripts/mcp_servers/web_search/web_search_server.py` so it describes the true import-time behavior — an empty `auth_token` causes import refusal (failure) via `require_auth_token` — instead of denying any import-time refusal and calling it a warning.

## Priority
Medium

## Scope
- **In-Scope**: rewriting the `_build_security_posture()` docstring (lines 63-72) in `web_search_server.py`; validation that no executable line changes.
- **Out-of-Scope**: all executable code in `web_search_server.py`; `require_auth_token` / `attach_auth_middleware` semantics (`scripts/mcp_servers/server.py`); other servers' docstrings; the stale module docstring in `tests/mcp_servers/web_search/test_web_search_health_posture.py:8-9` (see Problem — flagged, not changed, per the Issue's Out-of-Scope).
- **Dependencies**: N/A: none.

## Background
web_search loads its config via a module-level singleton, builds its security posture at import (`web_search_server.py:83 _security_posture: SecurityPosture = _build_security_posture(_cfg)`), and wires auth middleware at import (`web_search_server.py:101-104`) with `attach_auth_middleware(cast(_FastAPIApp, app), require_auth_token("web-search-mcp", "MCP_WEB_SEARCH_AUTH_TOKEN", _cfg.auth_token))`. `require_auth_token` lives in `scripts/mcp_servers/server.py:137-148` and raises `RuntimeError` at call time when the token is empty. Shell-style servers refuse at import via a module-level guard (`scripts/mcp_servers/shell/shell_server.py:120-124 if not _cfg.auth_token: raise RuntimeError(...)`); web_search refuses via the middleware helper instead. The posture flow itself (`scripts/shared/security/startup_flow.py:186`) never raises — that part of the docstring is accurate.

## Problem
The `_build_security_posture()` docstring (`web_search_server.py:69-71`) claims: "Unlike Shell, this module has no import-time refusal for an empty token, so the posture is where an empty auth_token first becomes visible, as a warning rather than a failure." Step 2 verification confirms this is false: `require_auth_token(...)` is evaluated at module scope (`web_search_server.py:103`) and raises `RuntimeError` on an empty token (`server.py:141-146`), so the module import fails. True order at import with an empty token: the posture is built first (its common auth-token check records a warning — `startup_flow.py` never raises), then `require_auth_token` refuses the import. Two report-only flags from Step 2 (out-of-scope, no change here):

- No other server module makes the "no import-time refusal / warning rather than failure" claim — repo grep matches only this docstring (resolves the Issue's Unresolved Question for this claim class).
- `tests/mcp_servers/web_search/test_web_search_health_posture.py:8-9` states conftest sets `MCP_WEB_SEARCH_AUTH_TOKEN` to an empty string, but `tests/conftest.py:230-248` actually sets it (and all MCP tokens) to `"test-token"`; the stale test-docstring is a same-class doc/behavior mismatch worth a follow-up but lies in a test file the Issue excludes.

## Reason for Change
A security-behavior claim in the docstring is the opposite of reality: a reader relying on it could believe an empty token degrades to a warning and deploy web_search-mcp without authentication, when in fact the server refuses to import without a token.

## Implementation Intent
Rewrite only the docstring prose: keep the accurate statements (the posture flow never raises; only the server-security stage is supplied; the mechanism differs from Shell's module-level guard) and replace the false sentence with the true behavior — an empty `auth_token` is a failure: the module refuses to import via `require_auth_token` inside the `attach_auth_middleware` call, after the posture (with its auth-token warning) has been built.

## Requirements
- `REQ-001`: the `_build_security_posture()` docstring states that an empty `auth_token` causes import-time refusal via `require_auth_token` (called inside `attach_auth_middleware` at module scope), i.e. a failure, not a warning; no "no import-time refusal" claim remains.
- `REQ-002`: the docstring keeps the accurate Shell comparison reframed as a mechanism difference (middleware helper vs. module-level `if not token: raise` guard), and keeps the accurate "flow never raises" statement about the posture flow itself.
- `REQ-003`: no executable code changes: `web_search_server.py`'s diff touches only the docstring lines; `require_auth_token` / `attach_auth_middleware` semantics are untouched.

## Implementation Target Files
**Freeze status**: Frozen (the single row is `Verified`; `issue-to-plan` Step 8b
Implementation Target Files Validation passed — see `rules/workflow-lifecycle.md`
Implementation Target Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/web_search/web_search_server.py | Modify | Rewrite the false `_build_security_posture()` docstring sentences (lines 69-71) to describe import-time refusal via `require_auth_token`; docstring-only edit | REQ-001, REQ-002, REQ-003 | False claim at `web_search_server.py:69-71`; module-scope `attach_auth_middleware(..., require_auth_token(...))` at lines 101-104; posture built at line 83; `require_auth_token` raises `RuntimeError` at `scripts/mcp_servers/server.py:141-146` (checked in Step 2) | `T1` (consistency check), existing `tests/mcp_servers/web_search` suite | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/mcp_servers/server.py | `require_auth_token` (lines 137-148) and `attach_auth_middleware` (lines 96-135) semantics — the exact behavior the new docstring must describe | REQ-001, REQ-003 |
| scripts/mcp_servers/shell/shell_server.py | Shell-style module-level guard (lines 120-124) — the accurate half of the Shell comparison | REQ-002 |
| scripts/shared/security/startup_flow.py | `run_startup_validation` "never raises, never binds HTTP" (line 186) — the accurate "flow never raises" statement to preserve | REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001): the docstring no longer claims "no import-time refusal" or "warning rather than a failure" for an empty `auth_token`.
- `AC-2` (REQ-001, REQ-002): the docstring accurately describes the middleware-helper-based import refusal (its ordering after the posture build) and the Shell mechanism difference.
- `AC-3` (REQ-003): the diff of `web_search_server.py` contains only docstring-line changes; `uv run pytest tests/mcp_servers/web_search` passes unchanged; ruff / mypy stay clean.

## Tests
- `T1` (REQ-001, REQ-002): documentation consistency check — read `scripts/mcp_servers/server.py:137-148` and `web_search_server.py:83,101-104` and confirm each sentence of the rewritten docstring matches the code (no behavioral tests required, per the Issue's Testing Expectations).
- `T2` (REQ-003): gate suite — `uv run pytest tests/mcp_servers/web_search` and `uv run ruff check scripts/mcp_servers/web_search`; `uv run mypy --no-namespace-packages scripts/mcp_servers/web_search`.

## Documentation Impact
N/A: no `docs/*.md` update required. The Issue's documentation correction is the in-code docstring in the target file (carried in the `Implementation Target Files` table); Step 2 grep found the false claim nowhere in `docs/`.

## Assumptions
- `run_startup_validation` never raising (`startup_flow.py:164-169,186`) remains true at implementation time, so the preserved sentence stays accurate. Falsifiable by `T1`.
- The flag about `test_web_search_health_posture.py:8-9` (stale "empty string" docstring vs. `tests/conftest.py:248 "test-token"`) is report-only; acting on it would need its own Issue.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | N/A: no unresolved unknowns; the Issue's Unresolved Question (same-class mismatches in other servers' docstrings) was resolved in Step 2 for the "no import-time refusal" claim class — repo grep matches only this docstring; the separate stale test-docstring flag is recorded in Problem | — | — | — |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/web_search/web_search_server.py | Modify (docstring only) | None at runtime — docstring text only; no call sites affected (checked in Step 2) | 8 commits | N/A | not applicable (rsynced) |

## Design
Docstring-only correction; no executable-code decision left open. The rewrite must capture the verified import ordering so the prose is literally true for an empty token:

1. `_build_security_posture(_cfg)` runs first (`web_search_server.py:83`); the posture flow never raises (`startup_flow.py:186`), and its common auth-token check records the empty token as a warning.
2. The module-scope `attach_auth_middleware(..., require_auth_token(...))` (`web_search_server.py:101-104`) then refuses the import with `RuntimeError` (`server.py:141-146`).
3. Therefore the accurate phrasing is "the empty token first appears as a posture warning, but the module still refuses to import via `require_auth_token` — a failure, not a degraded-warn mode" — while the Shell comparison becomes a mechanism contrast (helper call vs. module-level guard), not a presence/absence contrast.

Path A classification: 1 modification target, documentation-only behavior, no interface/schema change.

## Implementation steps
1. **Phase 1: Docstring Correction**
   - [ ] Rewrite the `_build_security_posture()` docstring lines 69-71 per the Design's verified ordering, preserving the accurate sentences (REQ-001, REQ-002; File Path: scripts/mcp_servers/web_search/web_search_server.py)
2. **Phase 2: Verification & Deployment Hand-off**
   - [ ] Run `T1` consistency check and `T2` gates; confirm the diff is docstring-only (`git diff` review) (REQ-003; File Path: scripts/mcp_servers/web_search/web_search_server.py)
   - [ ] Deployment validation/scripts check: commit and push the change, then hand off to `skills/deploy/SKILL.md`; the web_search server runs as a NUITKA onefile binary (`mcp_web_search`), so the hand-off includes the binary rebuild for the docstring text to reach the deployed binary; deploying is the user's decision (approval gate) (REQ-003; File Path: scripts/mcp_servers/web_search/web_search_server.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/web_search/web_search_server.py | Documentation consistency (`T1`) | Read `scripts/mcp_servers/server.py:137-148`, `web_search_server.py:83,101-104`, `scripts/shared/security/startup_flow.py:186` | Every rewritten docstring sentence matches the code |
| scripts/mcp_servers/web_search/web_search_server.py | Regression | `uv run pytest tests/mcp_servers/web_search` | Suite green, unchanged results (no behavior touched) |
| scripts/mcp_servers/web_search/web_search_server.py | Static + diff scope | `uv run ruff check scripts/mcp_servers/web_search`; `uv run mypy --no-namespace-packages scripts/mcp_servers/web_search`; `git diff` review | No errors; diff contains only docstring lines |
| whole change | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No import-layer violations (no imports change) |

## Risks
- **Risk**: the rewrite mis-states the import ordering (posture built before refusal) and creates a new doc/behavior mismatch → **Mitigation**: `T1` grounds every sentence against the three cited code locations; the Design section records the verified ordering.
- **Risk**: an accidental executable edit while editing the docstring (the Issue forbids code changes) → **Mitigation**: `AC-3` requires a docstring-only `git diff` review in Phase 2, plus the unchanged regression suite.
- **Risk**: preserving the "flow never raises" sentence becomes wrong if `startup_flow` changes → **Mitigation**: `startup_flow.py:186` is a documented shared guarantee (REQ-004 stage contract); `T1` re-confirms it at implementation time.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `_build_security_posture()` docstring (scripts/mcp_servers/web_search/web_search_server.py) | In Progress | — | — | REQ-001, REQ-002 |
| 2 | Run consistency check + gates; docstring-only diff review; deploy hand-off incl. mcp_web_search binary rebuild | Pending | — | — | REQ-003; deploy is user-gated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261029-140154_01_scripts_mcp_servers_web_search_web_search_server.py.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-012525_ebrev002_websearch-import-refusal-doc-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-075747
- **Related target files**: scripts/mcp_servers/web_search/web_search_server.py

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Summary / Problem (docstring quote) / Required Changes; confirmed at `web_search_server.py:69-71` and `server.py:141-146` (Step 2) | scripts/mcp_servers/web_search/web_search_server.py | Phase 1 | AC-1, AC-2 | T1 | Explicit in issue |
| REQ-002 | Required Changes ("preserve the accurate part of the comparison"); confirmed against `shell_server.py:120-124` and `startup_flow.py:186` (Step 2) | scripts/mcp_servers/web_search/web_search_server.py | Phase 1 | AC-2 | T1 | Derived from confirmed evidence |
| REQ-003 | Constraints / AI Implementation Instruction ("do not change any executable code") | scripts/mcp_servers/web_search/web_search_server.py | Phase 2 | AC-3 | T2 | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261029-140154 -->