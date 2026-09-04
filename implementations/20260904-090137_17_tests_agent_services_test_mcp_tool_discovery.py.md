## Goal
Update `test_mcp_tool_discovery.py`'s Local/Production-parametrized tests to
match row 9's `_is_fatal_severity()` simplification (`self._is_strict()`
only) and remove the file's dependency on constructing
`SecurityProfile.LOCAL`.

## Scope
- **In-Scope**: `_make_ctx()`'s `security_profile` default parameter (line
  73), every test parametrized over
  `[SecurityProfile.LOCAL, SecurityProfile.PRODUCTION]` whose expected
  outcome differs by profile (lines 795-882, 1610-1770 — the
  `_is_fatal_severity()`-equivalent behavior tests), and every standalone
  `security_profile=SecurityProfile.LOCAL` construction (lines 1368, 1453,
  1525, 1594).
- **Out-of-Scope**: `test_classification_equivalent_across_security_profiles()`
  (~line 805) and its `_dup_ctx()` helper (~line 829) if their assertion is
  that behavior is *equivalent* across profiles (not `_is_fatal_severity()`-
  dependent) — confirm at execution time by reading the full test body; if
  equivalence holds independent of `_is_fatal_severity()`, this test needs
  only its parametrize list narrowed (see Procedure step 3), not a logic
  change.

## Assumptions
- Must execute after row 9's `_is_fatal_severity()` edit lands — the tests at
  lines 1610-1690 and 1730-1763 directly assert the FATAL/WARNING matrix
  that method produces; once row 9 makes it `self._is_strict()`-only, the
  `security_profile=PRODUCTION, strict=False` combination (currently
  expected FATAL per lines 1621/1677 in the strict-varying table, WARNING per
  line 1675 in the other) collapses to always-WARNING-unless-strict,
  eliminating the profile axis entirely from these two parametrized tables.

## Design decisions
- Rather than deleting the `security_profile` parametrize axis from these
  tables outright, collapse each table to a single-axis parametrize over
  `strict` only, since `security_profile` no longer affects
  `_is_fatal_severity()`'s outcome (verified against row 9's corrected
  method body: `return self._is_strict()`).
- Keep `_make_ctx()`'s `security_profile: SecurityProfile = SecurityProfile.LOCAL`
  default parameter's *type* (`SecurityProfile`) but change its default value
  to `SecurityProfile.PRODUCTION`, matching row 2's dataclass-default change,
  so callers that don't pass this parameter still construct a valid context
  post-row-1.

## Alternatives considered
- Leaving `security_profile` in the parametrize lists but always expecting
  the same outcome for both values: rejected — once `SecurityProfile.LOCAL`
  is removed (row 1), the list `[SecurityProfile.LOCAL, SecurityProfile.PRODUCTION]`
  fails at collection time with an `AttributeError`, not merely produces a
  redundant assertion; the axis must be removed, not just its differing
  expectations.

## Implementation
### Target file
`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure
1. Change `_make_ctx()`'s `security_profile` default (verified 2026-09-04,
   line 73) from `SecurityProfile.LOCAL` to `SecurityProfile.PRODUCTION`.
2. Replace every standalone `security_profile=SecurityProfile.LOCAL`
   construction (lines 1368, 1453, 1525, 1594) with
   `security_profile=SecurityProfile.PRODUCTION`, unless the surrounding test
   specifically asserts pre-row-9 Local-vs-Production divergence (re-read
   each call site's assertions at execution time to confirm no such test
   remains after step 3/4).
3. Collapse the FATAL/WARNING matrix table at lines 1610-1623 (parametrized
   over `(strict_flag, security_profile, expected_status)`) to a single-axis
   table over `strict_flag` only: `strict=False → WARNING`, `strict=True →
   FATAL`. Remove the `profile` parameter from the corresponding test
   function signature (~line 1630) and its `_make_ctx(..., security_profile=profile)`
   usage (~line 1661).
4. Apply the same collapse to the second FATAL/WARNING matrix at lines
   1675-1736 and its associated test function (~lines 1743-1763).
5. Re-read `test_classification_equivalent_across_security_profiles()`
   (~lines 795-827) and `_dup_ctx()` (~lines 829-882) in full at execution
   time: if their point is specifically that duplicate-tool classification
   does NOT depend on `security_profile` (a claim now vacuously true once
   there is only one profile), narrow the parametrize list at lines 795-796
   to `[SecurityProfile.PRODUCTION]` only, or remove the parametrize
   dimension entirely and delete `_dup_ctx(SecurityProfile.LOCAL)`'s call at
   line 876.

### Method
Direct `Edit` at each site listed above; re-run
`grep -n "SecurityProfile\|security_profile\|production_mode\|_is_fatal_severity" tests/agent/services/test_mcp_tool_discovery.py`
immediately before editing to confirm no further drift since this document's
creation (verified 2026-09-04, 34 matches at the line numbers cited above).

### Details
Representative current matrix (verified 2026-09-04, lines 1673-1691):
```python
@pytest.mark.parametrize(
    "strict, profile, expected",
    [
        (False, SecurityProfile.LOCAL, StartupCheckStatus.WARNING),
        (False, SecurityProfile.PRODUCTION, StartupCheckStatus.FATAL),
        (True, SecurityProfile.LOCAL, StartupCheckStatus.FATAL),
        (True, SecurityProfile.PRODUCTION, StartupCheckStatus.FATAL),
    ],
)
async def test_...(
    self,
    strict: bool,
    profile: SecurityProfile,
) -> None:
    """FATAL iff strict or security_profile==PRODUCTION, else WARNING."""
    ...
    ctx = _make_ctx({"srv": _server()}, http, security_profile=profile)
```
After:
```python
@pytest.mark.parametrize(
    "strict, expected",
    [
        (False, StartupCheckStatus.WARNING),
        (True, StartupCheckStatus.FATAL),
    ],
)
async def test_...(
    self,
    strict: bool,
) -> None:
    """FATAL iff strict (security_profile no longer affects severity)."""
    ...
    ctx = _make_ctx({"srv": _server()}, http)
```
Update the docstring to remove the retired `security_profile==PRODUCTION`
clause. Apply the equivalent transformation to the other matrix at lines
1610-1623/1730-1736.

## Compatibility considerations
Coupled to row 9 — this row's edits assume row 9's `_is_fatal_severity()`
body is already `self._is_strict()`-only; landing this row before row 9
would make these tests fail against the still-conditional method.

## Security considerations
None directly — test-only file.

## Rollback considerations
Multi-site edit within a single file, under version control; revert via
`git revert` if needed, together with row 9.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/services/test_mcp_tool_discovery.py` | Unit | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | All tests pass against row 9's `self._is_strict()`-only severity logic; no test references `SecurityProfile.LOCAL` |

## Completion criteria
No test in this file references `SecurityProfile.LOCAL`; the FATAL/WARNING
matrix tests assert severity depends only on `strict`.

## Out of scope
Any test in this file not listed in Scope (confirmed unaffected by direct
read).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Coordinate with row 9's own edit; largest test file in this Plan (34 references) |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row's target file is itself the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | N/A: test-only file |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: tests/agent/services/test_mcp_tool_discovery.py
