# Adversarial Review — `scripts/mcp_servers/web_search` (10 modules)

Reviewed head: `de26cfcadb4bd7a0502c3ecd05ce1e4c09072ed9` (working tree matched HEAD, no uncommitted edits).

## Review Scope

- Reviewed (orchestration): `web_search_service.py`.
- Reviewed (provider/security boundary): `search_provider.py`, `web_search_security_checks.py`.
- Reviewed (server/dispatch): `web_search_server.py`, `formatters.py`, `web_search_tools.py`.
- Reviewed (models/config): `web_search_models.py`.
- Reviewed (observability): `health.py`, `metrics.py`.
- Reviewed (shared backbone): `mcp_servers/dispatch.py`, `mcp_servers/server.py` (auth middleware + REQ-004 idempotency boundary), `mcp_servers/audit.py`, `scripts/shared/tool_constants.py`.
- Not reviewed: non-Python assets, shell/TOML, tests (no test-run phase beyond the existing suite), other `scripts/mcp_servers/*` servers.

Working tree vs reviewed head: matched at `de26cfcadb4bd7a0502c3ecd05ce1e4c09072ed9`.

## Commands run

| Tool | Scope | Result |
|---|---|---|
| `ruff check` | `scripts/mcp_servers/web_search/` | All checks passed |
| `mypy --no-namespace-packages` | `scripts/mcp_servers/web_search/` | Success: no issues found (10 files) |
| `bandit -ll` | `scripts/mcp_servers/web_search/` | Clean (0 issues) |
| `pytest tests/mcp_servers/web_search/` | full web_search suite | 248 passed |

## Summary

- Overall assessment: **Clean.** No correctness, concurrency, resource-lifecycle, error-handling, configuration, or security defect survives adversarial scrutiny across the provider, server, dispatch, config, and observability layers. The code is defensively structured: the browser-fetch allowlist boundary is fail-closed (scheme + lowercase-hostname + unconditional IP-literal block + allowlist membership), config load is fail-fast (invalid bounds rejected at import), auth is constant-time Bearer with an empty-token fail-closed gate registered outermost, purge/dispatch paths are dedup-safe, and read-only tools are correctly excluded from the side-effect/idempotency gate.
- Highest-risk area: **the `browser_fetch` SSRF boundary** (`search_provider._check_domain` + `fetch_browser`). Scrutinized for URL-parsing bypasses (userinfo/port/IDN/IP-literal/encoding); no hostname-spoofing bypass found. The one residual observation is that redirect-following is *not* set explicitly and relies on httpx's default.
- Recommended next step: **proceed.** No fix required. The items below are all Low/Informational; each is either documented-and-intentional, a deliberate fail-closed tradeoff, or defensive fragility that is currently safe. None warrants a tracked issue.

## Adversarial scenarios exercised

| Scenario | Path examined | Outcome |
|---|---|---|
| `browser_fetch` to an IP-literal loopback target | `search_provider._check_domain` (IP check) | `BrowserAuthorizationError`; no fetch (checked unconditionally, before allowlist). |
| `browser_fetch` to a non-allowlisted domain | `_check_domain` allowlist membership | `BrowserAuthorizationError`; fail-closed. |
| `browser_fetch` with empty allowlist | `_check_domain` + `_web_search_tool_availability` | Denied at runtime AND tool withheld from `/v1/tools`. |
| URL with userinfo / port (`http://a@host/x`) | `urlsplit().hostname` | Userinfo/port stripped; only hostname compared. No spoof. |
| Non-http(s) scheme / missing hostname | `_check_domain` scheme guard | `BrowserValidationError`; no fetch. |
| `browser_fetch` target returns a 3xx to an internal host | `httpx.AsyncClient` default | Redirects **not** followed (default `follow_redirects=False`); no SSRF-via-redirect today. |
| Search times out after `search_timeout_sec` | `search_duckduckgo` `asyncio.wait_for` | `WebSearchTimeoutError`; classified, recorded, re-raised. |
| Invalid `max_results` / empty / control-char query | `SearchRequest` Pydantic + `normalize_query` | `ValueError` → `validation_error`; never reaches provider. |
| Keyless POST to a side-effecting tool | `server.py` REQ-004 middleware | 422 (inert until `ALL_SIDE_EFFECTING_TOOLS` defined); web_search tools are read-only, correctly exempt. |
| Request without matching Bearer token | `_auth_middleware` `hmac.compare_digest` | 401 (outermost middleware, runs before dispatch). |
| Empty `auth_token` | `require_auth_token` | `RuntimeError` at import → server refuses to start. |
| Configured bound exceeds hard ceiling | `_validate_config_bounds` + posture `_numeric_checks` | Rejected at load; posture would also FAILED. |

## Findings

No Medium-or-higher finding survived adversarial scrutiny. The four items below are all Low/Informational; each is either a deliberate fail-closed tradeoff, defensive fragility that is currently safe, or by-design audit behavior. None warrants a tracked issue.

### F-001 — `browser_fetch` audit log records the full URL plus an 80-char preview

