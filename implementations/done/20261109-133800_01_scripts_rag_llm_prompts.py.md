## Goal

Make `_parse_mqe_response` normalize, deduplicate, and cap the model's paraphrases: strip, case-insensitive dedup against each other and the original query, drop whitespace-only entries, keep the original query first, and cap paraphrases at an optional limit (`REQ-001`: normalize and dedup; `REQ-002`: cap; `REQ-004`: backward-compatible signature).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_parse_mqe_response` and one new private helper in `scripts/rag/llm_prompts.py`.
- Out of scope: prompt wording and template contract (`_mqe_prompt`), RRF, any config key.

## Assumptions

- Re-verified at generation time: `_parse_mqe_response(raw, original_query)` returns `MqeParseResult(queries=[original_query] + valid)` where `valid` keeps every non-empty string with no normalization, dedup, or cap; its only production caller is `RagLLM.expand_queries` in `scripts/rag/llm_client.py`, and no test calls it directly (`rg "_parse_mqe_response" scripts tests`).
- `mqe_n_queries` is the number of paraphrases (the prompt asks for that many), so the total cap is `mqe_n_queries + 1`.
- A limit of zero or below is clamped to zero paraphrases (Plan Assumptions, Step 3a correction); `None` means unbounded.
- Sibling Plan ragrev001 (`implementations/20261109-104259_01_scripts_rag_llm_client.py.md`) edits only `expand_queries` in `scripts/rag/llm_client.py`; it does not touch this file, so there is no ordering constraint here.

## Design decisions

- Add an optional keyword `max_paraphrases` (new) with default `None` so the existing two-argument call keeps its shape (`REQ-004`).
- Put normalization in a small private helper `_normalize_paraphrases` (new) so `_parse_mqe_response` stays at complexity grade B.

## Alternatives considered

- Cap and dedup in `MqeStage`: rejected; the parser owns validation of the model output and the stage would need config-aware dedup.

## Implementation
### Target file
`scripts/rag/llm_prompts.py`

### Procedure
1. Add `_normalize_paraphrases(candidates: list[object], original_query: str, max_paraphrases: int | None) -> list[str]` (new) above `_parse_mqe_response`: iterate in order, keep only `str` entries, strip each, skip empty results, skip a key (`casefold()` of the stripped text) already seen, seed the seen set with the stripped, case-folded original query, keep the first spelling, and stop once `max(0, max_paraphrases)` entries are kept when a limit is given.
2. Add the keyword parameter `max_paraphrases: int | None = None` (new) to `_parse_mqe_response`, replace the `valid = [...]` comprehension with a call to the helper, and return `MqeParseResult(queries=[original_query] + valid)` as before.
3. Update the `_parse_mqe_response` docstring (normalization, dedup, cap) and keep the `MqeParseError` raising paths untouched.

### Method
- The dedup key is `casefold()`; the stored value is the stripped original spelling.
- The `logger.info("MQE: ...")` count reports the paraphrases kept after normalization.

### Details
- Do not change `_mqe_prompt`, `MqeParseResult`, or the `__all__` export list (`_parse_mqe_response` is already exported).
- Locate code by symbol name; line numbers drift if sibling procedures run first.

## Compatibility considerations

- Calling `_parse_mqe_response(raw, query)` without the new argument keeps the output shape `[original] + paraphrases`, now deduplicated (`REQ-004`).
- Behavior change: duplicate, padded, or whitespace-only model output no longer reaches `ctx.queries`; this is the intended fix.

## Security considerations

N/A: pure string normalization of model output; no new I/O or trust boundary.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_rag_stages.py tests/rag/test_llm_client_timeout.py -q` (new parse tests from the tests procedure fail on HEAD, pass after).
- `uv run ruff check scripts/rag/llm_prompts.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit scripts/rag/llm_prompts.py`.
- `uv run radon cc scripts/rag/llm_prompts.py -s -n C` and `uv run python tools/check_module_size.py`.

## Completion criteria

- Padded, mixed-case, and repeated paraphrases, and ones equal to the original query, appear at most once and never as a duplicate of the original; whitespace-only entries are dropped.
- With a limit of N the result has at most N paraphrases; without a limit the shape is unchanged.
- ruff, mypy, bandit, and complexity checks are clean.

## Out of Scope

- `scripts/rag/llm_client.py`, `scripts/rag/stages/search.py`, tests, and docs (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_normalize_paraphrases` (new) and the optional limit to `_parse_mqe_response` | Completed | 20261109-151852 | 20261109-155642 | changed: scripts/rag/llm_prompts.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-151852 | 20261109-155642 | ruff/mypy/bandit/lint-imports/radon/check_module_size pass; full suite 12029 passed; diff-cover 100% measured at batch end after tests procedure landed |

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
- **Requirement ID**: `REQ-001` (normalize and dedup), `REQ-002` (cap), `REQ-004` (backward-compatible helper)
- **Source issue**: issues/20261108-131120_ragrev007_mqe-queries-uncapped-duplicated.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165229_ragrev007_mqe-queries-uncapped-duplicated.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-133800
- **Related target files**: `scripts/rag/llm_prompts.py`