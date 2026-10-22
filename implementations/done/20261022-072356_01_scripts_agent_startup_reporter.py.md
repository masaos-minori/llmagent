## Goal

Add a `_status_word(counts)` helper to `scripts/agent/startup_reporter.py` that
derives the aggregated status word from the full `OK` / `FATAL` / `WARNING` /
`SKIPPED` count breakdown, and substitute it for the inline ternaries on the three
summary lines of `ReadinessReporter.report_readiness()` (lines 82, 85, 88). This
stops a warning-only source (any `WARNING`, no `FATAL`) from being mislabeled
`FAIL`, and unifies the status-word vocabulary across all three lines (`REQ-001`
through `REQ-006`).

## Scope

- **In-Scope**:
  - Add `_status_word(counts: OrderedDict[str, int]) -> str` next to
    `_count_by_status()` implementing `FATAL` > `WARNING` > `SKIPPED` > `OK`
    precedence (`REQ-001`..`REQ-004`).
  - Replace the ternary on line 82 with `_status_word(mcp_counts)`.
  - Replace the ternary on line 85 with `_status_word(tool_disc_counts)`.
  - Replace the ternary on line 88 with `_status_word(rag_counts)`; this also
    removes the legacy `WARN` token (`REQ-005`).
  - Leave the parenthetical counts (`fatal` / `warnings` / `skipped`) unchanged
    (`REQ-006`).
- **Out-of-Scope**:
  - Any change to `StartupValidationPipeline.check_services()` or how outcomes are
    produced.
  - Changing the counts shown in parentheses.
  - Renaming `report_readiness()` or changing its return type (still `None`).
  - Governance documentation updates.

## Assumptions

- **ASM-001**: The status word is purely display text; no caller parses it
  programmatically (verified by grep — no programmatic consumers found outside
  `startup_reporter.py`).
- **ASM-002**: `_count_by_status()` always returns all four keys (`OK`, `FATAL`,
  `WARNING`, `SKIPPED`), so `_status_word()` can index them safely.
- **ASM-003**: An empty pipeline (all counts zero) should report `OK` (nothing
  failed); this matches the existing
  `test_report_readiness_emits_readiness_summary` which uses an empty pipeline and
  does not assert the word.

## Design decisions

- Introduce a small module-level helper `_status_word(counts)` returning the
  highest-precedence present status. The `counts["OK"] == 0` guard in the
  `SKIPPED` branch ensures a source that mixes `SKIPPED` and `OK` outcomes reports
  `OK` (not `SKIPPED`), matching the plan's "else `SKIPPED` if all are `SKIPPED`,
  else `OK`" precedence.
- Substitute `_status_word(...)` for the inline ternaries on all three lines so the
  vocabulary is uniform (`REQ-005`). The parenthetical counts are left untouched
  (`REQ-006`).

## Alternatives considered

- Fixing only the `FAIL`→`WARNING` case and leaving the inline ternaries in place:
  rejected — the RAG line would still emit `WARN`, so the three lines would
  disagree on vocabulary (`REQ-005`). A single shared helper is required to make
  the three lines share one word set.

## Implementation

### Target file

`scripts/agent/startup_reporter.py`

### Procedure

1. Add `_status_word(counts)` (marked (new)) next to `_count_by_status()`
   implementing `FATAL` > `WARNING` > `SKIPPED` > `OK` precedence (`REQ-001`..`REQ-004`).
2. Replace the ternary on line 82 with `_status_word(mcp_counts)`.
3. Replace the ternary on line 85 with `_status_word(tool_disc_counts)`.
4. Replace the ternary on line 88 with `_status_word(rag_counts)`; this removes the
   legacy `WARN` token (`REQ-005`).

### Method

Add the helper immediately after `_count_by_status()` (which ends at line 47),
then edit the three `lines.append(f"...")` statements in `report_readiness()`
(lines 82, 85, 88), swapping each inline ternary for a `_status_word(...)` call.
No new import is needed: `OrderedDict` is already imported at module scope
(`startup_reporter.py:13`).

### Details

Current `_count_by_status()` ends at line 47. Append the helper right after it:

```python
def _status_word(counts: OrderedDict[str, int]) -> str:
    """Return the highest-precedence present status: FATAL > WARNING > SKIPPED > OK."""
    if counts["FATAL"] > 0:
        return "FATAL"
    if counts["WARNING"] > 0:
        return "WARNING"
    if counts["SKIPPED"] > 0 and counts["OK"] == 0:
        return "SKIPPED"
    return "OK"
```

