# Implementation procedure: `tests/test_browser_mcp_service.py` (new file)

Source plan: `plans/20260719-101501_plan.md`, Implementation step 5. Depends on the paired
`models.py`/`service.py` docs (`implementations/20260719-111829_browser_models.py.md`,
`implementations/20260719-111830_browser_service.py.md`).

No existing implementations doc under `implementations/` or `implementations/done/` matches
this exact filename (`grep -rl "test_browser_mcp_service"` across both directories returned no
hits). Not a genuine overlap concern — this filename is server-specific and unused elsewhere.

## Goal

Create `tests/test_browser_mcp_service.py` — unit tests for `BrowserService`'s guard methods
and dispatch handler — following `tests/test_shell_mcp_service.py`'s (632 lines, verified)
conventions: local `_make_policy`/`_make_service`-style factories using `tmp_path` where
relevant, direct instantiation and private-method testing over mocking, `pytest.mark.asyncio`
for async paths, and `respx` for mocked HTTP calls (project dependency, confirmed in
`pyproject.toml:62`, `"respx>=0.21"`, and already used by `tests/test_llm_client.py` and
`tests/test_rag_pipeline_service.py`).

## Scope

**In scope**
- `TestCheckDomain` class: allowed-domain pass case, disallowed-domain-raises-403 case
  (mirrors `TestCheckCommand`, `test_shell_mcp_service.py:236-254`), empty-`allowed_domains`-
  denies-all case (fail-closed default), and IP-literal/loopback-rejection cases (e.g.
  `http://127.0.0.1/`, `http://169.254.169.254/` — the AWS/GCP metadata-endpoint SSRF classic —
  and a private-range address, all raising `BrowserAuthorizationError` even if hypothetically
  present in `allowed_domains`, per the defense-in-depth design).
- `TestTruncate` class: under-limit passthrough (`truncated=False`), over-limit truncation
  (`truncated=True`, byte-length assertion), mirroring `TestOutputTruncation`
  (`test_shell_mcp_service.py:288-307`).
- `TestExtractText` class: `<script>`/`<style>` stripped, visible text preserved — a
  Browser-specific case with no direct shell-mcp analog (new logic; no template exists for
  this, since no other server does HTML parsing).
- `TestFetch` class (`@pytest.mark.asyncio`): a `respx`-mocked HTTP GET returning HTML with
  known text content, asserting the returned `BrowserFetchResponse.text` contains the expected
  extracted text and `status_code` matches; a `respx`-mocked non-2xx response case; a
  `respx`-mocked timeout/connection-error case, asserting it surfaces as the domain exception
  chosen in the `server.py`/`service.py` docs (`BrowserFetchError` or equivalent) rather than a
  raw `httpx` exception leaking out.
- `TestBuildService` class: empty-`allowed_domains`-logs-warning case, mirroring
  `TestLazyShellService.test_empty_allowlist_logs_warning`
  (`test_shell_mcp_service.py:487-512`).
- `TestFmtFetch` class (`@pytest.mark.asyncio`): dispatch-handler formatting — asserts the
  plain-text output includes status/truncated markers, mirroring `TestDryRun`'s
  `test_fmt_run_command_*` cases (`test_shell_mcp_service.py:559-609`), adapted (no `dry_run`
  concept for Browser — every `browser_fetch` call actually fetches; there is no preview mode
  in this plan's scope, so no `TestDryRun`-equivalent class is needed).

**Out of scope**
- No `TestHealthResponse`-style `FastAPI TestClient` test is *required* by this plan (the plan's
  own Affected-areas text claims `test_shell_mcp_service.py` uses "no FastAPI TestClient" — this
  is a **minor drift**, verified: `test_shell_mcp_service.py:612-631`
  (`TestHealthResponse.test_health_response_includes_sandbox_backend_in_details`) *does* use
  `fastapi.testclient.TestClient` against `shell_server.app`. This doc does not mandate an
  equivalent for Browser since `server.py`'s HTTP wiring is covered by the `server.py` doc's own
  manual-smoke-test validation steps; a `TestClient`-based health-check unit test may optionally
  be added for parity if a reviewer wants closer 1:1 structural matching with shell-mcp's test
  file, but it is not required to satisfy this plan's Validation Plan table (which only requires
  `pytest tests/test_browser_mcp_service.py -v` to pass with the cases above).
- No sandboxing/subprocess/resource-limit tests (not applicable; Browser has no subprocess
  execution).

## Assumptions

1. Verified: `test_shell_mcp_service.py:29-52` (`_make_policy`) and `:55-70` (`_make_service`)
   are the local-factory pattern; Browser's tests should define an equivalent
   `_make_config(*, allowed_domains=None, max_response_kb=256, timeout_sec=15) -> BrowserConfig`
   helper (no `tmp_path` dependency needed for Browser's config, since it has no filesystem
   paths, unlike shell's `cwd_allowed_dirs`/`audit_log_path` — simpler than shell's factory).
2. Verified: `pytest.mark.asyncio` is the project's async-test marker (used throughout
   `test_shell_mcp_service.py`, e.g. line 289, 396, 432, 519, etc.) — Browser's async test
   methods (`fetch`, `fmt_fetch`) use the same marker; confirm `pytest-asyncio` is configured in
   `pyproject.toml`/`pytest.ini` (already true project-wide, evidenced by its use across the
   existing test suite).
