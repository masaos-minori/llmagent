# `mask_args` content-scrub tests

## Goal

Add direct unit tests for the new content scrub in `mask_args()` to
`tests/agent/test_tool_result_formatter.py`, pinning depth coverage, key-based precedence,
non-mutation, idempotence and performance (Plan REQ-001 / AC-1..AC-4, REQ-002 / AC-2).

## Scope

- New class `TestMaskArgsContentScrub` (new) after `TestMaskArgs`.
- `TestMaskArgs` and `TestMaskArgsDefaultConfig` untouched: they are the AC-6 key-based regression.
- No fixture changes; the file already imports `mask_args` and `AgentConfig`-shaped config mocks.

## Assumptions

- Verified 20261102: classes `TestMaskArgsDefaultConfig` (:55) and `TestMaskArgs` (:76) exist with
  the depth/non-string cases; no test asserts scrubbing of secret-shaped substrings under unlisted
  keys — those are the red-first cases here (Plan Phase 1).
- Tests written before row 01 lands and MUST fail red until it does.
- Secret shapes used are ones the post-secmask001 masker covers (`key=value` and colon forms);
  secmask001 lands before this Plan (Plan UNK-01), so these expectations are valid at execution.

## Design decisions

- Assert absence-of-secret in the returned structure rather than exact masked strings where the
  value also contains non-secret prose — pins AC-1 without freezing masker output shapes.
- Precedence test asserts the exact value `"***"` under a `masked_fields` key (AC-2), not a
  contains-not check: the key-based replacement must remain byte-identical.

## Alternatives considered

- Parametrize into `TestMaskArgs` — rejected: that class pins pre-existing key-based behavior
  (AC-6); a new class keeps the new contract separable for triage.

## Implementation
### Target file
`tests/agent/test_tool_result_formatter.py`

### Procedure
Append `TestMaskArgsContentScrub` (new) after `TestMaskArgs` (before `TestBuildPreview`).

### Method
New tests calling `mask_args` directly:
- `test_scrubs_secret_in_free_form_string` (new): `{"command": "export API_KEY=abcd1234 && run"}`
  with `masked_fields=[]` → output contains no `abcd1234` (AC-1).
- `test_scrubs_at_depth` (new): nested dict and list items, e.g.
  `{"headers": {"Authorization": "Bearer abc12345678"}, "items": [{"note": "token=xyz789"}]}` →
  neither secret survives (REQ-001 "any depth").
- `test_key_based_masking_takes_precedence` (new): `masked_fields=["token"]`,
  `{"token": "abc12345678"}` → value is exactly `"***"`, and a sibling key carrying the same
  value is scrubbed by content (AC-2).
- `test_non_string_values_untouched` (new): ints, bools, None under unlisted keys round-trip
  unchanged (REQ-001).
- `test_input_not_mutated` (new): deep-copy compare the input dict before/after the call (AC-3).
- `test_idempotent` (new): `mask_args(mask_args(a, f), f) == mask_args(a, f)` (AC-4).
- `test_no_secret_string_unchanged` (new): ordinary prose returns identical.
- `test_large_string_terminates` (new): a 100 000-char value under an unlisted key completes in
  bounded time — assert completion, not duration (Plan Performance note).

### Details
- Keep the module's existing import style (module-level `from agent.tool_result_formatter import
  mask_args` already present).

## Compatibility considerations

- N/A: tests only; row 01's behavior change is what these tests gate.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_result_formatter.py` — red for the new class until row 01
  lands, then green.
- `uv run ruff format`, `uv run ruff check` on the touched file; coverage via
  `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`.

## Completion criteria

- All new tests pass with row 01 applied; every pre-existing test in the module passes unchanged.

## Out of Scope

- Sink-level assertions (rows 03-04); approval preview (out of the Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestMaskArgsContentScrub` (new) tests (red before row 01 lands) | Completed | 20261102-173426 | 20261102-180004 | Plan Phase 1 red-phase evidence: 3 failed / 44 passed vs pre-scrub code (Plan Phase 1); ruff clean landed in batch 20261102-132615; red-first verified, all targets green |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261102-173830 | 20261102-180004 | green gate deferred to row 01 implementation landing full suite 11348 passed/8 skipped; diff-cover 100%; ruff/mypy/bandit/lint-imports/check_module_size green; docs checkers green |

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
- **Requirement ID**: REQ-001 (content scrub at any depth), REQ-002 (key-based precedence)
- **Source issue**: issues/20261003-180335_maskargs001_audit-masking-misses-free-form-secrets.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-140856_maskargs001_audit-masking-misses-free-form-secrets.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-132615
- **Related target files**: tests/agent/test_tool_result_formatter.py