## Goal
Pin the bare-password masking and the unchanged colon form, plain URL and email (REQ-001, REQ-002), including the intentional over-mask of username-only userinfo.

## Scope
**Release unit**: N/A: not part of a release unit
- `TestExtendedShapeMasking` and `test_extended_idempotence` in `tests/agent/test_secrets_masker.py`.

## Assumptions
- `test_pattern_count_matches_inventory` (`== 14`) and `test_large_input_terminates` stay green unchanged.
- Depends on seq 1 of this Plan.
- `tests/agent/test_diagnostic_store_security.py` already pins the colon-form refusal; adding a bare-form refusal there is not in the frozen target list and is not required.

## Design decisions
- Add one parametrized test next to `test_url_credential_masked`; extend the idempotence samples with the bare form.

## Alternatives considered
N/A: follows the file's existing layout.

## Implementation
### Target file
`tests/agent/test_secrets_masker.py`

### Procedure
1. After `test_url_credential_masked`, add `test_bare_password_url_masked` (new), parametrized over: `("x=https://LONECRED@h/p", "x=https://***MASKED***@h/p")`, `("raw=https://RAWJWTTOKENEXAMPLEABC123@svc.io/x", "raw=https://***MASKED***@svc.io/x")`, `("redis://:pw@host:6379/0", "redis://***MASKED***@host:6379/0")`; assert the raw credential is absent (REQ-001).
2. Add `test_username_only_userinfo_is_masked` (new) asserting `ssh://git@github.com/o/r.git` becomes `ssh://***MASKED***@github.com/o/r.git`, documented as an accepted over-mask matching `_redact_remote_url`.
3. Add `test_userinfo_negative_cases` (new): `https://example.com/api/items`, `https://example.com:8080/a?e=a@b.co`, `mail a@b.com` and `a_b@domain.org` are returned unchanged (REQ-003).
4. Keep `test_url_credential_masked` as is (REQ-002) and add `"https://LONECRED@h/p"` to the `samples` list of `test_extended_idempotence`.

### Method
Use `pytest.mark.parametrize` with the pairs above; import nothing new (`pytest` and `_mask_secrets` are already imported in the module).

### Details
- Every expected string was reproduced against the candidate pattern on 2026-11-08.
- Do not assert behavior of `user:p@ss@host`; its partial masking is pre-existing and out of scope.

## Compatibility considerations
Tests only.

## Security considerations
N/A: tests only; fixtures use synthetic credentials.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_secrets_masker.py -q`; the bare-form tests must fail against the old pattern.

## Completion criteria
- New tests pass; old pattern fails the bare-form cases; the pattern-count and large-input tests stay green.

## Out of Scope
Production code, docs, `test_diagnostic_store_security.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the bare-form, username-only and negative-case tests | Completed | 20261109-101933 | 20261109-101933 |  |
| 2 | Extend the idempotence samples | Completed | 20261109-101933 | 20261109-101933 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-101933 | 20261109-101933 | targeted tests 112+254 pass; full suite after 195603_3 docs cycle |

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
- **Requirement ID**: `REQ-001` (bare credential masked), `REQ-002` (colon form preserved)
- **Source issue**: `issues/20261107-191650_secmask002_url-userinfo-secret-leak.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-190626_secmask002_url-userinfo-secret-leak.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-195603
- **Related target files**: `tests/agent/test_secrets_masker.py`