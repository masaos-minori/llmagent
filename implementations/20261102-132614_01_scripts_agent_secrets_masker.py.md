# Shared detection function and extended `SECRET_PATTERNS`

## Goal

Add one shared detection function over `SECRET_PATTERNS` to `scripts/agent/secrets_masker.py`
and extend the pattern set to the shapes the diagnostic guard covered or missed, so log masking
and diagnostic persistence share one implementation (Plan REQ-001 single detection function,
REQ-003 new coverage, REQ-005 log masking keeps working with the extended set).

## Scope

- New `detects_secrets(text: str) -> bool` (new) implemented as `_mask_secrets(text) != text`.
- New `_KEY_ALT` (new) module constant unifying the key alternation:
  `password|passwd|pwd|api[_-]?key|apikey|secret|token|access_token|auth_token|client_secret|bearer|authorization|credential|private_key`
  — the composite names are listed explicitly: in the quoted-JSON pattern the alternation must match
  from the key start inside the quotes, so a suffix alternation (`secret`, `token`) cannot reach
  `"client_secret"`; in the unquoted `=`/`:` forms suffix matching also works.
- Extended/appended patterns (designed inventory; final literal pinned by row 03's count test):
  - widen the quoted-JSON pattern's key alternation to `_KEY_ALT` (new) and require a non-empty value
    (`[^"']+`), so `{"token": ""}` is not masked (UNK-01 empty-value exemption, AC-4);
  - `=>` separator pattern over `_KEY_ALT` (new) (`api_key => value` — REQ-003);
  - `=` pattern for the four new names (`bearer|authorization|credential|private_key`);
  - `:` pattern for `bearer|credential|private_key|access_token|auth_token|client_secret`
    (authorization deliberately excluded — see Design decisions);
  - single-token `authorization:` pattern with a negative lookahead for `Bearer`/`Basic` schemes;
  - bare-JWT pattern (empty group 1, three `eyJ...` base64url segments);
  - URL userinfo pattern (`scheme://user:pass@host`).
- `_mask_secrets` signature, substitution lambda and all four call-site modules unchanged.

## Assumptions

- Verified 20261102: `diagnostic_store.py:29-33` `_SENSITIVE_PATTERNS` is a single pattern with a
  16-char value minimum covering `api_key|secret|token|password|access_token|auth_token|bearer|client_secret`;
  `re` (line 11) is used only for it; the six `TestSensitiveDataRefusal` parametrized cases all use
  values of 16+ chars, so the shared set keeps every shape blocked (REQ-002).
- Verified 20261102 (probe): no existing masker test pins an empty JSON value; `{"token": ""}` is
  masked to `{"token": "***MASKED***"}` today by the JSON pattern's `*` quantifier (probe confirmed;
  corrected 20261102 — the earlier "passes through today" note was wrong). Changing `*` to `+` makes
  empty values pass through unchanged — required for the AC-4 empty-value exemption at the guard side
  (UNK-01 default: fail-closed, no minimum length; empty and already-masked values exempt) and pinned
  by row 03's exemption test.
- This row executes after secmask001's patterns have landed (Plan UNK-04 / Scope Dependencies):
  the pattern set here starts from secmask001's 8 patterns.
- Verified 20261102 (pattern probe): the shipped JSON pattern does not mask `{"client_secret": ...}`,
  `{"access_token": ...}` or `{"auth_token": ...}` today; the old diagnostic guard caught them through
  its explicit alternation. Without the three composite names in `_KEY_ALT`, the consolidated guard
  would stop refusing `{"client_secret": "client_secret_very_long_string_123"}` — an existing
  `TestSensitiveDataRefusal` case (REQ-002 regression). With them added, the probe confirms all
  AC-2/AC-3/AC-4 shapes, ordering (Bearer/Basic scheme kept), idempotence and a 10 000-char run
  under 6 ms. Final count stays 14.
