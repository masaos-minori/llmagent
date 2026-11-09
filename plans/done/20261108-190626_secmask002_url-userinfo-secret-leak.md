## Goal
- Extend `scripts/agent/secrets_masker.py` so that a bare-password URL userinfo (`scheme://token@host`, userinfo containing only a credential with no `username:` prefix) is masked the same way the colon-separated form (`scheme://user:password@host`) already is, closing a secret-leak path into MCP subprocess failure reports and logs. The public `_mask_secrets(text: str) -> str` signature and every call site stay unchanged.

## Priority
High

## Scope
- **In-Scope**: Generalize the existing URL-credential pattern in `scripts/agent/secrets_masker.py` so the `username:` segment is optional; add a unit test covering the bare-password form; update the operator-facing secret-masking doc sentence that enumerates URL masking shapes.
- **Out-of-Scope**: Any change to the `_mask_secrets(text: str) -> str` signature or to a call site (`http_lifecycle.py`, `http_lifecycle_errors.py`, `shared/retry_helper.py`, and others); modifying any of the other 13 patterns; adding a new pattern entry; touching non-URL masking shapes.
- **Dependencies**: `N/A: none`
  - Sequencing note: no dependency on loopguard02; both are independent additive changes.

## Background
`_mask_secrets` centralizes secret redaction for the agent's log output and MCP subprocess failure reports. Per `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` ("Secret Masking in MCP Subprocess Failure Reports"), masking covers several case-insensitive shapes, including credentials embedded in URLs: currently only the colon form `scheme://user:password@host` is masked (only the password between `:` and `@`, username preserved).

## Problem
The single URL pattern requires a trailing `:` inside the userinfo segment:
```python
re.compile(r"(?i)([a-z][a-z0-9+.-]*://[^/\s:@]+:)([^/\s@]+)(?=@)")
```
A bare-password URL `scheme://token@host` (userinfo is a lone credential, no `username:` prefix) does not match, so the credential is written verbatim into failure reports/logs. Empirically verified against current HEAD:
- `endpoint=https://user:supersecret@api.example.com/path` -> masked ✓
- `endpoint=https://MYBEARTOKENEXAMPLETOKEN@api.example.com/path` -> **not masked (leak)** ✗
- `raw=https://RAWJWTTOKENEXAMPLEABC123@svc.io/x` -> **not masked (leak)** ✗
- `Bearer` / `password=key` / plain URLs / email addresses behave correctly (unchanged).

## Reason for Change
Secrets embedded as bare-password userinfo leak into masked log/stderr output. Decoupling the "is there userinfo" question from "is there a username prefix" removes the leak without altering any other shape.

## Implementation Intent
Make the `username:` prefix of the existing URL pattern optional while keeping the scheme anchor and the `(?=@)` lookahead. Concretely, wrap the `[^/\s:@]+:` username+colon group in an optional non-capturing group so the pattern matches both `scheme://user:pw@` and `scheme://pw@`. Because the replacement is `lambda m: m.group(1) + "***MASKED***"` and group 1 becomes `scheme://` (+ optional `username:`), the masked output is identical for the colon form and correct for the bare form. Do not add a second pattern entry; keep the inventory at 14.

## Requirements
- `REQ-001`: A bare-password URL (`scheme://<credential>@host`) has its credential masked to `scheme://***MASKED***@host`.
- `REQ-002`: The colon form (`scheme://user:<password>@host`) still masks only the password and preserves the username.
- `REQ-003`: A plain URL without userinfo and an email address are returned unchanged (no false positive introduced by the optional group).
- `REQ-004`: `_mask_secrets(text: str) -> str` signature and every existing call site are unchanged.
- `REQ-005`: The `SECRET_PATTERNS` inventory stays at 14 (in-place generalization, no new entry).

## Implementation Target Files
**Freeze status**: Frozen (Implementation Target Files Validation passed all rows `Verified`; Step 8 complete).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/secrets_masker.py` | Modify | Make the `username:` segment of the URL pattern (line 38) optional; keep pattern count at 14 | REQ-001, REQ-002, REQ-005 | `scripts/agent/secrets_masker.py:38` current `r"(?i)([a-z][a-z0-9+.-]*://[^/\s:@]+:)([^/\s@]+)(?=@)"`; verified candidate `r"(?i)([a-z][a-z0-9+.-]*://(?:[^/\s:@]+:)?)([^/\s@]+)(?=@)"` masks both forms and leaves plain URLs/emails unchanged | `tests/agent/test_secrets_masker.py::TestColonFormMasking::test_url_credential_masked` (extend) | Verified |
| `tests/agent/test_secrets_masker.py` | Add | Add a parametrized case / method asserting the bare-password form is masked and the colon form is preserved | REQ-001, REQ-002 | `tests/agent/test_secrets_masker.py:258` existing `test_url_credential_masked` | REQ-001, REQ-002 | Verified |
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Modify | Update the URL-masking sentence (line 96) to state bare-password userinfo is also masked | REQ-001 | `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md:96` currently documents only `scheme://user:password@host` | REQ-001 | Verified |

