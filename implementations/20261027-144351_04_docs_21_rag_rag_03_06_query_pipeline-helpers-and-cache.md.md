# Implementation Procedure: Add the timeout-source note to the RAG LLM helper page (rag_03_06)

## Goal

State where the in-process timeout comes from on the page that documents the RAG LLM helper
functions, so a future call site added here sees the rule (REQ-005, AC-5).

## Scope

- One sentence/paragraph addition to `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`
  in section 7.3 `RagLLM` (verified at L60-62: methods and `get_embedding` described with no
  timeout statement).
- No other section of the page changes.

## Assumptions

- N/A: documentation-only row.
- Shared page with the rag001 Plan procedure
  (`implementations/20261027-131124_07_docs_21_rag_rag_03_06_query_pipeline-helpers-and-cache.md.md`,
  sanitization invariant after the `RagLLM` methods paragraph at L62): the two additions are
  different sentences; both Plans record the overlap as Compatible and the second implementer
  rebases.
- Churn 16 commits/30d per the Plan Affected areas: rebase immediately before editing.

## Design decisions

- Place the note in section 7.3 next to the `RagLLM`/`get_embedding` description — the page a
  future prompt/embedding call site would be documented on (Plan row evidence).
- Wording per Plan Design: name the mechanism (`timeout=client.timeout`, inherited from the
  injected `httpx.AsyncClient`) and the contrast (delegate path's fixed per-attempt
  `_REQUEST_TIMEOUT_SECONDS`); no number copy beyond what the code names.

## Alternatives considered

- Documenting only on the config-reference page — rejected: the Plan pins a second
  statement at the helper page where the call sites are described.

## Implementation
### Target file

`docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`

### Procedure

1. After the section 7.3 `RagLLM` methods paragraph (L62, verified), add one sentence: the
   in-process HTTP calls in this module (`RagLLM._call_llm`, `get_embedding`) pass
   `timeout=client.timeout` explicitly, inheriting the injected client's configured timeout;
   the delegate path (`call_rag_service`, see `rag_05_01-configuration-reference.md`) uses a
   fixed per-attempt timeout instead. `refine_context` already takes an explicit `timeout`
   parameter.
2. Keep the existing exception-module text and the link to
   `rag_05_04-error-handling-reference.md` unchanged.

### Method

Single-sentence/paragraph insertion; edit after the `scripts/rag/llm_client.py` row lands so
the doc describes actual code.

### Details

- If the rag001 sanitization sentence has already landed on this page, insert the timeout
  sentence after it; both coexist in section 7.3.

## Compatibility considerations

- N/A: docs only; symbols named (`_call_llm`, `get_embedding`, `refine_context`,
  `call_rag_service`) all exist; `check_docs_consistency.py --domain rag` must resolve them.

## Security considerations

- N/A: docs only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py
  docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`,
  `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain rag` — all clean.

## Completion criteria

- AC-5: the helper page states the timeout source (client inheritance) and names the
  fixed-timeout delegate contrast.

## Out of Scope

- The config-reference page (own procedure document), the rag001 sanitization invariant
  sentence (separate Plan, separate procedure), and any timeout numeric change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers (`routing.md` Tools: docs quality/structure/content-policy/consistency --domain rag) | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (timeout source visible on the helper page)
- **Source issue**: issues/20261027-071811_rag002_rag-timeout-enforcement-gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110252_rag002_rag-timeout-enforcement-gap.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-144351
- **Related target files**: docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md
