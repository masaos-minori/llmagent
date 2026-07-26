## Goal

Fix RuntimeToolRegistry API mismatch in test_rag_tools_consistency.py to restore RAG tool registration verification.

## Scope

**In-Scope:**
- Identify correct method on RuntimeToolRegistry for enumerating tool names
- Update test_rag_tools_consistency.py to use correct API
- Verify all 5 tests pass

**Out-of-Scope:**
- Any changes beyond the test file itself
- Changes to RuntimeToolRegistry class

## Assumptions

1. RuntimeToolRegistry has a method to enumerate registered tool names
2. The method name differs from the expected `get_all_tool_names()`
3. No behavioral change needed — just API correction

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | What is the correct method name on RuntimeToolRegistry for enumerating tool names | Inspect route_resolver.py | True |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `tests/test_rag_tools_consistency.py:22` — incorrect method call

- **Blast Radius:**
  - Low churn — single line change in one test file
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the RuntimeToolRegistry class:
```python
# Key behaviors:
# - RuntimeToolRegistry needs a method to enumerate tool names
# - Current test uses get_all_tool_names() which doesn't exist
# - Need to find the correct method name
```

The fix will update the test to use the correct method name.

## Implementation

### Target files
- `tests/test_rag_tools_consistency.py`

### Procedure
1. Phase 1: Inspect RuntimeToolRegistry class for correct method name
2. Phase 2: Update test_rag_tools_consistency.py with correct method call
3. Phase 3: Verify with lint and tests

### Method
Find the correct method name by inspecting the RuntimeToolRegistry class definition.

### Details
1. Inspect `scripts/shared/route_resolver.py` to find the correct method name:
   ```bash
   grep -n "def.*tool" scripts/shared/route_resolver.py
   ```

2. Update `tests/test_rag_tools_consistency.py:22`:
   ```python
   # Before:
   registry.get_all_tool_names()
   
   # After (example):
   registry.list_tool_names()  # Use actual method name found
   ```

## Compatibility considerations

N/A — this is an API correction only

## Security considerations

N/A — this is a test fix only

## Rollback considerations

- Simple revert: restore original test file from git history

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_rag_tools_consistency.py` | Run all 5 tests | `uv run pytest tests/test_rag_tools_consistency.py -v` | All 5 tests pass |

## Out of scope

- Any changes beyond the test file itself
- Changes to RuntimeToolRegistry class

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260726_30_issue.md
- Source requirement: requires/20260726-122409_require.md
- Source plan: plans/20260726-180647_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: tests/test_rag_tools_consistency.py, scripts/shared/route_resolver.py
