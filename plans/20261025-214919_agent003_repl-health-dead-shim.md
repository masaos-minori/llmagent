# Plan: agent003 repl_health dead shim

## Goal
- Delete the zero-consumer `scripts/agent/repl_health.py` backward-compatibility shim
  and clear every stale reference to it (two live-behavior code comments, the coverage
  omit list, the docstring baseline, and one docs keyword), so the health-check
  functions live only in `agent/services/` and their private symbols are no longer
  importable through a second path.

## Priority
Medium

## Scope
- **In-Scope**:
  - Re-confirm zero importers of `agent.repl_health` (repo `scripts/`, `tests/`,
    deployed `/opt/llm` tree, cron/systemd), then delete `scripts/agent/repl_health.py`.
  - Update the stale comment in `scripts/agent/config_dataclasses.py` (~line 199-200)
    to describe the real services modules.
  - Update the live-wiring claims in `scripts/shared/tool_registry.py`'s module
    docstring (lines 10 and 12) that name `repl_health.py` as an active consumer; the
    actual live consumer is `agent/startup_validation.py` (via
    `agent/services/routing_drift.py`).
  - Remove `"scripts/agent/repl_health.py"` from the coverage omit list in
    `pyproject.toml` (line 163).
  - Regenerate `tools/check_docstrings_baseline.txt` (`--update-baseline`) after the
    deletion; its line 53 entry becomes stale and would otherwise fail
    `check_docstrings.py`.
  - Remove the `repl_health` keyword from
    `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` (line 126) and run the docs
    checkers.
- **Out-of-Scope**:
  - The health-check implementations in `agent/services/` and any rename/reorg there.
  - Historical "Extracted from agent/repl_health.py" provenance notes in
    `agent/services/workflow_schema.py`, `agent/services/tool_validation.py`,
    `agent/services/mcp_tool_discovery.py` docstrings — accurate history, not live
    claims; leave unchanged.
  - `scripts/llmagent.egg-info/SOURCES.txt` (untracked build artifact, regenerates).
- **Dependencies**:
  - `issues/done/20260831-152636_refactor_004_repl_health_separation.md` — depends on
    (archived/closed): the refactor that created the services modules and left this
    shim. Importer absence re-verified against current source in this Plan's
    verification pass.

## Background
The shim was kept when health checks were extracted into `agent/services/` to preserve
`agent.startup`'s old import path. Re-verified at HEAD `b0415bd3d`: no importer in
`scripts/`, `tests/`, or the deployed `/opt/llm/scripts` tree; no cron job, systemd
unit, or running process references it (`crontab -l`, `/etc/cron*`,
`/etc/systemd/system`, `ps` all clean). It re-exports private symbols
(`_probe_mcp_health_detail`, `_validate_tools_response`, `_collect_server_tool_names`,
`_check_tool_definitions`), keeping them a de facto public surface.

## Problem
A shipped module with zero consumers, plus four stale or dangling references the Issue
and verification found:
- `config_dataclasses.py:200` comment: "re-exported by agent/repl_health.py".
- `tool_registry.py:10,12` docstring: presents `repl_health.py` as live wiring
  ("confirmed by the live wiring in repl_health.py") — the live drift checks actually
  run through `startup_validation.py` → `agent/services/routing_drift.py`
  (startup_validation.py:24, :145, :154).
- `pyproject.toml:163` coverage omit entry, and `tools/check_docstrings_baseline.txt:53`
  baseline entry — both become mechanically stale (checker failures) after deletion.
- `docs/22_mcp/mcp_02_02_startup-modes-and-health.md:126` keyword.

## Reason for Change
Dead-module cost: every future health-check refactor must keep the shim consistent for
no consumer, the comments mislead implementers about where functions live, and the
shim's re-export of private symbols weakens the services modules' encapsulation.

## Reason for Change (alternatives considered)
The Issue's alternative "retain-and-document" outcome applies only if an importer is
found; the re-check (repo + deployed + cron/systemd + process table) is clean, so the
delete outcome is selected.

