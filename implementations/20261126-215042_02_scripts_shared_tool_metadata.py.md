## Goal

Add the `issue` and `pull_request` key kinds to the closed key-kind vocabulary so the GitHub
issue and pull-request scope declarations validate (REQ-001: the vocabulary the finer scopes
need).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `ResourceKeyKind` and `RESOURCE_KEY_KIND_VALUES` are at `scripts/shared/tool_metadata.py:61-64`
  and currently `{path, branch, repo, non_escalating}`; `branch` already exists, so only `issue`
  and `pull_request` are added.
- The Plan's original claim that no test pins this set was wrong: `tests/shared/test_tool_metadata.py:51-52`
  asserts exact equality, so that file was added as a target row (amendment 20261126, class
  `scope`, owner-approved) and is the companion of this document.
- No escalation rule reads the new kinds; the comment at `tool_metadata.py:59-60` describes only
  `non_escalating` and stays accurate, so it is not rewritten.

## Design decisions
- The Literal alias and the frozenset must stay in the same order and the same membership — the
  companion test asserts `value_set == frozenset(alias.__args__)` for every closed set
  (`tests/shared/test_tool_metadata.py:36-48`), so both are extended together in one change.

## Alternatives considered
- N/A: single-constant vocabulary change with no design choice; the only alternative is not to
  add the kinds, which contradicts REQ-001.

## Implementation
### Target file
`scripts/shared/tool_metadata.py`

### Procedure
1. Extend `ResourceKeyKind` (61) with `issue` and `pull_request`.
2. Extend `RESOURCE_KEY_KIND_VALUES` (62-64) with the same two values, in the same order as the
   Literal.

### Method
Add the two members to the `Literal[...]` alias and to the `frozenset({...})` literal; no other
code path changes. `validate_tool_schema_v2()` reads the set through
`scripts/shared/resource_scope.py:153`, so widening it is the whole behavioral change.

### Details
- The values are the key-kind labels used by `resource_scope_keys` declarations, not scope-kind
  names; the scope-kind vocabulary lives in procedure 01.

### Companion test files
- `tests/shared/test_tool_metadata.py`
  - Procedure: update `test_resource_key_kind_includes_non_escalating` (51-52) so the expected
    set includes `issue` and `pull_request`; keep the parametrized closed-set equality test
    unchanged — it follows the Literal automatically.
  - Validation: `uv run pytest tests/shared/test_tool_metadata.py -v` passes with the widened set.

## Compatibility considerations
- Widening a closed value set only accepts more declarations; no existing tool declaration becomes
  invalid. The exact-equality pin is the only test that must change, and it is this document's
  companion.

## Security considerations
- N/A: vocabulary widening only; validation still rejects any value outside the closed set.

## Rollback considerations
- N/A: revert the commit (single-commit change).

## Validation plan
| Check | Command | Expected |
|---|---|---|
| Unit | `uv run pytest tests/shared/test_tool_metadata.py tests/shared/test_resource_scope.py -v` | New key kinds accepted by `validate_tool_schema_v2()`; the exact-equality pin matches |
| Static | `uv run ruff format --check scripts/shared/tool_metadata.py`, `uv run ruff check scripts/shared/tool_metadata.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` | No new findings |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | `shared-is-leaf` kept |
| Security | `uv run bandit -r scripts/ -c pyproject.toml -ll` | No new findings |

## Completion criteria
- `RESOURCE_KEY_KIND_VALUES` contains `issue` and `pull_request` and matches its Literal alias.
- A declaration using the new kinds passes `validate_tool_schema_v2()` (AC-2).

## Out of Scope
- The scope-kind vocabulary and the conflict predicate — procedure 01.
- The tool declarations that use the new kinds — procedures 03, 04, 05.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion `tests/shared/test_tool_metadata.py`) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: documentation is covered by procedure 08 |

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
- **Requirement ID**: `REQ-001` (finer scopes for provably independent resources)
- **Source issue**: issues/20261119-140520_mcpai013_github-resource-scope-refine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-073010_mcpai013_github-resource-scope-refine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-215042
- **Related target files**: `scripts/shared/tool_metadata.py`, `tests/shared/test_tool_metadata.py`
