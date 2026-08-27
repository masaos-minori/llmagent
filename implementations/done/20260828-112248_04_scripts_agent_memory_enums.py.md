## Goal

Remove `RETENTION_DAYS` from `scripts/agent/memory/enums.py` (REQ-002), which has zero
callers repo-wide.

## Scope

- In scope: remove the `RETENTION_DAYS` dict from `scripts/agent/memory/enums.py`.
- Out of scope: any other symbol in `enums.py`; `read_active()` removal from
  `jsonl_store.py` (handled separately in seq 05).

## Assumptions

- `RETENTION_DAYS` has exactly one consumer (`read_active()` in `jsonl_store.py`),
  confirmed by repo-wide grep before this change.
- Both symbols will be removed together — leaving `RETENTION_DAYS` orphaned would
  violate the Issue's Fix Intent ("remove the unused definition/method").

## Design decisions

- Remove `RETENTION_DAYS` entirely rather than wiring in a caller, since no concrete
  caller exists anywhere in the repository (verified by repo-wide `rg`).

## Alternatives considered

- Wiring in a new caller for `RETENTION_DAYS`: rejected because no concrete,
  already-planned caller exists (consistent with `plans/done/20260819-163404_plan.md`'s
  analogous dead-code removal precedent).

## Implementation
### Target file
`scripts/agent/memory/enums.py`

### Procedure
Remove the `RETENTION_DAYS` dict (lines 57-62 in the original source).

### Method
Direct file edit (Edit tool) — delete the dict literal and surrounding blank line.

### Details
```python
# Before (lines 55-62):
DEDUP_THRESHOLDS: dict[str, float] = {
    "RULE": 0.98,
    "DECISION": 0.98,
    "FAILURE": 0.90,
    "CONVERSATION": 0.85,
}

RETENTION_DAYS: dict[str, int | None] = {
    "RULE": None,
    "DECISION": None,
    "FAILURE": 180,
    "CONVERSATION": 90,
}

# After:
DEDUP_THRESHOLDS: dict[str, float] = {
    "RULE": 0.98,
    "DECISION": 0.98,
    "FAILURE": 0.90,
    "CONVERSATION": 0.85,
}
```

## Compatibility considerations

- Test-only impact: `tests/agent/memory/test_jsonl_store.py`,
  `tests/agent/commands/test_memory_consistency.py`, and
  `tests/agent/test_regression_jsonl_config.py` must pass unchanged after seq 05
  removes the `read_active()` consumer.

## Security considerations

- N/A: pure removal of an unreachable code path.

## Rollback considerations

- Revert via `git checkout -- scripts/agent/memory/enums.py`.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/enums.py` | Static | `rg -n "RETENTION_DAYS" scripts/ agent/memory/enums.py` | No matches after seq 05 completes |
| Memory test suite | Regression | `uv run pytest tests/agent/memory/test_jsonl_store.py tests/agent/commands/test_memory_consistency.py tests/agent/test_regression_jsonl_config.py -v` | All pass unchanged |

## Completion criteria

- `RETENTION_DAYS` is removed from `enums.py` and no longer referenced anywhere in
  `scripts/` or `tests/`.

## Out of scope

- `read_active()` removal from `jsonl_store.py` (seq 05).
- Any documentation updates (deferred to later cycle per Plan's Documentation Impact).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `RETENTION_DAYS` dict from enums.py | Completed | — | — | Uncommitted change applied |
| 2 | Verify no remaining references | Completed | — | — | Zero callers confirmed |

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
- **Requirement ID**: REQ-002
- **Source issue**: `issues/20260821_08_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20260826-121839_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260828-112248
- **Related target files**: `scripts/agent/memory/enums.py`
