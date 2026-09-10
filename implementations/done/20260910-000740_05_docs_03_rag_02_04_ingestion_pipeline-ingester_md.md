## Goal

Remove literal port numbers from the RagIngester detail document and replace with prose describing what the setting controls rather than its current value.

## Scope

Modify `docs/03_rag_02_04_ingestion_pipeline-ingester.md`: remove literal port numbers at lines 37 and 110, confirm the surrounding sentences still read coherently.

## Assumptions

- Lines 37 and 110 contain literal port numbers "8081" that duplicate configuration values and go stale when ports change.
- Removing the port numbers does not break the sentence structure.
- The surrounding prose ("generates embeddings via `embed-llm`") remains coherent after removal.

## Design decisions

- Replace literal port numbers with descriptions of what the setting controls rather than its current value.
- Preserve the rest of the sentence describing the component's responsibility.

## Alternatives considered

- Retain the port number with a note that it is illustrative: rejected because the policy targets literal port numbers in prose regardless of intent.
- Remove the entire sentence about embed-llm: rejected because the sentence describes component responsibility, which is retain-category content.

## Implementation

### Target file

`docs/03_rag_02_04_ingestion_pipeline-ingester.md`

### Procedure

1. Read lines 37 and 110 and their surrounding paragraphs to confirm the context of the literal port numbers.
2. Remove the literal port numbers.
3. Confirm the surrounding sentences still read coherently.
4. Run `uv run python tools/check_docs_content_policy.py` to verify zero findings.

### Method

Read line 37: "`RagIngester` reads chunk files, generates embeddings via `embed-llm` (port 8081), and upserts them into SQLite (`documents` / `chunks` / `chunks_vec`)."

Line 110 repeats the same content (duplicate section).

Both lines contain the literal port number "8081" in parentheses as a parenthetical clarification of which embed-llm service is being referenced. This is a concrete configuration value that duplicates the embedding service's configuration and goes stale when the port changes.

Replace "(port 8081)" with prose describing the embed-llm service's role without referencing its current port assignment. The sentence remains grammatically coherent without the parenthetical port number. The embed-llm service's identity is established by its name; the specific port is an implementation detail best sourced from the configuration file.

### Details

Lines 37 and 110 currently read:
```
`RagIngester` reads chunk files, generates embeddings via `embed-llm` (port 8081), and upserts them into SQLite (`documents` / `chunks` / `chunks_vec`).
```

The literal port number "8081" appears in parentheses as a parenthetical clarification of which embed-llm service is being referenced. This is a concrete configuration value that duplicates the embedding service's configuration and goes stale when the port changes.

Also present in this file:
- Line 153: `POST http://127.0.0.1:8081/embedding` — an HTTP request example showing the full URL with port number
- Line 231: Same HTTP request example repeated in a duplicate section

These HTTP request examples also contain literal port numbers and should be reviewed against the policy. However, they are code examples (not prose) and may fall under different rules. The plan only flags lines 37 and 110, so focus on those.

## Compatibility considerations

- The replacement must maintain the same information coverage as the original sentence. The embed-llm service's identity is preserved; only the concrete port number is removed.
- Cross-references to other documents must be preserved.

## Security considerations

- None identified. This is a documentation-only change removing literal port numbers.

## Rollback considerations

- If the prose replacement loses critical identification of the embed-llm service, the original sentence can be restored temporarily while a better replacement is drafted.
- The rollback path is straightforward: revert the edit and restore the original sentence.

## Validation plan

| Target File | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/03_rag_02_04_ingestion_pipeline-ingester.md` | Manual review + checker | `uv run python tools/check_docs_content_policy.py` && `uv run python tools/check_docs_structure.py docs/03_rag_02_04_ingestion_pipeline-ingester.md` | Zero literal-port-number findings; structure check passes |

## Completion criteria

- The literal port numbers at lines 37 and 110 have been removed.
- The surrounding sentences remain coherent and still describe what the setting controls.
- `check_docs_content_policy.py` reports zero literal-port-number findings for this file.

## Out of scope

- Modifying any other content in this file beyond the flagged port numbers and their immediate sentences.
- Any other file or section of this document.
- Any file outside the RAG domain.

## execution status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read lines 37 and 110 and their surrounding paragraphs | Completed | — | — | Confirmed context of literal port numbers at both locations |
| 2 | Remove the literal port numbers and replace with prose | Completed | — | — | Removed "(port 8081)" from both duplicate sections; sentences remain coherent |
| 3 | Run validation checks | Completed | — | — | Zero literal-port-number findings for this file; consistency check has pre-existing warnings unrelated to this change |

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
- **Requirement ID**: REQ-003: Read and resolve the remaining findings in other five files, applying the same remove/replace pattern for genuine index-table or file-tree/location-mapping content
- **Source issue**: issues/20260905-153715_dcp005_rag_docs_content_policy_cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-211729_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-000740
- **Related target files**: docs/03_rag_02_04_ingestion_pipeline-ingester.md
