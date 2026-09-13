## Goal

Replace the greedy, `re.DOTALL`-flagged bracket/brace regex patterns in `_parse_mqe_response()` and `_apply_rerank_scores()` with non-greedy, no-nested-bracket patterns that extract only the innermost JSON structure, per REQ-001 and REQ-002.

## Scope

- In-Scope: Replacing the two regex patterns in `_parse_mqe_response()` and `_apply_rerank_scores()` (`scripts/rag/llm_prompts.py`) and removing the now-unneeded `re.DOTALL` flag from both
- Out-of-Scope: Support for multi-line/nested JSON extraction (would require a proper JSON-parser-based approach, e.g. `json.JSONDecoder.raw_decode()`); changes to how fallback is triggered when no JSON is found; changes to `orjson` parsing itself

## Assumptions

- MQE's JSON payload is a flat array of strings (no nested arrays) — confirmed by `_parse_mqe_response()`'s validation (`isinstance(q, str)` per element, line 159)
- Rerank's JSON payload is a flat object mapping string keys to numeric scores (no nested objects) — confirmed by `_apply_rerank_scores()`'s usage (`score_map.get(str(i), ...)`, line 199)
- Neither payload shape requires nested-bracket support, so the non-greedy `[^\]]`/`[^{}]` character-class restriction (which cannot match nested brackets/braces) does not affect real LLM outputs for these two use cases

## Design decisions

1. Use a character-class-exclusion pattern (`[^\]]`/`[^{}]`) rather than a fully general JSON-aware parser (e.g. `json.JSONDecoder.raw_decode()`) — the Issue's own Unresolved Questions correctly identifies the general approach as more complex; the flat-array/flat-object payload shapes here don't need it
2. Drop `re.DOTALL` from both calls — it is no longer needed once the pattern itself excludes the closing delimiter, and keeping it would not change behavior since the new patterns don't use `.` at all

Evidence grounding:
- The actual source patterns (`r"\[.*\]"` / `r"\{.*\}"`) have no digit-boundary requirement, making them even more permissive than the Issue described
- Reproduced directly: `re.search(r"\[.*\]", '[Query 1: What is X?]\n[Query 2: How does Y work?]', re.DOTALL).group()` returns `'[Query 1: What is X?]\n[Query 2: How does Y work?]'` — spanning multiple bracket pairs
- Confirmed the proposed fix pattern (`r"\[[^\]]*\]"`) both rejects the multi-bracket case above (extracts only the first `[...]`) and correctly extracts a well-formed array from realistic input (`'Here are the queries: ["query one", "query two"]'` → `["query one", "query two"]`, parses via `orjson.loads()`)

## Alternatives considered

- **Use `json.JSONDecoder.raw_decode()`**: Would provide true JSON-aware parsing but adds complexity and dependency on Python's standard library JSON module. Rejected because the flat-array/flat-object payload shapes don't need it (see Assumptions).
- **Keep existing patterns and add pre-processing**: Strip out non-JSON text before regex matching. Rejected because it adds unnecessary complexity and could break valid JSON containing bracket characters within string values.

## Implementation
### Target file
`scripts/rag/llm_prompts.py`

### Procedure
1. Replace `r"\[.*\]"`/`re.DOTALL` with `r"\[[^\]]*\]"` in `_parse_mqe_response()`
2. Replace `r"\{.*\}"`/`re.DOTALL` with `r"\{[^{}]*\}"` in `_apply_rerank_scores()`
3. Update both functions' docstrings to note the innermost-pair-only extraction
4. Run validation sequence

### Method
Inline regex pattern replacement + docstring update in `_parse_mqe_response()` and `_apply_rerank_scores()`.

