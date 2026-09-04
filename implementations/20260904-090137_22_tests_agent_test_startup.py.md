## Goal
Update `test_startup.py`'s `_make_startup()`/`_make_startup_ctx()` helpers
and every test parametrized over `SecurityProfile.LOCAL`/`production_mode`
to match rows 5/6/9/11's unconditional-FATAL, parameter-removed signatures.

## Scope
- **In-Scope**: `_make_startup()`'s `security_profile: SecurityProfile = SecurityProfile.LOCAL`
  default (verified 2026-09-04, line 48) and its 12 call sites passing
  `security_profile=SecurityProfile.LOCAL` explicitly (lines 82, 93, 135,
  151, 169, 189, 217, 1395, 1406, 1437, 1464, 1511, plus bare assignments at
  1476, 1490, 1600); `_make_startup_ctx()`'s `production_mode: bool = False`
  parameter (line 899) and its internal
  `SecurityProfile.PRODUCTION if production_mode else SecurityProfile.LOCAL`
  branch (lines 905-906); the parametrize table at lines 767-771 covering
  `[SecurityProfile.PRODUCTION, SecurityProfile.LOCAL]`; every test using
  `_make_startup_ctx(production_mode=...)` (lines 1012, 1030, 1050, 1067,
  1273, 1290); the comment block at lines 1623/1631 referencing
  `security_profile_val`.
- **Out-of-Scope**: any test in this file not listed above — this file's
  full content beyond the grep-matched lines has not yet been read; confirm
  scope boundary at execution time.

## Assumptions
- **Largest reference count of any file in this Plan (40+ matches).** This
  file tests `StartupOrchestrator`/`_make_startup()`'s integration surface
  across the entire refactor series discovered during this Plan's
  revalidation (rows 5-8). Must execute after rows 1, 2, 5, 6, 7, 8, 9, and
  11 all land, since this file's tests exercise the combined end-to-end
  behavior of all of them.
- The comment at line 1623 ("REQ-002 consequence...") refers to a *different*
  Plan's own internal REQ-002 numbering (the upstream refactor's own
  requirement ID, unrelated to this Plan's REQ-002) — re-read this comment's
  full context at execution time before deciding whether it needs updating;
  do not assume it maps to this Plan's REQ-002 (`config_dataclasses.py`
  default change).

## Design decisions
- Change `_make_startup()`'s `security_profile` default (line 48) from
  `SecurityProfile.LOCAL` to `SecurityProfile.PRODUCTION`.
- For every call site explicitly passing `security_profile=SecurityProfile.LOCAL`:
  re-read the enclosing test at execution time. If the test's purpose is
  generic (any valid profile), change to `SecurityProfile.PRODUCTION` or
  remove the explicit argument (relying on the new default). If the test
  specifically compares Local-vs-Production behavior (e.g. the parametrize
  table at lines 767-771, or the FATAL-assertion pairs at lines 1010-1067
  and 1270-1290), collapse to a single-profile case per Design decisions
  below.
- Collapse `_make_startup_ctx()`'s `production_mode: bool` parameter (line
  899) entirely, removing the `SecurityProfile.PRODUCTION if production_mode
  else SecurityProfile.LOCAL` branch (lines 905-906) and always constructing
  with `SecurityProfile.PRODUCTION`. Every caller passing
  `production_mode=True` (lines 1012, 1050, 1273) drops the keyword
  argument; every caller passing `production_mode=False` (lines 1030, 1067,
  1290) must be re-read individually — since rows 6/11 make FATAL
  unconditional, a `production_mode=False` test currently asserting a
  non-FATAL/non-raising outcome is now testing an eliminated behavior and
  must either be deleted (if a `production_mode=True` counterpart for the
  same scenario already exists) or converted to also assert FATAL.
- Collapse the parametrize table at lines 767-771
  (`[SecurityProfile.PRODUCTION, SecurityProfile.LOCAL]`) to a single case
  (`SecurityProfile.PRODUCTION` only), removing the parametrize decorator
  entirely if only one value remains, per the same reasoning applied to row
  17's equivalent tables.

