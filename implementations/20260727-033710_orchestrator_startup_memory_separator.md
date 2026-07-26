## Goal

Add clear separation between system prompt and injected memory content to prevent potential prompt injection through memory content.

## Scope

**In-Scope:**
- Replace `[Relevant memories]` with `--- USER MEMORY ---` separator in both locations
- Update all references to the old separator text

**Out-of-Scope:**
- Option B (injecting memory as separate user messages) — deferred due to scope constraints

## Assumptions

1. The separator approach (Option A) is sufficient for initial protection against prompt injection
2. The new separator must be distinguishable from legitimate memory content

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether any existing tests or configs reference the old `[Relevant memories]` separator | Search test files and configs | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/agent/orchestrator.py` — update separator on line 410
  - `scripts/agent/startup.py` — update separator on line 558

- **Blast Radius:**
  - Very low churn — two string constant changes
  - No behavioral change for normal operation

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the affected files:
```python
# Current (weak separator):
memory_block = "[Relevant memories]\n" + "\n".join(...)

# Proposed:
memory_block = "--- USER MEMORY ---\n" + "\n".join(...)
```

```python
# Current (weak separator):
memory_block = "\n\n[Relevant memories]\n" + "\n".join(...)

# Proposed:
memory_block = "\n\n--- USER MEMORY ---\n" + "\n".join(...)
```

## Implementation

### Target files
- `scripts/agent/orchestrator.py`
- `scripts/agent/startup.py`

### Procedure
1. Open `scripts/agent/orchestrator.py`
2. Locate line 410: `memory_block = "[Relevant memories]\n" + "\n".join(...)`
3. Replace with: `memory_block = "--- USER MEMORY ---\n" + "\n".join(...)`
4. Save the file
5. Open `scripts/agent/startup.py`
6. Locate line 558: `memory_block = "\n\n[Relevant memories]\n" + "\n".join(...)`
7. Replace with: `memory_block = "\n\n--- USER MEMORY ---\n" + "\n".join(...)`
8. Save the file

### Method
Direct string replacement of the separator text.

### Details
- `orchestrator.py:410`: `"[Relevant memories]\n"` → `"--- USER MEMORY ---\n"`
- `startup.py:558`: `"\n\n[Relevant memories]\n"` → `"\n\n--- USER MEMORY ---\n"`

## Compatibility considerations

N/A — separator change has no runtime effect unless memory content is present

## Security considerations

N/A — this change improves security posture

## Rollback considerations

- Simple revert: restore original separator text from git history

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/orchestrator.py` | Separator present in memory block | Manual verification | New separator used |
| `scripts/agent/startup.py` | Separator present in memory block | Manual verification | New separator used |
| Full test suite | No regressions | `uv run pytest -q` | Pass count unchanged |

## Out of scope

- Option B (injecting memory as separate user messages) — deferred due to scope constraints

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-170112_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-033710
- Related target files: scripts/agent/orchestrator.py, scripts/agent/startup.py
