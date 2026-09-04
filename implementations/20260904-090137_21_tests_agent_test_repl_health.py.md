## Goal
Update every call site in this file that passes `production_mode=` to
`audit_security_defaults()`/`check_readiness()` to match rows 6/11's
unconditional-FATAL signatures (parameter removed), and convert or remove
every test whose assertion depends on the now-eliminated
`production_mode=False` warnings-only return path.

## Scope
- **In-Scope**: every call site passing `production_mode=` to
  `audit_security_defaults()` (verified 2026-09-04: ~30 call sites at lines
  408, 422, 457, 471, 487, 509, 522, 539, 555, 568, 586, 602, 616, 642, 671,
  699, 728, 754, 780, 803, 829, 851, 877, 900) and to `check_readiness()`
  (lines 923, 932, 942, 949, 960, 969); the `_make_ctx()`-equivalent helper's
  `security_profile: str = "local"` default (line 355) and its
  `SecurityProfile(security_profile)` construction (line 378); every
  standalone `security_profile="local"`/`SecurityProfile.LOCAL` fixture
  value (lines 390-396).
- **Out-of-Scope**: any test in this file unrelated to
  `audit_security_defaults()`/`check_readiness()`/`security_profile` — this
  file's full content beyond the grep-matched lines has not yet been read in
  full; confirm scope boundary at execution time.