## Alternatives considered
- Leaving `production_mode`/`security_profile` axes in place with both
  values forced to resolve to the same outcome: rejected — same reasoning as
  rows 17/19/21: `SecurityProfile.LOCAL` will not exist after row 1, so any
  literal reference fails at collection time, not merely produces a
  redundant assertion.

## Implementation
### Target file
`tests/agent/test_startup.py`

### Procedure
1. Change `_make_startup()`'s default (line 48) to
   `SecurityProfile.PRODUCTION`.
2. Re-read and update each of the 15 `security_profile=SecurityProfile.LOCAL`/
   bare-assignment call sites (lines 82, 93, 135, 151, 169, 189, 217, 1395,
   1406, 1437, 1464, 1476, 1490, 1511, 1600) per Design decisions.
3. Collapse `_make_startup_ctx()` (lines 899-906) to always construct
   `SecurityProfile.PRODUCTION`, removing the `production_mode` parameter.
4. Update the 6 `_make_startup_ctx(production_mode=...)` call sites (lines
   1012, 1030, 1050, 1067, 1273, 1290) per Design decisions — drop the
   keyword argument for `True` cases; re-read and resolve `False` cases
   individually (delete-as-redundant or convert-to-FATAL).
5. Collapse the parametrize table at lines 767-771 and its associated test
   function (~line 786) to a single `SecurityProfile.PRODUCTION` case,
   removing the parametrize decorator.
6. Re-read the comment block at lines 1623-1631 in full context; update only
   if it factually describes behavior this Plan's rows change (distinguish
   from the unrelated upstream refactor's own "REQ-002" label per
   Assumptions).

### Method
Direct `Edit`, driven by a full read of this file at execution time — this
document identifies every call-site line via grep but defers per-test
delete-vs-convert judgment to execution time.

### Details
`_make_startup_ctx()` current (verified 2026-09-04, lines 897-907):
```python
def _make_startup_ctx(
    ...,
    production_mode: bool = False,
) -> MagicMock:
    ...
    ctx.cfg.mcp.security_profile = (
        SecurityProfile.PRODUCTION if production_mode else SecurityProfile.LOCAL
    )
```
After:
```python
def _make_startup_ctx(
    ...,
) -> MagicMock:
    ...
    ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
```
Representative FATAL-assertion pair to resolve (verified 2026-09-04, lines
1045-1067):
```python
async def test_readiness_fatal_via_production_mode_raise(self) -> None:
    """FATAL is produced via the production_mode raise + generic except catch — the ..."""
    ctx = _make_startup_ctx(production_mode=True)
    ...

async def test_...(self) -> None:  # line 1067's production_mode=False counterpart
    ctx = _make_startup_ctx(production_mode=False)
    ...
```
Re-read both test bodies in full at execution time; if the `False` case
currently asserts a non-FATAL outcome, delete it (row 6 makes this outcome
unreachable) and rename the `True` case to drop "via_production_mode" from
its name (e.g. `test_readiness_fatal_on_check_readiness_raise`), updating its
docstring accordingly.

## Compatibility considerations
Coupled to rows 1, 2, 5, 6, 7, 8, 9, and 11 — must land strictly after all of
them, as the last test file in the sequence.

## Security considerations
None directly — test-only file; net effect documents a security-hardening
behavior change (no more non-FATAL startup path).

## Rollback considerations
Large multi-site edit within a single file, under version control; revert
via `git revert` if needed, together with the coupled rows above.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_startup.py` | Unit | `uv run pytest tests/agent/test_startup.py -v` | All tests pass against the fully-landed unconditional-FATAL behavior across the entire startup refactor surface; no test references `SecurityProfile.LOCAL` or a `production_mode` keyword argument |

## Completion criteria
No reference to `SecurityProfile.LOCAL` or `production_mode=` as a keyword
argument remains in this file.

## Out of scope
Any test in this file unrelated to `security_profile`/`production_mode`,
confirmed at execution time via a full file read.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Largest reference count in this Plan (40+); must land last, after all coupled rows |
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
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: tests/agent/test_startup.py
