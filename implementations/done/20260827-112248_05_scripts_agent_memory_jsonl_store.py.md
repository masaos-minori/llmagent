## Goal

Remove `JsonlMemoryStore.read_active()`, its `RETENTION_DAYS` import, and the
now-unused `import datetime` (REQ-002), per `plans/20260826-121839_plan.md`.

## Scope

- In scope: `read_active()` method body (verified at lines 91-111 as of
  2026-08-27), the `RETENTION_DAYS` import (line 26), and `import datetime` (line
  17) in this one file.
- Out of scope: `MemoryType` (the other symbol imported on the same line 26 as
  `RETENTION_DAYS` — must be kept); `read_all()`, `count_all()`, or any other
  method in this file.

## Assumptions

- `read_active()` has zero callers anywhere in the repository, including
  `tests/` — re-verified 2026-08-27 via `rg -n "read_active" scripts/ tests/`,
  finding only the method's own definition.
- `import datetime` (line 17) is used ONLY inside `read_active()` — re-verified
  2026-08-27 via `grep -n "datetime\." scripts/agent/memory/jsonl_store.py`,
  finding exactly two usages (`datetime.datetime.now(datetime.UTC)` at line 94,
  `datetime.datetime.fromisoformat(...)` at line 103), both inside `read_active()`
  — safe to remove once that method is deleted.
- Must land in the same change as seq 04 (`enums.py`'s `RETENTION_DAYS` removal) —
  this file's import at line 26 would otherwise raise `ImportError`.

## Design decisions

- Remove `read_active()` entirely (not deprecate/comment out) — per this Plan's
  Design section reasoning (Deprecation policy, zero-caller re-check holds).
- Change the import line from `from agent.memory.enums import RETENTION_DAYS,
  MemoryType` to `from agent.memory.enums import MemoryType` — keep `MemoryType`,
  drop only `RETENTION_DAYS`.
- Remove `import datetime` entirely (not narrow it to a submodule import) since no
  other use remains in this file.

## Alternatives considered

- Keeping `import datetime` in case a future method needs it was considered and
  rejected — `rules/coding.md`'s conventions favor removing genuinely unused
  imports (this is not the `logger = logging.getLogger(__name__)` exemption
  pattern, which applies narrowly to that one specific declaration); re-add it if
  and when a future change actually needs it.

## Implementation
### Target file
`scripts/agent/memory/jsonl_store.py`

### Procedure
1. Re-run `rg -n "read_active" .` immediately before editing, to confirm no new
   caller landed since this Plan was written.
2. Remove `read_active()` (lines 91-111).
3. Change the import at line 26 to drop `RETENTION_DAYS`, keeping `MemoryType`.
4. Remove `import datetime` (line 17).
5. Run `uv run pytest tests/agent/memory/test_jsonl_store.py
   tests/agent/commands/test_memory_consistency.py
   tests/agent/test_regression_jsonl_config.py -v` — confirm all pass unchanged
   (none reference `read_active`/`RETENTION_DAYS` today, per this Plan's Tests
   section).
6. Run `uv run mypy scripts/agent/memory/jsonl_store.py` — confirm no new errors.

### Method
Direct code deletions (Edit tool) — one method removal, one import-line edit, one
import-line removal.

### Details
Current code (verified 2026-08-27):
- Line 17: `import datetime`
- Line 26: `from agent.memory.enums import RETENTION_DAYS, MemoryType`
- Lines 91-111:
```python
    def read_active(self) -> list[MemoryEntry]:
        """Return entries that have not expired based on per-source-type retention policy."""
        entries = self.read_all()
        now = datetime.datetime.now(datetime.UTC)
        active: list[MemoryEntry] = []
        for entry in entries:
            source_key = str(entry.source_type).upper()
            max_days = RETENTION_DAYS.get(source_key)
            if max_days is None:
                active.append(entry)
                continue
            try:
                created = datetime.datetime.fromisoformat(
                    entry.created_at.replace("Z", "+00:00")
                )
                age_days = (now - created).total_seconds() / 86_400.0
                if age_days <= max_days:
                    active.append(entry)
            except (ValueError, OverflowError):
                active.append(entry)
        return active
```
Delete lines 91-111 entirely. Change line 26 to:
```python
from agent.memory.enums import MemoryType
```
Delete line 17 (`import datetime`) entirely.

## Compatibility considerations

- Must land in the same change as seq 04 (`enums.py`) — this file's import would
  otherwise reference a removed symbol.
- `read_all()`, `count_all()`, and every other method in this file are unaffected.

## Security considerations

- N/A: no security-relevant behavior; removes an unreachable, unused code path.

## Rollback considerations

- Revert via `git diff`/`git checkout -- scripts/agent/memory/jsonl_store.py`;
  must be reverted together with seq 04 (`enums.py`) in this same pass.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/memory/jsonl_store.py` | Static | `rg -n "RETENTION_DAYS\|read_active" scripts/ tests/` | No matches |
| `scripts/agent/memory/jsonl_store.py` | Regression | `uv run pytest tests/agent/memory/test_jsonl_store.py tests/agent/commands/test_memory_consistency.py tests/agent/test_regression_jsonl_config.py -v` | All pass, unchanged |
| `scripts/agent/memory/jsonl_store.py` | Type check | `uv run mypy scripts/agent/memory/jsonl_store.py` | No new errors |

## Completion criteria

- `read_active()`, the `RETENTION_DAYS` import, and `import datetime` are all
  removed.
- `rg -n "RETENTION_DAYS|read_active" scripts/ tests/` returns no matches.
- The existing memory test suite passes unchanged.

## Out of scope

- `MemoryType` and any other symbol in this file.
- `read_all()`, `count_all()`, or any other method.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-run `rg` re-verification before editing | Pending | — | — | |
| 2 | Remove `read_active()` | Pending | — | — | Must land together with seq 04 |
| 3 | Update import to drop `RETENTION_DAYS`, keep `MemoryType` | Pending | — | — | |
| 4 | Remove `import datetime` | Pending | — | — | |
| 5 | Run regression test suite | Pending | — | — | |
| 6 | Run `uv run mypy scripts/agent/memory/jsonl_store.py` | Pending | — | — | |

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
- **Related target files**: `scripts/agent/memory/jsonl_store.py`
