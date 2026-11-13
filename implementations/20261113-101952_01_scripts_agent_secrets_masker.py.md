## Goal
- Make the URL userinfo pattern of `SECRET_PATTERNS` scan in near-linear time so `mask_args({"payload": "x" * 100_000}, [])` completes in under 1 s instead of about 67 s, with identical masking output for every input (`REQ-002`: fix in place; `REQ-005`: under 1 s; `REQ-001`: record the cause; `REQ-006`: deploy hand-off).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the one regular expression in `SECRET_PATTERNS` that contains `://`.
- Not in scope: the other 13 patterns, `_mask_secrets` and `detects_secrets` bodies and docstrings, any caller, the pattern count.

## Assumptions
- Cause (measured on `"x" * n`): the pattern's scheme class matches the whole run of scheme characters from every start position and then fails for lack of `://`, so the cost is quadratic (0.77 s at 5,000, 2.5 s at 10,000, 9.7 s at 20,000 characters); the other 13 patterns together take under 0.05 s at 20,000. Falsifier: the per-pattern profile in step 1 names a different pattern.
- The candidate in Method gave identical output to the current pattern on 200,000 random strings and about 0.02 s at 100,000 characters when tried outside the repository. This procedure re-proves it through the parity tests of the sibling procedure for `tests/agent/test_secrets_masker.py`.
- `test_pattern_count_matches_inventory` pins 14 patterns, so the pattern is changed in place, not added.
- Docstrings and signatures stay unchanged so the generated reference table does not drift.

## Design decisions
- Anchor each match attempt to the start of a scheme-character run (a negative lookbehind on the scheme-character class) and allow leading digits and `+.-` before the first letter, so the leftmost match start, and with it the preserved prefix group, stay as they are today.
- If the parity test shows any differing output, stop and report the trade-off instead of changing detection.

## Alternatives considered
- A possessive quantifier: rejected, every start position still scans to the end of the run.
- A literal `"://"` pre-check in `_mask_secrets`: kept only as a fallback; it removes the measured case but not a long run followed by `://`.
- Bounding the scheme length: rejected, it changes what is detected.

## Implementation
### Target file
`scripts/agent/secrets_masker.py`

### Procedure
1. Profile first: time each pattern of `SECRET_PATTERNS` with one `re.sub` on `"x"`, digit, space, and `a.` runs of 10,000 and 20,000 characters, and record the result for the commit message (expected: only the URL userinfo pattern is superlinear).
2. Replace the URL userinfo entry (the last element of `SECRET_PATTERNS`, the only one containing `://`) with the anchored form in Method, keeping it a `re.compile(...)` entry in the same position so the list length stays 14.
3. Re-run the profile at 100,000 characters and record the before and after timings and the root cause in the commit message.
4. Run `uv run pytest tests/agent/test_secrets_masker.py tests/agent/test_tool_result_formatter.py tests/agent/test_diagnostic_store_security.py -o addopts=""`.

### Method
The current pattern is `(?i)([a-z][a-z0-9+.-]*://(?:[^/\s:@]+:)?)([^/\s@]+)(?=@)`. The candidate is `(?i)((?<![a-z0-9+.-])[0-9+.-]*[a-z][a-z0-9+.-]*://(?:[^/\s:@]+:)?)([^/\s@]+)(?=@)`: attempts start only where no scheme character precedes, any leading digits and `+.-` are consumed into group 1 (which `_mask_secrets` re-emits unchanged), and the rest is the same, so output stays equal while each run is scanned once.

### Details
- Keep the `r"..."` raw-string style of neighbouring entries.
- Do not edit `_mask_secrets`, `detects_secrets`, or any docstring.
- Run `uv run python tools/generate_reference_table.py --check` and `uv run python tools/check_module_size.py` after the edit.

## Compatibility considerations
- Output of `_mask_secrets`, `detects_secrets`, and `mask_args` is identical by construction and by the parity test; the six importing modules need no change.

## Security considerations
- No secret form currently masked may become unmasked: the parity test against the pre-fix pattern is the guard. Do not add or relax any other pattern.

## Rollback considerations
N/A: revert the commit (the only runtime effect is the scrub cost).

## Validation plan
- Tests of step 4; `uv run ruff format scripts/agent/secrets_masker.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/generate_reference_table.py --check` and `uv run python tools/check_module_size.py`.
- Full suite once (`uv run pytest -m "not integration and not production_paths_allowed"`; three `tests/mcp_servers` failures are pre-existing) and coverage on changed lines at least 90%.

## Completion criteria
- The profile at 100,000 characters shows no superlinear pattern; `mask_args` on `"x" * 100_000` takes under 1 s (`AC-001`, `AC-005`).
- `len(SECRET_PATTERNS) == 14`; names and signatures unchanged; existing masker, formatter, and diagnostic-store tests pass unchanged (`AC-002`).
- Deploy hand-off recorded: change committed and pushed first, then `skills/deploy/SKILL.md`, the user's decision (`AC-006`).

## Out of Scope
- Other patterns, other input shapes beyond the profiled ones (a new finding becomes a follow-up Issue), `tool_result_formatter.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Parity and scaling tests come from the sibling procedure for `tests/agent/test_secrets_masker.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A expected: no docs state masking performance |

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
- **Requirement ID**: REQ-001 (record the cause), REQ-002 (fix the pattern in place), REQ-005 (under 1 s), REQ-006 (deploy hand-off)
- **Source issue**: issues/20261112-183807_testspeed002_bound-secret-scrub-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-091430_testspeed002_bound-secret-scrub-cost.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-101952
- **Related target files**: `scripts/agent/secrets_masker.py`
