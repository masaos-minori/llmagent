# Issue: Validate and fix inconsistencies in refactor_001_refactor-mcp-tool-discovery-service.md

## Priority
High

## Summary

Adversarial validation of `issues/20260924-105819_refactor_001_refactor-mcp-tool-discovery-service.md` revealed multiple contradictions between its claims and actual source code, unrealistic acceptance criteria, and unresolved design decisions. This issue tracks the fixes needed before the original issue can be safely implemented.

## Background

The original issue proposes refactoring `scripts/agent/services/mcp_tool_discovery.py` by extracting bounded contexts into separate classes. The validation examined both the source files (`mcp_tool_discovery.py`, `runtime_tool_registry.py`) and the test suite (`test_mcp_tool_discovery.py`).

## Findings

### F1: Contradiction — Severity escalation for duplicates

**Severity**: High

**Description**: The issue contains two contradictory statements about how duplicate tool findings should be handled after refactoring:

- Section 4 (Implementation Intent): "Duplicate findings should follow the same scheme unless explicitly documented as an exception."
- Constraint 69: "Must not change the external behavior of any finding (same messages, same status values)"

If severity classification is consolidated per Section 4's proposal, the duplicate-FATAL exception would either need to be removed (violating Constraint 69) or kept as a documented exception (contradicting Section 4's direction).

**Current state verification**: The duplicate-FATAL exception exists in `_dedupe_and_build()` line 377 and is documented in the module docstring (lines 32-34). Both `_is_strict()` and `_is_fatal_severity()` are currently identical methods (lines 404-414), so consolidation alone does not change behavior — but the issue text suggests alignment with the `is_fatal = strict` scheme, which would eliminate the exception.

**Required action**: Explicitly decide whether the duplicate-FATAL exception is retained or removed, and update all affected sections consistently.

---

### F2: Unrealistic acceptance criterion — `discover_all()` under 30 lines

**Severity**: Medium

**Description**: Acceptance criterion states "`discover_all()` method reduced to under 30 lines". Current `discover_all()` is 65 lines (line 121-185). Even after extracting helper methods, the following logic must remain inline:

- Per-server fetch loop (~30 lines including unreachable handling)
- Required tools check (~18 lines)
- Drift findings call (~2 lines)
- Registry creation (~4 lines)

Even if every block were extracted to a single-line call, the minimum achievable line count is approximately 35-40 lines, not under 30.

**Current state verification**: Verified against `mcp_tool_discovery.py` lines 121-185.

**Required action**: Change acceptance criterion from "under 30 lines" to "under 40 lines" or remove the specific line-count target entirely.

---

### F3: Incomplete resolution path — redundant registry creation

**Severity**: Medium

**Description**: The issue correctly identifies that `discover_all()` creates a second filtered registry (lines 176-180) when `RuntimeToolRegistry.__init__()` already filters unavailable servers via `_is_excluded_server()`. However, the proposed solution requires changing `_dedupe_and_build()`'s return signature to accept `unavailable_servers`, which will affect the test suite.

**Current state verification**: `RuntimeToolRegistry.__init__()` (line 40-53 in `runtime_tool_registry.py`) accepts `unavailable_servers` and excludes tools via `_is_excluded_server()`. The current code still creates a second registry because `_dedupe_and_build()` returns a plain registry without server exclusion info.

**Required action**: Document the expected test changes and ensure tests are updated accordingly.

---

### F4: Low-value change — `/v1/tools` constant extraction

**Severity**: Low

**Description**: The issue proposes moving `/v1/tools` to a module-level constant. This path appears only twice in the codebase (both within `_fetch_server_tools()` at lines 202 and 212). The value is low since there are no other references to this path elsewhere.

**Current state verification**: Confirmed — only two occurrences in `_fetch_server_tools()`.

**Required action**: Deprioritize or remove from acceptance criteria. Not harmful but adds little value.

---