## Assumptions
- **This is the largest and most structurally-affected test file in this
  Plan's scope.** Both `audit_security_defaults()` (row 11) and
  `check_readiness()` (row 6) drop their `production_mode` parameter
  entirely and become unconditionally FATAL-on-violation. This eliminates an
  entire behavioral branch (the `production_mode=False` "return a warnings
  list instead of raising" path) that a large fraction of this file's tests
  currently exercise. Must execute after rows 6 and 11 land.

## Design decisions
- For every call site currently written as
  `audit_security_defaults(ctx, production_mode=True)`: drop the keyword
  argument, since `True` is now the only behavior — `audit_security_defaults(ctx)`.
- For every call site currently written as
  `warnings = audit_security_defaults(ctx, production_mode=False)`
  (expecting a returned warnings list): re-read the specific test at
  execution time and choose one of:
  (a) if the test's real purpose is to confirm a *specific violation is
  detected at all* (regardless of severity), convert it to
  `with pytest.raises(RuntimeError): audit_security_defaults(ctx)`, or
  (b) if the test is a near-duplicate of an existing `production_mode=True`
  counterpart for the same violation (i.e. the file already has a
  `production_mode=True` version of the same scenario), delete the
  `production_mode=False` version as now-redundant rather than convert it.
- Change `_make_ctx()`-equivalent's `security_profile: str = "local"`
  default (line 355) to `"production"`.
- Apply the same drop-the-keyword-argument treatment to all 6
  `check_readiness()` call sites (lines 923-969).

## Alternatives considered
- Keeping a `production_mode` parameter shim in this test file's own helpers
  that always forces `True` internally: rejected — the parameter is removed
  from the real function signatures (rows 6/11); a test-local shim would
  mask a `TypeError` that should surface immediately if any call site is
  missed.

## Implementation
### Target file
`tests/agent/test_repl_health.py`

### Procedure
1. Change the context-builder helper's `security_profile: str = "local"`
   default (verified 2026-09-04, line 355) to `"production"`, and its
   `SecurityProfile(security_profile)` construction (line 378) is unaffected
   (still valid syntax, now always resolving to `PRODUCTION`).
2. Update the two explicit `security_profile="local"`/
   `SecurityProfile.LOCAL` fixture setups (lines 390-396) to `"production"`/
   `SecurityProfile.PRODUCTION`.
3. For each of the ~24 `audit_security_defaults(ctx, production_mode=True)`
   call sites: drop the keyword argument.
4. For each of the ~13 `audit_security_defaults(ctx, production_mode=False)`
   call sites that assign the result to `warnings`/`warnings_dev`: re-read
   the enclosing test, then apply Design decisions' choice (a) or (b) per
   test. Re-run
   `grep -n "production_mode=False" tests/agent/test_repl_health.py`
   at execution time to enumerate the exact current set before editing (list
   may have shifted from this document's creation-time grep).
5. For each of the 6 `check_readiness(ctx, production_mode=...)` call sites
   (lines 923-969): drop the keyword argument; for any
   `production_mode=False` call site among them expecting a non-raising
   result, apply the same (a)/(b) choice as step 4, informed by
   `check_readiness()`'s own new unconditional-FATAL behavior (row 6).
6. Rename `test_production_mode_no_auth_raises`,
   `test_production_mode_all_authed_no_error`, and any other test whose name
   references "production_mode" as a distinguishing condition, since this
   Plan's post-landing behavior no longer has a non-production mode to
   contrast against (e.g. `test_no_auth_raises`,
   `test_all_authed_no_error`).

### Method
Direct `Edit`, driven by a full read of this file at execution time — this
document identifies every call-site line via grep but defers the per-test
raise-vs-delete judgment (Design decisions) to execution time, when the full
surrounding test body is read.

### Details
Representative pair (verified 2026-09-04, lines 412-423):
```python
def test_production_mode_no_auth_raises(self) -> None:
    ...
    security_profile="production",
    ...
    ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
    with pytest.raises(RuntimeError):
        audit_security_defaults(ctx, production_mode=True)
```
After (rename + drop keyword):
```python
def test_no_auth_raises(self) -> None:
    ...
    security_profile="production",
    ...
    ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
    with pytest.raises(RuntimeError):
        audit_security_defaults(ctx)
```
Representative `production_mode=False` conversion candidate (verified
2026-09-04, line ~408):
```python
warnings = audit_security_defaults(ctx, production_mode=False)
# ... assert some violation appears in `warnings`
```
After (choice (a), if no `production_mode=True` counterpart exists for this
exact scenario):
```python
with pytest.raises(RuntimeError):
    audit_security_defaults(ctx)
```

## Compatibility considerations
Coupled to rows 6 and 11 — must land strictly after both.

## Security considerations
None directly — test-only file; net effect documents a security-hardening
behavior change (no more silent-warning path).

## Rollback considerations
Large multi-site edit within a single file, under version control; revert
via `git revert` if needed, together with rows 6 and 11.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/test_repl_health.py` | Unit | `uv run pytest tests/agent/test_repl_health.py -v` | All tests pass against rows 6/11's unconditional-FATAL signatures; no call site passes `production_mode=`; no test references `SecurityProfile.LOCAL` or `"local"` |

## Completion criteria
No reference to `production_mode=` as a keyword argument, `SecurityProfile.LOCAL`,
or the string `"local"` as a profile value remains in this file.

## Out of scope
Any test in this file unrelated to `security_profile`/`production_mode`,
confirmed at execution time via a full file read.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260904 | 20260904 | Mechanically stripped `production_mode=` from ~36 call sites via scripted regex, then ran the file to find only 6 actual failures (fewer than the ~13 estimated `production_mode=False` sites — most were already `production_mode=True` and needed no behavior change); deleted 5 now-redundant `_local`/`_dev_mode`-flavored duplicate tests and renamed their `_production`/`_in_production_mode` siblings |
| 2 | Add or update tests per Validation plan | Completed | 20260904 | 20260904 | This row's target file is itself the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260904 | 20260904 | ruff clean; 57 passed (62 - 5 removed duplicates). Full-suite diff deferred to end of batch |
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
- **Requirement ID**: REQ-005, REQ-008
- **Source issue**: issues/done/20260902-143333_localremoval_remove_local_mode_and_enforce_production_grade_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-091417_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-090137
- **Related target files**: tests/agent/test_repl_health.py
