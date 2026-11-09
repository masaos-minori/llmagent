## Goal

State the crawler redirect trust boundary in the crawler document (`REQ-007`): redirects are no longer followed automatically; `fetch_html` follows them hop by hop with a per-hop policy (same host, with an http-to-https upgrade allowed, and a non-public-address check for non-start hosts), refused hops are logged distinctly, and an accepted page is persisted under its final URL — including the DNS-resolution limitation.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md` — add a trust-boundary statement describing what is fetched, what is refused, and the DNS limitation, in the conditional-GET / robots section near the existing bullets (`docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md:72-73`).
- Out of scope: the policy helpers (document `03`), the fetch and orchestrator changes (documents `01`, `02`), and the mock-transport tests (document `04`).

## Assumptions

- The sibling plan `plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md` edits the same file in different paragraphs (the 304 handling); this addition sits beside the conditional-GET and robots bullets and does not rewrite them.
- The document already describes conditional GET and the opt-in robots policy; the new text extends it with the redirect policy.

## Design decisions

- Keep the statement at the operator-facing level: what the crawler fetches, what it refuses and why, and the one limitation the owner needs to know (DNS resolution is checked before the request but not pinned to the connection).
- Point the reader at the configuration keys (`skip_external`, `respect_robots`) so the boundary is understood relative to the defaults.

## Alternatives considered

- Describing the per-hop algorithm in detail: rejected; the document is operator-facing, and the algorithm lives in the code and its procedure (document `01`).

## Implementation
### Target file
`docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`

### Procedure
1. Add a paragraph to the crawl-behavior description stating that automatic redirect following is off and `fetch_html` follows redirects hop by hop, allowing only the start host (with an http-to-https upgrade) when external crawling is off and otherwise requiring every non-start host to resolve to a public address.
2. State that a refused hop (cross-origin, loopback, link-local, reserved, multicast, unspecified, or a downgrade) is logged distinctly and enqueues nothing.
3. State that an accepted page is persisted under its final URL and marked visited, and note that a redirected page is therefore looked up under the requested URL on the next run and re-fetched by the freshness check.
4. Add the DNS limitation: the address check resolves the host before the request but the resolution is not pinned to the connection, so a DNS-rebinding attacker is not fully excluded.
5. Keep the wording consistent with the existing conditional-GET and robots bullets (`docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md:72-73`).

### Method

- Insert the paragraph into section 2.2's behavior list or a short subsection, matching the existing bullet style; do not alter the front matter or other sections.

### Details

- Reference `skip_external` and `respect_robots` as the config that selects the boundary, and link the Configuration Reference as the existing bullets do.
- Do not duplicate the algorithm; refer readers to the code for the per-hop detail.

## Compatibility considerations

- N/A: this is a documentation-only addition; it changes no API, config, or behavior.

## Security considerations

- This is the operator-facing half of the trust boundary (`REQ-002`): it tells the owner what the crawler will and will not follow, so an open redirect or a malicious page can no longer silently reach an internal service without the refusal being visible in logs. The DNS-limitation sentence is required so the limitation is disclosed rather than implied.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_content_policy.py`, `tools/check_docs_consistency.py --domain rag`, `tools/check_docs_japanese.py` — no findings.

## Completion criteria

- The document states that redirects are followed hop by hop with a per-hop same-host and non-public-address policy, that refused hops are logged distinctly, that pages are persisted under their final URL, and that DNS resolution is checked before the request but not pinned to the connection.
- The docs gates pass.

## Out of Scope

- The policy helpers (document `03`).
- The fetch and orchestrator changes (documents `01`, `02`).
- The mock-transport tests (document `04`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261109-234525 | 20261109-234525 | Edit the crawler document |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-234525 | 20261109-234525 | Docs gates named above |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261109-234525 | 20261109-234525 | This document is the change |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-205004_05_docs_21_rag_rag_02_02_ingestion_pipeline-crawler.md.md | 1 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-007` (crawler trust-boundary documentation, including the DNS limitation)
- **Source issue**: issues/20261108-131127_ragrev012_crawler-redirect-trust-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170101_ragrev012_crawler-redirect-trust-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-205004
- **Related target files**: `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`