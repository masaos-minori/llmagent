# Colon-form coverage for `SECRET_PATTERNS`

## Goal

Extend `SECRET_PATTERNS` so unquoted and quoted colon-separated `key: value` secrets for the
existing key names are masked like their `key=value` forms, without touching the
`_mask_secrets` signature, the substitution lambda, or any call site (Plan REQ-001 unquoted
colon masking, REQ-002 quoted colon masking, REQ-003 whitespace/multi-line decision, REQ-005
signature/call-site stability).

## Scope

- Append two patterns to `SECRET_PATTERNS`: quoted-colon first, then unquoted-colon (order
  rationale in Design decisions).
- No new key names beyond the existing alternation; no change to the five existing patterns or
  the quoted-JSON pattern.
- The UNK-01 decision is recorded here and pinned by tests in row 02: quoted values are masked
  in full including whitespace; unquoted values keep stopping at the first whitespace/newline
  (`(\S+)`), so unquoted whitespace and multi-line values are out of coverage by decision.

## Assumptions

- Verified 20261102: `SECRET_PATTERNS` holds 6 patterns (`scripts/agent/secrets_masker.py:6-17`);
  `password: hunter2` and `token: abc123` pass through unmasked; the substitution is
  `m.group(1) + "***MASKED***"` for every pattern.
- Per the Plan's Phase 1 (tests first), the document for row 02 (`tests/agent/test_secrets_masker.py`)
  is executed before this document; its new tests fail until these patterns land.
- Batch sequencing: this Plan lands before `diagmask001` and `maskargs001`, which extend or reuse
  the final pattern set (Plan Scope Dependencies).
- Call-site behavior (`startup_mcp_starter.py`, `http_lifecycle_errors.py`,
  `http_lifecycle_health_checker.py`, `shared/retry_helper.py`) is regression-verified, not
  modified (reference files).

## Design decisions

- Reuse the existing key alternation without word boundaries — `(?:password|passwd|pwd|api[_-]?key|apikey|secret|token)`
  — so key suffixes match exactly like the `key=value` patterns do today (`access_token: abc`,
  `X-Api-Key: abc` are masked; REQ-001).
- Order the appended patterns last in `SECRET_PATTERNS` (quoted-colon before unquoted-colon):
  the `Bearer` pattern then runs before the colon patterns, so `token: Bearer abc` becomes
  `token: Bearer ***MASKED***` and the subsequent unquoted-colon pass masks the leftover
  `Bearer` word — no part of the token survives (AC-4, Plan Risk mitigation).
- The quoted-colon pattern consumes its quotes in the matched region, so the shared
  `m.group(1) + "***MASKED***"` lambda works unchanged and the whole quoted value disappears
  (REQ-002).
- Bounded, non-nested quantifiers only (`[^'"]*`, `\S+`): tails are 512/500 chars, so no
  catastrophic-backtracking risk (Plan Risk 3 mitigation).

## Alternatives considered

- Mask unquoted values to end of line (Plan UNK-01 alternative b) — rejected as default:
  over-masks trailing prose and would change the pinned `token=abc def` expectation; the Plan's
  default (a) keeps quoted-only whitespace coverage.
- A single colon pattern with a `(?:'...'|\"...\"|\S+)` value alternation — rejected: mixes
  quoted/unquoted precedence rules in one pattern and makes the AC-4 ordering test harder to
  read; two patterns keep each shape explicit.

## Implementation
### Target file
`scripts/agent/secrets_masker.py`

### Procedure
Append two compiled patterns after the existing quoted-JSON pattern in `SECRET_PATTERNS`
(current order 6 patterns, `secrets_masker.py:6-17`).

### Method
```python
re.compile(r"(?i)((?:password|passwd|pwd|api[_-]?key|apikey|secret|token)\s*:\s*)['\"][^'\"]*['\"]"),
re.compile(r"(?i)((?:password|passwd|pwd|api[_-]?key|apikey|secret|token)\s*:\s*)(\S+)"),
```
- Pattern 7 (quoted colon): group 1 ends after `: `; the quotes and value are inside the matched
  region, replaced by `***MASKED***`.