- Title: Audit `target`/`preview` may carry query-string secrets.
- Severity: Informational
- Confidence: Medium
- Evidence label: Observed
- Evidence: `scripts/mcp_servers/web_search/web_search_server.py::_build_audit_target_and_detail` returns `(url, detail)` for `browser_fetch`, where `detail = f"... url_preview={url[:80]!r}"`; both become the audit record's `target`/`detail`. `_check_domain` validates only scheme + hostname, so the path/query is unconstrained.
- Current behavior: The full requested URL is stored in the audit `target` field and an 80-char prefix in `detail`. Callers can place tokens/signatures in the query (e.g. signed URLs) on an allowlisted host; those land in the plaintext audit log.
- Impact: Real but low — the allowlist restricts the domain, and audit traceability requires recording the target. The exposure is limited to callers that embed credentials in the URL query string.
- Recommended action: None required. If URLs may carry credentials, consider redacting the query string from the audit `target`/`preview` (e.g. strip everything after `?`).

### F-002 — `fetch_browser` SSRF-via-redirect protection relies on httpx's default

- Title: `follow_redirects` not set explicitly.
- Severity: Informational
- Confidence: High
- Evidence label: Verified (`httpx.Client.__init__` default for `follow_redirects` is `False`)
- Evidence: `scripts/mcp_servers/web_search/search_provider.py::fetch_browser` builds `httpx.AsyncClient(timeout=cfg.timeout_sec)` with no `follow_redirects=` argument.
- Current behavior: Redirects are not followed today (httpx default), so only the allowlisted host is fetched — no SSRF-via-redirect.
- Impact: Currently safe. The protection is implicit rather than declared; adding `follow_redirects=True` in a future edit would reintroduce SSRF-via-redirect to an internal target.
- Recommended action: Optional hardening — pass `follow_redirects=False` explicitly to lock the intent and make the boundary self-documenting.

### F-003 — `DDGS` search thread/session not torn down on timeout

- Title: Leaked worker thread on the timeout path.
- Severity: Low
- Confidence: Medium
- Evidence label: Observed
- Evidence: `scripts/mcp_servers/web_search/search_provider.py::search_duckduckgo` runs `DDGS()` inside `asyncio.to_thread(_sync_search)` wrapped by `asyncio.wait_for(..., timeout=search_timeout_sec)`.
- Current behavior: On timeout, `wait_for` cancels the future but the underlying worker thread keeps running and `DDGS.__exit__` (session close) never executes.
- Impact: Minor — a leaked thread/connection on the rare timeout path; Python eventually reclaims it. Inherent to the `to_thread` + `wait_for` pattern; not fixable without restructuring the provider call.
- Recommended action: None unless timeout frequency becomes a measured concern.

### F-004 — IDN/homoglyph allowlist entries are display concerns, not authz bypasses

- Title: Homoglyph resistance out of scope.
- Severity: Informational
- Confidence: High
- Evidence label: Observed
- Evidence: `search_provider._check_domain` compares the lowercased requested hostname verbatim against `allowed_domains`.
- Current behavior: An IDN/homoglyph hostname (e.g. Cyrillic homoglyph of an ASCII allowlist entry) does not byte-match the allowlist and is denied (fail-closed).
- Impact: No authorization bypass. A homoglyph is a phishing/display risk, outside the SSRF/authz boundary under review.
- Recommended action: None. Confirm homoglyph resistance is intentionally out of scope.

## Open Questions

- Question: Is `browser_fetch`'s `target`/`preview` audit logging acceptable as-is for URLs that may carry credentials?
- Why it matters: The audit `target` carries the full URL by design (traceability). If any caller embeds tokens/signature params in the query, they are persisted in plaintext.
- Required confirmation: Confirm whether allowlisted-domain URLs are ever requested with credential-bearing query strings. If yes, redact the query before logging; if no, risk is low and current behavior is acceptable.

## Suggested Tests

- Test target: `search_provider.fetch_browser` when the allowlisted host returns a 3xx redirect to an internal/IP-literal target.
- Behavior to verify: The client does not follow the redirect and the response reflects the original allowlisted URL (guards F-002 regression if `follow_redirects` is ever added).
- Failure mode: A future edit adding `follow_redirects=True` would fetch the internal metadata endpoint, reintroducing SSRF-via-redirect.

## Documentation Notes

- Target document: the `validate_web_search_security` posture contract (already complete and accurate; five check ids always present).
- Required update: none. The numeric-invariant and allowlist-posture checks match `_validate_config_bounds` and the runtime `_check_domain`/`fetch_browser` behavior.

## Final Recommendation

**Proceed.** No Medium-or-higher finding survives adversarial scrutiny. The toolchain is green (ruff, mypy clean over 10 files; bandit clean; 248 web_search tests pass). The four Low/Informational items are optional polish, defensive-fragility notes, or by-design audit behavior; none is actionable enough to warrant a tracked issue. The single Open Question (F-001/F-004 audit-logging of credential-bearing URLs) is confirmable without code change and does not block.