- UNK-02 recorded default: the REQ-003 minimum set only (`=>`; `authorization` / `credential` /
  `private_key` (new) / `passwd` / `pwd`; bare JWT; URL userinfo); no further key names.

## Design decisions

- Detection predicate `masked != text` (Plan Decision 2): substitution to the same
  `***MASKED***` marker is a no-op, so already-masked text (`token=***MASKED***`) is not refused,
  and the function cannot diverge from the masker it guards.
- New key names go into the one `_KEY_ALT` (new) constant (Plan Decision 3): one alternation reused by
  every keyed pattern; no second config key — maskargs001's AC-5 reuses this same name list.
- `authorization` is excluded from the colon pattern and gets its own single-token pattern with
  `(?!(?:Bearer|Basic|Digest)\s)`: the pre-existing `Authorization: <scheme> <token>` pattern masks
  first and preserves the scheme (secmask001 AC-4; existing tests pin `Bearer`, `Basic` and `Digest`
  schemes — verified 20261102 against `tests/agent/test_secrets_masker.py:41-46`); a colon pattern
  matching `authorization:` afterwards would then mask the surviving scheme keyword. Unknown scheme
  keywords are masked (fail-closed).
- Bare-JWT pattern uses an empty group 1 (`()`) so the shared `m.group(1) + "***MASKED***"`
  lambda replaces the whole match (Plan Decision 3); anchored with `(?<![\w.-])` so tokens inside
  larger words do not match. URL pattern captures `scheme://user:` in group 1 and the password in
  group 2 with a `(?=@)` lookahead, masking nothing outside the credential.
- Patterns are appended after secmask001's two colon patterns; ordering cases in row 03 pin the
  no-partial-leak property (Plan Risks 2).

## Alternatives considered

- Per-pattern `search` for detection — rejected (Plan Decision 2): `(\S+)` matches the
  `***MASKED***` marker itself, so already-masked text would be refused without an extra no-op
  check.
- A separate shared module for patterns — rejected (Plan Decision 1): `secrets_masker.py` is
  already the pattern owner (stdlib-only leaf); a new file adds a second place without benefit.

## Implementation
### Target file
`scripts/agent/secrets_masker.py`

### Procedure
Add `_KEY_ALT` (new) and `detects_secrets` (new); widen the quoted-JSON entry; append the five
new compiled patterns after the two colon patterns. Do not touch `_mask_secrets`.

### Method
```python
_KEY_ALT = "password|passwd|pwd|api[_-]?key|apikey|secret|token|access_token|auth_token|client_secret|bearer|authorization|credential|private_key"

re.compile(rf"(?i)(\"(?:{_KEY_ALT})\"\s*[:,]\s*[\"'])([^\"']+)"),  # widened, non-empty value
re.compile(rf"(?i)((?:{_KEY_ALT})\s*=>\s*)(\S+)"),
re.compile(r"(?i)((?:bearer|authorization|credential|private_key)\s*=\s*)(?!>)(\S+)"),
re.compile(r"(?i)((?:bearer|credential|private_key|access_token|auth_token|client_secret)\s*:\s*)(\S+)"),
re.compile(r"(?i)((?:authorization)\s*:\s+)(?!(?:Bearer|Basic|Digest)\s)(\S+)"),
re.compile(r"(?i)()(?<![\w.-])eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
re.compile(r"(?i)([a-z][a-z0-9+.-]*://[^/\s:@]+:)([^/\s@]+)(?=@)"),

def detects_secrets(text: str) -> bool:
    """Return True when any SECRET_PATTERNS substitution would change the text."""
    return _mask_secrets(text) != text
```

### Details
- Suffix matching covers composites only in the unquoted forms: `access_token=abc` still matches the
  `token=` family; the three composite names are in `_KEY_ALT` (new) explicitly for the quoted-JSON
  and `=>` patterns, and the remaining new names are added where no suffix covers them
  (`authorization=`, `credential`, `private_key`).
- All quantifiers bounded and non-nested (`[^"']+`, `\S+`, fixed-segment JWT shape): no
  catastrophic backtracking on long diagnostic payloads (Plan Risks 4).
