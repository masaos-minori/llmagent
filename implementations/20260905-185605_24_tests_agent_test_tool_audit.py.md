## Goal
Remove `use_semantic_cache`/`semantic_cache_threshold`/`semantic_cache_max_size`
fixture-dict keys from `tests/agent/test_tool_audit.py`, made obsolete by procedure
documents `01`/`04` (`REQ-009`).

## Scope
- **In-Scope**: remove `"use_semantic_cache": False,` (line 39),
  `"semantic_cache_threshold": 0.92,` (line 40), and `"semantic_cache_max_size": 100,`
  (line 41).
- **Out-of-Scope**: every other key in the same dict and every tool-audit-specific
  test in this file — confirmed unrelated by reading the surrounding lines.

## Assumptions
- This dict is a raw-config-dict fixture analogous to procedure documents `20`-`23`'s.

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §7, narrow bullet only)
- Remove all three keys together — discovered as one fixture-dict block by this
  Plan's repository-wide search.

## Alternatives considered
N/A: straightforward removal of three now-rejected fixture keys.

## Implementation
### Target file
`tests/agent/test_tool_audit.py`

### Procedure
1. Remove `"use_semantic_cache": False,` (line 39).
2. Remove `"semantic_cache_threshold": 0.92,` (line 40).
3. Remove `"semantic_cache_max_size": 100,` (line 41).

### Method
Direct removal via `Edit`.

### Details
- Confirm after editing: `rg -n "semantic_cache" tests/agent/test_tool_audit.py`
  returns zero matches.

## Compatibility considerations
N/A: test-only file.

## Security considerations
N/A.

## Rollback considerations
- Revert via `git checkout` on this single file; must be reverted together with
  procedure document `04`.

## Validation plan
- `uv run pytest tests/agent/test_tool_audit.py -v` — all tests pass.
- `rg -n "semantic_cache" tests/agent/test_tool_audit.py` — zero matches.

## Completion criteria
- No reference to any of the three removed keys remains in this file (Plan `AC-8`).

## Out of scope
- `scripts/agent/config_builders.py`'s `_build_rag_config()` (procedure document `04`).
- Every tool-audit-specific test in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixture cleanup only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-009` (remove cache references from mocks and fixtures)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: tests/agent/test_tool_audit.py
