## Goal
State strict-only startup behavior (REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line numbers were read on 2026-11-10 before the code phases; re-locate them with `rg` if the file changed. Strict-only startup: tool-definition mismatch and routing drift are always FATAL with no toggle; empty `allowed_tools` denies every tool (also after reload); empty `allowed_root` and empty `protected_branches` (git, github) are rejected at config load; empty `path_denylist` stays permitted as a registered ADR-004 exception; `security_profile`/`SecurityProfile` no longer exist.
- The document is edited in Phase 6, after the code phases, so it describes the final behavior.
- This file is shared with the (archived) adrrev002 Plan, which edited a different paragraph (archive retention note); edits here are limited to the startup-severity bullets.

## Design decisions
- Describe behavior only; do not copy concrete config values (`skills/DESIGN.md` Docs content policy).
- English only (`skills/DESIGN.md` Output language).

## Alternatives considered
N/A: documentation-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
### Procedure
1. Line 70: `tool_definitions` severity is always FATAL; delete the 'strict mode / WARNING otherwise' and the `security_profile` clause.
2. Line 71: `routing_drift` is always FATAL, including an unexpected failure of the drift check; delete the `routing_drift_strict` wording.
3. Line 72: delete 'Drift and tool-definition findings are FATAL only in strict mode'; keep the ADR-004 required/non-required rule for discovery.
4. Line 88: leave the WAL `allowed_root` sentence unchanged (the WAL manager is not a Plan target).
### Method
- Locate each statement with `rg -n 'tool_definitions_strict|routing_drift_strict|security_profile|SecurityProfile|accept_all_for_tests|list_tools|allowed_tools|allowed_root|protected_branches|path_denylist|fail-open' docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` and read the surrounding lines before editing.
### Details
- Target behavior to state: Strict-only startup: tool-definition mismatch and routing drift are always FATAL with no toggle; empty `allowed_tools` denies every tool (also after reload); empty `allowed_root` and empty `protected_branches` (git, github) are rejected at config load; empty `path_denylist` stays permitted as a registered ADR-004 exception; `security_profile`/`SecurityProfile` no longer exist.
- After the edit, `rg -n 'security_profile|SecurityProfile|accept_all_for_tests|list_tools_with_server_key' docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` returns nothing (AC-07, AC-05, AC-06).

## Compatibility considerations
N/A: documentation only; no code or config behavior changes in this row.

## Security considerations
N/A: documentation only; the text must not weaken the described fail-closed behavior.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `uv run python tools/check_docs_content_policy.py --strict`, `uv run python tools/check_docs_japanese.py`, `uv run python tools/check_docs_consistency.py --domain agent`.

## Completion criteria
- Every listed statement is changed, the checkers above pass, and no removed name remains in the file.

## Out of Scope
- Renaming `mcp_06_09_startup-validation-behavior-tool_definitions_strict.md`; any file other than the target; writing the ADR-004 rationale text (maintainer, UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation > Procedure | Done | 20261110-231551 | 20261110-231551 | startup table rows rewritten: tool_definitions and routing_drift (incl. unexpected check failure) always FATAL, strict-only startup wording and security_profile/routing_drift_strict removed; ADR-004 required/non-required rule kept; WAL allowed_root line unchanged |
| 2 | Run the documentation checkers per Validation plan | Done | 20261110-231551 | 20261110-231551 | structure/consistency --domain agent/quality/content-policy --strict pass |

### Verification Findings
| Item | Finding | Action taken |
|------|---------|--------------|
| VF-1 | Procedure Assumption 4 treated routing-drift check failure as SKIPPED; implementation is add_fatal (startup_validation.py:143-153) | Procedure wording and target doc row state FATAL |
| VF-2 | Procedure Verification Steps implied strict-conditional tool_definitions tests; current code has no such toggle: finding is always FATAL (tool_validation.py, mcp_tool_discovery.py) | Doc states unconditional FATAL |

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
- **Requirement ID**: REQ-008
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