- `(?!>)` value guard on the four `=`-family patterns (3a finding 20261102): unguarded, the existing
  `api_key=` pattern matched `api_key => topsecretxyz` with value group `>` alone (greedy `\S+` stops
  at the space after `>`), leaving `topsecretxyz` unmasked and corrupting the output to
  `api_key =***MASKED*** topsecretxyz`. With the guard the `=` patterns skip `=>` forms and the arrow
  pattern masks them intact. Regression check: no existing test pins a `>`-prefixed `=` value; the
  `key=>x` (no space) case shifts from the `=` patterns to the arrow pattern, which covers every
  `=`-pattern key name (`password|passwd|pwd|api[_-]?key|apikey|secret|token` ⊂ `_KEY_ALT`).
- Designed final count: 14 patterns. If `code-implementation` consolidates entries, the count
  test literal is set to the final `len(SECRET_PATTERNS)` in the same change (row 03).

## Compatibility considerations

- Widening the JSON alternation keeps every existing JSON test green; the `*`→`+` change only
  affects empty values (no test pins them; verified 20261102).
- `_mask_secrets` and `SECRET_PATTERNS` names stay exported; four importers
  (`startup_mcp_starter.py`, `http_lifecycle_errors.py`, `http_lifecycle_health_checker.py`,
  `shared/retry_helper.py`) untouched (AC-5).
- Import contract: `agent → agent` only; no new cross-layer edge (Plan Step 3 baseline:
  `lint-imports` 6 kept).

## Security considerations

- Fail-closed: the 16-char minimum disappears from the guard side (masker has no minimum), so
  short secrets like `password=hunter2` are now masked/refused; recorded consequence for
  uncaught-`RuntimeError` callers is UNK-03 (owner follow-up, out of this row).
- Accepted over-masking: `scheme://user:x@host` examples in error text are masked (Plan Risks 3);
  negative test for plain URLs without userinfo lives in row 03.

## Rollback considerations

- Revert the single commit. Row 02's guard depends on this row; revert order must be 02 then 01
  if both have landed.

## Validation plan

- `uv run pytest tests/agent/test_secrets_masker.py` — green only after row 03's additions land
  (Plan Phase 1 red-first).
- `uv run ruff format`, `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/ -c pyproject.toml`,
  `uv run python tools/check_module_size.py`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`
  per `rules/toolchain.md`; `uv run lint-imports` (6 contracts kept).

## Completion criteria

- `detects_secrets` (new) returns True for every AC-3 shape and False for every AC-4 exemption shape;
  `_mask_secrets` masks the new shapes with no part of the secret left and stays idempotent;
  signature and call sites unchanged in `git diff`.

## Out of Scope

- `diagnostic_store.py` consolidation (row 02); tests (rows 03-04); docs (rows 05-06);
  UNK-03 caller-`RuntimeError` handling (recorded owner follow-up).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_KEY_ALT` (new) and `detects_secrets` (new); widen JSON pattern; append new patterns | Completed | 20261102-164252 | — | After secmask001 and row 03's red tests land Adversarial verification done 20261102: composite-key _KEY_ALT fix, Digest scheme lookahead, empty-value correction masked_shapes 14 patterns, _KEY_ALT const, detects_secrets added; red phase 17 failed/43 passed resolved; 60 masker tests green; full suite 11276 passed; ruff/mypy/bandit exit 0; diff-cover 100% |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format/check, mypy, bandit -ll -r scripts/, lint-imports (6 kept), check_module_size, full suite 11276 passed/8 skipped, diff-cover 100%, docs checkers exit 0 |

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
- **Requirement ID**: REQ-001 (shared detection function), REQ-003 (new coverage), REQ-005 (log masking with extended set)
- **Source issue**: issues/20261003-180341_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140448_diagmask001_diagnostic-guard-is-incomplete-secret-allowlist.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132614
- **Related target files**: scripts/agent/secrets_masker.py