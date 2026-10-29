# Plan: mdq `_load_auth_token` does not catch the exception `ConfigLoader.load()` actually raises

## Goal
- Make the MDQ server's two module-scope config reads (`_load_auth_token()` and `_collect_dependencies()`) tolerate the config errors `ConfigLoader.load()` actually raises, so a missing/broken `mdq_mcp_server.toml` degrades to the documented fail-closed empty-config path instead of raising at import, and correct the module comment that claims the opposite.

## Priority
Low

## Scope
- **In-Scope**: extending the `except` tuple in `scripts/mcp_servers/mdq/mdq_server.py::_load_auth_token()` and `scripts/mcp_servers/mdq/health_check.py::_collect_dependencies()` to cover `ConfigMissingError` / `ConfigParseError` / `ConfigReadError`; rewriting the misleading module comment in `mdq_server.py`; regression tests for both paths.
- **Out-of-Scope**: `scripts/shared/config_loader.py` and `scripts/shared/config_errors.py` (explicitly untouchable per the Issue's AI Implementation Instruction); other MCP servers' config reads — Step 2 grep found no other server with the same stale tuple (report flag only, no changes); extending either `except` to non-config exceptions (e.g. sqlite probe errors in `health_check.py`).
- **Dependencies**: N/A: none.

## Background
Every MCP server builds its security posture once at import. The MDQ server reads its Bearer token via `_load_auth_token()` (`scripts/mcp_servers/mdq/mdq_server.py:72-78`), invoked at module scope (`mdq_server.py:81 _AUTH_TOKEN: str = _load_auth_token()`), and builds its posture from `_collect_dependencies()` (`scripts/mcp_servers/mdq/health_check.py:113`), invoked at module scope (`mdq_server.py:88-97`). The intended degradation path is: config unreadable → empty config view → empty token → the module-level posture gate fails closed at startup. The shared loader (`scripts/shared/config_loader.py`) never surfaces a bare `FileNotFoundError` from `load()`: `load()` raises `ValueError` on missing/parse error (`config_loader.py:80` docstring), implemented in `_load_single()` as `FileNotFoundError` → `ConfigMissingError` (`config_loader.py:152-153`), TOML/JSON decode → `ConfigParseError` (`config_loader.py:154-157`), read OSError → `ConfigReadError` (`config_loader.py:159`); all three are `ValueError` subclasses (`scripts/shared/config_errors.py:5,14,23`).

## Problem
Both mdq call sites catch only name-based tuples that omit the loader's real error hierarchy:

- `mdq_server.py:76` — `except (FileNotFoundError, KeyError, TypeError)`: a missing `mdq_mcp_server.toml` raises `ConfigMissingError` out of `_load_auth_token()` at module scope, so the server import fails outright instead of degrading to the empty-token fail-closed path.
- `health_check.py:169` — `except (FileNotFoundError, PermissionError, KeyError, TypeError)`: `_collect_dependencies()` does not call `_load_auth_token()`; it reads the config itself (`health_check.py:143 ConfigLoader().load(MDQ_OWN_CONFIG_FILE)`) and independently raises `ConfigMissingError` on a missing file. Fixing only `_load_auth_token()` would leave the import-time behavior unchanged, because `_collect_dependencies()` is also called at module scope (`mdq_server.py:88-96`).
- `mdq_server.py:84-87` — the module comment asserts `_collect_dependencies()` "swallows config/probe exceptions ... so this never raises at import", which is false: neither module-scope caller swallows `ConfigMissingError` (confirmed in Step 2; grep shows this claim exists only in this comment, not in `docs/`).

Out-of-scope flag (Issue Unresolved Question, resolved in Step 2): no other server shares the identical stale tuple — `grep -rn "except (FileNotFoundError" scripts/` matches only the two mdq sites; the other servers' `ConfigLoader().load()` call sites are either unguarded model loaders or a broad-`Exception` health guard (`rag_pipeline_server.py:229`), i.e. the defect is mdq-specific.

## Reason for Change
The catch lists are stale relative to the shared loader's real error hierarchy (introduced when the loader converted `FileNotFoundError` into `ConfigMissingError`), and the comment actively misleads maintainers into believing the MDQ module import is exception-safe when it is not. The Issue was already corrected and downgraded to Low in commit `1d6b0eae8` (its Problem section now names both module-scope callers); this Plan acts on that corrected mechanism.

## Implementation Intent
Extend both `except` tuples to cover the loader's three public `ValueError`-based config error types (explicitly named, per the Issue's preferred option), drop the now-unreachable `FileNotFoundError` entry, and rewrite the module comment so it states exactly what the posture build does and does not swallow. Keep behavior fail-closed and keep the shared loader untouched.