Rules: one row per file; the doc row is recorded separately from the source rows per the freeze rules.

## Reference Files
Files that must be read to implement the targets but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/shared/retry_helper.py` | Direct caller of `_mask_secrets`; confirm the `.sub()` replacement contract (`m.group(1) + "***MASKED***"`) holds under the generalized pattern (caller safety) | `scripts/agent/secrets_masker.py` (REQ-004) |

## Acceptance Criteria
- `REQ-001`: `_mask_secrets("x=https://LONECRED@h/p")` yields `x=https://***MASKED***@h/p`; the raw credential substring is absent from the output.
- `REQ-002`: `_mask_secrets("postgres://admin:s3cr3tpw@db:5432/x")` still equals `postgres://admin:***MASKED***@db:5432/x`.
- `REQ-003`: `_mask_secrets("https://example.com/api/items")` and an email string are returned unchanged.
- `REQ-004`: No signature or call-site diff for `_mask_secrets`; `git diff` shows only the regex literal on line 38 plus test/doc additions.
- `REQ-005`: `assert len(SECRET_PATTERNS) == 14` still passes.

## Tests
- Extend `TestColonFormMasking::test_url_credential_masked` (or add `test_bare_password_url_masked`) to parametrize both the colon and bare-password forms, referencing REQ-001/REQ-002.
- Keep `test_pattern_count_matches_inventory` (REQ-006-equivalent, `== 14`) green, referencing REQ-005.
- Regression sweep: run the full `tests/agent/test_secrets_masker.py` plus callers to confirm no false positives.

## Documentation Impact
- `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` line 96 enumerates the URL-masking shape as `scheme://user:password@host`; update it to also cover `scheme://token@host` (bare-password). Driven by REQ-001. Name resolved via `docs/00_index.md` "Document References by Task" mapping (do not hardcode the filename downstream).

## Assumptions
- The replacement lambda keeps `group(1)` intact; making the username+colon optional only widens what matches, it does not change the masked token.
- No other pattern in `SECRET_PATTERNS` also matches bare-password URLs and would double-mask; verified only line 38 matches URL userinfo.
- `detects_secrets()` (which compares masked vs. original) will now report `True` for bare-password URLs, consistent with the leak being closed.
- Adversarial verification (plan-to-implementation-procedure, 2026-11-08), reproduced against the candidate pattern:
  - A bare userinfo cannot be told apart from a username-only one, so `ssh://git@github.com/o/r.git`, `https://user@host/x` and `ftp://anon@host/f` are masked too (`ssh://***MASKED***@github.com/...`). This is an accepted over-mask; the repository already redacts every userinfo in `scripts/mcp_servers/git/repository_state.py::_redact_remote_url` (`://[^@/]+@`).
  - `redis://:pw@host:6379/0` (empty username) leaked before and is now masked (`redis://***MASKED***@host:6379/0`).
  - Real consumer of `detects_secrets()`: `scripts/agent/diagnostic_store.py:164` raises `RuntimeError` (contained to a warning by diagstore001) when diagnostic content has a secret and no encryption key is set. Diagnostic content holding a bare-userinfo URL, including `ssh://git@...`, is now refused in that mode. Accepted; no change to that module (not a target file).
  - The masker output is idempotent for the bare form (`https://***MASKED***@h/p` re-masks to itself).
  - Pre-existing and unchanged by this plan: the pattern scan is quadratic on long input with a scheme prefix and no `@` (about 2.1 s for 16 000 chars, identical for the old and new pattern). Follow-up issue candidate, out of scope here.
  - `docs/.../agent_10_01` line 96 says "only the password ... is masked, the username is preserved"; that stays true for the colon form only, so the doc edit must scope that clause to the colon form.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any production config or fixture embeds a bare-password URL that a new test fixture should pin | None required; behavior is deterministic from the regex | Covered by the added parametrized test | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor` columns.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/secrets_masker.py` | One regex literal generalized (optional username group) | Low: affects only URL-credential masking path used by logs + MCP subprocess failure reports | Low | High (single owner) | None: no new module; `deploy.sh` unaffected |

