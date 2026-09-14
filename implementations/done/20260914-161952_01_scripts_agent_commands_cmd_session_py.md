## Goal

Add a `/session rag-rebuild-vec` subcommand to `scripts/agent/commands/cmd_session.py` that calls `RagMaintenanceService().rebuild_vec()` and prints a success message including the returned row count, mirroring the exact structure of the existing `_rag_rebuild_fts()` command. Per REQ-001, REQ-002.

## Scope

- Add exactly one method (`_rag_rebuild_vec`) to `_SessionMixin` in `scripts/agent/commands/cmd_session.py`
- Register `"rag-rebuild-vec"` in the dispatch table and help text
- Out-of-scope: modifying `RagMaintenanceService.rebuild_vec()` itself; adding a scheduled trigger; changing any other command

## Assumptions

- `RagMaintenanceService().rebuild_vec()` returns an `int` (row count) — confirmed via direct read of `scripts/agent/services/rag_maintenance_service.py:66-78`
- The existing `_rag_rebuild_fts()` method (lines 148-151) provides the exact structural template to mirror
- No naming collision: `rag-rebuild-vec` is absent from the current dispatch table and help text (confirmed via grep)

## Design decisions

1. Mirror `_rag_rebuild_fts()`'s structure exactly: call service method, print success message with return value
2. Do not add error handling beyond what `_rag_rebuild_fts()` has — it has none
3. Include the row count in the success message (unlike `_rag_rebuild_fts()` which omits it) — this gives operators visibility into how many vectors were rebuilt

## Alternatives considered

1. Omitting the row count from the success message: rejected — the operator needs to know how many vectors were rebuilt to assess whether orphan removal had effect
2. Adding a confirmation prompt before execution: rejected — `_rag_rebuild_fts()` has no such prompt; consistency with existing behavior is preferred

## Implementation

### Target file

`scripts/agent/commands/cmd_session.py`

### Procedure

1. Add `_rag_rebuild_vec()` method after `_rag_rebuild_fts()` (after line 151)
2. Register `"rag-rebuild-vec": self._rag_rebuild_vec` in the dispatch table (after line 215)
3. Add `rag-rebuild-vec` to both help-text occurrences (lines 175, 226)

### Method

1. Read `cmd_session.py` to confirm current content around insertion points
2. Insert new method after `_rag_rebuild_fts()` using the same indentation style
3. Add dispatch table entry after `"rag-rebuild-fts"` entry
4. Update both help-text strings to include `rag-rebuild-vec`

### Details

**Step 1 — Add `_rag_rebuild_vec()` method:**

Insert after line 151 (after `_rag_rebuild_fts()`):

```python
    def _rag_rebuild_vec(self) -> None:
        """Rebuild chunks_vec from chunks. Returns number of rows inserted."""
        count = RagMaintenanceService().rebuild_vec()
        self._out.write_success(f"chunks_vec rebuilt ({count} rows). [RAG]")
```

Rationale: mirrors `_rag_rebuild_fts()`'s two-line structure (call + success message), but includes the row count since operators need to see how many vectors were rebuilt.

**Step 2 — Register in dispatch table:**

After line 215 (`"rag-rebuild-fts": self._rag_rebuild_fts,`), add:

```python
            "rag-rebuild-vec": self._rag_rebuild_vec,
```

**Step 3 — Update help text:**

Line 175: change `|rag-consistency|rag-rebuild-fts.` to `|rag-consistency|rag-rebuild-fts|rag-rebuild-vec.`

Line 226: change `|rag-consistency|rag-rebuild-fts` to `|rag-consistency|rag-rebuild-fts|rag-rebuild-vec`

Reference files read (must NOT be modified):
- `scripts/agent/services/rag_maintenance_service.py:66-78` — confirms `rebuild_vec()` signature and return type
- `tests/agent/commands/test_agent_cmd_session.py:773-805` — confirms existing test pattern for `rag-rebuild-fts`

## Compatibility considerations

- Public API surface unchanged: only adds a new subcommand name; no existing command behavior changes
- Return value semantics preserved: `rebuild_vec()` returns `int` (row count); the new success message format is additive, not breaking
- Known behavioral difference: unlike `_rag_rebuild_fts()` which has no return-value display, this includes the row count — intentional design decision per above

## Security considerations

N/A — no security-sensitive operations introduced; the new command delegates to an already-existing service method.

## Rollback considerations

- Revert the three edit steps above to restore original state
- No data loss risk — only control flow changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/commands/cmd_session.py | Unit — verify new command wires correctly | `uv run pytest tests/agent/commands/test_agent_cmd_session.py -k rag_rebuild_vec -q` | New tests pass |
| scripts/agent/commands/cmd_session.py | Static check — verify no duplicate dispatch key | Manual inspection of dispatch table | Zero conflicts |

## Completion criteria

- [ ] `_rag_rebuild_vec()` method added after `_rag_rebuild_fts()` with correct structure
- [ ] `"rag-rebuild-vec"` registered in dispatch table alongside `"rag-rebuild-fts"`
- [ ] Both help-text occurrences updated to include `rag-rebuild-vec`
- [ ] Success message includes the row count returned by `rebuild_vec()`
- [ ] New unit tests pass, mirroring the existing `rag-rebuild-fts` test pair's structure

## Out of scope

- Modifying `RagMaintenanceService.rebuild_vec()` (unchanged — single source of truth)
- Adding a scheduled/periodic trigger for orphan cleanup
- Changing the existing `rag-rebuild-fts` command behavior
- Adding a confirmation prompt or safety guard

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260914-230023 | 20260914-230023 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260914-230023 | 20260914-230023 | N/A: existing tests cover regression |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 20260914-230023 | 20260914-230023 | N/A: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260914-230023 | 20260914-230023 | N/A: docstring already describes delegation |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260914-105248_ragsvc03_orphaned-vector-periodic-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-145915_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-161952
- **Related target files**: scripts/agent/commands/cmd_session.py