- Pattern 8 (unquoted colon): group 2 (`\S+`) masked; stops at whitespace/newline.
- No edits to `_mask_secrets`, the lambda, or the existing six entries.

### Details
- `Authorization: Bearer abc` is still handled by the existing Authorization pattern first;
  neither colon pattern matches a key alternation inside `Authorization` text, so scheme
  preservation is untouched (AC-4).
- The quoted-JSON pattern (`"password": "hunter2"`) runs before the new ones and already masks
  such lines; the colon patterns do not re-match the resulting `"password": "***MASKED***"`
  text (quote sits between key and colon), keeping masking idempotent (AC-5).
- Double-masking artifact: `token: Bearer abc` lands on `token: ***MASKED*** ***MASKED***`;
  accepted by AC-4 (test row asserts no leak, not exact shape) and stable under re-application.

## Compatibility considerations

- `test_pattern_count_grew_by_exactly_one` (`tests/agent/test_secrets_masker.py:138`) fails on
  this change by design; row 02 updates it to `== 8` in the same commit (Plan Risk 5).
- Four call-site modules keep their behavior (masked text only changes shape); regression tests
  named in the Validation plan must pass unchanged (REQ-005, AC-6).

## Security considerations

- Fail-open risk reduced: YAML/log-style `key: value` secrets previously leaked verbatim into
  startup failure reports. Accepted over-masking: prose like `Invalid token: expired` gets its
  trailing word masked (Plan Risk 2, accepted for a security masker).

## Rollback considerations

- Revert the single commit; no persistence or schema involvement. Rolling back re-exposes the
  leak — rollback only alongside the dependent plans' reverts.

## Validation plan

- `uv run pytest tests/agent/test_secrets_masker.py` — green only after row 02's updates land
  (Phase 1 red until then).
- `uv run pytest tests/agent/test_http_lifecycle_command_validator.py tests/agent/test_startup_mcp_starter.py`
  and the other `tests/agent/test_http_lifecycle*.py` — pass unchanged.
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml`,
  `uv run python tools/check_module_size.py`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`
  per `rules/toolchain.md`.

## Completion criteria

- Colon forms (`password: hunter2`, `api_key: 'abc def'`, `access_token: abc`, `X-Api-Key: abc`)
  leave no secret characters in the output; all pre-existing masker tests pass after the count
  update; signature, lambda and call sites are byte-identical in `git diff`.

## Out of Scope

- New key names, other separators, bare-JWT/URL-credential shapes (owned by `diagmask001`).
- Unquoted whitespace / multi-line masking (decision: out, pinned by row 02 tests).
- Call-site changes; docs (row 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append quoted-colon and unquoted-colon patterns to `SECRET_PATTERNS` | Completed | 20261102-155107 | 20261102-160413 | Executes after row 02's failing tests land (Plan Phase 1) executes after row 02 red tests landed (Plan Phase 1); changed files: scripts/agent/secrets_masker.py, tests/agent/test_secrets_masker.py 2 colon-form patterns appended to SECRET_PATTERNS; helper and call sites unchanged; resolves the red phase |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261102-160413 | Coverage run needs row 02 tests targeted 40 passed; ruff/mypy(491 files)/lint-imports 6 kept/bandit -ll exit 0/pre-commit on changed files passed; full suite 11272 passed 8 skipped; secrets_masker coverage 100%; ast-grep CLI unavailable, grep confirms no bare except |

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
- **Requirement ID**: REQ-001 (unquoted colon masking), REQ-002 (quoted colon masking), REQ-003 (whitespace/multi-line decision), REQ-005 (signature/call-site stability)
- **Source issue**: issues/20261003-180324_secmask001_secrets-masker-leaks-unmasked-value.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140116_secmask001_secrets-masker-leaks-unmasked-value.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132558
- **Related target files**: scripts/agent/secrets_masker.py