3. `respx` (verified project dependency, `pyproject.toml:62`) is the correct choice for mocking
   `httpx.AsyncClient` calls, per `rules/toolchain.md`'s pytest-plugin list and per the plan's
   own Implementation step 5 wording ("`respx`-mocked, since the project already uses `respx`").
   Precedent usage: `tests/test_llm_client.py`, `tests/test_rag_pipeline_service.py` (both
   confirmed via `grep -rl "respx" tests/*.py`) — inspect one of these at implementation time
   for the exact `respx.mock`/`@respx.mock` decorator or fixture idiom used in this codebase,
   to match style (not independently re-verified line-by-line in this investigation pass, to
   avoid redundant reads per the token-efficiency guidance — the paired `service.py` doc already
   establishes the `httpx.AsyncClient` DI/usage shape to mock against).
4. IP-literal/loopback rejection test values: `127.0.0.1` (loopback), `169.254.169.254`
   (link-local — the canonical cloud-metadata SSRF target), and `10.0.0.1` (private) are the
   three `ipaddress` classification branches exercised by `_check_domain` per the paired
   `service.py` doc's Procedure step 3 (`.is_loopback`, `.is_link_local`, `.is_private`) — tests
   should cover all three distinctly, not just one representative case, since they are three
   separate boolean checks in the implementation and a bug in any one would not be caught by
   testing only the others.

## Implementation

### Target file

`tests/test_browser_mcp_service.py` (new file).

### Procedure

1. Imports: `pytest`, `respx`, `httpx`; `from mcp_servers.browser.browser_models import
   BrowserAuthorizationError, BrowserConfig, BrowserFetchRequest` (plus `BrowserFetchError` if
   introduced per the `server.py`/`service.py` docs); `from mcp_servers.browser.browser_service import
   BrowserService, build_service`.
2. Define `_make_config(*, allowed_domains=None, max_response_kb=256, timeout_sec=15) ->
   BrowserConfig` local factory per Assumption 1.
3. `TestCheckDomain`:
   - `test_allowed_domain_passes`: `allowed_domains=["example.com"]`, call
     `svc._check_domain("https://example.com/page")`, assert no exception and hostname
     returned.
   - `test_disallowed_domain_raises_403`: `allowed_domains=["example.com"]`, call with
     `"https://evil.example/"`, assert `pytest.raises(BrowserAuthorizationError)`.
   - `test_empty_allowlist_denies_all`: `allowed_domains=[]` (default), call with any URL,
     assert `pytest.raises(BrowserAuthorizationError)`.
   - `test_loopback_ip_rejected_even_if_allowlisted`: `allowed_domains=["127.0.0.1"]` (simulating
     misconfiguration), call with `"http://127.0.0.1/"`, assert
     `pytest.raises(BrowserAuthorizationError)` (defense-in-depth wins over allowlist).
   - `test_link_local_metadata_ip_rejected`: call with `"http://169.254.169.254/"`, assert
     raises regardless of allowlist contents.
   - `test_private_range_ip_rejected`: call with `"http://10.0.0.1/"`, assert raises.
4. `TestTruncate`:
   - `test_under_limit_returns_unmodified`: short text, `max_kb` large, assert
     `(text, False)`.
   - `test_over_limit_truncates_with_flag`: text sized > `max_kb * 1024` bytes, assert
     `truncated is True` and `len(result.encode()) <= max_kb * 1024`.
5. `TestExtractText`:
   - `test_strips_script_and_style_tags`: HTML with `<script>`/`<style>` blocks plus visible
     `<p>` text; assert script/style content absent, paragraph text present.
6. `TestFetch` (`@pytest.mark.asyncio`, `respx`-mocked):
   - `test_fetch_returns_extracted_text`: mock GET to an allowlisted URL returning
     `<html><body><p>Hello</p></body></html>`; assert `resp.text` contains `"Hello"`,
     `resp.status_code == 200`, `resp.truncated is False`.
   - `test_fetch_disallowed_domain_raises_before_network_call`: assert the mocked route is
     **not** called (domain check happens before the HTTP request) when the URL is not
     allowlisted.
   - `test_fetch_timeout_raises_domain_exception`: mock a `httpx.TimeoutException`, assert it
     surfaces as the chosen domain exception, not a raw `httpx` exception.
7. `TestBuildService`:
   - `test_empty_allowed_domains_logs_warning` (`caplog`): mirrors
     `test_shell_mcp_service.py:487-512`'s shape, asserting a warning is logged when
     `cfg.allowed_domains == []`.
8. `TestFmtFetch` (`@pytest.mark.asyncio`):
   - `test_fmt_fetch_formats_success_result`: patch `svc.fetch` to return a canned
     `BrowserFetchResponse`, assert formatted string includes status/text.
   - `test_fmt_fetch_truncated_flag`: canned response with `truncated=True`, assert a
     "[TRUNCATED]"-equivalent marker appears in the formatted output (per the `service.py`
     doc's `_format_fetch_result` design, mirroring shell's `[OUTPUT TRUNCATED]` marker style).

### Method

New-file creation adapting `test_shell_mcp_service.py`'s structure; direct instantiation and
private-method testing (`svc._check_domain(...)`, `svc._truncate(...)`, `svc._extract_text(...)`)
over mocking framework internals, matching the existing convention exactly.

### Details

No new production types are introduced by this test file itself; it exercises the types defined
in the paired `models.py`/`service.py` docs.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format tests/test_browser_mcp_service.py && uv run ruff check tests/test_browser_mcp_service.py` | 0 errors |
| Type check | `uv run mypy tests/test_browser_mcp_service.py` | 0 errors (per `rules/coding.md`'s mypy note: `tests/` is covered) |
| Target tests | `uv run pytest tests/test_browser_mcp_service.py -v` | all pass |
| Full suite | `uv run pytest -v` | no new failures |
| Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines across `scripts/mcp_servers/browser/*.py` |
| No bare except | `ast-grep --pattern 'except: $$$' --lang python tests/test_browser_mcp_service.py` | no matches |
