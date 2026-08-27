## Goal

`REQ-003`: add `GitConfig.allow_detached_head: bool = False`, parsed the same way as
`protected_branches`, to let operators explicitly permit detached-HEAD checkouts per
ADR-012 Decision #5.

## Scope

- **In-Scope**: `GitConfig` dataclass (`scripts/mcp_servers/git/git_models.py:25-58`)
  — add the field and its `from_dict()` parsing.
- **Out-of-Scope**: consuming this field — see the companion `git_security.py`
  (REQ-001/REQ-002) and `git_service.py` (REQ-004) implementation procedure documents.

## Assumptions

- Confirmed via Read (`scripts/mcp_servers/git/git_models.py:25-58`) that
  `protected_branches` follows the pattern: dataclass field with `default_factory=
  list`, parsed in `from_dict()` via `get_typed(d, "protected_branches", list, "a
  list", default=[])`, and passed positionally to `cls(...)`. `allow_detached_head` is
  a plain `bool` (not a `list`), so it follows `read_only`'s parsing pattern instead:
  `get_typed(d, "read_only", bool, "a boolean", default=True)`.
- Confirmed via Read (`rules/coding.md` Type-coercion policy) that `get_typed` is the
  required helper for typed config fields — bare `bool()` coercion is prohibited.

## Design decisions

- Add `allow_detached_head: bool = False` as a new dataclass field, placed after
  `protected_branches` (matching the source Plan's own field-ordering intent).
- In `from_dict()`, add `allow_detached_head = get_typed(d, "allow_detached_head",
  bool, "a boolean", default=False)`, placed after the existing `protected_branches =
  get_typed(...)` line, and pass it to `cls(...)`.

## Alternatives considered

- N/A — this Requirement is a direct application of the existing `read_only`/
  `get_typed` pattern to a new boolean field; no alternative design was considered
  necessary.

## Implementation

### Target file
`scripts/mcp_servers/git/git_models.py`

### Procedure
1. Add `allow_detached_head: bool = False` to the `GitConfig` dataclass field list
   (after `protected_branches`, line ~32).
2. In `from_dict()` (lines 36-53), add `allow_detached_head = get_typed(d,
   "allow_detached_head", bool, "a boolean", default=False)` after the
   `protected_branches = get_typed(...)` line, and add
   `allow_detached_head=allow_detached_head` to the `cls(...)` call.

### Method
One dataclass field addition plus one `from_dict()` parsing line, following the
existing `read_only` field's exact pattern.

### Details
- Do not change `protected_branches`, `read_only`, or any other existing field.

## Compatibility considerations

- New field defaults to `False` — no existing `config/git_mcp_server.toml` needs to
  change; omitting the key preserves the current "detached HEAD always denied"
  behavior.

## Security considerations

- Provides the policy-controlled escape hatch ADR-012 Decision #5 requires
  ("Detached HEAD は、ポリシーで明示的に許可されない限り拒否しなければならない") —
  defaulting to `False` keeps the safe behavior as the default.

## Rollback considerations

- Remove the new field and its `from_dict()` parsing line.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/mcp_servers/git/git_models.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/mcp_servers/git/ -v` | `GitConfig.from_dict()` correctly parses `allow_detached_head`, defaulting to `False` when absent |

## Completion criteria

- `GitConfig` has `allow_detached_head: bool = False`.
- `GitConfig.from_dict({"allow_detached_head": True})` produces a `GitConfig` with
  `allow_detached_head=True`; omitting the key defaults to `False`.

## Out of scope

- Consuming this field in `GitSecurityGuards`/`GitService` — see the companion
  implementation procedure documents for REQ-001/REQ-002/REQ-004.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `allow_detached_head` field to `GitConfig` | Pending | — | — | |
| 2 | Add `from_dict()` parsing for the new field | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) scoped to this file and its tests | Pending | — | — | |
| 4 | Documentation update | N/A | — | — | Not in scope for this file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Assumption | `GitConfig.allow_detached_head` フィールドが未追加。手順書の前提と実際のコードに依存関係あり。 | No | 2026-08-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` — add `GitConfig.allow_detached_head`
- **Source issue**: `issues/20260823_git_dirty_worktree_detached_head_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-133945_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-181507
- **Related target files**: `scripts/mcp_servers/git/git_models.py`