### F5: Unresolved design decisions not answered

**Severity**: Medium

**Description**: Three questions in the "Unresolved Questions" section have no answers:

1. Should `ToolEntryValidator` be standalone or nested? No recommendation provided.
2. Should `McpToolsHttpClient` accept `httpx.AsyncClient` as a parameter or create internally? No recommendation provided.
3. Is the "always FATAL for duplicates" exception intentional? No decision recorded.

**Current state verification**: These questions appear verbatim in the issue's "Unresolved Questions" section (lines 115-117).

**Required action**: Record design decisions before implementation begins. These choices affect the extracted class boundaries and constructor signatures.

---

### F6: Test coverage gap — message string comparison

**Severity**: Medium

**Description**: The acceptance criterion "Verify no behavioral regression: compare StartupCheckOutcome messages before/after refactoring for identical outputs" cannot be reliably executed because existing tests do not perform strict message-string comparisons. Tests use assertions like `assert any(f.status == StartupCheckStatus.FATAL for f in mcp_findings)` rather than checking exact message content.

**Current state verification**: Examined `test_mcp_tool_discovery.py`. Multiple test methods assert on status codes and presence of keywords in messages, but none assert exact message strings. For example, `test_duplicate_name_production_is_fatal_and_excluded` asserts `dup_findings[0].status == StartupCheckStatus.FATAL` but does not verify the message text.

**Required action**: Either add strict message comparison assertions to relevant tests, or modify the acceptance criterion to rely on status-code and structural assertions instead.

---

### F7: Minor — severity classification claim overstated

**Severity**: Low

**Description**: The issue claims "severity classification logic is scattered across 4+ methods". Actual analysis shows the `is_fatal = strict` pattern appears in exactly 3 locations:

1. `_fetch_server_tools()` line 265-271 (required server escalation)
2. `discover_all()` line 132-149 (unreachable server escalation)
3. `_build_drift_findings()` line 430-434 (drift findings)

Additionally, `_check_tool_definitions_finding()` line 456-458 and line 468-472 contain similar patterns. So the actual count is 5, not 4+, making the claim technically correct but imprecise.

**Current state verification**: Verified against `mcp_tool_discovery.py` lines 265, 132, 430, 456, 468.

**Required action**: Update the claim to "scattered across 5 methods" for precision.

---

## Risk Assessment

| Finding | Severity | Probability |
|---|---|---|
| F1: Severity escalation contradiction | High | Medium |
| F2: Line-count target unachievable | Low | High |
| F3: Redundant registry change affects tests | Medium | Low |
| F4: Low-value constant extraction | Low | N/A |
| F5: Unresolved design decisions | Medium | Medium |
| F6: Message comparison gap | Medium | Medium |
| F7: Imprecise severity claim | Low | N/A |

## Required Changes to Original Issue

Before implementing the original refactor, the following updates must be made to `issues/20260924-105819_refactor_001_refactor-mcp-tool-discovery-service.md`:

1. **F1**: Add explicit decision on duplicate-FATAL exception retention/removal; update Section 4, Constraint 69, and Acceptance Criteria consistently.
2. **F2**: Change acceptance criterion from "under 30 lines" to "under 40 lines" or remove the specific target.
3. **F3**: Document expected test changes for `_dedupe_and_build()` return signature modification.
4. **F4**: Remove or deprioritize `/v1/tools` constant extraction from acceptance criteria.
5. **F5**: Record answers to all three unresolved questions.
6. **F6**: Add strict message comparison assertions to tests, or revise acceptance criterion.
7. **F7**: Update "4+ methods" to "5 methods" in Problem section.

## Dependencies

- None blocking this validation work.

## Unresolved Questions

- After fixing the above issues, should the original issue be re-filed as a new document, or amended in place?
- Should the duplicate-FATAL exception be aligned with the `is_fatal = strict` scheme (removing it), or preserved as a documented exception?
