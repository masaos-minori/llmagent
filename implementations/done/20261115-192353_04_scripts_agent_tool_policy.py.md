## Goal

Point `scripts/agent/tool_policy.py`'s static side-effect classification (`_STATIC_SIDE_EFFECT_TOOLS`) at the imported canonical `ALL_SIDE_EFFECTING_TOOLS` (new), so risk classification, dedup, and retry suppression share one source — with membership unchanged.

## Scope
**Release unit**: N/A: not part of a release unit

- Covers `REQ-004`: `tool_policy.py` derives its static side-effect membership from the canonical set, keeping its operation-type tiers intact.

## Assumptions
- `ALL_SIDE_EFFECTING_TOOLS` is created by sibling procedure `20261115-192353_01_scripts_shared_tool_constants.py.md` and already equals `tool_policy._STATIC_SIDE_EFFECT_TOOLS` today (verified: both 25 members, empty symmetric difference). Delegation is behavior-preserving.
- The canonical name resolves from the earlier-`seq` sibling; this document does not create it.

## Design decisions
- Re-point only the side-effect membership set (line 131's `static_write` check). Keep the granular tier sets (`_ALL_WRITE_TOOLS`, `_EXEC_TOOLS`, `_GITHUB_MUTATION_TOOLS`) and the tier branches in `classify_operation_type` (lines 104-110) so WRITE/DELETE/EXECUTE/API_WRITE classification is unchanged.

## Alternatives considered
- N/A: the Plan fixes delegating `_STATIC_SIDE_EFFECT_TOOLS` while preserving tiers.

## Implementation
### Target file
- `scripts/agent/tool_policy.py`

### Procedure
1. Add `ALL_SIDE_EFFECTING_TOOLS` to the `from shared.tool_constants import (...)` block (lines 20-28). Keep the existing category imports (`WRITE_TOOLS`, `DELETE_TOOLS`, `GIT_WRITE_TOOLS`, `RAG_WRITE_TOOLS`, `CICD_WRITE_TOOLS`, `GITHUB_WRITE_TOOLS`, `GITHUB_DANGEROUS_TOOLS`, `SHELL_TOOLS`, `MDQ_WRITE_TOOLS`) — they remain used by the tier sets and tier branches (lines 78-79, 104-110, 451-453, 518).
2. Replace `_STATIC_SIDE_EFFECT_TOOLS: frozenset[str] = (_ALL_WRITE_TOOLS | DELETE_TOOLS | _EXEC_TOOLS | _GITHUB_MUTATION_TOOLS)` (lines 82-84) with `_STATIC_SIDE_EFFECT_TOOLS: frozenset[str] = ALL_SIDE_EFFECTING_TOOLS`.

### Method
- Membership-preserving: because the two sets are already equal, no tool's classification changes. `_ALL_WRITE_TOOLS`, `_EXEC_TOOLS`, and `_GITHUB_MUTATION_TOOLS` are kept (still referenced for tier resolution), so no import becomes unused.

### Details
- Do not modify `classify_operation_type`'s tier branches (lines 104-110) or the `check_write_classification` and approval paths (lines 451-453, 518). Only the `_STATIC_SIDE_EFFECT_TOOLS` assignment (used at line 131) changes source.

## Compatibility considerations
- No import removal needed here (unlike `dispatch.py`/`http_transport.py`): the category constants stay used for tiers. Adding one import keeps `ruff` clean.
- Import direction unchanged (`agent/` importing from `shared/`).

## Security considerations
- Keeps approval/audit risk classification consistent with dedup and retry suppression: the same tools are side-effecting across all three consumers, so no tool is treated as safe by one layer and side-effecting by another.

## Rollback considerations
- Revert the commit: restore the `_STATIC_SIDE_EFFECT_TOOLS` composition expression and remove the added import.

## Validation plan
- `pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py` — `classify_operation_type` and `check_write_classification` still classify `index_paths`/`refresh_index` as side-effecting and all tier assignments are unchanged.
- `uv run ruff check scripts/agent/tool_policy.py`; `uv run mypy --no-namespace-packages scripts/`; `PYTHONPATH=scripts uv run lint-imports` clean.

## Completion criteria
- `scripts/agent/tool_policy.py`'s `_STATIC_SIDE_EFFECT_TOOLS` is assigned from `ALL_SIDE_EFFECTING_TOOLS`.
- Membership is unchanged (25 members), and the operation-type tier branches are untouched.

## Out of Scope
- Changing tier logic, `RiskLevel` mapping, shell shape rules, or approval tiers; editing `tool_constants.py` (seq 01), `dispatch.py` (seq 02), or `http_transport.py` (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import `ALL_SIDE_EFFECTING_TOOLS`; re-point `_STATIC_SIDE_EFFECT_TOOLS` to it | Completed | 20261115 | 20261115 | REQ-004; keep tier sets import added; _STATIC_SIDE_EFFECT_TOOLS = ALL_SIDE_EFFECTING_TOOLS; tier sets kept |
| 2 | Add/extend tool_policy test asserting classification membership unchanged | Completed | — | 20261115 | REQ-004, REQ-005 test_static_side_effect_membership_is_canonical added |
| 3 | Run validation sequence (`rules/toolchain.md`) | Completed | — | 20261115 | pytest + ruff + mypy + lint-imports 328 targeted pytest passed; ruff/lint-imports/mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261115 | N/A: no doc row in this Plan N/A: no doc row in this Plan |

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
- **Requirement ID**: `REQ-004` (tool_policy derives static side-effect classification from the canonical set)
- **Source issue**: `issues/20261111-163800_sideeffect001_side-effect-classification-central.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-052032_sideeffect001_side-effect-classification-central.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261115-192353
- **Related target files**: `scripts/agent/tool_policy.py`