### Details
1. **Phase 1: Preparation — Confirm no caller depends on current greedy-match behavior**
   a. Verify no test or caller relies on `_parse_mqe_response()`/_apply_rerank_scores()` successfully parsing multi-fragment input (this would be relying on a bug)
   
2. **Phase 2: Core Logic — Replace the regex patterns**
   a. Locate `_parse_mqe_response()` at line 148 in `scripts/rag/llm_prompts.py`
   b. Replace the regex pattern and remove `re.DOTALL`:
      ```python
      # Before:
      m = re.search(r"\[.*\]", raw, re.DOTALL)
      
      # After:
      m = re.search(r"\[[^\]]*\]", raw)
      ```
   
   c. Locate `_apply_rerank_scores()` at line 189 in `scripts/rag/llm_prompts.py`
   d. Replace the regex pattern and remove `re.DOTALL`:
      ```python
      # Before:
      m = re.search(r"\{.*\}", raw, re.DOTALL)
      
      # After:
      m = re.search(r"\{[^{}]*\}", raw)
      ```
   
   e. Update both functions' docstrings to note the innermost-pair-only extraction:
      - Add a note explaining that the function now matches only the innermost bracket/brace pair, not spanning across multiple bracket/brace pairs
   
3. **Phase 3: Deployment & Verification**
   a. Run `pytest tests/rag/test_rag_pipeline.py -k mqe` to verify existing and new tests pass

## Compatibility considerations

- The new pattern cannot match a JSON array/object containing nested brackets/braces (e.g. `[[1,2],[3,4]]` or `{"a": {"b": 1}}`) — mitigated by confirmation that neither MQE's flat string-array payload nor rerank's flat score-map payload requires nested structures
- Removing `re.DOTALL` could theoretically change behavior for JSON containing literal newlines inside string values — mitigated by the fact that the new patterns exclude `]`/`{`/`}` characters, not newlines; a newline inside a JSON string value is still matched by `[^\]]`/`[^{}]` since it is not one of the excluded characters, so multi-line JSON *values* within a single well-formed array/object are still handled correctly

## Security considerations

N/A: Regex pattern correction only, no security impact.

## Rollback considerations

Simple revert of the two regex pattern replacements and the two docstring updates — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/llm_prompts.py | Unit — verify correct extraction from single and multi-fragment input | pytest tests/rag/test_rag_pipeline.py -k mqe | Extracts only the first valid JSON structure; existing well-formed cases unaffected |

## Completion criteria

- [ ] `_parse_mqe_response()` correctly parses a well-formed JSON array even when the raw input contains additional bracket-like text before/after it
- [ ] `_parse_mqe_response()` does not span across two separate `[...]` fragments in the same input
- [ ] `_apply_rerank_scores()` correctly parses a well-formed JSON object even when the raw input contains additional brace-like text before/after it
- [ ] `_apply_rerank_scores()` does not span across two separate `{...}` fragments in the same input
- [ ] All existing tests pass after changes

## Out of scope

- Modifying `scripts/rag/llm_client.py` (reference file only)
- Support for multi-line/nested JSON extraction
- Changes to how fallback is triggered when no JSON is found
- Changes to `orjson` parsing itself

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm no caller depends on greedy-match behavior | Pending | — | — | Check callers of _parse_mqe_response/_apply_rerank_scores |
| 2 | Replace r"\\[.*\\]"/re.DOTALL with r"\\[[^\\]]*\\]" in _parse_mqe_response | Pending | — | — | Line 148 |
| 3 | Replace r"\\{.*\\}"/re.DOTALL with r"\\{[^{}]*\\}" in _apply_rerank_scores | Pending | — | — | Line 189 |
| 4 | Update _parse_mqe_response docstring | Pending | — | — | Note innermost-pair-only extraction |
| 5 | Update _apply_rerank_scores docstring | Pending | — | — | Note innermost-pair-only extraction |
| 6 | Run pytest tests/rag/test_rag_pipeline.py -k mqe | Pending | — | — | Verify existing and new tests pass |

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
- **Requirement ID**: REQ-001, REQ-002 — replace greedy regex patterns with non-greedy innermost-pair-only patterns
- **Source issue**: issues/20260913-163623_regex001_llm_response_parsing_vulnerabilities.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-195005_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-210606
- **Related target files**: scripts/rag/llm_prompts.py
