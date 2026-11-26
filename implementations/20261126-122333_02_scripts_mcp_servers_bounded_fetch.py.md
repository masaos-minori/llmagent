## Goal
- Create the reusable bounded streaming download: a pinned connection to validated addresses (REQ-002), a bounded redirect loop with per-hop revalidation (REQ-003), 2xx-only status handling (REQ-004), independent raw, decoded, and parser-input limits (REQ-005), and a content-type gate before the body is read (REQ-006), with the host policy, limits, hop bound, types, and transport supplied by the caller (REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the new module `scripts/mcp_servers/bounded_fetch.py` and its test companion.
- Out of scope: HTML parsing and the extracted-text (returned-bytes) truncation, which stay with the caller; the web search wiring (seq 03); error mapping for metrics and health (seq 05 and 07).

## Assumptions
- Plan Assumptions carried over: httpx 0.28.1 and httpcore 1.0.9 are installed; the per-request sni_hostname extension sets the TLS server name (`httpcore/_async/connection.py` reads `request.extensions.get("sni_hostname")`, checked in Step 3a); no new dependency.
- The module imports only the standard library, `httpx`, and `mcp_servers.address_policy` (seq 01, an earlier-`seq` sibling whose names resolve by the stale detector).
- The CI/CD log retrieval will call `fetch_bounded` (new) with its own host policy; this document defines the contract it will use and changes no CI/CD file.
- Plan overlap check: this new file overlaps no other Frozen Plan.

## Design decisions
- The helper owns network concerns only. Host authorization is a caller-supplied callable `host_policy(url) -> hostname` run on every hop, so the web search allowlist and a trusted-GitHub-host policy plug in without the helper importing either.
- Decoding is done by the helper, not httpx: the body is read with `aiter_raw` (new) and decoded with `zlib.decompressobj` using `max_length`, so a decompression bomb cannot expand beyond the remaining budget in one step. Only `identity`, `gzip`, `x-gzip`, and `deflate` are accepted; any other content encoding is rejected.
- Four limits live in one frozen `FetchLimits` (new) (`raw_bytes`, `decoded_bytes` (new), parser_input_bytes, returned_bytes). The helper enforces the first three and reports which one stopped the stream in truncated_by; returned_bytes is carried for the caller's extracted-text cut.

## Alternatives considered
- `follow_redirects=True`: rejected, hops would skip revalidation (Plan D-4).
- Let httpx decode (`aiter_bytes`): rejected, one raw chunk could expand without bound before the decoded count is checked.
- A custom httpcore network backend for pinning: rejected, private httpx internals (Plan D-2).

## Implementation
### Target file
`scripts/mcp_servers/bounded_fetch.py` (new)

### Procedure
1. Create the module with the repository module docstring format and a `Dependency direction:` line.
2. Add the data types: `FetchLimits` (new) (frozen dataclass; every field a positive integer, validated in `__post_init__` with `ValueError`), `BoundedFetchResult` (new) (frozen dataclass: `final_url`, `status_code`, content_type, `charset`, `body`, download_truncated, truncated_by, declared_length, `elapsed_sec`).
3. Add the errors, all `RuntimeError` subclasses defined here: `FetchStatusError` (new) (attributes `status_code`, `category`), `FetchRedirectError` (new), `FetchContentTypeError` (new) (attribute content_type), `FetchUnsupportedEncodingError` (new) (attribute `encoding`). `category` is one of client_error, rate_limited, `server_error`, `other`.
4. Add `async def fetch_bounded(url, *, limits, host_policy, allowed_content_types, timeout_sec, max_redirects=5, resolver=None, transport=None, headers=None) -> BoundedFetchResult`.
5. Add private helpers: `_pinned_request(url, address)` (URL rewrite plus `Host` header), `_bounded_decoder(encoding, budget)` (incremental decode), `_media_type(header)`.

### Method
- Client: one `httpx.AsyncClient(timeout=timeout_sec, follow_redirects=False, trust_env=False, transport=transport)` per call, so environment proxies are never read. The whole call runs under an overall deadline of `timeout_sec * (max_redirects + 1)` seconds; its expiry is raised as an `httpx.TimeoutException` so existing timeout handling keeps working.
- Per hop: `hostname = host_policy(url)` (the caller's exceptions propagate unchanged); `addresses = await resolve_public_addresses(hostname, port, resolver=resolver)`; try the addresses in order, moving to the next only on `httpx.ConnectError`. The request URL host is replaced by the address (IPv6 in brackets), the `Host` header carries the original host and port, and the request extension `{"sni_hostname": hostname}` keeps the TLS server name and certificate-check name. Send `Accept-Encoding: gzip, deflate` and `GET` only.
- Redirects: for 301, 302, 303, 307, 308, read `Location`, resolve it with `urllib.parse.urljoin` against the current URL, close the response without reading the body, and loop; a missing `Location`, a non-http(s) scheme, or the hop count exceeding max_redirects raises `FetchRedirectError` (new). Each hop repeats the host policy and the address policy.
- Status: 2xx continues; 429 raises `FetchStatusError(category="rate_limited")`; other 4xx client_error; 5xx `server_error`; anything else `other`. The body of a non-2xx response is never read into the result.
- Content type: parse the media type from the `Content-Type` header before reading the body; a media type absent from allowed_content_types (or a missing header) raises `FetchContentTypeError` (new). Record `charset` from the parameters.
- Streaming: iterate `response.aiter_raw(chunk_size=8192)`. After each raw chunk, stop with `truncated_by="raw"` when `response.num_bytes_downloaded` exceeds `limits.raw_bytes`. Decode each chunk with the bounded decoder (`max_length` set to the remaining decoded budget); stop with `truncated_by="decoded"` when the decoded total reaches `limits.decoded_bytes`, and with `truncated_by="parser_input"` when the kept body reaches `limits.parser_input_bytes`. A `Content-Length` value is parsed only to fill declared_length; it never changes a limit. download_truncated is true exactly when truncated_by is set.
- `body` is the first `min(parser_input_bytes, decoded bytes read)` decoded bytes.

### Details
- Write the redirect, pinning, status, type, and limit tests first (companion) and confirm they fail before the module exists.
- Names other procedures rely on: `FetchLimits` (new), `BoundedFetchResult` (new), `FetchStatusError` (new), `FetchRedirectError` (new), `FetchContentTypeError` (new), `FetchUnsupportedEncodingError` (new), `fetch_bounded` (new).

### Companion test files
- `tests/mcp_servers/test_bounded_fetch.py` (new)
  - Procedure: with `httpx.MockTransport` and a fake resolver, assert the pinned request (target IP, `Host`, sni_hostname, resolver called once per hop and a changing answer cannot alter the connected address within a hop); redirects (allowed hop, host-policy rejection, prohibited address on a hop, non-http scheme, sixth hop, missing `Location`, relative `Location`); statuses 301 (unresolved), 403, 404, 429, 500, 503 and a 200; content types (`text/html`, `text/plain`, PDF, ZIP, image, missing); limits (each of raw, decoded, parser-input as the binding one), gzip expansion, deflate, a rejected `br` encoding, chunked transfer, a false and a missing `Content-Length`; trust_env ignored when HTTPS_PROXY is set.
  - Validation: `uv run pytest tests/mcp_servers/test_bounded_fetch.py`.

## Compatibility considerations
- New module; no existing caller until seq 03. The CI/CD service's current `follow_redirects=True` request is unchanged by this document.

## Security considerations
- Fail-closed at every hop: host policy, address policy, redirect bound, status gate, type gate, and three byte limits. No environment proxy. The `Host`, SNI, and certificate name stay the original host, so IP pinning does not weaken TLS verification; if the pinned request cannot verify a certificate for the original name, the fetch fails and there is no fallback to an unpinned request.

## Rollback considerations
- N/A: revert the commit; nothing imports the module until seq 03 lands.

## Validation plan
- `uv run pytest tests/mcp_servers/test_bounded_fetch.py`; `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy`; `uv run lint-imports`; `uv run bandit -r scripts/mcp_servers/bounded_fetch.py -c pyproject.toml`; `wc -c scripts/mcp_servers/bounded_fetch.py` below 24576; then the sequence in `rules/toolchain.md`. A live smoke test against an allowlisted public HTTPS site confirms certificate verification with the pinned address (run in seq 03).

## Completion criteria
- Every case of the companion test passes; a redirect cannot leave the host policy or the address policy; no non-2xx body and no non-allowed type reaches the caller; each limit independently stops the stream and reports truncated_by; the module stays standard-library plus `httpx` and address_policy; all validation commands pass.

## Out of Scope
- HTML parsing, extracted-text truncation, web search error mapping, metrics, health, the CI/CD adoption, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the module described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add the companion tests first, then confirm they pass | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (pinned connection), `REQ-003` (bounded redirects), `REQ-004` (2xx only), `REQ-005` (independent limits), `REQ-006` (content types), `REQ-008` (reusable helper)
- **Source issue**: issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114539_mcpws001_websearch-fetch-network-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-122333
- **Related target files**: `scripts/mcp_servers/bounded_fetch.py`, `tests/mcp_servers/test_bounded_fetch.py`
