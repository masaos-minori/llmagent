# Fix regex parsing vulnerabilities in MQE and rerank score extraction

## Priority
Medium

## Summary
Replace overly permissive regex patterns in `_parse_mqe_response()` and `_apply_rerank_scores()` with precise patterns that match only innermost bracket/brace pairs. Current `\[\d.*\d\]` and `\{\d.*\d\}` patterns with `re.DOTALL` can match across multiple JSON structures, causing silent degradation when LLM outputs contain nested brackets or braces.

## Background
Both functions use `re.search()` with `re.DOTALL` to find JSON arrays/objects in raw LLM output. The DOTALL flag makes `.` match newlines, allowing the regex to span across multiple bracket/brace pairs. This was likely intended to handle multi-line LLM responses but creates false positives.

## Problem
When the LLM outputs text containing brackets or braces outside the JSON data, the regex matches incorrectly:
- MQE: `[Query 1: What is X?]\n[Query 2: How does Y work?]` matches as one pair → JSON parse fails → fallback to original query without expansion
- Rerank: `{1: 5.0}\n{2: 3.0}` matches as one pair → JSON parse fails → fallback to RRF order without reranking

While these cases trigger fallback (safe behavior), they silently degrade retrieval quality. An attacker who controls the LLM could craft responses that bypass MQE expansion or reranking entirely.

## Reason for Change
The regex patterns should extract only the JSON structure, ignoring surrounding text. Using `\[\d.*\d\]` with DOTALL is fundamentally broken for nested content. The fix uses `\[[^\]]*\]` and `\{[^{}]*\}` which match only innermost pairs.

## Implementation Intent
1. In `_parse_mqe_response()` (llm_prompts.py:148): Replace `r"\[\d.*\d\]"` with `r"\[[^\]]*\]"` to match only the innermost bracket pair
2. In `_apply_rerank_scores()` (llm_prompts.py:189): Replace `r"\{\d.*\d\}"` with `r"\{[^{}]*\}"` to match only the innermost brace pair
3. If neither pattern finds a match, return None/fallback as currently done
4. No behavioral change for well-formed LLM responses; improved robustness for adversarial inputs

## Target Files or Areas
- scripts/rag/llm_prompts.py

## Required Changes
- Replace regex in `_parse_mqe_response()` line ~148: `r"\[\d.*\d\]"` → `r"\[[^\]]*\]"`
- Replace regex in `_apply_rerank_scores()` line ~189: `r"\{\d.*\d\}"` → `r"\{[^{}]*\}"`
- Remove `re.DOTALL` flag from both calls since it's no longer needed
- Update docstrings if they reference the current regex behavior

## Constraints
- Must preserve existing fallback behavior when no JSON is found
- Must not break existing tests that rely on current regex behavior
- The new patterns will NOT match multi-line JSON spanning multiple lines — callers must ensure JSON is on a single line or use a different approach

## Acceptance Criteria
- MQE regex extracts only the first valid JSON array from mixed content
- Rerank regex extracts only the first valid JSON object from mixed content
- Multi-line JSON arrays/objects are handled correctly (single-line format expected)
- Existing tests pass after changes
- Adversarial inputs with nested brackets/braces do not cause incorrect matches

## Testing Expectations
- Add test for `_parse_mqe_response()` with LLM output containing brackets outside JSON
- Add test for `_apply_rerank_scores()` with LLM output containing braces outside JSON
- Verify existing test cases still pass
- Run: pytest tests/rag/test_rag_pipeline.py -k mqe

## Documentation Impact
Update docstrings in `_parse_mqe_response()` and `_apply_rerank_scores()` to clarify that JSON must be on a single line or within a single bracket/brace pair.

## Out of Scope
- Support for multi-line JSON extraction (would require a proper JSON parser approach)
- Changes to how fallback is triggered when JSON is not found
- Changes to the JSON parsing itself (orjson remains unchanged)

## Dependencies
N/A: none

## Unresolved Questions
Should we switch from regex-based extraction to a more robust approach using json.JSONDecoder.raw_decode() or a streaming JSON parser? This would handle multi-line JSON but adds complexity.

## AI Implementation Instruction
1. Read scripts/rag/llm_prompts.py
2. At line ~148, change `m = re.search(r"\[\d.*\d\]", raw, re.DOTALL)` to `m = re.search(r"\[[^\]]*\]", raw)`
3. At line ~189, change `m = re.search(r"\{\d.*\d\}", raw, re.DOTALL)` to `m = re.search(r"\{[^{}]*\}", raw)`
4. Do NOT add any additional logic — just replace the regex patterns
5. Run pytest tests/rag/test_rag_pipeline.py to verify existing tests pass
6. If any tests fail due to multi-line JSON expectations, note them for separate handling

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/llm_prompts.py
