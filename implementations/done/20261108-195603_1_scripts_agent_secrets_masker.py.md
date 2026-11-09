## Goal
Mask a bare-password URL userinfo (`scheme://token@host`) like the colon form (REQ-001), keep the colon form, plain URLs and emails unchanged (REQ-002, REQ-003), keep the pattern inventory at 14 (REQ-005) and the public signature unchanged (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit
- The last `SECRET_PATTERNS` entry (URL userinfo) only.

## Assumptions
- Reproduced against the candidate pattern: bare form masked; colon form `postgres://admin:s3cr3tpw@db:5432/x` -> `postgres://admin:***MASKED***@db:5432/x`; `https://example.com:8080/a?e=a@b.co` and `a@b.com` unchanged; output idempotent.
- Accepted over-mask (Plan Assumptions): username-only userinfo such as `ssh://git@github.com/o/r.git` is masked, matching `_redact_remote_url` in `scripts/mcp_servers/git/repository_state.py`.
- Overlap check: no finding names this Plan.

## Design decisions
- Make `username:` optional with a non-capturing group so the shared replacement `m.group(1) + "***MASKED***"` keeps `scheme://` plus an optional username.
- No second pattern: inventory stays 14.

## Alternatives considered
N/A: a second pattern was rejected by the Plan (REQ-005); both would match the colon form and double-process it.

## Implementation
### Target file
`scripts/agent/secrets_masker.py`

### Procedure
1. Replace the last `SECRET_PATTERNS` entry `re.compile(r"(?i)([a-z][a-z0-9+.-]*://[^/\s:@]+:)([^/\s@]+)(?=@)")` with `re.compile(r"(?i)([a-z][a-z0-9+.-]*://(?:[^/\s:@]+:)?)([^/\s@]+)(?=@)")`.

### Method
Edit the single regex literal; leave `_mask_secrets`, `detects_secrets` and the other 13 patterns untouched.

### Details
- Group 1 becomes `scheme://` or `scheme://username:`; group 2 is the credential; `(?=@)` is kept.
- `scripts/agent/shared/retry_helper.py` and the other callers only call `_mask_secrets(text)`; no call-site change.
- `scripts/agent/diagnostic_store.py::DiagnosticStore.save` uses `detects_secrets`; it will now also refuse bare-userinfo URLs without an encryption key (accepted, see Assumptions).

## Compatibility considerations
Wider masking only; the colon-form output is byte-identical. `detects_secrets` returns True for more inputs (bare userinfo); diagnostic save without encryption refuses them.

## Security considerations
Closes a leak of bare credentials in MCP subprocess failure reports and logs. The known over-mask is the safe direction.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_secrets_masker.py tests/agent/test_diagnostic_store_security.py -q`
- `uv run pytest tests/agent -q -k "masker or retry_helper or http_lifecycle"`

## Completion criteria
- `_mask_secrets("x=https://LONECRED@h/p") == "x=https://***MASKED***@h/p"`.
- Colon form, plain URL and email behave as before; `len(SECRET_PATTERNS) == 14`; `git diff` of this file shows only the regex literal.

## Out of Scope
Signature and call sites, the other 13 patterns, the pre-existing quadratic scan on long no-`@` input (follow-up candidate), `diagnostic_store.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the URL userinfo regex literal | Completed | 20261109-101933 | 20261109-101933 |  |
| 2 | Add or extend tests (`test_secrets_masker.py` procedure) | Completed | 20261109-101933 | 20261109-101933 | Must land with step 1 delivered by 195603_2; landed with step 1 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-101933 | 20261109-101933 | targeted+gates pass; full suite after 195603_3 docs cycle full suite 11955 passed; diff-cover gate pass |

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
- **Requirement ID**: `REQ-001` (bare credential masked), `REQ-002` (colon form preserved), `REQ-003` (no false positive for plain URL/email), `REQ-004` (signature unchanged), `REQ-005` (inventory stays 14)
- **Source issue**: `issues/20261107-191650_secmask002_url-userinfo-secret-leak.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-190626_secmask002_url-userinfo-secret-leak.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-195603
- **Related target files**: `scripts/agent/secrets_masker.py`