## Design
- Current pattern (line 38): `(?i)([a-z][a-z0-9+.-]*://[^/\s:@]+:)([^/\s@]+)(?=@)`. The first group requires `scheme://username:`; the second captures the password; `(?=@)` requires an `@` after.
- Generalized pattern: `(?i)([a-z][a-z0-9+.-]*://(?:[^/\s:@]+:)?)([^/\s@]+)(?=@)`. The `(?:[^/\s:@]+:)?` makes the `username:` part optional. Group 1 is now `scheme://` or `scheme://username:`; group 2 is the credential. The shared replacement `m.group(1) + "***MASKED***"` preserves the scheme (+ optional username) and masks the credential.
- Verified candidate behavior (all pass): bare-password masked; colon form preserved; `postgres://admin:s3cr3tpw@db:5432/x` -> `postgres://admin:***MASKED***@db:5432/x`; plain URL and email unchanged.
- In-place change keeps `SECRET_PATTERNS` length at 14, so the pinned count assertion needs no edit.

## Implementation steps
1. **Phase 1: Core Logic Implementation**
   - [ ] Replace the line-38 URL pattern in `scripts/agent/secrets_masker.py` with the optional-username variant (REQ-001, REQ-002, REQ-005).
2. **Phase 2: Tests**
   - [ ] Add bare-password coverage to `tests/agent/test_secrets_masker.py` and confirm `test_pattern_count_matches_inventory` stays green (REQ-001, REQ-002, REQ-005).
3. **Phase 3: Documentation & Verification**
   - [ ] Update the URL-masking sentence in `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` (REQ-001).
   - [ ] Run `tests/agent/test_secrets_masker.py` and a caller sweep; confirm no false positives and pattern count == 14 (REQ-003, REQ-004).

### Release units
N/A: no release unit.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/secrets_masker.py` | Unit: parametrize colon + bare-password forms; plain-URL/email negative cases | `uv run pytest tests/agent/test_secrets_masker.py` | All pass; `len(SECRET_PATTERNS) == 14` |
| Callers (`http_lifecycle*.py`, `shared/retry_helper.py`) | Integration: confirm masked output unchanged for non-URL secrets | `uv run pytest tests/agent` (subset) | No regressions |

## Risks
- **Risk**: The optional group could over-match a scheme-like token followed by `@` in prose. → **Mitigation**: the mandatory `scheme://` anchor and `(?=@)` lookahead restrict matches to real URL userinfo; verified no match on `user@example.com` / `a_b@domain.org`.
- **Risk**: Username-only userinfo (`ssh://git@host`) is now masked, and `diagnostic_store` refuses such content when no encryption key is set. → **Mitigation**: accepted over-mask consistent with `_redact_remote_url`; pinned by a test so the behavior is intentional (Phase 2).
- **Risk**: A second pattern already covers bare-password URLs, causing a redundant re-mask. → **Mitigation**: confirmed only line 38 matches URL userinfo; idempotence test in `test_extended_idempotence` covers this.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Core Logic Implementation (optional-username URL regex) | Completed | 20261109-101933 | 20261109-101933 | Procedure generated 2026-11-08: implementations/20261108-195603_1_ |
| 2 | Phase 2: Tests (bare, username-only, negative, idempotence) | Completed | 20261109-101933 | 20261109-101933 | Procedure generated: _2_ |
| 3 | Phase 3: Documentation & Verification | Completed | 20261109-101933 | 20261109-101933 | Doc procedure generated: _3_; the final suite and caller sweep are carried out by code-implementation |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261108-195603_1_scripts_agent_secrets_masker.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261108-195603_2_tests_agent_test_secrets_masker.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261108-195603_3_docs_23_agent_agent_10_01_operations-and-observability-startup-and-health.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261107-191650_secmask002_url-userinfo-secret-leak.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-190626
- **Related target files**: `scripts/agent/secrets_masker.py`, `tests/agent/test_secrets_masker.py`, `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem (leak evidence, verified at HEAD) | `scripts/agent/secrets_masker.py` | Phase 1 | REQ-001 | `test_bare_password_url_masked` (new) | Confirmed by repository evidence |
| REQ-001 | Problem (leak evidence) | `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Phase 3 | REQ-001 | doc sentence update | Confirmed by repository evidence |
| REQ-002 | Background | `scripts/agent/secrets_masker.py` | Phase 1 | REQ-002 | `test_url_credential_masked` (extended) | Confirmed by repository evidence |
| REQ-003 | Problem (no false positive) | `scripts/agent/secrets_masker.py` | Phase 1 | REQ-003 | plain-URL/email negative case | Confirmed by repository evidence |
| REQ-004 | Summary (signature/call-site unchanged) | `scripts/agent/secrets_masker.py` | Phase 1 | REQ-004 | `git diff` shows only line-38 regex + test/doc | Explicit in issue |
| REQ-004 | Summary (call-site unchanged) | `scripts/agent/shared/retry_helper.py` | Phase 3 | REQ-004 | caller sweep | Explicit in issue |
| REQ-005 | Implementation Intent (keep inventory at 14) | `scripts/agent/secrets_masker.py` | Phase 1 | REQ-005 | `test_pattern_count_matches_inventory` | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261108-195603 -->