## Goal
- Add detection-parity tests against the pre-fix URL userinfo pattern and a machine-speed-independent scaling regression check to `tests/agent/test_secrets_masker.py` (`REQ-003`: parity; `REQ-004`: scaling).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: two new test classes appended to the file, and the imports they need.
- Not in scope: existing tests (all stay unchanged), `tests/agent/test_tool_result_formatter.py`.
- Ordering note: filename order runs the sibling procedure for `scripts/agent/secrets_masker.py` first, so the fix is already in place when these tests are added; the Plan's "run the scaling check against the unchanged pattern" is therefore shown by pointing the scaling helper once at the retained pre-fix pattern (step 4), not committed.

## Assumptions
- The pre-fix pattern is `(?i)([a-z][a-z0-9+.-]*://(?:[^/\s:@]+:)?)([^/\s@]+)(?=@)` (the text of the entry in `SECRET_PATTERNS` before the fix); the test keeps it as a reference with a comment that it only guards this equivalence. Falsifier: parity fails on any input, then stop and report (do not change detection).
- The fixed pattern is found with `next(p for p in SECRET_PATTERNS if "://" in p.pattern)` so the test does not depend on list position.
- `_mask_secrets` substitutes each pattern with `m.group(1) + "***MASKED***"`; the parity helper applies the same substitution to one pattern.
- Pre-fix timings on `"x"` runs were 2.5 s at 10,000 and 9.7 s at 20,000 characters; after the fix both are milliseconds.

## Design decisions
- Parity: fixed forms plus a seeded generated corpus (`random.Random` with a fixed seed, small alphabet including `://`, `@`, `:`, `/`, digits, `+`, `.`, `-`, letters, space), each compared with the reference pattern.
- Scaling: time one `re.sub` of the fixed pattern on 10,000 and 20,000 characters (letter run and digit run), best of three; pass when `t(20,000) <= 3 * t(10,000) + 0.05` (quadratic gives about 4x and tens of seconds, so it fails) and `t(20,000) < 2.0` s. The additive 0.05 s absorbs noise when both are milliseconds, so the check does not depend on machine speed.

## Alternatives considered
N/A: a bare `pytest-timeout` marker depends on machine speed; the ratio plus a wide absolute bound is chosen.

## Implementation
### Target file
`tests/agent/test_secrets_masker.py`

### Procedure
1. Add `import random`, `import re`, and `import time` (new) next to the existing `import os`.
2. Append class `TestUrlUserinfoParity` (new): module-level reference pattern `_PRE_FIX_URL_USERINFO` (new) and helper `_sub` (new); a parametrized test over fixed forms (user and password, user only, no `@`, scheme-less text, leading digit before the scheme, `+.-` inside the scheme, uppercase scheme, empty string) comparing outputs; a test over 20,000 seeded strings of length up to 30.
3. Append class `TestUrlUserinfoScaling` (new) with the two shapes of Design decisions, written so the pattern under test is a parameter of a helper `_best_time` (new).
4. Demonstrate red once, not committed: point the helper at `_PRE_FIX_URL_USERINFO` (new) and run the scaling test; it must fail on the ratio. Revert that edit.
5. Run `uv run pytest tests/agent/test_secrets_masker.py -o addopts=""`, serially and with `-n auto`, several times.

### Method
Use `time.perf_counter`, best of three, on `pattern.sub(lambda m: m.group(1) + "***MASKED***", text)`. Name failures with the differing input (`assert out_new == out_old, repr(text)`). Keep the existing tests and imports untouched.

### Details
- Keep each new test under about 1 s after the fix; the corpus loop must stay under that.
- Do not weaken or edit `test_pattern_count_matches_inventory` or `test_large_input_terminates`.
- Comment that the reference pattern is the pre-fix text kept only for the equivalence check.

## Compatibility considerations
N/A: test-only addition.

## Security considerations
- The parity test is the guard that no masked secret form becomes unmasked; keep the fixed forms covering user-and-password and user-only userinfo.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_secrets_masker.py tests/agent/test_tool_result_formatter.py -o addopts=""`, serially and `-n auto`, repeated.
- `uv run ruff format tests/agent/test_secrets_masker.py`, `uv run ruff check tests/agent/test_secrets_masker.py`, `uv run mypy --no-namespace-packages tests/agent/test_secrets_masker.py`.

## Completion criteria
- The parity tests pass and name the input on a difference (`AC-003`).
- The scaling check passes after the fix and failed against the pre-fix pattern when shown once (`AC-004`).
- Existing tests in the file pass unchanged.

## Out of Scope
- Any change to `scripts/agent/secrets_masker.py` (sibling procedure) or to other test files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-115420 | 20261113-120518 | Changed tests/agent/test_secrets_masker.py: imports random, re, time and SECRET_PATTERNS; new classes TestUrlUserinfoParity (13 fixed forms, a masked-output check, a seeded corpus of 20,000 strings compared with the retained pre-fix pattern) and TestUrlUserinfoScaling (10,000 versus 20,000 characters for x, 1, and a. runs: t_large <= 3 * t_small + 0.05 and t_large < 2.0). The pattern under test is found by the :// in its text, not by list position. |
| 2 | Add or update tests per Validation plan | Completed | 20261113-120518 | 20261113-120518 | Red shown once and reverted (not committed): with the helper pointed at the pre-fix pattern, the scaling cases x and a. fail on the ratio and the digit case passes, as digits never matched the scheme start. File plus formatter tests: 133 passed in three random-order serial runs and three -n auto runs; existing tests unchanged. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261113-120518 | 20261113-120518 | ruff and mypy clean. Full suite serial 12177 passed (18 new), 3 failed: the known mdq cases (unrelated, Plan testspeed004). diff-cover N/A: no source file changed in this procedure. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261113-120518 | 20261113-120518 | N/A: no docs/00_index.md task-scope mapping for tests/agent/test_secrets_masker.py |

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
- **Requirement ID**: REQ-003 (parity tests), REQ-004 (scaling regression check)
- **Source issue**: issues/20261112-183807_testspeed002_bound-secret-scrub-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-091430_testspeed002_bound-secret-scrub-cost.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-101952
- **Related target files**: `tests/agent/test_secrets_masker.py`
