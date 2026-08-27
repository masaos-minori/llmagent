## Goal

Remove the dead `RETENTION_DAYS` dict (REQ-002) from `scripts/agent/memory/enums.py`,
per `plans/20260826-121839_plan.md`.

## Scope

- In scope: the `RETENTION_DAYS` dict literal (verified at lines 57-62 as of
  2026-08-27) only.
- Out of scope: `DEDUP_THRESHOLDS` (adjacent, unrelated dict — verified 2026-08-27
  immediately preceding `RETENTION_DAYS` in this file, not part of this removal);
  `MemoryType` or any other symbol in this file.

## Assumptions

- `RETENTION_DAYS` has exactly one consumer, `JsonlMemoryStore.read_active()`
  (`jsonl_store.py:98`) — re-verified 2026-08-27 via `rg -n "RETENTION_DAYS"
  scripts/ tests/`, finding only its own definition (`enums.py:57`), its import
  (`jsonl_store.py:26`), and its one usage (`jsonl_store.py:98`).
- Both symbols must be removed together (this item and seq 05, `jsonl_store.py`) in
  the same change — removing `RETENTION_DAYS` alone would break `jsonl_store.py`'s
  import.

## Design decisions

- Remove the dict outright — no deprecation shim, no `# deprecated` comment
  retention — per `rules/coding.md`'s Deprecation policy ("removed the next time
  `plans/` touches the corresponding file for an unrelated reason, provided a
  zero-caller `rg` re-check still holds") and this Plan's own Design section
  reasoning (mirrors `plans/done/20260819-163404_plan.md`'s analogous
  `mcp_health.py` dead-code removal).

## Alternatives considered

- Wiring in a caller for the retention-filter logic instead of removing it was
  considered and rejected by this Plan's own Design section — no concrete,
  already-planned caller exists anywhere in the repository, and inventing one
  would be speculative (see this Plan's Assumptions and three independent prior
  verification cycles cited in Background).

## Implementation
### Target file
`scripts/agent/memory/enums.py`

### Procedure
1. Re-run `rg -n "RETENTION_DAYS" scripts/ tests/` immediately before editing, to
   confirm no new caller landed since this Plan was written.
2. Remove the `RETENTION_DAYS` dict literal (lines 57-62).
3. Run `uv run pytest tests/agent/memory/test_jsonl_store.py -v` (will fail with an
   `ImportError` until seq 05, `jsonl_store.py`, is also applied — these two items
   must land together).

### Method
Direct code deletion (Edit tool) — remove one dict literal block.

### Details
Current code (verified 2026-08-27, lines 57-62):
```python
RETENTION_DAYS: dict[str, int | None] = {
    "RULE": None,
    "DECISION": None,
    "FAILURE": 180,
    "CONVERSATION": 90,
}
```
Delete this block entirely. Leave `DEDUP_THRESHOLDS` (the immediately preceding
dict) and any other symbol in this file unchanged.

## Compatibility considerations

- Must land in the same change as seq 05 (`jsonl_store.py`'s `read_active()` and
  import removal) — this file alone, without that removal, breaks
  `jsonl_store.py:26`'s `from agent.memory.enums import RETENTION_DAYS,
  MemoryType`.

## Security considerations

- N/A: no security-relevant behavior; removes an unreachable configuration dict.

## Rollback considerations

- Single-block revert via `git diff`/`git checkout -- scripts/agent/memory/enums.py`;
  must be reverted together with seq 05 (`jsonl_store.py`) in this same pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/enums.py` | Static | `rg -n "RETENTION_DAYS" scripts/ tests/` | No matches after this item and seq 05 both land |
| `scripts/agent/memory/enums.py` | Regression | `uv run pytest tests/agent/memory/test_jsonl_store.py -v` | Passes once seq 05 has also landed |

## Completion criteria

- `RETENTION_DAYS` no longer exists in this file.
- `rg -n "RETENTION_DAYS" scripts/ tests/` returns no matches once seq 05 has also
  landed.

## Out of scope

- `DEDUP_THRESHOLDS` and any other symbol in this file.
- `jsonl_store.py`'s `read_active()` (separate target file, seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-run `rg` re-verification before editing | Pending | — | — | |
| 2 | Remove `RETENTION_DAYS` dict | Pending | — | — | Must land together with seq 05 |
| 3 | Run `uv run pytest tests/agent/memory/test_jsonl_store.py -v` | Pending | — | — | Requires seq 05 applied |

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
- **Source plan**: `plans/20260826-121839_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-112248
- **Related target files**: `scripts/agent/memory/enums.py`