## Implementation Intent
Deletion-first: one file removed, four mechanical reference cleanups, one baseline
regeneration. No logic moves — implementations already live in `agent/services/`.

## Requirements
- `REQ-001`: Re-confirm zero importers of `agent.repl_health` immediately before
  deletion (repo + deployed tree + cron/systemd); delete the shim only on a clean
  result, otherwise switch to the retain-and-document outcome and report.
- `REQ-002`: After the change, `rg 'agent\.repl_health'` finds no live-relationship
  claims under `scripts/` or `tests/`; remaining mentions are historical provenance
  notes only (`agent/services/*` "Extracted from" docstrings).
- `REQ-003`: `config_dataclasses.py` and `tool_registry.py` comments describe the
  actual live consumers (`agent/services/tool_validation.py`,
  `agent/startup_validation.py` via `agent/services/routing_drift.py`).
- `REQ-004`: Toolchain bookkeeping is consistent: `pyproject.toml` no longer omits the
  deleted file from coverage; `tools/check_docstrings_baseline.txt` no longer contains
  the deleted file's entry and `check_docstrings.py` passes.
- `REQ-005`: The `repl_health` keyword is removed from the mcp startup-modes doc and
  the docs checkers pass.
- `REQ-006`: ruff, mypy, `lint-imports`, docs checkers, `check_docstrings.py`, and the
  full test suite pass after the change (a suite Pass proves no hidden importer).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/repl_health.py | Delete the module | Zero consumers in repo, deployed tree, cron/systemd, process table | REQ-001, REQ-006 / AC-1 | grep over `scripts/`, `tests/`, `/opt/llm/scripts/`, `/opt/llm/tools/`: only self and provenance comments; `crontab -l`, `/etc/cron*`, `/etc/systemd/system`, `ps` clean | full suite (`tests/`) as importer proof | Verified |
| scripts/agent/config_dataclasses.py | Fix stale comment (~lines 199-200) | Comment claims `_check_tool_definitions` is "re-exported by agent/repl_health.py" — false after deletion | REQ-002, REQ-003 / AC-2 | config_dataclasses.py:200 | tests/agent/test_config_builders.py (must pass unchanged) | Verified |
| scripts/shared/tool_registry.py | Fix docstring live-wiring claims (lines 10, 12) | Docstring names `repl_health.py` as an active consumer; actual live path is `startup_validation.py` → `services/routing_drift.py` (discovered in verification; not listed by the Issue) | REQ-002, REQ-003 / AC-2 | tool_registry.py:10,12; startup_validation.py:24,145,154 | tests/shared/ tool-registry tests (docstring-only change, must pass unchanged) | Verified |
| pyproject.toml | Delete coverage-omit entry line 163 | Omit list would reference a nonexistent file | REQ-004 / AC-3 | pyproject.toml:163 `"scripts/agent/repl_health.py",` inside coverage omit block | coverage run in validation | Verified |
| tools/check_docstrings_baseline.txt | Regenerate with `--update-baseline` | Line 53 `agent/repl_health.py\tmissing separator` becomes a stale entry; the checker fails stale entries (check_docstrings.py:13-15) | REQ-004 / AC-3 | check_docstrings_baseline.txt:53; `check_docstrings.py --update-baseline` flag at check_docstrings.py:20 | `uv run python tools/check_docstrings.py` | Verified |
| docs/22_mcp/mcp_02_02_startup-modes-and-health.md | Remove `repl_health` keyword (line 126) | Keyword asserts a live relationship that no longer exists | REQ-005 / AC-4 | doc line 126 `- repl_health` | docs checkers (`check_docs_structure.py`, gate `manage_frontmatter`) | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/startup_validation.py | The actual live consumer of `check_routing_drift` / `check_routing_safety_tiers` (:24, :145, :154) — the replacement name for tool_registry.py's docstring fix | REQ-003 |
| scripts/agent/services/tool_validation.py | Real home of `_check_tool_definitions` et al. — the replacement reference for the config_dataclasses.py comment | REQ-003 |
| scripts/agent/services/routing_drift.py | Live drift-check path invoked by startup_validation — confirms shim removal does not break drift detection | REQ-001, REQ-003 |
| tests/agent/test_repl_health.py, tests/agent/test_repl_health_malformed.py | Confirm they import `agent.services.*` directly (:16-26 / :4), not the shim; they stay unchanged | REQ-006 |
| tools/check_docstrings.py | Baseline semantics (stale entries fail, :13-15) and `--update-baseline` (:20) driving the regeneration step | REQ-004 |
| scripts/agent/services/workflow_schema.py, scripts/agent/services/tool_validation.py, scripts/agent/services/mcp_tool_discovery.py | Provenance mentions of repl_health are historical notes; verified they must NOT be edited (out-of-scope) | REQ-002 |

