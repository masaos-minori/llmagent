# Implementation Procedure: State both timeout mechanisms in the RAG configuration reference (rag_05_01)

## Goal

Extend the existing `http_timeout`/delegate-timeout paragraph so the configuration reference
states that in-process LLM/embedding calls inherit the shared client timeout explicitly at
the call site (REQ-005, AC-5).

## Scope

- One paragraph extension in `docs/21_rag/rag_05_01-configuration-reference.md` at the
  paragraph verified at L80 ("`http_timeout` is the HTTP client timeout of the MCP server
  itself ... neither is loaded from configuration or `RagPipelineConfig`.").
- No other section of the page changes.

## Assumptions

- N/A: documentation-only row.
- Churn 14 commits/30d per the Plan Affected areas: rebase immediately before editing.
- Overlap with the rag003 Plan on this file (config-key rename + key-contrast paragraph) is
  recorded as Compatible in the Plan Dependencies: disjoint paragraphs, second implementer
  rebases. rag003 is not yet processed as a procedure (memo2 order: rag003 after rag002), so
  check for a collision when rag003 procedures are generated.
- The existing "neither is loaded from configuration" sentence scopes to the RAG config
  sections of this page; the new sentence must not contradict it — the agent-section
  `http_timeout` is the client construction value, and the new text describes what the
  in-process calls do with it.

## Design decisions

- Extend the existing paragraph (where the two timeouts are already contrasted) rather than
  adding a new section — the page already carries the delegate/in-server split (Plan row
  evidence).
- Wording per Plan Design "contrast, not copy": name the mechanisms (delegate path's fixed
  per-attempt `_REQUEST_TIMEOUT_SECONDS` vs in-process calls' explicit `timeout=client.timeout`
  inheritance), not a converged number.

## Alternatives considered

- N/A: docs-only; placement fixed by the Plan row.

## Implementation
### Target file

`docs/21_rag/rag_05_01-configuration-reference.md`

### Procedure

1. Locate the paragraph at L80 (verified) ending "...neither is loaded from configuration or
   `RagPipelineConfig`."
2. Append to that paragraph: the in-process RAG query-path calls (`RagLLM._call_llm`,
   `get_embedding` in `scripts/rag/llm_client.py`) pass `timeout=client.timeout` explicitly
   at each POST, inheriting the injected `httpx.AsyncClient`'s configured timeout (120.0s in
   both production client paths: agent `llm.http_timeout`, rag_pipeline server's
   process-level client), while the delegate path `call_rag_service()` keeps its fixed
   per-attempt 10.0s.

### Method

Single-paragraph extension; edit after the `scripts/rag/llm_client.py` row lands so the doc
describes actual code.

### Details

- N/A: nothing further beyond the Plan text is required.

## Compatibility considerations

- N/A: docs only; symbols named by the new text (`_call_llm`, `get_embedding`,
  `call_rag_service`, `_REQUEST_TIMEOUT_SECONDS`) exist before and after the source row —
  `check_docs_consistency.py --domain rag` must resolve them.

## Security considerations

- N/A: docs only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py
  docs/21_rag/rag_05_01-configuration-reference.md`,
  `uv run python tools/check_docs_content_policy.py`,
  `uv run python tools/check_docs_consistency.py --domain rag` — all clean.

## Completion criteria

- AC-5: the page names both mechanisms — fixed delegate timeout and explicit client-timeout
  inheritance at the in-process call sites.

## Out of Scope

- The helper page (`docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`, own
  procedure document), the rag003 key-rename edits on this page (separate Plan), and any
  numeric timeout change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261027-202638 | 20261027-202638 | — |
| 2 | Run the documentation checkers (`routing.md` Tools: docs quality/structure/content-policy/consistency --domain rag) | Completed | 20261027-202638 | 20261027-202638 | — |

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
- **Requirement ID**: REQ-005 (both timeout mechanisms documented on the config page)
- **Source issue**: issues/20261027-071811_rag002_rag-timeout-enforcement-gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110252_rag002_rag-timeout-enforcement-gap.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-144351
- **Related target files**: docs/21_rag/rag_05_01-configuration-reference.md