Current lines 81-89 in `report_readiness()`:

```python
        lines.append(
            f"  Service readiness: {'OK' if mcp_counts['OK'] else 'FAIL'} ({mcp_counts['FATAL']} fatal, {mcp_counts['WARNING']} warnings, {mcp_counts['SKIPPED']} skipped)"
        )
        lines.append(
            f"  Tool discovery: {'OK' if tool_disc_counts['OK'] else 'FAIL'} ({tool_disc_counts['FATAL']} fatal, {tool_disc_counts['WARNING']} warnings, {tool_disc_counts['SKIPPED']} skipped)"
        )
        lines.append(
            f"  RAG consistency: {'OK' if rag_counts['OK'] else 'WARN'} ({rag_counts['FATAL']} fatal, {rag_counts['WARNING']} warnings, {rag_counts['SKIPPED']} skipped)"
        )
```

After substitution:

```python
        lines.append(
            f"  Service readiness: {_status_word(mcp_counts)} ({mcp_counts['FATAL']} fatal, {mcp_counts['WARNING']} warnings, {mcp_counts['SKIPPED']} skipped)"
        )
        lines.append(
            f"  Tool discovery: {_status_word(tool_disc_counts)} ({tool_disc_counts['FATAL']} fatal, {tool_disc_counts['WARNING']} warnings, {tool_disc_counts['SKIPPED']} skipped)"
        )
        lines.append(
            f"  RAG consistency: {_status_word(rag_counts)} ({rag_counts['FATAL']} fatal, {rag_counts['WARNING']} warnings, {rag_counts['SKIPPED']} skipped)"
        )
```

## Compatibility considerations

The status word is display-only operator-facing diagnostics; no caller parses it
programmatically (ASM-001). Existing tests do not assert the literal `FAIL` /
`WARN` words (adversarial grep of `tests/agent/test_startup_reporter.py` found
none), so the wording change is non-breaking. The empty-pipeline case still
reports `OK` (ASM-003), so `test_report_readiness_emits_readiness_summary` keeps
passing.

## Security considerations

N/A: display-only change; no auth, secret, or crypto impact.

## Rollback considerations

Revert the helper addition and the three line replacements — a single logical
commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/startup_reporter.py` | Static: `_status_word` (new) implements correct precedence; ternaries replaced; no `WARN` token | `pytest`, `mypy`, `ruff`, `bandit` | AC-001..AC-006 |
| `tests/agent/test_startup_reporter.py` | Behavior: warning-only source reports `WARNING` | `pytest` | AC-007 |
| `tests/agent/` (full) | Regression | `pytest` | All green (AC-006, AC-007) |

## Completion criteria

- `_status_word({"OK": 0, "FATAL": 0, "WARNING": 3, "SKIPPED": 0})` returns `"WARNING"` (AC-001).
- `_status_word` (new) returns `"FATAL"` when any `FATAL` is present (AC-002).
- `_status_word` (new) returns `"SKIPPED"` only when all outcomes are `SKIPPED` (AC-003).
- `_status_word` (new) returns `"OK"` when at least one `OK` is present (AC-004).
- No summary line contains the legacy `WARN` token; all three lines share one vocabulary (AC-005).
- The parenthetical `(N fatal, M warnings, K skipped)` counts are unchanged for every source (AC-006).

## Out of Scope

`StartupValidationPipeline.check_services()`, the parenthetical counts,
`report_readiness()`'s signature/return type, governance documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261022-101300 | Added _status_word(counts) helper; replaced ternaries on lines 82/85/88 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261022-101300 | N/A: warning-only regression tests added by companion procedure 20261022-072356_02 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261022-101300 | ruff/mypy(439 clean)/lint-imports(6 kept,0 broken)/bandit -ll(0 findings); tests/agent 3483 passed,7 skipped |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261022-101300 | N/A: no docs map to `startup_reporter.py` N/A: no docs/00_index.md task-scope mapping for startup_reporter.py |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006
- **Source issue**: `issues/done/20261021-220426_star003_fix-readiness-summary-mislabeling-warning-only-sources-as-fail.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261021-233223_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-100742
- **Related target files**: `scripts/agent/startup_reporter.py`