## Acceptance Criteria
- `AC-1` (REQ-001): `scripts/agent/repl_health.py` does not exist in the repo and
  disappears from `/opt/llm/scripts/agent/` on the next deploy (deploy.sh rsyncs
  `scripts/` with `--delete`).
- `AC-2` (REQ-002, REQ-003): `rg 'agent\.repl_health' scripts/ tests/` returns only
  the historical "Extracted from" notes under `agent/services/`; `config_dataclasses.py`
  and `tool_registry.py` comments name the real live consumers.
- `AC-3` (REQ-004): `pyproject.toml` coverage omit no longer lists the deleted file;
  `uv run python tools/check_docstrings.py` reports OK.
- `AC-4` (REQ-005): the doc's Keywords block no longer contains `repl_health`; docs
  checkers pass.
- `AC-5` (REQ-006): `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages
  scripts/`, `uv run lint-imports`, `uv run python tools/run_validation_gates.py
  --fast` (docs gate included), and `uv run pytest -q` all pass.

## Tests
- `REQ-006`: No new tests. The full suite passing after deletion is the regression
  proof that no hidden importer existed (Issue's testing expectation). Existing
  `tests/agent/test_repl_health*.py` already exercise the services modules directly and
  must pass unchanged; `lint-imports` contracts must remain all-kept.

## Documentation Impact
Per `docs/00_index.md`'s task mapping (MCP startup/health documentation task), the
affected doc is `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` — a frozen target
row (REQ-005). No other doc presents `repl_health` as an active import path (grep
verified: the only docs occurrence is that keyword line). ADR historical docs are
untouched.

## Assumptions
- Production deploy propagates deletions via deploy.sh's `rsync --delete` over
  `scripts/` and `tests/`; no manual cleanup on the deployed tree is needed.
- "Live relationship" vs "historical note": docstrings saying "Extracted from
  agent/repl_health.py" are provenance and stay; docstrings claiming current wiring
  are fixed.
- `check_docstrings_baseline.txt` regeneration is done via the tool's
  `--update-baseline`, not by hand-editing line 53.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether an external script outside the repo/deployed trees (another host, ad-hoc ops script) imports `agent.repl_health` at runtime | Cannot grep code that lives outside this machine | Checked everything reachable: repo `scripts/`+`tests/`, `/opt/llm/scripts/`+`/opt/llm/tools/`, `crontab -l`, `/etc/cron*`, `/etc/systemd/system`, `ps` — all clean. Before the production deploy that carries the deletion, re-run the `/opt/llm` grep on the deploy host | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/repl_health.py | Delete | None measured (zero importers) — startup health path is unaffected (startup_validation imports services directly) | 1 | 1 (single-author repo; git-fame not installed, `git log` author check) | Deleted on next deploy via rsync `--delete`; no new deps; repl/service restarts on the regular deploy cycle, none required for correctness |
| scripts/agent/config_dataclasses.py | Comment fix only | None (comment text) | 8 | 1 | rsynced; no restarts required |
| scripts/shared/tool_registry.py | Docstring fix only | None (docstring text); file itself stays active as drift-detection input | 5 | 1 | rsynced; no restarts required |
| pyproject.toml | Remove one omit line | Coverage config only | 8 | 1 | Not deployed; dev/CI only |
| tools/check_docstrings_baseline.txt | Regenerated baseline | Toolchain gate only | 4 | 1 | tools/ rsynced; no restarts required |
| docs/22_mcp/mcp_02_02_startup-modes-and-health.md | Remove one keyword | Docs only | 20 | 1 | docs rsynced by deploy.sh; no restarts required |

## Design
Architecture analysis (Path B): `repl_health.py` is a leaf re-export layer
(`agent.repl_health` → `agent.services.{mcp_health,routing_drift,tool_validation,workflow_schema}`)
with no inbound edges; import-linter reports "Contracts: 6 kept, 0 broken" both before
and after the removal (the deleted edge direction `agent → agent.services` is inside
the same layer). Removing it restores the services modules' encapsulation: the four
private `_`-prefixed symbols stop being importable through a second module. Dependency
graphing produced the concrete 6-file change list (target table). Operational check:
no process, cron, or systemd unit touches the shim. The high churn (20) on
mcp_02_02 is docs churn; the single-keyword edit is mechanical. Historical analysis:
the shim had 1 commit in 30 days (it is frozen transitional code).

## Implementation steps

1. **Phase 1: Importer re-check and deletion (gated)**
   - [ ] Re-run importer grep over `scripts/`, `tests/`, `/opt/llm/scripts/`,
     `/opt/llm/tools/`, plus cron/systemd/process checks (REQ-001; scripts/agent/repl_health.py)
   - [ ] Delete the shim only on a clean result; otherwise stop and report the
     importer (REQ-001; scripts/agent/repl_health.py)
2. **Phase 2: Reference cleanup**
   - [ ] Fix the services/re-export comment (~lines 199-200) to name
     `agent/services/tool_validation.py` directly (REQ-003; scripts/agent/config_dataclasses.py)
   - [ ] Fix docstring lines 10/12 to name `agent/startup_validation.py` (via
     `agent/services/routing_drift.py`) as the live consumer (REQ-003; scripts/shared/tool_registry.py)
   - [ ] Remove the coverage-omit line 163 (REQ-004; pyproject.toml)
   - [ ] Remove the `repl_health` keyword (REQ-005; docs/22_mcp/mcp_02_02_startup-modes-and-health.md)
3. **Phase 3: Toolchain regeneration and verification**
   - [ ] Regenerate the baseline: `uv run python tools/check_docstrings.py --update-baseline` (REQ-004; tools/check_docstrings_baseline.txt)
   - [ ] Run gates: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run lint-imports`, `uv run python tools/check_docstrings.py`, docs checkers (`check_docs_structure.py` + `manage_frontmatter` fast gate) (REQ-006; scripts/agent/repl_health.py)
   - [ ] Run `uv run pytest -q` full suite (REQ-006; scripts/agent/repl_health.py)
   - [ ] Deployment validation: confirm next deploy removes the deployed copy
     (`rsync --delete`) and that `/opt/llm` greps clean before deploy (UNK-01)
     (REQ-001, REQ-006; scripts/agent/repl_health.py)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/repl_health.py | Pre-delete gate | `grep -rn "agent\.repl_health" scripts/ tests/ /opt/llm/scripts/ /opt/llm/tools/` | only provenance comments, no imports |
| scripts/agent/repl_health.py | Integration (importer absence) | `uv run pytest -q` | full suite Pass |
| scripts/agent/repl_health.py, scripts/shared/tool_registry.py | Architecture | `uv run lint-imports` | Contracts: 6 kept, 0 broken |
| scripts/ | Static gates | `uv run ruff check scripts/` ; `uv run mypy --no-namespace-packages scripts/` | both exit 0 |
| pyproject.toml, tools/check_docstrings_baseline.txt | Toolchain consistency | `uv run python tools/check_docstrings.py` | OK, no stale entries |
| docs/22_mcp/mcp_02_02_startup-modes-and-health.md | Docs gate | `uv run python tools/check_docs_structure.py` ; fast gate `manage_frontmatter` | Pass |

## Risks
- **Risk**: An unreachable external consumer (UNK-01) breaks at the deploy that
  removes the shim. → **Mitigation**: deletion is repo-local until deploy; re-run the
  deployed-tree grep immediately before deploy (Phase 3 step); restoration is a single
  `git revert` of one commit.
- **Risk**: Stale baseline entry (check_docstrings_baseline.txt:53) fails the gate if
  regeneration is skipped. → **Mitigation**: regeneration is an explicit frozen step
  (REQ-004), and `check_docstrings.py` failure makes omission loud.
- **Risk**: `tool_registry.py` churn (5 commits/30d) + single-author bus factor —
  concurrent edits could conflict with the docstring fix. → **Mitigation**: docstring-only
  diff keeps merge conflicts trivial; sequence this change immediately after any
  in-flight tool_registry work.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Importer re-check (repo/deployed/cron/systemd/ps) | Pending | — | — | Phase 1 gate |
| 2 | Delete scripts/agent/repl_health.py | Pending | — | — | Phase 1 |
| 3 | Comment fix config_dataclasses.py | Pending | — | — | Phase 2 |
| 4 | Docstring fix tool_registry.py | Pending | — | — | Phase 2 |
| 5 | Remove coverage-omit line pyproject.toml | Pending | — | — | Phase 2 |
| 6 | Remove keyword mcp_02_02 doc | Pending | — | — | Phase 2 |
| 7 | Regenerate docstrings baseline | Pending | — | — | Phase 3 |
| 8 | Gate suite: ruff/mypy/lint-imports/docs/check_docstrings | Pending | — | — | Phase 3 |
| 9 | Full pytest suite | Pending | — | — | Phase 3 |
| 10 | Pre-deploy grep + deploy.sh convergence check | Pending | — | — | Phase 3 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blockers identified | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261025-210146_agent003_repl-health-dead-shim.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261025-214919
- **Related target files**: scripts/agent/repl_health.py, scripts/agent/config_dataclasses.py, scripts/shared/tool_registry.py, pyproject.toml, tools/check_docstrings_baseline.txt, docs/22_mcp/mcp_02_02_startup-modes-and-health.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes item 1 / Constraints; re-verified greps + cron/systemd/ps checks | scripts/agent/repl_health.py | Phase 1 | AC-1 | Validation plan rows 1-2 | Explicit in issue |
| REQ-002 | Issue Acceptance Criteria; verification distinguished provenance vs live claims | scripts/agent/repl_health.py | Phase 1 | AC-2 | Validation plan row 1 | Explicit in issue |
| REQ-003 | Issue Background (config_dataclasses comment) + discovered live-wiring claims at tool_registry.py:10,12 | scripts/agent/config_dataclasses.py | Phase 2 | AC-2 | Static gates row 4 | Explicit in issue |
| REQ-003 | Same, second occurrence | scripts/shared/tool_registry.py | Phase 2 | AC-2 | Static gates row 4 | Derived from confirmed evidence |
| REQ-004 | Discovered in verification (pyproject omit; baseline staleness semantics check_docstrings.py:13-15) | pyproject.toml | Phase 2 | AC-3 | Validation plan row 5 | Derived from confirmed evidence |
| REQ-004 | Same, second occurrence | tools/check_docstrings_baseline.txt | Phase 3 | AC-3 | Validation plan row 5 | Derived from confirmed evidence |
| REQ-005 | Issue Required Changes item 4 / Documentation Impact | docs/22_mcp/mcp_02_02_startup-modes-and-health.md | Phase 2 | AC-4 | Validation plan row 6 | Explicit in issue |
| REQ-006 | Issue Acceptance Criteria / Testing Expectations; lint-imports baseline "6 kept" measured | scripts/agent/repl_health.py | Phase 3 | AC-5 | Validation plan rows 2-4 | Explicit in issue |
