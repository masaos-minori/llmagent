## Goal

Add a unit test to `tests/shared/test_config_validator.py` asserting that `RagConfigValidator.validate`
rejects a non-string `mqe_prompt_template` or `rerank_prompt_template` with `ok=False` and a message
naming the key (T1 / REQ-001 / AC-1).

## Scope

- **In-Scope**: add a unit test in `TestRagConfigValidator` covering a non-string template for each
  of `mqe_prompt_template` and `rerank_prompt_template`; confirm the error names the key and
  `ok=False`.
- **Out-of-Scope**: changing the validator's behavior; adding tests for other RAG fields; any
  `docs/*.md` change.

## Assumptions

- Tests exercise `RagConfigValidator.validate` directly against flat dicts, matching the existing
  `TestRagConfigValidator` conventions (`setup_method`, `self.validator`).
- The new test supplies valid values for the *other* template key so only the key under test is
  exercised in isolation.
- Per the doc-1 Plan Gap, the validator flags present-but-wrong-type values (approach (a)); the test
  therefore passes a non-string value for one key while supplying a valid string for the other.

## Design decisions

- Follow the existing `TestRagConfigValidator` patterns (flat-dict inputs, `result.ok` /
  `result.errors` assertions) so the new test fits the suite.
- One test per key so each template is independently covered.

## Alternatives considered

N/A: mirroring existing test patterns is the lowest-risk approach.

## Implementation

### Target file

`tests/shared/test_config_validator.py`

### Procedure

1. In `TestRagConfigValidator`, add `test_non_string_mqe_prompt_template_rejected`:
   ```python
       def test_non_string_mqe_prompt_template_rejected(self) -> None:
           result = self.validator.validate(
               {
                   "mqe_prompt_template": 123,
                   "rerank_prompt_template": "Rerank results for: {query}",
               }
           )
           assert result.ok is False
           assert len(result.errors) == 1
           assert "mqe_prompt_template" in result.errors[0]
   ```
2. Add `test_non_string_rerank_prompt_template_rejected` symmetrically, passing a valid
   `mqe_prompt_template` and a non-string `rerank_prompt_template`, asserting the error names
   `rerank_prompt_template`.
3. Confirm the existing tests still pass, including `test_ok_no_errors` and `test_no_rag_key`
   (which validate `{}` and expect `ok is True`) — these remain green under approach (a).
4. Run the affected test target and confirm clean. (T1)

### Method

- **Isolate the key under test.** Supply a valid string for the sibling template so exactly one key
  is non-string; assert exactly one error naming that key.
- **Assert the contract.** `result.ok is False`, exactly one error, and the error contains the
  offending key name (actionable failure).
- **Preserve existing coverage.** Do not modify `test_ok_no_errors` / `test_no_rag_key` under
  approach (a); they still validate `{}` and expect no errors.

### Details

- `REQ-001`: a non-string template yields `ok=False` and a message naming the key.
- **UNK-01:** not blocking; the single production construction site of `RagConfigImpl` is
  `resolve_rag_config`, which validates before construction.

## Compatibility considerations

Test-only change; does not affect production code or the CI exit contract. No `docs/*.md` change.

## Security considerations

N/A.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_config_validator.py` | Unit: non-string template rejected, key named, `ok=False` | `uv run pytest tests/shared/test_config_validator.py` | New tests pass; existing tests (incl. `test_ok_no_errors`) still pass |

## Completion criteria

- A test each asserting a non-string `mqe_prompt_template` and `rerank_prompt_template` yields
  `ok=False` with a message naming the key (T1).
- The existing `TestRagConfigValidator` suites pass unchanged.

## Out of scope

Changing the validator's behavior, adding tests for other RAG fields, and any `docs/*.md` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Add prompt-template type validation to `RagConfigValidator.validate` | Completed | — | — | REQ-001; AC-1, AC-3 |
| 2 | Phase 2: Add unit + integration tests | Completed | — | — | REQ-001/002; T1/T2 |
| 3 | Phase 3: Run ruff / mypy / bandit / affected tests | Completed | — | — | all REQs |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/20261018-193310_rag001_rag-prompt-templates-are-not-type-validated-at-config-load-so-the-pipeline-crashes-with-typeerror.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-220244_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-073608
- **Related target files**: tests/shared/test_config_validator.py