## Requirements
- `REQ-001`: `_load_auth_token()` catches `ConfigMissingError`, `ConfigParseError`, and `ConfigReadError` (in addition to the existing `KeyError` / `TypeError`) and returns `""` for a missing or broken config, preserving the fail-closed empty-token path.
- `REQ-002`: the module comment in `mdq_server.py` states the actual behavior: config errors from `_collect_dependencies()` are recorded under `deps["config"]` with an empty config view; no unconditional "never raises at import" claim remains, and `_load_auth_token()`'s docstring documents the tolerated error types.
- `REQ-003`: `_collect_dependencies()` swallows `ConfigMissingError` / `ConfigParseError` / `ConfigReadError` alongside its current `PermissionError` / `KeyError` / `TypeError`, returning the documented empty-config-view contract (`deps["config"]` recorded, `mdq_cfg` empty — defaults already initialized at `health_check.py:134-140`).
- `REQ-004`: regression tests assert the missing-config path for both callers: `_load_auth_token()` returns `""`, and `_collect_dependencies()` returns without raising with `deps["config"]` recorded.

## Implementation Target Files
**Freeze status**: Frozen (all rows `Verified`; `issue-to-plan` Step 8b Implementation
Target Files Validation passed — see `rules/workflow-lifecycle.md` Implementation Target
Files Validation (Plan Freeze)).

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/mcp_servers/mdq/mdq_server.py | Modify | Replace the stale `except (FileNotFoundError, KeyError, TypeError)` in `_load_auth_token()` with the loader's real config error types, update its docstring, and rewrite the misleading module comment | REQ-001, REQ-002 | `_load_auth_token()` at `mdq_server.py:72-78` with stale tuple at line 76; module-scope call at line 81; false comment at lines 84-87 (checked in Step 2) | `TestStartupRequiresToken` in tests/mcp_servers/mdq/test_mdq_authentication.py, new tests in tests/mcp_servers/mdq/test_mdq_config.py | Verified |
| scripts/mcp_servers/mdq/health_check.py | Modify | Extend the `except` tuple in `_collect_dependencies()` to cover `ConfigMissingError` / `ConfigParseError` / `ConfigReadError` | REQ-003 | `_collect_dependencies()` at `health_check.py:113`, config read at line 143, stale tuple at line 169 (checked in Step 2) | new `_collect_dependencies` regression test in tests/mcp_servers/mdq/test_mdq_config.py | Verified |
| tests/mcp_servers/mdq/test_mdq_config.py | Modify | Add the two missing-config regression tests (no existing test exercises either caller's exception path) | REQ-004 | file exists with config-fallback tests (`test_mdq_config.py:129 test_missing_config_file_falls_back_to_defaults` covers `MdqService`, not `_load_auth_token` / `_collect_dependencies`); grep found no test referencing either symbol (checked in Step 2) | new tests `T1`, `T2` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/shared/config_loader.py | Confirms the loader's public error surface: `load()` docstring ("raises ValueError on missing/parse error", line 80) and `_load_single()`'s conversions at lines 152-159; the Issue's instruction forbids changing it | REQ-001, REQ-003 |
| scripts/shared/config_errors.py | Confirms `ConfigMissingError` / `ConfigParseError` / `ConfigReadError` are the `ValueError`-based hierarchy to catch (`config_errors.py:5,14,23`); untouchable per the Issue | REQ-001, REQ-003 |
| tests/mcp_servers/mdq/test_mdq_authentication.py | Existing fail-closed gate tests (`test_empty_token_refuses_to_start`, `test_unset_token_variable_refuses_to_start`, lines 108-118) that pin the startup-rejection behavior this change must not alter (AC-4) | REQ-001 |

## Acceptance Criteria
- `AC-1` (REQ-001): with `ConfigLoader.load` raising `ConfigMissingError`, `_load_auth_token()` returns `""` instead of raising.
- `AC-2` (REQ-002): the `mdq_server.py` module comment and `_load_auth_token()` docstring match actual behavior; no unqualified "never raises at import" claim remains in the module.
- `AC-3` (REQ-003): with `ConfigLoader.load` raising `ConfigMissingError`, `_collect_dependencies()` returns without raising, with `deps["config"]` recorded and `mdq_cfg` empty.
- `AC-4` (REQ-001, REQ-003): fail-closed behavior preserved — an empty token still makes the posture/startup gate refuse to start (existing `TestStartupRequiresToken` tests stay green); `uv run pytest tests/mcp_servers/mdq` passes; ruff / mypy / bandit `-ll` gates stay clean; `scripts/shared/config_loader.py` and `scripts/shared/config_errors.py` are not modified.

## Tests
- `T1` (REQ-001, REQ-004): unit test in `tests/mcp_servers/mdq/test_mdq_config.py` — monkeypatch `ConfigLoader.load` to raise `ConfigMissingError`, assert `mdq_server._load_auth_token()` returns `""`.
- `T2` (REQ-003, REQ-004): unit test in the same file — same monkeypatch, call `_collect_dependencies()`, assert no exception, `deps["config"]` recorded, `mdq_cfg == {}`.
- `T3` (REQ-001, REQ-003): gate suite — `uv run pytest tests/mcp_servers/mdq` (baseline recorded in Step 5: 412 passed, 1 skipped) including the existing start-gate tests (`AC-4`).
- `T4` (REQ-004): static gates — `uv run ruff check scripts/mcp_servers/mdq tests/mcp_servers/mdq`; `uv run mypy --no-namespace-packages scripts/mcp_servers/mdq`; `uv run bandit -r scripts/ -c pyproject.toml -ll` (baseline recorded in Step 5: no medium/high findings in `scripts/mcp_servers/mdq/`).

## Documentation Impact
N/A: no `docs/*.md` update required. The Issue's requested documentation fixes are the in-code module comment and `_load_auth_token()` docstring in `mdq_server.py` (carried in the `Implementation Target Files` table); Step 2 grep confirmed the false "never raises at import" claim exists nowhere in `docs/`.

## Assumptions
- `ConfigLoader()` is constructed with no allowed-files restriction at both mdq call sites (`config_loader.py:73 __init__` takes only `config_dir`), so `ConfigPermissionError(RuntimeError)` is unreachable there and stays out of the catch lists. Falsifiable by inspecting the call sites (already confirmed in Step 2: both call `ConfigLoader()` bare).
- `mdq_mcp_server.toml` is TOML, so the loader's one bare-`ValueError` site (`config_loader.py:148`, non-mapping JSON top-level) is unreachable from these call names; explicit subclass catching is therefore complete for mdq's config reads. Falsifiable if the config name ever changes to a JSON file.
- Both `except` lists drop the `FileNotFoundError` entry because `load()` never surfaces it (`_load_single` converts it); `PermissionError` is kept in `health_check.py` because its DB-probe block can still raise a raw `PermissionError` outside the loader.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | N/A: no unresolved unknowns; the Issue's Unresolved Question (do other servers share the stale tuple?) was resolved in Step 2 — repo-wide grep found the tuple only in the two mdq sites | — | — | — |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here is a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/mcp_servers/mdq/mdq_server.py | Modify | Low — MDQ server module import path only; no public function signature changes (checked in Step 2) | 3 commits | N/A | not applicable (rsynced) |
| scripts/mcp_servers/mdq/health_check.py | Modify | Low — imported by `mdq_server.py` and the MDQ /health endpoint only (checked in Step 2) | 2 commits | N/A | not applicable (rsynced) |
| tests/mcp_servers/mdq/test_mdq_config.py | Modify | Low — test file, no production importers (checked in Step 2) | 0 commits | N/A | not applicable (rsynced) |

## Design
Design decision (resolves the Issue's open choice between explicit config-error classes and a base-`ValueError` catch): catch the three explicit classes `ConfigMissingError` / `ConfigParseError` / `ConfigReadError` — the Issue's preferred option. Grounds, from Step 2 verification:

1. These three are the complete public `ValueError`-based error surface reachable from `load()` on a `.toml` config name (`config_loader.py:152-159`; confirmed hierarchy `config_errors.py:5,14,23`).
2. A base-`ValueError` catch in `health_check.py` would be dangerously wide: its `try` block is not just the config read but the whole DB/schema/index probe (`health_check.py:142-168`), so `ValueError` could silently swallow probe-side bugs. Explicit classes keep the swallow scoped to config errors.
3. The staleness risk of explicit enumeration (the root cause of this Issue) is bounded by `T1`/`T2` pinning the contract and by the loader's error hierarchy being a frozen shared contract (the Issue forbids changing it).

New imports: `from shared.config_errors import ConfigMissingError, ConfigParseError, ConfigReadError` in both mdq modules — `mcp_servers → shared` is an existing, compliant import direction (`mdq_server.py:23-28` already imports `shared.*`). No change to the posture gate, the fail-closed startup semantics, or the loader.

Path A classification: 3 modification targets, no schema/interface/module-structure change.

## Implementation steps
1. **Phase 1: Core Logic Implementation**
   - [ ] Extend `_load_auth_token()`'s `except` to the three config error classes (dropping `FileNotFoundError`), update its docstring, and rewrite the module comment at `mdq_server.py:84-87` (REQ-001, REQ-002; File Path: scripts/mcp_servers/mdq/mdq_server.py)
   - [ ] Extend `_collect_dependencies()`'s `except` to the three config error classes, keeping `PermissionError` / `KeyError` / `TypeError` (REQ-003; File Path: scripts/mcp_servers/mdq/health_check.py)
2. **Phase 2: Test Update**
   - [ ] Add `T1` / `T2` missing-config regression tests (REQ-004; File Path: tests/mcp_servers/mdq/test_mdq_config.py)
3. **Phase 3: Verification & Deployment Hand-off**
   - [ ] Run the Validation plan gates (`uv run pytest tests/mcp_servers/mdq`, ruff, mypy, bandit `-ll`, diff-cover >= 90% on changed lines) (REQ-004; File Paths: scripts/mcp_servers/mdq/mdq_server.py, scripts/mcp_servers/mdq/health_check.py, tests/mcp_servers/mdq/test_mdq_config.py)
   - [ ] Deployment validation/scripts check: commit and push the change, then hand off to `skills/deploy/SKILL.md`; note the MDQ server runs as a NUITKA onefile binary (`mcp_mdq`), so the hand-off must include the binary rebuild; deploying is the user's decision (approval gate) (REQ-001; File Paths: scripts/mcp_servers/mdq/mdq_server.py, scripts/mcp_servers/mdq/health_check.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/mcp_servers/mdq/mdq_server.py | Unit (`T1`) | `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py -v` | `_load_auth_token()` returns `""` on `ConfigMissingError` |
| scripts/mcp_servers/mdq/health_check.py | Unit (`T2`) | `uv run pytest tests/mcp_servers/mdq/test_mdq_config.py -v` | `_collect_dependencies()` returns empty-config view, no raise |
| both source files | Regression | `uv run pytest tests/mcp_servers/mdq` | 412+ passed including the existing start-gate tests (fail-closed preserved) |
| both source files | Static | `uv run ruff check scripts/mcp_servers/mdq tests/mcp_servers/mdq`; `uv run mypy --no-namespace-packages scripts/mcp_servers/mdq`; `uv run bandit -r scripts/ -c pyproject.toml -ll` | No errors; no medium/high bandit findings |
| diff scope | Coverage | `uv run coverage run -m pytest tests/`; `uv run coverage xml`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | >= 90% coverage on changed lines (baseline recorded in Step 5: clean tree vs master, "no lines with coverage information"; the Plan MUST raise it to the `rules/toolchain.md` threshold) |
| whole change | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No import-layer violations (new `shared.config_errors` imports stay within the existing `mcp_servers → shared` direction) |

## Risks
- **Risk**: a wider `except` could mask future non-config bugs at import → **Mitigation**: catch lists name only the three config error classes (Design point 2); `T1`/`T2` pin exactly those paths; `PermissionError` scope unchanged.
- **Risk**: dropping `FileNotFoundError` from the tuples could break a path that still surfaces a raw one → **Mitigation**: Step 2 verification shows `load()` never surfaces it (`_load_single` converts at `config_loader.py:152-153`); full mdq suite (`T3`) guards the regression.
- **Risk**: the import of `shared.config_errors` could violate the import-layer contract → **Mitigation**: `lint-imports` row in the Validation plan; the direction `mcp_servers → shared` is already used at `mdq_server.py:23-28`.
- **Risk**: the rewritten comment could overclaim again (the current one does) → **Mitigation**: `AC-2` requires the comment to name only the config-error swallow; review point in Phase 1.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix both catch lists + module comment (scripts/mcp_servers/mdq/mdq_server.py, scripts/mcp_servers/mdq/health_check.py) | In Progress | — | — | REQ-001, REQ-002, REQ-003 |
| 2 | Add regression tests (tests/mcp_servers/mdq/test_mdq_config.py) | In Progress | — | — | REQ-004 |
| 3 | Run validation gates; commit/push; deploy hand-off incl. mcp_mdq binary rebuild | Pending | — | — | REQ-004; deploy is user-gated |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261029-135744_01_scripts_mcp_servers_mdq_mdq_server.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261029-135744_02_scripts_mcp_servers_mdq_health_check.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261029-135744_03_tests_mcp_servers_mdq_test_mdq_config.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261029-012525_ebrev001_mdq-config-loader-exception-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-075321
- **Related target files**: scripts/mcp_servers/mdq/mdq_server.py, scripts/mcp_servers/mdq/health_check.py, tests/mcp_servers/mdq/test_mdq_config.py

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Summary / Problem / Required Changes; confirmed against `mdq_server.py:72-81` (Step 2) | scripts/mcp_servers/mdq/mdq_server.py | Phase 1 | AC-1, AC-4 | T1, T3 | Explicit in issue |
| REQ-002 | Problem (comment quote) / Required Changes; comment confirmed at `mdq_server.py:84-87` (Step 2) | scripts/mcp_servers/mdq/mdq_server.py | Phase 1 | AC-2 | Phase 1 review point | Explicit in issue |
| REQ-003 | Required Changes (`_collect_dependencies` omission); confirmed at `health_check.py:143,169` (Step 2) | scripts/mcp_servers/mdq/health_check.py | Phase 1 | AC-3, AC-4 | T2, T3 | Explicit in issue |
| REQ-004 | Required Changes / Testing Expectations; no existing test covers either caller (Step 2) | tests/mcp_servers/mdq/test_mdq_config.py | Phase 2 | AC-1, AC-3 | T1, T2, T4 | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261029-135744 -->